from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

from tpp.core.constants import VERSION
from tpp.core.errors import (
    Diagnostic,
    ExecutionBudgetExceeded,
    IndexTppError,
    MathTppError,
    ModuleNotFoundTppError,
    PluginTppError,
    RuntimeTppError,
    SecurityTppError,
    SyntaxTppError,
    TppError,
    TypeTppError,
)
from tpp.runtime.engine import EngineConfig, RuntimeEngine
from tpp.runtime.environment import Scope

__version__ = VERSION

__all__ = [
    "__version__",
    "EngineConfig",
    "RuntimeEngine",
    "Scope",
    "TppError",
    "SyntaxTppError",
    "RuntimeTppError",
    "TypeTppError",
    "MathTppError",
    "IndexTppError",
    "SecurityTppError",
    "PluginTppError",
    "ModuleNotFoundTppError",
    "ExecutionBudgetExceeded",
    "Diagnostic",
    "run_source",
    "run_file",
    "eval_expr",
]


def run_source(
    source: str,
    config: Optional[EngineConfig] = None,
    initial_scope: Optional[dict[str, Any]] = None,
    file_path: Optional[str] = None,
) -> RuntimeEngine:
    """Public embedding API to execute T++ code from Python."""
    engine = RuntimeEngine(config or EngineConfig())
    if initial_scope:
        for k, v in initial_scope.items():
            engine.global_scope.define(k, v)
    engine.run_source(source, file_path=file_path)
    return engine


def run_file(
    path: str | Path,
    config: Optional[EngineConfig] = None,
    initial_scope: Optional[dict[str, Any]] = None,
) -> RuntimeEngine:
    """Public embedding API to execute a T++ file from Python."""
    p = Path(path)
    source = p.read_text(encoding="utf-8")
    return run_source(source, config=config, initial_scope=initial_scope, file_path=str(p.resolve()))


def eval_expr(
    expr: str,
    scope: Optional[dict[str, Any]] = None,
    config: Optional[EngineConfig] = None,
) -> Any:
    """Public embedding API to evaluate a single T++ expression from Python."""
    engine = RuntimeEngine(config or EngineConfig())
    eval_scope = Scope()
    if scope:
        for k, v in scope.items():
            eval_scope.define(k, v)
    return engine.evaluate_expression(expr, eval_scope, line=1)
