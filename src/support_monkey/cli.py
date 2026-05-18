from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .models import Incident
from .questions import render_questions_markdown
from .triage import build_triage_pack, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="support-monkey")
    subparsers = parser.add_subparsers(dest="command", required=True)

    triage_parser = subparsers.add_parser("triage", help="Generate a local triage pack from incident JSON.")
    triage_parser.add_argument("incident_json", type=Path)

    questions_parser = subparsers.add_parser(
        "questions",
        help="Generate clarification questions from incomplete incident JSON.",
    )
    questions_parser.add_argument("incident_json", type=Path)

    args = parser.parse_args(argv)
    if args.command == "triage":
        return _triage(args.incident_json)
    if args.command == "questions":
        return _questions(args.incident_json)
    parser.error(f"unknown command: {args.command}")
    return 2


def _triage(path: Path) -> int:
    incident = _read_incident(path)
    if incident is None:
        return 2
    print(render_markdown(build_triage_pack(incident)), end="")
    return 0


def _questions(path: Path) -> int:
    incident = _read_incident(path)
    if incident is None:
        return 2
    print(render_questions_markdown(incident), end="")
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
