#!/usr/bin/env python3
"""Import skill atoms from claudeskills.in.

claudeskills.in is a directory that aggregates SKILL.md files from community GitHub
lists into a public Supabase table. The site states no license for the aggregated
content and records no per-skill author, so every imported atom carries a
`provenance` block: source, the record URL, the author and license when the
SKILL.md frontmatter names them, and `license: unknown` otherwise. Nothing is
invented.

Reads the table through the same public REST endpoint the site's own front end
uses (the publishable key is taken from the site's JavaScript bundle at run time,
never stored here). `--from-file <json>` imports a previously downloaded dump instead.

Existing atoms are never overwritten: a slug that already exists in atoms/skill/ is
reported and skipped, so an Anthropic-sourced atom keeps its own attribution.

Usage: python3 scripts/import-claudeskills.py [--dry-run] [--from-file rows.json]
"""
import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from skillmd import parse_frontmatter  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
ATOMS_DIR = REPO / "atoms" / "skill"
SITE = "https://claudeskills.in"
TABLE_URL = "https://vdduyltnybopajiclwej.supabase.co/rest/v1/skills"
SELECT = "id,name,category,description,risk,source,content,created_at,updated_at"
PAGE = 1000
TODAY = date.today().isoformat()

# claudeskills.in categories -> ai-atoms common category enum.
CATEGORY = {
    "devops": "devops", "frontend": "frontend", "backend": "backend", "security": "security",
    "ai": "ai", "test": "testing", "business": "product", "other": "other",
}
DRY_RUN = "--dry-run" in sys.argv


def http_get(url: str, headers: dict | None = None) -> bytes:
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def publishable_key() -> str:
    """The site's public, client-side Supabase key, read from its bundle."""
    html = http_get(SITE + "/").decode("utf-8", "replace")
    bundle = re.search(r'src="(/assets/index-[^"]+\.js)"', html)
    if not bundle:
        raise SystemExit("could not find the site bundle")
    js = http_get(SITE + bundle.group(1)).decode("utf-8", "replace")
    key = re.search(r"sb_publishable_[A-Za-z0-9_-]+", js)
    if not key:
        raise SystemExit("could not find the publishable key in the bundle")
    return key.group(0)


def fetch_rows() -> list[dict]:
    key = publishable_key()
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    rows: list[dict] = []
    start = 0
    while True:
        page_headers = {**headers, "Range": f"{start}-{start + PAGE - 1}"}
        batch = json.loads(http_get(f"{TABLE_URL}?select={SELECT}&order=name.asc", page_headers))
        rows.extend(batch)
        if len(batch) < PAGE:
            return rows
        start += PAGE


def license_for(row: dict, fm: dict) -> str:
    stated = fm.get("license", "")
    if stated and "LICENSE" not in stated:
        return stated
    source = row.get("source") or ""
    if "Apache 2.0" in source or "Apache-2.0" in source:
        return "Apache-2.0"
    return "unknown"


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9-]", "-", s.lower())
    return re.sub(r"-+", "-", s).strip("-")


def row_to_atom(row: dict) -> dict | None:
    fm, body = parse_frontmatter(row.get("content") or "")
    slug = slugify(row["name"])
    if not slug or not body:
        return None
    name = (fm.get("name") or row["name"]).replace("-", " ").title() if not fm.get("name") or fm["name"] == row["name"] else fm["name"]
    # Frontmatter descriptions arrive with their YAML escaping intact (\" for a quote).
    description = (row.get("description") or fm.get("description") or name).strip().replace('\\"', '"')
    if len(description) > 1000:
        description = description[:997] + "..."
    upstream = row.get("source") or ""
    notes = "Aggregated by claudeskills.in from community GitHub lists."
    if upstream and upstream not in ("community", "self", "personal", "test"):
        notes += f" Upstream as recorded by the aggregator: {upstream}."
    tags = ["claudeskills", row.get("category") or "other"]
    if row.get("risk") == "safe":
        tags.append("risk-reviewed")
    atom = {
        "schema": "https://ai-atoms.com/schemas/skill-v1.json",
        "type": "skill",
        "id": f"skill/{slug}",
        "version": "1.0.0",
        "name": name[:80],
        "description": description,
        "system_prompt_fragment": body,
        "applicable_domains": [CATEGORY.get(row.get("category") or "other", "other")],
        "category": CATEGORY.get(row.get("category") or "other", "other"),
        "invocation": [f"/{slug}"],
        "authored_by": fm.get("author") or "claudeskills.in community",
        "source_url": f"{SITE}/skill/{row['name']}",
        "provenance": {
            "source": "claudeskills.in",
            "source_url": f"{SITE}/skill/{row['name']}",
            **({"author": fm["author"]} if fm.get("author") else {}),
            "license": license_for(row, fm),
            "imported_at": TODAY,
            "notes": notes,
        },
        "tags": tags,
        "lifecycle": "draft",
    }
    return atom


def main() -> int:
    if "--from-file" in sys.argv:
        rows = json.loads(Path(sys.argv[sys.argv.index("--from-file") + 1]).read_text())
    else:
        rows = fetch_rows()
    ATOMS_DIR.mkdir(parents=True, exist_ok=True)
    written, skipped_existing, skipped_empty = [], [], []
    for row in sorted(rows, key=lambda r: r["name"]):
        atom = row_to_atom(row)
        if atom is None:
            skipped_empty.append(row["name"])
            continue
        path = ATOMS_DIR / f"{atom['id'].removeprefix('skill/')}.json"
        if path.exists():
            skipped_existing.append(atom["id"])
            continue
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written.append(atom["id"])
    report = {
        "dry_run": DRY_RUN, "rows": len(rows), "written": len(written),
        "skipped_existing": skipped_existing, "skipped_empty": skipped_empty,
        "license_unknown": sum(1 for r in rows if license_for(r, parse_frontmatter(r.get("content") or "")[0]) == "unknown"),
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
