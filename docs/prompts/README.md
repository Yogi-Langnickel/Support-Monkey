# Support-Monkey Prompt Pack

These prompts are portable reference scripts for running Support-Monkey through
VS Code Copilot Chat, Claude Enterprise, or another approved workplace AI
assistant.

## Use Order

1. `support-monkey-orchestrator.md`
2. `support-monkey-evidence-reviewer.md`
3. `support-monkey-incident-council.md`
4. `support-monkey-rca-writer.md`
5. `support-monkey-jira-drafter.md`
6. `support-monkey-redaction-reviewer.md`

## Operating Boundary

- Default to local files, pasted excerpts, and user-provided command output.
- Do not write to ServiceNow, Jira, Slack, Teams, email, cloud resources, or
  repositories unless explicitly instructed.
- Do not claim root cause without direct evidence.
- Treat all incident evidence as sensitive.
- Every material claim must cite evidence or be labelled as a hypothesis,
  assumption, or open question.

## VS Code Workflow

Use VS Code as the control center:

- Keep one case folder per incident under `cases/`.
- Review generated Markdown drafts before copying them into workplace systems.
- Use integrated terminal commands for local analysis.
- Paste only the minimum evidence needed for the current investigation.
