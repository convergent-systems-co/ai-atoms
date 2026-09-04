# ai-atoms — AI Instructions

**Site:** https://ai-atoms.com
**Index:** https://ai-atoms.com/ai/index.json
**Catalog:** https://ai-atoms.com/exports/catalog.json
**Audience:** an AI agent or runtime that wants to discover, query, and install atoms without a human.

## What is ai-atoms?

A typed, versioned catalog of AI runtime primitives. Nine classes: **skill**, **hook**, **prompt**,
**agent**, **persona**, **model**, **policy**, **tool**, **template**. Every atom is static JSON validated against its class schema,
carries a `category` from one shared vocabulary, and (when imported) a `provenance` block naming the
source, original URL, author, and license.

## Discover

1. `GET /ai/index.json` — classes, per-class counts, per-category counts, every atom id, endpoint
   and schema URLs.
2. `GET /categories/<category>.json` — ids in one category grouped by class. Categories are listed in
   the index; the full vocabulary is in `/schemas/common-v1.json` under `$defs.category.enum`.

## Query

- One atom: `GET /atoms/<class>/<slug>.json` — the slug is the id without its class prefix
  (`skill/commit` → `/atoms/skill/commit.json`).
- Whole catalog: `GET /exports/catalog.json` — every atom inline, plus `classes`, `counts`,
  `categories`, and `compositions`.
- Text search is client-side on the HTML pages only; for programmatic search, load the catalog and
  filter on `name`, `description`, `tags`, `category`.

## Install and use, by class

### skill
- Inject `system_prompt_fragment` into the system prompt, or write it to
  `.claude/skills/<slug>/SKILL.md` with `name` and `description` as frontmatter.
- `invocation` lists slash-command forms. `depends_on` lists sub-skills to install with it.
- `ai skills install <slug>` does all of this on a machine with the `ai` CLI.

### hook
- `event` and `trigger` say when it fires; `events`, when present, lists every event to wire it to;
  `blocking` says whether it can abort the operation.
- `script` is the complete source. Install it to `~/.ai/hooks/<slug>.<ext>` and wire
  `ai hooks run <slug>` (or the script path) into the client's hook configuration.
- `depends_on` (usually `hook/lib`) must be installed alongside. `requires_wrap` names a command
  wrapper needed for full coverage. `ai hooks install <slug>` handles all of it.

### prompt
- Inject `content` verbatim into the turns listed in `applicable_turns` (default: system).
- `subtype` tells you what kind of text it is. A `composite` prompt's `content` is already the
  resolved concatenation of `includes`; you do not need to resolve them.
- `persona_ref` points at the persona a `persona` prompt renders.

### persona
- Self-contained identity. Render `role` (job to be done, tasks, out of scope), `voice`, `tone`,
  `work_contract`, `constraints[].text`, and `knowledge_boundaries[].text` into the system turn.
  When `system_prompt_fragment` is present, use it as the opening text.
- Binds nothing. To run it with tools, use an agent.

### agent
- Resolve `persona`, then `prompts`, `skills`, `hooks`, `tools`, `policies` by id. Every reference
  resolves to a typed atom in the catalog.
- `subtype: reviewer` means the agent judges work against `review_criteria` and emits verdicts.
- `execution.planner` and `execution.memory` are preferences for the runtime loop.

### model
- Pick an entry in `providers[]`: `model_id` is what the provider's API expects; `pull_command`
  obtains it locally when the provider supports that (Ollama).
- `task`, `capabilities`, `parameter_sizes`, and `context_window_tokens` are for selection.
- `provenance.license: unknown` means the listing did not publish the weights license.

### policy
- `rule.text` is the rule as a model or operator reads it. `effect` says whether it forbids, requires,
  permits, or bounds.
- `subtype: capability` carries `rule.grants` and `rule.elevation` (`declared` or `user-approved`);
  gate tool calls whose `spec.side_effects` need those grants.
- `subtype: isolation` carries `rule.process`, `rule.network`, `rule.filesystem`, `rule.scoped_paths`
  for the sandbox.
- `subtype: boundary` carries covered and excluded domains or explicit `rule.refusals`.

### tool
- `spec.function_name`, `spec.parameters`, and `spec.returns` are the signature the model sees;
  the tool page renders the JSON-Schema-shaped definition ready to pass to a model.
- `spec.side_effects` (fs-read, fs-write, exec, network, user-prompt) must be permitted by a
  capability policy before the runtime executes the call. `gated_by` names such policies.

### template
- Render `body` by replacing each `{{name}}` with a value that satisfies its entry in
  `placeholders`; every placeholder marked required must be filled. Apply `rules` to the result.
- `example` is one finished instance; `produced_by` lists the skills whose output is this document.
- `subtype: agent` is the shape of a one-shot subagent definition (Claude Code `.claude/agents/*.md`);
  `subtype: persona` is the shape of a conversational character. Render either to a markdown file.
- Minimal valid starting files for every class: `/schemas/examples/<class>.json`.

## Attribution

Check `provenance.license` before redistributing an atom. `unknown` means the source stated no
license; the atom is served under the source's own terms and the catalog's CC-BY-4.0 covers only
the catalog metadata. `authored_by` names the author; `provenance.source_url` is the original.

## Schemas

- Common definitions (category, provenance): https://ai-atoms.com/schemas/common-v1.json
- Per class: https://ai-atoms.com/schemas/<class>-v1.json

## License

Code: Apache-2.0. Catalog data: CC-BY-4.0. Imported content keeps its source's terms.
Part of the convergent-systems.co atoms ecosystem.
