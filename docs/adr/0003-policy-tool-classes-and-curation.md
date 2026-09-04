# 0003. Type policy and tool; record the curation decisions

- Status: proposed
- Date: 2026-09-03
- Builds on: 0001, 0002; executes §5 of `docs/reviews/2026-09-03-atom-evaluation.md`

## Context

After v0.3.0 the catalog had eight typed classes' worth of content but six schemas: agents
referenced `policy/` and `tool/` ids that resolved only to files in untyped directories. The
evaluation report also left seven decisions to the steward. Two were product calls and were put to
the principal; the rest were quality calls.

## Decisions

1. **`policy-v1`.** One class for everything that answers "what may this agent do?". `subtype`
   is `boundary`, `capability`, or `isolation`; `effect` is `forbid`, `require`, `permit`, or
   `bound`; `rule.text` is always present so a model or operator can read the rule, and the
   subtype's machine-checkable fields sit beside it (grants and elevation; process, network,
   filesystem; domains and refusals). The five retired source types map onto it without loss.
2. **`tool-v1`.** `spec` is the signature a model sees (`function_name`, `parameters`,
   `returns`) plus `side_effects`, the thing a runtime must gate. `gated_by` names the policies
   that permit it. `parameters` is optional because a tool can take none (`git-status`).
3. **Unknown-license claudeskills atoms stay, as drafts.** Principal's decision. Upstream discovery
   through the GitHub API resolved 17; the remaining 351 have no upstream recorded by the
   aggregator or an upstream with no license file. They keep `provenance.license: unknown`,
   `lifecycle: draft`, and the visible warning.
4. **The 111 knowledge-work skills stay.** Principal's decision. They are Apache-2.0 and work; the
   category filters carry the scope signal.
5. **Drops are deletions; duplicates are deprecations.** A broken or placeholder atom is removed.
   Where two atoms cover the same ground, the weaker one is kept with `lifecycle: deprecated` and a
   description pointing at the survivor, so an installed id keeps resolving.
6. **`hook.events` rather than an array-typed `event`.** The `ai` CLI reads `event` as a string;
   changing its type would break installs. `events` is additive and consumers that read only
   `event` still work.
7. **Empty agents fold into their personas.** Nine agents bound nothing but a persona and a
   planner preference; that is a persona with a hint, not an agent. They are removed; the personas
   stay and are the same identity.

## Consequences

- Every cross-atom reference in the catalog resolves to a typed atom. `atoms/workflow/` is the
  last untyped tree and nothing references it.
- 351 draft skills carry an unknown license. Commercial redistribution still needs review.
- `hook/secret-precommit` now declares `event: git-pre-commit`; a consumer that expected one of the
  Claude Code event names will not wire it as a PreToolUse hook, which is correct.
- The persona and skill deprecations keep ids stable at the cost of some catalog noise; the
  deprecated atoms are excluded from "of the day" by the existing candidate rules.

## Alternatives considered

- **Delete duplicates outright.** Rejected: ids may already be installed.
- **Make `hook.event` an array.** Rejected for the CLI compatibility reason above.
- **Keep policy and tool references as file-existence checks.** Rejected: an unvalidated atom is
  not a contract.
