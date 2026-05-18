import json
import tempfile
import unittest
from pathlib import Path

from support_monkey.cli import main
from support_monkey.models import Incident
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


if __name__ == "__main__":
    unittest.main()

