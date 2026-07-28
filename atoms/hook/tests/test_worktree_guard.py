"""Tests for the worktree-guard hook atom.

The hook's Python lives in the `script` field of
atoms/hook/worktree-guard.json. These tests extract it (plus its
`hook/lib` dependency) into a temp dir, then exercise it both as an
imported module (unit) and as a subprocess (behavior).
"""
import importlib.util
import json
import os
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parents[1]  # atoms/hook/


def _materialize(dest: Path) -> Path:
    """Write worktree-guard.py + _lib.py into dest; return the hook path."""
    wg = json.loads((HOOK_DIR / "worktree-guard.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "worktree-guard.py"
    hook.write_text(wg)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def guard(hook_path):
    spec = importlib.util.spec_from_file_location("worktree_guard", hook_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("command,expected", [
    # Bare invocation still works.
    ("git worktree add /tmp/x origin/main", "/tmp/x"),
    # ISSUE 1: compound commands must be detected.
    ("cd /repo && git worktree add /tmp/x origin/main", "/tmp/x"),
    ('echo "==="; git worktree add -b feat/x /tmp/x origin/main', "/tmp/x"),
    ("true || git worktree add /tmp/x", "/tmp/x"),
    # git global options before the subcommand.
    ("git -C /repo worktree add /tmp/x", "/tmp/x"),
    ("git --git-dir=/r/.git worktree add /tmp/x", "/tmp/x"),
    # leading env assignment.
    ("FOO=bar git worktree add /tmp/x", "/tmp/x"),
    # value-less flags between add and the path.
    ("git worktree add --detach /tmp/x HEAD", "/tmp/x"),
    # Non-add subcommands and unrelated commands pass through.
    ("git worktree list", None),
    ("git worktree remove foo", None),
    ("git status && echo hi", None),
])
def test_finds_path_across_segments(guard, command, expected):
    tokens = shlex.split(command, posix=True)
    paths = guard._worktree_add_paths(tokens)
    result = paths[0] if paths else None
    assert result == expected


def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-q", str(path)], check=True)


def _wrapper_env(tmp_path, argv):
    """Env for a wrapper-mode invocation with an isolated AI_ROOT."""
    return {
        **os.environ,
        "AI_ROOT": str(tmp_path / "aihome"),
        "WRAPPED_CMD": "git",
        "WRAPPED_ARGV": json.dumps(argv),
    }


def test_wrapper_mode_blocks_noncanonical(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=_wrapper_env(tmp_path, ["worktree", "add", "/tmp/x", "HEAD"]),
        cwd=str(repo), stdin=subprocess.DEVNULL,
        capture_output=True, text=True,
    )
    assert proc.returncode == 1, "wrapper mode must block a /tmp worktree"
    assert "Common.md" in proc.stderr


def test_wrapper_mode_allows_canonical(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    target = repo / ".worktrees" / "feat"
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=_wrapper_env(tmp_path, ["worktree", "add", str(target), "HEAD"]),
        cwd=str(repo), stdin=subprocess.DEVNULL,
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, "canonical <repo>/.worktrees/ must pass"


def test_wrapper_mode_allows_claude_native(hook_path, tmp_path):
    """Claude Code's EnterWorktree places worktrees under .claude/worktrees/;
    it can't be redirected to `ai worktree add`, so this root must pass."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    target = repo / ".claude" / "worktrees" / "feat"
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=_wrapper_env(tmp_path, ["worktree", "add", str(target), "HEAD"]),
        cwd=str(repo), stdin=subprocess.DEVNULL,
        capture_output=True, text=True,
    )
    assert proc.returncode == 0, (
        "canonical <repo>/.claude/worktrees/ must pass: " + proc.stderr
    )


def test_wrapper_mode_ignores_non_add(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=_wrapper_env(tmp_path, ["worktree", "list"]),
        cwd=str(repo), stdin=subprocess.DEVNULL,
        capture_output=True, text=True,
    )
    assert proc.returncode == 0


def test_pretooluse_denies_compound_command(hook_path, tmp_path):
    payload = {
        "hookEventName": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "cd /r && git worktree add /tmp/x HEAD"},
        "cwd": str(tmp_path),
    }
    proc = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        env={**os.environ, "AI_ROOT": str(tmp_path / "aihome")},
        capture_output=True, text=True,
    )
    assert proc.returncode == 0
    out = json.loads(proc.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"


def test_internal_git_bypasses_ai_bin_shim(hook_path, tmp_path):
    """resolve_repo_root must use the real git, not the $AI_ROOT/bin shim.

    Regression for the cross-client target environment, where the
    governance shim dir is on PATH. A sabotage `git` placed on
    $AI_ROOT/bin/ stands in for that shim: if the hook routed its own
    internal git through it, resolve_repo_root would fail and the
    canonical target would be wrongly denied. _clean_path_env must strip
    $AI_ROOT/bin so the real git is used.
    """
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    ai_root = tmp_path / "aihome"
    ai_bin = ai_root / "bin"
    ai_bin.mkdir(parents=True)
    sabotage = ai_bin / "git"
    sabotage.write_text("#!/bin/sh\nexit 99\n")
    sabotage.chmod(0o755)
    target = repo / ".worktrees" / "feat"
    env = {
        **os.environ,
        "PATH": f"{ai_bin}{os.pathsep}{os.environ.get('PATH', '')}",
        "AI_ROOT": str(ai_root),
        "WRAPPED_CMD": "git",
        "WRAPPED_ARGV": json.dumps(["worktree", "add", str(target), "HEAD"]),
    }
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--mode=wrapper"],
        env=env, cwd=str(repo), stdin=subprocess.DEVNULL,
        capture_output=True, text=True, timeout=15,
    )
    assert proc.returncode == 0, (
        "canonical target denied — internal git likely used the shim: "
        + proc.stderr
    )


def _pretooluse_decision(hook_path, command, cwd, ai_root):
    """Run the hook's PreToolUse path; return its permissionDecision or None."""
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
    assert proc.returncode == 0, proc.stderr
    if not proc.stdout.strip():
        return None
    return json.loads(proc.stdout)["hookSpecificOutput"]["permissionDecision"]


def test_collects_every_worktree_add(guard):
    """A canonical add must not mask a later non-canonical add."""
    toks = shlex.split(
        "git worktree add repo/.worktrees/ok HEAD "
        "&& git worktree add /tmp/evil HEAD", posix=True)
    assert guard._worktree_add_paths(toks) == ["repo/.worktrees/ok", "/tmp/evil"]


def test_command_helper_splits_on_newlines(guard):
    """shlex folds newlines into whitespace; the helper must split first."""
    cmd = "git fetch\ngit worktree add /tmp/evil HEAD"
    assert guard._worktree_add_paths_in_command(cmd) == ["/tmp/evil"]


def test_pretooluse_denies_newline_separated(hook_path, tmp_path):
    # Regression: multi-line scripts are the normal agent Bash shape.
    decision = _pretooluse_decision(
        hook_path, "git fetch\ngit worktree add /tmp/evil HEAD",
        cwd=tmp_path, ai_root=tmp_path / "aihome")
    assert decision == "deny"


def test_pretooluse_denies_second_noncanonical_add(hook_path, tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _init_repo(repo)
    cmd = (f"git worktree add {repo}/.worktrees/feat HEAD "
           f"&& git worktree add /tmp/evil HEAD")
    decision = _pretooluse_decision(
        hook_path, cmd, cwd=repo, ai_root=tmp_path / "aihome")
    assert decision == "deny"


def test_pretooluse_fails_closed_on_unparseable(hook_path, tmp_path):
    # Unbalanced quote + 'worktree' present -> deny, not pass-through.
    decision = _pretooluse_decision(
        hook_path, "git worktree add '/tmp/bad",
        cwd=tmp_path, ai_root=tmp_path / "aihome")
    assert decision == "deny"
