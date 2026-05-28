# Architecture — ai-atoms

## Overview

ai-atoms is a typed, versioned catalog of AI runtime primitives. It contains two atom classes,
each with its own JSON Schema, validated at build time.

## Two atom classes

### skill (`atoms/skill/`)
Skills are bounded, invocable units of AI capability. A skill bundles a `system_prompt_fragment`
that can be injected into any AI agent's system context, along with a declared `invocation_contract`
(inputs, outputs, side effects). Skills are keyed by `skill/<slug>`.

### hook (`atoms/hook/`)
Hooks are event-driven runtime behaviors wired into AI tool infrastructure. A hook declares the
`event` it responds to (e.g. `PreToolUse`, `PostToolUse`, `SessionStart`), the `language` of its
implementation, a `trigger` (by tool name, file pattern, always, or tool category), and whether
it is `blocking`. Hooks are keyed by `hook/<slug>`.

## Schema locations

| Schema | Path | Validates |
|---|---|---|
| skill-v1.json | `schemas/skill-v1.json` | `atoms/skill/*.json` |
| hook-v1.json | `schemas/hook-v1.json` | `atoms/hook/*.json` |

## Build pipeline

```
atoms/skill/*.json  ──┐
                      ├─► scripts/build-exports.py ──► exports/catalog.json
atoms/hook/*.json   ──┘                                          │
                                                                 ▼
                                                  web/public/exports/catalog.json
                                                                 │
                                                                 ▼
                                                       Astro static build
                                                                 │
                                                                 ▼
                                                    Cloudflare Pages (ai-atoms.com)
```

1. `scripts/build-exports.py` walks `atoms/skill/` and `atoms/hook/`, validating each JSON file
   against the appropriate schema. Exits 1 on any validation failure.
2. It writes `exports/catalog.json` — the machine-readable catalog manifest.
3. The Astro web build (`web/`) copies `exports/catalog.json` to `web/public/exports/catalog.json`
   via the `prebuild` npm script, then builds a static site served at `https://ai-atoms.com`.
4. CI runs the build on every PR and push. Deployment to Cloudflare Pages runs on push to `main`.

## Compositions

Workflow compositions live in `workflows/`. They are collected by the build script without schema
validation (freeform JSON). Compositions reference atoms by ID.

## Infrastructure

Terraform in `infra/terraform/` provisions the Cloudflare Pages project and DNS records for
`ai-atoms.com`. State is stored in an R2-backed S3 backend.
