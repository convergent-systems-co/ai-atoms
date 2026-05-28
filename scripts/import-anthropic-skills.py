#!/usr/bin/env python3
"""Import skill atoms from Anthropic's open-source plugin repos.

Sources (both Apache-2.0 where noted):
  anthropics/knowledge-work-plugins  — Apache-2.0, all domains
  anthropics/skills                  — Apache-2.0 skills only
                                       (skips docx/pdf/pptx/xlsx which are source-available only)

Attribution: All imported atoms carry authored_by="anthropics" and a
source_url field pointing to the original SKILL.md on GitHub.

Usage: python3 scripts/import-anthropic-skills.py [--dry-run]
"""
import json
import re
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ATOMS_DIR = REPO_ROOT / "atoms" / "skill"
ATOMS_DIR.mkdir(parents=True, exist_ok=True)

# Source-available (non-OSS) skill dirs in anthropics/skills — skip these
SKIP_ANTHROPIC_SKILLS = {"docx", "pdf", "pptx", "xlsx"}

# Domains in knowledge-work-plugins that have a skills/ sub-directory
KWP_DOMAINS = [
    "bio-research", "customer-support", "data", "design", "engineering",
    "enterprise-search", "finance", "human-resources", "legal", "marketing",
    "operations", "product-management", "productivity", "sales", "small-business",
]

DRY_RUN = "--dry-run" in sys.argv
GITHUB_TOKEN = None
try:
    import subprocess
    result = subprocess.run(["gh", "auth", "token", "--user", "polliard"],
                            capture_output=True, text=True, timeout=5)
    if result.returncode == 0:
        GITHUB_TOKEN = result.stdout.strip()
except Exception:
    pass


def gh_get(path: str):
    url = f"https://api.github.com{path}"
    req = urllib.request.Request(url)
    req.add_header("Accept", "application/vnd.github+json")
    if GITHUB_TOKEN:
        req.add_header("Authorization", f"Bearer {GITHUB_TOKEN}")
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code == 403:  # rate limit
                time.sleep(10 * (attempt + 1))
            else:
                raise
        except Exception:
            time.sleep(2)
    return None


def fetch_file_content(owner: str, repo: str, path: str):
    data = gh_get(f"/repos/{owner}/{repo}/contents/{path}")
    if not data or "content" not in data:
        return None
    import base64
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def list_dir(owner: str, repo: str, path: str) -> list[dict]:
    data = gh_get(f"/repos/{owner}/{repo}/contents/{path}")
    if not isinstance(data, list):
        return []
    return data


def parse_skill_md(content: str) -> dict:
    """Parse a SKILL.md file into {name, description, invocation, body}."""
    frontmatter = {}
    body = content

    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.splitlines():
                if ":" in line:
                    key, _, val = line.partition(":")
                    frontmatter[key.strip()] = val.strip().strip('"')

    return {
        "name": frontmatter.get("name", ""),
        "description": frontmatter.get("description", ""),
        "argument_hint": frontmatter.get("argument-hint", ""),
        "body": body,
    }


def slugify(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9-]", "-", s)
    s = re.sub(r"-+", "-", s)
    return s.strip("-")


def skill_to_atom(parsed: dict, slug: str, source_url: str,
                   domains: list[str], tags: list[str]) -> dict:
    """Convert parsed SKILL.md into a skill atom JSON."""
    name = parsed["name"] or slug.replace("-", " ").title()
    description = parsed["description"] or f"{name} skill from Anthropic."
    if len(description) > 1000:
        description = description[:997] + "..."

    # Build invocation from name
    invocation = [f"/{slug}"]
    if parsed["argument_hint"]:
        invocation.append(f"/{slug} {parsed['argument_hint']}")

    # system_prompt_fragment is the body of the SKILL.md
    system_prompt = parsed["body"].strip()
    if not system_prompt:
        system_prompt = f"Execute the {name} skill as described."

    atom = {
        "schema": "https://ai-atoms.com/schemas/skill-v1.json",
        "type": "skill",
        "id": f"skill/{slug}",
        "version": "1.0.0",
        "name": name,
        "description": description,
        "system_prompt_fragment": system_prompt,
        "applicable_domains": domains,
        "invocation": invocation,
        "tags": tags,
        "authored_by": "anthropics",
        "source_url": source_url,
        "lifecycle": "stable",
    }
    return atom


def write_atom(atom: dict) -> Path:
    slug = atom["id"].removeprefix("skill/")
    path = ATOMS_DIR / f"{slug}.json"
    if path.exists():
        return path  # don't overwrite existing custom atoms
    if not DRY_RUN:
        path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n")
    return path


def import_knowledge_work_plugins() -> int:
    count = 0
    owner, repo = "anthropics", "knowledge-work-plugins"
    print(f"\n{'DRY RUN: ' if DRY_RUN else ''}Importing from {owner}/{repo}...")

    for domain in KWP_DOMAINS:
        skills_path = f"{domain}/skills"
        entries = list_dir(owner, repo, skills_path)
        if not entries:
            skills_path = domain  # some have skills at domain root
            entries = list_dir(owner, repo, domain)

        for entry in entries:
            if entry.get("type") != "dir":
                continue
            skill_name = entry["name"]
            if skill_name.startswith("."):
                continue

            skill_md_path = f"{skills_path}/{skill_name}/SKILL.md"
            content = fetch_file_content(owner, repo, skill_md_path)
            if not content:
                continue

            parsed = parse_skill_md(content)
            slug = slugify(parsed["name"] or skill_name)
            source_url = (
                f"https://github.com/{owner}/{repo}/blob/main/"
                f"{skills_path}/{skill_name}/SKILL.md"
            )

            # Map domain to applicable_domains
            domain_map = {
                "engineering": ["code", "engineering", "architecture"],
                "productivity": ["productivity", "planning"],
                "design": ["design", "ux"],
                "marketing": ["marketing", "content"],
                "sales": ["sales", "crm"],
                "operations": ["operations", "process"],
                "data": ["data", "analytics"],
                "finance": ["finance", "accounting"],
                "human-resources": ["hr", "people"],
                "legal": ["legal", "compliance"],
                "product-management": ["product", "planning"],
                "bio-research": ["research", "science"],
                "small-business": ["business", "operations"],
                "customer-support": ["support", "customer"],
                "enterprise-search": ["search", "knowledge"],
            }
            applicable = domain_map.get(domain, [domain])
            tags = [domain, "anthropics", "knowledge-work"]

            atom = skill_to_atom(parsed, slug, source_url, applicable, tags)
            path = write_atom(atom)
            print(f"  {'[dry] ' if DRY_RUN else ''}{slug} ({domain}/{skill_name})")
            count += 1

    return count


def import_anthropic_skills() -> int:
    count = 0
    owner, repo = "anthropics", "skills"
    print(f"\n{'DRY RUN: ' if DRY_RUN else ''}Importing from {owner}/{repo}...")

    entries = list_dir(owner, repo, "skills")
    for entry in entries:
        if entry.get("type") != "dir":
            continue
        skill_set = entry["name"]
        if skill_set.startswith(".") or skill_set in SKIP_ANTHROPIC_SKILLS:
            if skill_set in SKIP_ANTHROPIC_SKILLS:
                print(f"  SKIP {skill_set} (source-available, not Apache-2.0)")
            continue

        # Each entry may be a single skill or a set with sub-skills
        skill_entries = list_dir(owner, repo, f"skills/{skill_set}")
        skill_md_direct = next(
            (e for e in skill_entries if e.get("name") == "SKILL.md"), None
        )

        if skill_md_direct:
            # Single skill at skills/<name>/SKILL.md
            content = fetch_file_content(owner, repo, f"skills/{skill_set}/SKILL.md")
            if content:
                parsed = parse_skill_md(content)
                slug = slugify(parsed["name"] or skill_set)
                source_url = (
                    f"https://github.com/{owner}/{repo}/blob/main/"
                    f"skills/{skill_set}/SKILL.md"
                )
                atom = skill_to_atom(
                    parsed, slug, source_url,
                    domains=["code", "productivity"],
                    tags=[skill_set, "anthropics", "skills-repo"],
                )
                write_atom(atom)
                print(f"  {'[dry] ' if DRY_RUN else ''}{slug} ({skill_set})")
                count += 1
        else:
            # Skill set with sub-skills
            for sub in skill_entries:
                if sub.get("type") != "dir" or sub["name"].startswith("."):
                    continue
                content = fetch_file_content(
                    owner, repo, f"skills/{skill_set}/{sub['name']}/SKILL.md"
                )
                if not content:
                    continue
                parsed = parse_skill_md(content)
                slug = slugify(parsed["name"] or sub["name"])
                source_url = (
                    f"https://github.com/{owner}/{repo}/blob/main/"
                    f"skills/{skill_set}/{sub['name']}/SKILL.md"
                )
                atom = skill_to_atom(
                    parsed, slug, source_url,
                    domains=["code", "productivity"],
                    tags=[skill_set, sub["name"], "anthropics", "skills-repo"],
                )
                write_atom(atom)
                print(f"  {'[dry] ' if DRY_RUN else ''}{slug} ({skill_set}/{sub['name']})")
                count += 1

    return count


def import_dotnet_skills() -> int:
    """Import from github.com/dotnet/skills (MIT).
    Structure: plugins/<plugin>/skills/<skill>/SKILL.md
    """
    count = 0
    owner, repo = "dotnet", "skills"
    print(f"\n{'DRY RUN: ' if DRY_RUN else ''}Importing from {owner}/{repo}...")

    plugin_entries = list_dir(owner, repo, "plugins")
    for plugin_entry in plugin_entries:
        if plugin_entry.get("type") != "dir":
            continue
        plugin_name = plugin_entry["name"]
        skills_entries = list_dir(owner, repo, f"plugins/{plugin_name}/skills")
        for skill_entry in skills_entries:
            if skill_entry.get("type") != "dir" or skill_entry["name"].startswith("."):
                continue
            skill_name = skill_entry["name"]
            skill_path = f"plugins/{plugin_name}/skills/{skill_name}/SKILL.md"
            content = fetch_file_content(owner, repo, skill_path)
            if not content:
                continue
            parsed = parse_skill_md(content)
            slug = slugify(parsed["name"] or skill_name)
            source_url = (
                f"https://github.com/{owner}/{repo}/blob/main/{skill_path}"
            )
            atom = skill_to_atom(
                parsed, slug, source_url,
                domains=["code", "dotnet", "engineering"],
                tags=[plugin_name, "dotnet", "csharp", "microsoft"],
            )
            path = write_atom(atom)
            print(f"  {'[dry] ' if DRY_RUN else ''}{slug} ({plugin_name}/{skill_name})")
            count += 1
    return count


def import_obsidian_skills() -> int:
    """Import from github.com/kepano/obsidian-skills (MIT).
    Structure: skills/<skill>/SKILL.md
    Attribution: Steph Ango (kepano)
    """
    count = 0
    owner, repo = "kepano", "obsidian-skills"
    print(f"\n{'DRY RUN: ' if DRY_RUN else ''}Importing from {owner}/{repo}...")

    entries = list_dir(owner, repo, "skills")
    for entry in entries:
        if entry.get("type") != "dir" or entry["name"].startswith("."):
            continue
        skill_name = entry["name"]
        content = fetch_file_content(owner, repo, f"skills/{skill_name}/SKILL.md")
        if not content:
            continue
        parsed = parse_skill_md(content)
        slug = slugify(parsed["name"] or skill_name)
        source_url = (
            f"https://github.com/{owner}/{repo}/blob/main/skills/{skill_name}/SKILL.md"
        )
        atom = skill_to_atom(
            parsed, slug, source_url,
            domains=["knowledge", "productivity", "notes"],
            tags=["obsidian", "markdown", "kepano", "knowledge-management"],
        )
        # Override authored_by for proper attribution
        atom["authored_by"] = "kepano"
        path = write_atom(atom)
        print(f"  {'[dry] ' if DRY_RUN else ''}{slug} ({skill_name})")
        count += 1
    return count


def main():
    n1 = import_knowledge_work_plugins()
    n2 = import_anthropic_skills()
    n3 = import_dotnet_skills()
    n4 = import_obsidian_skills()
    total = n1 + n2 + n3 + n4
    print(f"\n{'Would import' if DRY_RUN else 'Imported'}: {total} skill atoms total")
    print(f"  {n1} from anthropics/knowledge-work-plugins (Apache-2.0)")
    print(f"  {n2} from anthropics/skills (Apache-2.0)")
    print(f"  {n3} from dotnet/skills (MIT)")
    print(f"  {n4} from kepano/obsidian-skills (MIT)")


if __name__ == "__main__":
    main()
