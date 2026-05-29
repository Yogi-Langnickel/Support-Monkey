from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .cases import capture_learning_candidate, create_incident_case, render_case_next_action
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

    next_parser = subparsers.add_parser(
        "next",
        help="Show the next small investigation step for a case folder.",
    )
    next_parser.add_argument("case", type=Path)

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

    args = parser.parse_args(argv)
    if args.command == "triage":
        return _triage(args.incident_json)
    if args.command == "new-incident":
        return _new_incident(args.incident_number, cases_dir=args.cases_dir)
    if args.command == "next":
        return _next(args.case)
    if args.command == "capture-learning":
        return _capture_learning(args.case, learnings_dir=args.learnings_dir)
    if args.command == "questions":
        return _questions(args.incident_json)
    if args.command == "resolution-gate":
        return _resolution_gate(args.incident_json)
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


def _next(case_path: Path) -> int:
    try:
        print(render_case_next_action(case_path), end="")
    except (FileNotFoundError, OSError, ValueError, json.JSONDecodeError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
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


def _read_incident(path: Path) -> Incident | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"error: failed to read {path}: {error}", file=sys.stderr)
        return None
    except json.JSONDecodeError as error:
        print(f"error: invalid JSON in {path}: {error}", file=sys.stderr)
        return None

    if not isinstance(payload, dict):
        print("error: incident JSON must be an object", file=sys.stderr)
        return None

    return Incident.from_dict(payload)


if __name__ == "__main__":
    raise SystemExit(main())
