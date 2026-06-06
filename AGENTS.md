# Support-Monkey Agent Instructions

Read this file before inspecting or changing the project.

Support-Monkey is a local-first incident intelligence and administration
copilot for Digital Application Support. Its primary user is a junior support
engineer who needs messy incident input turned into structured facts, evidence,
hypotheses, open questions, and one bounded next action.

## Source Of Truth

Read these files first for project work:

- `README.md`
- `docs/agent-memory.md`
- `docs/evidence-standards.md`
- `docs/orchestrator-behaviour.md`
- `docs/transport/staged-prompts/README.md`
- `docs/transport/staged-prompts/08-junior-chaos-control.md`

Use `docs/prompts/` for the portable assistant prompt pack. Use
`docs/transport/bootstrap-prompt.md` and
`docs/transport/prompt-only-activation.md` only when the project must be carried
to a locked-down workplace environment.

## Working Rules

- Work on scoped branches. Completed deliverables target `develop`; `master` is
  release/promotion only and needs explicit user approval.
- Before substantial or high-risk work is merged into `develop`, run two
  persona review iterations with relevant reviewers, address required feedback,
  and classify any remaining feedback with rationale.
- Keep MVP behavior read-only and local-first.
- Do not write to ServiceNow, Jira, Slack, Teams, email, cloud systems, or
  customer-facing channels without explicit instruction.
- Never commit credentials, workplace data, customer data, incident exports, log
  payloads, screenshots, tokens, or `.env` files.
- Every conclusion must cite evidence. Do not claim root cause, impact,
  workaround, fix validation, or vendor fault without evidence.
- Keep support outputs copyable and human-reviewed. Generated worknotes, Jira
  drafts, RCA drafts, vendor escalations, and Problem Record candidates are
  drafts until a senior support engineer approves them.
- Treat `.support-monkey/learnings/pending/` as a review inbox only. Do not
  auto-promote early incident notes into durable memory.
- Use `rg` and `rg --files` for search.

## Validation

Use focused validation:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test*.py'
```

For prompt-only or documentation-only changes, read the changed Markdown and run
any available repo lint/check command before closeout.
