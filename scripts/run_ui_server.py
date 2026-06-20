import os

from hybrid_extractor.api_server import run_server


if __name__ == "__main__":
    host = os.environ.get("HYBRID_UI_HOST", "127.0.0.1")
    port = int(os.environ.get("HYBRID_UI_PORT", "8000"))
    run_server(host=host, port=port)
