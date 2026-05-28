# Changelog — ai-atoms

All notable changes to this catalog are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

## v0.1.0 — 2026-05-28

Initial catalog. 5 skill atoms, 4 hook atoms.

### Skills added
- `skill/brainstorming` — Brainstorm Before Building
- `skill/systematic-debugging` — Systematic Debugging
- `skill/checkpoint` — Session Checkpoint
- `skill/verification-before-completion` — Verify Before Claiming Done
- `skill/dispatching-parallel-agents` — Dispatch Parallel Agents

### Hooks added
- `hook/branch-guard` — Branch Guard (blocking PreToolUse)
- `hook/audit-logger` — Interaction Audit Logger (non-blocking, always)
- `hook/worktree-guard` — Worktree Placement Guard (blocking PreToolUse)
- `hook/security-reminder` — GitHub Actions Security Reminder (non-blocking, file-pattern)

### Infrastructure
- Schemas: `skill-v1.json`, `hook-v1.json`
- Build pipeline: `scripts/build-exports.py`
- CI and deploy workflows for Cloudflare Pages
- Terraform for `ai-atoms.com` DNS and Pages project
