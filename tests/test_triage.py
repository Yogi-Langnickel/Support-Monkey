import json
import tempfile
import unittest
from pathlib import Path

from support_monkey.cli import main
from support_monkey.models import Incident
from support_monkey.questions import generate_clarification_questions
from support_monkey.resolution import (
    assess_evidence_quality,
    classify_resolution_state,
    render_resolution_gate_markdown,
)
from support_monkey.triage import build_triage_pack, render_markdown


class TriageTest(unittest.TestCase):
    def test_build_triage_pack_cites_ticket_evidence_and_timeout_hypothesis(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC42",
                "priority": "P1",
                "shortDescription": "Checkout timeout",
                "affectedSystems": ["checkout"],
                "evidence": [
                    {
                        "source": "ServiceNow",
                        "reference": "INC42",
                        "summary": "Caller reported timeout.",
                    }
                ],
            }
        )

        markdown = render_markdown(build_triage_pack(incident))

        self.assertIn("# Incident Triage Pack: INC42", markdown)
        self.assertIn("ServiceNow", markdown)
        self.assertIn("Latency/timeout path", markdown)
        self.assertIn("Required Evidence Before RCA", markdown)
        self.assertIn("Clarification Questions", markdown)
        self.assertIn("local checkout paths", markdown)
        self.assertIn("| ID | Source | Type | Strength | Reference | Confidence | Supports | Summary |", markdown)
        self.assertIn("## Timeline", markdown)
        self.assertIn("## Impact", markdown)

    def test_cli_generates_markdown_from_incident_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            incident_path = Path(temp_dir) / "incident.json"
            incident_path.write_text(
                json.dumps(
                    {
                        "number": "INC99",
                        "priority": "P3",
                        "shortDescription": "Missing order",
                    }
                ),
                encoding="utf-8",
            )

            result = main(["triage", str(incident_path)])

        self.assertEqual(result, 0)

    def test_questions_target_missing_resolution_evidence(self) -> None:
        incident = Incident.from_dict({"number": "INC100", "priority": "P2"})

        questions = generate_clarification_questions(incident)

        self.assertIn(
            "Which application, service, API, batch job, or customer journey appears affected?",
            questions,
        )
        self.assertTrue(any("100% resolved" in question for question in questions))

    def test_cli_generates_questions(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            incident_path = Path(temp_dir) / "incident.json"
            incident_path.write_text(
                json.dumps({"number": "INC101", "priority": "P4"}),
                encoding="utf-8",
            )

            result = main(["questions", str(incident_path)])

        self.assertEqual(result, 0)

    def test_resolution_gate_blocks_until_evidence_classes_are_present(self) -> None:
        incident = Incident.from_dict({"number": "INC102", "priority": "P2"})

        state, missing = classify_resolution_state(incident)
        markdown = render_resolution_gate_markdown(incident)

        self.assertEqual(state, "intake_incomplete")
        self.assertIn("technical evidence", missing)
        self.assertIn("resolution path", missing)
        self.assertIn("State: `intake_incomplete`", markdown)

    def test_resolution_gate_allows_human_review_after_cited_resolution_evidence(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC103",
                "priority": "P2",
                "shortDescription": "Checkout timeout",
                "openedAt": "2026-05-18T09:00:00+10:00",
                "affectedSystems": ["checkout-service"],
                "evidence": [
                    {
                        "source": "CloudWatch logs",
                        "reference": "checkout-service/2026-05-18T09:00",
                        "summary": "Error spike confirmed in service logs.",
                    },
                    {
                        "source": "Runbook",
                        "reference": "checkout owner matrix",
                        "summary": "Owner team and repository identified.",
                    },
                    {
                        "source": "ServiceNow work notes",
                        "reference": "INC103",
                        "summary": "Workaround applied, monitoring verified customer requests recovered.",
                    },
                ],
            }
        )

        state, missing = classify_resolution_state(incident)

        self.assertEqual(state, "ready_for_human_review")
        self.assertEqual(missing, ())

    def test_resolution_gate_uses_structured_evidence_classes(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC105",
                "priority": "P2",
                "shortDescription": "Checkout timeout",
                "openedAt": "2026-05-18T09:00:00+10:00",
                "affectedSystems": ["checkout-service"],
                "impact": {
                    "scope": "multi_tenant",
                    "depth": "latency_degradation",
                    "affectedUsersEstimate": 12,
                    "evidenceIds": ["EV-002"],
                },
                "timeline": [
                    {
                        "occurredAt": "2026-05-18T09:01:00+10:00",
                        "summary": "Error-rate SLI breached.",
                        "evidenceId": "EV-001",
                    }
                ],
                "evidence": [
                    {
                        "id": "EV-001",
                        "source": "APM",
                        "type": "metric",
                        "strength": "hard",
                        "reference": "checkout/error-rate",
                        "confidence": "confirmed",
                        "observedAt": "2026-05-18T09:01:00+10:00",
                        "supports": ["timeline", "technical_evidence"],
                        "summary": "Checkout error-rate SLI breached.",
                    },
                    {
                        "id": "EV-002",
                        "source": "ServiceNow",
                        "type": "ticket",
                        "strength": "soft",
                        "reference": "INC105",
                        "confidence": "likely",
                        "supports": ["symptom", "impact"],
                        "summary": "Multiple tenants reported checkout latency.",
                    },
                    {
                        "id": "EV-003",
                        "source": "Runbook",
                        "type": "runbook",
                        "strength": "hard",
                        "reference": "checkout ownership",
                        "confidence": "confirmed",
                        "supports": ["owner"],
                        "summary": "Checkout service owner identified.",
                    },
                    {
                        "id": "EV-004",
                        "source": "Deployment record",
                        "type": "deployment",
                        "strength": "hard",
                        "reference": "rollback 2026-05-18T09:20:00+10:00",
                        "confidence": "confirmed",
                        "supports": ["resolution_path", "validation"],
                        "validationPattern": "deployment_based",
                        "summary": "Rollback completed and error-rate returned to normal.",
                    },
                ],
            }
        )

        state, missing = classify_resolution_state(incident)
        quality = assess_evidence_quality(incident)

        self.assertEqual(state, "ready_for_human_review")
        self.assertEqual(missing, ())
        self.assertEqual(quality.risk, "defensible")
        self.assertGreaterEqual(quality.score, 85)

    def test_resolution_gate_flags_soft_only_evidence_quality(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC106",
                "priority": "P3",
                "shortDescription": "Checkout timeout",
                "openedAt": "2026-05-18T09:00:00+10:00",
                "affectedSystems": ["checkout-service"],
                "evidence": [
                    {
                        "id": "EV-001",
                        "source": "ServiceNow",
                        "type": "ticket",
                        "strength": "soft",
                        "reference": "INC106",
                        "confidence": "likely",
                        "supports": [
                            "symptom",
                            "impact",
                            "timeline",
                            "owner",
                            "technical_evidence",
                            "resolution_path",
                            "validation",
                        ],
                        "summary": "Reporter says the workaround fixed checkout.",
                    }
                ],
            }
        )

        state, missing = classify_resolution_state(incident)
        quality = assess_evidence_quality(incident)
        markdown = render_resolution_gate_markdown(incident)

        self.assertEqual(state, "needs_more_evidence")
        self.assertEqual(missing, ("hard evidence",))
        self.assertEqual(quality.risk, "high_risk_soft_only")
        self.assertIn("State: `needs_more_evidence`", markdown)
        self.assertIn("Data Quality Risk: `high_risk_soft_only`", markdown)
        self.assertIn("No hard evidence is present", markdown)

    def test_resolution_gate_rejects_broken_evidence_citations(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC107",
                "priority": "P2",
                "shortDescription": "Checkout timeout",
                "openedAt": "2026-05-18T09:00:00+10:00",
                "affectedSystems": ["checkout-service"],
                "impact": {
                    "scope": "multi_tenant",
                    "depth": "partial_outage",
                    "affectedUsersEstimate": 20,
                    "evidenceIds": ["EV-999"],
                },
                "timeline": [
                    {
                        "occurredAt": "2026-05-18T09:01:00+10:00",
                        "summary": "Error-rate SLI breached.",
                        "evidenceId": "EV-999",
                    }
                ],
                "evidence": [
                    {
                        "id": "EV-001",
                        "source": "CloudWatch logs",
                        "type": "log",
                        "strength": "hard",
                        "reference": "checkout-service/2026-05-18T09:00",
                        "confidence": "confirmed",
                        "supports": [
                            "technical_evidence",
                            "resolution_path",
                            "validation",
                        ],
                        "summary": "Rollback validated and error-rate returned to normal.",
                    }
                ],
            }
        )

        state, missing = classify_resolution_state(incident)
        quality = assess_evidence_quality(incident)
        markdown = render_resolution_gate_markdown(incident)

        self.assertEqual(state, "needs_more_evidence")
        self.assertEqual(missing, ("valid evidence citations",))
        self.assertEqual(quality.risk, "incomplete")
        self.assertIn("Timeline cites evidence IDs not present", markdown)
        self.assertIn("Impact cites evidence IDs not present", markdown)

    def test_cli_generates_resolution_gate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            incident_path = Path(temp_dir) / "incident.json"
            incident_path.write_text(
                json.dumps({"number": "INC104", "priority": "P4"}),
                encoding="utf-8",
            )

            result = main(["resolution-gate", str(incident_path)])

        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
