# Support-Monkey Prompt Pack

These prompts are portable reference scripts for running Support-Monkey through
VS Code Copilot Chat, Claude Enterprise, or another approved workplace AI
assistant.

## Use Order

1. `support-monkey-orchestrator.md`
2. `support-monkey-evidence-reviewer.md`
3. `support-monkey-incident-council.md`
4. `support-monkey-bug-avengers.md`
5. `support-monkey-problem-records.md`
6. `support-monkey-rca-writer.md`
7. `support-monkey-jira-drafter.md`
8. `support-monkey-redaction-reviewer.md`

## Operating Boundary

- Default to local files, pasted excerpts, and user-provided command output.
- Do not write to ServiceNow, Jira, Slack, Teams, email, cloud resources, or
  repositories unless explicitly instructed.
- Do not claim root cause without direct evidence.
- Use `docs/evidence-standards.md` for evidence type, strength, confidence,
  timeline, impact, and validation-pattern rules.
- Treat all incident evidence as sensitive.
- Every material claim must cite evidence or be labelled as a hypothesis,
  assumption, or open question.
- Repeating incidents without a confirmed permanent fix should be evaluated as
  known issues and possible Problem Record candidates.

## VS Code Workflow

Use VS Code as the control center:

- Keep one case folder per incident under `cases/`.
- Start a new case with `support-monkey new-incident <IncidentNumber>`.
- Use `support-monkey next cases/<IncidentNumber>` to get one bounded action
  for the junior engineer.
- Treat `worknotes.md` as the ServiceNow-copyable investigation log.
- Review generated Markdown drafts before copying them into workplace systems.
- Use integrated terminal commands for local analysis.
- Paste only the minimum evidence needed for the current investigation.

Use the Bug Avengers prompt when a defect, vulnerability, incident pattern, or
proposed fix needs specialist review from multiple perspectives. Use the Problem
Records prompt when incidents repeat, workarounds persist, or there is a known
issue that needs durable ownership and prevention work.
