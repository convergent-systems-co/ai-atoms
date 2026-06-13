"""Tests for the test-coverage-gate hook atom.

Extracts the script from atoms/hook/test-coverage-gate.json, materializes
it into a temp dir alongside _lib.py, then exercises it both as an imported
module (unit) and as a subprocess (integration).
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parents[1]


def _materialize(dest: Path) -> Path:
    """Write test-coverage-gate.py + _lib.py into dest; return hook path."""
    script = json.loads((HOOK_DIR / "test-coverage-gate.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "test-coverage-gate.py"
    hook.write_text(script)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def mod(hook_path):
    spec = importlib.util.spec_from_file_location("test_coverage_gate", hook_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# Unit tests — is_test_file / is_source_file
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("path", [
    "tests/test_auth.py",
    "src/__tests__/auth.test.ts",
    "spec/auth_spec.rb",
    "auth_test.go",
    "AuthTest.java",
    "src/test/AuthSpec.kt",
])
def test_is_test_file_true(mod, path):
    assert mod.is_test_file(path), f"expected {path!r} to be a test file"


@pytest.mark.parametrize("path", [
    "src/auth.py",
    "src/auth.ts",
    "cmd/main.go",
    "lib/auth.rb",
])
def test_is_test_file_false(mod, path):
    assert not mod.is_test_file(path), f"expected {path!r} NOT to be a test file"


@pytest.mark.parametrize("path", [
    "src/auth.py",
    "src/auth.ts",
    "cmd/main.go",
])
def test_is_source_file_true(mod, path):
    assert mod.is_source_file(path)


@pytest.mark.parametrize("path", [
    "tests/test_auth.py",
    "README.md",
    "src/config.json",
    ".gitignore",
])
def test_is_source_file_false(mod, path):
    assert not mod.is_source_file(path)


# ---------------------------------------------------------------------------
# Unit tests — check_repo with a real git repo
# ---------------------------------------------------------------------------

def _init_git_repo(repo: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True, capture_output=True)


def _commit(repo: Path, files: dict[str, str], message: str) -> None:
    for name, content in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
        subprocess.run(["git", "add", name], cwd=repo, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", message], cwd=repo, check=True, capture_output=True)


def test_no_violation_when_tests_changed(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _commit(repo, {"src/auth.py": "def login(): pass\n"}, "initial")
    # Make a branch and change both source and test
    subprocess.run(["git", "checkout", "-b", "feat/x"], cwd=repo, check=True, capture_output=True)
    _commit(repo, {
        "src/auth.py": "def login(): return True\n",
        "tests/test_auth.py": "def test_login(): assert True\n",
    }, "feat: add login with test")

    violations = mod.check_repo(repo)
    assert violations == []


def test_violation_when_no_tests_changed(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _commit(repo, {"src/auth.py": "def login(): pass\n"}, "initial")
    subprocess.run(["git", "checkout", "-b", "feat/x"], cwd=repo, check=True, capture_output=True)
    _commit(repo, {"src/auth.py": "def login(): return True\n"}, "feat: change login")

    violations = mod.check_repo(repo)
    assert len(violations) == 1
    assert "TEST-COVERAGE-VIOLATION" in violations[0]
    assert "src/auth.py" in violations[0] or "Changed:" in violations[0]


def test_no_violation_when_only_docs_changed(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_git_repo(repo)
    _commit(repo, {"README.md": "# Hello\n"}, "initial")
    subprocess.run(["git", "checkout", "-b", "docs/x"], cwd=repo, check=True, capture_output=True)
    _commit(repo, {"README.md": "# Updated\n"}, "docs: update readme")

    violations = mod.check_repo(repo)
    assert violations == []


def test_no_violation_outside_git_repo(tmp_path, mod):
    violations = mod.check_repo(tmp_path / "not_a_repo")
    assert violations == []


# ---------------------------------------------------------------------------
# Integration — subprocess self-check
# ---------------------------------------------------------------------------

def test_self_check(hook_path):
    result = subprocess.run(
        [sys.executable, str(hook_path), "--self-check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0
