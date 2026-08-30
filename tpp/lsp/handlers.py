from __future__ import annotations

import re
from typing import Any, Optional

from tpp.core.ast_nodes import ClassDefStmt, FunctionDefStmt, LetStmt, Program
from tpp.core.constants import CORE_STATEMENT_STARTERS
from tpp.core.errors import TppError
from tpp.lsp.protocol import (
    CompletionItem,
    Hover,
    Location,
    LspDiagnostic,
    Position,
    Range,
    TextEdit,
)
from tpp.parser.parser import Parser
from tpp.parser.semantic import SemanticAnalyzer
from tpp.parser.synonyms import GLOBAL_SYNONYMS
from tpp.stdlib.native import create_native_stdlib_registry
from tpp.tools.formatter import format_tpp_source


class LspHandler:
    def __init__(self) -> None:
        self.documents: dict[str, str] = {}
        self.stdlib_registry = create_native_stdlib_registry()

    def update_document(self, uri: str, text: str) -> list[LspDiagnostic]:
        self.documents[uri] = text
        return self.compute_diagnostics(uri, text)

    def compute_diagnostics(self, uri: str, text: str) -> list[LspDiagnostic]:
        diagnostics: list[LspDiagnostic] = []
        lines = text.splitlines()

        parser = Parser(text)
        try:
            program = parser.parse()
            analyzer = SemanticAnalyzer()
            analyzer.analyze(program)
        except TppError as exc:
            line_val = getattr(exc, "line", None)
            line_idx = max(0, line_val - 1) if line_val else 0
            col_val = getattr(exc, "column", None)
            col_idx = max(0, col_val - 1) if col_val else 0
            line_len = len(lines[line_idx]) if line_idx < len(lines) else 1
            diagnostics.append(
                LspDiagnostic(
                    range=Range(
                        start=Position(line=line_idx, character=col_idx),
                        end=Position(line=line_idx, character=line_len),
                    ),
                    message=getattr(exc, "message", str(exc)) + (f"\nHint: {exc.suggestion}" if getattr(exc, "suggestion", None) else ""),
                    severity=1,
                )
            )
        except Exception as exc:
            diagnostics.append(
                LspDiagnostic(
                    range=Range(start=Position(line=0, character=0), end=Position(line=0, character=1)),
                    message=f"Internal analysis error: {exc}",
                    severity=2,
                )
            )

        return diagnostics

    def get_hover(self, uri: str, position: Position) -> Optional[Hover]:
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        if position.line >= len(lines):
            return None

        line = lines[position.line]
        word = self._get_word_at_pos(line, position.character)
        if not word:
            return None

        # 1. Check Stdlib
        if word in self.stdlib_registry:
            mod = self.stdlib_registry[word]
            members = ", ".join(sorted(mod.members.keys())[:12])
            return Hover(
                contents=f"**Standard Library Module `{word}`**\n\nMembers: `{members}...`"
            )

        for mod_name, mod in self.stdlib_registry.items():
            if mod.has_member(word):
                member = mod.member(word)
                doc = getattr(member, "__doc__", None) or "Native standard function."
                return Hover(contents=f"**`{mod_name}.{word}`**\n\n{doc}")

        # 2. Check Synonyms
        syn = GLOBAL_SYNONYMS.get(word)
        if syn is not None:
            return Hover(
                contents=f"**Natural Synonym `{syn.natural_spelling}`**\n\nMaps to: `{syn.symbol_spelling}`\nCategory: `{syn.category}`\n\n{syn.description}"
            )

        # 3. Check AST definitions in current file
        try:
            program = Parser(text).parse()
            for stmt in program.statements:
                if isinstance(stmt, FunctionDefStmt) and stmt.name == word:
                    sig = f"define {stmt.name} with {', '.join(stmt.params)}"
                    if stmt.return_type:
                        sig += f", giving back {stmt.return_type}"
                    return Hover(contents=f"```tpp\n{sig}\n```\n_Function defined at line {stmt.line}_")
                if isinstance(stmt, ClassDefStmt) and stmt.name == word:
                    return Hover(contents=f"```tpp\ncreate class {stmt.name}\n```\n_Class defined at line {stmt.line}_")
                if isinstance(stmt, LetStmt) and stmt.name == word:
                    t_info = f" as {stmt.type_annotation}" if stmt.type_annotation else ""
                    return Hover(contents=f"```tpp\nlet {stmt.name}{t_info}\n```\n_Variable declared at line {stmt.line}_")
        except Exception:
            pass

        return None

    def get_completions(self, uri: str, position: Position) -> list[CompletionItem]:
        completions: list[CompletionItem] = []

        # Statement Starters (Keywords)
        for kw in sorted(CORE_STATEMENT_STARTERS | {"use", "from", "export", "try", "handle", "finally", "raise", "match", "when", "otherwise"}):
            completions.append(
                CompletionItem(
                    label=kw,
                    kind=14,
                    detail="Keyword / Statement Starter",
                    insertText=kw + " ",
                )
            )

        # Natural Synonyms
        for syn in GLOBAL_SYNONYMS.all_entries():
            completions.append(
                CompletionItem(
                    label=syn.natural_spelling,
                    kind=1,
                    detail=f"Synonym for '{syn.symbol_spelling}'",
                    documentation=syn.description,
                )
            )

        # Stdlib Functions
        for mod_name, mod in self.stdlib_registry.items():
            for m_name in mod.members:
                completions.append(
                    CompletionItem(
                        label=m_name,
                        kind=3,
                        detail=f"Stdlib ({mod_name})",
                        documentation=f"Function from {mod_name} standard library module.",
                    )
                )

        # In-scope AST identifiers from current document
        text = self.documents.get(uri, "")
        if text:
            try:
                prog = Parser(text).parse()
                for stmt in prog.statements:
                    if isinstance(stmt, FunctionDefStmt):
                        completions.append(CompletionItem(label=stmt.name, kind=3, detail="Local Function"))
                    elif isinstance(stmt, ClassDefStmt):
                        completions.append(CompletionItem(label=stmt.name, kind=7, detail="Local Class"))
                    elif isinstance(stmt, LetStmt):
                        completions.append(CompletionItem(label=stmt.name, kind=6, detail="Local Variable"))
            except Exception:
                pass

        return completions

    def get_definition(self, uri: str, position: Position) -> Optional[Location]:
        text = self.documents.get(uri, "")
        lines = text.splitlines()
        if position.line >= len(lines):
            return None

        word = self._get_word_at_pos(lines[position.line], position.character)
        if not word:
            return None

        try:
            program = Parser(text).parse()
            for stmt in program.statements:
                if isinstance(stmt, (FunctionDefStmt, ClassDefStmt, LetStmt)) and getattr(stmt, "name", None) == word:
                    line_0 = stmt.line - 1
                    return Location(
                        uri=uri,
                        range=Range(
                            start=Position(line=line_0, character=0),
                            end=Position(line=line_0, character=len(lines[line_0]) if line_0 < len(lines) else 0),
                        ),
                    )
        except Exception:
            pass

        return None

    def get_formatting(self, uri: str) -> list[TextEdit]:
        text = self.documents.get(uri, "")
        if not text:
            return []

        formatted = format_tpp_source(text)
        if formatted == text:
            return []

        lines = text.splitlines()
        last_line = max(0, len(lines) - 1)
        last_col = len(lines[last_line]) if lines else 0

        return [
            TextEdit(
                range=Range(
                    start=Position(line=0, character=0),
                    end=Position(line=last_line, character=last_col),
                ),
                newText=formatted,
            )
        ]

    @staticmethod
    def _get_word_at_pos(line: str, char_pos: int) -> str:
        if char_pos >= len(line):
            char_pos = max(0, len(line) - 1)
        # Find word boundary
        start = char_pos
        while start > 0 and (line[start - 1].isalnum() or line[start - 1] == "_"):
            start -= 1
        end = char_pos
        while end < len(line) and (line[end].isalnum() or line[end] == "_"):
            end += 1
        return line[start:end].strip()
