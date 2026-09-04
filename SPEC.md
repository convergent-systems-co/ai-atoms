# Specification — ai-atoms

**Audience:** contributors writing atoms; runtime authors consuming them.

## Common envelope

Every atom, regardless of class, carries these fields. Validation is per class, but the envelope
is identical so a single reader can dispatch on `type`.

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema` | string (const) | yes | `https://ai-atoms.com/schemas/<class>-v1.json` |
| `type` | enum | yes | The class name |
| `id` | string | yes | Pattern: `^<class>/[a-z0-9][a-z0-9-]*$` |
| `version` | string | yes | Semver: `^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$` |
| `name` | string | yes | Max 80 characters |
| `description` | string | yes | Max 1000 characters |
| `authored_by` | string | no | Key atom ID or author identifier |
| `source_url` | string | no | Original file when imported from an external repository |
| `category` | enum | no | One of the shared categories below; used to browse across classes |
| `provenance` | object | no | `source` (required), `source_url`, `author`, `license`, `imported_at`, `notes` |
| `tags` | array of strings | no | Max 40 chars each, unique |
| `lifecycle` | enum | no | `draft`, `stable`, or `deprecated` |

All schemas set `additionalProperties: false`. `category` and `provenance` are defined once in
`schemas/common-v1.json` and referenced by every class schema.

### Categories

`coding`, `frontend`, `backend`, `devops`, `security`, `testing`, `dotnet`, `data`, `ai`, `design`,
`product`, `operations`, `finance`, `legal`, `sales`, `marketing`, `hr`, `support`, `knowledge`,
`research`, `governance`, `other`. Display names are in the schema description.

### Provenance

`provenance.license` is an SPDX id or the source's own name for its license. `unknown` means the
source stated none; the atom is redistributed under the source's terms and should be reviewed
before commercial use. `provenance.source` names the catalog, site, or repository; `source_url`
is the original record; `author` is the original author when known.

## skill-v1.json

**`$id`:** `https://ai-atoms.com/schemas/skill-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `system_prompt_fragment` | string | yes | Self-contained prompt fragment for agent system context |
| `applicable_domains` | array of strings | yes | At least one domain (e.g. `code`, `debug`, `planning`) |
| `category` | enum | no | Single primary category for grouping |
| `depends_on` | array of skill ids | no | Sub-skills installed with this one (dispatcher pattern) |
| `invocation_contract` | object | no | Declared inputs, outputs, side_effects |
| `invocation` | array of strings | no | Slash-command forms, e.g. `/debug "<symptom>"` |

## hook-v1.json

**`$id`:** `https://ai-atoms.com/schemas/hook-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `event` | string | yes | `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`, ... Empty for `trigger.type = library` |
| `language` | enum | yes | `python`, `bash`, `javascript`, or `typescript` |
| `trigger` | object | yes | `type` (`tool-name`, `file-pattern`, `always`, `tool-category`, `library`) + optional `pattern` |
| `script` | string | no | Complete source; installed to `~/.ai/hooks/<slug>.<ext>` |
| `script_path` | string | no | Relative path to implementation script |
| `blocking` | boolean | no | Whether the hook can abort the triggering operation |
| `side_effects` | array of strings | no | Observable effects |
| `platforms` | array of enum | no | `linux`, `macos`, `windows`; omit for all |
| `platform_notes` | string | no | Platform-specific behaviour |
| `depends_on` | array of hook ids | no | e.g. `hook/lib` |
| `requires_wrap` | object | no | `binary`, `description`, `install_hint` when full coverage needs a command wrapper |
| `events` | array of strings | no | Every event to wire when the hook fires on more than one; `event` stays the primary |

## prompt-v1.json

**`$id`:** `https://ai-atoms.com/schemas/prompt-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `subtype` | enum | yes | `persona`, `constraint`, `format`, `output-schema`, `refusal`, `tool-use`, `composite` |
| `content` | string | yes | The injected text, verbatim. For `composite`, the resolved concatenation of `includes` |
| `applicable_turns` | array of enum | no | `system`, `user`, `assistant`, `tool`; omit means system |
| `vendors` | array of strings | no | e.g. `any`, `anthropic`, `openai`, `ollama` |
| `persona_ref` | persona id | no | For `subtype: persona`, the persona this text renders |
| `includes` | array of prompt ids | composite only | Parts in order; every entry must resolve |

## persona-v1.json

**`$id`:** `https://ai-atoms.com/schemas/persona-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | object | yes | `job_to_be_done` (required), `primary_tasks`, `out_of_scope`, `domain`, `expertise` |
| `voice` | object | no | `formality`, `hedging_tolerance`, `sentence_length`, `style_notes` |
| `tone` | object | no | `warmth` (`cold`, `neutral`, `warm`, `empathetic`), `directness` (`direct`, `balanced`, `gentle`) |
| `work_contract` | object | no | `class` (`planner`, `executor`, `reviewer`, `coordinator`, `aggregator`, `moderator`) and `goal` required; inputs, allowed/forbidden actions, outputs, handoffs, escalation, done criteria, decision scope |
| `constraints` | array of objects | no | `{name, text, effect}` — behavioural constraints, inline |
| `knowledge_boundaries` | array of objects | no | `{name, text, covered_domains, excluded_domains}` |
| `system_prompt_fragment` | string | no | Hand-written identity text; runtimes render one from the fields when absent |
| `brand_ref` | string | no | brand-atoms reference this persona is bound to |
| `vendors` | array of strings | no | `any` for vendor-neutral |

A persona binds no tools, skills, or policies. That is what makes it portable.

## agent-v1.json

**`$id`:** `https://ai-atoms.com/schemas/agent-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `subtype` | enum | yes | `actor` (produces work) or `reviewer` (judges work) |
| `persona` | persona id | yes | The persona this agent embodies |
| `prompts` | array of prompt ids | no | Injected in order after the persona |
| `skills` | array of skill ids | no | |
| `tools` | array of tool ids | no | `tool/<slug>`; must exist under `atoms/tool/` |
| `policies` | array of policy ids | no | `policy/<slug>`; must exist under `atoms/policy/` |
| `hooks` | array of hook ids | no | |
| `execution` | object | no | `planner` (`none`, `react`, `plan-and-execute`, `tree-of-thoughts`), `memory` (`none`, `scratchpad`, `short-term`, `long-term`, `vector`), `supervisor` |
| `review_criteria` | array of strings | reviewer only | Criteria verdicts are judged against |

## model-v1.json

**`$id`:** `https://ai-atoms.com/schemas/model-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `vendor` | string | yes | Organisation that trained the model; `unknown` when the provider does not say |
| `family` | string | no | Model family or series |
| `task` | enum | yes | `text-generation`, `code-generation`, `reasoning`, `embedding`, `vision`, `image-generation`, `speech-to-text`, `text-to-speech`, `multimodal`, `translation`, `reranking`, `other` |
| `capabilities` | array of strings | no | Feature flags: tools, vision, thinking, embedding, cloud, ... |
| `parameter_sizes` | array of strings | no | Provider notation: `1b`, `3b`, `8x7b`, `335m` |
| `context_window_tokens` | integer | no | Maximum context length |
| `license` | string | no | Weights license |
| `providers` | array of objects | yes (≥1) | `name`, `model_id`, `url` required; `pull_command`, `run_command`, `tag_count`, `pulls`, `updated_at` optional |
| `links` | object | no | `homepage`, `model_card`, `paper`, `weights` |
| `planned_deprecation` | boolean | no | |
| `replacement` | model id | no | Recommended replacement when deprecated |

Model ids allow dots (`model/llama3.2`) because model names carry versions.

## policy-v1.json

**`$id`:** `https://ai-atoms.com/schemas/policy-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `subtype` | enum | yes | `boundary`, `capability`, `isolation` |
| `effect` | enum | yes | `forbid`, `require`, `permit`, `bound` |
| `rule` | object | yes | `text` required. Boundary: `boundary_type`, `covered_domains`, `excluded_domains`, `refusals`, `escalate_to`. Capability: `grants` and `elevation` required, `audit`. Isolation: `process`, `network`, `filesystem` required, `scoped_paths` |
| `rationale` | string | no | Why the rule exists |
| `vendors` | array of strings | no | |

## tool-v1.json

**`$id`:** `https://ai-atoms.com/schemas/tool-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `subtype` | enum | yes | `command`, `http`, `mcp`, `builtin` |
| `spec` | object | yes | `function_name` (snake_case), `summary`, `returns` required; `parameters` (name → type, description, required); `side_effects` from `fs-read`, `fs-write`, `exec`, `network`, `user-prompt` |
| `gated_by` | array of policy ids | no | Policies that must permit the tool |

## Reference resolution

The build fails on any reference that does not resolve:

| Owning class | Field | Must resolve to |
|---|---|---|
| agent | `persona` | a persona atom |
| agent | `prompts`, `skills`, `hooks` | atoms of that class |
| agent | `tools`, `policies` | atoms of that class |
| tool | `gated_by` | policy atoms |
| prompt | `persona_ref` | a persona atom |
| prompt | `includes` | prompt atoms |
| skill, hook | `depends_on` | atoms of the same class |

## ID patterns

`<class>/<slug>` — slug is lowercase alphanumeric with hyphens. The directory name, the `type`
field, and the id prefix must agree; the build rejects mismatches.

## Versioning rules

All atoms use semantic versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR** — breaking change to the operative text (`system_prompt_fragment`, `content`,
  `script`, persona fields) or to schema field semantics
- **MINOR** — additive changes (new optional fields, expanded description)
- **PATCH** — corrections, typo fixes, clarifications with no behavioral change

## Catalog format

`exports/catalog.json` shape:
```json
{
  "catalog": "ai-atoms",
  "version": "0.4.0",
  "built_at": "<ISO-8601>",
  "classes": ["skill", "hook", "prompt", "agent", "persona", "model", "policy", "tool"],
  "counts": {"skill": 0, "hook": 0, "prompt": 0, "agent": 0, "persona": 0, "model": 0, "policy": 0, "tool": 0},
  "categories": {"security": {"skill": 0, "hook": 0}},
  "atoms": [...],
  "compositions": [...],
  "rules": []
}
```

## Endpoints

| Path | Returns |
|---|---|
| `/exports/catalog.json` | The whole catalog |
| `/ai/index.json` | Classes, every atom id, endpoint and schema URLs |
| `/atoms/<class>/<slug>.json` | One atom, verbatim |
| `/atoms/<class>/<slug>/` | Human-readable detail page with copy, download, raw JSON, and install command |
| `/categories/<slug>/` | Every class in one category |
| `/categories/<slug>.json` | Ids in one category, grouped by class |
| `/schemas/common-v1.json` | Shared category and provenance definitions |
| `/schemas/<class>-v1.json` | The class schema |
