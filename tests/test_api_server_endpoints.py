from __future__ import annotations

import json
import threading
import urllib.request
from http import HTTPStatus
from typing import Any
import pytest

from tpp.api.json_api import (
    check_code_response,
    execute_json_request,
    format_code_response,
    get_ast_response,
    get_examples_catalog,
    get_stdlib_catalog,
)
from tpp.api.server import ApiServerConfig, ThreadingHttpServer, TppApiHandler


def test_api_ast_endpoint() -> None:
    source = "let x be 42\nsay x"
    res = get_ast_response({"source": source})
    assert res["ok"] is True
    assert "ast" in res
    assert res["ast"]["node_type"] == "Program"
    assert len(res["ast"]["statements"]) == 2
    assert res["ast"]["statements"][0]["node_type"] == "LetStmt"
    assert res["ast"]["statements"][0]["name"] == "x"


def test_api_check_valid_code() -> None:
    source = "let count be 10\nincrease count by 5\nsay count"
    res = check_code_response({"source": source})
    assert res["ok"] is True
    assert len(res["diagnostics"]) == 0
    assert "count" in res["inferred_types"]


def test_api_check_invalid_syntax() -> None:
    source = "let x be\n"
    res = check_code_response({"source": source})
    assert res["ok"] is False
    assert len(res["diagnostics"]) > 0
    diag = res["diagnostics"][0]
    assert "line" in diag
    assert "column" in diag
    assert "message" in diag
    assert diag["severity"] == "error"


def test_api_fmt_endpoint() -> None:
    source = "let   x   be   5\n"
    res = format_code_response({"source": source})
    assert res["ok"] is True
    assert res["formatted"] == "let x be 5\n"


def test_api_examples_catalog() -> None:
    res = get_examples_catalog()
    assert res["ok"] is True
    assert res["count"] >= 8
    categories = set(res["categories"])
    expected_categories = {
        "Basics",
        "Control Flow",
        "Pattern Matching",
        "Collections & Comprehensions",
        "Algorithms",
        "Classes & OOP",
        "Error Handling",
        "System & Stdlib",
    }
    assert expected_categories.issubset(categories)


def test_api_stdlib_catalog() -> None:
    res = get_stdlib_catalog()
    assert res["ok"] is True
    assert res["count"] == 7
    module_names = [m["name"] for m in res["modules"]]
    assert set(module_names) == {"math", "text", "collections", "system", "time", "json", "validate"}
    for mod in res["modules"]:
        assert len(mod["members"]) > 0
        for m in mod["members"]:
            assert "name" in m
            assert "signature" in m
            assert "doc" in m


def test_api_run_variables_and_duration() -> None:
    source = "let num be 100\nlet msg be 'hello'\n"
    res = execute_json_request({"mode": "run", "source": source})
    assert res["ok"] is True
    assert "duration_ms" in res
    assert "variables" in res
    var_dict = {v["name"]: v for v in res["variables"]}
    assert "num" in var_dict
    assert var_dict["num"]["value"] == 100
    assert "msg" in var_dict
    assert var_dict["msg"]["value"] == "hello"


def test_http_server_endpoints() -> None:
    server = ThreadingHttpServer(("127.0.0.1", 0), TppApiHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    base_url = f"http://127.0.0.1:{port}"

    try:
        # GET /
        with urllib.request.urlopen(f"{base_url}/") as resp:
            assert resp.status == 200
            content = resp.read().decode("utf-8")
            assert "<!doctype html>" in content.lower()

        # GET /manifest
        with urllib.request.urlopen(f"{base_url}/manifest") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["name"] == "T++ API"
            assert "POST /ast" in data["endpoints"]
            assert "POST /check" in data["endpoints"]
            assert "POST /fmt" in data["endpoints"]
            assert "GET /examples" in data["endpoints"]
            assert "GET /stdlib" in data["endpoints"]

        # GET /examples
        with urllib.request.urlopen(f"{base_url}/examples") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert len(data["examples"]) >= 8

        # GET /stdlib
        with urllib.request.urlopen(f"{base_url}/stdlib") as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert len(data["modules"]) == 7

        # POST /run
        req = urllib.request.Request(
            f"{base_url}/run",
            data=json.dumps({"source": "let a be 5\nsay a"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert "5" in data["stdout"]
            assert "duration_ms" in data

        # POST /ast
        req = urllib.request.Request(
            f"{base_url}/ast",
            data=json.dumps({"source": "let a be 5"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert "ast" in data

        # POST /check
        req = urllib.request.Request(
            f"{base_url}/check",
            data=json.dumps({"source": "let a be 5"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert data["diagnostics"] == []

        # POST /fmt
        req = urllib.request.Request(
            f"{base_url}/fmt",
            data=json.dumps({"source": "let   val   be   10"}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req) as resp:
            assert resp.status == 200
            data = json.loads(resp.read().decode("utf-8"))
            assert data["ok"] is True
            assert data["formatted"] == "let val be 10\n"

    finally:
        server.shutdown()
        server.server_close()
