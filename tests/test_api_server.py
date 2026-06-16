import json
import threading
import urllib.error
import urllib.request

from hybrid_extractor.api_server import ApiHandler, ThreadingHTTPServer


def test_api_server_health_and_validation_responses():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ApiHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with urllib.request.urlopen(f"{base_url}/health") as response:
            payload = json.loads(response.read().decode("utf-8"))
            assert payload["status"] == "ok"

        with urllib.request.urlopen(f"{base_url}/") as response:
            html = response.read().decode("utf-8")
            assert "混合网页解析器" in html

        request = urllib.request.Request(
            f"{base_url}/extract",
            data=b'{"bad_json"',
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request)
        except urllib.error.HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            assert exc.code == 400
            assert payload["error"] == "Invalid JSON body"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
