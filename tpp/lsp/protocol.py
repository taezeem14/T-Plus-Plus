from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any, Optional


@dataclass
class Position:
    line: int  # 0-based
    character: int  # 0-based


@dataclass
class Range:
    start: Position
    end: Position


@dataclass
class Location:
    uri: str
    range: Range


@dataclass
class TextEdit:
    range: Range
    newText: str


@dataclass
class LspDiagnostic:
    range: Range
    message: str
    severity: int = 1  # 1: Error, 2: Warning, 3: Info, 4: Hint
    source: str = "tpp"


@dataclass
class CompletionItem:
    label: str
    kind: int = 1  # 1: Text, 2: Method, 3: Function, 6: Variable, 14: Keyword
    detail: Optional[str] = None
    documentation: Optional[str] = None
    insertText: Optional[str] = None


@dataclass
class Hover:
    contents: str | dict[str, Any]
    range: Optional[Range] = None


def format_json_rpc_response(request_id: Any, result: Any = None, error: Any = None) -> bytes:
    payload: dict[str, Any] = {"jsonrpc": "2.0", "id": request_id}
    if error is not None:
        payload["error"] = error
    else:
        payload["result"] = result
    encoded = json.dumps(payload, default=lambda o: asdict(o) if hasattr(o, "__dict__") or hasattr(o, "__dataclass_fields__") else str(o)).encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
    return header + encoded


def format_json_rpc_notification(method: str, params: Any) -> bytes:
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
    }
    encoded = json.dumps(payload, default=lambda o: asdict(o) if hasattr(o, "__dict__") or hasattr(o, "__dataclass_fields__") else str(o)).encode("utf-8")
    header = f"Content-Length: {len(encoded)}\r\n\r\n".encode("ascii")
    return header + encoded
