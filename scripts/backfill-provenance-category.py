#!/usr/bin/env python3
"""One-off backfill: give every atom a `category` and every imported atom a `provenance`.

Runs over the current tree, so it is safe to re-run; it only fills fields that are
missing and never overwrites a value a maintainer set by hand.

Rules:
  - skills imported from GitHub (source_url present, no provenance): provenance from
    the repository, with the license each repository publishes.
  - persona / prompt / agent atoms: category from the persona's role.domain or the
    atom's tags; the retired catalogs carried no category.
  - hooks: category governance (they enforce rules) or security (secret handling).
  - anything still uncategorised: 'other', reported so a maintainer can fix it.
"""
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATOMS = REPO / "atoms"

# Repositories the existing imports came from and the license each one publishes.
REPO_LICENSE = {
    "anthropics/knowledge-work-plugins": ("Anthropic", "Apache-2.0"),
    "anthropics/skills": ("Anthropic", "Apache-2.0"),
    "dotnet/skills": ("Microsoft / .NET Foundation", "MIT"),
    "kepano/obsidian-skills": ("Steph Ango (kepano)", "MIT"),
}
# Words in a domain or tag -> category.
WORD_CATEGORY = [
    (("security", "pentest", "penetration", "cybersecurity", "secret"), "security"),
    (("incident", "sre", "reliability", "devops", "infrastructure", "runbook", "oncall", "deploy", "kubernetes", "terraform", "operations"), "devops"),
    (("test", "tdd", "qa", "verifier"), "testing"),
    (("doc", "documentation", "writer", "technical-writing", "knowledge", "obsidian"), "knowledge"),
    (("data", "analysis", "analytics", "pipeline"), "data"),
    (("design", "ux", "accessibility", "wcag"), "design"),
    (("product", "planning", "planner", "roadmap"), "product"),
    (("research", "science", "bio"), "research"),
    (("support", "customer"), "support"),
    (("education", "teacher", "mentor"), "knowledge"),
    (("governance", "audit", "review", "moderator", "aggregator", "coordinator", "olympus", "constitution"), "governance"),
    (("engineering", "software", "code", "coder", "refactor", "debug", "architecture", "api", "database", "git"), "coding"),
]


def category_from_words(words: list[str]) -> str | None:
    joined = " ".join(w.lower() for w in words if w)
    for needles, category in WORD_CATEGORY:
        if any(n in joined for n in needles):
            return category
    return None


def backfill_skill(atom: dict) -> bool:
    changed = False
    url = atom.get("source_url", "")
    if url and "provenance" not in atom:
        for repo, (author, license_) in REPO_LICENSE.items():
            if f"github.com/{repo}/" in url:
                atom["provenance"] = {"source": repo, "source_url": url, "author": author, "license": license_,
                                      "notes": "Imported by scripts/import-anthropic-skills.py."}
                changed = True
                break
    if "category" not in atom:
        atom["category"] = category_from_words(atom.get("applicable_domains", []) + atom.get("tags", [])) or "other"
        changed = True
    return changed


RETIRED_REPOS = {"persona": "persona-atoms", "prompt": "prompt-atoms", "agent": "agent-atoms"}


def backfill_generic(atom: dict, words: list[str], default: str) -> bool:
    changed = False
    if "category" not in atom:
        atom["category"] = category_from_words(words) or default
        changed = True
    cls = atom["type"]
    url = atom.get("source_url", "")
    if cls in RETIRED_REPOS and "provenance" not in atom and "github.com/convergent-systems-co/" in url:
        # The retired catalogs published their data under Apache-2.0 (LICENSE-data in each repo).
        atom["provenance"] = {"source": f"convergent-systems-co/{RETIRED_REPOS[cls]}", "source_url": url,
                              "author": "convergent-systems-co", "license": "Apache-2.0",
                              "notes": "Re-typed by scripts/migrate-retired-atoms.py from the retired catalog."}
        changed = True
    return changed


def main() -> int:
    counts: dict[str, int] = {}
    uncategorised: list[str] = []
    for path in sorted(ATOMS.rglob("*.json")):
        cls = path.relative_to(ATOMS).parts[0]
        if cls not in ("skill", "hook", "prompt", "agent", "persona", "model"):
            continue
        atom = json.loads(path.read_text(encoding="utf-8"))
        if cls == "skill":
            changed = backfill_skill(atom)
        elif cls == "hook":
            changed = backfill_generic(atom, atom.get("tags", []), "governance")
        elif cls == "persona":
            changed = backfill_generic(atom, [atom.get("role", {}).get("domain", "")] + atom.get("tags", []) + [atom["name"]], "other")
        elif cls == "prompt":
            changed = backfill_generic(atom, atom.get("tags", []) + [atom["name"]], "governance")
        elif cls == "agent":
            changed = backfill_generic(atom, atom.get("tags", []) + [atom["name"]], "coding")
        else:
            changed = False
        if changed:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            counts[cls] = counts.get(cls, 0) + 1
        if atom.get("category") == "other" and cls != "skill":
            uncategorised.append(atom["id"])
    print(json.dumps({"changed": counts, "still_other": uncategorised}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
