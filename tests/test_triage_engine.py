import unittest

from app.reporting import render_markdown
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


if __name__ == "__main__":
    unittest.main()
