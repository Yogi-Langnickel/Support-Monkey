from __future__ import annotations

from .models import Evidence, Incident, TriagePack
from .questions import generate_clarification_questions


def build_triage_pack(incident: Incident) -> TriagePack:
    systems = ", ".join(incident.affected_systems) if incident.affected_systems else "unknown"
    impact_detail = ""
    if incident.impact.scope != "unknown" or incident.impact.depth != "unknown":
        impact_detail = f" Structured impact: scope={incident.impact.scope}, depth={incident.impact.depth}."
    impact = (
        f"Priority {incident.priority}; affected systems: {systems}. "
        "Impact must be confirmed from monitoring, logs, and ticket evidence."
        f"{impact_detail}"
    )
    hypotheses = _initial_hypotheses(incident)
    required_evidence = (
        "ServiceNow ticket timeline and latest work notes",
        "NewRelic/APM errors around the incident window",
        "CloudWatch logs for affected services around the incident window",
        "Recent deployments or configuration changes",
        "Known related incidents, Jira tickets, or vendor notices",
        "Local repo path, runbook excerpt, pasted log output, or screenshot when API integration is blocked or not permitted",
    )
    next_actions = (
        "Confirm customer/user impact and affected journey from ticket notes.",
        "Identify owning service/repository from affected system names and runbooks.",
        "Collect cited log/APM evidence before stating root cause.",
        "If ServiceNow, Confluence, NewRelic, AWS, or repository APIs are unavailable, ask for local exports, pasted outputs, or local checkout paths instead.",
        "Draft workaround, product Jira, vendor escalation, or hotfix branch only after evidence supports it.",
    )
    return TriagePack(
        incident=incident,
        impact_summary=impact,
        hypotheses=hypotheses,
        next_actions=next_actions,
        required_evidence=required_evidence,
    )


def _initial_hypotheses(incident: Incident) -> tuple[str, ...]:
    text = f"{incident.short_description} {incident.description} {incident.caller_notes}".lower()
    hypotheses: list[str] = []
    if any(token in text for token in ("timeout", "timed out", "504", "latency")):
        hypotheses.append("Latency/timeout path: check upstream dependency response times and retry behavior.")
    if any(token in text for token in ("login", "auth", "token", "unauthorised", "unauthorized", "403", "401")):
        hypotheses.append("Authentication/authorization path: check identity provider, token claims, and role mapping.")
    if any(token in text for token in ("payment", "invoice", "checkout", "stripe")):
        hypotheses.append("Payment/order path: check provider status, webhook processing, and reconciliation.")
    if any(token in text for token in ("not found", "404", "missing", "blank")):
        hypotheses.append("Data/routing path: check identifiers, recent data changes, and routing rules.")
    if not hypotheses:
        hypotheses.append("Unknown path: start with timeline, affected journey, recent changes, and error-rate evidence.")
    return tuple(hypotheses)


def render_markdown(pack: TriagePack) -> str:
    incident = pack.incident
    evidence_rows = "\n".join(_evidence_row(item) for item in incident.evidence)
    if not evidence_rows:
        evidence_rows = "| pending | pending | pending | pending | pending | unverified | pending | No evidence collected yet. |"
    timeline_rows = "\n".join(
        f"| {item.occurred_at or 'unknown'} | {item.summary} | {item.evidence_id or 'pending'} |"
        for item in incident.timeline
    )
    if not timeline_rows:
        timeline_rows = "| pending | pending | pending |"
    impact_evidence = ", ".join(incident.impact.evidence_ids) if incident.impact.evidence_ids else "pending"
    impact_users = (
        incident.impact.affected_users_estimate
        if incident.impact.affected_users_estimate is not None
        else "unknown"
    )

    sections = [
        f"# Incident Triage Pack: {incident.number}",
        "## Ticket Summary",
        f"- Priority: {incident.priority}",
        f"- Opened: {incident.opened_at or 'unknown'}",
        f"- Short description: {incident.short_description or 'not provided'}",
        f"- Affected systems: {', '.join(incident.affected_systems) if incident.affected_systems else 'unknown'}",
        "",
        "## Caller / Call Center Notes",
        incident.caller_notes or incident.description or "No caller notes provided.",
        "",
        "## Impact Summary",
        pack.impact_summary,
        "",
        "## Evidence Ledger",
        "| ID | Source | Type | Strength | Reference | Confidence | Supports | Summary |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
        evidence_rows,
        "",
        "## Timeline",
        "| Timestamp | Event | Evidence ID |",
        "| --- | --- | --- |",
        timeline_rows,
        "",
        "## Impact",
        f"- Scope: {incident.impact.scope}",
        f"- Depth: {incident.impact.depth}",
        f"- Affected users estimate: {impact_users}",
        f"- Evidence IDs: {impact_evidence}",
        "",
        "## Working Hypotheses",
        *_bullet_list(pack.hypotheses),
        "",
        "## Required Evidence Before RCA",
        *_bullet_list(pack.required_evidence),
        "",
        "## Recommended Next Actions",
        *_bullet_list(pack.next_actions),
        "",
        "## Clarification Questions",
        *_bullet_list(generate_clarification_questions(incident)),
        "",
        "## Draft Work Notes",
        (
            "Initial triage started. Current state is evidence gathering; no root cause "
            "has been confirmed yet. Next update will cite monitoring/log/ticket evidence."
        ),
    ]
    return "\n".join(sections).strip() + "\n"


def _bullet_list(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(f"- {item}" for item in items)


def _evidence_row(item: Evidence) -> str:
    supports = ", ".join(item.supports) or "pending"
    return (
        f"| {item.evidence_id} | {item.source} | {item.evidence_type} | "
        f"{item.strength} | {item.reference} | {item.confidence} | "
        f"{supports} | {item.summary} |"
    )
