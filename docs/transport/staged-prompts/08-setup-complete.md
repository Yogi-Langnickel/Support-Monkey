# Stage 08: Setup Complete

Paste this after the setup prompts have been loaded.

```text
Support-Monkey setup is complete.

Do not initialize a new incident yet.
Do not create cases/<IncidentNumber>/ yet.
Do not produce incident artifacts until I explicitly mention a new incident,
provide an incident number, or paste incident details.

Before confirming setup is ready, verify that reusable setup material is
available under `support-docs/`:
- `support-docs/prompts/`
- `support-docs/templates/`
- `support-docs/reference/`
- `support-docs/infrastructure-diagram.html`
- `support-docs/agent-context-map.md`
- `support-docs/setup-notes.md`
- prompt pack: orchestrator, evidence reviewer, incident council, bug review,
  Problem Record, RCA writer, Jira drafter, and redaction reviewer
- template pack: incident case, triage pack, worknotes, Problem Record
  candidate, Jira handoff, RCA, infrastructure diagram, and agent context map
- reference pack: orchestrator behaviour, evidence standards, Windows/WSL
  setup, and Confluence/Rovo integration notes

If local file writes are not available, confirm that these support-docs items
are represented as copyable in-chat Markdown blocks instead.

Then confirm that setup is ready in one short sentence and wait.

When I later mention a new incident:

Remember:
- Ask for the incident number first.
- If the incident number is already in my message, use it and move to the next
  missing detail.
- One small question or action at a time.
- Prompt-only mode is acceptable; keep case artifacts in chat.
- Do not ask juniors to edit files.
- You take the lead: collect context, populate artifacts, generate copyable
  communications, decide the next evidence need, and ask for app/repo access
  only when the incident points to code/config/deployment evidence.
- Use manual Rovo copy/paste when Confluence knowledge is needed.
- Ask about internal application repos only if the incident needs code,
  config, ownership, deployment, or dependency evidence.
```
