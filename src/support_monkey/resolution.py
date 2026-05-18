from __future__ import annotations

from .models import Incident
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


def classify_resolution_state(incident: Incident) -> tuple[str, tuple[str, ...]]:
    """Return the current resolution state and missing evidence classes.

    The result is intentionally conservative. Support-Monkey can draft next
    steps with weak evidence, but it should not claim closure or RCA until the
    minimum evidence classes are present.
    """

    present = _present_evidence_classes(incident)
    missing = tuple(item for item in MINIMUM_RESOLUTION_EVIDENCE if item not in present)
    if not missing:
        return "ready_for_human_review", ()
    if incident.evidence:
        return "needs_more_evidence", missing
    return "intake_incomplete", missing


def render_resolution_gate_markdown(incident: Incident) -> str:
    state, missing = classify_resolution_state(incident)
    lines = [
        f"# Resolution Gate: {incident.number}",
        "",
        f"State: `{state}`",
        "",
        "Support-Monkey should not claim root cause, customer impact, closure, or permanent fix until this gate is ready for human review.",
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
    return "\n".join(lines).strip() + "\n"


def _present_evidence_classes(incident: Incident) -> set[str]:
    present: set[str] = set()
    if incident.short_description or incident.description or incident.caller_notes:
        present.add("symptom")
    if incident.priority != "unknown" or incident.affected_systems:
        present.add("impact")
    if incident.opened_at:
        present.add("timeline")
    if incident.affected_systems:
        present.add("owner")

    for item in incident.evidence:
        text = f"{item.source} {item.reference} {item.summary}".lower()
        if any(token in text for token in ("log", "cloudwatch", "newrelic", "trace", "error", "stack")):
            present.add("technical evidence")
        if any(token in text for token in ("workaround", "fix", "vendor", "jira", "rollback", "mitigation")):
            present.add("resolution path")
        if any(token in text for token in ("validated", "verified", "confirmed", "monitoring", "retested")):
            present.add("validation")
        if any(token in text for token in ("owner", "repo", "service", "runbook", "team")):
            present.add("owner")
        if any(token in text for token in ("customer", "user", "orders", "requests", "tenant", "market")):
            present.add("impact")

    return present
