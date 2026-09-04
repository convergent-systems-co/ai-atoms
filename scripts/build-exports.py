#!/usr/bin/env python3
"""Build exports/catalog.json from validated atoms and workflow compositions.

Walks atoms/<class>/ for every class that has a schema at schemas/<class>-v1.json
(skill, hook, prompt, agent, persona), validating each JSON file against it.
Classes without a schema are skipped with a warning so staged, not-yet-typed
content never reaches the published catalog.

After schema validation, every cross-atom reference (agent.persona, agent.skills,
prompt.includes, prompt.persona_ref, ...) must resolve. A dangling reference is a
build failure: consumers install compositions as a unit and cannot recover from a
missing part at runtime.

Walks workflows/ (no schema — compositions). Assembles a single machine-readable
catalog manifest. Exits 1 on any validation failure.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import jsonschema
    from referencing import Registry, Resource
except ImportError:
    print("error: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO / "schemas"
ATOMS_DIR = REPO / "atoms"
COMPOSITIONS_DIR = REPO / "workflows"
EXPORT_PATH = REPO / "exports" / "catalog.json"
CATALOG_NAME = "ai-atoms"
CATALOG_VERSION = "0.4.0"

# Atom classes with a published schema, in catalog display order.
TYPED_CLASSES = ("skill", "hook", "prompt", "agent", "persona", "model", "policy", "tool")
COMMON_SCHEMA = "common-v1.json"

# Fields whose values are references to other atoms, by owning class.
# Each entry is (field, expected-class-of-target). A `None` target class means
# the reference already carries its class prefix (e.g. "policy/no-fabrication").
REFERENCE_FIELDS: dict[str, list[tuple[str, str | None]]] = {
    "agent": [
        ("persona", "persona"),
        ("prompts", "prompt"),
        ("skills", "skill"),
        ("hooks", "hook"),
        ("tools", "tool"),
        ("policies", "policy"),
    ],
    "prompt": [
        ("persona_ref", "persona"),
        ("includes", "prompt"),
    ],
    "tool": [
        ("gated_by", "policy"),
    ],
    "skill": [
        ("depends_on", "skill"),
    ],
    "hook": [
        ("depends_on", "hook"),
    ],
}


def display_path(path: Path) -> str:
    """Repo-relative when inside the repo; absolute otherwise (tests validate trees elsewhere)."""
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def load_registry() -> Registry:
    """Every schema under schemas/ is registered by its $id so $ref across files resolves offline."""
    registry = Registry()
    for path in SCHEMA_DIR.glob("*.json"):
        schema = json.loads(path.read_text(encoding="utf-8"))
        registry = registry.with_resource(schema["$id"], Resource.from_contents(schema))
    return registry


def load_validator(name: str, registry: Registry | None = None) -> jsonschema.Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema, registry=registry or load_registry())


def load_schema_map() -> dict[str, jsonschema.Draft202012Validator]:
    """One validator per class that ships a schemas/<class>-v1.json."""
    registry = load_registry()
    return {
        cls: load_validator(f"{cls}-v1.json", registry)
        for cls in TYPED_CLASSES
        if (SCHEMA_DIR / f"{cls}-v1.json").exists()
    }


def collect_atoms(atoms_dir: Path) -> list[dict]:
    """Walk atoms/<class>/, validating each file against that class's schema."""
    schema_map = load_schema_map()

    out: list[dict] = []
    if not atoms_dir.exists():
        return out

    for type_dir in sorted(atoms_dir.iterdir()):
        if not type_dir.is_dir():
            continue
        atom_type = type_dir.name
        validator = schema_map.get(atom_type)
        if validator is None:
            print(f"warning: no schema for atom type '{atom_type}' — skipping {type_dir}", file=sys.stderr)
            continue
        label = f"{atom_type} atom"
        for path in sorted(type_dir.rglob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            errors = list(validator.iter_errors(data))
            if errors:
                print(f"x {display_path(path)} ({label}):", file=sys.stderr)
                for err in errors:
                    loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
                    print(f"    {err.message} at {loc}", file=sys.stderr)
                sys.exit(1)
            expected_prefix = f"{atom_type}/"
            if not str(data.get("id", "")).startswith(expected_prefix):
                print(
                    f"x {display_path(path)} ({label}): id {data.get('id')!r} "
                    f"must start with {expected_prefix!r}",
                    file=sys.stderr,
                )
                sys.exit(1)
            out.append(data)

    return out


def untyped_atom_exists(atoms_dir: Path, ref: str) -> bool:
    """A reference into a class with no schema resolves if a file with that slug exists."""
    cls, _, slug = ref.partition("/")
    class_dir = atoms_dir / cls
    if not class_dir.is_dir():
        return False
    return any(class_dir.rglob(f"{slug}.json"))


def find_dangling_references(atoms: list[dict], atoms_dir: Path = ATOMS_DIR) -> list[str]:
    """Return human-readable descriptions of every reference that does not resolve."""
    known_ids = {a["id"] for a in atoms}
    problems: list[str] = []
    for atom in atoms:
        for field, _target_class in REFERENCE_FIELDS.get(atom.get("type", ""), []):
            value = atom.get(field)
            if value is None:
                continue
            refs = value if isinstance(value, list) else [value]
            for ref in refs:
                if ref in known_ids or untyped_atom_exists(atoms_dir, ref):
                    continue
                problems.append(f"{atom['id']}.{field} -> {ref} (not in catalog)")
    return problems


def collect_compositions(compositions_dir: Path) -> list[dict]:
    """Walk workflows/ without schema validation (compositions are freeform)."""
    out: list[dict] = []
    if not compositions_dir.exists():
        return out
    for path in sorted(compositions_dir.rglob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def count_by_type(atoms: list[dict]) -> dict[str, int]:
    counts = {cls: 0 for cls in TYPED_CLASSES}
    for atom in atoms:
        counts[atom["type"]] = counts.get(atom["type"], 0) + 1
    return counts


def category_index(atoms: list[dict]) -> dict[str, dict[str, int]]:
    """Per-category atom counts by class, in the order the common schema lists categories."""
    common = json.loads((SCHEMA_DIR / COMMON_SCHEMA).read_text(encoding="utf-8"))
    categories = common["$defs"]["category"]["enum"]
    index: dict[str, dict[str, int]] = {}
    for atom in atoms:
        category = atom.get("category", "other")
        index.setdefault(category, {})[atom["type"]] = index.setdefault(category, {}).get(atom["type"], 0) + 1
    return {c: index[c] for c in categories if c in index}


def main() -> int:
    atoms = collect_atoms(ATOMS_DIR)

    dangling = find_dangling_references(atoms)
    if dangling:
        print("x dangling references:", file=sys.stderr)
        for problem in dangling:
            print(f"    {problem}", file=sys.stderr)
        return 1

    compositions = collect_compositions(COMPOSITIONS_DIR)
    counts = count_by_type(atoms)

    catalog = {
        "catalog": CATALOG_NAME,
        "version": CATALOG_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "classes": list(TYPED_CLASSES),
        "counts": counts,
        "categories": category_index(atoms),
        "atoms": atoms,
        "compositions": compositions,
        "rules": [],
    }

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    plural = {"policy": "policies"}
    summary = ", ".join(f"{n} {plural.get(cls, cls + 's')}" for cls, n in counts.items())
    print(f"wrote {EXPORT_PATH.relative_to(REPO)} — {len(atoms)} atoms ({summary}), {len(compositions)} compositions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
