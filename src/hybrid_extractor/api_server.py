from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from pydantic import ValidationError

from .controllers import ExtractionController
from .web_ui import build_web_ui_html


class ApiHandler(BaseHTTPRequestHandler):
    controller = ExtractionController()

    def do_GET(self) -> None:
        route = self._route_path()

        if route == "/":
            self._send_html(200, build_web_ui_html())
            return
        if route == "/health":
            self._send_json(200, {"status": "ok"})
            return
        if route == "/templates":
            self._send_json(200, self.controller.list_templates())
            return
        if route.startswith("/templates/"):
            template_id = route.removeprefix("/templates/")
            self._send_json(200, self.controller.get_template(template_id))
            return
        if route == "/template-candidates":
            self._send_json(200, self.controller.list_template_candidates())
            return
        if route.startswith("/template-candidates/"):
            candidate_id = route.removeprefix("/template-candidates/")
            self._send_json(200, self.controller.get_template_candidate(candidate_id))
            return
        self._send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        route = self._route_path()

        if route == "/extract":
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
            return

        if route.endswith("/promote") and route.startswith("/template-candidates/"):
            candidate_id = route.removeprefix("/template-candidates/").removesuffix("/promote")
            self._handle_candidate_promotion(candidate_id)
            return

        if route == "/templates/delete-batch":
            self._handle_template_batch_delete()
            return

        if route.endswith("/status") and route.startswith("/templates/"):
            template_id = route.removeprefix("/templates/").removesuffix("/status")
            self._handle_template_status_update(template_id)
            return

        if route.endswith("/activate") and route.startswith("/templates/"):
            template_id = route.removeprefix("/templates/").removesuffix("/activate")
            self._handle_template_toggle(template_id, True)
            return

        if route.endswith("/deactivate") and route.startswith("/templates/"):
            template_id = route.removeprefix("/templates/").removesuffix("/deactivate")
            self._handle_template_toggle(template_id, False)
            return

        self._send_json(404, {"error": "Not found"})

    def do_DELETE(self) -> None:
        route = self._route_path()

        if route.startswith("/templates/"):
            template_id = route.removeprefix("/templates/")
            self._handle_template_delete(template_id)
            return

        if route.startswith("/template-candidates/"):
            candidate_id = route.removeprefix("/template-candidates/")
            self._handle_candidate_delete(candidate_id)
            return

        self._send_json(404, {"error": "Not found"})

    def log_message(self, format: str, *args) -> None:
        return

    def _read_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(content_length).decode("utf-8") if content_length else "{}"
        payload = json.loads(body)
        if not isinstance(payload, dict):
            raise ValueError("Request body must be a JSON object.")
        return payload

    def _route_path(self) -> str:
        return urlparse(self.path).path

    def _handle_template_toggle(self, template_id: str, active: bool) -> None:
        try:
            response = self.controller.set_template_active(template_id, active)
            self._send_json(200, response)
        except ValueError as exc:
            self._send_json(404, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def _handle_candidate_promotion(self, candidate_id: str) -> None:
        try:
            payload = self._read_json_body()
            response = self.controller.promote_template_candidate(candidate_id, payload)
            self._send_json(200, response)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def _handle_template_status_update(self, template_id: str) -> None:
        try:
            payload = self._read_json_body()
            lifecycle_status = payload.get("lifecycle_status")
            if not isinstance(lifecycle_status, str):
                raise ValueError("lifecycle_status must be a string.")
            response = self.controller.set_template_status(template_id, lifecycle_status)
            self._send_json(200, response)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def _handle_template_delete(self, template_id: str) -> None:
        try:
            response = self.controller.delete_template(template_id)
            self._send_json(200, response)
        except ValueError as exc:
            self._send_json(404, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def _handle_template_batch_delete(self) -> None:
        try:
            payload = self._read_json_body()
            response = self.controller.delete_templates(payload)
            self._send_json(200, response)
        except json.JSONDecodeError:
            self._send_json(400, {"error": "Invalid JSON body"})
        except ValueError as exc:
            self._send_json(400, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

    def _handle_candidate_delete(self, candidate_id: str) -> None:
        try:
            response = self.controller.delete_template_candidate(candidate_id)
            self._send_json(200, response)
        except ValueError as exc:
            self._send_json(404, {"error": str(exc)})
        except Exception as exc:
            self._send_json(500, {"error": "Internal server error", "details": str(exc)})

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
