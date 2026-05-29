from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import re

from .models import Incident
from .resolution import assess_evidence_quality, classify_resolution_state, render_resolution_gate_markdown


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


@dataclass(frozen=True)
class CaseImportResult:
    case_dir: Path
    incident_number: str
    created_files: tuple[Path, ...]
    existing_files: tuple[Path, ...]
    overwritten_files: tuple[Path, ...]


@dataclass(frozen=True)
class CaseUpdateResult:
    case_dir: Path
    incident_number: str
    updated_files: tuple[Path, ...]
    worknote: str


@dataclass(frozen=True)
class EvidenceAddResult:
    case_dir: Path
    incident_number: str
    evidence_id: str
    updated_files: tuple[Path, ...]
    artifact_instruction: str


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
        "- If the requested data is unavailable, ask the assistant to record the exact blocker in the case files.",
        "- Do not claim root cause yet unless the resolution gate says the case is ready for human review.",
        "",
        "## Copy-Ready Worknote Stub",
        "```text",
        _worknote_stub(action),
        "```",
    ]
    return "\n".join(lines).strip() + "\n"


def import_incident_case(
    incident_payload: dict[str, object],
    *,
    cases_dir: Path = Path("cases"),
    overwrite: bool = False,
    now: datetime | None = None,
) -> CaseImportResult:
    incident = Incident.from_dict(incident_payload)
    created_case = create_incident_case(incident.number, cases_dir=cases_dir, now=now)
    case_dir = created_case.case_dir
    newly_created = set(created_case.created_files)
    overwritten: list[Path] = []

    incident_file_payload = _case_incident_payload(incident_payload, incident.number, now=now)
    evidence_payload = {
        "incidentNumber": incident.number,
        "items": list(incident_file_payload.get("evidence", [])),
    }
    writes = {
        "incident.json": json.dumps(incident_file_payload, indent=2) + "\n",
        "evidence-ledger.json": json.dumps(evidence_payload, indent=2) + "\n",
        "incident.md": _incident_markdown_from_incident(Incident.from_dict(incident_file_payload)),
        "worknotes.md": _imported_worknotes_markdown(Incident.from_dict(incident_file_payload)),
    }
    for relative, content in writes.items():
        path = case_dir / relative
        if path.exists() and path not in newly_created and not overwrite:
            continue
        path.write_text(content, encoding="utf-8")
        overwritten.append(path)

    return CaseImportResult(
        case_dir=case_dir,
        incident_number=incident.number,
        created_files=created_case.created_files,
        existing_files=created_case.existing_files,
        overwritten_files=tuple(overwritten),
    )


def render_case_status(case_path: Path) -> str:
    case_dir = _resolve_case_dir(case_path)
    incident = _read_case_incident(case_dir)
    state, missing = classify_resolution_state(incident)
    quality = assess_evidence_quality(incident)
    affected = ", ".join(incident.affected_systems) if incident.affected_systems else "unknown"
    evidence = incident.evidence
    hard = quality.hard_evidence_count
    soft = quality.soft_evidence_count
    missing_text = ", ".join(missing) if missing else "none"
    next_action = _next_action(incident, missing)
    files = _case_file_health(case_dir)

    lines = [
        f"# Case Status: {incident.number}",
        "",
        f"Case folder: `{case_dir}`",
        f"Priority: `{incident.priority}`",
        f"Opened: `{incident.opened_at or 'unknown'}`",
        f"Affected systems: {affected}",
        f"Resolution gate: `{state}`",
        f"Evidence quality: `{quality.score}/100` (`{quality.risk}`)",
        f"Evidence items: `{len(evidence)}` (hard `{hard}`, soft `{soft}`)",
        f"Missing evidence classes: {missing_text}",
        "",
        "## File Health",
        *files,
        "",
        "## Recommended Next Action",
        next_action,
    ]
    return "\n".join(lines).strip() + "\n"


def update_case_context(
    case_path: Path,
    *,
    priority: str = "",
    opened_at: str = "",
    short_description: str = "",
    description: str = "",
    caller_notes: str = "",
    affected_systems: tuple[str, ...] = (),
    impact_scope: str = "",
    impact_depth: str = "",
    affected_users_estimate: str = "",
    impact_evidence_ids: tuple[str, ...] = (),
    now: datetime | None = None,
) -> CaseUpdateResult:
    case_dir = _resolve_case_dir(case_path)
    payload = _read_case_payload(case_dir)

    _set_if_present(payload, "priority", priority)
    _set_if_present(payload, "openedAt", opened_at)
    _set_if_present(payload, "shortDescription", short_description)
    _set_if_present(payload, "description", description)
    _set_if_present(payload, "callerNotes", caller_notes)
    if affected_systems:
        existing = [str(item).strip() for item in payload.get("affectedSystems", []) if str(item).strip()]
        for system in affected_systems:
            value = system.strip()
            if value and value not in existing:
                existing.append(value)
        payload["affectedSystems"] = existing
    if impact_scope.strip() or impact_depth.strip() or affected_users_estimate.strip() or impact_evidence_ids:
        impact = payload.get("impact")
        if not isinstance(impact, dict):
            impact = {}
        impact = dict(impact)
        _set_if_present(impact, "scope", impact_scope)
        _set_if_present(impact, "depth", impact_depth)
        if affected_users_estimate.strip():
            try:
                impact["affectedUsersEstimate"] = int(affected_users_estimate.strip())
            except ValueError as error:
                raise ValueError("affected users estimate must be a number") from error
        if impact_evidence_ids:
            existing_ids = [str(item).strip() for item in impact.get("evidenceIds", []) if str(item).strip()]
            for evidence_id in impact_evidence_ids:
                value = evidence_id.strip()
                if value and value not in existing_ids:
                    existing_ids.append(value)
            impact["evidenceIds"] = existing_ids
        payload["impact"] = impact

    timestamp = _iso_now(now)
    incident = Incident.from_dict(payload)
    fields = _context_field_summary(
        priority=priority,
        opened_at=opened_at,
        short_description=short_description,
        description=description,
        caller_notes=caller_notes,
        affected_systems=affected_systems,
        impact_scope=impact_scope,
        impact_depth=impact_depth,
        affected_users_estimate=affected_users_estimate,
        impact_evidence_ids=impact_evidence_ids,
    )
    worknote = (
        f"[{timestamp}] Support-Monkey updated incident context from collected user input.\n"
        f"Result: {fields}.\n"
        "Outcome: Case files refreshed automatically; no manual case-file editing required.\n"
        "Next: Run support-monkey next for the next bounded investigation action."
    )
    updated = _write_case_state(case_dir, payload, incident=incident)
    _append_worknote(case_dir, worknote)
    return CaseUpdateResult(
        case_dir=case_dir,
        incident_number=incident.number,
        updated_files=updated + (case_dir / "worknotes.md",),
        worknote=worknote,
    )


def add_case_evidence(
    case_path: Path,
    *,
    source: str,
    evidence_type: str,
    strength: str,
    reference: str = "",
    summary: str,
    supports: tuple[str, ...] = (),
    confidence: str = "unverified",
    observed_at: str = "",
    evidence_id: str = "",
    artifact_kind: str = "",
    artifact_name: str = "",
    timeline_event: str = "",
    now: datetime | None = None,
) -> EvidenceAddResult:
    case_dir = _resolve_case_dir(case_path)
    payload = _read_case_payload(case_dir)
    ledger = _read_evidence_ledger(case_dir, incident_number=str(payload.get("number", "UNKNOWN")))
    items = ledger.setdefault("items", [])
    if not isinstance(items, list):
        raise ValueError("evidence-ledger.json items must be a list")

    new_id = evidence_id.strip() or _next_evidence_id(items)
    artifact_instruction = _artifact_instruction(case_dir, artifact_kind=artifact_kind, artifact_name=artifact_name)
    if artifact_name and not reference:
        reference = _artifact_reference(artifact_kind=artifact_kind, artifact_name=artifact_name)

    item = {
        "id": new_id,
        "source": source.strip() or "unknown",
        "type": evidence_type.strip().lower() or "unknown",
        "strength": strength.strip().lower() or "unknown",
        "reference": reference.strip() or "n/a",
        "confidence": confidence.strip().lower() or "unverified",
        "supports": [value.strip() for value in supports if value.strip()],
        "summary": summary.strip() or "No summary provided.",
    }
    if observed_at.strip():
        item["observedAt"] = observed_at.strip()
    if artifact_kind.strip() and artifact_name.strip():
        item["artifact"] = _artifact_reference(artifact_kind=artifact_kind, artifact_name=artifact_name)

    items.append(item)
    payload["evidence"] = items
    if timeline_event.strip():
        timeline = payload.setdefault("timeline", [])
        if not isinstance(timeline, list):
            raise ValueError("incident.json timeline must be a list")
        timeline.append(
            {
                "occurredAt": observed_at.strip() or _iso_now(now),
                "summary": timeline_event.strip(),
                "evidenceId": new_id,
            }
        )

    incident = Incident.from_dict(payload)
    updated = _write_case_state(case_dir, payload, ledger=ledger, incident=incident)
    timestamp = _iso_now(now)
    worknote = (
        f"[{timestamp}] Support-Monkey recorded evidence {new_id} from collected user input.\n"
        f"Result: {item['source']} {item['type']} evidence captured with strength={item['strength']}; reference={item['reference']}.\n"
        "Outcome: Evidence ledger and derived case files refreshed automatically.\n"
        "Next: Run support-monkey next to continue the investigation."
    )
    _append_worknote(case_dir, worknote)
    return EvidenceAddResult(
        case_dir=case_dir,
        incident_number=incident.number,
        evidence_id=new_id,
        updated_files=updated + (case_dir / "worknotes.md",),
        artifact_instruction=artifact_instruction,
    )


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


def _set_if_present(payload: dict[str, object], key: str, value: str) -> None:
    if value.strip():
        payload[key] = value.strip()


def _context_field_summary(
    *,
    priority: str,
    opened_at: str,
    short_description: str,
    description: str,
    caller_notes: str,
    affected_systems: tuple[str, ...],
    impact_scope: str,
    impact_depth: str,
    affected_users_estimate: str,
    impact_evidence_ids: tuple[str, ...],
) -> str:
    labels = []
    if priority.strip():
        labels.append("priority")
    if opened_at.strip():
        labels.append("opened time")
    if short_description.strip():
        labels.append("short description")
    if description.strip():
        labels.append("description")
    if caller_notes.strip():
        labels.append("caller notes")
    if affected_systems:
        labels.append("affected systems")
    if impact_scope.strip():
        labels.append("impact scope")
    if impact_depth.strip():
        labels.append("impact depth")
    if affected_users_estimate.strip():
        labels.append("affected users estimate")
    if impact_evidence_ids:
        labels.append("impact evidence IDs")
    return ", ".join(labels) if labels else "no populated fields supplied"


def _read_case_payload(case_dir: Path) -> dict[str, object]:
    incident_path = case_dir / "incident.json"
    payload = json.loads(incident_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"incident JSON must be an object: {incident_path}")
    ledger = _read_evidence_ledger(case_dir, incident_number=str(payload.get("number", "UNKNOWN")))
    items = ledger.get("items", [])
    if isinstance(items, list):
        payload["evidence"] = items
    return payload


def _read_evidence_ledger(case_dir: Path, *, incident_number: str) -> dict[str, object]:
    ledger_path = case_dir / "evidence-ledger.json"
    if not ledger_path.exists():
        return {"incidentNumber": incident_number, "items": []}
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    if not isinstance(ledger, dict):
        raise ValueError(f"evidence ledger must be an object: {ledger_path}")
    ledger.setdefault("incidentNumber", incident_number)
    ledger.setdefault("items", [])
    return ledger


def _write_case_state(
    case_dir: Path,
    payload: dict[str, object],
    *,
    ledger: dict[str, object] | None = None,
    incident: Incident | None = None,
) -> tuple[Path, ...]:
    incident = incident or Incident.from_dict(payload)
    if ledger is None:
        ledger = {
            "incidentNumber": incident.number,
            "items": list(payload.get("evidence", [])) if isinstance(payload.get("evidence"), list) else [],
        }
    payload = dict(payload)
    payload["number"] = incident.number
    payload["evidence"] = ledger.get("items", [])

    writes = {
        "incident.json": json.dumps(payload, indent=2) + "\n",
        "evidence-ledger.json": json.dumps(ledger, indent=2) + "\n",
        "incident.md": _incident_markdown_from_incident(incident),
        "timeline.md": _timeline_markdown_from_incident(incident),
        "impact.md": _impact_markdown_from_incident(incident),
        "resolution-gate.md": render_resolution_gate_markdown(incident),
    }
    updated: list[Path] = []
    for relative, content in writes.items():
        path = case_dir / relative
        path.write_text(content, encoding="utf-8")
        updated.append(path)
    return tuple(updated)


def _append_worknote(case_dir: Path, entry: str) -> None:
    path = case_dir / "worknotes.md"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n```text\n")
        handle.write(entry.strip())
        handle.write("\n```\n")


def _next_evidence_id(items: list[object]) -> str:
    highest = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        raw = str(item.get("id") or item.get("evidenceId") or "")
        match = re.match(r"^EV-(\d+)$", raw)
        if match:
            highest = max(highest, int(match.group(1)))
    return f"EV-{highest + 1:03d}"


def _artifact_reference(*, artifact_kind: str, artifact_name: str) -> str:
    directory = _artifact_directory_name(artifact_kind)
    return f"evidence/{directory}/{artifact_name.strip()}"


def _artifact_instruction(case_dir: Path, *, artifact_kind: str, artifact_name: str) -> str:
    if not artifact_name.strip():
        return ""
    target = case_dir / _artifact_reference(artifact_kind=artifact_kind, artifact_name=artifact_name)
    if target.exists():
        return f"Artifact already present: {target}"
    return f"Ask the junior to copy the artifact to: {target}"


def _artifact_directory_name(artifact_kind: str) -> str:
    normalized = artifact_kind.strip().lower().replace("_", "-")
    mapping = {
        "screenshot": "screenshots",
        "screenshots": "screenshots",
        "log": "logs",
        "logs": "logs",
        "export": "exports",
        "exports": "exports",
        "query": "query-results",
        "query-result": "query-results",
        "query-results": "query-results",
    }
    return mapping.get(normalized, "exports")


def _case_incident_payload(
    incident_payload: dict[str, object],
    incident_number: str,
    *,
    now: datetime | None,
) -> dict[str, object]:
    payload = dict(incident_payload)
    payload["number"] = incident_number
    timestamp = _iso_now(now)
    case_payload = payload.get("case")
    if not isinstance(case_payload, dict):
        case_payload = {}
    case_payload = dict(case_payload)
    case_payload.setdefault("createdAt", timestamp)
    case_payload.setdefault("startedAt", timestamp)
    case_payload.setdefault("resolvedAt", "")
    case_payload.setdefault("status", "intake")
    payload["case"] = case_payload
    payload.setdefault("evidence", [])
    payload.setdefault("timeline", [])
    payload.setdefault(
        "impact",
        {
            "scope": "unknown",
            "depth": "unknown",
            "affectedUsersEstimate": None,
            "evidenceIds": [],
        },
    )
    payload.setdefault("affectedSystems", [])
    return payload


def _incident_markdown_from_incident(incident: Incident) -> str:
    affected = ", ".join(incident.affected_systems)
    known_items = []
    if incident.short_description:
        known_items.append(f"- Symptom reported: {incident.short_description}")
    if incident.opened_at:
        known_items.append(f"- Opened: {incident.opened_at}")
    if affected:
        known_items.append(f"- Affected systems reported: {affected}")
    if incident.evidence:
        known_items.append(f"- Evidence items imported: {len(incident.evidence)}")
    known = "\n".join(known_items) if known_items else "- Pending ServiceNow details."
    description = incident.description or "not provided"
    caller_notes = incident.caller_notes or "not provided"
    return f"""# Incident {incident.number}

Status: intake
Case created:
Started:
Resolved:
Duration:

## ServiceNow Details

- Incident number: {incident.number}
- Priority: {incident.priority}
- Opened: {incident.opened_at or "unknown"}
- Short description: {incident.short_description or "not provided"}
- Description: {description}
- Caller / reporter notes: {caller_notes}

## Current Situation

- Reported symptom: {incident.short_description or "unknown"}
- Affected user journey:
- Affected systems: {affected or "unknown"}
- Known customer impact:
- Current workaround:

## Known / Unknown / Assumed

### Known

{known}

### Unknown

- Exact failing component.
- Quantified impact scope.
- Hard technical evidence.
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


def _imported_worknotes_markdown(incident: Incident) -> str:
    opened = incident.opened_at or "unknown"
    return f"""# Worknotes: {incident.number}

Use this file for ServiceNow-copyable internal worknotes. Keep entries factual,
timestamped, and evidence-based. Do not claim root cause until the resolution
gate is ready for human review.

## Worknote Entries

```text
[<timestamp>] Imported ServiceNow-style incident details into Support-Monkey case.
Result: Priority={incident.priority}; opened={opened}; short description=\"{incident.short_description or 'not provided'}\".
Outcome: Ticket data is intake/soft evidence only. No root cause, impact, workaround, or validation confirmed yet.
Next: Run support-monkey next for the first required evidence-gathering action.
```
"""


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


def _timeline_markdown_from_incident(incident: Incident) -> str:
    lines = [
        "# Timeline",
        "",
        "Use ISO 8601 timestamps and cite an evidence ID for every row.",
        "",
        "| Timestamp | Event | Evidence ID |",
        "| --- | --- | --- |",
    ]
    if incident.timeline:
        for entry in incident.timeline:
            lines.append(
                f"| {entry.occurred_at or 'unknown'} | {entry.summary} | {entry.evidence_id or 'pending'} |"
            )
    else:
        lines.append("| pending | pending | pending |")
    return "\n".join(lines).strip() + "\n"


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


def _impact_markdown_from_incident(incident: Incident) -> str:
    impact = incident.impact
    affected = impact.affected_users_estimate if impact.affected_users_estimate is not None else "unknown"
    evidence = ", ".join(impact.evidence_ids) if impact.evidence_ids else "pending"
    return f"""# Impact Analysis

## Current Impact

- Scope: {impact.scope}
- Depth: {impact.depth}
- Affected users / tenants: {affected}
- Business function affected: unknown
- Data/payment/security risk: unknown
- Evidence IDs: {evidence}

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


def _case_file_health(case_dir: Path) -> tuple[str, ...]:
    expected = (
        "incident.json",
        "incident.md",
        "worknotes.md",
        "evidence-ledger.json",
        "timeline.md",
        "impact.md",
        "hypotheses.md",
        "resolution-gate.md",
        "problem-record-candidate.md",
        "commands/cloudwatch.md",
        "commands/sql.md",
        "final-summary.md",
    )
    rows = []
    for relative in expected:
        marker = "ok" if (case_dir / relative).exists() else "missing"
        rows.append(f"- `{relative}`: {marker}")
    return tuple(rows)


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
    quality = assess_evidence_quality(incident)
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
            "The assistant should run `support-monkey add-evidence` with source `ServiceNow`, type `ticket`, "
            "strength `soft`, and supports for symptom, impact, or timeline only if the ticket actually contains those facts."
        )
    if quality.hard_evidence_count == 0:
        return (
            "Collect one hard technical signal for the incident window before choosing a resolution path. "
            "Use `commands/cloudwatch.md` or `commands/newrelic.md`; the assistant should summarize the first 20 relevant rows "
            "with `support-monkey add-evidence`. If there is an exported file, copy it only to the artifact path printed by Support-Monkey."
        )
    if "technical evidence" in missing:
        return (
            "Collect one hard technical signal for the incident window. "
            "Use `commands/cloudwatch.md` or `commands/newrelic.md`; the assistant should summarize the first 20 relevant rows "
            "with `support-monkey add-evidence`. If there is an exported file, copy it only to the artifact path printed by Support-Monkey."
        )
    if "impact" in missing:
        return (
            "Quantify impact. Ask for affected users, tenants, orders, messages, market/channel, and whether the issue is still active. "
            "The assistant should update the case files and cite evidence IDs; the junior should not edit `impact.md` manually."
        )
    if "owner" in missing:
        return (
            "Identify likely owner from affected system, Confluence/runbook, repository README, Teams channel, or service catalog. "
            "Record the source as evidence before assigning ownership."
        )
    if "resolution path" in missing:
        return (
            "Ask for the current resolution path: workaround, rollback, vendor escalation, hotfix, monitoring-only closure, "
            "or Problem Record candidate. The assistant should record it with `support-monkey add-evidence`; do not mark resolved without validation."
        )
    if "validation" in missing:
        return (
            "Validate the workaround or fix with one named pattern: synthetic, log_based, metric_based, deployment_based, or user_based. "
            "The assistant should record validation evidence with `support-monkey add-evidence` before closure."
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
        "Next: ask the assistant to record the result after the action is completed."
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
