from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path

from .models import CaseRecord, CaseTimelineEvent


DEFAULT_STORE_PATH = Path(__file__).resolve().parent.parent / "data" / "case_history.json"
DEFAULT_STATUS = "new"
DEFAULT_OWNER = "Unassigned"
DEFAULT_NOTES = "Pending analyst review."
STORE_LOCK = threading.RLock()


def load_case_records(store_path: Path | None = None) -> dict[str, CaseRecord]:
    path = store_path or DEFAULT_STORE_PATH
    with STORE_LOCK:
        return _load_case_records_unlocked(path)


def get_case_record(alert_id: str, store_path: Path | None = None) -> CaseRecord:
    records = load_case_records(store_path=store_path)
    return records.get(alert_id, _default_case_record(alert_id))


def update_case_record(
    alert_id: str,
    status: str,
    owner: str,
    decision_notes: str,
    actor: str = "Analyst",
    store_path: Path | None = None,
) -> CaseRecord:
    path = store_path or DEFAULT_STORE_PATH
    with STORE_LOCK:
        records = _load_case_records_unlocked(path)
        existing = records.get(alert_id, _default_case_record(alert_id))

        next_status = (status or existing.status).strip().lower()
        next_owner = (owner or existing.owner).strip() or DEFAULT_OWNER
        next_notes = decision_notes.strip() or DEFAULT_NOTES
        next_timestamp = _timestamp_now()

        changes: list[str] = []
        if next_status != existing.status:
            changes.append(f"Status changed to {next_status.replace('_', ' ')}")
        if next_owner != existing.owner:
            changes.append(f"Owner changed to {next_owner}")
        if next_notes != existing.decision_notes:
            changes.append("Analyst notes updated")

        next_history = list(existing.history)
        next_history.append(
            CaseTimelineEvent(
                timestamp=next_timestamp,
                actor=actor,
                action="Case updated" if changes else "Case reviewed",
                detail="; ".join(changes) if changes else "Reviewed with no field changes.",
                status=next_status,
            )
        )

        record = CaseRecord(
            alert_id=alert_id,
            status=next_status,
            owner=next_owner,
            decision_notes=next_notes,
            last_updated=next_timestamp,
            history=next_history,
        )
        records[alert_id] = record
        _persist_case_records_unlocked(records, path)
        return record


def summarize_queue(records: dict[str, CaseRecord]) -> dict[str, int]:
    summary = {
        "total": len(records),
        "new": 0,
        "in_progress": 0,
        "escalated": 0,
        "closed": 0,
        "owned": 0,
    }

    for record in records.values():
        if record.status in summary:
            summary[record.status] += 1
        if record.owner != DEFAULT_OWNER:
            summary["owned"] += 1

    return summary


def _load_case_records_unlocked(path: Path) -> dict[str, CaseRecord]:
    if not path.exists():
        return {}

    payload = json.loads(path.read_text())
    return {
        item["alert_id"]: CaseRecord.from_dict(item)
        for item in payload.get("cases", [])
    }


def _persist_case_records_unlocked(records: dict[str, CaseRecord], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "cases": [records[alert_id].to_dict() for alert_id in sorted(records)],
    }
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, indent=2) + "\n")
    temp_path.replace(path)


def _default_case_record(alert_id: str) -> CaseRecord:
    return CaseRecord(
        alert_id=alert_id,
        status=DEFAULT_STATUS,
        owner=DEFAULT_OWNER,
        decision_notes=DEFAULT_NOTES,
        last_updated="Not updated yet",
        history=[
            CaseTimelineEvent(
                timestamp="Queue seed",
                actor="System",
                action="Alert queued",
                detail="Alert entered the analyst queue and is waiting for first review.",
                status=DEFAULT_STATUS,
            )
        ],
    )


def _timestamp_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
