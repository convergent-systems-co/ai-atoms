#!/usr/bin/env python3
"""Re-type the staged policy and tool atoms into the policy and tool classes.

PR #46 left three untyped trees: atoms/policy/{boundary,capability,isolation} (from
persona-atoms' knowledge-boundary and behavioural-constraint types and agent-atoms'
role-boundary, capability-declaration, and isolation-constraint types) and
atoms/tool/command (agent-atoms' tool-definition). This script writes one typed atom
per file to atoms/policy/<slug>.json and atoms/tool/<slug>.json. It only writes;
removing the source subdirectories is a separate, deliberate step.

Usage: python3 scripts/migrate-policy-tool.py [--dry-run]
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATOMS = REPO / "atoms"
DRY_RUN = "--dry-run" in sys.argv
GITHUB = "https://github.com/convergent-systems-co"
AUTHOR = "convergent-systems-key"

SECURITY_WORDS = ("secur", "exfil", "network", "exec", "destruct", "secret", "sandbox", "isolation", "code-execution")
DATA_TOOLS = ("sql",)
DEVOPS_TOOLS = ("bash-exec", "http-", "schedule-task", "send-message")


def drop_empty(d: dict) -> dict:
    return {k: v for k, v in d.items() if v not in (None, [], {}, "")}


def category_for_policy(src: dict, slug: str) -> str:
    words = " ".join([slug, *src.get("tags", []), src.get("boundary_type", "")]).lower()
    if any(w in words for w in SECURITY_WORDS):
        return "security"
    if "domain" in slug:
        return {"api-design": "backend", "architecture": "coding", "customer-service": "support", "data-analysis": "data",
                "database-engineering": "backend", "documentation": "knowledge", "infrastructure": "devops",
                "product-management": "product", "research-methodology": "research", "site-reliability": "devops",
                "software-engineering": "coding", "software-testing": "testing", "wcag-accessibility": "design",
                "argumentation-and-logic": "knowledge", "delivery-evidence": "governance", "delivery-platform": "devops",
                "review-orchestration": "governance", "security-review": "security"}.get(slug.removesuffix("-domain"), "governance")
    return "governance"


def policy_from(src: dict, sub: str) -> dict:
    slug = src["id"]
    kind = src["type"]
    if kind == "behavioural-constraint":
        rule = {"text": src["constraint_text"], "boundary_type": "behavioural"}
        effect = src.get("effect", "require")
        description = src.get("description") or src["constraint_text"]
    elif kind == "knowledge-boundary":
        rule = drop_empty({"text": src["boundary_text"], "boundary_type": src.get("boundary_type"),
                           "covered_domains": src.get("covered_domains", []), "excluded_domains": src.get("excluded_domains", [])})
        effect = "bound"
        description = src.get("description") or src["boundary_text"]
    elif kind == "role-boundary":
        b = src["boundary"]
        rule = drop_empty({"text": " ".join(b["refusals"]), "boundary_type": "role-refusal", "refusals": b["refusals"], "escalate_to": b.get("escalate_to")})
        effect = "forbid"
        description = src["description"]
    elif kind == "capability-declaration":
        c = src["capability"]
        rule = drop_empty({"text": src["description"], "grants": c["grants"], "elevation": c["elevation"], "audit": c.get("audit")})
        effect = "permit"
        description = src["description"]
    elif kind == "isolation-constraint":
        i = src["isolation"]
        rule = drop_empty({"text": src["description"], "process": i["process"], "network": i["network"], "filesystem": i["filesystem"], "scoped_paths": i.get("scoped_paths", [])})
        effect = "bound"
        description = src["description"]
    else:
        raise SystemExit(f"unknown policy source type {kind}")
    origin_repo = "persona-atoms" if "persona-atoms" in (src.get("$schema") or src.get("schema") or "") else "agent-atoms"
    return drop_empty(OrderedDict([
        ("schema", "https://ai-atoms.com/schemas/policy-v1.json"), ("type", "policy"), ("id", f"policy/{slug}"),
        ("version", src["version"]), ("name", src["name"]), ("description", description[:1000]),
        ("subtype", sub), ("effect", effect), ("rule", rule), ("rationale", src.get("rationale")),
        ("vendors", src.get("vendors", [])), ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/{origin_repo}/blob/main/atoms/{kind}/{slug}.json"),
        ("category", category_for_policy(src, slug)),
        ("provenance", {"source": f"convergent-systems-co/{origin_repo}", "source_url": f"{GITHUB}/{origin_repo}/blob/main/atoms/{kind}/{slug}.json",
                        "author": "convergent-systems-co", "license": "Apache-2.0", "notes": f"Re-typed from {kind} by scripts/migrate-policy-tool.py."}),
        ("tags", src.get("tags", [])), ("lifecycle", "stable"),
    ]))


def tool_from(src: dict) -> dict:
    slug = src["id"]
    spec = src["tool_spec"]
    category = "data" if any(w in slug for w in DATA_TOOLS) else "devops" if any(w in slug for w in DEVOPS_TOOLS) else "coding"
    return drop_empty(OrderedDict([
        ("schema", "https://ai-atoms.com/schemas/tool-v1.json"), ("type", "tool"), ("id", f"tool/{slug}"),
        ("version", src["version"]), ("name", src["name"]), ("description", src["description"][:1000]),
        ("subtype", "command"),
        ("spec", drop_empty({"function_name": spec["function_name"], "summary": spec["summary"], "parameters": spec.get("parameters", {}),
                             "returns": spec["returns"], "side_effects": spec.get("side_effects", [])})),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/agent-atoms/blob/main/atoms/tool-definition/{slug}.json"),
        ("category", category),
        ("provenance", {"source": "convergent-systems-co/agent-atoms", "source_url": f"{GITHUB}/agent-atoms/blob/main/atoms/tool-definition/{slug}.json",
                        "author": "convergent-systems-co", "license": "Apache-2.0", "notes": "Re-typed from tool-definition by scripts/migrate-policy-tool.py."}),
        ("tags", src.get("tags", [])), ("lifecycle", "stable"),
    ]))


def main() -> int:
    written = {"policy": 0, "tool": 0}
    for sub in ("boundary", "capability", "isolation"):
        for path in sorted((ATOMS / "policy" / sub).glob("*.json")):
            atom = policy_from(json.loads(path.read_text(encoding="utf-8")), sub)
            if not DRY_RUN:
                (ATOMS / "policy" / f"{atom['id'].removeprefix('policy/')}.json").write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
            written["policy"] += 1
    for path in sorted((ATOMS / "tool" / "command").glob("*.json")):
        atom = tool_from(json.loads(path.read_text(encoding="utf-8")))
        if not DRY_RUN:
            (ATOMS / "tool" / f"{atom['id'].removeprefix('tool/')}.json").write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        written["tool"] += 1
    print(json.dumps({"dry_run": DRY_RUN, "written": written}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
