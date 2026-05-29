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
```
