import unittest

from app.case_store import load_case_records, summarize_queue
from app.reporting import render_json, render_markdown
from app.triage_engine import load_sample_alerts, triage_alert


class TriageEngineTests(unittest.TestCase):
    def test_loads_sample_alerts(self) -> None:
        alerts = load_sample_alerts()
        self.assertGreaterEqual(len(alerts), 3)

    def test_critical_alert_produces_high_risk_report(self) -> None:
        alert = next(item for item in load_sample_alerts() if item.id == "alert-003")
        report = triage_alert(alert)
        self.assertIn(report.risk_level, {"high", "critical"})
        self.assertGreaterEqual(report.confidence, 0.6)
        self.assertTrue(report.recommended_actions)
        self.assertTrue(report.suggested_kql)

    def test_markdown_export_contains_alert_title(self) -> None:
        alert = next(item for item in load_sample_alerts() if item.id == "alert-001")
        report = triage_alert(alert)
        markdown = render_markdown(alert, report)
        self.assertIn(alert.title, markdown)
        self.assertIn("Suggested KQL", markdown)

    def test_seeded_case_history_summary_matches_sample_queue(self) -> None:
        records = load_case_records()
        summary = summarize_queue(records)
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["in_progress"], 1)
        self.assertEqual(summary["escalated"], 1)
        self.assertEqual(summary["owned"], 2)

    def test_json_export_can_include_case_context(self) -> None:
        alert = next(item for item in load_sample_alerts() if item.id == "alert-003")
        report = triage_alert(alert)
        case = load_case_records()[alert.id]
        exported = render_json(alert, report, case=case)
        self.assertIn('"case"', exported)
        self.assertIn(case.owner, exported)


if __name__ == "__main__":
    unittest.main()
