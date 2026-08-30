from __future__ import annotations

from pathlib import Path
import pytest
import tpp


def test_public_run_source() -> None:
    source = (
        "let x be a + b\n"
        "let msg be \"Result: {x}\"\n"
    )
    engine = tpp.run_source(source, initial_scope={"a": 10, "b": 25})
    assert engine.global_scope.get("x", 1) == 35
    assert engine.global_scope.get("msg", 1) == "Result: 35"


def test_public_eval_expr() -> None:
    val = tpp.eval_expr("10 plus 25")
    assert val == 35

    scope_val = tpp.eval_expr("item's score times 2", scope={"item": {"score": 50}})
    assert scope_val == 100


def test_public_run_file(tmp_path: Path) -> None:
    script_file = tmp_path / "script.tpp"
    script_file.write_text(
        "let answer be 42\n",
        encoding="utf-8",
    )
    engine = tpp.run_file(script_file)
    assert engine.global_scope.get("answer", 1) == 42


def test_python_callback_interop() -> None:
    calls = []
    def custom_logger(msg: str) -> None:
        calls.append(msg)

    source = (
        "let log_res be call logger with \"Event logged from T++\"\n"
    )
    engine = tpp.run_source(source, initial_scope={"logger": custom_logger})
    assert calls == ["Event logged from T++"]
