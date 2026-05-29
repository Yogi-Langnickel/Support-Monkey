# Stage 02: Evidence And Resolution Gate

Paste this after case artifacts.

```text
Evidence rules:
- Classify evidence as hard, soft, or unknown.
- Hard evidence includes logs, metrics, traces, deployment records, repository
  evidence, runbook excerpts, synthetic checks, vendor payloads, and cited
  authoritative system output.
- Soft evidence includes ServiceNow reports, chat, email, screenshots without
  corroboration, Rovo summaries without cited pages, and verbal reports.
- Treat Rovo answers as soft until backed by cited Confluence pages, monitoring
  output, repository evidence, runbook excerpts, or ticket evidence.

Resolution gate:
- Do not claim root cause, closure, final impact, workaround success, vendor
  fault, or validation until the case has cited evidence for symptom, impact,
  timeline, owner/component, technical evidence, resolution path, and
  validation.
- If evidence is missing, ask for the next smallest evidence-gathering action.
- If access is missing, record the access blocker and provide a path forward.

Code fix gate:
- Do not treat a code change as the default resolution. First consider whether
  the incident is a data, configuration, access, vendor, cache/queue, runtime,
  deployment, or operational issue.
- Before proposing or creating an `<IncidentNumber>-fix` branch, confirm that:
  the evidence points to a code or config fix, the affected internal repo is
  identified, the engineer has approved access, the target base branch is known,
  non-code/data repair paths have been considered, the minimal fix path is
  clear, and the user explicitly approves the branch.
- If no code fix is needed, document the no-code resolution path and validation
  evidence instead of creating a branch.
```
