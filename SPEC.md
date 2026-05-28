# Specification — ai-atoms

## Two schemas

ai-atoms defines two JSON Schemas for its two atom classes.

### skill-v1.json

**`$id`:** `https://ai-atoms.com/schemas/skill-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema` | string (const) | yes | Must equal `https://ai-atoms.com/schemas/skill-v1.json` |
| `type` | enum | yes | Must be `"skill"` |
| `id` | string | yes | Pattern: `^skill/[a-z0-9][a-z0-9-]*$` |
| `version` | string | yes | Semver: `^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$` |
| `name` | string | yes | Max 80 characters |
| `description` | string | yes | Max 1000 characters |
| `system_prompt_fragment` | string | yes | Self-contained prompt fragment for agent system context |
| `applicable_domains` | array of strings | yes | At least one domain (e.g. `code`, `debug`, `planning`) |
| `invocation_contract` | object | no | Declared inputs, outputs, side_effects |
| `authored_by` | string | no | Key atom ID or author identifier |
| `tags` | array of strings | no | Max 40 chars each, unique |
| `lifecycle` | enum | no | `draft`, `stable`, or `deprecated` |

### hook-v1.json

**`$id`:** `https://ai-atoms.com/schemas/hook-v1.json`

| Field | Type | Required | Notes |
|---|---|---|---|
| `schema` | string (const) | yes | Must equal `https://ai-atoms.com/schemas/hook-v1.json` |
| `type` | enum | yes | Must be `"hook"` |
| `id` | string | yes | Pattern: `^hook/[a-z0-9][a-z0-9-]*$` |
| `version` | string | yes | Semver: `^[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?$` |
| `name` | string | yes | Max 80 characters |
| `description` | string | yes | Max 1000 characters |
| `event` | string | yes | AI tool event name (e.g. `PreToolUse`, `PostToolUse`, `SessionStart`, `Stop`) |
| `language` | enum | yes | `python`, `bash`, `javascript`, or `typescript` |
| `trigger` | object | yes | `type` (enum) + optional `pattern` string |
| `script_path` | string | no | Relative path to implementation script |
| `blocking` | boolean | no | Whether the hook can abort the triggering operation |
| `side_effects` | array of strings | no | Observable effects |
| `authored_by` | string | no | Key atom ID or author identifier |
| `tags` | array of strings | no | Max 40 chars each, unique |
| `lifecycle` | enum | no | `draft`, `stable`, or `deprecated` |

## ID patterns

- Skills: `skill/<slug>` — slug is lowercase alphanumeric with hyphens
- Hooks: `hook/<slug>` — slug is lowercase alphanumeric with hyphens

## Versioning rules

All atoms use semantic versioning (`MAJOR.MINOR.PATCH`):
- **MAJOR** — breaking change to the `system_prompt_fragment` or schema field semantics
- **MINOR** — additive changes (new optional fields, expanded description)
- **PATCH** — corrections, typo fixes, clarifications with no behavioral change

## Catalog format

`exports/catalog.json` shape:
```json
{
  "catalog": "ai-atoms",
  "version": "0.1.0",
  "built_at": "<ISO-8601>",
  "atoms": [...],
  "compositions": [...],
  "rules": []
}
```
