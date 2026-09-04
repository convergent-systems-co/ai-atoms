# Architecture — ai-atoms

**Audience:** contributors and future maintainers.

## Overview

ai-atoms is a typed, versioned catalog of AI runtime primitives. It contains nine atom classes,
each with its own JSON Schema, validated at build time. Three of the classes are parts a runtime
uses directly (skill, hook, prompt); one is an identity (persona); one composes an identity with
the parts it runs with (agent); one is reference data (model). Every class shares two fields
defined once in `schemas/common-v1.json`: `category` (one vocabulary for browsing across classes)
and `provenance` (where an imported atom came from and under what license).

## Nine atom classes

| Class | Runtime action | Directory | Schema |
|---|---|---|---|
| `skill` | invokes a bounded capability; injects `system_prompt_fragment` | `atoms/skill/` | `schemas/skill-v1.json` |
| `hook` | fires on a runtime event (`PreToolUse`, `Stop`, ...) | `atoms/hook/` | `schemas/hook-v1.json` |
| `prompt` | injects `content` into the context window; `subtype` says what kind of text | `atoms/prompt/` | `schemas/prompt-v1.json` |
| `persona` | renders an identity (role, voice, tone, work contract, constraints, boundaries) | `atoms/persona/` | `schemas/persona-v1.json` |
| `agent` | binds one persona to prompts, skills, tools, policies, hooks, and execution preferences | `atoms/agent/` | `schemas/agent-v1.json` |
| `model` | looks up reference data: vendor, task, sizes, and `providers[]` with the id and command a runtime needs | `atoms/model/` | `schemas/model-v1.json` |
| `policy` | permits, forbids, or bounds: boundaries, capability grants, isolation | `atoms/policy/` | `schemas/policy-v1.json` |
| `tool` | exposes an executable affordance: the signature the model sees and the side effects to gate | `atoms/tool/` | `schemas/tool-v1.json` |
| `template` | renders a document by filling `{{placeholders}}` in a skeleton: ADR, runbook, handoff, plan, PR, postmortem | `atoms/template/` | `schemas/template-v1.json` |

Atoms are keyed by `<class>/<slug>`. The file name is `atoms/<class>/<slug>.json`.

### skill
Skills are bounded, invocable units of AI capability. A skill bundles a `system_prompt_fragment`
that can be injected into any AI agent's system context, along with a declared `invocation_contract`
(inputs, outputs, side effects).

### hook
Hooks are event-driven runtime behaviors wired into AI tool infrastructure. A hook declares the
`event` it responds to, the `language` of its implementation, a `trigger`, whether it is
`blocking`, and carries its `script` inline so `ai hooks install` can materialise it.

### prompt
Prompts are text a runtime injects into a model's context window. The `subtype` is the
discriminator: `persona`, `constraint`, `format`, `output-schema`, `refusal`, `tool-use`, or
`composite`. A composite prompt lists the prompts it was assembled from in `includes`; its
`content` is the resolved concatenation so consumers never have to resolve it themselves.

### persona
A persona is a portable identity and binds nothing else. Role, voice, tone, work contract,
behavioural constraints, and knowledge boundaries are all carried **inline as text** so a runtime
can render the persona without resolving references. The retired `role-definition`,
`voice-profile`, `tone-parameter`, `work-contract`, `behavioural-constraint`, and
`knowledge-boundary` atom types from persona-atoms became fields of this class.

### agent
An agent is a persona bound to what it runs with. `subtype` is `actor` (produces work) or
`reviewer` (judges work against `review_criteria`). Every reference — `persona`, `prompts`,
`skills`, `hooks`, `tools`, `policies` — is an atom id and must resolve at build time.

### model
A model atom describes one AI model and where to get it. `providers[]` carries one entry per
hosting provider with the provider's own `model_id`, page `url`, and (when the provider has one)
a `pull_command`. Today every model atom comes from the Ollama library; the schema takes any
number of providers so the same model can list Cloudflare Workers AI or a vendor API later.

## Importers

| Script | Source | License handling |
|---|---|---|
| `scripts/import-anthropic-skills.py` | anthropics/knowledge-work-plugins, anthropics/skills, dotnet/skills, kepano/obsidian-skills | Apache-2.0 / MIT per repository |
| `scripts/import-claudeskills.py` | claudeskills.in (public Supabase table behind the site) | `provenance.license` from the SKILL.md frontmatter or the aggregator's `source` field; `unknown` otherwise |
| `scripts/import-ollama-models.py` | https://ollama.com/library (HTML listing) | weights license not published on the listing; recorded as `unknown` |
| `scripts/migrate-retired-atoms.py` | the retired persona-, prompt-, agent-atoms copies staged by PR #46 | Apache-2.0 (LICENSE-data in each retired repo) |
| `scripts/migrate-policy-tool.py` | the staged policy and tool trees from the same PR | Apache-2.0 |
| `scripts/discover-licenses.py` | GitHub API for atoms whose provenance names an upstream repository | fills `provenance.license` with the repository's SPDX id |
| `scripts/import-cloudflare-models.py` | model-atoms.com (Cloudflare Workers AI cards) | adds a Cloudflare `providers[]` entry to the matching Ollama atom, or a new atom; weights license recorded as `unknown` |
| `scripts/import-house-templates.py` | `~/.ai/templates/*.md` (the house ADR, agent, and persona templates) | MADR text MIT OR CC0-1.0; house text CC-BY-4.0; free-form placeholders renamed to `{{snake_case}}` with the original guidance kept as descriptions |
| `scripts/repair-descriptions.py` | the original SKILL.md, from GitHub or the claudeskills table | re-reads descriptions the old importer mangled; follows moved files |

All SKILL.md frontmatter is parsed by `scripts/skillmd.py`, which understands folded and literal
block scalars (the source of the old `description: ">"` defect).
| `scripts/backfill-provenance-category.py` | the current tree | fills missing `category` and `provenance`; never overwrites |

Importers never overwrite an existing atom with the same slug, so the first attribution wins.

### policy and tool
A policy is one rule: `effect` says what it does, `rule.text` is the rule as read, and the
subtype-specific fields beside it make it checkable (grants and elevation for a capability; process,
network, and filesystem for isolation; domains and refusals for a boundary). A tool carries the
function signature a model sees and the `side_effects` a runtime must gate with a capability policy.
Agents reference both by id; the build resolves every reference.

### template
A template is a document skeleton a runtime fills. `body` carries the skeleton with `{{name}}`
placeholders, `placeholders` says what each one wants, `rules` carries the constraints a skeleton
cannot express, and `example` shows one finished instance. The first eight are the documents the
convergent-systems constitution requires. Blank starting files for authoring atoms are not
templates; they live in `schemas/examples/`.

## Compositions

`workflows/` holds four Olympus workflow compositions from the retired workflow-atoms catalog.
They are collected into the catalog unvalidated and reference `workflow-atoms/...` step and gate
ids that no longer exist anywhere; they are kept as the only surviving copies until a workflow
class is designed.

## Build pipeline

```
atoms/skill/*.json   ──┐
atoms/hook/*.json    ──┤
atoms/prompt/*.json  ──┼─► scripts/build-exports.py ──► exports/catalog.json
atoms/agent/*.json   ──┤        │  validate each class against its schema
atoms/persona/*.json ──┤        │  fail on any dangling cross-atom reference
atoms/model/*.json   ──┤        │  index atoms by category
atoms/policy/*.json  ──┤
atoms/tool/*.json    ──┤
atoms/template/*.json──┘
                                ▼
                     web/public/exports/catalog.json
                                │
                                ▼
                       Astro static build (web/)
                       /atoms/<class>/           listing
                       /atoms/<class>/<slug>/    detail page
                       /atoms/<class>/<slug>.json the atom, verbatim
                       /categories/<slug>/       every class in one category
                       /categories/<slug>.json   ids in a category, by class
                       /ai/index.json            discovery index
                       /llms.txt                 plain-text map for language models
                       /search-index.json        one small record per atom, for the site search
                       /start/                   directions for humans and for AI agents
                                │
                                ▼
                    Cloudflare Pages (ai-atoms.com)
```

1. `scripts/build-exports.py` walks `atoms/<class>/` for each class with a schema, validating
   every JSON file. It then resolves every cross-atom reference. Exits 1 on any failure.
2. It writes `exports/catalog.json` — the machine-readable catalog manifest, including
   `classes`, per-class `counts`, and a per-category `categories` index.
3. The Astro web build (`web/`) copies the catalog via the `prebuild` npm script, then builds
   a static site served at `https://ai-atoms.com`. Every page uses `web/src/layouts/Site.astro`
   (head, top bar, search palette, theme toggle, footer) and the design system in
   `web/src/styles/site.css`; components under `web/src/components/` render cards, the listing
   filter rail, the detail action rail, provenance, and the daily specimens. The site has no
   runtime dependency on another host except Google Fonts.
4. CI runs the catalog build, the build-script tests (`scripts/tests/`), the hook tests
   (`atoms/hook/tests/`), and the web build on every PR and push. Deployment to Cloudflare Pages
   runs on push to `main`.

## Infrastructure

Terraform in `infra/terraform/` provisions the Cloudflare Pages project and DNS records for
`ai-atoms.com`. State is stored in an R2-backed S3 backend.

## Decisions

Architecture decisions are recorded in `docs/adr/`.
