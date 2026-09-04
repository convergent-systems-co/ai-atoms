#!/usr/bin/env python3
"""Repair skill descriptions that are literally '>' or '>-'.

The original importers split frontmatter lines on the first colon, so a folded
YAML scalar (`description: >`) became the text ">". For each affected atom this
re-reads the original SKILL.md — from GitHub for repository sources, from the
claudeskills.in table for aggregator sources — parses it with scripts/skillmd.py,
and writes the real description. Nothing else in the atom changes; the version
gets a patch bump.

Usage: python3 scripts/repair-descriptions.py [--dry-run] [--claudeskills-dump rows.json]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillmd import parse_frontmatter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "atoms" / "skill"
DRY_RUN = "--dry-run" in sys.argv
BROKEN = {">", ">-", "|", "|-", "&gt;", "&gt;-"}
QUOTES = "\"'"
BLOB = re.compile(r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)$")


_TREES: dict[str, list[str]] = {}


def repo_tree(owner: str, repo: str, ref: str) -> list[str]:
    key = f"{owner}/{repo}@{ref}"
    if key not in _TREES:
        r = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/git/trees/{ref}?recursive=1", "--jq", ".tree[].path"],
                           capture_output=True, text=True, timeout=60)
        _TREES[key] = r.stdout.split() if r.returncode == 0 else []
    return _TREES[key]


def github_skill_md(url: str) -> tuple[str | None, str | None]:
    """Fetch SKILL.md for a blob URL. If the path has moved, find `<slug>/SKILL.md` in the tree.
    Returns (content, url_actually_used)."""
    m = BLOB.search(url)
    if not m:
        return None, None
    owner, repo, ref, path = m.groups()
    candidates = [path]
    parts = path.split("/")
    slug = parts[-2] if len(parts) >= 2 and parts[-1] == "SKILL.md" else None
    if slug:
        candidates += [t for t in repo_tree(owner, repo, ref) if t.endswith(f"/{slug}/SKILL.md") and t != path]
    for candidate in candidates:
        r = subprocess.run(["gh", "api", f"repos/{owner}/{repo}/contents/{candidate}?ref={ref}", "-H", "Accept: application/vnd.github.raw+json"],
                           capture_output=True, text=True, timeout=30)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout, f"https://github.com/{owner}/{repo}/blob/{ref}/{candidate}"
    return None, None


def claudeskills_rows() -> dict[str, str]:
    if "--claudeskills-dump" in sys.argv:
        rows = json.loads(Path(sys.argv[sys.argv.index("--claudeskills-dump") + 1]).read_text())
        return {r["name"]: r["content"] for r in rows}
    return {}


def bump(version: str) -> str:
    major, minor, patch = version.split(".")[:3]
    return f"{major}.{minor}.{int(patch) + 1}"


def main() -> int:
    dump = claudeskills_rows()
    fixed, unresolved, moved = [], [], []
    for path in sorted(SKILLS.glob("*.json")):
        atom = json.loads(path.read_text(encoding="utf-8"))
        if atom["description"].strip().strip(QUOTES) not in BROKEN:
            continue
        url = atom.get("source_url", "")
        content, used_url = None, None
        if "github.com" in url:
            content, used_url = github_skill_md(url)
        elif "claudeskills.in" in url:
            content = dump.get(url.rsplit("/", 1)[-1])
        fields, _ = parse_frontmatter(content or "")
        description = (fields.get("description") or "").replace('\\"', '"').strip()
        if not description or description.strip(QUOTES) in BROKEN:
            unresolved.append(atom["id"])
            continue
        atom["description"] = description[:997] + "..." if len(description) > 1000 else description
        if used_url and used_url != url:
            atom["source_url"] = used_url
            if atom.get("provenance", {}).get("source_url") == url:
                atom["provenance"]["source_url"] = used_url
            moved.append(f"{atom['id']} -> {used_url}")
        atom["version"] = bump(atom["version"])
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        fixed.append(atom["id"])
    print(json.dumps({"dry_run": DRY_RUN, "fixed": len(fixed), "moved_upstream": moved, "unresolved": unresolved}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
