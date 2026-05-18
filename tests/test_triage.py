import json
import tempfile
import unittest
from pathlib import Path

from support_monkey.cli import main
from support_monkey.models import Incident
from support_monkey.questions import generate_clarification_questions
from support_monkey.resolution import classify_resolution_state, render_resolution_gate_markdown
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
