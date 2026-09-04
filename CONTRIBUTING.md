# Contributing — ai-atoms

**Audience:** contributors adding or changing atoms.

## Adding an atom

1. Fork the repository.
2. Pick the class: `skill`, `hook`, `prompt`, `agent`, `persona`, `model`, `policy`, `tool`,
   `template`, or `bundle`. The [builder](https://ai-atoms.com/builder/) generates a valid
   starting file for any class.
3. Create `atoms/<class>/<slug>.json`. The `id` must be `<class>/<slug>`.
4. Validate locally:
   ```bash
   pip install jsonschema pytest
   python3 scripts/build-exports.py
   python3 -m pytest
   ```
   The build fails on schema errors and on any reference to an atom that does not exist.
5. Open a pull request. Merges use merge commits; squash merging is not used.

## Class-specific rules

- **skill** — `system_prompt_fragment` must be self-contained. Do not reference files
  (`scripts/`, `references/`, `../CONNECTORS.md`) that are not shipped inside the atom.
- **hook** — carry the full `script` inline, honour `--self-check`, depend only on the Python
  standard library plus `hook/lib`, and add a test under `atoms/hook/tests/`.
- **prompt** — `content` is the injected text, verbatim. One prompt per idea; use a
  `composite` prompt with `includes` to bundle.
- **persona** — inline every constraint and boundary as text. A persona binds no tools or
  skills; that is what an agent is for.
- **agent** — every `persona`, `prompts`, `skills`, `hooks`, `tools`, and `policies` entry
  must resolve. Reviewers must declare `review_criteria`.
- **model** — at least one `providers[]` entry with the provider's own `model_id` and page
  `url`. Do not guess `vendor`; write `unknown`.
- **bundle** — every `files[].content` must be fully inlined; a bundle never references a file
  it does not ship. `entry_point` must match one `files[].path` exactly. Prefer a `skill` atom
  when the whole capability fits in one `system_prompt_fragment` — reach for `bundle` only when
  it genuinely doesn't (agent personas, contracts, runtime code, or docs beyond the entry point).

## Category and provenance

Give every atom a `category` from `schemas/common-v1.json`; the site's category pages and
`ai skills categories` read it. An atom copied from anywhere else carries `provenance` with
`source`, `source_url`, and `license` — write `unknown` rather than guessing a license. The
import scripts under `scripts/` do this for their sources and never overwrite an existing slug.

## Requirements

- Python 3.10+ with `jsonschema` and `pytest`
- Node 22 for the web build (`cd web && npm ci && npm run build`)
- `build-exports.py` must exit 0 with no validation errors

## Attribution

Imported atoms carry `authored_by` and `source_url` pointing at the original file. Keep both
when editing an imported atom; bump `version` per SPEC.md.

## Lifecycle

New atoms start at `lifecycle: draft`. When the atom has been used in production and its
schema and semantics are stable, it graduates to `lifecycle: stable`. Deprecated atoms
retain their files and gain `lifecycle: deprecated` with a deprecation note in `description`.
