from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    source: str
    reference: str
    summary: str
    confidence: str = "unverified"


@dataclass(frozen=True)
class Incident:
    number: str
    priority: str
    short_description: str
    description: str
    caller_notes: str = ""
    opened_at: str = ""
    affected_systems: tuple[str, ...] = ()
    evidence: tuple[Evidence, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Incident":
        evidence_items = tuple(
            Evidence(
                source=str(item.get("source", "")).strip() or "unknown",
                reference=str(item.get("reference", "")).strip() or "n/a",
                summary=str(item.get("summary", "")).strip() or "No summary provided.",
                confidence=str(item.get("confidence", "")).strip() or "unverified",
            )
            for item in payload.get("evidence", [])
            if isinstance(item, dict)
        )
        affected_systems = tuple(
            str(item).strip()
            for item in payload.get("affectedSystems", [])
            if str(item).strip()
        )
        return cls(
            number=str(payload.get("number", "")).strip() or "UNKNOWN",
            priority=str(payload.get("priority", "")).strip() or "unknown",
            short_description=str(payload.get("shortDescription", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            caller_notes=str(payload.get("callerNotes", "")).strip(),
            opened_at=str(payload.get("openedAt", "")).strip(),
            affected_systems=affected_systems,
            evidence=evidence_items,
        )


@dataclass(frozen=True)
class TriagePack:
    incident: Incident
    impact_summary: str
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    required_evidence: tuple[str, ...] = field(default_factory=tuple)

