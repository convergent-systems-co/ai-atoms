"""Tests for the push-guard hook atom."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parents[1]


def _materialize(dest: Path) -> Path:
    script = json.loads((HOOK_DIR / "push-guard.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "push-guard.py"
    hook.write_text(script)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def guard(hook_path):
    spec = importlib.util.spec_from_file_location("push_guard", hook_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# Unit — _parse_push
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("argv,expected_force,expected_dest", [
    (["git", "push", "origin", "main"], False, "main"),
    (["git", "push", "--force", "origin", "main"], True, "main"),
    (["git", "push", "-f", "origin", "main"], True, "main"),
    (["git", "push", "--force-with-lease", "origin", "feat/x"], True, "feat/x"),
    (["git", "push", "--force-with-lease=origin/feat:abc", "origin", "feat/x"], True, "feat/x"),
    (["git", "push", "origin", "HEAD:refs/heads/main"], False, "main"),
    (["git", "push", "--force", "origin", "HEAD:refs/heads/main"], True, "main"),
    (["git", "push", "--force", "origin", "+HEAD:main"], True, "main"),
    (["git", "push"], False, None),
    (["git", "push", "--force"], True, None),
    (["git", "status"], False, None),
])
def test_parse_push(guard, argv, expected_force, expected_dest):
    is_force, dest = guard._parse_push(argv)
    assert is_force == expected_force
    assert dest == expected_dest


# ---------------------------------------------------------------------------
# Unit — _git_push_segments
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command,expected_count", [
    ("git push origin main", 1),
    ("git fetch && git push --force origin main", 1),
    ("git push origin a\ngit push origin b", 2),
    ("echo hi", 0),
    ("git status", 0),
])
def test_git_push_segments(guard, command, expected_count):
    segs = guard._git_push_segments(command)
    assert len(segs) == expected_count


# ---------------------------------------------------------------------------
# Unit — _is_protected
# ---------------------------------------------------------------------------

def test_is_protected_main(guard):
    assert guard._is_protected("main", ["main"])

def test_is_protected_custom(guard):
    assert guard._is_protected("production", ["main", "production"])

def test_is_not_protected(guard):
    assert not guard._is_protected("feat/x", ["main"])

def test_is_protected_none(guard):
    assert not guard._is_protected(None, ["main"])


# ---------------------------------------------------------------------------
# Integration — PreToolUse via subprocess
# ---------------------------------------------------------------------------

def _pretooluse(hook_path, command, cwd, ai_root):
    payload = {
        "hookEventName": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "cwd": str(cwd),
    }
    proc = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        env={**os.environ, "AI_ROOT": str(ai_root)},
        capture_output=True, text=True,
    )
    return proc


def test_pretooluse_blocks_force_push_to_main(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "git push --force origin main", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
    assert "main" in out["hookSpecificOutput"]["permissionDecisionReason"]


def test_pretooluse_blocks_force_with_lease_to_main(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "git push --force-with-lease origin main", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_allows_normal_push(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "git push origin feat/my-feature", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    assert proc.stdout.strip() == "" or json.loads(proc.stdout).get("hookSpecificOutput", {}).get("permissionDecision") != "deny"


def test_pretooluse_allows_force_to_non_protected(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "git push --force origin feat/x", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    assert not proc.stdout.strip() or json.loads(proc.stdout).get("hookSpecificOutput", {}).get("permissionDecision") != "deny"


def test_pretooluse_blocks_compound_force_push(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "git fetch && git push -f origin main", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_pretooluse_ignores_non_git(hook_path, tmp_path):
    proc = _pretooluse(hook_path, "echo hello", tmp_path, tmp_path / "ai")
    assert proc.returncode == 0
    assert proc.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Integration — wrapper mode via subprocess
# ---------------------------------------------------------------------------

def _wrapper(hook_path, argv, cwd, ai_root):
    env = {
        **os.environ,
        "WRAPPED_CMD": "git",
        "WRAPPED_ARGV": json.dumps(argv),
        "AI_ROOT": str(ai_root),
        "HOME": os.environ.get("HOME", ""),
    }
    return subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=env, cwd=str(cwd), stdin=subprocess.DEVNULL,
        capture_output=True, text=True,
    )


def test_wrapper_blocks_force_push_to_main(hook_path, tmp_path):
    proc = _wrapper(hook_path, ["push", "--force", "origin", "main"], tmp_path, tmp_path / "ai")
    assert proc.returncode == 1
    assert "main" in proc.stderr


def test_wrapper_allows_normal_push(hook_path, tmp_path):
    proc = _wrapper(hook_path, ["push", "origin", "feat/x"], tmp_path, tmp_path / "ai")
    assert proc.returncode == 0


def test_wrapper_allows_force_to_non_protected(hook_path, tmp_path):
    proc = _wrapper(hook_path, ["push", "--force", "origin", "feat/x"], tmp_path, tmp_path / "ai")
    assert proc.returncode == 0


def test_wrapper_respects_custom_protected_branches(hook_path, tmp_path):
    ai_root = tmp_path / "ai"
    ai_root.mkdir()
    (ai_root / "settings.json").write_text(json.dumps({"protectedBranches": ["main", "production"]}))
    proc = _wrapper(hook_path, ["push", "--force", "origin", "production"], tmp_path, ai_root)
    assert proc.returncode == 1
    assert "production" in proc.stderr


def test_self_check(hook_path):
    proc = subprocess.run([sys.executable, str(hook_path), "--self-check"], capture_output=True, text=True)
    assert proc.returncode == 0
