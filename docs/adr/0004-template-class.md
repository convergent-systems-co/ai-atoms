# 0004. Add a template class for rendered documents

- Status: proposed
- Date: 2026-09-03
- Builds on: 0001, 0002, 0003

## Context

An agent told to write an ADR, runbook, HANDOFF.md, plan, or postmortem had nothing in the
catalog to fill. Two prompt atoms (`handoff-md`, `plan-with-alternatives`) described those
shapes in prose, and the constitution mandates several such documents with fixed section sets.
The principal asked whether a "templates" class should also hold blank persona and agent files.

## Decision

1. **`template-v1`** is a ninth class. Its runtime action — render a document by filling
   placeholders — is distinct from a prompt's (inject text into context), which is the taxonomy's
   test for a class. It carries `body`, `placeholders`, `rules`, `example`, and `produced_by`.
2. **Blank atom files are not templates.** Authoring aids live in `schemas/examples/<class>.json`,
   validated in CI and linked from the builder. Catalog atoms that were only templates were
   removed in the first curation pass for polluting the catalog; this keeps them out.
3. **The first eight templates are the constitution's required documents.** Their section sets
   come from the constitution's rules, not from invention; the postmortem is the common blameless
   form, with its 48-hour rule from the incident-commander persona.
4. **The two prose prompts migrate.** Nothing referenced them.

## Consequences

- Nine classes; the home page grid and the top navigation carry one more entry.
- A template's placeholders and body are checked to agree at build time.
- `skill/checkpoint`, `skill/commit`, `skill/pr`, `skill/runbook`, `skill/incident-response`,
  `skill/architecture`, `skill/write-spec`, `skill/documentation` gain a typed link to the
  document they produce.

## Alternatives considered

- **A `template` subtype of prompt.** Rejected: injecting a skeleton into context is not the same
  as rendering it, and a prompt has no place for placeholders or a rendered example.
- **Put templates in the separate doc-atoms catalog.** Rejected: they are consumed by AI
  runtimes, which is this catalog's scope; doc-atoms is not populated.
- **Store persona and agent templates as atoms.** Rejected for the reason in decision 2.
