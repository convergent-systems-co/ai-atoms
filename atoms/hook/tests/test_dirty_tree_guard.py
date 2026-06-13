"""Tests for the dirty-tree-guard hook atom.

Extracts the script from atoms/hook/dirty-tree-guard.json, materializes
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
    script = json.loads((HOOK_DIR / "dirty-tree-guard.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "dirty-tree-guard.py"
    hook.write_text(script)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def mod(hook_path):
    spec = importlib.util.spec_from_file_location("dirty_tree_guard", hook_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _init_repo(repo: Path) -> None:
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


# ---------------------------------------------------------------------------
# Unit — check_repo
# ---------------------------------------------------------------------------

def test_clean_repo_no_violations(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    violations = mod.check_repo(repo)
    assert violations == []


def test_uncommitted_changes_emit_violation(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    (repo / "README.md").write_text("changed\n")
    violations = mod.check_repo(repo)
    assert len(violations) == 1
    assert "GIT-HYGIENE-VIOLATION" in violations[0]
    assert "§4.11.1" in violations[0]
    assert "uncommitted" in violations[0]


def test_staged_changes_emit_violation(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    (repo / "new.py").write_text("x = 1\n")
    subprocess.run(["git", "add", "new.py"], cwd=repo, check=True, capture_output=True)
    violations = mod.check_repo(repo)
    assert any("GIT-HYGIENE-VIOLATION" in v and "§4.11.1" in v for v in violations)


def test_outside_git_repo_no_violations(tmp_path, mod):
    violations = mod.check_repo(tmp_path / "not_a_repo")
    assert violations == []


def test_violation_includes_branch_name(tmp_path, mod):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    subprocess.run(["git", "checkout", "-b", "feat/my-feature"], cwd=repo, check=True, capture_output=True)
    (repo / "README.md").write_text("changed\n")
    violations = mod.check_repo(repo)
    assert any("feat/my-feature" in v for v in violations)


# ---------------------------------------------------------------------------
# Integration — subprocess
# ---------------------------------------------------------------------------

def test_self_check(hook_path):
    result = subprocess.run(
        [sys.executable, str(hook_path), "--self-check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_subprocess_clean_repo(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    env = {"CLAUDE_CWD": str(repo), "PATH": __import__("os").environ["PATH"]}
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input="{}", capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0
    assert "GIT-HYGIENE-VIOLATION" not in result.stdout
    assert "GIT-HYGIENE-VIOLATION" not in result.stderr


def test_subprocess_dirty_repo_emits_sentinel(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    (repo / "README.md").write_text("changed\n")
    env = {"CLAUDE_CWD": str(repo), "PATH": __import__("os").environ["PATH"]}
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input="{}", capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0  # non-blocking
    assert "GIT-HYGIENE-VIOLATION" in result.stdout
    assert "GIT-HYGIENE-VIOLATION" in result.stderr
    assert "§4.11.1" in result.stdout


def test_subprocess_empty_stdin(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    _commit(repo, {"README.md": "hello\n"}, "initial")
    env = {"CLAUDE_CWD": str(repo), "PATH": __import__("os").environ["PATH"]}
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input="", capture_output=True, text=True, env=env,
    )
    assert result.returncode == 0
