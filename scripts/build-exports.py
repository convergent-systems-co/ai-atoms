#!/usr/bin/env python3
"""Build exports/catalog.json from validated skill and hook atoms, and workflow compositions.

Walks atoms/skill/ validating each against schemas/skill-v1.json;
walks atoms/hook/ validating each against schemas/hook-v1.json;
walks workflows/ (no schema — compositions).
Assembles a single machine-readable catalog manifest. Exits 1 on validation failure.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import jsonschema
except ImportError:
    print("error: jsonschema not installed. Run: pip install jsonschema", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parent.parent
SCHEMA_DIR = REPO / "schemas"
ATOMS_DIR = REPO / "atoms"
COMPOSITIONS_DIR = REPO / "workflows"
EXPORT_PATH = REPO / "exports" / "catalog.json"
CATALOG_NAME = "ai-atoms"
CATALOG_VERSION = "0.1.0"


def load_validator(name: str) -> jsonschema.Draft202012Validator:
    schema = json.loads((SCHEMA_DIR / name).read_text(encoding="utf-8"))
    return jsonschema.Draft202012Validator(schema)


def collect_atoms(atoms_dir: Path) -> list[dict]:
    """Walk atoms/skill/ and atoms/hook/, validating each against the appropriate schema."""
    skill_validator = load_validator("skill-v1.json")
    hook_validator = load_validator("hook-v1.json")

    schema_map = {
        "skill": skill_validator,
        "hook": hook_validator,
    }

    out: list[dict] = []
    if not atoms_dir.exists():
        return out

    # Collect from each typed subdirectory
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
                print(f"x {path.relative_to(REPO)} ({label}):", file=sys.stderr)
                for err in errors:
                    loc = "/".join(str(x) for x in err.absolute_path) or "<root>"
                    print(f"    {err.message} at {loc}", file=sys.stderr)
                sys.exit(1)
            out.append(data)

    return out


def collect_compositions(compositions_dir: Path) -> list[dict]:
    """Walk workflows/ without schema validation (compositions are freeform)."""
    out: list[dict] = []
    if not compositions_dir.exists():
        return out
    for path in sorted(compositions_dir.rglob("*.json")):
        out.append(json.loads(path.read_text(encoding="utf-8")))
    return out


def main() -> int:
    atoms = collect_atoms(ATOMS_DIR)
    compositions = collect_compositions(COMPOSITIONS_DIR)

    skills = [a for a in atoms if a.get("type") == "skill"]
    hooks = [a for a in atoms if a.get("type") == "hook"]

    catalog = {
        "catalog": CATALOG_NAME,
        "version": CATALOG_VERSION,
        "built_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "atoms": atoms,
        "compositions": compositions,
        "rules": [],
    }

    EXPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EXPORT_PATH.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"wrote {EXPORT_PATH.relative_to(REPO)} — "
        f"{len(atoms)} atoms ({len(skills)} skills, {len(hooks)} hooks), "
        f"{len(compositions)} compositions"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
