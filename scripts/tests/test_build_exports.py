"""Behavioural tests for scripts/build-exports.py.

Each test builds a throwaway atoms tree so it exercises the validator the way CI
does, without touching the real catalog.
"""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
SCHEMA_DIR = REPO / "schemas"

spec = importlib.util.spec_from_file_location("build_exports", REPO / "scripts" / "build-exports.py")
build_exports = importlib.util.module_from_spec(spec)
sys.modules["build_exports"] = build_exports
spec.loader.exec_module(build_exports)


def envelope(cls: str, slug: str, defaults: dict, **fields) -> dict:
    """Minimal valid atom of `cls`; `fields` override `defaults` so tests can break one thing."""
    atom = {
        "schema": f"https://ai-atoms.com/schemas/{cls}-v1.json",
        "type": cls,
        "id": f"{cls}/{slug}",
        "version": "1.0.0",
        "name": slug.replace("-", " ").title(),
        "description": f"Fixture {cls} atom.",
    }
    atom.update(defaults)
    atom.update(fields)
    return atom


def persona(slug="staff-engineer", **fields):
    return envelope("persona", slug, {"role": {"job_to_be_done": "Ship durable software."}}, **fields)


def prompt(slug="no-fabrication", **fields):
    return envelope("prompt", slug, {"subtype": "constraint", "content": "Never fabricate."}, **fields)


def agent(slug="tech-lead", **fields):
    return envelope("agent", slug, {"subtype": "actor", "persona": "persona/staff-engineer"}, **fields)


def skill(slug="commit", **fields):
    return envelope("skill", slug, {"system_prompt_fragment": "Write a commit.", "applicable_domains": ["git"]}, **fields)


def model(slug="llama3.2", **fields):
    return envelope("model", slug, {"vendor": "Meta", "task": "text-generation",
                                    "providers": [{"name": "Ollama", "model_id": "llama3.2", "url": "https://ollama.com/library/llama3.2"}]}, **fields)


def policy(slug="read-only-workspace", **fields):
    return envelope("policy", slug, {"subtype": "capability", "effect": "permit",
                                     "rule": {"text": "Read files only.", "grants": ["read-files"], "elevation": "declared"}}, **fields)


def tool(slug="git-diff", **fields):
    return envelope("tool", slug, {"subtype": "command", "spec": {"function_name": "git_diff", "summary": "Show a diff.",
                                   "parameters": {"ref": {"type": "string", "description": "Ref to diff against", "required": False}},
                                   "returns": {"type": "string", "description": "Unified diff"}, "side_effects": ["fs-read"]}}, **fields)


def template(slug="adr", **fields):
    return envelope("template", slug, {"subtype": "adr", "format": "markdown", "body": "# {{title}}\n\n{{context}}\n",
                                       "placeholders": [{"name": "title", "description": "Decision title"}, {"name": "context", "description": "Forces"}]}, **fields)


def hook(slug="branch-guard", **fields):
    return envelope("hook", slug, {"event": "PreToolUse", "language": "python", "trigger": {"type": "always"}}, **fields)


def bundle(slug="develop", **fields):
    return envelope("bundle", slug, {
        "entry_point": "SKILL.md",
        "files": [{"path": "SKILL.md", "role": "entry", "content": "Do the thing."}],
        "applicable_domains": ["code"],
    }, **fields)


def write_tree(root: Path, atoms: list[dict]) -> Path:
    atoms_dir = root / "atoms"
    for atom in atoms:
        cls, slug = atom["id"].split("/", 1)
        path = atoms_dir / cls / f"{slug}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(atom), encoding="utf-8")
    return atoms_dir


def collect(root: Path, atoms: list[dict]) -> list[dict]:
    return build_exports.collect_atoms(write_tree(root, atoms))


def test_it_accepts_one_valid_atom_of_every_typed_class(tmp_path):
    atoms = [persona(), prompt(), agent(), skill(), hook(), model(), policy(), tool(), template(), bundle()]
    collected = collect(tmp_path, atoms)
    assert {a["type"] for a in collected} == set(build_exports.TYPED_CLASSES)
    assert build_exports.find_dangling_references(collected, tmp_path / "atoms") == []


def test_it_rejects_a_bundle_with_no_files(tmp_path):
    with pytest.raises(SystemExit):
        collect(tmp_path, [bundle(files=[])])


def test_it_resolves_bundle_depends_on_across_bundle_and_skill(tmp_path):
    collected = collect(tmp_path, [skill(), bundle(depends_on=["skill/commit"])])
    assert build_exports.find_dangling_references(collected, tmp_path / "atoms") == []


def test_it_rejects_an_atom_that_fails_its_class_schema(tmp_path):
    bad = prompt()
    del bad["content"]
    with pytest.raises(SystemExit) as exc:
        collect(tmp_path, [bad])
    assert exc.value.code == 1


def test_it_rejects_an_id_whose_prefix_does_not_match_its_directory(tmp_path):
    wrong = persona()
    wrong["id"] = "agent/staff-engineer"  # persona schema pattern would reject this
    with pytest.raises(SystemExit):
        collect(tmp_path, [wrong])


def test_it_skips_directories_without_a_schema(tmp_path, capsys):
    atoms_dir = write_tree(tmp_path, [skill()])
    untyped = atoms_dir / "workflow" / "gate" / "ci-green.json"
    untyped.parent.mkdir(parents=True)
    untyped.write_text(json.dumps({"id": "workflow-atoms/gate-type/ci-green", "type": "gate-type"}))
    collected = build_exports.collect_atoms(atoms_dir)
    assert [a["id"] for a in collected] == ["skill/commit"]
    assert "no schema for atom type 'workflow'" in capsys.readouterr().err


def test_it_reports_an_agent_whose_persona_is_missing(tmp_path):
    collected = collect(tmp_path, [agent()])
    problems = build_exports.find_dangling_references(collected, tmp_path / "atoms")
    assert problems == ["agent/tech-lead.persona -> persona/staff-engineer (not in catalog)"]


def test_it_resolves_agent_references_across_every_class(tmp_path):
    atoms = [persona(), prompt(), skill(), hook(), policy(), tool(),
             agent(prompts=["prompt/no-fabrication"], skills=["skill/commit"], hooks=["hook/branch-guard"],
                   policies=["policy/read-only-workspace"], tools=["tool/git-diff"])]
    collected = collect(tmp_path, atoms)
    assert build_exports.find_dangling_references(collected, tmp_path / "atoms") == []


def test_it_reports_a_tool_gated_by_a_missing_policy(tmp_path):
    collected = collect(tmp_path, [tool(gated_by=["policy/absent"])])
    assert build_exports.find_dangling_references(collected, tmp_path / "atoms") == ["tool/git-diff.gated_by -> policy/absent (not in catalog)"]


def test_it_requires_grants_on_capability_policies_and_sandbox_fields_on_isolation(tmp_path):
    bad = policy(); bad["rule"] = {"text": "Read files only."}
    with pytest.raises(SystemExit):
        collect(tmp_path, [bad])
    iso = policy("read-only-sandbox", subtype="isolation", effect="bound",
                 rule={"text": "Read-only sandbox.", "process": "subprocess", "network": "none", "filesystem": "read-only"})
    assert collect(tmp_path / "ok", [iso])[0]["subtype"] == "isolation"  # fresh tree: the bad file is still in tmp_path


def test_it_reports_a_composite_prompt_with_a_missing_part(tmp_path):
    composite = prompt("review-bundle", subtype="composite", includes=["prompt/no-fabrication", "prompt/absent"])
    collected = collect(tmp_path, [prompt(), composite])
    problems = build_exports.find_dangling_references(collected, tmp_path / "atoms")
    assert problems == ["prompt/review-bundle.includes -> prompt/absent (not in catalog)"]


def test_it_requires_includes_on_composite_prompts(tmp_path):
    composite = prompt("review-bundle", subtype="composite")
    with pytest.raises(SystemExit):
        collect(tmp_path, [composite])


def test_it_requires_review_criteria_on_reviewer_agents(tmp_path):
    reviewer = agent("adversarial-reviewer", subtype="reviewer")
    with pytest.raises(SystemExit):
        collect(tmp_path, [persona(), reviewer])
    reviewer["review_criteria"] = ["Findings cite path:line."]
    collected = collect(tmp_path, [persona(), reviewer])
    assert [a["id"] for a in collected if a["type"] == "agent"] == ["agent/adversarial-reviewer"]


def test_it_counts_every_typed_class_even_when_empty():
    counts = build_exports.count_by_type([skill(), skill("pr")])
    assert counts == {"skill": 2, "hook": 0, "prompt": 0, "agent": 0, "persona": 0, "model": 0, "policy": 0, "tool": 0, "template": 0, "bundle": 0}


def test_it_rejects_a_category_outside_the_shared_vocabulary(tmp_path):
    with pytest.raises(SystemExit):
        collect(tmp_path, [skill(category="astrology")])
    collected = collect(tmp_path, [skill(category="coding"), model(category="ai")])
    assert [a["category"] for a in collected] == ["ai", "coding"] or [a["category"] for a in collected] == ["coding", "ai"]


def test_it_rejects_provenance_without_a_source(tmp_path):
    with pytest.raises(SystemExit):
        collect(tmp_path, [skill(provenance={"license": "MIT"})])
    collected = collect(tmp_path, [skill(provenance={"source": "claudeskills.in", "license": "unknown"})])
    assert collected[0]["provenance"]["license"] == "unknown"


def test_it_indexes_atoms_by_category_and_class():
    index = build_exports.category_index([skill(category="coding"), skill("pr", category="coding"), model(category="ai")])
    assert index == {"coding": {"skill": 2}, "ai": {"model": 1}}


def test_it_rejects_a_model_without_a_provider(tmp_path):
    bad = model()
    bad["providers"] = []
    with pytest.raises(SystemExit):
        collect(tmp_path, [bad])


def test_it_reports_a_template_whose_body_and_placeholders_disagree():
    undeclared = template(body="# {{title}} by {{author}}\n")
    unused = template("plan", placeholders=[{"name": "title", "description": "t"}, {"name": "context", "description": "c"}, {"name": "extra", "description": "never used"}])
    problems = build_exports.find_template_defects([template(), undeclared, unused])
    assert problems == [
        "template/adr: body uses {{author}} but placeholders does not declare it",
        "template/adr: placeholders declares context but body never uses it",
        "template/plan: placeholders declares extra but body never uses it",
    ]


def test_it_reports_a_template_produced_by_a_missing_skill(tmp_path):
    collected = collect(tmp_path, [template(produced_by=["skill/absent"])])
    assert build_exports.find_dangling_references(collected, tmp_path / "atoms") == ["template/adr.produced_by -> skill/absent (not in catalog)"]
