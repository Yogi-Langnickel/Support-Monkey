from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .models import Evidence, Incident
from .questions import generate_clarification_questions


MINIMUM_RESOLUTION_EVIDENCE = (
    "symptom",
    "impact",
    "timeline",
    "owner",
    "technical evidence",
    "resolution path",
    "validation",
)

HARD_EVIDENCE_TYPES = {
    "apm",
    "config",
    "deployment",
    "interface_contract",
    "log",
    "metric",
    "repository",
    "runbook",
    "synthetic_check",
    "trace",
    "vendor_payload",
}

SOFT_EVIDENCE_TYPES = {
    "chat",
    "email",
    "screenshot",
    "ticket",
    "user_report",
    "verbal_report",
}

CONFIDENCE_CRITERIA = {
    "confirmed": "Two independent hard evidence sources, or one authoritative hard source plus validation evidence.",
    "likely": "One hard evidence source that is consistent with the timeline and has no strong contradiction.",
    "possible": "A plausible hypothesis that has not been disproven but lacks direct hard evidence.",
    "unknown": "Evidence is absent, insufficient, or materially conflicting.",
}


@dataclass(frozen=True)
class EvidenceQualityReport:
    score: int
    risk: str
    hard_evidence_count: int
    soft_evidence_count: int
    covered_classes: tuple[str, ...]
    missing_classes: tuple[str, ...]
    issues: tuple[str, ...]


def classify_resolution_state(incident: Incident) -> tuple[str, tuple[str, ...]]:
    """Return the current resolution state and missing evidence classes.

    The result is intentionally conservative. Support-Monkey can draft next
    steps with weak evidence, but it should not claim closure or RCA until the
    minimum evidence classes are present.
    """

    present = _present_evidence_classes(incident)
    missing = tuple(item for item in MINIMUM_RESOLUTION_EVIDENCE if item not in present)
    if not missing:
        citation_issues = _citation_issues(incident)
        if citation_issues:
            return "needs_more_evidence", ("valid evidence citations",)
        if incident.evidence and not any(_is_hard_evidence(item) for item in incident.evidence):
            return "needs_more_evidence", ("hard evidence",)
        return "ready_for_human_review", ()
    if incident.evidence:
        return "needs_more_evidence", missing
    return "intake_incomplete", missing


def assess_evidence_quality(incident: Incident) -> EvidenceQualityReport:
    present = _present_evidence_classes(incident)
    missing = tuple(item for item in MINIMUM_RESOLUTION_EVIDENCE if item not in present)
    hard_count = sum(1 for item in incident.evidence if _is_hard_evidence(item))
    soft_count = sum(1 for item in incident.evidence if _is_soft_evidence(item))
    validation_items = tuple(
        item
        for item in incident.evidence
        if "validation" in _evidence_supported_classes(item)
    )

    coverage_score = round(
        (
            len(present.intersection(MINIMUM_RESOLUTION_EVIDENCE))
            / len(MINIMUM_RESOLUTION_EVIDENCE)
        )
        * 50
    )
    hard_score = min(hard_count, 2) * 15
    validation_score = 0
    if validation_items:
        validation_score = 15 if any(_is_hard_evidence(item) for item in validation_items) else 8
    confidence_score = (
        5
        if incident.evidence
        and all(item.confidence != "unverified" for item in incident.evidence)
        else 0
    )
    score = min(100, coverage_score + hard_score + validation_score + confidence_score)

    issues: list[str] = []
    if incident.evidence and hard_count == 0:
        issues.append("No hard evidence is present; RCA claims are high risk even if all fields are filled.")
    if missing:
        issues.append("Minimum resolution evidence classes are incomplete.")
    if any(
        item.observed_at and not _is_iso_8601(item.observed_at)
        for item in incident.evidence
    ):
        issues.append("One or more evidence timestamps are not ISO 8601.")
    if any(
        entry.occurred_at and not _is_iso_8601(entry.occurred_at)
        for entry in incident.timeline
    ):
        issues.append("One or more timeline timestamps are not ISO 8601.")
    if incident.timeline and any(not entry.evidence_id for entry in incident.timeline):
        issues.append("Every timeline entry should cite an evidence ID.")
    if incident.impact.scope != "unknown" and not incident.impact.evidence_ids:
        issues.append("Structured impact is present but has no evidence IDs.")
    issues.extend(_citation_issues(incident))

    if hard_count == 0 and incident.evidence:
        risk = "high_risk_soft_only"
    elif missing or _citation_issues(incident):
        risk = "incomplete"
    elif score >= 85:
        risk = "defensible"
    else:
        risk = "moderate"

    return EvidenceQualityReport(
        score=score,
        risk=risk,
        hard_evidence_count=hard_count,
        soft_evidence_count=soft_count,
        covered_classes=tuple(item for item in MINIMUM_RESOLUTION_EVIDENCE if item in present),
        missing_classes=missing,
        issues=tuple(issues),
    )


def render_resolution_gate_markdown(incident: Incident) -> str:
    state, missing = classify_resolution_state(incident)
    quality = assess_evidence_quality(incident)
    lines = [
        f"# Resolution Gate: {incident.number}",
        "",
        f"State: `{state}`",
        f"Data Quality Score: `{quality.score}/100`",
        f"Data Quality Risk: `{quality.risk}`",
        "",
        "Support-Monkey should not claim root cause, customer impact, closure, or permanent fix until this gate is ready for human review.",
        "",
        "## Evidence Quality",
        f"- Hard evidence items: {quality.hard_evidence_count}",
        f"- Soft evidence items: {quality.soft_evidence_count}",
        f"- Covered classes: {', '.join(quality.covered_classes) if quality.covered_classes else 'none'}",
        f"- Quality issues: {'; '.join(quality.issues) if quality.issues else 'none'}",
        "",
        "## Missing Evidence Classes",
    ]
    if missing:
        lines.extend(f"- {item}" for item in missing)
    else:
        lines.append("- none")

    lines.extend(
        (
            "",
            "## Clarification Loop",
            "Ask for the following until the missing classes are closed or a named blocker is documented:",
        )
    )
    lines.extend(f"- {question}" for question in generate_clarification_questions(incident))
    lines.extend(
        (
            "",
            "## Confidence Criteria",
            *(
                f"- `{label}`: {definition}"
                for label, definition in CONFIDENCE_CRITERIA.items()
            ),
        )
    )
    return "\n".join(lines).strip() + "\n"


def _present_evidence_classes(incident: Incident) -> set[str]:
    present: set[str] = set()
    if incident.short_description or incident.description or incident.caller_notes:
        present.add("symptom")
    if (
        incident.priority != "unknown"
        or incident.affected_systems
        or incident.impact.scope != "unknown"
        or incident.impact.depth != "unknown"
    ):
        present.add("impact")
    if incident.opened_at or incident.timeline:
        present.add("timeline")
    if incident.affected_systems:
        present.add("owner")

    for item in incident.evidence:
        present.update(_evidence_supported_classes(item))

    return present


def _evidence_supported_classes(item: Evidence) -> set[str]:
    present: set[str] = set()
    for value in item.supports:
        normalized = _normalize_evidence_class(value)
        if normalized in MINIMUM_RESOLUTION_EVIDENCE:
            present.add(normalized)

    text = f"{item.source} {item.reference} {item.summary}".lower()
    if any(
        token in text
        for token in ("log", "cloudwatch", "newrelic", "trace", "error", "stack")
    ):
        present.add("technical evidence")
    if any(
        token in text
        for token in ("workaround", "fix", "vendor", "jira", "rollback", "mitigation")
    ):
        present.add("resolution path")
    if any(
        token in text
        for token in ("validated", "verified", "confirmed", "monitoring", "retested")
    ):
        present.add("validation")
    if any(token in text for token in ("owner", "repository", "service", "runbook", "team")):
        present.add("owner")
    if any(
        token in text
        for token in ("customer", "user", "orders", "requests", "tenant", "market")
    ):
        present.add("impact")

    return present


def _normalize_evidence_class(value: str) -> str:
    return value.strip().lower().replace("_", " ").replace("-", " ")


def _citation_issues(incident: Incident) -> tuple[str, ...]:
    evidence_ids = {item.evidence_id for item in incident.evidence if item.evidence_id}
    issues: list[str] = []

    unknown_timeline_ids = sorted(
        {
            entry.evidence_id
            for entry in incident.timeline
            if entry.evidence_id and entry.evidence_id not in evidence_ids
        }
    )
    if unknown_timeline_ids:
        issues.append(
            "Timeline cites evidence IDs not present in the evidence ledger: "
            + ", ".join(unknown_timeline_ids)
            + "."
        )

    unknown_impact_ids = sorted(
        {
            evidence_id
            for evidence_id in incident.impact.evidence_ids
            if evidence_id not in evidence_ids
        }
    )
    if unknown_impact_ids:
        issues.append(
            "Impact cites evidence IDs not present in the evidence ledger: "
            + ", ".join(unknown_impact_ids)
            + "."
        )

    return tuple(issues)


def _is_hard_evidence(item: Evidence) -> bool:
    text = f"{item.source} {item.reference} {item.summary}".lower()
    return (
        item.strength == "hard"
        or item.evidence_type in HARD_EVIDENCE_TYPES
        or any(
            token in text
            for token in (
                "log",
                "cloudwatch",
                "newrelic",
                "metric",
                "trace",
                "deployment",
                "repository",
                "payload",
            )
        )
    )


def _is_soft_evidence(item: Evidence) -> bool:
    text = f"{item.source} {item.reference} {item.summary}".lower()
    return (
        item.strength == "soft"
        or item.evidence_type in SOFT_EVIDENCE_TYPES
        or any(
            token in text
            for token in ("servicenow", "ticket", "caller", "chat", "email", "reported")
        )
    )


def _is_iso_8601(value: str) -> bool:
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True
