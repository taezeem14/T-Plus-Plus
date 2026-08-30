from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from tpp.core.ast_nodes import ClassDefStmt, FunctionDefStmt, Program
from tpp.parser.parser import Parser
from tpp.stdlib.native import create_native_stdlib_registry


def generate_docs_for_source(source: str, title: Optional[str] = None) -> str:
    lines = source.splitlines()
    parser = Parser(source)
    try:
        program = parser.parse()
    except Exception:
        program = Program(statements=[])

    doc_title = title or "T++ Module Documentation"
    output: list[str] = [f"# {doc_title}\n"]

    # Extract top-level comments as module summary
    module_comments: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            module_comments.append(stripped.lstrip("#").strip())
        elif stripped:
            break

    if module_comments:
        output.append("\n".join(module_comments) + "\n\n---\n")

    functions: list[FunctionDefStmt] = []
    classes: list[ClassDefStmt] = []

    for stmt in program.statements:
        if isinstance(stmt, FunctionDefStmt):
            functions.append(stmt)
        elif isinstance(stmt, ClassDefStmt):
            classes.append(stmt)

    if functions:
        output.append("## Functions\n")
        for fn in functions:
            output.append(_format_function_doc(fn, lines))

    if classes:
        output.append("## Classes\n")
        for cls in classes:
            output.append(_format_class_doc(cls, lines))

    if not functions and not classes:
        output.append("_No public functions or classes exported in this file._\n")

    return "\n".join(output)


def _format_function_doc(fn: FunctionDefStmt, lines: list[str]) -> str:
    ret_str = f" -> `{fn.return_type}`" if fn.return_type else ""
    params_rendered = []
    for p in fn.params:
        p_type = fn.param_types.get(p)
        p_default = fn.param_defaults.get(p)
        item = f"`{p}`"
        if p_type:
            item += f" as `{p_type}`"
        if p_default is not None:
            item += f" = `{p_default}`"
        params_rendered.append(item)

    sig = f"### `define {fn.name}`"
    if params_rendered:
        sig += f" with {', '.join(params_rendered)}"
    sig += ret_str

    docstring = _extract_preceding_doc(fn.line, lines)
    doc_body = f"\n{docstring}\n" if docstring else "\n_No documentation provided._\n"
    return f"{sig}\n{doc_body}"


def _format_class_doc(cls: ClassDefStmt, lines: list[str]) -> str:
    header = f"### `create class {cls.name}`\n"
    docstring = _extract_preceding_doc(cls.line, lines)
    body = [header]
    if docstring:
        body.append(f"{docstring}\n")

    if cls.init_method:
        body.append("#### Constructor\n")
        body.append(_format_function_doc(cls.init_method, lines))

    if cls.methods:
        body.append("#### Methods\n")
        for m in cls.methods:
            body.append(_format_function_doc(m, lines))

    return "\n".join(body)


def _extract_preceding_doc(stmt_line: int, lines: list[str]) -> str:
    doc_lines: list[str] = []
    current_idx = stmt_line - 2  # 0-indexed line right above statement

    while current_idx >= 0:
        line = lines[current_idx].strip()
        if line.startswith("#"):
            doc_lines.insert(0, line.lstrip("#").strip())
            current_idx -= 1
        else:
            break

    return "\n".join(doc_lines)


def generate_docs_for_stdlib(module_name: str) -> str:
    registry = create_native_stdlib_registry()
    if module_name not in registry:
        return f"# Error\n\nStdlib module `{module_name}` was not found."

    mod = registry[module_name]
    output = [
        f"# Standard Library: `{module_name}`\n",
        f"The `{module_name}` standard module provides built-in functions and constants.\n",
        "## Exported Members\n",
    ]

    for member_name in sorted(mod.members):
        member = mod.member(member_name)
        doc = getattr(member, "__doc__", None) or "Native standard function."
        output.append(f"- **`{member_name}`**: {doc}")

    return "\n".join(output) + "\n"
