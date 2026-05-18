from __future__ import annotations

from .models import Incident


def generate_clarification_questions(incident: Incident) -> tuple[str, ...]:
    """Return concrete questions needed to move an incident toward resolution."""

    questions: list[str] = []
    if not incident.short_description:
        questions.append("What is the shortest accurate description of the failing user journey?")
    if not incident.description and not incident.caller_notes:
        questions.append("What exactly did the call center or reporter record as the symptom?")
    if not incident.affected_systems:
        questions.append("Which application, service, API, batch job, or customer journey appears affected?")
    if not incident.opened_at:
        questions.append("When did the issue start, and what timezone is the timestamp in?")
    if not incident.evidence:
        questions.extend(
            (
                "Can you provide ServiceNow work notes, caller notes, screenshots, or exact error text?",
                "Can you provide relevant CloudWatch/NewRelic log snippets around the incident window?",
                "Which local repository or code path should I inspect first?",
            )
        )

    symptom_text = f"{incident.short_description} {incident.description} {incident.caller_notes}".lower()
    if any(token in symptom_text for token in ("customer", "user", "external", "client")):
        questions.append("How many users/customers are affected, and is there a known market, tenant, or channel pattern?")
    if any(token in symptom_text for token in ("vendor", "interface", "contract", "agreement")):
        questions.append("Which vendor/interface agreement applies, and what payload or SLA evidence is available?")
    if any(token in symptom_text for token in ("deploy", "release", "change", "config")):
        questions.append("What changed before the incident: deployment, config, data load, certificate, secret, or vendor release?")

    questions.append("What outcome would count as 100% resolved: workaround, hotfix branch, vendor ticket, Jira handoff, or monitoring-only closure?")
    return tuple(dict.fromkeys(questions))


def render_questions_markdown(incident: Incident) -> str:
    questions = generate_clarification_questions(incident)
    lines = [
        f"# Clarification Questions: {incident.number}",
        "",
        "Support-Monkey should keep asking for evidence until resolution is proven or a precise blocker is identified.",
        "",
    ]
    lines.extend(f"{index}. {question}" for index, question in enumerate(questions, start=1))
    return "\n".join(lines).strip() + "\n"

