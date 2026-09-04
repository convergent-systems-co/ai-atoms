#!/usr/bin/env python3
"""Import the house document templates from ~/.ai/templates/*.md as template atoms.

The house files use free-form placeholders — `{{one sentence: the single job…}}` — and,
in the MADR file, single-brace `{…}`. template-v1 wants each placeholder named
(`{{snake_case}}`) and declared once with a description. This importer:

  - turns every placeholder into a snake_case name derived from its leading words
    (with an override table for the ones that deserve a better name),
  - keeps the placeholder's original text as the placeholder description,
  - keeps the file's HTML comments and prose in the body verbatim,
  - maps the same placeholder text to the same name wherever it repeats.

Re-running it after editing a house file updates the atom and bumps the patch version.

Usage: python3 scripts/import-house-templates.py [--dry-run] [--dir ~/.ai/templates]
"""
import json
import os
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "atoms" / "template"
DRY_RUN = "--dry-run" in sys.argv
SRC = Path(sys.argv[sys.argv.index("--dir") + 1] if "--dir" in sys.argv else os.path.expanduser("~/.ai/templates"))

# Which house file becomes which atom, and the facts the file itself does not carry.
FILES = {
    "adr.md": {
        "slug": "adr", "name": "Architecture Decision Record (MADR 4.0.0)", "subtype": "adr", "category": "governance",
        "description": "The MADR 4.0.0 decision-record template: metadata, context and problem statement, decision drivers, considered options, decision outcome with consequences and confirmation, pros and cons per option, more information. One file per decision under docs/adr/. Sections marked optional in the comments may be deleted.",
        "rules": ["Never edit an accepted ADR; write a new one that supersedes it.", "Every non-trivial decision gets an ADR before the conversation that made it ends.", "Delete an optional section rather than leave its heading empty."],
        "produced_by": ["skill/architecture", "skill/amendment-author"], "tags": ["adr", "madr", "decision", "required-document"],
        "provenance": {"source": "adr/madr", "source_url": "https://adr.github.io/madr/", "author": "MADR project", "license": "MIT",
                       "notes": "Template text is MADR 4.0.0 (github.com/adr/madr, MIT), carried in ~/.ai/templates/adr.md; placeholders renamed to template-v1's {{snake_case}} form with the original guidance kept as each placeholder's description."},
        "brace": "both",
    },
    "agent.md": {
        "slug": "agent", "name": "Agent Definition (task-executing persona)", "subtype": "agent", "category": "governance",
        "description": "Template for an autonomous, one-shot subagent: frontmatter (name, description, tool allowlist, model), a numbered job, ranked priorities for when instructions conflict, shared-worktree discipline, a STATUS report contract, worked examples, red flags, a machine-readable RESULT_JSON line, and a capacity rule. For a conversational persona with a voice, use template/persona instead.",
        "rules": ["Fill every placeholder; delete an optional section rather than leave its heading empty.", "The tools allowlist is never omitted.", "End with exactly one RESULT_JSON line, not wrapped in a code fence."],
        "produced_by": ["skill/dispatching-parallel-agents", "skill/skill-creator"], "tags": ["agent", "subagent", "persona", "claude-code"],
        "provenance": {"source": "~/.ai/templates", "author": "convergent-systems-co", "license": "CC-BY-4.0",
                       "notes": "House template. The ranked-priorities and worked-examples sections are adapted, as plain prose, from the Soul.md persona spec (github.com/rokoss21/soul.md); nothing else from that spec is used."},
        "brace": "double",
    },
    "persona.md": {
        "slug": "persona", "name": "Persona Definition (conversational character)", "subtype": "persona", "category": "governance",
        "description": "Template for a conversational, character-driven persona that holds a voice across many turns: who you are, how you speak, always/never behaviours, situation handling, how you think, ranked priorities, what is fixed versus what can shift, hard limits, staying in character under pressure, example exchanges, reading list, permitted change, and a closing restatement of the limits that never bend. For a one-shot task worker use template/agent.",
        "rules": ["'Hard limits' and 'Above all' are never optional and always win over staying in character.", "Every behaviour must be checkable against a transcript, not a vibe.", "Restate the least-negotiable limits verbatim at the very end; recency matters."],
        "produced_by": ["skill/skill-creator"], "tags": ["persona", "character", "voice", "claude-code"],
        "provenance": {"source": "~/.ai/templates", "author": "convergent-systems-co", "license": "CC-BY-4.0",
                       "notes": "House template. The ranked-priorities and example-exchanges sections are adapted, as plain prose, from the Soul.md persona spec (github.com/rokoss21/soul.md); nothing else from that spec is used."},
        "brace": "double",
    },
}

# Placeholder text (exact, as it appears in the file) -> preferred snake_case name.
OVERRIDES = {
    "persona-name, kebab-case, unique among sibling personas": "name",
    "Persona Name": "persona_name",
    "Name": "name",
    "model tier": "model",
    "name of the pipeline/system": "system",
    "...": "item",
    "…": "item",
    "short title, representative of solved problem and found solution": "title",
    "YYYY-MM-DD when the decision was last updated": "date",
    "proposed | rejected | accepted | deprecated | … | superseded by ADR-0123": "status",
    "list everyone involved in the decision": "decision_makers",
    "title of option 1": "option_1",
    "title of option 2": "option_2",
    "title of option 3": "option_3",
    "title of other option": "other_option",
}
# Nested single-brace placeholders MADR uses inside a placeholder; flattened before conversion.
PRESUB = {
    "adr.md": [("{justification. e.g., only option, which meets k.o. criterion decision driver | which resolves force {force} | … | comes out best (see below)}",
                "{{justification}}"),
               # The header comment names the placeholder syntax itself; keep it as prose.
               ("Every {{...}}/{...} placeholder", "Every @@SYNTAX@@ placeholder")],
}
POSTSUB = {"adr.md": [("@@SYNTAX@@", "{{...}}/{...}")]}
# Auto-derived name -> the name a reader would choose. Applied after derivation, per file.
RENAME = {
    "adr.md": {"item": "more", "list_everyone_whose": "consulted", "list_everyone_who": "informed", "describe_context_problem": "context",
               "positive_consequence_improvement": "good_consequence", "negative_consequence_compromising": "bad_consequence",
               "describe_how_implementation": "confirmation", "example_description_pointer": "option_details", "argument": "argument_a",
               "might_want_provide": "more_information"},
    "agent.md": {"item": "fill", "one_sentence_single": "description", "explicit_allowlist_never": "tools", "one_two_sentences": "mandate",
                 "first_step_read": "step_read_inputs", "core_step_s": "step_core", "verification_step_how": "step_verify",
                 "self_review_step": "step_self_review", "short_ranked_list": "priorities", "where_dispatch_tells": "worktree_context",
                 "field": "report_field", "what_persona_must": "report_value", "specific_kind_input": "needs_context_when",
                 "specific_way_job": "blocked_when", "completed_but": "concerns_when", "p_2_4_short": "worked_examples",
                 "persona_specific_prohibition": "red_flag_1", "persona_specific_prohibition_2": "red_flag_2"},
    "persona.md": {"item": "fill", "role_title_useful": "role", "p_3_6_sentences": "who_you_are", "tone_formality_verbosity": "how_you_speak",
                   "specific_situation": "situation_1", "short_realistic_line": "line_1", "different_situation_ideally": "situation_2",
                   "concrete_checkable_behaviors": "behaviours", "connect_recognizable_situation": "situations_intro", "what_do": "action",
                   "concrete_action": "example_action", "situation_where_should": "refusal_situation", "what_do_instead": "refusal_action",
                   "default_approach_new": "how_you_think", "short_ranked_list": "priorities", "core_identity_values": "fixed",
                   "tone_emphasis_style": "can_shift", "mood_urgency_register": "varies", "absolute_safety_boundaries": "hard_limits",
                   "how_remain_recognizably": "under_pressure", "p_3_6_short": "example_exchanges", "list_paths_relative": "reading_list",
                   "whether_persona_may": "change_policy", "restate_up_4": "above_all"},
}
# One rendered illustration per template. These are about this catalog and were written to
# show the shape; they are not records of real decisions, agents, or characters.
EXAMPLES = {
    "adr": """---
status: "proposed"
date: 2026-09-03
decision-makers: catalog steward
consulted: none
informed: contributors
---

# Add a template class for documents a runtime renders

## Context and Problem Statement

An agent told to write an ADR, runbook, or handoff had no skeleton to fill; two prompt atoms described those shapes in prose. Should document skeletons be a class of their own, a prompt subtype, or stay outside the catalog?

## Decision Drivers

* Rendering a document by filling placeholders is a distinct runtime action from injecting text.
* The constitution mandates fixed section sets for several documents.
* Blank atom files for authoring had already polluted the catalog once.

## Considered Options

* A new template class
* A template subtype of prompt
* Keep describing shapes in prompt/output-schema prose

## Decision Outcome

Chosen option: "A new template class", because it is the only option that carries placeholders and a rendered example, and the runtime action is distinct.

### Consequences

* Good, because a runtime can fill a skeleton instead of guessing a shape.
* Bad, because the catalog has a ninth class and the navigation grows.

### Confirmation

The build rejects a template whose body and placeholder list disagree; scripts/tests cover it.

## Pros and Cons of the Options

### A new template class

* Good, because placeholders are typed and checked.
* Bad, because it is one more schema to maintain.

### A template subtype of prompt

* Good, because no new class.
* Bad, because a prompt has no place for placeholders or a rendered example.

## More Information

See docs/adr/0004-template-class.md in convergent-systems-co/ai-atoms.
""",
    "agent": """---
name: catalog-validator
description: Validates one atom JSON file against its class schema and reports the exact errors. Does NOT fix the file — that is the author's job.
tools: Read, Bash
model: fast
---

You are the Catalog Validator persona in the ai-atoms publish pipeline. Your single mandate is to say whether one atom file is valid and, if not, exactly why. You do not edit atoms or judge their content — that is the reviewer's job. Stay narrow.

## Your job

1. Read the atom file named in your dispatch and the schema its `schema` field points at.
2. Run `python3 scripts/build-exports.py` in a scratch copy containing only that atom and report every validation error verbatim with its JSON path.
3. Confirm the run's exit code matches your verdict: 0 for valid, 1 for invalid.
4. Check that your report names only the file you were given.

## What you optimize for, when it conflicts

1. Reporting every error over reporting quickly.
2. Quoting the validator's message over paraphrasing it.

## Report contract

End your final message with exactly this shape:

```
STATUS: DONE
File: the path you validated
Errors: count, or 0
```

Use `STATUS: NEEDS_CONTEXT` if the file's `schema` URL names a class this repository has no schema for. Use `STATUS: BLOCKED` if the file is not JSON at all.

## Red flags — never do these

- Never edit the atom to make it pass.
- Never report "valid" without a zero exit code to prove it.
- Never hardcode a secret, API key, token, or credential.

## Machine-readable result

RESULT_JSON: {"status":"DONE","summary":"atoms/skill/commit.json validates against skill-v1","evidence":["exit 0"],"artifacts":[],"concerns":[],"missing_context":[],"blockers":[],"findings":[],"commands":["python3 scripts/build-exports.py"]}
""",
    "persona": """# You are Atlas

You are **Atlas**, the guide to the ai-atoms catalog. You think, decide, and respond as Atlas. The rules below are who you are — but they never override your underlying safety limits, which always come first.

## Who you are

You help people find, understand, and install atoms from ai-atoms.com. You know the nine classes, what each one is for, and how the ids resolve. You do not write new atoms for people and you do not guess at licenses; when the catalog says `unknown`, so do you.

## How you speak

Plain, short, specific. You name the atom id and the URL. When someone asks for something the catalog does not have, you say so and point at the builder.

**You sound like this:**
- When someone asks how to add a skill to Claude Code, you say: "Copy the SKILL.md from /atoms/skill/commit/ into .claude/skills/commit/ — or run `ai skills install commit`."
- When someone asks you to vouch for an unknown-license atom, you say: "The source states no license. I can't call it clear for commercial use; here is the provenance so you can check."

## What you always do, and what you never do

**Always:**
- Give the atom id and its JSON URL.
- Show the license chip when it is `unknown`.

**Never:**
- Invent an atom that is not in the catalog.
- Claim a license the provenance does not state.

## Hard limits — never overridden

You never fabricate ids, licenses, or authors. You never tell someone to disable a hook to get past a guard.

## Above all

- You never fabricate ids, licenses, or authors.
- You never tell someone to disable a hook to get past a guard.
""",
}
STOP = {"a", "an", "the", "of", "to", "in", "for", "and", "or", "e", "g", "this", "that", "your", "you", "is", "it", "on", "with", "as", "if"}


def slug_name(text: str, taken: set[str]) -> str:
    if text in OVERRIDES:
        base = OVERRIDES[text]
    else:
        words = [w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP][:3]
        base = "_".join(words) or "field"
        if base[0].isdigit():
            base = "p_" + base
    name, n = base, 2
    while name in taken:
        name, n = f"{base}_{n}", n + 1
    return name


def convert(text: str, brace: str, filename: str = "") -> tuple[str, list[dict]]:
    """Replace free-form placeholders with {{snake_case}} and collect declarations in order."""
    for old, new in PRESUB.get(filename, []):
        assert old in text, f"{filename}: expected nested placeholder not found; the house file changed"
        text = text.replace(old, new)
    pattern = re.compile(r"\{\{(.+?)\}\}" + (r"|\{([^{}\n]+?)\}" if brace == "both" else ""), re.S)
    names: dict[str, str] = {}
    declared: list[dict] = []
    taken: set[str] = set()

    def sub(m: re.Match) -> str:
        raw = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
        key = re.sub(r"\s+", " ", raw)
        if key not in names:
            name = slug_name(key, taken)
            taken.add(name)
            names[key] = name
            declared.append({"name": name, "description": key})
        return "{{" + names[key] + "}}"

    body = pattern.sub(sub, text)
    for old, new in RENAME.get(filename, {}).items():
        if any(d["name"] == old for d in declared):
            body = body.replace("{{" + old + "}}", "{{" + new + "}}")
            for d in declared:
                if d["name"] == old:
                    d["name"] = new
    assert len({d["name"] for d in declared}) == len(declared), f"{filename}: rename produced a duplicate placeholder name"
    for old, new in POSTSUB.get(filename, []):
        body = body.replace(old, new)
    return body, declared


def bump(version: str) -> str:
    major, minor, patch = version.split(".")[:3]
    return f"{major}.{minor}.{int(patch) + 1}"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for filename, meta in FILES.items():
        src = SRC / filename
        if not src.exists():
            report.append(f"{filename}: missing")
            continue
        body, placeholders = convert(src.read_text(encoding="utf-8"), meta["brace"], filename)
        path = OUT / f"{meta['slug']}.json"
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
        atom = {
            "schema": "https://ai-atoms.com/schemas/template-v1.json", "type": "template", "id": f"template/{meta['slug']}",
            "version": bump(previous["version"]) if previous and previous.get("body") != body else (previous["version"] if previous else "1.0.0"),
            "name": meta["name"], "description": meta["description"], "subtype": meta["subtype"], "format": "markdown",
            "body": body, "placeholders": placeholders,
            **({"example": EXAMPLES[meta["slug"]]} if meta["slug"] in EXAMPLES else {}),
            "rules": meta["rules"], "produced_by": meta["produced_by"], "authored_by": "convergent-systems-key",
            "source_url": meta["provenance"].get("source_url", f"file://~/.ai/templates/{filename}"),
            "category": meta["category"], "provenance": meta["provenance"], "tags": meta["tags"], "lifecycle": "stable",
        }
        if not DRY_RUN:
            path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        report.append(f"{filename} -> {atom['id']} v{atom['version']}: {len(placeholders)} placeholders")
    print("\n".join(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
