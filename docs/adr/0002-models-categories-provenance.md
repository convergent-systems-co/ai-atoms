# 0002. Add the model class, a shared category vocabulary, and structured provenance

- Status: proposed
- Date: 2026-09-03
- Builds on: `0001-prompt-agent-persona-classes.md`

## Context

Three requests arrived together: include the skills published on claudeskills.in with credit to
where they came from; add categories so the catalog can be browsed by subject rather than only by
class; and add a `model` class, starting with the Ollama library. Each exposed a gap:

- The catalog had two attribution fields (`authored_by`, `source_url`) and no place for a
  license. claudeskills.in aggregates 409 SKILL.md files from community GitHub lists, states no
  license for the aggregate, and records no per-skill author; 29 of the files name an author in
  their frontmatter and 13 name a license. Importing them without a structured, honest record of
  that would launder unknown terms into a CC-BY-4.0 catalog.
- `category` existed only on `skill`, with a 14-value enum shaped by one importer.
- The umbrella taxonomy ADR folds model-atoms into ai-atoms as a `model` type; model-atoms.com is
  still live with 77 Cloudflare Workers AI cards, and Ollama publishes no JSON index of its
  library.

## Decision

1. **`schemas/common-v1.json`** defines `category` and `provenance` once; every class schema
   references them by `$ref`. The build resolves `$ref` through a local registry so validation
   works offline.
2. **`provenance`** is `{source, source_url, author, license, imported_at, notes}`. `license` is
   an SPDX id, the source's own name for it, or the literal `unknown`. `unknown` is displayed as
   such on every page and called out in `/ai/instructions.md`. The older `authored_by` and
   `source_url` fields stay, because the `ai` CLI and 244 existing atoms use them.
3. **Categories** are one 22-value vocabulary across all classes. The site gets `/categories/`
   and `/categories/<slug>.json`; the catalog manifest gets a `categories` index. The importers
   map their source's categories onto it; a backfill script assigns one to every atom already in
   the tree and reports what it could only call `other`.
4. **claudeskills.in import** reads the public Supabase table the site's front end reads,
   through the site's own publishable key taken from its bundle at run time. `license` comes from
   the SKILL.md frontmatter, else from the aggregator's `source` field when it names one
   (`vibeship-spawner-skills (Apache 2.0)`), else `unknown`. The operator's local file `path`
   column is not imported. Existing slugs are never overwritten. Imported atoms are
   `lifecycle: draft`.
5. **`model-v1`** models one AI model with a `providers[]` list rather than one atom per
   provider, so the same model can list Ollama, Cloudflare Workers AI, and a vendor API. Ids allow
   dots because model names carry versions. The first import reads the Ollama library page;
   vendor, family, and task are inferred from the name by a table and labelled as inferred, with
   `unknown` when the table has no entry.
6. **Site theme.** The brand shell reads `--color-role-*` variables that brand-atoms' tokens
   file never defines, so the shell always fell back to dark while pages hard-coded light cards.
   `web/src/styles/ai-atoms.css` defines the role variables and the page tokens for both themes
   from the brand's own swatches, honouring `prefers-color-scheme` and `data-theme` stamps. Each
   class gets one hue for its chip; nothing else is coloured by class.

## Consequences

- 397 skills of mostly unknown license are now in the catalog as drafts. The catalog's data
  license does not cover them; the provenance block says so. Anyone redistributing commercially
  has to review them, and the steward may decide to remove them.
- 179 of those skills are categorised `other` because the aggregator's category was `other`;
  a later pass can classify them from content.
- 12 Ollama models have vendor `unknown` because the name table has no entry; the table is in
  the importer and grows by pull request.
- model-atoms.com's 77 Cloudflare cards are not yet folded in. The provider list makes that a
  merge onto existing atoms where names match and new atoms otherwise.
- `hook.category` and `prompt.category` were assigned by keyword; they are reviewable, not
  authoritative.

## Alternatives considered

- **Reuse `authored_by` + `source_url` and add only `license`.** Rejected: three loose fields
  cannot say "aggregated by X from Y under terms Z", which is exactly the claudeskills case.
- **One atom per (model, provider).** Rejected: the same weights would appear under several ids
  and a runtime choosing a provider would have to search by name.
- **Skip the claudeskills import until licenses are known.** Raised as a concern; the principal
  asked for the import with attribution. Draft lifecycle plus explicit `unknown` is the
  compromise.
- **Per-class category enums.** Rejected: the point of categories is browsing across classes.
