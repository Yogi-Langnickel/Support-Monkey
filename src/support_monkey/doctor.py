from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import sys


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str


def render_doctor_report(
    *,
    cases_dir: Path = Path("cases"),
    project_root: Path = Path("."),
    checks: tuple[DoctorCheck, ...] | None = None,
) -> str:
    checks = checks or run_doctor_checks(cases_dir=cases_dir, project_root=project_root)
    status = "ready" if doctor_checks_ready(checks) else "needs_attention"
    lines = [
        "# Support-Monkey Doctor",
        "",
        f"Status: `{status}`",
        "",
        "## Checks",
    ]
    for check in checks:
        marker = "ok" if check.ok else "needs_attention"
        lines.append(f"- `{marker}` {check.name}: {check.detail}")
    if status != "ready":
        lines.extend(
            (
                "",
                "## Next",
                "Fix the checks marked `needs_attention`, then run `support-monkey doctor` again.",
            )
        )
    return "\n".join(lines).strip() + "\n"


def doctor_checks_ready(checks: tuple[DoctorCheck, ...]) -> bool:
    return all(check.ok for check in checks)


def run_doctor_checks(*, cases_dir: Path = Path("cases"), project_root: Path = Path(".")) -> tuple[DoctorCheck, ...]:
    root = project_root.resolve()
    checks = [
        _python_check(),
        _file_check(root / "pyproject.toml", "project metadata"),
        _json_file_check(root / "examples" / "monday-test-incident.json", "Monday mock incident"),
        _file_check(root / "docs" / "monday-junior-test.md", "Monday junior test guide"),
        _file_check(root / "docs" / "transport" / "bootstrap-prompt.md", "portable bootstrap prompt"),
        _cases_dir_check(root / cases_dir),
    ]
    return tuple(checks)


def _python_check() -> DoctorCheck:
    version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    ok = sys.version_info >= (3, 9)
    detail = f"Python {version}" if ok else f"Python {version}; expected 3.9 or newer"
    return DoctorCheck("Python runtime", ok, detail)


def _file_check(path: Path, label: str) -> DoctorCheck:
    if path.exists() and path.is_file():
        return DoctorCheck(label, True, str(path))
    return DoctorCheck(label, False, f"missing: {path}")


def _json_file_check(path: Path, label: str) -> DoctorCheck:
    if not path.exists() or not path.is_file():
        return DoctorCheck(label, False, f"missing: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return DoctorCheck(label, False, f"invalid JSON: {error}")
    if not isinstance(payload, dict):
        return DoctorCheck(label, False, "JSON must be an object")
    number = str(payload.get("number", "")).strip()
    if not number:
        return DoctorCheck(label, False, "missing incident number")
    return DoctorCheck(label, True, f"{path} ({number})")


def _cases_dir_check(path: Path) -> DoctorCheck:
    if path.exists() and not path.is_dir():
        return DoctorCheck("case directory", False, f"not a directory: {path}")
    try:
        path.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return DoctorCheck("case directory", False, f"cannot create {path}: {error}")
    return DoctorCheck("case directory", True, str(path))
