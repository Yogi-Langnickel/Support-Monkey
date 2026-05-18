from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from .models import Incident
from .triage import build_triage_pack, render_markdown


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="support-monkey")
    subparsers = parser.add_subparsers(dest="command", required=True)

    triage_parser = subparsers.add_parser("triage", help="Generate a local triage pack from incident JSON.")
    triage_parser.add_argument("incident_json", type=Path)

    args = parser.parse_args(argv)
    if args.command == "triage":
        return _triage(args.incident_json)
    parser.error(f"unknown command: {args.command}")
    return 2


def _triage(path: Path) -> int:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as error:
        print(f"error: failed to read {path}: {error}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as error:
        print(f"error: invalid JSON in {path}: {error}", file=sys.stderr)
        return 2

    if not isinstance(payload, dict):
        print("error: incident JSON must be an object", file=sys.stderr)
        return 2

    incident = Incident.from_dict(payload)
    print(render_markdown(build_triage_pack(incident)), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

