# Goals — ai-atoms

## G1 — Catalog all Claude Code hooks as typed atoms

Every governance hook in the convergent-systems ecosystem (branch-guard, audit-logger,
worktree-guard, security-reminder, and future hooks) is cataloged as a typed `hook` atom
in this repository. Each hook atom declares its event, trigger, language, blocking behavior,
and side effects — making the hook ecosystem discoverable, versioned, and portable.

## G2 — Catalog all AI agent skills with invocation contracts

Every reusable AI agent behavior protocol is cataloged as a typed `skill` atom with a
declared `system_prompt_fragment`, `applicable_domains`, and optional `invocation_contract`.
Skills are the canonical source for system-prompt fragments injected by Claude Code skill
loading, the Olympus runtime, and aish.

## G3 — Make ai-atoms.com the canonical AI discovery entry for the convergent-systems ecosystem

`https://ai-atoms.com/ai/index.json` serves as the machine-readable discovery endpoint for
AI tools navigating the convergent-systems atom ecosystem. Skills and hooks are discoverable
without human intervention.
