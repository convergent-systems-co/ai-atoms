#!/usr/bin/env python3
"""Resolve `provenance.license: unknown` by reading the upstream repository's license.

claudeskills.in records, for many skills, the GitHub repository the SKILL.md came from
(kept in provenance.notes as "Upstream as recorded by the aggregator: <url>"). For each
such atom this script asks the GitHub API for that repository's detected license and
records the SPDX id. Atoms whose aggregator source is 'community', 'personal', or
'self' have no upstream to ask and stay 'unknown'.

Requires the `gh` CLI to be authenticated. Never overwrites a known license.

Usage: python3 scripts/discover-licenses.py [--dry-run]
"""
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATOMS = REPO / "atoms"
DRY_RUN = "--dry-run" in sys.argv
GITHUB_REPO = re.compile(r"github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+)*?)(?=[/.\s)]|$)")


def repo_license(owner: str, name: str, cache: dict) -> str | None:
    key = f"{owner}/{name}"
    if key in cache:
        return cache[key]
    result = subprocess.run(["gh", "api", f"repos/{owner}/{name}/license", "--jq", ".license.spdx_id"],
                            capture_output=True, text=True, timeout=30)
    spdx = result.stdout.strip() if result.returncode == 0 else None
    if spdx in ("", "NOASSERTION", "null"):
        spdx = None
    cache[key] = spdx
    return spdx


def main() -> int:
    cache: dict = {}
    resolved, still_unknown, no_upstream = [], [], []
    for path in sorted(ATOMS.rglob("*.json")):
        atom = json.loads(path.read_text(encoding="utf-8"))
        prov = atom.get("provenance")
        if not prov or prov.get("license") != "unknown":
            continue
        match = GITHUB_REPO.search(prov.get("notes", ""))
        if not match:
            no_upstream.append(atom["id"])
            continue
        owner, name = match.group(1), match.group(2).removesuffix(".git")
        spdx = repo_license(owner, name, cache)
        if not spdx:
            still_unknown.append(f"{atom['id']} ({owner}/{name})")
            continue
        prov["license"] = spdx
        prov["notes"] = prov["notes"].rstrip(".") + f". License {spdx} read from github.com/{owner}/{name} on 2026-09-03."
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        resolved.append(f"{atom['id']} -> {spdx}")
    print(json.dumps({"dry_run": DRY_RUN, "resolved": resolved, "upstream_without_license": still_unknown,
                      "no_upstream_recorded": len(no_upstream), "repos_queried": cache}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
