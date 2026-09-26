from __future__ import annotations

import json
import socketserver
import urllib.parse
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from importlib.resources import files
from typing import Any

from tpp.api.json_api import (
    check_code_response,
    execute_json_request,
    format_code_response,
    get_ast_response,
    get_examples_catalog,
    get_stdlib_catalog,
)


@dataclass
class ApiServerConfig:
    host: str = "127.0.0.1"
    port: int = 8787


class ThreadingHttpServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True
    daemon_threads = True


class TppApiHandler(BaseHTTPRequestHandler):
    server_version = "TppApiServer/2.0"

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:
        self.send_response(HTTPStatus.NO_CONTENT)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_GET(self) -> None:
        raw_path = urllib.parse.urlparse(self.path).path
        clean_path = raw_path.rstrip("/")
        if not clean_path:
            clean_path = "/"

        if clean_path in {"/", "/index.html"}:
            try:
                html = files("tpp.api.webide").joinpath("index.html").read_text(encoding="utf-8")
                self._send_html(html)
            except Exception as exc:
                self._send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"ok": False, "error": f"Failed reading Web IDE: {exc}"})
            return

        if clean_path == "/manifest":
            self._send_json(
                HTTPStatus.OK,
                {
                    "name": "T++ API",
                    "version": "2.0",
                    "endpoints": [
                        "POST /run",
                        "POST /ast",
                        "POST /check",
                        "POST /fmt",
                        "GET /examples",
                        "GET /stdlib",
                        "GET /manifest",
                    ],
                },
            )
            return

        if clean_path == "/examples":
            self._send_json(HTTPStatus.OK, get_examples_catalog())
            return

        if clean_path == "/stdlib":
            self._send_json(HTTPStatus.OK, get_stdlib_catalog())
            return

        self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"Endpoint '{self.path}' not found"})

    def do_POST(self) -> None:
        raw_path = urllib.parse.urlparse(self.path).path
        clean_path = raw_path.rstrip("/")
        if not clean_path:
            clean_path = "/"

        valid_endpoints = {"/run", "/ast", "/check", "/fmt"}
        if clean_path not in valid_endpoints:
            self._send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": f"POST endpoint '{self.path}' not found"})
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                raise ValueError("Payload must be a JSON object")
        except Exception as exc:
            self._send_json(HTTPStatus.BAD_REQUEST, {"ok": False, "error": f"Invalid JSON payload: {exc}"})
            return

        if clean_path == "/run":
            result = execute_json_request(payload)
            status = HTTPStatus.OK if result.get("ok", False) else HTTPStatus.BAD_REQUEST
            self._send_json(status, result)
        elif clean_path == "/ast":
            result = get_ast_response(payload)
            status = HTTPStatus.OK if result.get("ok", False) else HTTPStatus.BAD_REQUEST
            self._send_json(status, result)
        elif clean_path == "/check":
            result = check_code_response(payload)
            self._send_json(HTTPStatus.OK, result)
        elif clean_path == "/fmt":
            result = format_code_response(payload)
            status = HTTPStatus.OK if result.get("ok", False) else HTTPStatus.BAD_REQUEST
            self._send_json(status, result)

    def log_message(self, format: str, *args: Any) -> None:
        # Quiet default server logging for cleaner CLI output.
        return


def serve_api(config: ApiServerConfig) -> None:
    with ThreadingHttpServer((config.host, config.port), TppApiHandler) as httpd:
        print(f"T++ API server running at http://{config.host}:{config.port}")
        print(f"  Web IDE:      http://{config.host}:{config.port}/")
        print("  POST /run:    Execute T++ code")
        print("  POST /ast:    Parse source into AST JSON")
        print("  POST /check:  Syntax & type diagnostics")
        print("  POST /fmt:    Code formatter")
        print("  GET /examples: Curated catalog of T++ examples")
        print("  GET /stdlib:  Standard library modules and functions")
        print("  GET /manifest: API endpoints manifest")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopping T++ API server")
