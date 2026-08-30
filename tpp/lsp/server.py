from __future__ import annotations

import json
import socketserver
import sys
from typing import Any, BinaryIO, Optional

from tpp.core.constants import VERSION
from tpp.lsp.handlers import LspHandler
from tpp.lsp.protocol import (
    Position,
    format_json_rpc_notification,
    format_json_rpc_response,
)


class LspServer:
    def __init__(self, reader: BinaryIO, writer: BinaryIO) -> None:
        self.reader = reader
        self.writer = writer
        self.handler = LspHandler()
        self.is_running = True

    def run(self) -> None:
        while self.is_running:
            message = self._read_message()
            if message is None:
                break
            self._dispatch_message(message)

    def _read_message(self) -> Optional[dict[str, Any]]:
        # Read headers
        content_length = 0
        while True:
            line_bytes = self.reader.readline()
            if not line_bytes:
                return None
            line = line_bytes.decode("latin1").strip()
            if not line:
                break
            if line.lower().startswith("content-length:"):
                try:
                    content_length = int(line.split(":")[1].strip())
                except ValueError:
                    pass

        if content_length <= 0:
            return None

        body_bytes = self.reader.read(content_length)
        if len(body_bytes) < content_length:
            return None

        try:
            return json.loads(body_bytes.decode("utf-8"))
        except Exception:
            return None

    def _send(self, data: bytes) -> None:
        self.writer.write(data)
        self.writer.flush()

    def _dispatch_message(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        msg_id = msg.get("id")
        params = msg.get("params", {})

        if method == "initialize":
            result = {
                "capabilities": {
                    "textDocumentSync": 1,  # Full
                    "hoverProvider": True,
                    "completionProvider": {
                        "resolveProvider": False,
                        "triggerCharacters": [" ", ".", ":"],
                    },
                    "definitionProvider": True,
                    "documentFormattingProvider": True,
                },
                "serverInfo": {
                    "name": "tpp-language-server",
                    "version": VERSION,
                },
            }
            self._send(format_json_rpc_response(msg_id, result=result))
            return

        if method == "shutdown":
            self._send(format_json_rpc_response(msg_id, result=None))
            return

        if method == "exit":
            self.is_running = False
            return

        if method == "textDocument/didOpen":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            text = doc.get("text", "")
            diags = self.handler.update_document(uri, text)
            self._send(format_json_rpc_notification("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": diags}))
            return

        if method == "textDocument/didChange":
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "")
            changes = params.get("contentChanges", [])
            if changes:
                text = changes[-1].get("text", "")
                diags = self.handler.update_document(uri, text)
                self._send(format_json_rpc_notification("textDocument/publishDiagnostics", {"uri": uri, "diagnostics": diags}))
            return

        if method == "textDocument/hover":
            uri = params.get("textDocument", {}).get("uri", "")
            pos_dict = params.get("position", {})
            pos = Position(line=pos_dict.get("line", 0), character=pos_dict.get("character", 0))
            hover = self.handler.get_hover(uri, pos)
            self._send(format_json_rpc_response(msg_id, result=hover))
            return

        if method == "textDocument/completion":
            uri = params.get("textDocument", {}).get("uri", "")
            pos_dict = params.get("position", {})
            pos = Position(line=pos_dict.get("line", 0), character=pos_dict.get("character", 0))
            completions = self.handler.get_completions(uri, pos)
            self._send(format_json_rpc_response(msg_id, result={"isIncomplete": False, "items": completions}))
            return

        if method == "textDocument/definition":
            uri = params.get("textDocument", {}).get("uri", "")
            pos_dict = params.get("position", {})
            pos = Position(line=pos_dict.get("line", 0), character=pos_dict.get("character", 0))
            location = self.handler.get_definition(uri, pos)
            self._send(format_json_rpc_response(msg_id, result=location))
            return

        if method == "textDocument/formatting":
            uri = params.get("textDocument", {}).get("uri", "")
            edits = self.handler.get_formatting(uri)
            self._send(format_json_rpc_response(msg_id, result=edits))
            return

        # Default fallback for unhandled requests
        if msg_id is not None:
            self._send(format_json_rpc_response(msg_id, result=None))


def run_lsp_server(stdio: bool = True, port: Optional[int] = None) -> int:
    if port:
        class LSPTCPHandler(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                server = LspServer(self.rfile, self.wfile)
                server.run()

        with socketserver.TCPServer(("127.0.0.1", port), LSPTCPHandler) as tcp_server:
            tcp_server.serve_forever()
        return 0

    server = LspServer(sys.stdin.buffer, sys.stdout.buffer)
    server.run()
    return 0
