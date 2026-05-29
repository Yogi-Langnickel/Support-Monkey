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

For the expected Windows workstation setup, use
`docs/setup/windows-wsl.md`. The recommended control center is VS Code with the
Remote - WSL extension, running Support-Monkey from the WSL filesystem.

Use `docs/prompts/` as the portable assistant prompt pack for VS Code Copilot,
Claude Enterprise, or another approved workplace AI assistant. These prompts
define the Support-Monkey orchestrator, incident council, evidence review, RCA
drafting, Jira drafting, and redaction-review workflows.

Use `docs/evidence-standards.md` for the formal evidence taxonomy, confidence
labels, timeline format, impact buckets, and validation patterns used by the
resolution gate.

## Local Offline Demo

```sh
python3 -m support_monkey.cli new-incident INC0012345
python3 -m support_monkey.cli next cases/INC0012345
python3 -m support_monkey.cli triage examples/incident.sample.json
python3 -m support_monkey.cli questions examples/incident.sample.json
python3 -m support_monkey.cli resolution-gate examples/incident.sample.json
```

`new-incident` creates a guarded local case folder under `cases/<incident>/`
with ServiceNow-copyable worknotes, evidence ledger, timeline, impact,
hypothesis, RCA, branch-plan, command, Problem Record, and final-summary files.
`next` reads the case and gives the junior engineer one small investigation
action with guardrails and a copy-ready worknote stub.

The older `triage`, `questions`, and `resolution-gate` commands read a
sanitized incident JSON file and emit Markdown to stdout.

## Local Validation

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'
```

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
It also reports a data quality score so soft-only investigations are flagged as
high risk even when all required fields appear to be filled.

The `new-incident` and `next` commands are the first junior-support workflow.
They intentionally keep the process manual and local: the junior pastes
ServiceNow details, log outputs, query results, screenshots, and local repo
findings into the case folder. API integrations should come after this workflow
is reliable under incident pressure.

API integrations are optional, not assumed. If ServiceNow, Confluence, AWS,
NewRelic, Jira, or repository APIs are blocked by policy or access, use local
exports, screenshots, pasted command output, and local repo checkouts as the
evidence source.
