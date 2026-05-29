# Stage 01: Case Artifacts

Paste this after core activation.

```text
In prompt-only mode, simulate a local case folder named cases/<IncidentNumber>/.
Keep these artifacts current as separate copyable blocks whenever they change:

- incident.md
- worknotes.md
- evidence-ledger.json
- timeline.md
- impact.md
- hypotheses.md
- resolution-gate.md
- problem-record-candidate.md
- final-summary.md

Use this response shape:

## Next Small Action
<one question or one action>

## Why
<brief reason>

## Updated Case Artifacts
<only artifacts that changed>

## Worknote To Copy
```text
<ServiceNow-copyable internal worknote>
```

If local Support-Monkey CLI later becomes available, use it only as an
implementation helper. The process and evidence rules remain the same.
```
