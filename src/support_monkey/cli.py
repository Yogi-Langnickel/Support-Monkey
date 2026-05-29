from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .cases import (
    add_case_evidence,
    capture_learning_candidate,
    create_incident_case,
    import_incident_case,
    render_case_next_action,
    render_case_status,
    update_case_context,
)
from .doctor import doctor_checks_ready, render_doctor_report, run_doctor_checks
from .models import Incident
from .questions import render_questions_markdown
from .resolution import render_resolution_gate_markdown
from .triage import build_triage_pack, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="support-monkey")
    subparsers = parser.add_subparsers(dest="command", required=True)

    triage_parser = subparsers.add_parser("triage", help="Generate a local triage pack from incident JSON.")
    triage_parser.add_argument("incident_json", type=Path)

    new_incident_parser = subparsers.add_parser(
        "new-incident",
        help="Create a guarded local case folder for a new incident.",
    )
    new_incident_parser.add_argument("incident_number", nargs="?")
    new_incident_parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path("cases"),
        help="Directory where incident case folders are stored.",
    )

    import_parser = subparsers.add_parser(
        "import-incident",
        help="Create or update a local case folder from incident JSON.",
    )
    import_parser.add_argument("incident_json", type=Path)
    import_parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path("cases"),
        help="Directory where incident case folders are stored.",
    )
    import_parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite generated incident, evidence ledger, and worknotes files.",
    )

    next_parser = subparsers.add_parser(
        "next",
        help="Show the next small investigation step for a case folder.",
    )
    next_parser.add_argument("case", type=Path)

    status_parser = subparsers.add_parser(
        "status",
        help="Show concise readiness status for a case folder.",
    )
    status_parser.add_argument("case", type=Path)

    update_parser = subparsers.add_parser(
        "update-case",
        help="Let the assistant update case files from collected user context.",
    )
    update_parser.add_argument("case", type=Path)
    update_parser.add_argument("--priority", default="")
    update_parser.add_argument("--opened-at", default="")
    update_parser.add_argument("--short-description", default="")
    update_parser.add_argument("--description", default="")
    update_parser.add_argument("--caller-notes", default="")
    update_parser.add_argument("--affected-system", action="append", default=[])
    update_parser.add_argument("--impact-scope", default="")
    update_parser.add_argument("--impact-depth", default="")
    update_parser.add_argument("--affected-users-estimate", default="")
    update_parser.add_argument("--impact-evidence-id", action="append", default=[])

    evidence_parser = subparsers.add_parser(
        "add-evidence",
        help="Let the assistant append evidence and refresh case files.",
    )
    evidence_parser.add_argument("case", type=Path)
    evidence_parser.add_argument("--source", required=True)
    evidence_parser.add_argument("--type", required=True, dest="evidence_type")
    evidence_parser.add_argument("--strength", required=True)
    evidence_parser.add_argument("--summary", required=True)
    evidence_parser.add_argument("--reference", default="")
    evidence_parser.add_argument("--supports", action="append", default=[])
    evidence_parser.add_argument("--confidence", default="unverified")
    evidence_parser.add_argument("--observed-at", default="")
    evidence_parser.add_argument("--evidence-id", default="")
    evidence_parser.add_argument("--artifact-kind", default="")
    evidence_parser.add_argument("--artifact-name", default="")
    evidence_parser.add_argument("--timeline-event", default="")

    learn_parser = subparsers.add_parser(
        "capture-learning",
        help="Create a human-reviewed learning candidate from a case folder.",
    )
    learn_parser.add_argument("case", type=Path)
    learn_parser.add_argument(
        "--learnings-dir",
        type=Path,
        default=Path(".support-monkey/learnings/pending"),
        help="Directory for pending learning candidates.",
    )

    questions_parser = subparsers.add_parser(
        "questions",
        help="Generate clarification questions from incomplete incident JSON.",
    )
    questions_parser.add_argument("incident_json", type=Path)

    resolution_parser = subparsers.add_parser(
        "resolution-gate",
        help="Check whether an incident has enough cited evidence for human review.",
    )
    resolution_parser.add_argument("incident_json", type=Path)

    doctor_parser = subparsers.add_parser(
        "doctor",
        help="Check local readiness for the Monday junior test.",
    )
    doctor_parser.add_argument(
        "--cases-dir",
        type=Path,
        default=Path("cases"),
        help="Directory where incident case folders are stored.",
    )

    args = parser.parse_args(argv)
    if args.command == "triage":
        return _triage(args.incident_json)
    if args.command == "new-incident":
        return _new_incident(args.incident_number, cases_dir=args.cases_dir)
    if args.command == "import-incident":
        return _import_incident(
            args.incident_json,
            cases_dir=args.cases_dir,
            overwrite=args.overwrite,
        )
    if args.command == "next":
        return _next(args.case)
    if args.command == "status":
        return _status(args.case)
    if args.command == "update-case":
        return _update_case(
            args.case,
            priority=args.priority,
            opened_at=args.opened_at,
            short_description=args.short_description,
            description=args.description,
            caller_notes=args.caller_notes,
            affected_systems=tuple(args.affected_system),
            impact_scope=args.impact_scope,
            impact_depth=args.impact_depth,
            affected_users_estimate=args.affected_users_estimate,
            impact_evidence_ids=tuple(args.impact_evidence_id),
        )
    if args.command == "add-evidence":
        return _add_evidence(
            args.case,
            source=args.source,
            evidence_type=args.evidence_type,
            strength=args.strength,
            reference=args.reference,
            summary=args.summary,
            supports=tuple(args.supports),
            confidence=args.confidence,
            observed_at=args.observed_at,
            evidence_id=args.evidence_id,
            artifact_kind=args.artifact_kind,
            artifact_name=args.artifact_name,
            timeline_event=args.timeline_event,
        )
    if args.command == "capture-learning":
        return _capture_learning(args.case, learnings_dir=args.learnings_dir)
    if args.command == "questions":
        return _questions(args.incident_json)
    if args.command == "resolution-gate":
        return _resolution_gate(args.incident_json)
    if args.command == "doctor":
        return _doctor(cases_dir=args.cases_dir)
    parser.error(f"unknown command: {args.command}")
    return 2


def _triage(path: Path) -> int:
    incident = _read_incident(path)
    if incident is None:
        return 2
    print(render_markdown(build_triage_pack(incident)), end="")
    return 0


def _new_incident(incident_number: str | None, *, cases_dir: Path) -> int:
    number = incident_number
    if not number:
        try:
            number = input("Incident number: ").strip()
        except EOFError:
            print("error: incident number is required", file=sys.stderr)
            return 2
    try:
        result = create_incident_case(number, cases_dir=cases_dir)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Created case folder: {result.case_dir}")
    if result.created_files:
        print("Created files:")
        for path in result.created_files:
            print(f"- {path.relative_to(result.case_dir)}")
    if result.existing_files:
        print("Existing files left unchanged:")
        for path in result.existing_files:
            print(f"- {path.relative_to(result.case_dir)}")
    print(f"\nNext: support-monkey next {result.case_dir}")
    return 0


def _import_incident(path: Path, *, cases_dir: Path, overwrite: bool) -> int:
    payload = _read_json_object(path)
    if payload is None:
        return 2
    try:
        result = import_incident_case(payload, cases_dir=cases_dir, overwrite=overwrite)
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Imported incident {result.incident_number} into: {result.case_dir}")
    if result.created_files:
        print(f"Created base files: {len(result.created_files)}")
    if result.overwritten_files:
        print("Updated files:")
        for path in result.overwritten_files:
            print(f"- {path.relative_to(result.case_dir)}")
    if result.existing_files and not overwrite:
        print("Existing files preserved. Use --overwrite to refresh generated files.")
    print(f"\nNext: support-monkey status {result.case_dir}")
    return 0


def _next(case_path: Path) -> int:
    try:
        print(render_case_next_action(case_path), end="")
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


def _status(case_path: Path) -> int:
    try:
        print(render_case_status(case_path), end="")
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


def _update_case(
    case_path: Path,
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
) -> int:
    try:
        result = update_case_context(
            case_path,
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
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Updated case context for {result.incident_number}: {result.case_dir}")
    print("Updated files:")
    for path in result.updated_files:
        print(f"- {path.relative_to(result.case_dir)}")
    print(f"\nNext: support-monkey next {result.case_dir}")
    return 0


def _add_evidence(
    case_path: Path,
    *,
    source: str,
    evidence_type: str,
    strength: str,
    reference: str,
    summary: str,
    supports: tuple[str, ...],
    confidence: str,
    observed_at: str,
    evidence_id: str,
    artifact_kind: str,
    artifact_name: str,
    timeline_event: str,
) -> int:
    try:
        result = add_case_evidence(
            case_path,
            source=source,
            evidence_type=evidence_type,
            strength=strength,
            reference=reference,
            summary=summary,
            supports=supports,
            confidence=confidence,
            observed_at=observed_at,
            evidence_id=evidence_id,
            artifact_kind=artifact_kind,
            artifact_name=artifact_name,
            timeline_event=timeline_event,
        )
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Added evidence {result.evidence_id} to {result.incident_number}: {result.case_dir}")
    print("Updated files:")
    for path in result.updated_files:
        print(f"- {path.relative_to(result.case_dir)}")
    if result.artifact_instruction:
        print(f"\nArtifact: {result.artifact_instruction}")
    print(f"\nNext: support-monkey next {result.case_dir}")
    return 0


def _capture_learning(case_path: Path, *, learnings_dir: Path) -> int:
    try:
        result = capture_learning_candidate(case_path, learnings_dir=learnings_dir)
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"Created pending learning candidate for {result.incident_number}: {result.learning_path}")
    print("Review before promoting to durable memory.")
    return 0


def _questions(path: Path) -> int:
    incident = _read_incident(path)
    if incident is None:
        return 2
    print(render_questions_markdown(incident), end="")
    return 0


def _resolution_gate(path: Path) -> int:
    incident = _read_incident(path)
    if incident is None:
        return 2
    print(render_resolution_gate_markdown(incident), end="")
    return 0


def _doctor(*, cases_dir: Path) -> int:
    checks = run_doctor_checks(cases_dir=cases_dir)
    print(render_doctor_report(checks=checks), end="")
    return 0 if doctor_checks_ready(checks) else 2


def _read_incident(path: Path) -> Incident | None:
    payload = _read_json_object(path)
    if payload is None:
        return None
    return Incident.from_dict(payload)


def _read_json_object(path: Path) -> dict[str, object] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"error: failed to read {path}: {error}", file=sys.stderr)
        return None
    except json.JSONDecodeError as error:
        print(f"error: invalid JSON in {path}: {error}", file=sys.stderr)
        return None

    if not isinstance(payload, dict):
        print("error: JSON must be an object", file=sys.stderr)
        return None
    return payload


if __name__ == "__main__":
    raise SystemExit(main())
