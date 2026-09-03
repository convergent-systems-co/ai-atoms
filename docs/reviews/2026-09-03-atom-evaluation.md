# Atom evaluation — 2026-09-03

**Audience:** the catalog steward deciding what stays in ai-atoms. **Scope:** every atom in the
repository at the time of the prompt/agent/persona class work (branch
`feat/prompt-agent-persona-classes`), plus the live catalog downloaded from ai-atoms.com.

Verdicts are recommendations. Nothing was deleted on the strength of a verdict; the only
removals on the branch are the verbatim retired-catalog copies that the typed atoms replace
(see the ADR). All per-atom data is in the appendix; the working files (rubric, per-batch JSONL,
migration gap report) are in this session's scratchpad.

## 1. What was downloaded and compared

| Source | Result |
|---|---|
| `https://ai-atoms.com/exports/catalog.json` | 200, 313 atoms ({'hook': 18, 'skill': 295}), built 2026-08-16T20:57:59+00:00 |
| persona-, agent-, prompt-, skill-, workflow-atoms.com | offline (connection failed) — the copies in this repo are the only surviving ones |
| `https://model-atoms.com/exports/catalog.json` | 200, 84 atoms — out of scope for this review |
| `/atoms/skill/commit.json` on the live site | 200 but **HTML**, not JSON: the documented per-atom endpoints did not exist. Fixed on the branch. |

Live vs branch: 313 atoms in common, 119 new on the branch (prompt/agent/persona), 0 live atoms missing from the branch.

## 2. Skills — 295 atoms

Method: four evaluators each read every assigned atom in full against a written rubric
(self-containedness, scope, actionability, duplication, attribution, safety, quality) and
emitted one JSON verdict per atom; the ids were cross-checked against the directory listing.
Verdict counts: **keep 145, fix 143, drop 7**. Scope:
**core 76, adjacent 108, out-of-scope 111**.

| scope | keep | fix | drop |
|---|---|---|---|
| core | 58 | 16 | 2 |
| adjacent | 57 | 50 | 1 |
| out-of-scope | 30 | 77 | 4 |

### 2.1 Systemic defects (one fix covers many atoms)

- **Unshipped dependency `../../CONNECTORS.md` — 63 atoms.** Every knowledge-work
  import from anthropics/knowledge-work-plugins tells the agent to read a connectors file that
  is not in the atom. Fix once in `scripts/import-anthropic-skills.py`: strip or inline the
  reference.
- **Unshipped `reference/gotchas.md` and friends — 15 dotnet atoms**, plus
  261 other
  missing paths (`references/troubleshooting.md`, `scripts/Symbolicate-*.ps1`,
  `templates/viewer.html`, ...). These atoms are only useful with their bundle; either ship the
  bundle or drop the atom.
- **YAML-leak descriptions — 70 atoms** whose `description` is literally `>` or
  `>-` (a folded-scalar marker the importer copied as text): `skill/analyzing-dotnet-performance`, `skill/author-component`, `skill/business-pulse`, `skill/canva-creator`, `skill/cash-flow-snapshot`, `skill/clr-activation-debugging`, `skill/code-testing-agent`, `skill/code-testing-extensions`, `skill/configure-auth`, `skill/content-strategy`, `skill/contract-review`, `skill/convert-blazor-server-to-webapp`, `skill/convert-to-cpm`, `skill/coordinate-components`, `skill/coverage-analysis`, `skill/crap-score`, `skill/create-blazor-project`, `skill/crm-maintenance`, `skill/customer-pulse`, `skill/data-context-extractor`, `skill/detect-static-dependencies`, `skill/dotnet-aot-compat`, `skill/dotnet-maui-doctor`, `skill/dotnet-pinvoke`, `skill/dotnet-webapi`, `skill/generate-testability-wrappers`, `skill/invoice-chase`, `skill/job-post-builder`, `skill/lead-triage`, `skill/margin-analyzer`, `skill/maui-app-lifecycle`, `skill/maui-collectionview`, `skill/maui-data-binding`, `skill/maui-dependency-injection`, `skill/maui-safe-area`, `skill/maui-shell-navigation`, `skill/maui-theming`, `skill/mcp-csharp-create`, `skill/mcp-csharp-debug`, `skill/mcp-csharp-publish`, `skill/mcp-csharp-test`, `skill/microbenchmarking`, `skill/migrate-dotnet10-to-dotnet11`, `skill/migrate-dotnet8-to-dotnet9`, `skill/migrate-dotnet9-to-dotnet10`, `skill/migrate-mstest-v1v2-to-v3`, `skill/migrate-mstest-v3-to-v4`, `skill/migrate-nullable-references`, `skill/migrate-static-to-wrapper`, `skill/migrate-vstest-to-mtp`, `skill/migrate-xunit-to-xunit-v3`, `skill/month-end-prep`, `skill/mtp-hot-reload`, `skill/nuget-trusted-publishing`, `skill/plan-ui-change`, `skill/run-tests`, `skill/smb-onboard`, `skill/smb-router`, `skill/system-text-json-net11`, `skill/tax-season-organizer`, `skill/template-authoring`, `skill/template-discovery`, `skill/template-instantiation`, `skill/template-validation`, `skill/test-anti-patterns`, `skill/test-smell-detection`, `skill/thread-abort-migration`, `skill/ticket-deflector`, `skill/use-js-interop`, `skill/writing-mstest-tests`.
  The importer's frontmatter parser splits on the first `:` and does not handle block scalars.
- **Not self-contained overall: 124 of 295.**

### 2.2 Recommended drops (7)

| atom | why |
|---|---|
| `skill/atom-status` | Near-identical 'Atom Fleet Status' skill, subset of skill/atom-state's checks; Missing invocation and category fields; looks like a stale predecessor |
| `skill/business-pulse` | description field is literally '>' (placeholder/broken); core steps (thresholds, output template) depend on four unshipped reference files |
| `skill/canva-creator` | description field is literally '>' (placeholder/broken); multiple core stages (API details, CSV fallback, redirect language) depend on unshipped reference files |
| `skill/cash-flow-snapshot` | description field is literally '>' (placeholder/broken); core XLSX-generation step requires unshipped xlsx/SKILL.md plus two other reference files |
| `skill/code-testing-extensions` | description field is a literal YAML-leak stub '>-'; entire fragment is an index pointing to 12 extension files, none shipped in the atom — no standalone functional content |
| `skill/debug-systematically` | near-identical five-phase debug protocol to skill/debug; skill/debug has richer invocation/category metadata |
| `skill/test-publish` | Placeholder test skill for publish workflow, lifecycle draft, no real capability |

### 2.3 Duplicate pairs to merge (9)

- `skill/atom-state` ↔ `skill/atom-status`
- `skill/competitive-brief` ↔ `skill/competitive-intelligence`
- `skill/crm-cleanup` ↔ `skill/crm-maintenance`
- `skill/customer-pulse` ↔ `skill/customer-pulse-check`
- `skill/debug` ↔ `skill/debug-systematically`
- `skill/journal-entry` ↔ `skill/journal-entry-prep`
- `skill/margin-analyzer` ↔ `skill/price-check`
- `skill/search` ↔ `skill/search-strategy`
- `skill/tax-prep` ↔ `skill/tax-season-organizer`

### 2.4 Scope question for the steward

111 skills are non-engineering knowledge work (finance, legal, HR, sales,
marketing, support, small-business ops). The catalog's own description is "AI runtime primitives".
They are not broken — most are `keep` or `fix` on their merits — but they triple the catalog
size and dilute discovery for the stated consumers (Claude Code, Olympus, the `ai` CLI). Options:
keep and give them a `category` filter on the site; move them to a separate knowledge-work
catalog; or drop the import. This is a product decision, not a quality one.

### 2.5 House skills (authored_by convergent-systems-key, 51)

47 keep, 1 fix, 3 drop.
Drops: `skill/atom-status`, `skill/debug-systematically`, `skill/test-publish`.

## 3. Hooks — 18 atoms

Method: every `script` was extracted and run with `--self-check` (the contract `hook/lib`
documents), metadata was checked for internal consistency, and test coverage was tallied.

| Check | Result |
|---|---|
| `--self-check` | **16 of 16 runnable scripts pass** (with `hook/lib` installed as `_lib.py`) |
| Scripts present | 17 of 18; `hook/security-reminder` has **no `script`** and cannot be installed by `ai hooks install` |
| Tests | 6 of 18 hooks have a test module (`agentic-review`, `dirty-tree-guard`, `no-commented-code`, `push-guard`, `test-coverage-gate`, `worktree-guard`); 140 hook tests pass |
| Event typing | `hook/audit-logger` claims eight events but `event` is `PreToolUse`; `hook/dirty-tree-guard` and `hook/test-coverage-gate` fire on Stop **and** SubagentStop but `event` holds one value; `hook/secret-precommit` is a git pre-commit hook typed as `PreToolUse` |
| Private references | 10 descriptions cite `Common.md §…`, a private constitution file a public consumer cannot read |
| Safety | `hook/agentic-review` calls external LLM APIs and reads API keys from the environment — declared in `side_effects` and `platform_notes`, acceptable |

Verdicts: **keep 17, fix 1** (`security-reminder`: add the script or deprecate). Schema follow-up
worth doing: allow `event` to be an array, since three hooks already need it.


## 4. Migrated atoms from the retired catalogs

PR #46 staged 241 atoms and 52 compositions verbatim. None were in the published catalog
(the build skipped every class without a schema). After re-typing:

| Class | Published now | Source | Notes |
|---|---|---|---|
| persona | 48 | 39 persona-atoms compositions (minus the template) + 9 agent-atoms identities not covered by a composition | facets, constraints, and boundaries inlined |
| prompt | 59 | 61 prompt-atoms atoms − 1 template − 3 empty-content `none-*` + 2 compositions as `composite` | subtypes renamed to `format`, `refusal`, `tool-use` |
| agent | 12 | 10 agent-atoms identities + `runbook-executor` + `safe-by-default` | all `actor`; `reviewer` has zero instances |

### 4.1 Unresolved references in the retired data (16)

These personas referenced atoms that never existed in persona-atoms. The affected part was
omitted, not invented.

| persona | missing parts |
|---|---|
| `persona/convergent-systems-docs-writer` | voice_profile → clear-instructional (voice omitted); tone_parameters → instructional-clear (tone omitted) |
| `persona/documentation-writer` | voice_profile → clear-instructional (voice omitted); tone_parameters → instructional-clear (tone omitted) |
| `persona/incident-commander` | behavioural_constraints → prefer-reversible-actions (constraint omitted) |
| `persona/none` | role_definition → passthrough (role.job_to_be_done taken from the composition description); voice_profile → unframed (voice omitted); tone_parameters → neutral-unframed (tone omitted) |
| `persona/security-architect` | role_definition → security-architect (role.job_to_be_done taken from the composition description); behavioural_constraints → threat-scenarios-over-exploits (constraint omitted); knowledge_boundaries → security-domain (boundary omitted) |
| `persona/sre` | role_definition → site-reliability-engineer (role.job_to_be_done taken from the composition description); behavioural_constraints → prefer-reversible-actions (constraint omitted) |
| `persona/valkyre-ai-security-analyst` | role_definition → security-architect (role.job_to_be_done taken from the composition description); behavioural_constraints → threat-scenarios-over-exploits (constraint omitted); knowledge_boundaries → security-domain (boundary omitted) |

### 4.2 Verdicts on the migrated atoms

**Prompts (59).** Keep 52, fix 7. The vendor variants `sre-anthropic`/`sre-openai`/`sre-ollama`,
`documentation-writer-anthropic`/`-openai`, and `security-architect-anthropic`/`-openai` have
byte-identical `content`; collapse each group to one atom with `vendors: ["any"]` (−4 atoms).
Twelve `subtype: persona` prompts carry no `persona_ref` even though a matching persona often
exists (`code-reviewer-strict`, `debug-detective`, `refactor-scout`, ...); link them. `prompt/
no-fabrication` duplicates the constraint most personas already inline — fine as a standalone
prompt, but agents should not bind both.

**Personas (48).** Keep 31, fix 15, drop 2. Thirteen are thin (role only, no tone, constraints,
or boundaries) — the nine agent-atoms identities plus `code-reviewer`, `devops-engineer`,
`convergent-systems-docs-writer`, `documentation-writer`, and `none`. Four groups share the
same job to be done and differ only in voice or contract: `coding-assistant-strict` ↔
`senior-engineer-mentor`; `convergent-systems-docs-writer` ↔ `documentation-writer` ↔
`executor-document-writer` ↔ `technical-writer-docs`; `coordinator-devops-engineer` ↔
`devops-engineer-runbook`; `creative-challenger` ↔ `devils-advocate`. Recommended drops:
`persona/none` (pass-through with three missing parts; a runtime should model "no persona" as
absence) and `persona/valkyre-ai-security-analyst` (brand-bound, two missing parts, near-copy of
`security-architect` — or keep only if the brand binding is wanted).

**Agents (12).** Keep 4, fix 8. `code-reviewer`, `runbook-executor`, `safe-by-default` bind real
tools and policies; the other nine bind nothing but a persona and execution preferences, which
makes them personas with a planner attached. Either bind them (skills, tools, policies) or fold
them back into their persona. `runbook-executor` and `devops-engineer` share one persona.

### 4.3 Still staged and untyped

| Directory | Files | Recommendation |
|---|---|---|
| `atoms/policy/` | 54 | Type next (`policy-v1`, subtypes boundary/capability/isolation). Agents already reference 9 of them. 41 boundary atoms are also inlined into personas now — after typing, decide whether personas reference or inline. |
| `atoms/tool/` | 20 | Type as `tool-v1` with `tool_spec`; agents reference 7. |
| `atoms/workflow/` | 40 | Olympus step/gate primitives. Type or move to an Olympus-owned catalog; nothing here references them. |
| `workflows/` | 4 | Compositions collected into the catalog unvalidated; they reference `workflow-atoms/...` ids that no longer resolve. |
| `skills/project-workspace.json` | 1 | Retired skill left at the repo root, outside the build. Delete or move to `atoms/skill/` as `lifecycle: deprecated`. |

## 5. Summary of recommendations, in priority order

1. Fix the importer (CONNECTORS.md reference, YAML block-scalar descriptions) and re-import — clears ~72 `fix` verdicts at once.
2. Decide the scope question in §2.4 (111 knowledge-work skills).
3. Drop the 7 skills in §2.2, merge the 10 duplicate pairs in §2.3.
4. Add the missing `security-reminder` script; let `hook.event` be an array; strip `Common.md §` citations from public descriptions.
5. Collapse the 4 vendor-variant prompt groups; link persona prompts to their personas.
6. Merge the 4 persona groups; enrich or drop the 13 thin personas; bind or fold the 9 empty agents.
7. Type `policy` and `tool` so agent references validate against a schema, then decide `workflow`.

## Appendix A — every skill

| atom | verdict | scope | self-contained | duplicate of | fix |
|---|---|---|---|---|---|
| `skill/accessibility-review` | keep | core | yes |  |  |
| `skill/account-research` | keep | out-of-scope | yes |  |  |
| `skill/algorithmic-art` | fix | out-of-scope | no |  | Bundle templates/viewer.html and generator_template.js as atom assets or inline their contents. |
| `skill/amendment-author` | keep | core | yes |  |  |
| `skill/analyze` | keep | core | yes |  |  |
| `skill/analyzing-dotnet-performance` | keep | adjacent | yes |  |  |
| `skill/android-tombstone-symbolication` | fix | adjacent | no |  | Bundle scripts/Symbolicate-Tombstone.ps1 as an atom asset or remove the reference. |
| `skill/apple-crash-symbolication` | fix | adjacent | no |  | Bundle scripts/Symbolicate-Crash.ps1 and references/ips-crash-format.md or remove the links. |
| `skill/architecture` | keep | core | yes |  |  |
| `skill/assertion-quality` | keep | adjacent | yes |  |  |
| `skill/atom-publisher` | keep | core | yes |  |  |
| `skill/atom-state` | fix | core | yes |  | Correct invocation entries to /atom-state and treat as canonical over skill/atom-status. |
| `skill/atom-status` | drop | core | yes | skill/atom-state |  |
| `skill/atoms-discover` | keep | core | yes |  |  |
| `skill/audit-support` | keep | out-of-scope | yes |  |  |
| `skill/author-component` | keep | adjacent | yes |  |  |
| `skill/binlog-failure-analysis` | keep | adjacent | yes |  |  |
| `skill/binlog-generation` | keep | adjacent | yes |  |  |
| `skill/brainstorming` | keep | core | yes |  |  |
| `skill/brand-guidelines` | keep | adjacent | yes |  |  |
| `skill/brand-review` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/brief` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/build-dashboard` | fix | adjacent | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/build-parallelism` | keep | adjacent | yes |  |  |
| `skill/build-perf-baseline` | keep | adjacent | yes |  |  |
| `skill/build-perf-diagnostics` | keep | adjacent | yes |  |  |
| `skill/business-pulse` | drop | out-of-scope | no |  |  |
| `skill/call-list` | keep | out-of-scope | yes |  |  |
| `skill/call-prep` | keep | out-of-scope | yes |  |  |
| `skill/call-summary` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/campaign-plan` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/canva-creator` | drop | out-of-scope | no |  |  |
| `skill/canvas-design` | fix | out-of-scope | no |  | Bundle the canvas-fonts directory or remove the reference; reconsider the scripted fake user quote. |
| `skill/capacity-plan` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/cash-flow-snapshot` | drop | out-of-scope | no |  |  |
| `skill/change-request` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inside the atom or drop the reference. |
| `skill/check-bin-obj-clash` | keep | adjacent | yes |  |  |
| `skill/checkpoint` | keep | core | yes |  |  |
| `skill/claude-api` | fix | core | no |  | Bundle the shared/ and {lang}/ reference files inside the atom or inline the essential guidance. |
| `skill/cleanup` | keep | core | yes |  |  |
| `skill/close-management` | keep | out-of-scope | yes |  |  |
| `skill/close-month` | keep | out-of-scope | yes |  |  |
| `skill/clr-activation-debugging` | fix | adjacent | yes |  | Fix the stub description metadata; optionally bundle the reference/*.md files. |
| `skill/code-review` | fix | core | no |  | Bundle CONNECTORS.md alongside the atom or remove the reference. |
| `skill/code-testing-agent` | fix | core | no |  | Fix the stub description and bundle or verify the referenced prompt file and sub-agents. |
| `skill/code-testing-extensions` | drop | adjacent | no |  | Bundle all 12 extensions/*.md files inside the atom; until then it is non-functional as a catalog atom. |
| `skill/collect-user-input` | keep | adjacent | yes |  |  |
| `skill/commit` | keep | core | yes |  |  |
| `skill/comp-analysis` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/competitive-brief` | fix | out-of-scope | no | skill/competitive-intelligence | Bundle CONNECTORS.md; clarify differentiation from competitive-intelligence or merge the two. |
| `skill/competitive-intelligence` | fix | out-of-scope | yes | skill/competitive-brief | Differentiate scope from competitive-brief explicitly (sales HTML battlecard vs marketing brief) or merge. |
| `skill/compliance-check` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/compliance-tracking` | keep | out-of-scope | yes |  |  |
| `skill/configure-auth` | fix | adjacent | yes |  | Fix the stub description metadata (currently just '>'). |
| `skill/configuring-opentelemetry-dotnet` | keep | adjacent | yes |  |  |
| `skill/content-creation` | keep | out-of-scope | yes |  |  |
| `skill/content-strategy` | fix | out-of-scope | no |  | Bundle the reference files, fix the description, and strip the internal draft/owner header from the fragment. |
| `skill/contract-review` | fix | out-of-scope | no |  | Bundle the referenced reference/*.md files or strip the links. |
| `skill/convert-blazor-server-to-webapp` | keep | adjacent | yes |  |  |
| `skill/convert-to-cpm` | fix | adjacent | no |  | Bundle the referenced references/*.md files. |
| `skill/coordinate-components` | keep | adjacent | yes |  |  |
| `skill/coverage-analysis` | fix | adjacent | no |  | Bundle scripts/*.ps1 and references/*.md alongside the atom. |
| `skill/crap-score` | keep | adjacent | yes |  |  |
| `skill/create-an-asset` | keep | out-of-scope | yes |  |  |
| `skill/create-blazor-project` | fix | adjacent | no |  | Bundle the assets/agents-md/*.md templates. |
| `skill/create-viz` | fix | adjacent | no |  | Bundle CONNECTORS.md or drop the reference for standalone use. |
| `skill/crm-cleanup` | fix | out-of-scope | yes | skill/crm-maintenance | Merge as a documented alias/invocation of crm-maintenance rather than a separate atom. |
| `skill/crm-maintenance` | fix | out-of-scope | no |  | Bundle the referenced reference/*.md files. |
| `skill/csharp-scripts` | keep | adjacent | yes |  |  |
| `skill/customer-escalation` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or drop the reference. |
| `skill/customer-pulse` | fix | out-of-scope | no |  | Bundle reference/gotchas.md and reference/examples/example-report.md. |
| `skill/customer-pulse-check` | fix | out-of-scope | yes | skill/customer-pulse | Clarify as a customer-pulse variant (adds top-3 fixable + drafted replies) or merge. |
| `skill/customer-research` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or drop the reference. |
| `skill/daily-briefing` | keep | out-of-scope | yes |  |  |
| `skill/data-context-extractor` | fix | adjacent | no |  | Bundle references/skill-template.md, sql-dialects.md, domain-template.md or inline their content |
| `skill/data-visualization` | keep | adjacent | yes |  |  |
| `skill/debug` | keep | core | yes | skill/debug-systematically |  |
| `skill/debug-systematically` | drop | core | yes | skill/debug | Drop in favor of skill/debug; merge any unique wording first |
| `skill/defuddle` | keep | core | yes |  |  |
| `skill/deploy-checklist` | fix | core | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/design-critique` | fix | adjacent | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/design-handoff` | fix | adjacent | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/design-system` | fix | adjacent | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/detect-static-dependencies` | fix | adjacent | yes |  | Replace description with an actual sentence |
| `skill/diagram` | keep | core | yes |  |  |
| `skill/digest` | fix | adjacent | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/directory-build-organization` | fix | adjacent | no |  | Bundle the three references/*.md files or inline their content |
| `skill/dispatching-parallel-agents` | keep | core | yes |  |  |
| `skill/doc-coauthoring` | keep | core | yes |  |  |
| `skill/documentation` | keep | core | yes |  |  |
| `skill/dotnet-aot-compat` | fix | adjacent | no |  | Bundle references/polyfills.md and fix the description field |
| `skill/dotnet-maui-doctor` | fix | adjacent | no |  | Bundle the platform-specific references/*.md files and fix the description field |
| `skill/dotnet-pinvoke` | fix | adjacent | no |  | Bundle references/type-mapping.md and references/diagnostics.md; fix description |
| `skill/dotnet-test-frameworks` | keep | adjacent | yes |  |  |
| `skill/dotnet-trace-collect` | fix | adjacent | no |  | Bundle the referenced tool-specific reference files |
| `skill/dotnet-webapi` | fix | adjacent | yes |  | Replace description with an actual sentence |
| `skill/draft-content` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/draft-offer` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/draft-outreach` | keep | out-of-scope | yes |  |  |
| `skill/draft-response` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/dump-collect` | fix | adjacent | no |  | Bundle the three references/*.md files |
| `skill/email-sequence` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/eval-performance` | keep | adjacent | yes |  |  |
| `skill/exp-mock-usage-analysis` | keep | adjacent | yes |  |  |
| `skill/exp-simd-vectorization` | keep | adjacent | yes |  |  |
| `skill/exp-test-maintainability` | keep | adjacent | yes |  |  |
| `skill/explain` | keep | core | yes |  |  |
| `skill/explore-data` | fix | adjacent | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/extension-points` | keep | adjacent | yes |  |  |
| `skill/fetch-and-send-data` | keep | adjacent | yes |  |  |
| `skill/filter-syntax` | keep | adjacent | yes |  |  |
| `skill/financial-statements` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/finishing-a-development-branch` | keep | core | yes |  |  |
| `skill/forecast` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/friday-brief` | keep | out-of-scope | yes |  |  |
| `skill/frontend-design` | keep | core | yes |  |  |
| `skill/generate-testability-wrappers` | fix | adjacent | yes |  | Replace description with an actual sentence |
| `skill/handle-complaint` | keep | out-of-scope | yes |  |  |
| `skill/hook-author` | keep | core | yes |  |  |
| `skill/incident-response` | fix | core | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/including-generated-files` | keep | adjacent | yes |  |  |
| `skill/incremental-build` | keep | adjacent | yes |  |  |
| `skill/instrument-data-to-allotrope` | fix | out-of-scope | no |  | Bundle the scripts/ and references/ files this atom depends on, or drop the example framing |
| `skill/internal-comms` | fix | out-of-scope | no |  | Bundle the examples/*.md files that contain the actual formatting instructions |
| `skill/interview-prep` | keep | out-of-scope | yes |  |  |
| `skill/invoice-chase` | fix | out-of-scope | no |  | Bundle the reference/*.md files and fix the description field |
| `skill/item-management` | keep | adjacent | yes |  |  |
| `skill/job-post-builder` | fix | out-of-scope | no |  | Bundle the references/*.md and tests/*.md files, and the docx skill dependency |
| `skill/journal-entry` | fix | out-of-scope | no | skill/journal-entry-prep | Bundle CONNECTORS.md; consider merging journal-entry-prep's content into this atom |
| `skill/journal-entry-prep` | fix | out-of-scope | yes | skill/journal-entry | Merge unique reference content into skill/journal-entry and drop this atom |
| `skill/json-canvas` | fix | adjacent | no |  | Bundle references/EXAMPLES.md or remove the link |
| `skill/kb-article` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/knowledge-synthesis` | keep | adjacent | yes |  |  |
| `skill/lead-triage` | fix | out-of-scope | no |  | Bundle the reference/*.md files and fix the description field |
| `skill/legal-response` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the cross-reference |
| `skill/legal-risk-assessment` | keep | out-of-scope | yes |  |  |
| `skill/make` | keep | core | yes |  |  |
| `skill/make-atoms` | keep | core | yes |  |  |
| `skill/make-build` | keep | core | yes |  |  |
| `skill/make-clean` | keep | core | yes |  |  |
| `skill/make-doctor` | keep | core | yes |  |  |
| `skill/make-project` | keep | core | yes |  |  |
| `skill/make-release` | keep | core | yes |  |  |
| `skill/make-review` | keep | core | yes |  |  |
| `skill/make-sprint` | keep | core | yes |  |  |
| `skill/make-status` | keep | core | yes |  |  |
| `skill/make-sync` | keep | core | yes |  |  |
| `skill/make-test` | keep | core | yes |  |  |
| `skill/margin-analyzer` | fix | out-of-scope | no |  | Bundle the referenced reference/ files into the atom or inline their content. |
| `skill/maui-app-lifecycle` | keep | adjacent | yes |  |  |
| `skill/maui-collectionview` | keep | adjacent | yes |  |  |
| `skill/maui-data-binding` | keep | adjacent | yes |  |  |
| `skill/maui-dependency-injection` | keep | adjacent | yes |  |  |
| `skill/maui-safe-area` | keep | adjacent | yes |  |  |
| `skill/maui-shell-navigation` | fix | adjacent | no |  | Bundle references/shell-navigation-api.md or drop the reference. |
| `skill/maui-theming` | keep | adjacent | yes |  |  |
| `skill/mcp-builder` | fix | core | no |  | Bundle the reference/ directory (best practices, node/python guides, evaluation guide) with the atom. |
| `skill/mcp-csharp-create` | fix | adjacent | no |  | Bundle references/api-patterns.md and references/transport-config.md. |
| `skill/mcp-csharp-debug` | fix | adjacent | no |  | Bundle references/mcp-inspector.md and references/ide-config.md. |
| `skill/mcp-csharp-publish` | fix | adjacent | no |  | Bundle references/nuget-packaging.md, references/docker-azure.md, references/mcp-registry.md. |
| `skill/mcp-csharp-test` | fix | adjacent | no |  | Bundle references/test-patterns.md and references/evaluations.md. |
| `skill/meeting-briefing` | keep | out-of-scope | yes |  |  |
| `skill/memory-curator` | keep | core | yes |  |  |
| `skill/memory-management` | keep | core | yes |  |  |
| `skill/metrics-review` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/microbenchmarking` | fix | adjacent | no |  | Bundle the five referenced references/*.md files. |
| `skill/migrate-dotnet10-to-dotnet11` | fix | adjacent | no |  | Bundle the seven references/*.md breaking-change docs referenced by the workflow. |
| `skill/migrate-dotnet8-to-dotnet9` | fix | adjacent | no |  | Bundle the ten references/*.md breaking-change docs referenced by the workflow. |
| `skill/migrate-dotnet9-to-dotnet10` | fix | adjacent | no |  | Bundle the ten references/*.md breaking-change docs referenced by the workflow. |
| `skill/migrate-mstest-v1v2-to-v3` | keep | adjacent | yes |  |  |
| `skill/migrate-mstest-v3-to-v4` | keep | adjacent | yes |  |  |
| `skill/migrate-nullable-references` | fix | adjacent | no |  | Bundle the four references/*.md files and the optional readiness script, or note the script as optional tooling not required for core guidance. |
| `skill/migrate-static-to-wrapper` | keep | adjacent | yes |  |  |
| `skill/migrate-vstest-to-mtp` | keep | adjacent | yes |  |  |
| `skill/migrate-xunit-to-xunit-v3` | keep | adjacent | yes |  |  |
| `skill/minimal-api-file-upload` | keep | adjacent | yes |  |  |
| `skill/monday-brief` | keep | out-of-scope | yes |  |  |
| `skill/month-end-prep` | fix | out-of-scope | no |  | Bundle the five referenced reference/ files. |
| `skill/month-heads-up` | keep | out-of-scope | yes |  |  |
| `skill/msbuild-antipatterns` | fix | adjacent | no |  | Bundle the three referenced references/*.md files. |
| `skill/msbuild-modernization` | keep | adjacent | yes |  |  |
| `skill/msbuild-server` | keep | adjacent | yes |  |  |
| `skill/mtp-hot-reload` | keep | adjacent | yes |  |  |
| `skill/nextflow-development` | fix | out-of-scope | no |  | Bundle the scripts/ and references/ directories from the source repo; without them the skill is a checklist, not an executable workflow. |
| `skill/nuget-trusted-publishing` | fix | adjacent | no |  | Bundle references/package-types.md and references/publish-workflow.md. |
| `skill/obsidian-bases` | fix | adjacent | no |  | Bundle references/FUNCTIONS_REFERENCE.md. |
| `skill/obsidian-cli` | keep | adjacent | yes |  |  |
| `skill/obsidian-markdown` | fix | adjacent | no |  | Bundle references/PROPERTIES.md, references/EMBEDS.md, references/CALLOUTS.md. |
| `skill/onboard` | keep | core | yes |  |  |
| `skill/onboarding` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/optimizing-ef-core-queries` | keep | adjacent | yes |  |  |
| `skill/org-planning` | keep | out-of-scope | yes |  |  |
| `skill/people-report` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/performance-report` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/performance-review` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/pipeline-review` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/plan-payroll` | keep | out-of-scope | yes |  |  |
| `skill/plan-ui-change` | keep | adjacent | yes |  |  |
| `skill/platform-detection` | keep | adjacent | yes |  |  |
| `skill/policy-lookup` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/pr` | keep | core | yes |  |  |
| `skill/price-check` | fix | out-of-scope | yes | skill/margin-analyzer | Merge into margin-analyzer, or trim price-check to just its unique customer-messaging-brief output and delegate margin/scenario math to margin-analyzer. |
| `skill/process-doc` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/process-optimization` | keep | out-of-scope | yes |  |  |
| `skill/product-brainstorming` | keep | out-of-scope | yes |  |  |
| `skill/project` | keep | core | yes |  |  |
| `skill/project-claude` | keep | core | yes |  |  |
| `skill/project-copilot` | keep | core | yes |  |  |
| `skill/property-patterns` | keep | adjacent | yes |  |  |
| `skill/quarterly-review` | keep | out-of-scope | yes |  |  |
| `skill/receiving-code-review` | keep | core | yes |  |  |
| `skill/reconciliation` | keep | out-of-scope | yes |  |  |
| `skill/recruiting-pipeline` | keep | out-of-scope | yes |  |  |
| `skill/refactor` | keep | core | yes |  |  |
| `skill/repo` | keep | core | yes |  |  |
| `skill/requesting-code-review` | keep | core | yes |  |  |
| `skill/research-synthesis` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/resolve-project-references` | keep | adjacent | yes |  |  |
| `skill/review-contract` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/review-panel` | keep | core | yes |  |  |
| `skill/risk-assessment` | keep | out-of-scope | yes |  |  |
| `skill/roadmap-update` | fix | out-of-scope | no |  | Inline the connector-check guidance or bundle CONNECTORS.md; drop the dangling relative link. |
| `skill/run-campaign` | keep | out-of-scope | yes |  |  |
| `skill/run-tests` | fix | adjacent | yes |  | Replace the description field (currently the literal string '>') with real descriptive text. |
| `skill/runbook` | fix | core | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/sales-brief` | keep | out-of-scope | yes |  |  |
| `skill/scientific-problem-selection` | fix | out-of-scope | no |  | Bundle the nine references/*.md files the fragment repeatedly points to. |
| `skill/scvi-tools` | fix | out-of-scope | no |  | Bundle the scripts/ and references/ directories referenced throughout the fragment. |
| `skill/search` | fix | core | no | skill/search-strategy | Bundle CONNECTORS.md; consider merging with search-strategy so the algorithm lives in one place. |
| `skill/search-strategy` | fix | core | no | skill/search | Bundle CONNECTORS.md and consolidate the overlapping decomposition/ranking logic with skill/search. |
| `skill/seo-audit` | fix | out-of-scope | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/signature-request` | fix | out-of-scope | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/single-cell-rna-qc` | fix | out-of-scope | no |  | Bundle scripts/qc_analysis.py, qc_core.py, qc_plotting.py, and references/scverse_qc_guidelines.md. |
| `skill/skill-creator` | fix | core | no |  | Bundle the scripts/, agents/, references/, and assets/ directories the fragment depends on. |
| `skill/slack-gif-creator` | fix | out-of-scope | no |  | Bundle the core/ Python package (gif_builder.py, validators.py, easing.py, frame_composer.py). |
| `skill/smb-onboard` | fix | out-of-scope | no |  | Fix the broken description field and bundle reference/onboard-checklist.md, gotchas.md, and examples/happy-path.md. |
| `skill/smb-router` | fix | out-of-scope | yes |  | Replace the broken '>' description field with real descriptive text. |
| `skill/source-management` | fix | core | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/sox-testing` | fix | out-of-scope | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/sprint-planning` | fix | core | no |  | Bundle CONNECTORS.md with the atom or remove the dangling reference. |
| `skill/sql-queries` | keep | adjacent | yes |  |  |
| `skill/stakeholder-update` | fix | out-of-scope | no |  | Bundle CONNECTORS.md inline or drop the reference; skill still works standalone without connectors. |
| `skill/standup` | fix | core | no |  | Bundle or remove the CONNECTORS.md link. |
| `skill/start` | fix | out-of-scope | no |  | Bundle or remove the CONNECTORS.md reference. |
| `skill/statistical-analysis` | keep | adjacent | yes |  |  |
| `skill/status` | keep | core | yes |  |  |
| `skill/status-report` | fix | out-of-scope | no |  | Bundle/remove CONNECTORS.md and confirm risk-assessment atom exists before cross-referencing it. |
| `skill/subagent-driven-development` | keep | core | yes |  |  |
| `skill/support-prerendering` | keep | adjacent | yes |  |  |
| `skill/synthesize-research` | fix | out-of-scope | no |  | Bundle or remove the CONNECTORS.md reference. |
| `skill/system-design` | keep | core | yes |  |  |
| `skill/system-text-json-net11` | fix | adjacent | yes |  | Replace the description field with a real one-to-two-sentence summary. |
| `skill/systematic-debugging` | keep | core | yes |  |  |
| `skill/target-authoring` | keep | adjacent | yes |  |  |
| `skill/task-management` | fix | out-of-scope | no |  | Bundle dashboard.html with the atom or remove the copy-on-first-run step. |
| `skill/tax-prep` | fix | out-of-scope | yes | skill/tax-season-organizer | Merge into tax-season-organizer as a fast-path/no-discovery mode instead of duplicating its logic. |
| `skill/tax-season-organizer` | fix | out-of-scope | no |  | Bundle the five reference/*.md files or inline their essential content; fix the description field. |
| `skill/tech-debt` | keep | core | yes |  |  |
| `skill/technology-selection` | keep | adjacent | yes |  |  |
| `skill/template-authoring` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>' which breaks catalog search/discoverability. |
| `skill/template-discovery` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>'. |
| `skill/template-instantiation` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>'. |
| `skill/template-validation` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>'. |
| `skill/test` | keep | core | yes |  |  |
| `skill/test-anti-patterns` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>'. |
| `skill/test-driven-development` | keep | core | yes |  |  |
| `skill/test-gap-analysis` | keep | adjacent | yes |  |  |
| `skill/test-publish` | drop | out-of-scope | yes |  |  |
| `skill/test-smell-detection` | fix | adjacent | no |  | Bundle references/test-smell-catalog.md or remove the reference; fix stub description. |
| `skill/test-tagging` | keep | adjacent | yes |  |  |
| `skill/testing-strategy` | keep | core | yes |  |  |
| `skill/theme-factory` | fix | out-of-scope | no |  | Bundle theme-showcase.pdf and the themes/ directory inside the atom, or replace with inline theme specs. |
| `skill/thread-abort-migration` | fix | adjacent | yes |  | Replace description with real summary text; currently only '>'. |
| `skill/ticket-deflector` | fix | out-of-scope | no |  | Bundle the referenced reference/*.md files or remove the links; fix stub description. |
| `skill/ticket-triage` | fix | out-of-scope | no |  | Bundle CONNECTORS.md reference or replace with an inline note about checking connected tools. |
| `skill/triage-nda` | fix | out-of-scope | no |  | Bundle CONNECTORS.md reference or replace with an inline note about checking connected tools. |
| `skill/update` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or strip the reference so the atom is self-contained. |
| `skill/update-config` | keep | core | yes |  |  |
| `skill/use-js-interop` | fix | adjacent | yes |  | Restore the full description text from the source SKILL.md frontmatter instead of the literal '>'. |
| `skill/user-research` | keep | out-of-scope | yes |  |  |
| `skill/using-git-worktrees` | keep | core | yes |  |  |
| `skill/ux-copy` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference to make the atom self-contained. |
| `skill/validate-data` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/variance-analysis` | keep | out-of-scope | yes |  |  |
| `skill/vendor-check` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/vendor-review` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/verification-before-completion` | keep | core | yes |  |  |
| `skill/web-artifacts-builder` | fix | core | no |  | Bundle the init-artifact.sh and bundle-artifact.sh scripts with the atom or inline their logic. |
| `skill/webapp-testing` | fix | core | no |  | Bundle scripts/with_server.py and the examples/ directory with the atom. |
| `skill/write-conventional-commit` | keep | core | yes |  |  |
| `skill/write-query` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/write-spec` | fix | out-of-scope | no |  | Bundle CONNECTORS.md or remove the reference. |
| `skill/writing-mstest-tests` | fix | adjacent | yes |  | Restore the full description text from the source SKILL.md frontmatter. |
| `skill/writing-plans` | keep | core | yes |  |  |
| `skill/writing-skills` | keep | core | yes |  |  |


## Addendum — claudeskills.in skills and Ollama models (same day, later)

Two more sources were imported after the review above, plus a shared `category` vocabulary and
a structured `provenance` block on every class.

### claudeskills.in → 397 skills

| Fact | Value |
|---|---|
| Rows in the site's public table | 409 |
| Imported | 397 (12 slugs already existed and were skipped: architecture, brainstorming, canvas-design, commit, doc-coauthoring, finishing-a-development-branch, frontend-design, mcp-builder, skill-creator, theme-factory, using-git-worktrees, web-artifacts-builder) |
| License recorded | unknown: 368, Apache-2.0: 27, MIT: 2 |
| Author named in the SKILL.md frontmatter | 12 |
| Category (from the aggregator's own field) | other: 178, devops: 103, frontend: 77, security: 22, ai: 13, backend: 2, product: 1, testing: 1 |
| Reference unshipped `scripts/`, `references/`, or `assets/` | 76 |
| Fragment under 300 characters | 7 |

**The license question is real.** The site states no license for the aggregate and names no
per-skill author; it says it collects from the "awesome-claude" and "awesome-llm-apps" GitHub lists.
368 of the imported atoms therefore carry `provenance.license: unknown`, are
`lifecycle: draft`, and are shown with an "unknown" license chip. The catalog's CC-BY-4.0 covers
its own metadata only. Before any commercial redistribution, these need per-atom license
discovery (most SKILL.md files name their upstream repository in `source`). The steward can also
decide to drop the `unknown` set wholesale; the importer is idempotent either way.

Not imported: the table's `path` column, which is the operator's local filesystem path.

Quality, from the same rubric as §2: 76 reference bundle files that do not ship, and
178 arrived with category `other` because that is what the aggregator recorded.
They were not individually read; the §2 evaluators' rubric applies unchanged and can be re-run.

### ollama.com/library → 239 models

| Fact | Value |
|---|---|
| Models on the library page | 239 |
| Task (inferred from name and capability badges) | text-generation: 127, reasoning: 46, code-generation: 31, multimodal: 23, embedding: 12 |
| Vendor inferred by the name table | 227; `unknown`: 12 (laguna-s-2.1, laguna-xs-2.1, laguna-xs.2, minicpm-v, minicpm-v4.5, minicpm-v4.6, muse-glimmer, north-mini-code-1.0, ornith, ornith-1.5, rnj-1, translategemma) |
| Fields taken verbatim from the listing | description, capability badges, sizes, pulls, tag count, updated date |
| Weights license | not published on the listing; recorded as `unknown` on every atom |

Recommendation: keep all 239 (the data is current and the provider link is the point), fix the
12 unknown vendors by extending the importer's table, and fold in model-atoms.com's 77 Cloudflare
cards as additional `providers[]` entries where names match.

### Categories and provenance backfill

Every atom now has a `category`; 244 GitHub-imported skills and 119 re-typed atoms gained a
`provenance` block with the license their repository publishes. Four personas could only be
categorised `other` (`creative-challenger`, `devils-advocate`, `none`, `triage-agent`), and the
hook/prompt/agent categories were assigned by keyword and are reviewable.
