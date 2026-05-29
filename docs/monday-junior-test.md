# Monday Junior Test

Use this script for the first Support-Monkey trial before giving it to a larger
junior group. Keep the test local and draft-only.

## Tester Goal

Confirm that a junior can:

- create a local case folder,
- understand the next small action,
- copy a factual worknote,
- provide answers and evidence context without editing case files,
- avoid premature root-cause language,
- understand when escalation or more evidence is needed.

## Setup Check

Run from the Support-Monkey repo:

```sh
PYTHONPATH=src python3 -m support_monkey.cli --help
PYTHONPATH=src python3 -m support_monkey.cli doctor
PYTHONPATH=src python3 -m support_monkey.cli new-incident INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli next cases/INC-MONDAY-001
```

Expected result:

- `cases/INC-MONDAY-001/` exists.
- `doctor` reports `Status: ready`.
- `worknotes.md` has copy-ready worknote text.
- `next` asks for the ServiceNow short description first.
- The junior did not edit any case file manually.

## Mock ServiceNow Input

Use `examples/monday-test-incident.json` as the sanitized mock ticket.

Import the mock into a case:

```sh
PYTHONPATH=src python3 -m support_monkey.cli import-incident examples/monday-test-incident.json --overwrite
PYTHONPATH=src python3 -m support_monkey.cli status cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli rovo-questions cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli next cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli resolution-gate cases/INC-MONDAY-001/incident.json
```

Expected result:

- The resolution gate should still block RCA/closure.
- The next action should ask for hard technical evidence, impact, owner, or
  validation depending on what the tester filled in.
- `status` should show file health, evidence count, evidence quality, missing
  evidence classes, and the recommended next action.
- `rovo-questions` should produce copy-ready Confluence/Rovo questions for
  runbooks, ownership, known errors, monitoring, dependencies, and validation.

## Assistant-Owned Case Updates

The junior should not edit `incident.json`, `evidence-ledger.json`, `worknotes.md`,
or any generated Markdown file. The assistant collects answers in the chat and
runs commands to update the case.

Example context update:

```sh
PYTHONPATH=src python3 -m support_monkey.cli update-case cases/INC-MONDAY-001 \
  --priority P2 \
  --opened-at 2026-06-01T09:10:00+10:00 \
  --short-description "Customer portal intermittently returns 502 during account lookup" \
  --description "Call-centre users report intermittent lookup failures. Some retries succeed." \
  --caller-notes "Two users reported 502 around 09:05-09:10." \
  --affected-system customer-portal \
  --affected-system account-bff \
  --impact-scope call_centre \
  --impact-depth partial_outage \
  --affected-users-estimate 2
```

Example evidence capture:

```sh
PYTHONPATH=src python3 -m support_monkey.cli add-evidence cases/INC-MONDAY-001 \
  --source CloudWatch \
  --type log \
  --strength hard \
  --confidence confirmed \
  --observed-at 2026-06-01T09:12:00+10:00 \
  --supports technical_evidence \
  --supports timeline \
  --summary "Customer profile API emitted 502 timeout errors during the incident window." \
  --artifact-kind log \
  --artifact-name customer-profile-api-502.txt \
  --timeline-event "CloudWatch query found customer profile API 502 timeout errors."
```

Expected result:

- Support-Monkey updates `incident.json`, `evidence-ledger.json`, `incident.md`,
  `timeline.md`, `impact.md`, `resolution-gate.md`, and `worknotes.md`.
- If an artifact name is provided, Support-Monkey prints the exact folder path
  where the junior should copy the screenshot, log export, or query result.
- The junior only copies external artifacts into the instructed folder. They do
  not edit case files.
- Support engineers should not be asked to contact customers directly. Use
  ServiceNow, call-centre notes, monitoring, Confluence/Rovo, Teams, and
  internal systems for evidence.

## Junior Observation Checklist

During the test, watch for:

- Did the junior avoid editing case files?
- Did `next` give a small enough action?
- Did the junior paste too much sensitive data?
- Did the junior understand hard versus soft evidence?
- Did the junior avoid root-cause claims?
- Did the worknote sound copy-ready for ServiceNow?
- Did the junior know when to ask for senior help?

## Debrief Questions

Ask the tester:

- What step was confusing?
- Which file did you expect to open first?
- Did the next action feel too broad or too narrow?
- What evidence did you think was enough for RCA?
- Would you copy the generated worknote into ServiceNow?
- What command/query template was missing?

## Learning Capture

After the test, capture a pending learning candidate:

```sh
PYTHONPATH=src python3 -m support_monkey.cli capture-learning cases/INC-MONDAY-001
```

Expected result:

- A file is created in `.support-monkey/learnings/pending/`.
- The file is marked `PENDING HUMAN REVIEW`.
- It must not be promoted to durable memory until a senior reviews evidence and
  redaction.

## Pass Criteria

For the Monday pilot, this is enough:

- The junior can create a case.
- The junior can run `next`.
- The assistant can update case files from the junior's answers.
- The junior understands that ServiceNow ticket text is soft evidence.
- The junior does not claim root cause from the mock ticket alone.
- The junior knows what hard evidence to collect next.

## Stop Criteria

Pause the rollout if:

- juniors copy unsupported RCA text,
- worknotes are too vague for ServiceNow,
- `next` repeatedly asks for the wrong thing,
- command templates encourage unsafe production actions,
- testers cannot tell where external evidence artifacts should be copied,
- the assistant asks juniors to manually edit generated case files.
