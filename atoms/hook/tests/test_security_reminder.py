"""Behavioural tests for hook/security-reminder.

The script lives inside the atom JSON; tests load it from there so the shipped
text is what runs.
"""
import json
import subprocess
import sys
from pathlib import Path

ATOM = Path(__file__).resolve().parent.parent / "security-reminder.json"


def run(payload: dict | None, *args: str) -> subprocess.CompletedProcess:
    script = json.loads(ATOM.read_text())["script"]
    stdin = json.dumps(payload) if payload is not None else ""
    return subprocess.run([sys.executable, "-c", script, *args], input=stdin, capture_output=True, text=True, timeout=20)


def test_it_passes_self_check():
    r = run(None, "--self-check")
    assert r.returncode == 0 and "self-check OK" in r.stdout


def test_it_stays_silent_for_files_outside_workflows():
    r = run({"tool_name": "Edit", "tool_input": {"file_path": "src/app.py", "new_string": "${{ github.event.issue.title }}"}})
    assert r.returncode == 0 and r.stderr == ""


def test_it_reminds_when_a_workflow_is_edited_and_never_blocks():
    r = run({"tool_name": "Write", "tool_input": {"file_path": ".github/workflows/ci.yml", "content": "name: CI\n"}})
    assert r.returncode == 0
    assert "security-reminder" in r.stderr and "env:" in r.stderr


def test_it_flags_untrusted_interpolation_in_the_edit():
    content = "run: echo ${{ github.event.pull_request.title }}"
    r = run({"tool_name": "Edit", "tool_input": {"file_path": "repo/.github/workflows/pr.yaml", "new_string": content}})
    assert r.returncode == 0
    assert "untrusted interpolation" in r.stderr and "github.event.pull_request.title" in r.stderr


def test_it_ignores_a_non_json_payload():
    script = json.loads(ATOM.read_text())["script"]
    r = subprocess.run([sys.executable, "-c", script], input="not json", capture_output=True, text=True, timeout=20)
    assert r.returncode == 0 and r.stderr == ""
