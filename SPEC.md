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
| `provenance` | object | no | Where the atom came from — see [Provenance](#provenance) |
| `source_url` | string | no | URL of the original source file (legacy; prefer `provenance.source_url`) |
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
| `provenance` | object | no | Where the atom came from — see [Provenance](#provenance) |
| `tags` | array of strings | no | Max 40 chars each, unique |
| `lifecycle` | enum | no | `draft`, `stable`, or `deprecated` |

## Provenance

Every atom that did not originate in this catalog must carry a `provenance`
block so the original author keeps credit and downstream consumers can check
redistribution terms.

| Field | Type | Required | Notes |
|---|---|---|---|
| `source` | string | yes | Stable identifier of the upstream, e.g. `anthropics/knowledge-work-plugins`, `claudeskills.in` |
| `source_type` | enum | no | `first-party`, `github-repo`, `catalog-site`, `documentation`, `community`, `unknown` |
| `source_url` | string | no | URL of the original artifact upstream |
| `author` | string | no | Original author or maintainer to credit, as named upstream |
| `license` | string | no | SPDX id (`Apache-2.0`, `MIT`, `CC-BY-4.0`), or `unknown` |
| `retrieved_at` | string | no | `YYYY-MM-DD` the atom was pulled |
| `modified` | boolean | no | Whether the content was changed from the upstream original |
| `notes` | string | no | Attribution or licensing caveats a redistributor needs (max 500 chars) |

`license: "unknown"` is a signal, not a default: it means redistribution has
**not** been cleared for that atom. `source_type: first-party` marks work
authored in this catalog.

### Sources in this catalog

| Source | Atoms | Credit | License |
|---|---:|---|---|
| `anthropics/knowledge-work-plugins` | 134 | Anthropic | Apache-2.0 |
| `dotnet/skills` | 92 | .NET Foundation and contributors | MIT |
| `anthropics/skills` | 13 | Anthropic | Apache-2.0 (mixed-license repo; only the OSS skills are imported) |
| `kepano/obsidian-skills` | 5 | kepano | MIT |
| `convergent-systems-co/ai-atoms` | 69 | Convergent Systems | Apache-2.0 |
| [`claudeskills.in`](https://claudeskills.in/) | 397 | Individual upstream authors where the aggregator recorded one, otherwise "claudeskills.in contributors" | **unknown** |

[claudeskills.in](https://claudeskills.in/) is a community aggregator that
re-hosts SKILL.md files from across the ecosystem. It publishes no license and
no terms of use, so its atoms carry `license: "unknown"` and
`lifecycle: "draft"`, and are tagged `claudeskills.in` so the whole set can be
filtered or withdrawn. Each one links back to its page on the aggregator via
`provenance.source_url`, and names the original repo in `provenance.notes`
where one was recorded. **Do not redistribute these until terms are cleared.**

Re-run either importer to refresh:

```bash
python3 scripts/import-anthropic-skills.py [--dry-run]
python3 scripts/import-claudeskills.py [--dry-run]
```

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
