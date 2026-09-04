"""Every schemas/examples/<class>.json must validate against schemas/<class>-v1.json,
and its cross-atom references must point at ids that exist in the real catalog, so
a contributor who starts from an example starts from something that would pass CI."""
import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
EXAMPLES = sorted((REPO / "schemas" / "examples").glob("*.json"))

spec = importlib.util.spec_from_file_location("build_exports", REPO / "scripts" / "build-exports.py")
build_exports = importlib.util.module_from_spec(spec)
sys.modules["build_exports"] = build_exports
spec.loader.exec_module(build_exports)


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.stem for p in EXAMPLES])
def test_example_validates_against_its_class_schema(path):
    atom = json.loads(path.read_text(encoding="utf-8"))
    assert atom["type"] == path.stem
    validator = build_exports.load_validator(f"{path.stem}-v1.json")
    errors = [e.message for e in validator.iter_errors(atom)]
    assert errors == []


def test_examples_exist_for_every_typed_class():
    assert {p.stem for p in EXAMPLES} == set(build_exports.TYPED_CLASSES)


def test_example_references_resolve_in_the_real_catalog():
    real = build_exports.collect_atoms(REPO / "atoms")
    examples = [json.loads(p.read_text(encoding="utf-8")) for p in EXAMPLES]
    problems = build_exports.find_dangling_references(real + examples, REPO / "atoms")
    assert [p for p in problems if p.startswith(tuple(e["id"] for e in examples))] == []
