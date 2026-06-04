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
    assert guard.find_worktree_add_path(tokens) == expected
