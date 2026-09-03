#!/usr/bin/env python3
"""Import skill atoms from claudeskills.in.

claudeskills.in is a community aggregator: it re-hosts SKILL.md files collected
from across the ecosystem. It publishes no license and no terms of use, so
every atom imported here lands with provenance.license = "unknown" unless the
row's own `source` column names an upstream with stated terms.

"unknown" means redistribution has NOT been cleared. These atoms are imported
lifecycle="draft" and tagged "claudeskills.in" so they can be filtered or
pulled back out wholesale if terms are ever clarified.

Attribution: every atom links back to its page on claudeskills.in via
provenance.source_url, and names the upstream repo in provenance.notes when
the aggregator recorded one.

Data comes from the same public Supabase REST endpoint the site's own frontend
reads, using the publishable key shipped in its client bundle.

Usage: python3 scripts/import-claudeskills.py [--dry-run] [--limit N]
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = REPO_ROOT / "atoms" / "skill"
ATOMS_DIR.mkdir(parents=True, exist_ok=True)

SUPABASE_URL = "https://vdduyltnybopajiclwej.supabase.co/rest/v1/skills"
PUBLISHABLE_KEY = "sb_publishable_pKyG2Ak37NtilA9E_2XP0A_ErEQ-EJ2"
SITE = "https://claudeskills.in"
PAGE_SIZE = 200

DRY_RUN = "--dry-run" in sys.argv
LIMIT = None
if "--limit" in sys.argv:
    LIMIT = int(sys.argv[sys.argv.index("--limit") + 1])

# claudeskills.in category -> ai-atoms category enum. Their "other" bucket is
# too heterogeneous to map, so those atoms carry no category.
CATEGORY_MAP = {
    "devops": "operations",
    "frontend": "coding",
    "backend": "coding",
    "security": "governance",
    "ai": "coding",
    "test": "coding",
    "business": "product",
}

DOMAIN_MAP = {
    "devops": ["operations", "devops"],
    "frontend": ["code", "frontend"],
    "backend": ["code", "backend"],
    "security": ["security"],
    "ai": ["code", "agents"],
    "test": ["code", "testing"],
    "business": ["product"],
    "other": ["general"],
}

# Upstream `source` values that state a license explicitly.
KNOWN_LICENSES = {
    "vibeship-spawner-skills (Apache 2.0)": "Apache-2.0",
}

# Aggregator-internal source values that name no upstream.
OPAQUE_SOURCES = {"community", "personal", "self", "test", ""}


def fetch_rows() -> list[dict]:
    rows: list[dict] = []
    offset = 0
    while True:
        url = (f"{SUPABASE_URL}?select=name,category,description,risk,source,content"
               f"&order=name.asc&limit={PAGE_SIZE}&offset={offset}")
        req = urllib.request.Request(url, headers={
            "apikey": PUBLISHABLE_KEY,
            "Authorization": f"Bearer {PUBLISHABLE_KEY}",
        })
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.loads(r.read())
        rows += batch
        if len(batch) < PAGE_SIZE:
            break
        offset += PAGE_SIZE
    return rows


def slugify(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def strip_frontmatter(content: str) -> str:
    """Drop the leading YAML frontmatter block from a SKILL.md body."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            return parts[2].strip()
    return content.strip()


def upstream_of(source: str) -> str | None:
    """Extract an upstream URL from the aggregator's free-text source column."""
    if not source or source in OPAQUE_SOURCES:
        return None
    m = re.search(r"https?://[^\s()]+", source)
    return m.group(0) if m else None


def author_of(upstream: str | None) -> str:
    """Credit the upstream GitHub owner when we can identify one."""
    if upstream:
        m = re.match(r"https?://github\.com/([^/]+)", upstream)
        if m:
            return m.group(1)
    return "claudeskills.in contributors"


def row_to_atom(row: dict, today: str) -> dict | None:
    slug = slugify(row["name"])
    if not slug:
        return None

    body = strip_frontmatter(row.get("content") or "")
    if not body:
        return None

    description = (row.get("description") or f"{row['name']} skill.").strip()
    if len(description) > 1000:
        description = description[:997] + "..."

    name = row["name"][:80]
    category = row.get("category") or "other"
    source = (row.get("source") or "").strip()
    upstream = upstream_of(source)

    note = ("Aggregated by claudeskills.in, which publishes no license or terms of use. "
            "Redistribution is NOT cleared.")
    if upstream:
        note = (f"Aggregated by claudeskills.in from {upstream}. "
                "Verify the upstream license before redistributing.")
    elif source and source not in OPAQUE_SOURCES:
        note = (f"Aggregated by claudeskills.in; upstream recorded as \"{source}\". "
                "Verify the upstream license before redistributing.")
    if len(note) > 500:
        note = note[:497] + "..."

    provenance = {
        "source": "claudeskills.in",
        "source_type": "catalog-site",
        "source_url": f"{SITE}/skill/{row['name']}",
        "author": author_of(upstream),
        "license": KNOWN_LICENSES.get(source, "unknown"),
        "retrieved_at": today,
        "modified": False,
        "notes": note,
    }

    tags = ["claudeskills.in", category]
    if row.get("risk") == "unknown":
        tags.append("unreviewed")

    atom = {
        "schema": "https://ai-atoms.com/schemas/skill-v1.json",
        "type": "skill",
        "id": f"skill/{slug}",
        "version": "1.0.0",
        "name": name,
        "description": description,
        "system_prompt_fragment": body,
        "applicable_domains": DOMAIN_MAP.get(category, ["general"]),
        "invocation": [f"/{slug}"],
        "tags": sorted(set(tags)),
        "authored_by": provenance["author"],
        "source_url": provenance["source_url"],
        "provenance": provenance,
        "lifecycle": "draft",
    }
    if category in CATEGORY_MAP:
        atom["category"] = CATEGORY_MAP[category]
    return atom


def main() -> int:
    today = date.today().isoformat()
    print(f"{'DRY RUN: ' if DRY_RUN else ''}Fetching from claudeskills.in...")
    rows = fetch_rows()
    if LIMIT:
        rows = rows[:LIMIT]
    print(f"  {len(rows)} rows")

    written = skipped_existing = skipped_bad = 0
    collisions: list[str] = []
    for row in rows:
        atom = row_to_atom(row, today)
        if atom is None:
            skipped_bad += 1
            continue
        path = ATOMS_DIR / f"{atom['id'].removeprefix('skill/')}.json"
        if path.exists():
            skipped_existing += 1
            collisions.append(atom["id"])
            continue
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n")
        written += 1

    print(f"\n  written:  {written}")
    print(f"  skipped (id already in catalog): {skipped_existing}")
    print(f"  skipped (empty/unusable):        {skipped_bad}")
    if collisions:
        print("\n  collisions (existing atom kept):")
        for c in sorted(collisions):
            print(f"    {c}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
