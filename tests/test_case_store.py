from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.case_store import get_case_record, load_case_records, update_case_record


class CaseStoreTests(unittest.TestCase):
    def test_missing_store_returns_default_case(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "case_history.json"
            record = get_case_record("alert-999", store_path=path)
            self.assertEqual(record.status, "new")
            self.assertEqual(record.owner, "Unassigned")
            self.assertEqual(len(record.history), 1)

    def test_update_case_record_persists_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "case_history.json"
            updated = update_case_record(
                alert_id="alert-123",
                status="in_progress",
                owner="Kristina Mateva",
                decision_notes="Validated token abuse indicators.",
                actor="Kristina Mateva",
                store_path=path,
            )

            loaded = load_case_records(store_path=path)["alert-123"]
            self.assertEqual(updated.status, "in_progress")
            self.assertEqual(loaded.owner, "Kristina Mateva")
            self.assertEqual(loaded.decision_notes, "Validated token abuse indicators.")
            self.assertGreaterEqual(len(loaded.history), 2)


if __name__ == "__main__":
    unittest.main()
