# ai-atoms — AI Instructions

**Site:** https://ai-atoms.com
**Catalog:** https://ai-atoms.com/exports/catalog.json
**Index:** https://ai-atoms.com/ai/index.json

## What is ai-atoms?

ai-atoms is a typed, versioned catalog of AI runtime primitives for AI agents, Claude Code,
and agentic pipelines. It contains two classes of atom: **skills** and **hooks**.

## Two classes

### skill
A skill is a bounded, invocable unit of AI capability. Each skill bundles:
- A human-readable `description` explaining when to use it and what it prevents
- A `system_prompt_fragment` — the prompt text injected into an agent's system context
  when the skill is loaded. It is self-contained and actionable.
- An `applicable_domains` list (e.g. code, debug, planning, agents)
- An optional `invocation_contract` with declared inputs, outputs, and side effects

**Use skills to:** load bounded behavior protocols into an AI agent on demand. The
`system_prompt_fragment` is the operative text; inject it into the agent's system prompt
or prepend it to the conversation context.

### hook
A hook is an event-driven runtime behavior wired into AI tool infrastructure. Each hook declares:
- The `event` it responds to (e.g. PreToolUse, PostToolUse, SessionStart, Stop)
- The `language` it is implemented in (python, bash, javascript, typescript)
- A `trigger` with a type (tool-name, file-pattern, always, tool-category) and optional pattern
- Whether it is `blocking` (can abort the triggering operation) or advisory
- Its `side_effects` (e.g. writes to audit log, emits warning to stderr)

**Use hooks with:** Claude Code (settings.json hooks configuration), Copilot CLI, or any
AI tool that exposes an event-hook mechanism.

## Navigation

1. Read `/ai/index.json` — lists all skill IDs and hook IDs
2. Fetch a skill: `GET /atoms/skill/<slug>.json` — returns the full skill atom
3. Read `system_prompt_fragment` to understand how to invoke the skill
4. Fetch a hook: `GET /atoms/hook/<slug>.json` — returns the full hook atom
5. Read `trigger.event` and `trigger.pattern` to understand when the hook fires

## Integration with Claude Code

Hooks are wired via `~/.claude/settings.json` (or project `.claude/settings.json`) under the
`hooks` key. Each hook entry maps an event name to a script command. The `blocking` field
indicates whether the hook should use the `blocking` hook type (returns exit code) or the
`non-blocking` type (fire-and-forget).

## Catalog schema

- Skills validate against: https://ai-atoms.com/schemas/skill-v1.json
- Hooks validate against: https://ai-atoms.com/schemas/hook-v1.json
- Full catalog: https://ai-atoms.com/exports/catalog.json

## License

Code: Apache-2.0. Data: CC-BY-4.0. Part of the convergent-systems.co atoms ecosystem.
