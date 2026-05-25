from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    source: str
    reference: str
    summary: str
    evidence_type: str = "unknown"
    strength: str = "unknown"
    confidence: str = "unverified"
    supports: tuple[str, ...] = ()
    observed_at: str = ""
    validation_pattern: str = ""


@dataclass(frozen=True)
class TimelineEntry:
    occurred_at: str
    summary: str
    evidence_id: str = ""


@dataclass(frozen=True)
class Impact:
    scope: str = "unknown"
    depth: str = "unknown"
    affected_users_estimate: int | None = None
    evidence_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Incident:
    number: str
    priority: str
    short_description: str
    description: str
    caller_notes: str = ""
    opened_at: str = ""
    affected_systems: tuple[str, ...] = ()
    impact: Impact = field(default_factory=Impact)
    timeline: tuple[TimelineEntry, ...] = ()
    evidence: tuple[Evidence, ...] = ()

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Incident":
        evidence_items = tuple(
            _evidence_from_dict(index, item)
            for index, item in enumerate(payload.get("evidence", []), start=1)
            if isinstance(item, dict)
        )
        affected_systems = tuple(
            str(item).strip()
            for item in payload.get("affectedSystems", [])
            if str(item).strip()
        )
        timeline_entries = tuple(
            _timeline_entry_from_dict(item)
            for item in payload.get("timeline", [])
            if isinstance(item, dict)
        )
        return cls(
            number=str(payload.get("number", "")).strip() or "UNKNOWN",
            priority=str(payload.get("priority", "")).strip() or "unknown",
            short_description=str(payload.get("shortDescription", "")).strip(),
            description=str(payload.get("description", "")).strip(),
            caller_notes=str(payload.get("callerNotes", "")).strip(),
            opened_at=str(payload.get("openedAt", "")).strip(),
            affected_systems=affected_systems,
            impact=_impact_from_dict(payload.get("impact", {})),
            timeline=timeline_entries,
            evidence=evidence_items,
        )


@dataclass(frozen=True)
class TriagePack:
    incident: Incident
    impact_summary: str
    hypotheses: tuple[str, ...] = field(default_factory=tuple)
    next_actions: tuple[str, ...] = field(default_factory=tuple)
    required_evidence: tuple[str, ...] = field(default_factory=tuple)


def _evidence_from_dict(index: int, item: dict[str, Any]) -> Evidence:
    supports = tuple(
        str(value).strip()
        for value in item.get("supports", [])
        if str(value).strip()
    )
    return Evidence(
        evidence_id=str(
            item.get("id") or item.get("evidenceId") or f"EV-{index:03d}"
        ).strip(),
        source=str(item.get("source", "")).strip() or "unknown",
        reference=str(item.get("reference", "")).strip() or "n/a",
        summary=str(item.get("summary", "")).strip() or "No summary provided.",
        evidence_type=str(
            item.get("type") or item.get("evidenceType") or "unknown"
        ).strip().lower(),
        strength=str(item.get("strength", "")).strip().lower() or "unknown",
        confidence=str(item.get("confidence", "")).strip().lower() or "unverified",
        supports=supports,
        observed_at=str(item.get("observedAt", "")).strip(),
        validation_pattern=str(item.get("validationPattern", "")).strip().lower(),
    )


def _timeline_entry_from_dict(item: dict[str, Any]) -> TimelineEntry:
    occurred_at = str(
        item.get("occurredAt") or item.get("eventAt") or item.get("timestamp") or ""
    ).strip()
    return TimelineEntry(
        occurred_at=occurred_at,
        summary=str(item.get("summary", "")).strip() or "No summary provided.",
        evidence_id=str(item.get("evidenceId", "")).strip(),
    )


def _impact_from_dict(value: Any) -> Impact:
    if not isinstance(value, dict):
        return Impact()
    affected_users = value.get("affectedUsersEstimate")
    if affected_users is not None:
        try:
            affected_users = int(affected_users)
        except (TypeError, ValueError):
            affected_users = None
    evidence_ids = tuple(
        str(item).strip()
        for item in value.get("evidenceIds", [])
        if str(item).strip()
    )
    return Impact(
        scope=str(value.get("scope", "unknown")).strip().lower() or "unknown",
        depth=str(value.get("depth", "unknown")).strip().lower() or "unknown",
        affected_users_estimate=affected_users,
        evidence_ids=evidence_ids,
    )
