from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Alert:
    id: str
    title: str
    severity: str
    provider: str
    category: str
    tactics: list[str]
    affected_identity: str
    affected_asset: str
    summary: str
    event_count: int
    source_ip: str | None = None
    location: str | None = None
    evidence: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Alert":
        return cls(
            id=payload["id"],
            title=payload["title"],
            severity=payload["severity"],
            provider=payload["provider"],
            category=payload["category"],
            tactics=list(payload.get("tactics", [])),
            affected_identity=payload["affected_identity"],
            affected_asset=payload["affected_asset"],
            summary=payload["summary"],
            event_count=int(payload.get("event_count", 0)),
            source_ip=payload.get("source_ip"),
            location=payload.get("location"),
            evidence=list(payload.get("evidence", [])),
            tags=list(payload.get("tags", [])),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TriageReport:
    alert_id: str
    risk_level: str
    confidence: float
    executive_summary: str
    attack_story: list[str]
    recommended_actions: list[str]
    containment_steps: list[str]
    suggested_kql: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
