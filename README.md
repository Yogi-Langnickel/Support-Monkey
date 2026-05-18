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
python3 -m support_monkey.cli questions examples/incident.sample.json
python3 -m support_monkey.cli resolution-gate examples/incident.sample.json
```

The command reads a sanitized incident JSON file and emits a Markdown triage
pack to stdout.

## Orchestrator Behaviour

Support-Monkey should behave like a persistent incident orchestrator:

1. Ask for missing evidence until the problem is fully resolved or the exact
   external blocker is proven.
2. Prefer local evidence: ServiceNow exports, pasted log snippets, AWS CLI
   output, local repository paths, screenshots, vendor payloads, and timestamps.
3. Use available local repositories for investigation when API integrations are
   not practical or permitted.
4. Keep a clear evidence ledger and never claim root cause without citations.
5. Produce drafts and branches only after explicit instruction; write nothing
   externally by default.

The `questions` command is the first local helper for this behaviour. It
generates concrete follow-up questions from incomplete incident data.

The `resolution-gate` command is the conservative closure guard. It reports
which evidence classes are still missing before Support-Monkey may claim root
cause, impact, workaround, fix validation, vendor fault, or Jira-ready handoff.

API integrations are optional, not assumed. If ServiceNow, Confluence, AWS,
NewRelic, Jira, or repository APIs are blocked by policy or access, use local
exports, screenshots, pasted command output, and local repo checkouts as the
evidence source.
