from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class DiagnosticSeverity(str, Enum):
    ERROR = "error"
    WARNING = "warning"
    HINT = "hint"
    INFO = "info"


@dataclass
class DiagnosticHint:
    suggestion: Optional[str] = None
    fix_preview: Optional[str] = None


@dataclass
class TppCallFrame:
    function_name: str
    line: Optional[int] = None
    col: Optional[int] = None
    file_path: Optional[str] = None

    def __str__(self) -> str:
        loc = []
        if self.file_path:
            loc.append(self.file_path)
        if self.line is not None:
            loc.append(f"{self.line}")
            if self.col is not None:
                loc.append(f"{self.col}")
        loc_str = ":".join(loc) if loc else "unknown location"
        return f"  at {self.function_name} ({loc_str})"


@dataclass
class Diagnostic:
    message: str
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR
    line: Optional[int] = None
    col: Optional[int] = None
    end_line: Optional[int] = None
    end_col: Optional[int] = None
    suggestion: Optional[str] = None
    fix_preview: Optional[str] = None
    source_line: Optional[str] = None
    file_path: Optional[str] = None
    category: str = "general"
    call_stack: list[TppCallFrame] = field(default_factory=list)

    def render(self, *, color: bool = True) -> str:
        # Check NO_COLOR convention
        if os.environ.get("NO_COLOR") or not color:
            c_red = c_yellow = c_blue = c_bold = c_reset = ""
        else:
            c_red = "\033[31m"
            c_yellow = "\033[33m"
            c_blue = "\033[36m"
            c_bold = "\033[1m"
            c_reset = "\033[0m"

        sev_label = self.severity.value.upper()
        sev_color = c_red if self.severity == DiagnosticSeverity.ERROR else (c_yellow if self.severity == DiagnosticSeverity.WARNING else c_blue)

        header = f"{sev_color}{c_bold}{sev_label}:{c_reset} {self.message}"
        lines = [header]

        # Location info
        loc_parts = []
        if self.file_path:
            loc_parts.append(self.file_path)
        if self.line is not None:
            loc_parts.append(str(self.line))
            if self.col is not None:
                loc_parts.append(str(self.col))
        if loc_parts:
            lines.append(f"  --> {':'.join(loc_parts)}")

        # Source code preview with carets
        if self.source_line is not None and self.line is not None:
            line_str = f"{self.line} | "
            indent = len(line_str)
            lines.append(f"  {' ' * (indent - 3)}|")
            lines.append(f"  {line_str}{self.source_line}")

            if self.col is not None:
                start_col = max(1, self.col) - 1
                length = max(1, (self.end_col - self.col) if self.end_col is not None and self.end_col >= self.col else 1)
                caret_line = " " * start_col + "^" * length
                lines.append(f"  {' ' * (indent - 3)}| {c_red}{caret_line}{c_reset}")
            else:
                lines.append(f"  {' ' * (indent - 3)}|")

        if self.suggestion:
            lines.append(f"  {c_blue}Hint:{c_reset} {self.suggestion}")
        if self.fix_preview:
            lines.append(f"  {c_blue}Try:{c_reset}  {self.fix_preview}")

        if self.call_stack:
            lines.append("Call stack:")
            for frame in self.call_stack:
                lines.append(f"  {frame}")

        return "\n".join(lines)


class TppError(Exception):
    """Base class for all language errors."""

    category: str = "general"

    def __init__(
        self,
        message: str,
        line: Optional[int] = None,
        col: Optional[int] = None,
        *,
        end_line: Optional[int] = None,
        end_col: Optional[int] = None,
        suggestion: Optional[str] = None,
        fix_preview: Optional[str] = None,
        source_line: Optional[str] = None,
        file_path: Optional[str] = None,
        severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
        call_stack: Optional[list[TppCallFrame]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.line = line
        self.col = col
        self.end_line = end_line
        self.end_col = end_col
        self.suggestion = suggestion
        self.fix_preview = fix_preview
        self.source_line = source_line
        self.file_path = file_path
        self.severity = severity
        self.call_stack: list[TppCallFrame] = call_stack or []

    def to_diagnostic(self) -> Diagnostic:
        return Diagnostic(
            message=self.message,
            severity=self.severity,
            line=self.line,
            col=self.col,
            end_line=self.end_line,
            end_col=self.end_col,
            suggestion=self.suggestion,
            fix_preview=self.fix_preview,
            source_line=self.source_line,
            file_path=self.file_path,
            category=self.category,
            call_stack=self.call_stack,
        )

    def __str__(self) -> str:
        prefix = f"Line {self.line}: " if self.line is not None else ""
        parts = [f"{prefix}{self.message}"]
        if self.suggestion:
            parts.append(f"Hint: {self.suggestion}")
        if self.fix_preview:
            parts.append(f"Try: {self.fix_preview}")
        if self.call_stack:
            parts.append("Call stack:")
            for frame in self.call_stack:
                parts.append(f"  {frame}")
        return "\n".join(parts)


class SyntaxTppError(TppError):
    category = "syntax"


class SemanticTppError(TppError):
    category = "semantic"


class RuntimeTppError(TppError):
    category = "runtime"


class TypeTppError(RuntimeTppError):
    category = "type"


class MathTppError(RuntimeTppError):
    category = "math"


class IndexTppError(RuntimeTppError):
    category = "index"


class KeyNotFoundTppError(RuntimeTppError):
    category = "key_not_found"


class ModuleNotFoundTppError(SemanticTppError):
    category = "module"


class PluginTppError(TppError):
    category = "plugin"


class SecurityTppError(TppError):
    category = "security"


class ExecutionBudgetExceeded(TppError):
    """Raised when execution limits (time or instruction budget) are reached."""
    category = "resource_limit"


class IncompleteBlockError(SyntaxTppError):
    pass


class ReturnSignal(Exception):
    def __init__(self, value: object) -> None:
        self.value = value


class BreakSignal(Exception):
    pass


class ContinueSignal(Exception):
    pass


class UserRaisedSignal(Exception):
    """Signal carrying a user-raised exception for try/handle."""
    def __init__(self, error_instance: Any, line: Optional[int] = None) -> None:
        self.error_instance = error_instance
        self.line = line


def format_diagnostic(diagnostic: Diagnostic, *, color: bool = True) -> str:
    return diagnostic.render(color=color)


def render_error(exc: Exception, *, debug_trace: bool = False, color: bool = True) -> str:
    if isinstance(exc, TppError):
        # If source_line is available or location info is present, use rich rendering
        if exc.source_line is not None or exc.col is not None:
            return exc.to_diagnostic().render(color=color)
        return str(exc)
    if debug_trace:
        import traceback
        return "".join(traceback.format_exception(exc))
    return str(exc)
