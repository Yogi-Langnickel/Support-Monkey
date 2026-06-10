# Support-Monkey Agent Memory

Last updated: 2026-06-10

## Current State

- Support-Monkey is a local-first, read-only incident intelligence copilot for
  Digital Application Support.
- Primary workflow is local case folders under `cases/<IncidentNumber>/`, with
  generated facts, worknote, evidence, resolution-gate, coordinator, handoff,
  and conclusion files.
- New case folders use top-level `Facts/`, `Worknotes/`, and `Conclusion/`
  directories under the incident-number folder. Do not recreate the older
  `Incident/`, `worknotes/`, or `outcomes/` roots.
- Case updates should go through `support-monkey update-case` and
  `support-monkey add-evidence`; juniors should not manually edit generated
  case files.

## Active Rules

- Do not write to ServiceNow, Jira, Slack, Teams, email, cloud systems, or
  customer-facing channels without explicit instruction.
- Every material conclusion must cite evidence or remain a hypothesis.
- Resolution readiness is based on explicit evidence ledger `supports` classes,
  not incident metadata or keyword inference.
- Timeline and impact support also require structured timeline/impact citations
  to existing evidence IDs.
- Hard evidence is determined from structured `strength` or evidence `type`,
  not from words in source, reference, or summary text.
- Evidence IDs are unique; duplicate IDs fail the resolution gate and
  `add-evidence` rejects duplicates before writing.
- Generated case writes are root-locked to the case folder, use a case-level
  lock for read/modify/write flows, reject symlink paths, and use atomic
  temp-file replacement for generated files.
- Learning-candidate filenames normalize the incident number before writing to
  `.support-monkey/learnings/pending/`.
- Treat `.support-monkey/learnings/pending/` as a review inbox only.

## Validation

- Run `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'` for
  implementation changes.
