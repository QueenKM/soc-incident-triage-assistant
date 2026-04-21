from __future__ import annotations

import json
from pathlib import Path

from .models import Alert, TriageReport


SEVERITY_BASE = {"low": 20, "medium": 45, "high": 72, "critical": 88}
TACTIC_BONUS = {
    "credential access": 8,
    "persistence": 8,
    "privilege escalation": 12,
    "defense evasion": 10,
    "exfiltration": 12,
    "initial access": 6,
}


def load_sample_alerts() -> list[Alert]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "sample_alerts.json"
    payload = json.loads(data_path.read_text())
    return [Alert.from_dict(item) for item in payload]


def find_alert(alert_id: str) -> Alert | None:
    for alert in load_sample_alerts():
        if alert.id == alert_id:
            return alert
    return None


def triage_alert(alert: Alert) -> TriageReport:
    score = SEVERITY_BASE.get(alert.severity.lower(), 40)
    for tactic in alert.tactics:
        score += TACTIC_BONUS.get(tactic.lower(), 0)
    score += min(alert.event_count, 10)
    score += min(len(alert.evidence) * 2, 10)
    if "identity" in alert.tags:
        score += 5
    if "external-ip" in alert.tags:
        score += 4

    if score >= 95:
        risk_level = "critical"
    elif score >= 75:
        risk_level = "high"
    elif score >= 50:
        risk_level = "medium"
    else:
        risk_level = "low"

    confidence = min(0.98, 0.56 + (0.05 * len(alert.evidence)) + (0.02 * min(alert.event_count, 8)))
    confidence = round(confidence, 2)

    executive_summary = (
        f"{alert.provider} raised a {risk_level} confidence {alert.category.lower()} alert affecting "
        f"{alert.affected_identity} on {alert.affected_asset}. The current signal suggests "
        f"{_category_narrative(alert)}"
    )

    attack_story = [
        f"Signal source: {alert.provider} detected {alert.title.lower()}.",
        f"Primary blast radius is {alert.affected_identity} on {alert.affected_asset}.",
        f"Tactics observed: {', '.join(alert.tactics) or 'not classified yet'}.",
        f"Evidence count is {alert.event_count}, with notable indicators: {', '.join(alert.evidence[:3])}.",
    ]

    recommended_actions = _recommended_actions(alert)
    containment_steps = _containment_steps(alert)
    suggested_kql = _suggested_kql(alert)

    return TriageReport(
        alert_id=alert.id,
        risk_level=risk_level,
        confidence=confidence,
        executive_summary=executive_summary,
        attack_story=attack_story,
        recommended_actions=recommended_actions,
        containment_steps=containment_steps,
        suggested_kql=suggested_kql,
    )


def _category_narrative(alert: Alert) -> str:
    category = alert.category.lower()
    if "impossible travel" in category:
        return "a potentially compromised identity or token replay from geographically inconsistent sign-ins."
    if "inbox rule" in category:
        return "post-compromise persistence designed to hide or reroute sensitive email activity."
    if "app consent" in category:
        return "a risky cloud identity grant that could expose tenant data to a malicious application."
    return alert.summary.lower()


def _recommended_actions(alert: Alert) -> list[str]:
    actions = [
        "Validate whether the affected identity has an active incident or recent high-risk sign-ins.",
        "Review sign-in, audit, and endpoint context before closing as benign.",
    ]

    category = alert.category.lower()
    if "impossible travel" in category:
        actions.extend(
            [
                "Check recent sign-ins for token reuse, unfamiliar MFA prompts, and impossible ASN / country hops.",
                "Compare user agent and device details against known managed devices.",
            ]
        )
    if "inbox rule" in category:
        actions.extend(
            [
                "Review Exchange audit logs for recently created forwarding or hide-delete rules.",
                "Check whether suspicious OAuth grants or mailbox delegates were added around the same time.",
            ]
        )
    if "app consent" in category:
        actions.extend(
            [
                "Review the granted API permissions and whether admin consent was abused.",
                "Inspect service principal activity and confirm whether the app publisher is trusted.",
            ]
        )

    return actions


def _containment_steps(alert: Alert) -> list[str]:
    steps = []
    if alert.affected_identity:
        steps.append(f"Reset credentials and revoke active refresh tokens for {alert.affected_identity}.")
    if "app consent" in alert.category.lower():
        steps.append("Disable or remove the suspicious enterprise application pending validation.")
    else:
        steps.append(f"Place {alert.affected_asset} under heightened monitoring or isolate if additional evidence appears.")
    steps.append("Document analyst decision, evidence reviewed, and user communication status.")
    return steps


def _suggested_kql(alert: Alert) -> list[str]:
    identity = alert.affected_identity
    ip = alert.source_ip or "<source-ip>"
    return [
        f"SigninLogs | where UserPrincipalName =~ '{identity}' | sort by TimeGenerated desc | take 25",
        f"SecurityAlert | where Entities has '{identity}' or CompromisedEntity =~ '{identity}'",
        f"CloudAppEvents | where IPAddress == '{ip}' | sort by TimeGenerated desc | take 25",
    ]
