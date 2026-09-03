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

## G4 — Catalog prompts, personas, and agents as typed, resolvable atoms

Every prompt fragment, portable identity, and bound agent from the retired prompt-atoms,
persona-atoms, and agent-atoms catalogs lives here as a typed atom. A persona is self-contained
(its rules are inline text); an agent's references all resolve at build time, so a composition
can be installed as a unit.

## G5 — One vocabulary and honest attribution across every class

Every atom carries a `category` from one shared list, so a human or an agent can ask for
"everything for security" and get skills, hooks, prompts, agents, personas, and models together.
Every imported atom carries `provenance` naming its source, original URL, author, and license,
with `unknown` shown as such rather than hidden.

## G6 — Models as catalog data

Every model a runtime in the ecosystem can call is a `model` atom with the provider ids and
commands needed to use it, starting with the Ollama library and growing to hosted providers.
