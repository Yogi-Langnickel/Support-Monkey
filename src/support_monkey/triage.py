from __future__ import annotations

from .models import Incident, TriagePack
from .questions import generate_clarification_questions


def build_triage_pack(incident: Incident) -> TriagePack:
    systems = ", ".join(incident.affected_systems) if incident.affected_systems else "unknown"
    impact = (
        f"Priority {incident.priority}; affected systems: {systems}. "
        "Impact must be confirmed from monitoring, logs, and ticket evidence."
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
    evidence_rows = "\n".join(
        f"| {item.source} | {item.reference} | {item.confidence} | {item.summary} |"
        for item in incident.evidence
    )
    if not evidence_rows:
        evidence_rows = "| pending | pending | unverified | No evidence collected yet. |"

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
        "| Source | Reference | Confidence | Summary |",
        "| --- | --- | --- | --- |",
        evidence_rows,
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
