# Monday Junior Test

Use this script for the first Support-Monkey trial before giving it to a larger
junior group. Keep the test local and draft-only.

## Tester Goal

Confirm that a junior can:

- create a local case folder,
- understand the next small action,
- copy a factual worknote,
- add or identify first evidence,
- avoid premature root-cause language,
- understand when escalation or more evidence is needed.

## Setup Check

Run from the Support-Monkey repo:

```sh
PYTHONPATH=src python3 -m support_monkey.cli --help
PYTHONPATH=src python3 -m support_monkey.cli new-incident INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli next cases/INC-MONDAY-001
```

Expected result:

- `cases/INC-MONDAY-001/` exists.
- `worknotes.md` has copy-ready worknote text.
- `next` asks for the ServiceNow short description first.

## Mock ServiceNow Input

Use `examples/monday-test-incident.json` as the sanitized mock ticket.

Import the mock into a case:

```sh
PYTHONPATH=src python3 -m support_monkey.cli import-incident examples/monday-test-incident.json --overwrite
PYTHONPATH=src python3 -m support_monkey.cli status cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli next cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli resolution-gate cases/INC-MONDAY-001/incident.json
```

Expected result:

- The resolution gate should still block RCA/closure.
- The next action should ask for hard technical evidence, impact, owner, or
  validation depending on what the tester filled in.
- `status` should show file health, evidence count, evidence quality, missing
  evidence classes, and the recommended next action.

## Junior Observation Checklist

During the test, watch for:

- Did the junior know which file to edit?
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
- The junior can update `worknotes.md`.
- The junior understands that ServiceNow ticket text is soft evidence.
- The junior does not claim root cause from the mock ticket alone.
- The junior knows what hard evidence to collect next.

## Stop Criteria

Pause the rollout if:

- juniors copy unsupported RCA text,
- worknotes are too vague for ServiceNow,
- `next` repeatedly asks for the wrong thing,
- command templates encourage unsafe production actions,
- testers cannot tell where evidence should be stored.
