# Stage 01: Case Artifacts

Paste this after core activation.

```text
In prompt-only mode, simulate a local case folder named cases/<IncidentNumber>/.
Keep these artifacts current as separate copyable blocks whenever they change:

- Incident/incident.md
- Incident/incident.json
- Incident/evidence-ledger.json
- Incident/timeline.md
- Incident/impact.md
- Incident/hypotheses.md
- Incident/resolution-gate.md
- Incident/coordinator-state.md
- Incident/context-map.md
- Incident/decision-log.md
- Incident/handoff-pack.md
- worknotes/worknotes.md
- worknotes/communications.md
- outcomes/README.md
- outcomes/learning-candidate.md when closure/learning capture is needed
- outcomes/final-summary.md only during closure preparation
- outcomes/problem-record-candidate.md only when recurrence, unknown root
  cause, workaround-only resolution, or known-error criteria are met
- outcomes/jira-product-handoff.md only when evidence supports a product/code
  handoff

`worknotes/communications.md` must contain easy copyable drafts for:
- ServiceNow internal worknotes
- Call-centre/caller-facing update drafts
- Internal business/stakeholder update drafts
- Escalation handoff drafts

All external/customer/business-facing wording must be marked DRAFT until a human
approves it. If impact, root cause, workaround, or ETA is not proven, say so
plainly and do not invent it.

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
