"""Webhook server for triggering the newsletter pipeline from n8n.

Exposes a single endpoint:
    POST http://localhost:8080/run  →  triggers main.py pipeline

Start this server before activating the n8n workflow:
    python server.py
"""

import logging
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

from main import main

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
log = logging.getLogger(__name__)

PORT = 8080


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        if self.path != "/run":
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'{"error": "not found"}')
            return

        log.info("Webhook triggered — starting newsletter pipeline")
        exit_code = main()

        if exit_code == 0:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'{"status": "success"}')
        else:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b'{"status": "error", "message": "pipeline failed - check logs"}')

    def log_message(self, format: str, *args: object) -> None:
        pass  # suppress default HTTP access logs (we use our own)


if __name__ == "__main__":
    server = HTTPServer(("localhost", PORT), WebhookHandler)
    log.info("Webhook server listening on http://localhost:%d/run", PORT)
    log.info("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        log.info("Server stopped.")
