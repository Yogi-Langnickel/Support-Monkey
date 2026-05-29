from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .models import Incident
from .resolution import assess_evidence_quality, classify_resolution_state


INCIDENT_NUMBER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")


@dataclass(frozen=True)
class CaseCreationResult:
    case_dir: Path
    created_files: tuple[Path, ...]
    existing_files: tuple[Path, ...]


@dataclass(frozen=True)
class LearningCaptureResult:
    learning_path: Path
    incident_number: str


def create_incident_case(
    incident_number: str,
    *,
    cases_dir: Path = Path("cases"),
    now: datetime | None = None,
) -> CaseCreationResult:
    number = _normalize_incident_number(incident_number)
    timestamp = _iso_now(now)
    case_dir = cases_dir / number
    case_dir.mkdir(parents=True, exist_ok=True)
    for directory in (
        "evidence",
        "evidence/screenshots",
        "evidence/logs",
        "evidence/exports",
        "evidence/query-results",
        "commands",
    ):
        (case_dir / directory).mkdir(parents=True, exist_ok=True)

    files = _case_files(number, timestamp)
    created: list[Path] = []
    existing: list[Path] = []
    for relative_path, content in files.items():
        path = case_dir / relative_path
        if path.exists():
            existing.append(path)
            continue
        path.write_text(content, encoding="utf-8")
        created.append(path)

    return CaseCreationResult(
        case_dir=case_dir,
        created_files=tuple(created),
        existing_files=tuple(existing),
    )


def render_case_next_action(case_path: Path) -> str:
    case_dir = _resolve_case_dir(case_path)
    incident = _read_case_incident(case_dir)
    state, missing = classify_resolution_state(incident)
    quality = assess_evidence_quality(incident)
    action = _next_action(incident, missing)

    lines = [
        f"# Next Action: {incident.number}",
        "",
        f"Case folder: `{case_dir}`",
        f"Resolution gate: `{state}`",
        f"Evidence quality: `{quality.score}/100` (`{quality.risk}`)",
        "",
        "## Do This Next",
        action,
        "",
        "## Guardrails",
        "- Keep the action read-only unless a senior explicitly approves a write.",
        "- Paste only the minimum output needed; redact secrets, tokens, customer PII, and internal URLs when possible.",
        "- If the requested data is unavailable, write the exact blocker in `worknotes.md`.",
        "- Do not claim root cause yet unless the resolution gate says the case is ready for human review.",
        "",
        "## Copy-Ready Worknote Stub",
        "```text",
        _worknote_stub(action),
        "```",
    ]
    return "\n".join(lines).strip() + "\n"


def capture_learning_candidate(
    case_path: Path,
    *,
    learnings_dir: Path = Path(".support-monkey/learnings/pending"),
    now: datetime | None = None,
) -> LearningCaptureResult:
    case_dir = _resolve_case_dir(case_path)
    incident = _read_case_incident(case_dir)
    timestamp = _iso_now(now)
    learnings_dir.mkdir(parents=True, exist_ok=True)
    safe_timestamp = timestamp.replace(":", "").replace("-", "")
    path = learnings_dir / f"{incident.number}-{safe_timestamp}.md"
    path.write_text(_learning_candidate_markdown(incident, case_dir, timestamp), encoding="utf-8")
    return LearningCaptureResult(learning_path=path, incident_number=incident.number)


def _normalize_incident_number(value: str) -> str:
    number = value.strip()
    if not number:
        raise ValueError("incident number is required")
    if "/" in number or "\\" in number or number in {".", ".."}:
        raise ValueError("incident number must not contain path separators")
    if not INCIDENT_NUMBER_RE.match(number):
        raise ValueError("incident number may contain only letters, numbers, dot, dash, and underscore")
    return number


def _iso_now(now: datetime | None) -> str:
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    return current.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _case_files(incident_number: str, created_at: str) -> dict[str, str]:
    incident_payload = {
        "number": incident_number,
        "priority": "unknown",
        "openedAt": "",
        "shortDescription": "",
        "description": "",
        "callerNotes": "",
        "affectedSystems": [],
        "impact": {
            "scope": "unknown",
            "depth": "unknown",
            "affectedUsersEstimate": None,
            "evidenceIds": [],
        },
        "timeline": [],
        "evidence": [],
        "case": {
            "createdAt": created_at,
            "startedAt": created_at,
            "resolvedAt": "",
            "status": "intake",
        },
    }
    evidence_ledger = {
        "incidentNumber": incident_number,
        "items": [],
    }
    return {
        "incident.json": json.dumps(incident_payload, indent=2) + "\n",
        "evidence-ledger.json": json.dumps(evidence_ledger, indent=2) + "\n",
        "incident.md": _incident_markdown(incident_number, created_at),
        "worknotes.md": _worknotes_markdown(incident_number, created_at),
        "timeline.md": _timeline_markdown(),
        "impact.md": _impact_markdown(),
        "hypotheses.md": _hypotheses_markdown(),
        "rca.md": _rca_markdown(incident_number),
        "resolution-gate.md": _resolution_gate_markdown(),
        "problem-record-candidate.md": _problem_record_markdown(incident_number),
        "commands/README.md": _commands_markdown(),
        "commands/cloudwatch.md": _cloudwatch_commands_markdown(),
        "commands/aws.md": _aws_commands_markdown(),
        "commands/sql.md": _sql_commands_markdown(),
        "commands/newrelic.md": _newrelic_commands_markdown(),
        "final-summary.md": _final_summary_markdown(incident_number),
        "branches.md": _branches_markdown(incident_number),
    }


def _incident_markdown(incident_number: str, created_at: str) -> str:
    return f"""# Incident {incident_number}

Status: intake
Case created: {created_at}
Started: {created_at}
Resolved:
Duration:

## ServiceNow Details

- Incident number: {incident_number}
- Priority: unknown
- Opened:
- Short description:
- Description:
- Caller / reporter notes:

## Current Situation

- Reported symptom:
- Affected user journey:
- Affected systems:
- Known customer impact:
- Current workaround:

## Known / Unknown / Assumed

### Known

- Pending ServiceNow details.

### Unknown

- Exact failing component.
- Impact scope.
- Technical evidence.
- Resolution path.
- Validation evidence.

### Assumed

- None. Do not add assumptions without labeling them.

## Current Owner / Escalation

- Incident commander:
- Support owner:
- Product/platform owner:
- Vendor owner:
- Teams/bridge channel:
- Last stakeholder update:
"""


def _worknotes_markdown(incident_number: str, created_at: str) -> str:
    return f"""# Worknotes: {incident_number}

Use this file for ServiceNow-copyable internal worknotes. Keep entries factual,
timestamped, and evidence-based. Do not claim root cause until the resolution
gate is ready for human review.

```text
[{created_at}] Support-Monkey case created. Status: intake. Next action: collect ServiceNow short description, description, priority, opened time, affected CI/service, and current work notes.
```

## Worknote Entries

```text
[{created_at}] Started incident investigation.
Result: ServiceNow details are pending.
Outcome: No root cause, impact, workaround, or validation confirmed yet.
Next: Capture ticket details and first technical evidence.
```
"""


def _timeline_markdown() -> str:
    return """# Timeline

Use ISO 8601 timestamps and cite an evidence ID for every row.

| Timestamp | Event | Evidence ID |
| --- | --- | --- |
| pending | pending | pending |
"""


def _impact_markdown() -> str:
    return """# Impact Analysis

## Current Impact

- Scope: unknown
- Depth: unknown
- Affected users / tenants: unknown
- Business function affected: unknown
- Data/payment/security risk: unknown
- Evidence IDs: pending

## Questions To Close

- Who is affected?
- How many users, customers, tenants, orders, messages, or records are affected?
- Since when?
- Is there a workaround?
- Is the issue active now?
"""


def _hypotheses_markdown() -> str:
    return """# Hypotheses

| Hypothesis | Evidence For | Evidence Against | Next Check | Status |
| --- | --- | --- | --- | --- |
| pending | pending | pending | pending | open |
"""


def _rca_markdown(incident_number: str) -> str:
    return f"""# RCA Draft: {incident_number}

Status: NOT READY - evidence required.

## Root Cause Or Leading Hypothesis

Not established.

## Evidence Required Before RCA

- Symptom evidence.
- Impact evidence.
- Timeline evidence.
- Owner / component evidence.
- Technical evidence.
- Resolution path or workaround evidence.
- Validation evidence.
"""


def _resolution_gate_markdown() -> str:
    return """# Resolution Gate

Do not close the incident or publish RCA language until each item is satisfied
or a named blocker is documented.

- [ ] Symptom understood.
- [ ] Impact understood.
- [ ] Timeline built.
- [ ] Owner or suspected owner identified.
- [ ] Technical evidence collected.
- [ ] Resolution path or workaround documented.
- [ ] Validation completed.
- [ ] Stakeholders updated.
- [ ] Problem Record decision made.
"""


def _problem_record_markdown(incident_number: str) -> str:
    return f"""# Problem Record Candidate: {incident_number}

Status: DRAFT - not recommended until recurrence, workaround-only resolution,
unknown root cause, or permanent-fix ownership is established.

## Linked Incidents

- {incident_number}

## Known Symptoms

## Recurrence Evidence

## Current Workaround

## Root Cause Status

Unknown.

## Recommended Owner

Unknown.

## Closure Criteria
"""


def _commands_markdown() -> str:
    return """# Commands

All commands are drafts for human review. Prefer read-only commands. Label any
write, mutation, restart, purge, deployment, or database update as requiring
senior approval.

Command labels:

- `read-only`: safe investigation command.
- `requires approval`: may change state or expose sensitive data.
- `potentially destructive`: do not run without explicit senior approval.
"""


def _cloudwatch_commands_markdown() -> str:
    return """# CloudWatch Commands

Replace placeholders before running.

```sh
# read-only
aws logs start-query \\
  --profile <profile> \\
  --region <region> \\
  --log-group-name <log-group> \\
  --start-time <epoch-start> \\
  --end-time <epoch-end> \\
  --query-string 'fields @timestamp, @message | filter @message like /ERROR|Exception|timeout|5xx/ | sort @timestamp desc | limit 20'
```

Expected result:

- Confirms: matching errors in the incident time window.
- Disconfirms: no matching errors for the suspected service/time window.
"""


def _aws_commands_markdown() -> str:
    return """# AWS Commands

```sh
# read-only
aws sts get-caller-identity --profile <profile>

# read-only
aws sqs get-queue-attributes \\
  --profile <profile> \\
  --queue-url <queue-url> \\
  --attribute-names ApproximateNumberOfMessages ApproximateNumberOfMessagesNotVisible
```

Do not run delete, purge, update, restart, or deploy commands without explicit
senior approval.
"""


def _sql_commands_markdown() -> str:
    return """# SQL Queries

Default to read-only `SELECT` queries. Limit rows. Do not run updates, deletes,
inserts, DDL, or stored procedures without explicit senior approval.

```sql
-- read-only
SELECT *
FROM <table_name>
WHERE <timestamp_column> >= :incident_start
ORDER BY <timestamp_column> DESC
FETCH FIRST 20 ROWS ONLY;
```
"""


def _newrelic_commands_markdown() -> str:
    return """# NewRelic Queries

```sql
-- read-only NRQL draft
SELECT count(*)
FROM TransactionError
WHERE appName = '<app-name>'
SINCE '<incident-start>'
UNTIL '<incident-end>'
FACET error.class, error.message
LIMIT 20
```

Expected result:

- Confirms: error class/message spike during the incident window.
- Disconfirms: no matching error signal for this app/time window.
"""


def _final_summary_markdown(incident_number: str) -> str:
    return f"""# Final Summary: {incident_number}

Status: NOT READY.

## What Happened

Unknown.

## Root Cause

Not confirmed.

## Impact

Unknown.

## Resolution / Workaround

Not confirmed.

## Validation

Not completed.

## Follow-Up
"""


def _branches_markdown(incident_number: str) -> str:
    return f"""# Branch Plan: {incident_number}

Do not create branches until a likely repo and fix path are identified.

Target branch name:

```text
{incident_number}-fix
```

Before creating a branch:

- [ ] Confirm the affected repository.
- [ ] Check working tree is clean.
- [ ] Detect the repo default branch (`master`, `main`, or release branch).
- [ ] Ask before branching if the default branch is not known.
- [ ] Pull latest default branch.
- [ ] Create `{incident_number}-fix`.
- [ ] Document tests and rollback notes.
"""


def _resolve_case_dir(case_path: Path) -> Path:
    if case_path.is_dir():
        return case_path
    candidate = Path("cases") / str(case_path)
    if candidate.is_dir():
        return candidate
    raise FileNotFoundError(f"case folder not found: {case_path}")


def _read_case_incident(case_dir: Path) -> Incident:
    incident_path = case_dir / "incident.json"
    payload = json.loads(incident_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"incident JSON must be an object: {incident_path}")

    ledger_path = case_dir / "evidence-ledger.json"
    if ledger_path.exists():
        ledger_payload = json.loads(ledger_path.read_text(encoding="utf-8"))
        if isinstance(ledger_payload, dict) and isinstance(ledger_payload.get("items"), list):
            payload = dict(payload)
            payload["evidence"] = ledger_payload["items"]

    return Incident.from_dict(payload)


def _next_action(incident: Incident, missing: tuple[str, ...]) -> str:
    if not incident.short_description:
        return (
            "Ask the junior to paste the ServiceNow short description. "
            "Expected output: one sentence describing the failing user journey."
        )
    if not incident.description and not incident.caller_notes:
        return (
            "Ask the junior to paste the ServiceNow description, caller notes, and latest work notes. "
            "Expected output: reported symptom, exact error text, priority, opened time, and affected CI if present."
        )
    if not incident.opened_at:
        return (
            "Ask for the incident start/opened timestamp and timezone from ServiceNow. "
            "Expected output: ISO 8601 timestamp or the original ticket timestamp plus timezone."
        )
    if not incident.affected_systems:
        return (
            "Ask which application, service, API, batch job, queue, database, or user journey appears affected. "
            "Expected output: at least one affected system or 'unknown'."
        )
    if not incident.evidence:
        return (
            "Create the first evidence item from ServiceNow ticket text. "
            "Add it to `evidence-ledger.json` as EV-001 with source `ServiceNow`, type `ticket`, strength `soft`, "
            "and supports for symptom, impact, or timeline only if the ticket actually contains those facts."
        )
    if "technical evidence" in missing:
        return (
            "Collect one hard technical signal for the incident window. "
            "Use `commands/cloudwatch.md` or `commands/newrelic.md`, paste only the first 20 relevant rows into "
            "`evidence/query-results/`, then summarize it as a new hard evidence item."
        )
    if "impact" in missing:
        return (
            "Quantify impact. Ask for affected users, tenants, orders, messages, market/channel, and whether the issue is still active. "
            "Update `impact.md` and cite evidence IDs."
        )
    if "owner" in missing:
        return (
            "Identify likely owner from affected system, Confluence/runbook, repository README, Teams channel, or service catalog. "
            "Record the source as evidence before assigning ownership."
        )
    if "resolution path" in missing:
        return (
            "Document the current resolution path: workaround, rollback, vendor escalation, hotfix, monitoring-only closure, "
            "or Problem Record candidate. Do not mark resolved without validation."
        )
    if "validation" in missing:
        return (
            "Validate the workaround or fix with one named pattern: synthetic, log_based, metric_based, deployment_based, or user_based. "
            "Add the validation evidence before closure."
        )
    return (
        "Run the resolution gate and prepare a human review package. "
        "Do not close externally until a senior reviews `worknotes.md`, `final-summary.md`, and `resolution-gate.md`."
    )


def _worknote_stub(action: str) -> str:
    return (
        "[<timestamp>] Next investigation step identified.\n"
        f"Action: {action}\n"
        "Result: pending.\n"
        "Outcome: no root cause or resolution claim made yet.\n"
        "Next: update this note after the action is completed."
    )


def _learning_candidate_markdown(incident: Incident, case_dir: Path, created_at: str) -> str:
    quality = assess_evidence_quality(incident)
    state, missing = classify_resolution_state(incident)
    evidence_count = len(incident.evidence)
    hard_count = quality.hard_evidence_count
    soft_count = quality.soft_evidence_count
    missing_text = ", ".join(missing) if missing else "none"
    affected = ", ".join(incident.affected_systems) if incident.affected_systems else "unknown"
    return f"""# Learning Candidate: {incident.number}

Status: PENDING HUMAN REVIEW
Created: {created_at}
Case folder: {case_dir}

Do not promote this into durable Support-Monkey memory until a senior reviews
the evidence and removes sensitive details.

## Incident Snapshot

- Priority: {incident.priority}
- Short description: {incident.short_description or "not provided"}
- Affected systems: {affected}
- Resolution gate: {state}
- Evidence quality: {quality.score}/100 ({quality.risk})
- Evidence items: {evidence_count}
- Hard evidence items: {hard_count}
- Soft evidence items: {soft_count}
- Missing evidence classes: {missing_text}

## Candidate Learning

Write the reusable lesson here after review. Keep it general enough to help the
next incident without exposing customer data, secrets, hostnames, account IDs,
or internal URLs.

## Evidence That Supports The Learning

List evidence IDs and short summaries. Do not paste raw sensitive logs.

## Applicability

- Services / repo patterns:
- Error signatures:
- Safe next checks:
- Known workaround:
- Validation pattern:

## Review Checklist

- [ ] Root cause is supported or phrased as a hypothesis.
- [ ] Sensitive data removed.
- [ ] Vendor/team blame is evidence-backed or removed.
- [ ] The lesson is reusable.
- [ ] The lesson does not conflict with runbooks or known ownership.
- [ ] A senior approved promotion to durable memory.

## Promotion Decision

- Decision: pending
- Reviewer:
- Reviewed at:
- Destination:
"""
