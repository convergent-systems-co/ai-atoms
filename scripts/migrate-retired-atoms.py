#!/usr/bin/env python3
"""Re-type the atoms staged by PR #46 into the persona, prompt, and agent classes.

PR #46 copied 293 files verbatim from the retired persona-atoms, agent-atoms,
prompt-atoms, skill-atoms, and workflow-atoms catalogs. Those files carry their
old schemas and were skipped by the catalog build. This script reads them and
writes schema-valid atoms:

  personas/<id>/atom.json  + atoms/agent/persona/ (role-definition)
    + atoms/agent/_facets/ (voice-profile, tone-parameter, work-contract)
    + atoms/policy/boundary/ (behavioural-constraint, knowledge-boundary)
                                            -> atoms/persona/<id>.json
  atoms/agent/actor/<id>.json (agent-atoms "persona" with persona_profile)
                                            -> atoms/persona/<id>.json
                                               atoms/agent/<id>.json (actor)
  agents/<id>.json (agent-atoms compositions) -> atoms/agent/<id>.json
  atoms/prompt/<subtype>/<id>.json            -> atoms/prompt/<id>.json
  prompts/<id>.json (prompt-atoms compositions)
                                            -> atoms/prompt/<id>-bundle.json

Facet, constraint, and boundary text is inlined into each persona so a persona is
self-contained. References that cannot be resolved are reported, never invented.

The script only writes. Removing the source files is a separate, deliberate step
(see docs/adr/0001-prompt-agent-persona-classes.md).

Usage: python3 scripts/migrate-retired-atoms.py [--dry-run]
Prints a JSON gap report to stdout.
"""
import json
import sys
from collections import OrderedDict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ATOMS = REPO / "atoms"
DRY_RUN = "--dry-run" in sys.argv

AUTHOR = "convergent-systems-key"
GITHUB = "https://github.com/convergent-systems-co"
SCHEMA = {
    "persona": "https://ai-atoms.com/schemas/persona-v1.json",
    "prompt": "https://ai-atoms.com/schemas/prompt-v1.json",
    "agent": "https://ai-atoms.com/schemas/agent-v1.json",
}

# Retired subtype names -> prompt-v1 subtype enum.
PROMPT_SUBTYPE = {
    "persona": "persona",
    "constraint": "constraint",
    "format-instruction": "format",
    "output-schema": "output-schema",
    "refusal-pattern": "refusal",
    "tool-use-template": "tool-use",
}
# Order in which a prompt composition's parts are concatenated.
COMPOSITE_ORDER = (
    "persona", "constraints", "format_instruction", "tool_use_template",
    "refusal_patterns", "output_schema",
)
# agent-atoms persona_profile vocabulary -> agent-v1 execution enums.
PLANNER = {"react": "react", "plan-and-execute": "plan-and-execute", "tree-of-thoughts": "tree-of-thoughts", "none": "none"}
MEMORY = {"scratchpad": "scratchpad", "short-term": "short-term", "long-term": "long-term", "vector": "vector", "none": "none"}
# persona-atoms voice-profile field name differs from persona-v1.
VOICE_FIELDS = {"formality": "formality", "hedging_tolerance": "hedging_tolerance", "sentence_length_preference": "sentence_length"}
WORK_CONTRACT_FIELDS = (
    "class", "goal", "inputs", "allowed_actions", "forbidden_actions", "output_artifacts",
    "handoff_targets", "escalation_triggers", "done_criteria", "decision_scope",
)

gaps: list[dict] = []


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_dir(pattern: str) -> dict[str, dict]:
    return {d["id"]: d for d in (load(p) for p in sorted(ATOMS.glob(pattern)))}


def ref_slug(ref: str) -> str:
    """'persona-atoms://atoms/role-definition/coder' -> 'coder'."""
    return ref.rsplit("/", 1)[-1]


def gap(atom_id: str, field: str, ref: str, effect: str) -> None:
    gaps.append({"atom": atom_id, "field": field, "unresolved": ref, "effect": effect})


def write(atom: dict, path: Path) -> None:
    if DRY_RUN:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(atom, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def drop_empty(atom: dict) -> dict:
    return {k: v for k, v in atom.items() if v not in (None, [], {}, "")}


# ---------------------------------------------------------------- personas

def persona_from_composition(comp: dict, role_defs: dict, actors: dict, facets: dict, boundaries: dict) -> dict:
    pid = comp["id"]
    atom_id = f"persona/{pid}"

    role: dict = {}
    rd_ref = ref_slug(comp["role_definition"]["ref"])
    rd = role_defs.get(rd_ref)
    if rd:
        role = drop_empty({
            "job_to_be_done": rd["job_to_be_done"],
            "primary_tasks": rd.get("primary_tasks", []),
            "out_of_scope": rd.get("out_of_scope", []),
            "domain": rd.get("domain") or comp.get("domain"),
        })
    else:
        gap(atom_id, "role_definition", rd_ref, "role.job_to_be_done taken from the composition description")
        role = drop_empty({"job_to_be_done": comp["description"], "domain": comp.get("domain")})

    voice: dict = {}
    actor = actors.get(pid)
    if actor:
        profile = actor["persona_profile"]
        role["expertise"] = profile.get("expertise", [])
        voice["style_notes"] = profile.get("voice")
    vp = facets.get(("voice-profile", ref_slug(comp["voice_profile"]["ref"])))
    if vp:
        voice.update({new: vp[old] for old, new in VOICE_FIELDS.items() if old in vp})
    else:
        gap(atom_id, "voice_profile", ref_slug(comp["voice_profile"]["ref"]), "voice omitted")

    tone: dict = {}
    tp = facets.get(("tone-parameter", ref_slug(comp["tone_parameters"]["ref"])))
    if tp:
        tone = {k: tp[k] for k in ("warmth", "directness") if k in tp}
    else:
        gap(atom_id, "tone_parameters", ref_slug(comp["tone_parameters"]["ref"]), "tone omitted")

    work_contract: dict = {}
    if "work_contract" in comp:
        wc = facets.get(("work-contract", ref_slug(comp["work_contract"]["ref"])))
        if wc:
            work_contract = drop_empty({k: wc.get(k) for k in WORK_CONTRACT_FIELDS})
        else:
            gap(atom_id, "work_contract", ref_slug(comp["work_contract"]["ref"]), "work_contract omitted")

    constraints = []
    for ref in comp.get("behavioural_constraints", []):
        slug = ref_slug(ref["ref"])
        bc = boundaries.get(("behavioural-constraint", slug))
        if bc:
            constraints.append(drop_empty({"name": bc["name"], "text": bc["constraint_text"], "effect": bc.get("effect")}))
        else:
            gap(atom_id, "behavioural_constraints", slug, "constraint omitted")

    knowledge_boundaries = []
    for ref in comp.get("knowledge_boundaries", []):
        slug = ref_slug(ref["ref"])
        kb = boundaries.get(("knowledge-boundary", slug))
        if kb:
            knowledge_boundaries.append(drop_empty({
                "name": kb["name"], "text": kb["boundary_text"],
                "covered_domains": kb.get("covered_domains", []),
                "excluded_domains": kb.get("excluded_domains", []),
            }))
        else:
            gap(atom_id, "knowledge_boundaries", slug, "boundary omitted")

    brand_ref = None
    if "extends_brand" in comp:
        brand_ref = comp["extends_brand"]["ref"].replace("brand-atoms://", "brand-atoms.com/")

    return drop_empty(OrderedDict([
        ("schema", SCHEMA["persona"]),
        ("type", "persona"),
        ("id", atom_id),
        ("version", comp["version"]),
        ("name", comp["name"]),
        ("description", comp["description"]),
        ("role", role),
        ("voice", drop_empty(voice)),
        ("tone", tone),
        ("work_contract", work_contract),
        ("constraints", constraints),
        ("knowledge_boundaries", knowledge_boundaries),
        ("system_prompt_fragment", comp.get("system_prompt_template")),
        ("brand_ref", brand_ref),
        ("vendors", comp.get("vendors", [])),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/persona-atoms/blob/main/personas/{pid}/atom.json"),
        ("tags", comp.get("tags", [])),
        ("lifecycle", comp.get("lifecycle", "draft")),
    ]))


def persona_from_actor(actor: dict) -> dict:
    """agent-atoms 'persona' atoms carry identity (role, expertise, voice) — that is a persona."""
    profile = actor["persona_profile"]
    return drop_empty(OrderedDict([
        ("schema", SCHEMA["persona"]),
        ("type", "persona"),
        ("id", f"persona/{actor['id']}"),
        ("version", actor["version"]),
        ("name", actor["name"]),
        ("description", actor["description"]),
        ("role", drop_empty({"job_to_be_done": f"{profile['role']}. {actor['description']}", "expertise": profile.get("expertise", [])})),
        ("voice", drop_empty({"style_notes": profile.get("voice")})),
        ("vendors", ["any"]),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/agent-atoms/blob/main/atoms/persona/{actor['id']}.json"),
        ("tags", actor.get("tags", [])),
        ("lifecycle", "draft"),
    ]))


# ------------------------------------------------------------------ agents

def policy_refs(comp_refs: dict) -> list[str]:
    out: list[str] = []
    for key in ("capabilities", "role_boundaries"):
        out.extend(f"policy/{ref_slug(r['ref'])}" for r in comp_refs.get(key, []))
    if "isolation" in comp_refs:
        out.append(f"policy/{ref_slug(comp_refs['isolation']['ref'])}")
    return out


def agent_from_actor(actor: dict, composition: dict | None) -> dict:
    profile = actor["persona_profile"]
    execution = drop_empty({
        "planner": PLANNER.get(profile.get("planner")),
        "memory": MEMORY.get(profile.get("memory_model")),
        "supervisor": profile.get("supervisor"),
    })
    for field, table in (("planner", PLANNER), ("memory_model", MEMORY)):
        if profile.get(field) and profile[field] not in table:
            gap(f"agent/{actor['id']}", f"execution.{field}", profile[field], "value outside agent-v1 enum, omitted")

    refs = (composition or {}).get("references", {})
    tools = [f"tool/{ref_slug(t['ref'])}" for t in refs.get("tools", [])]
    tags = list(dict.fromkeys(actor.get("tags", []) + (composition or {}).get("tags", [])))
    agent_id = (composition or actor)["id"]
    source_path = f"agents/{agent_id}.json" if composition else f"atoms/persona/{actor['id']}.json"
    return drop_empty(OrderedDict([
        ("schema", SCHEMA["agent"]),
        ("type", "agent"),
        ("id", f"agent/{agent_id}"),
        ("version", (composition or actor)["version"]),
        ("name", (composition or actor)["name"]),
        ("description", (composition or actor)["description"]),
        ("subtype", "actor"),
        ("persona", f"persona/{actor['id']}"),
        ("tools", tools),
        ("policies", policy_refs(refs)),
        ("execution", execution),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/agent-atoms/blob/main/{source_path}"),
        ("tags", tags),
        ("lifecycle", "draft"),
    ]))


# ----------------------------------------------------------------- prompts

def prompt_from_atom(src: dict) -> dict:
    subtype = PROMPT_SUBTYPE[src["type"]]
    persona_ref = None
    if src.get("persona_ref"):
        persona_ref = f"persona/{ref_slug(src['persona_ref'])}"
    return drop_empty(OrderedDict([
        ("schema", SCHEMA["prompt"]),
        ("type", "prompt"),
        ("id", f"prompt/{src['id']}"),
        ("version", src["version"]),
        ("name", src["name"]),
        ("description", src["description"]),
        ("subtype", subtype),
        ("content", src["content"]),
        ("applicable_turns", src.get("applicable_turns", [])),
        ("vendors", src.get("vendors", [])),
        ("persona_ref", persona_ref),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/prompt-atoms/blob/main/atoms/{src['type']}/{src['id']}.json"),
        ("tags", src.get("tags", [])),
        ("lifecycle", "draft"),
    ]))


def prompt_bundle(comp: dict, prompts_by_id: dict) -> dict:
    """A prompt-atoms composition becomes a composite prompt with resolved content."""
    bundle_id = f"prompt/{comp['id']}-bundle"
    includes: list[str] = []
    for key in COMPOSITE_ORDER:
        value = comp["references"].get(key)
        if not value:
            continue
        for ref in (value if isinstance(value, list) else [value]):
            pid = f"prompt/{ref_slug(ref['ref'])}"
            if pid in prompts_by_id:
                includes.append(pid)
            else:
                gap(bundle_id, f"references.{key}", pid, "part omitted from bundle")
    content = "\n\n".join(prompts_by_id[i]["content"] for i in includes)
    return drop_empty(OrderedDict([
        ("schema", SCHEMA["prompt"]),
        ("type", "prompt"),
        ("id", bundle_id),
        ("version", comp["version"]),
        ("name", comp["name"]),
        ("description", comp["description"]),
        ("subtype", "composite"),
        ("content", content),
        ("applicable_turns", ["system"]),
        ("vendors", comp.get("vendors", [])),
        ("includes", includes),
        ("authored_by", AUTHOR),
        ("source_url", f"{GITHUB}/prompt-atoms/blob/main/prompts/{comp['id']}.json"),
        ("tags", comp.get("tags", [])),
        ("lifecycle", "draft"),
    ]))


# -------------------------------------------------------------------- main

def main() -> int:
    role_defs = load_dir("agent/persona/*.json")
    actors = load_dir("agent/actor/*.json")
    facets = {(d["type"], d["id"]): d for d in (load(p) for p in sorted(ATOMS.glob("agent/_facets/*/*.json")))}
    boundaries = {(d["type"], d["id"]): d for d in (load(p) for p in sorted(ATOMS.glob("policy/boundary/*.json")))}
    compositions = [load(p) for p in sorted((REPO / "personas").glob("*/atom.json"))]
    agent_compositions = {load(p)["id"]: load(p) for p in sorted((REPO / "agents").glob("*.json"))}
    prompt_sources = [load(p) for p in sorted(ATOMS.glob("prompt/*/*.json"))]
    prompt_compositions = [load(p) for p in sorted((REPO / "prompts").glob("*.json"))]

    written: dict[str, list[str]] = {"persona": [], "agent": [], "prompt": []}
    skipped: list[str] = []

    # Personas: compositions first (richest), then actors that have no composition of the same id.
    for comp in compositions:
        if comp["id"] == "persona-template":
            skipped.append("personas/TEMPLATE/atom.json (template, not an atom)")
            continue
        atom = persona_from_composition(comp, role_defs, actors, facets, boundaries)
        write(atom, ATOMS / "persona" / f"{comp['id']}.json")
        written["persona"].append(atom["id"])
    composition_ids = {c["id"] for c in compositions}
    for actor_id, actor in actors.items():
        if actor_id in composition_ids:
            continue  # identity merged into the composition-derived persona above
        atom = persona_from_actor(actor)
        write(atom, ATOMS / "persona" / f"{actor_id}.json")
        written["persona"].append(atom["id"])

    # Agents: one per actor; agent-atoms compositions attach tools/policies or become their own agent.
    consumed_compositions: set[str] = set()
    for actor_id, actor in actors.items():
        comp = agent_compositions.get(actor_id)
        if comp is not None:
            consumed_compositions.add(actor_id)
        atom = agent_from_actor(actor, comp)
        write(atom, ATOMS / "agent" / f"{actor_id}.json")
        written["agent"].append(atom["id"])
    for comp_id, comp in agent_compositions.items():
        if comp_id in consumed_compositions:
            continue
        actor_slug = ref_slug(comp["references"]["persona"]["ref"])
        actor = actors.get(actor_slug)
        if actor is None:
            gap(f"agent/{comp_id}", "references.persona", actor_slug, "agent not written")
            continue
        atom = agent_from_actor(actor, comp)
        write(atom, ATOMS / "agent" / f"{comp_id}.json")
        written["agent"].append(atom["id"])

    # Prompts: flatten subtype directories, then bundles.
    prompts_by_id: dict[str, dict] = {}
    for src in prompt_sources:
        if src["id"] == "persona-template":
            skipped.append("atoms/prompt/persona/persona-template.json (template, not an atom)")
            continue
        if not src.get("content", "").strip():
            # A prompt with nothing to inject is not a prompt; the 'none' persona already
            # models pass-through. Dropping it is a data decision, so it is reported.
            skipped.append(f"atoms/prompt/{src['type']}/{src['id']}.json (empty content)")
            continue
        atom = prompt_from_atom(src)
        if atom["id"] in prompts_by_id:
            raise SystemExit(f"slug collision across prompt subtypes: {atom['id']}")
        prompts_by_id[atom["id"]] = atom
    for atom in prompts_by_id.values():
        write(atom, ATOMS / "prompt" / f"{atom['id'].split('/')[1]}.json")
        written["prompt"].append(atom["id"])
    for comp in prompt_compositions:
        atom = prompt_bundle(comp, prompts_by_id)
        write(atom, ATOMS / "prompt" / f"{atom['id'].split('/')[1]}.json")
        written["prompt"].append(atom["id"])

    report = {
        "dry_run": DRY_RUN,
        "written": {k: len(v) for k, v in written.items()},
        "skipped": skipped,
        "gaps": gaps,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
