# Changelog — ai-atoms

All notable changes to this catalog are documented here.
Versioning follows [Semantic Versioning](https://semver.org/).

## v0.5.0 — 2026-09-03

Second curation pass: the defects the first pass could only list.

### Added
- `scripts/skillmd.py`, a frontmatter parser that understands YAML block scalars; both skill
  importers use it. `scripts/repair-descriptions.py` re-read the original SKILL.md for every atom
  whose description was literally `>` and repaired 111; eight dotnet files had moved upstream and
  their `source_url` now points at the new path.
- `scripts/import-cloudflare-models.py`: model-atoms.com's 77 Cloudflare Workers AI cards folded
  in — 33 as additional `providers[]` entries on the matching Ollama atoms (exact model-name match
  after stripping size and variant tokens), 44 as new model atoms.
- Vendors for seven Ollama models whose pages state them (OpenBMB, Google, Essential AI, Meta,
  Cohere). Five (`ornith`, `laguna`) still say nothing and stay `unknown`.

### Removed
- `atoms/workflow/` (40 untyped step and gate atoms) and the retired `skills/project-workspace.json`.
- Four claudeskills atoms whose fragment was a placeholder (`...`, `test content`, a truncated
  file).

### Noted
- `persona/senior-engineer-mentor`'s knowledge boundaries match its source exactly; the earlier
  "miscopied" flag was wrong.

## v0.4.0 — 2026-09-03

Curation pass from `docs/reviews/2026-09-03-atom-evaluation.md`, plus two more typed classes.

### Added
- `schemas/policy-v1.json` and `schemas/tool-v1.json`; 54 policy and 20 tool atoms re-typed from
  the staged agent-atoms and persona-atoms trees by `scripts/migrate-policy-tool.py`. Agent
  `policies` and `tools` references now resolve to typed atoms; `tool.gated_by` names the policies
  that must permit a tool.
- `scripts/discover-licenses.py`: reads the upstream repository's license through the GitHub API
  for atoms whose provenance names one; 17 claudeskills atoms moved from `unknown` to a real SPDX id.
- `hook.events`: every event a hook fires on when there is more than one (`audit-logger`,
  `dirty-tree-guard`, `test-coverage-gate`). `event` stays the primary for consumers that read one.
- `hook/security-reminder` finally ships a script, with tests; it flags untrusted `${{ }}`
  interpolations in edited workflow files.
- Site: listing and detail pages for policies and tools; a tool page renders the JSON-Schema-shaped
  definition a runtime hands to the model.

### Changed
- `hook/secret-precommit` is typed as a `git-pre-commit` event, not `PreToolUse`.
- Ten hook descriptions no longer cite the private `Common.md` constitution.
- Vendor-variant prompts with byte-identical content collapsed: `prompt/sre`,
  `prompt/documentation-writer`, `prompt/security-architect` (−4 atoms). Nine persona prompts now
  carry `persona_ref`.
- Decisions recorded: claudeskills atoms whose license stays unknown remain in the catalog as
  drafts; the 111 knowledge-work skills stay, filterable by category.

### Removed
- Seven skills the evaluation recommended dropping: `atom-status`, `business-pulse`,
  `canva-creator`, `cash-flow-snapshot`, `code-testing-extensions`, `debug-systematically`,
  `test-publish`.
- `persona/none` (a pass-through with three missing parts) and nine agents that bound nothing but a
  persona and a planner preference; their personas remain.
- The staged `atoms/policy/{boundary,capability,isolation}/` and `atoms/tool/command/` trees,
  replaced by the typed atoms above.

## v0.3.0 — 2026-09-03

A sixth class, a shared vocabulary, a second wave of imports, and a redesigned site.

### Site
- Self-contained design system (`web/src/styles/site.css`): no external brand stylesheet; light
  and dark designed separately and honouring `prefers-color-scheme` and a persisted toggle.
  Bricolage Grotesque for display, Source Sans 3 for reading, JetBrains Mono for ids.
- Periodic-table motif: each class is an element tile (Sk, Hk, Pr, Ag, Pe, Mo) with its count.
- "Today's specimens": a skill, hook, persona, prompt, and model of the day, chosen by day
  number over a curated candidate list; the build-day pick is rendered, and the page re-picks
  for the viewer's date without a rebuild.
- Global search palette (`/` key) over `/search-index.json`, every atom in one small record.
- Listing pages with a sticky filter rail: search, subtype/task/event, category, source, license;
  filters are reflected in the URL so a filtered list can be shared.
- Detail pages with a sticky action rail: copy, download, raw JSON, install and run commands.
- `/start/` with side-by-side directions for humans and for AI agents; `/llms.txt`;
  `/sitemap.xml`; `/robots.txt`.

### Added
- `schemas/model-v1.json` and 239 `model` atoms from the Ollama library
  (`scripts/import-ollama-models.py`), each with a `providers[]` entry carrying the Ollama id,
  page, pull command, tag count, pulls, and updated date. Vendor, family, and task are inferred
  from the name and say so in `provenance.notes`.
- `schemas/common-v1.json` with two definitions every class references: `category` (22 values,
  one vocabulary for browsing across classes) and `provenance` (`source`, `source_url`, `author`,
  `license`, `imported_at`, `notes`).
- 397 skills from claudeskills.in (`scripts/import-claudeskills.py`) with `provenance.license`
  taken from each SKILL.md frontmatter or the aggregator's stated source, and `unknown` for the
  380 rows where neither states one. 12 slugs already in the catalog were skipped.
- `scripts/backfill-provenance-category.py`: provenance for the 244 GitHub-imported skills and
  the 119 re-typed atoms; a category on every atom.
- Site: a theme layer (`web/src/styles/ai-atoms.css`) so light and dark both resolve from brand
  tokens; a per-atom action bar (copy markdown, download, copy JSON, raw JSON, install command);
  search and category filters on every listing; category pages and `/categories/<slug>.json`;
  model pages; a provenance footer that shows `unknown` licenses as such; the home page's
  "For humans" and "For AI agents" entries covering inspect, install, and query.
- Builder forms for models and a category select on every class.
- `categories` index in `exports/catalog.json` and `/ai/index.json` (`version: "3"`).

### Changed
- `scripts/build-exports.py` resolves `$ref` across schema files through a local registry.
- Skill and hook pages rebuilt on the shared components; markdown rendering is unchanged.

## v0.2.0 — 2026-09-03

Three new atom classes. The catalog grows from two classes (313 atoms) to five.

### Added
- `schemas/prompt-v1.json`, `schemas/agent-v1.json`, `schemas/persona-v1.json`
- 59 `prompt` atoms, 48 `persona` atoms, 12 `agent` atoms, re-typed from the content PR #46
  staged from the retired prompt-atoms, persona-atoms, and agent-atoms catalogs
  (`scripts/migrate-retired-atoms.py` records every unresolved reference it met)
- Build-time reference resolution: a dangling `persona`, `prompts`, `skills`, `hooks`,
  `tools`, `policies`, `persona_ref`, `includes`, or `depends_on` entry fails the build
- `classes` and per-class `counts` in `exports/catalog.json`
- `/atoms/<class>/<slug>.json` endpoints for every class (previously documented but served
  the HTML 404 page), listing and detail pages for prompt, agent, and persona, builder forms
  for the three classes, and a shared site navigation component
- `scripts/tests/` behavioural tests for the build script; `pytest.ini`
- `README.md`; ADR `docs/adr/0001-prompt-agent-persona-classes.md`

### Changed
- `/ai/index.json` is now derived from the catalog's class list (`version: "2"`)
- `scripts/build-exports.py` validates any class with a `schemas/<class>-v1.json`
- `publish-atom.yml` accepts the three new classes

### Removed
- The verbatim retired-catalog copies under `atoms/agent/{actor,persona,_facets}/`,
  `atoms/prompt/<subtype>/`, `personas/`, `prompts/`, and `agents/`, replaced by the typed atoms
  above. `atoms/policy/`, `atoms/tool/`, and `atoms/workflow/` remain staged and untyped.
- Empty-content prompts `none-anthropic`, `none-ollama`, `none-openai`, and the two template
  files (`persona-template`, `personas/TEMPLATE`).

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
