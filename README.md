# Support-Monkey

Local-first incident intelligence and administration copilot for Digital
Application Support.

## Goal

Support-Monkey helps a senior support engineer turn weak incident input into an
evidence-backed triage pack:

- what is broken
- who and what is impacted
- likely ownership and affected systems
- evidence gathered
- hypotheses and next investigation steps
- workaround and resolution options
- draft RCA, impact analysis, Jira ticket, vendor escalation, and work notes

## Current Boundary

MVP is read-only and local-first.

- No customer-facing updates without explicit instruction.
- No ServiceNow/Jira/Slack/Teams/email writes without explicit instruction.
- No cloud changes without explicit instruction.
- No credentials committed or pasted into repo files.
- Every conclusion must cite evidence.

## Portable Bootstrap

Use `docs/transport/bootstrap-prompt.md` to carry this project to a work
machine through Slack/email. The receiving environment should create local
`.env` values from `.env.example` and keep real workplace data out of git.

## Local Offline Demo

```sh
python3 -m support_monkey.cli triage examples/incident.sample.json
```

The command reads a sanitized incident JSON file and emits a Markdown triage
pack to stdout.

