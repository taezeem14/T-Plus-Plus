from __future__ import annotations

import pytest

from tpp.core.errors import (
    Diagnostic,
    DiagnosticSeverity,
    ExecutionBudgetExceeded,
    IndexTppError,
    MathTppError,
    ModuleNotFoundTppError,
    SyntaxTppError,
    TppCallFrame,
    TppError,
    TypeTppError,
    format_diagnostic,
    render_error,
)
from tpp.parser import Parser, ParserConfig
from tpp.runtime import EngineConfig, RuntimeEngine


def test_diagnostic_rendering() -> None:
    diag = Diagnostic(
        message='I expected a number here, but "hello" is text.',
        severity=DiagnosticSeverity.ERROR,
        line=4,
        col=12,
        end_col=19,
        source_line='let x be 4 plus "hello"',
        file_path="main.tpp",
        suggestion='Did you mean to convert "hello" to a number first?',
        fix_preview="let x be 4 plus 10",
        call_stack=[TppCallFrame(function_name="calculate", line=4, col=12, file_path="main.tpp")],
    )
    rendered = diag.render(color=False)
    assert "ERROR: I expected a number here" in rendered
    assert "--> main.tpp:4:12" in rendered
    assert '4 | let x be 4 plus "hello"' in rendered
    assert "^^^^^^^" in rendered
    assert "Hint: Did you mean to convert" in rendered
    assert "Try:  let x be 4 plus 10" in rendered
    assert "at calculate (main.tpp:4:12)" in rendered


def test_exception_hierarchy() -> None:
    assert issubclass(TypeTppError, TppError)
    assert issubclass(MathTppError, TppError)
    assert issubclass(IndexTppError, TppError)
    assert issubclass(ModuleNotFoundTppError, TppError)
    assert issubclass(ExecutionBudgetExceeded, TppError)


def test_parser_multi_error_recovery() -> None:
    source = (
        "let a be \n"
        "let b be 10\n"
        "let c be \n"
    )
    parser = Parser(source, config=ParserConfig(collect_multiple_errors=True), file_path="sample.tpp")
    program = parser.parse()
    # Parser should have collected 2 errors instead of dying on the first
    assert len(parser.diagnostics) >= 2
    assert any("let" in d.message.lower() or "value" in d.message.lower() for d in parser.diagnostics)


def test_try_handle_math_error() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let caught be false\n"
        "try:\n"
        "    let x be 10 divided by 0\n"
        "handle MathTppError as e:\n"
        "    change caught to true\n"
        "finally:\n"
        "    let finished be true\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("caught", 1) is True
    assert engine.global_scope.get("finished", 1) is True


def test_try_handle_any_error() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let msg be \"\"\n"
        "try:\n"
        "    raise the error \"something went wrong\"\n"
        "handle any error as e:\n"
        "    change msg to \"caught\"\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("msg", 1) == "caught"


def test_execution_budget_limit() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy", max_execution_steps=50))
    source = (
        "let x be 0\n"
        "while true:\n"
        "    change x to x plus 1\n"
    )
    with pytest.raises(ExecutionBudgetExceeded) as exc_info:
        engine.run_source(source)
    assert "instruction limit" in str(exc_info.value)
