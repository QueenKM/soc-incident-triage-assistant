from __future__ import annotations

import json

from .models import Alert, TriageReport


def render_markdown(alert: Alert, report: TriageReport) -> str:
    return "\n".join(
        [
            f"# Incident Brief: {alert.title}",
            "",
            f"- Alert ID: `{alert.id}`",
            f"- Severity: **{alert.severity}**",
            f"- Provider: `{alert.provider}`",
            f"- Category: `{alert.category}`",
            f"- Risk Level: **{report.risk_level.upper()}**",
            f"- Confidence: `{report.confidence}`",
            f"- Identity: `{alert.affected_identity}`",
            f"- Asset: `{alert.affected_asset}`",
            "",
            "## Executive Summary",
            "",
            report.executive_summary,
            "",
            "## Evidence",
            "",
            *[f"- {item}" for item in alert.evidence],
            "",
            "## Attack Story",
            "",
            *[f"- {item}" for item in report.attack_story],
            "",
            "## Recommended Actions",
            "",
            *[f"- {item}" for item in report.recommended_actions],
            "",
            "## Containment Steps",
            "",
            *[f"- {item}" for item in report.containment_steps],
            "",
            "## Suggested KQL",
            "",
            "```kusto",
            *report.suggested_kql,
            "```",
        ]
    )


def render_json(alert: Alert, report: TriageReport) -> str:
    payload = {
        "alert": alert.to_dict(),
        "report": report.to_dict(),
    }
    return json.dumps(payload, indent=2)
