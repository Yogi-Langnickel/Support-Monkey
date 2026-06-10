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
If enterprise controls block cloning, package install, or local script
execution, use `docs/transport/prompt-only-activation.md`; Support-Monkey then
runs as a prompt-activated assistant that maintains copyable case artifacts in
chat.
If the assistant struggles with one large prompt, use the staged prompts in
`docs/transport/staged-prompts/`. The cloning limitation is for the personal
public Support-Monkey repo; approved internal application repositories can still
be used as evidence sources when the support engineer has access.
The staged prompt path also defines the full incident lifecycle: AI-led intake,
case artifact maintenance, copyable communications, internal repo/Rovo evidence
collection, closure/archive, and human-reviewed learning/memory candidates.
It also sets up or simulates `support-docs/` as the reusable workplace support
pack for prompts, templates, and reference docs, separate from incident cases.
`support-docs/infrastructure-diagram.html` is the interactive human view of
applications, repos, owners, dependencies, and information flow.
`support-docs/agent-context-map.md` is the compact assistant routing map used
before deciding which repo or application needs investigation.
Use `docs/transport/staged-prompts/07-junior-chaos-control.md` when the main
goal is to turn messy junior input into structured facts, claims, evidence,
hypotheses, open questions, and one bounded next action.

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

Use `docs/integrations/confluence-rovo.md` for the staged Confluence/Rovo path:
generated Rovo questions first, Confluence REST/API-token search later, and
Forge/Rovo/MCP integration only after the manual pilot proves useful.

## Local Offline Demo

```sh
python3 -m support_monkey.cli doctor
python3 -m support_monkey.cli new-incident INC0012345
python3 -m support_monkey.cli import-incident examples/monday-test-incident.json --overwrite
python3 -m support_monkey.cli status cases/INC-MONDAY-001
python3 -m support_monkey.cli rovo-questions cases/INC-MONDAY-001
python3 -m support_monkey.cli update-case cases/INC-MONDAY-001 --priority P2 --affected-system customer-portal
python3 -m support_monkey.cli add-evidence cases/INC-MONDAY-001 --source ServiceNow --type ticket --strength soft --summary "Ticket reports intermittent 502 errors." --supports symptom
python3 -m support_monkey.cli next cases/INC0012345
python3 -m support_monkey.cli capture-learning cases/INC0012345
python3 -m support_monkey.cli triage examples/incident.sample.json
python3 -m support_monkey.cli questions examples/incident.sample.json
python3 -m support_monkey.cli resolution-gate examples/incident.sample.json
```

`doctor` checks the local runtime, required Monday files, the mock incident JSON,
and case-directory writability before a junior starts the pilot.
`new-incident` creates a guarded local case folder under `cases/<incident>/`
with ServiceNow-copyable worknotes, evidence ledger, timeline, impact,
hypothesis, RCA, branch-plan, command, Problem Record, and final-summary files.
`import-incident` creates or updates a case from a JSON ticket/export, which is
the quickest path for Monday mock testing. `status` shows file health, evidence
quality, missing evidence classes, and the recommended next step.
`next` reads the case and gives the junior engineer one small investigation
action with guardrails and a copy-ready worknote stub.
`update-case` and `add-evidence` are assistant-facing commands: the assistant
collects answers from the junior, updates the case files, refreshes derived
Markdown, and prints exact artifact-copy instructions when screenshots or log
exports need to be placed in the incident folder.
`rovo-questions` generates copy-ready questions for Rovo/Confluence research so
the assistant can look for ownership, runbooks, known errors, monitoring,
dependencies, workarounds, and validation guidance without asking juniors to
manually search across Confluence.

`capture-learning` writes a pending learning candidate under
`.support-monkey/learnings/pending/`. Treat it as an inbox only: a senior must
review evidence, remove sensitive details, and approve promotion before it
becomes durable memory.

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
4. Assume support engineers usually do not have direct customer access; use
   ServiceNow, call-centre notes, monitoring, logs, Confluence/Rovo, Teams, and
   internal systems as evidence sources.
5. Keep a clear evidence ledger and never claim root cause without citations.
6. Produce drafts and branches only after explicit instruction; write nothing
   externally by default.

The `questions` command is the first local helper for this behaviour. It
generates concrete follow-up questions from incomplete incident data.

The `resolution-gate` command is the conservative closure guard. It reports
which evidence classes are still missing before Support-Monkey may claim root
cause, impact, workaround, fix validation, vendor fault, or Jira-ready handoff.
It also reports a data quality score so soft-only investigations are flagged as
high risk even when all required fields appear to be filled.

The `new-incident` and `next` commands are the first junior-support workflow.
They intentionally keep the process local, but not file-editing based: the
assistant asks for ServiceNow details, log outputs, query results, screenshots,
and local repo findings, then runs `update-case` and `add-evidence` so generated
case files stay consistent. Juniors may still need to copy screenshots or log
exports into the exact evidence folder named by Support-Monkey. API integrations
should come after this workflow is reliable under incident pressure.

`capture-learning` is the first learning loop. It creates a reviewed-learning
candidate from a case folder without auto-updating memory, because early
incident notes can contain wrong assumptions or sensitive data.

API integrations are optional, not assumed. If ServiceNow, Confluence, AWS,
NewRelic, Jira, or repository APIs are blocked by policy or access, use local
exports, screenshots, pasted command output, and local repo checkouts as the
evidence source.
