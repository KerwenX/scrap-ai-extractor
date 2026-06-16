from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from pydantic import ValidationError

from .controllers import ExtractionController
from .web_ui import build_web_ui_html


class ApiHandler(BaseHTTPRequestHandler):
    controller = ExtractionController()

    def do_GET(self) -> None:
        if self.path == "/":
            self._send_html(200, build_web_ui_html())
            return
        if self.path == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if self.path == "/templates":
            self._send_json(200, self.controller.list_templates())
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if self.path != "/extract":
            self._send_json(404, {"error": "Not found"})
            return

        try:
            payload = self._read_json_body()
            response = self.controller.extract(payload)
            self._send_json(200, response)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except ValidationError as exc:
            self._send_json(422, {"error": "Invalid request payload", "details": exc.errors()})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _send_html(self, status: int, body: str) -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), ApiHandler)
    print(f"Hybrid extractor API listening on http://{host}:{port}")
    server.serve_forever()
