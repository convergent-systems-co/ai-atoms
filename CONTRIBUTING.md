# Contributing — ai-atoms

## Adding a skill atom

1. Fork the repository.
2. Create a JSON file in `atoms/skill/<slug>.json`.
3. Ensure it validates against `schemas/skill-v1.json`:
   ```bash
   python3 scripts/build-exports.py
   ```
4. Open a pull request.

## Adding a hook atom

1. Fork the repository.
2. Create a JSON file in `atoms/hook/<slug>.json`.
3. Ensure it validates against `schemas/hook-v1.json`:
   ```bash
   python3 scripts/build-exports.py
   ```
4. Open a pull request.

## Requirements

- Python 3.10+ with `jsonschema` installed (`pip install jsonschema`)
- `build-exports.py` must exit 0 with no validation errors

## ID conventions

- Skills: `skill/<slug>` — lowercase alphanumeric with hyphens, no slashes within the slug
- Hooks: `hook/<slug>` — same convention

## Lifecycle

New atoms start at `lifecycle: draft`. When the atom has been used in production and its
schema and semantics are stable, it graduates to `lifecycle: stable`. Deprecated atoms
retain their files and gain `lifecycle: deprecated` with a deprecation note in `description`.
