import json
import tempfile
import unittest
from pathlib import Path

from support_monkey.cli import main
from support_monkey.cases import (
    add_case_evidence,
    capture_learning_candidate,
    create_incident_case,
    import_incident_case,
    render_case_next_action,
    render_case_status,
    update_case_context,
)
from support_monkey.doctor import render_doctor_report
from support_monkey.models import Incident
from support_monkey.questions import generate_clarification_questions
from support_monkey.resolution import (
    assess_evidence_quality,
    classify_resolution_state,
    render_resolution_gate_markdown,
)
from support_monkey.triage import build_triage_pack, render_markdown


class TriageTest(unittest.TestCase):
    def test_create_incident_case_writes_junior_workflow_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_incident_case("INC0012345", cases_dir=Path(temp_dir))

            expected_files = {
                "incident.json",
                "incident.md",
                "worknotes.md",
                "evidence-ledger.json",
                "timeline.md",
                "impact.md",
                "hypotheses.md",
                "rca.md",
                "resolution-gate.md",
                "problem-record-candidate.md",
                "commands/README.md",
                "commands/cloudwatch.md",
                "commands/aws.md",
                "commands/sql.md",
                "commands/newrelic.md",
                "branches.md",
                "final-summary.md",
            }

            self.assertEqual(result.case_dir.name, "INC0012345")
            self.assertTrue(expected_files.issubset({str(path.relative_to(result.case_dir)) for path in result.created_files}))
            self.assertTrue((result.case_dir / "evidence" / "screenshots").is_dir())
            self.assertIn("ServiceNow-copyable", (result.case_dir / "worknotes.md").read_text(encoding="utf-8"))
            self.assertIn("INC0012345-fix", (result.case_dir / "branches.md").read_text(encoding="utf-8"))

    def test_cli_new_incident_creates_case_folder(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = main(["new-incident", "INC200", "--cases-dir", temp_dir])

            self.assertEqual(result, 0)
            self.assertTrue((Path(temp_dir) / "INC200" / "incident.json").exists())
            self.assertTrue((Path(temp_dir) / "INC200" / "worknotes.md").exists())

    def test_next_action_guides_missing_servicenow_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_incident_case("INC201", cases_dir=Path(temp_dir))

            markdown = render_case_next_action(result.case_dir)

            self.assertIn("# Next Action: INC201", markdown)
            self.assertIn("ServiceNow short description", markdown)
            self.assertIn("read-only", markdown)
            self.assertIn("Copy-Ready Worknote Stub", markdown)

    def test_next_action_guides_technical_evidence_when_ticket_intake_exists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = create_incident_case("INC202", cases_dir=Path(temp_dir))
            incident_path = result.case_dir / "incident.json"
            payload = json.loads(incident_path.read_text(encoding="utf-8"))
            payload.update(
                {
                    "priority": "P2",
                    "openedAt": "2026-05-29T10:00:00+10:00",
                    "shortDescription": "Checkout timeout",
                    "description": "Users see timeout on checkout.",
                    "affectedSystems": ["checkout-service"],
                }
            )
            incident_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            ledger_path = result.case_dir / "evidence-ledger.json"
            ledger_path.write_text(
                json.dumps(
                    {
                        "incidentNumber": "INC202",
                        "items": [
                            {
                                "id": "EV-001",
                                "source": "ServiceNow",
                                "type": "ticket",
                                "strength": "soft",
                                "reference": "INC202",
                                "supports": ["symptom", "impact", "timeline"],
                                "summary": "Ticket reports checkout timeout.",
                            }
                        ],
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )

            markdown = render_case_next_action(result.case_dir)

            self.assertIn("Collect one hard technical signal", markdown)
            self.assertIn("commands/cloudwatch.md", markdown)

    def test_capture_learning_creates_pending_human_review_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            result = create_incident_case("INC203", cases_dir=base_dir / "cases")
            incident_path = result.case_dir / "incident.json"
            payload = json.loads(incident_path.read_text(encoding="utf-8"))
            payload.update(
                {
                    "priority": "P2",
                    "shortDescription": "Checkout timeout",
                    "affectedSystems": ["checkout-service"],
                }
            )
            incident_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

            learning = capture_learning_candidate(
                result.case_dir,
                learnings_dir=base_dir / "learnings" / "pending",
            )

            content = learning.learning_path.read_text(encoding="utf-8")
            self.assertEqual(learning.incident_number, "INC203")
            self.assertIn("Status: PENDING HUMAN REVIEW", content)
            self.assertIn("Do not promote", content)
            self.assertIn("checkout-service", content)

    def test_cli_capture_learning_creates_pending_candidate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            case = create_incident_case("INC204", cases_dir=base_dir / "cases")

            result = main(
                [
                    "capture-learning",
                    str(case.case_dir),
                    "--learnings-dir",
                    str(base_dir / "learnings" / "pending"),
                ]
            )

            self.assertEqual(result, 0)
            self.assertTrue(list((base_dir / "learnings" / "pending").glob("INC204-*.md")))

    def test_import_incident_case_seeds_case_from_json_payload(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            payload = {
                "number": "INC205",
                "priority": "P2",
                "openedAt": "2026-06-01T09:10:00+10:00",
                "shortDescription": "Customer portal 502",
                "description": "Several users see intermittent 502.",
                "affectedSystems": ["customer-portal", "account-bff"],
                "evidence": [
                    {
                        "id": "EV-001",
                        "source": "ServiceNow",
                        "type": "ticket",
                        "strength": "soft",
                        "reference": "INC205",
                        "supports": ["symptom", "timeline"],
                        "summary": "Ticket reports intermittent 502.",
                    }
                ],
            }

            result = import_incident_case(payload, cases_dir=Path(temp_dir), overwrite=True)

            incident_json = json.loads((result.case_dir / "incident.json").read_text(encoding="utf-8"))
            evidence_json = json.loads((result.case_dir / "evidence-ledger.json").read_text(encoding="utf-8"))
            self.assertEqual(result.incident_number, "INC205")
            self.assertEqual(incident_json["shortDescription"], "Customer portal 502")
            self.assertEqual(evidence_json["items"][0]["id"], "EV-001")
            self.assertIn("Customer portal 502", (result.case_dir / "incident.md").read_text(encoding="utf-8"))
            self.assertIn("soft evidence only", (result.case_dir / "worknotes.md").read_text(encoding="utf-8"))

    def test_cli_import_incident_and_status_are_monday_friendly(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir)
            incident_path = base_dir / "incident.json"
            incident_path.write_text(
                json.dumps(
                    {
                        "number": "INC206",
                        "priority": "P3",
                        "openedAt": "2026-06-01T09:10:00+10:00",
                        "shortDescription": "Lookup timeout",
                        "description": "Call centre reports intermittent lookup timeout.",
                        "callerNotes": "Several users saw timeout errors around 09:10.",
                        "affectedSystems": ["lookup-api"],
                        "evidence": [
                            {
                                "id": "EV-001",
                                "source": "ServiceNow",
                                "type": "ticket",
                                "strength": "soft",
                                "reference": "INC206",
                                "confidence": "reported",
                                "supports": ["symptom", "timeline"],
                                "summary": "Reporter saw timeout errors in lookup-api.",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            import_result = main(["import-incident", str(incident_path), "--cases-dir", str(base_dir / "cases")])
            status = render_case_status(base_dir / "cases" / "INC206")

            self.assertEqual(import_result, 0)
            self.assertIn("# Case Status: INC206", status)
            self.assertIn("lookup-api", status)
            self.assertIn("Collect one hard technical signal", status)
            self.assertIn("Recommended Next Action", status)

    def test_doctor_reports_monday_readiness(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "examples").mkdir()
            (root / "docs" / "transport").mkdir(parents=True)
            (root / "pyproject.toml").write_text("[project]\nname = \"support-monkey\"\n", encoding="utf-8")
            (root / "examples" / "monday-test-incident.json").write_text(
                json.dumps({"number": "INC-MONDAY-001"}),
                encoding="utf-8",
            )
            (root / "docs" / "monday-junior-test.md").write_text("# Monday\n", encoding="utf-8")
            (root / "docs" / "transport" / "bootstrap-prompt.md").write_text("# Bootstrap\n", encoding="utf-8")

            report = render_doctor_report(cases_dir=Path("cases"), project_root=root)

            self.assertIn("Status: `ready`", report)
            self.assertIn("Monday mock incident", report)
            self.assertTrue((root / "cases").is_dir())

    def test_cli_doctor_runs_from_repo_root(self) -> None:
        self.assertEqual(main(["doctor", "--cases-dir", "cases"]), 0)

    def test_update_case_context_refreshes_files_without_manual_editing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case = create_incident_case("INC207", cases_dir=Path(temp_dir))

            result = update_case_context(
                case.case_dir,
                priority="P2",
                opened_at="2026-06-01T09:10:00+10:00",
                short_description="Customer portal 502",
                description="Call centre reports intermittent 502 during lookup.",
                caller_notes="Two users reported retries sometimes work.",
                affected_systems=("customer-portal", "account-bff"),
                impact_scope="call_centre",
                impact_depth="partial_outage",
                affected_users_estimate="2",
            )

            incident_json = json.loads((case.case_dir / "incident.json").read_text(encoding="utf-8"))
            impact_markdown = (case.case_dir / "impact.md").read_text(encoding="utf-8")
            self.assertEqual(result.incident_number, "INC207")
            self.assertEqual(incident_json["priority"], "P2")
            self.assertIn("account-bff", incident_json["affectedSystems"])
            self.assertEqual(incident_json["impact"]["affectedUsersEstimate"], 2)
            self.assertIn("Scope: call_centre", impact_markdown)
            self.assertIn("Customer portal 502", (case.case_dir / "incident.md").read_text(encoding="utf-8"))
            self.assertIn("Case files refreshed automatically", (case.case_dir / "worknotes.md").read_text(encoding="utf-8"))

    def test_add_case_evidence_refreshes_ledger_timeline_and_artifact_instruction(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case = create_incident_case("INC208", cases_dir=Path(temp_dir))
            update_case_context(
                case.case_dir,
                short_description="Lookup timeout",
                description="Ticket has enough intake detail.",
                opened_at="2026-06-01T09:10:00+10:00",
                affected_systems=("lookup-api",),
            )

            result = add_case_evidence(
                case.case_dir,
                source="CloudWatch",
                evidence_type="log",
                strength="hard",
                summary="Lookup-api emitted timeout errors during the incident window.",
                supports=("technical_evidence", "timeline"),
                confidence="confirmed",
                observed_at="2026-06-01T09:12:00+10:00",
                artifact_kind="log",
                artifact_name="lookup-timeouts.txt",
                timeline_event="CloudWatch query found lookup timeout errors.",
            )

            ledger = json.loads((case.case_dir / "evidence-ledger.json").read_text(encoding="utf-8"))
            timeline = (case.case_dir / "timeline.md").read_text(encoding="utf-8")
            status = render_case_status(case.case_dir)
            self.assertEqual(result.evidence_id, "EV-001")
            self.assertEqual(ledger["items"][0]["type"], "log")
            self.assertIn("evidence/logs/lookup-timeouts.txt", ledger["items"][0]["artifact"])
            self.assertIn("Ask the junior to copy the artifact to:", result.artifact_instruction)
            self.assertIn("CloudWatch query found lookup timeout errors.", timeline)
            self.assertIn("hard `1`", status)

    def test_cli_update_case_and_add_evidence_avoid_manual_file_edits(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            case = create_incident_case("INC209", cases_dir=Path(temp_dir))

            update_result = main(
                [
                    "update-case",
                    str(case.case_dir),
                    "--priority",
                    "P3",
                    "--short-description",
                    "Portal latency",
                    "--description",
                    "ServiceNow says lookup is slow.",
                    "--opened-at",
                    "2026-06-01T09:00:00+10:00",
                    "--affected-system",
                    "portal",
                    "--impact-scope",
                    "single_tenant",
                    "--affected-users-estimate",
                    "3",
                ]
            )
            evidence_result = main(
                [
                    "add-evidence",
                    str(case.case_dir),
                    "--source",
                    "ServiceNow",
                    "--type",
                    "ticket",
                    "--strength",
                    "soft",
                    "--summary",
                    "Ticket reports portal latency.",
                    "--supports",
                    "symptom",
                    "--supports",
                    "timeline",
                ]
            )

            self.assertEqual(update_result, 0)
            self.assertEqual(evidence_result, 0)
            self.assertIn("Ticket reports portal latency.", (case.case_dir / "evidence-ledger.json").read_text(encoding="utf-8"))

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

    def test_resolution_gate_does_not_treat_reported_errors_as_hard_technical_evidence(self) -> None:
        incident = Incident.from_dict(
            {
                "number": "INC108",
                "priority": "P2",
                "shortDescription": "Customer portal 502",
                "openedAt": "2026-05-18T09:00:00+10:00",
                "affectedSystems": ["customer-portal"],
                "evidence": [
                    {
                        "id": "EV-001",
                        "source": "ServiceNow",
                        "type": "ticket",
                        "strength": "soft",
                        "reference": "INC108",
                        "confidence": "reported",
                        "supports": ["symptom", "timeline"],
                        "summary": "Reporter saw intermittent 502 errors in the customer portal.",
                    }
                ],
            }
        )

        state, missing = classify_resolution_state(incident)
        quality = assess_evidence_quality(incident)

        self.assertEqual(state, "needs_more_evidence")
        self.assertIn("technical evidence", missing)
        self.assertEqual(quality.risk, "high_risk_soft_only")

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
