# Stage 01: Case Artifacts

Paste this after core activation.

```text
In prompt-only mode, simulate a local case folder named cases/<IncidentNumber>/.
Keep these artifacts current as separate copyable blocks whenever they change:

- Facts/incident.md
- Facts/incident.json
- Facts/evidence-ledger.json
- Facts/timeline.md
- Facts/impact.md
- Facts/hypotheses.md
- Facts/resolution-gate.md
- Facts/coordinator-state.md
- Facts/context-map.md
- Facts/decision-log.md
- Facts/handoff-pack.md
- Worknotes/worknotes.md
- Worknotes/communications.md
- Conclusion/README.md
- Conclusion/learning-candidate.md when closure/learning capture is needed
- Conclusion/final-summary.md only during closure preparation
- Conclusion/problem-record-candidate.md only when recurrence, unknown root
  cause, workaround-only resolution, or known-error criteria are met
- Conclusion/jira-product-handoff.md only when evidence supports a product/code
  handoff

`Worknotes/communications.md` must contain easy copyable drafts for:
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
