import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.case_store import get_case_record, update_case_record
from app.reporting import render_json, render_markdown
from app.triage_engine import load_sample_alerts, triage_alert


class CaseHandoffTest(unittest.TestCase):
    def test_case_update_is_included_in_both_exports(self):
        alert = load_sample_alerts()[0]
        report = triage_alert(alert)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "cases.json"
            with patch("app.case_store.DEFAULT_STORE_PATH", path):
                update_case_record(
                    alert.id, "escalated", "Second analyst", "Review the evidence", actor="First analyst"
                )
                case = get_case_record(alert.id)

        json_export = render_json(alert, report, case=case)
        markdown_export = render_markdown(alert, report, case=case)
        json.loads(json_export)
        for exported in (json_export, markdown_export):
            with self.subTest(format=exported[:20]):
                self.assertIn("Second analyst", exported)
                self.assertIn("Review the evidence", exported)
                self.assertIn("First analyst", exported)
                self.assertIn("escalated", exported.lower())
