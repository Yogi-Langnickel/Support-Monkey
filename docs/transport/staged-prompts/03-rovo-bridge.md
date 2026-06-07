# Stage 03: Rovo Bridge

Paste this when Confluence/Rovo research is needed.

```text
Use the manual Rovo bridge.

When Confluence knowledge is needed, generate focused Rovo questions in this
format. I will paste them into Rovo and paste answers back here.

```text
You are helping with an internal support incident. Do not invent facts. Cite
Confluence/Jira page titles and links. If information is missing or stale, say
so.

Incident: <incident number>
Priority: <priority or unknown>
Symptom: <short symptom>
Affected systems: <systems or unknown>
Known evidence: <evidence summaries or none>

Task: <specific ownership/runbook/known-error/monitoring/dependency/workaround/
validation question>
```

Ask Rovo about ownership, service catalog entries, runbooks, known errors,
Problem Records, dashboards, CloudWatch/NewRelic identifiers, dependencies,
vendor escalation paths, workarounds, and validation guidance.

After I paste Rovo answers back:
- extract only cited useful findings,
- record them in `Incident/evidence-ledger.json`,
- update `worknotes/worknotes.md`, `Incident/timeline.md`,
  `Incident/impact.md`, `Incident/hypotheses.md`, and
  `Incident/resolution-gate.md` as needed,
- mark uncited Rovo statements as soft evidence or open questions.
```
