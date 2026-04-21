from __future__ import annotations

import json
from urllib.parse import parse_qs, urlparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .case_store import get_case_record, load_case_records, summarize_queue, update_case_record
from .models import Alert
from .reporting import render_json, render_markdown
from .triage_engine import find_alert, load_sample_alerts, triage_alert

HOST = "127.0.0.1"
PORT = 8090
WEB_ROOT = Path(__file__).resolve().parent.parent / "web"


class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if route in {"/", "/index.html"}:
            self._serve_file("index.html", "text/html; charset=utf-8")
            return
        if route == "/styles.css":
            self._serve_file("styles.css", "text/css; charset=utf-8")
            return
        if route == "/api/health":
            self._json({"status": "ok", "service": "soc-incident-triage-assistant"})
            return
        if route == "/api/alerts":
            alerts = load_sample_alerts()
            case_lookup = {alert.id: get_case_record(alert.id).to_dict() for alert in alerts}
            self._json(
                {
                    "alerts": [
                        {**alert.to_dict(), "case": case_lookup[alert.id]}
                        for alert in alerts
                    ],
                    "summary": summarize_queue(load_case_records()),
                }
            )
            return
        if route == "/api/case":
            alert_id = query.get("id", [None])[0]
            if not alert_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing alert id")
                return
            alert = find_alert(alert_id)
            if alert is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Alert id not found")
                return
            self._json({"case": get_case_record(alert.id).to_dict()})
            return
        if route == "/api/export":
            alert_id = query.get("id", [None])[0]
            format_name = query.get("format", ["markdown"])[0]
            if not alert_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing alert id")
                return
            alert = find_alert(alert_id)
            if alert is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Alert id not found")
                return

            report = triage_alert(alert)
            case = get_case_record(alert.id)
            if format_name == "json":
                body = render_json(alert, report, case=case).encode("utf-8")
                self._raw(
                    body,
                    "application/json; charset=utf-8",
                    f'attachment; filename="{alert.id}-incident-report.json"',
                )
                return

            body = render_markdown(alert, report, case=case).encode("utf-8")
            self._raw(
                body,
                "text/markdown; charset=utf-8",
                f'attachment; filename="{alert.id}-incident-report.md"',
            )
            return

        self.send_error(HTTPStatus.NOT_FOUND, "Not found")

    def do_POST(self) -> None:
        if self.path == "/api/case":
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_payload = self.rfile.read(content_length or 0)
            payload = json.loads(raw_payload or b"{}")

            alert_id = payload.get("id")
            if not alert_id:
                self.send_error(HTTPStatus.BAD_REQUEST, "Missing alert id")
                return

            alert = find_alert(alert_id)
            if alert is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Alert id not found")
                return

            record = update_case_record(
                alert_id=alert.id,
                status=payload.get("status", "new"),
                owner=payload.get("owner", ""),
                decision_notes=payload.get("decision_notes", ""),
                actor=payload.get("actor", "Analyst"),
            )
            self._json(
                {
                    "case": record.to_dict(),
                    "summary": summarize_queue(load_case_records()),
                }
            )
            return

        if self.path != "/api/triage":
            self.send_error(HTTPStatus.NOT_FOUND, "Not found")
            return

        content_length = int(self.headers.get("Content-Length", "0"))
        raw_payload = self.rfile.read(content_length or 0)
        payload = json.loads(raw_payload or b"{}")

        if "id" in payload:
            alert = find_alert(payload["id"])
            if alert is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Alert id not found")
                return
        else:
            alert = Alert.from_dict(payload)

        report = triage_alert(alert)
        self._json(
            {
                "alert": alert.to_dict(),
                "report": report.to_dict(),
                "case": get_case_record(alert.id).to_dict(),
            }
        )

    def log_message(self, format: str, *args: object) -> None:
        return

    def _serve_file(self, name: str, content_type: str) -> None:
        target = WEB_ROOT / name
        body = target.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._raw(body, "application/json; charset=utf-8")

    def _raw(self, body: bytes, content_type: str, content_disposition: str | None = None) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        if content_disposition:
            self.send_header("Content-Disposition", content_disposition)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run() -> None:
    server = ThreadingHTTPServer((HOST, PORT), RequestHandler)
    print(f"SOC Incident Triage Assistant running at http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    run()
