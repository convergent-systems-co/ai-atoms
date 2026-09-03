# 0001. Add prompt, agent, and persona as typed atom classes

- Status: proposed
- Date: 2026-09-03
- Relates to: convergent-systems-co/atoms `docs/adr/0001-unified-ai-atom-taxonomy.md` (proposed)

## Context

PR #46 moved 293 files from the retired persona-atoms, agent-atoms, prompt-atoms, skill-atoms,
and workflow-atoms catalogs into this repository verbatim. They kept their old schemas
(`persona-atoms.com/...`, `agent-atoms.com/...`), so `scripts/build-exports.py` skipped every
directory except `skill` and `hook`. 241 atoms and 52 compositions sat in the tree without
being validated, published, or addressable. The retired sites are offline, so these copies are
the only surviving ones.

The umbrella ADR proposes eight top-level types with `persona` folded into `agent` as a
sub-type. The principal asked for three classes — prompts, agents, personas — so persona is a
class here, not a sub-type.

## Decision

Three schemas, one directory each, one flat id space each (`prompt/<slug>`, `agent/<slug>`,
`persona/<slug>`):

1. **`prompt`** — text injected into the context window. `subtype` discriminates
   (`persona`, `constraint`, `format`, `output-schema`, `refusal`, `tool-use`, `composite`).
   The retired `format-instruction`, `refusal-pattern`, and `tool-use-template` names were
   shortened. prompt-atoms compositions became `composite` prompts whose `content` is the
   resolved concatenation of `includes`, so consumers never resolve references themselves.

2. **`persona`** — a portable identity that binds nothing. The retired `role-definition`,
   `voice-profile`, `tone-parameter`, `work-contract`, `behavioural-constraint`, and
   `knowledge-boundary` types become fields. Constraints and boundaries are **inlined as
   text**, not referenced, so a persona is self-contained. This keeps the umbrella ADR's
   argument ("nothing consumes a tone parameter on its own") while giving persona its own
   class.

3. **`agent`** — a persona bound to what it runs with (`prompts`, `skills`, `tools`,
   `policies`, `hooks`) plus `execution` preferences. `subtype` is `actor` or `reviewer`;
   reviewers require `review_criteria`. This is the umbrella ADR's `agent/actor` and
   `agent/reviewer`; its `agent/persona` is the `persona` class.

4. **Build-time reference resolution.** Every cross-atom reference must resolve or the build
   fails. References into classes that do not have a schema yet (`tool/`, `policy/`) resolve if
   a file with that slug exists under `atoms/<class>/`.

5. **Migration is a script, not a hand edit.** `scripts/migrate-retired-atoms.py` re-types the
   staged files and prints every unresolved reference it met. It never invents text for a
   missing part; gaps are reported.

## Consequences

- 59 prompts, 48 personas, and 12 agents are published. The staged copies they came from are
  removed from the tree; the originals remain in the retired repositories on GitHub and every
  atom carries a `source_url` pointing at its origin file.
- `atoms/policy/` (54), `atoms/tool/` (20), and `atoms/workflow/` (40) stay staged and untyped.
  Agents reference policies and tools by slug today; a later ADR types them.
- 16 references in the retired data pointed at atoms that never existed (for example
  `voice-profile/clear-instructional`, `behavioural-constraint/prefer-reversible-actions`,
  `role-definition/security-architect`). The affected personas ship without that part and are
  listed in `docs/reviews/2026-09-03-atom-evaluation.md`.
- Vendor-variant prompts (`sre-anthropic`, `sre-openai`, `sre-ollama`, ...) have byte-identical
  content. They are migrated as-is; collapsing them is a data decision left to the review.
- `ai mode` still resolves personas from `persona-atoms.com/<name>/latest`, which is offline.
  Pointing it at `ai-atoms.com/atoms/persona/<slug>.json` is a change to the `ai` CLI, outside
  this repository.
- The umbrella ADR's type list and this repository's class list now differ on `persona`. One
  of them needs amending; this ADR records the reason for the difference.

## Alternatives considered

- **Persona as `agent` sub-type (umbrella ADR).** Rejected by the principal's request. The
  practical cost is small: an agent references a persona by id either way.
- **Keep the subtype directory layout** (`atoms/prompt/constraint/…`). Rejected: the id is the
  address, the directory is not, and a flat layout removes a second place the subtype can
  disagree with the `subtype` field.
- **Reference constraints from personas instead of inlining.** Rejected: `policy/` has no
  schema yet, and a persona that needs resolution is not portable.
- **Delete the untyped `policy`, `tool`, and `workflow` directories.** Rejected: agents
  reference them, and they are the only copies. They are excluded from the published catalog
  instead.
