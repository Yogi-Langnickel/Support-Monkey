# Windows And WSL Setup

Use this guide for running Support-Monkey on a Windows work computer with WSL
and VS Code.

## Recommended Shape

- Run Support-Monkey inside WSL.
- Use VS Code with the Remote - WSL extension as the control center.
- Keep the repository inside the WSL filesystem, for example under
  `~/work/Support-Monkey`.
- Keep workplace evidence out of git.
- Review generated Markdown drafts in VS Code before manually copying approved
  text into ServiceNow, Jira, or other workplace systems.

Avoid keeping the active repository under `/mnt/c/...` unless there is a strong
reason. WSL-local files are usually faster for Python, search, and large log
handling.

## Prerequisites

Install or confirm:

- WSL 2 with Ubuntu or another approved Linux distribution.
- VS Code on Windows.
- VS Code Remote - WSL extension.
- Python 3.11 or newer inside WSL.
- Git inside WSL.

Check versions from the WSL terminal:

```sh
python3 --version
git --version
```

## First Setup

Clone the repository inside WSL:

```sh
mkdir -p ~/work
cd ~/work
git clone <support-monkey-repo-url> Support-Monkey
cd Support-Monkey
```

Create a local virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

Open the folder in VS Code:

```sh
code .
```

VS Code should show that it is connected to WSL. Use the integrated terminal in
VS Code for all Support-Monkey commands.

## Local Demo Commands

Run the current offline helpers:

```sh
support-monkey new-incident INC0012345
support-monkey import-incident examples/monday-test-incident.json --overwrite
support-monkey status cases/INC-MONDAY-001
support-monkey next cases/INC0012345
support-monkey capture-learning cases/INC0012345
support-monkey triage examples/incident.sample.json
support-monkey questions examples/incident.sample.json
support-monkey resolution-gate examples/incident.sample.json
```

If the console script is not installed yet, run with `PYTHONPATH`:

```sh
PYTHONPATH=src python3 -m support_monkey.cli new-incident INC0012345
PYTHONPATH=src python3 -m support_monkey.cli import-incident examples/monday-test-incident.json --overwrite
PYTHONPATH=src python3 -m support_monkey.cli status cases/INC-MONDAY-001
PYTHONPATH=src python3 -m support_monkey.cli next cases/INC0012345
PYTHONPATH=src python3 -m support_monkey.cli capture-learning cases/INC0012345
PYTHONPATH=src python3 -m support_monkey.cli triage examples/incident.sample.json
PYTHONPATH=src python3 -m support_monkey.cli questions examples/incident.sample.json
PYTHONPATH=src python3 -m support_monkey.cli resolution-gate examples/incident.sample.json
```

## Case Storage

Use local, gitignored folders for real work data:

```text
cases/
raw-evidence/
exports/
outputs/private/
```

These folders are intentionally ignored by git. Do not commit workplace ticket
exports, logs, screenshots, customer information, credentials, or generated
drafts that contain sensitive data.

## VS Code As Control Center

Recommended workflow:

1. Keep one case folder per incident under `cases/`.
2. Start new incidents with `support-monkey new-incident <IncidentNumber>`.
3. Use `support-monkey next cases/<IncidentNumber>` for the next small action.
4. Store pasted ticket text, log snippets, and command output as local evidence
   files.
5. Run Support-Monkey commands from the VS Code integrated terminal.
6. Review Markdown drafts in VS Code preview.
7. Capture pending learnings with `support-monkey capture-learning
   cases/<IncidentNumber>` only after reviewing the case.
8. Manually copy approved text into ServiceNow, Jira, or Slack.

Support-Monkey remains draft-only by default. It should not write to workplace
systems without explicit human approval and a later approved integration.

## Path Notes

Prefer WSL paths:

```text
/home/<user>/work/Support-Monkey/cases/INC0012345/
```

Avoid hardcoding Windows paths in config. If you must reference a Windows file,
copy the needed excerpt into the case folder or use WSL's `/mnt/c/...` path only
for temporary imports.

## Safety Baseline

- Do not put real secrets in `.env`.
- Do not paste full environment files into prompts.
- Do not upload workplace data to unapproved AI services.
- Do not use the home machine for workplace evidence.
- Delete or export case folders according to workplace retention rules.
- Keep customer-facing drafts marked as `DRAFT - HUMAN REVIEW REQUIRED` until a
  human approves them.

## Troubleshooting

If `support-monkey` is not found, activate the virtual environment:

```sh
source .venv/bin/activate
```

If imports fail when running modules directly, set `PYTHONPATH`:

```sh
PYTHONPATH=src python3 -m support_monkey.cli --help
```

If Python packages cannot be installed on the work computer, use the current
stdlib-only helpers and avoid optional dependencies until workplace policy is
clear.
