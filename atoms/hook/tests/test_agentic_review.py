"""Tests for the agentic-review hook atom.

API calls are never made in tests — _call_api is monkeypatched.
Git is exercised against real temp repos for the diff collection path.
"""
from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

HOOK_DIR = Path(__file__).resolve().parents[1]


def _materialize(dest: Path) -> Path:
    script = json.loads((HOOK_DIR / "agentic-review.json").read_text())["script"]
    lib = json.loads((HOOK_DIR / "lib.json").read_text())["script"]
    (dest / "_lib.py").write_text(lib)
    hook = dest / "agentic-review.py"
    hook.write_text(script)
    return hook


@pytest.fixture
def hook_path(tmp_path):
    return _materialize(tmp_path)


@pytest.fixture
def mod(hook_path):
    spec = importlib.util.spec_from_file_location("agentic_review", hook_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------

def test_load_config_defaults(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_CONFIG_PATH", tmp_path / "nonexistent.json")
    cfg = mod._load_config()
    assert cfg["enabled"] is True
    assert cfg["max_diff_lines"] == 300


def test_load_config_override(mod, tmp_path, monkeypatch):
    cfg_file = tmp_path / "agentic-review.json"
    cfg_file.write_text(json.dumps({"model": "gpt-4o", "max_diff_lines": 50}))
    monkeypatch.setattr(mod, "_CONFIG_PATH", cfg_file)
    cfg = mod._load_config()
    assert cfg["model"] == "gpt-4o"
    assert cfg["max_diff_lines"] == 50
    assert cfg["enabled"] is True  # default preserved


def test_load_config_enabled_false(mod, tmp_path, monkeypatch):
    cfg_file = tmp_path / "agentic-review.json"
    cfg_file.write_text(json.dumps({"enabled": False}))
    monkeypatch.setattr(mod, "_CONFIG_PATH", cfg_file)
    cfg = mod._load_config()
    assert cfg["enabled"] is False


def test_load_config_invalid_json(mod, tmp_path, monkeypatch):
    cfg_file = tmp_path / "agentic-review.json"
    cfg_file.write_text("{not valid json")
    monkeypatch.setattr(mod, "_CONFIG_PATH", cfg_file)
    cfg = mod._load_config()
    assert cfg["enabled"] is True  # falls back to defaults


# ---------------------------------------------------------------------------
# Provider detection
# ---------------------------------------------------------------------------

def test_detect_anthropic_by_env(mod, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider, model, key = mod._detect_provider({})
    assert provider == "anthropic"
    assert model == "claude-haiku-4-5-20251001"
    assert key == "sk-ant-test"


def test_detect_openai_by_env(mod, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider, model, key = mod._detect_provider({})
    assert provider == "openai"
    assert model == "gpt-4o-mini"


def test_detect_google_by_env(mod, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("GOOGLE_API_KEY", "gk-test")
    provider, model, key = mod._detect_provider({})
    assert provider == "google"
    assert model == "gemini-2.0-flash"


def test_detect_anthropic_takes_priority(mod, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    provider, model, _ = mod._detect_provider({})
    assert provider == "anthropic"


def test_detect_no_keys(mod, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    provider, model, key = mod._detect_provider({})
    assert provider is None
    assert model is None
    assert key is None


def test_config_overrides_provider(mod, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-openai-test")
    provider, model, _ = mod._detect_provider({"provider": "openai"})
    assert provider == "openai"


def test_config_overrides_model(mod, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    provider, model, _ = mod._detect_provider({"model": "claude-sonnet-4-6"})
    assert provider == "anthropic"
    assert model == "claude-sonnet-4-6"


def test_config_provider_without_key_returns_none(mod, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    provider, model, key = mod._detect_provider({"provider": "openai"})
    assert provider is None


# ---------------------------------------------------------------------------
# Diff collection
# ---------------------------------------------------------------------------

def _init_repo(path: Path) -> None:
    subprocess.run(["git", "init", "-b", "main"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@t.com"], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "T"], cwd=path, check=True, capture_output=True)


def _commit(path: Path, files: dict[str, str], msg: str) -> None:
    for name, content in files.items():
        (path / name).write_text(content)
        subprocess.run(["git", "add", name], cwd=path, check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", msg], cwd=path, check=True, capture_output=True)


def test_get_diff_returns_latest_commit(mod, tmp_path):
    _init_repo(tmp_path)
    _commit(tmp_path, {"a.py": "x = 1\n"}, "initial")
    _commit(tmp_path, {"a.py": "x = 2\n"}, "change")
    diff = mod._get_diff(str(tmp_path), 300)
    assert diff is not None
    assert "-x = 1" in diff or "+x = 2" in diff


def test_get_diff_truncates_at_max(mod, tmp_path):
    _init_repo(tmp_path)
    _commit(tmp_path, {"big.py": "\n".join(f"x{i} = {i}" for i in range(500))}, "initial")
    _commit(tmp_path, {"big.py": "\n".join(f"y{i} = {i}" for i in range(500))}, "change")
    diff = mod._get_diff(str(tmp_path), 50)
    assert diff is not None
    assert "truncated" in diff
    assert len(diff.splitlines()) <= 52


def test_get_diff_none_outside_repo(mod, tmp_path):
    diff = mod._get_diff(str(tmp_path / "not_a_repo"), 300)
    assert diff is None


# ---------------------------------------------------------------------------
# Response parsing
# ---------------------------------------------------------------------------

def test_parse_violations_clean(mod):
    raw = '{"violations": []}'
    assert mod._parse_violations(raw) == []


def test_parse_violations_with_findings(mod):
    raw = json.dumps({"violations": [
        {"rule": "§4.1.6", "file": "auth.py", "line": 42, "detail": "empty except"}
    ]})
    v = mod._parse_violations(raw)
    assert len(v) == 1
    assert v[0]["rule"] == "§4.1.6"


def test_parse_violations_strips_markdown_fence(mod):
    raw = "```json\n{\"violations\": [{\"rule\": \"§4.5.1\", \"file\": \"x.py\", \"line\": 1, \"detail\": \"bare print\"}]}\n```"
    v = mod._parse_violations(raw)
    assert len(v) == 1


def test_parse_violations_invalid_json(mod):
    assert mod._parse_violations("not json at all") == []


def test_parse_violations_unexpected_shape(mod):
    assert mod._parse_violations('{"something_else": true}') == []


# ---------------------------------------------------------------------------
# Self-check
# ---------------------------------------------------------------------------

def test_self_check(hook_path):
    proc = subprocess.run(
        [sys.executable, str(hook_path), "--self-check"],
        capture_output=True, text=True,
        env={**os.environ},
    )
    assert proc.returncode == 0
    assert "self-check OK" in proc.stderr


# ---------------------------------------------------------------------------
# End-to-end: no API key → silent skip
# ---------------------------------------------------------------------------

def test_no_api_key_silent_skip(hook_path, tmp_path):
    _init_repo(tmp_path)
    _commit(tmp_path, {"a.py": "x = 1\n"}, "initial")
    _commit(tmp_path, {"a.py": "x = 2\n"}, "change")
    env = {
        k: v for k, v in os.environ.items()
        if k not in {"ANTHROPIC_API_KEY", "OPENAI_API_KEY", "AZURE_OPENAI_API_KEY", "GOOGLE_API_KEY"}
    }
    env["HOME"] = os.environ.get("HOME", "")
    proc = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps({"cwd": str(tmp_path)}),
        capture_output=True, text=True, env=env,
    )
    assert proc.returncode == 0
    assert "GOVERNANCE-VIOLATION" not in proc.stderr


# ---------------------------------------------------------------------------
# End-to-end: mocked API call → violations emitted
# ---------------------------------------------------------------------------

def test_violations_emitted_when_api_returns_findings(mod, tmp_path, monkeypatch):
    _init_repo(tmp_path)
    _commit(tmp_path, {"auth.py": "def go():\n    pass\n"}, "initial")
    _commit(tmp_path, {"auth.py": "def go():\n    try:\n        x = 1\n    except:\n        pass\n"}, "add handler")

    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.setattr(mod, "_CONFIG_PATH", tmp_path / "no-config.json")

    findings = {"violations": [
        {"rule": "§4.1.6", "file": "auth.py", "line": 4, "detail": "bare except with pass swallows all errors"}
    ]}
    monkeypatch.setattr(mod, "_call_api", lambda *a, **kw: json.dumps(findings))

    captured = []
    monkeypatch.setattr(mod._lib, "log", lambda *args: captured.append(" ".join(str(a) for a in args)))

    import types
    fake_event = {}
    monkeypatch.setattr(sys, "stdin", types.SimpleNamespace(read=lambda: json.dumps({"cwd": str(tmp_path)})))

    # Patch Path.home to avoid touching real config
    monkeypatch.setattr(mod, "_load_config", lambda: {"enabled": True, "max_diff_lines": 300})

    mod.main()
    assert any("GOVERNANCE-VIOLATION" in c and "§4.1.6" in c for c in captured)


def test_disabled_in_config_skips(mod, tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_load_config", lambda: {"enabled": False})
    api_called = []
    monkeypatch.setattr(mod, "_call_api", lambda *a, **kw: api_called.append(1) or "{}")
    with pytest.raises(SystemExit) as exc:
        mod.main()
    assert exc.value.code == 0
    assert not api_called
