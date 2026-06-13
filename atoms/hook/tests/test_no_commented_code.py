"""Tests for the no-commented-code hook atom.

Extracts the script from atoms/hook/no-commented-code.json, materializes
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
    script = json.loads((HOOK_DIR / "no-commented-code.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "no-commented-code.py"
    hook.write_text(script)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def mod(hook_path):
    spec = importlib.util.spec_from_file_location("no_commented_code", hook_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# Unit — _looks_like_code
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("content", [
    "login(user, password)",
    "if user.is_active:",
    "return Response(status=200)",
    "const token = jwt.sign(payload)",
    "for item in items:",
    "import os",
    "from pathlib import Path",
    "x = compute_value()",
    "result := db.Query(ctx)",
    "class AuthMiddleware:",
    "@app.route('/login')",
    "    }",
    "  };",
])
def test_looks_like_code_true(mod, content):
    assert mod._looks_like_code(content), f"expected {content!r} to look like code"


@pytest.mark.parametrize("content", [
    "This is a plain English comment.",
    "TODO: refactor this later",
    "type: ignore",
    "noqa: E501",
    "See the docs for details.",
    "",
    "  ",
    "N",
])
def test_looks_like_code_false(mod, content):
    assert not mod._looks_like_code(content), f"expected {content!r} NOT to look like code"


# ---------------------------------------------------------------------------
# Unit — scan_file
# ---------------------------------------------------------------------------

def test_scan_file_detects_commented_python(mod, tmp_path):
    f = tmp_path / "auth.py"
    f.write_text("def login():\n    pass\n# return old_login(user)\n")
    violations = mod.scan_file(f, f.read_text())
    assert 3 in violations


def test_scan_file_detects_commented_typescript(mod, tmp_path):
    f = tmp_path / "auth.ts"
    f.write_text("function login() {\n  // return oldLogin(user);\n}\n")
    violations = mod.scan_file(f, f.read_text())
    assert 2 in violations


def test_scan_file_clean_prose_comment(mod, tmp_path):
    f = tmp_path / "auth.py"
    f.write_text("# This handles authentication by checking the user token.\ndef login(): pass\n")
    violations = mod.scan_file(f, f.read_text())
    assert violations == []


def test_scan_file_shebang_ignored(mod, tmp_path):
    f = tmp_path / "script.py"
    f.write_text("#!/usr/bin/env python3\ndef main(): pass\n")
    violations = mod.scan_file(f, f.read_text())
    assert violations == []


def test_scan_file_doc_comment_ignored(mod, tmp_path):
    f = tmp_path / "lib.ts"
    f.write_text("/// <reference types='node' />\nconst x = 1;\n")
    violations = mod.scan_file(f, f.read_text())
    assert violations == []


def test_scan_file_unsupported_extension_skipped(mod, tmp_path):
    f = tmp_path / "notes.txt"
    f.write_text("# return old_login(user)\n")
    violations = mod.scan_file(f, f.read_text())
    assert violations == []


def test_scan_file_multiple_violations(mod, tmp_path):
    f = tmp_path / "auth.py"
    f.write_text(
        "def login():\n"
        "    # old_login(user)\n"
        "    pass\n"
        "# return Response(200)\n"
    )
    violations = mod.scan_file(f, f.read_text())
    assert len(violations) == 2
    assert 2 in violations
    assert 4 in violations


# ---------------------------------------------------------------------------
# Integration — subprocess self-check and payload dispatch
# ---------------------------------------------------------------------------

def test_self_check(hook_path):
    result = subprocess.run(
        [sys.executable, str(hook_path), "--self-check"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_subprocess_clean_file(hook_path, tmp_path):
    f = tmp_path / "auth.py"
    f.write_text("def login():\n    # Check token validity before proceeding.\n    return True\n")
    payload = json.dumps({"tool_input": {"file_path": str(f)}})
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=payload, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "DEAD-CODE-VIOLATION" not in result.stderr


def test_subprocess_violation_file(hook_path, tmp_path):
    f = tmp_path / "auth.py"
    f.write_text("def login():\n    # return old_login(user)\n    return True\n")
    payload = json.dumps({"tool_input": {"file_path": str(f)}})
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=payload, capture_output=True, text=True,
    )
    assert result.returncode == 0
    assert "DEAD-CODE-VIOLATION" in result.stderr
    assert "DEAD-CODE-VIOLATION" in result.stderr


def test_subprocess_empty_stdin(hook_path):
    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input="", capture_output=True, text=True,
    )
    assert result.returncode == 0
