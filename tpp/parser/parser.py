from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from tpp.core.ast_nodes import (
    AddToStmt,
    AskStmt,
    BreakStmt,
    ChangeStmt,
    ClassDefStmt,
    ContinueStmt,
    CountStmt,
    CreateButtonStmt,
    CreateWindowStmt,
    DescribeStmt,
    DictSetStmt,
    ExpectEqualStmt,
    ExpectRangeStmt,
    ExpectTypeStmt,
    ExportStmt,
    ExprStmt,
    ForEachStmt,
    FunctionDefStmt,
    HandleClause,
    IfStmt,
    ImportFromStmt,
    ImportModuleStmt,
    LetStmt,
    MatchStmt,
    MatchWhenClause,
    OnButtonClickStmt,
    PassStmt,
    Program,
    RaiseStmt,
    RecordTypeDefStmt,
    RegisterKeywordStmt,
    RememberStmt,
    RemoveFromStmt,
    RepeatStmt,
    ReturnStmt,
    SayStmt,
    SetWindowSizeStmt,
    ShowWindowStmt,
    SmartAssignStmt,
    TestStmt,
    TestSuiteStmt,
    TryStmt,
    TypeAnnotation,
    UnionTypeAnnotation,
    UseFromModuleStmt,
    UseModuleStmt,
    WhileStmt,
)
from tpp.core.constants import CORE_STATEMENT_STARTERS, DEFAULT_REWRITE_LIMIT, PARSER_MODES
from tpp.core.errors import Diagnostic, DiagnosticSeverity, IncompleteBlockError, SyntaxTppError
from tpp.core.types import parse_type_annotation
from tpp.core.utils import (
    is_identifier,
    normalize_phrase,
    parse_quoted_string,
    split_natural_args,
    split_top_level,
    suggest_closest,
)
from tpp.parser.lexer import normalize_assignment_sugar


@dataclass
class ParserConfig:
    mode: str = "fuzzy"
    repl_mode: bool = False
    collect_multiple_errors: bool = False


class Parser:
    def __init__(
        self,
        source: str,
        *,
        config: Optional[ParserConfig] = None,
        plugin_rewrites: Optional[dict[str, str]] = None,
        plugin_keywords: Optional[set[str]] = None,
        file_path: Optional[str] = None,
    ) -> None:
        self.config = config or ParserConfig()
        if self.config.mode not in PARSER_MODES:
            raise SyntaxTppError(f"Unknown parser mode '{self.config.mode}'.")

        self.source = source
        self.file_path = file_path
        self.lines: list[tuple[int, str]] = self._build_logical_lines(source)
        self.plugin_rewrites = plugin_rewrites or {}
        self.plugin_keywords = plugin_keywords or set()
        self.diagnostics: list[Diagnostic] = []
        self._refresh_plugin_phrase_order()

    @staticmethod
    def _build_logical_lines(source: str) -> list[tuple[int, str]]:
        raw_lines = source.splitlines()
        logical: list[tuple[int, str]] = []
        i = 0
        n = len(raw_lines)

        while i < n:
            start_line_no = i + 1
            line = raw_lines[i].rstrip("\r\n")
            stripped = line.strip()

            # Empty lines or standalone comments are preserved directly
            if not stripped or stripped.startswith("#"):
                logical.append((start_line_no, line))
                i += 1
                continue

            bracket_depth = 0
            curr_i = i

            while True:
                in_quote: Optional[str] = None
                escaped = False
                backslash_continuation = False

                idx = 0
                seg = raw_lines[curr_i].rstrip("\r\n")
                while idx < len(seg):
                    ch = seg[idx]
                    if in_quote:
                        if ch == in_quote and not escaped:
                            in_quote = None
                        elif ch == "\\" and not escaped:
                            escaped = True
                            idx += 1
                            continue
                        escaped = False
                    else:
                        if ch in ('"', "'"):
                            in_quote = ch
                        elif ch == "#":
                            break
                        elif ch in "([{":
                            bracket_depth += 1
                        elif ch in ")]}":
                            bracket_depth = max(0, bracket_depth - 1)
                    idx += 1

                uncommented = seg[:idx].rstrip()
                if uncommented.endswith("\\"):
                    backslash_continuation = True
                    uncommented = uncommented[:-1].rstrip()

                if curr_i == i:
                    accum = uncommented
                else:
                    accum = accum + " " + uncommented.strip()

                if (bracket_depth > 0 or backslash_continuation) and curr_i + 1 < n:
                    curr_i += 1
                else:
                    break

            logical.append((start_line_no, accum))
            i = curr_i + 1

        return logical

    @property
    def fuzzy_mode(self) -> bool:
        return self.config.mode in {"fuzzy", "intent"}

    @property
    def intent_mode(self) -> bool:
        return self.config.mode == "intent"

    def _refresh_plugin_phrase_order(self) -> None:
        self._plugin_phrases_sorted = sorted(self.plugin_rewrites.keys(), key=len, reverse=True)

    def parse(self) -> Program:
        statements, index = self.parse_block(0, 0)
        while index < len(self.lines):
            line_no, text = self.lines[index]
            stripped = text.strip()
            if stripped == "" or stripped.startswith("#"):
                index += 1
                continue
            err = SyntaxTppError(
                "Unexpected content after end of block.",
                line_no,
                source_line=text,
                file_path=self.file_path,
            )
            if self.config.collect_multiple_errors:
                self.diagnostics.append(err.to_diagnostic())
                index += 1
            else:
                raise err
        return Program(statements)

    def parse_block(self, index: int, indent: int) -> tuple[list[Any], int]:
        statements: list[Any] = []
        while index < len(self.lines):
            line_no, raw_line = self.lines[index]
            stripped = raw_line.strip()
            if stripped == "" or stripped.startswith("#"):
                index += 1
                continue

            line_indent = self.count_indent(raw_line, line_no)
            if line_indent < indent:
                break
            if line_indent > indent:
                err = SyntaxTppError(
                    "Indentation looks incorrect here. This line is indented more than expected.",
                    line_no,
                    suggestion="Make sure block lines share the same indent width.",
                    source_line=raw_line,
                    file_path=self.file_path,
                )
                if self.config.collect_multiple_errors:
                    self.diagnostics.append(err.to_diagnostic())
                    index += 1
                    continue
                else:
                    raise err

            stripped = raw_line.strip()
            lowered = stripped.lower()
            if (
                lowered.startswith("but if ")
                or lowered.startswith("otherwise if ")
                or lowered == "otherwise:"
                or lowered.startswith("handle ")
                or lowered == "finally:"
            ):
                break

            try:
                statement, index = self.parse_statement(index, indent)
                statements.append(statement)
            except SyntaxTppError as e:
                if e.source_line is None:
                    e.source_line = raw_line
                if e.file_path is None:
                    e.file_path = self.file_path
                if self.config.collect_multiple_errors:
                    self.diagnostics.append(e.to_diagnostic())
                    # Synchronization recovery: skip forward to next line
                    index += 1
                else:
                    raise e

        return statements, index

    def parse_statement(self, index: int, indent: int) -> tuple[Any, int]:
        line_no, raw_line = self.lines[index]
        text = raw_line.strip()

        if self.intent_mode:
            text = normalize_assignment_sugar(text)

        # Export statements (Part 10)
        export_match = re.match(r"^export\s+(.+)$", text, re.IGNORECASE)
        if export_match:
            inner_text = export_match.group(1).strip()
            # Temporarily replace current line text to parse the exported statement
            self.lines[index] = (line_no, " " * indent + inner_text)
            inner_stmt, next_index = self.parse_statement(index, indent)
            self.lines[index] = (line_no, raw_line)
            return ExportStmt(line=line_no, statement=inner_stmt), next_index

        register_stmt = self.try_parse_register_keyword(text, line_no)
        if register_stmt is not None:
            self.plugin_keywords.add(normalize_phrase(register_stmt.phrase))
            if register_stmt.template is not None:
                self.plugin_rewrites[normalize_phrase(register_stmt.phrase)] = register_stmt.template
                self._refresh_plugin_phrase_order()
            return register_stmt, index + 1

        text = self.apply_plugin_rewrites(text, line_no)

        # --- Module Imports (Part 10) ---
        # 1. 'use Circle and Rectangle from the "shapes" module' / 'use Circle from "shapes"'
        use_from_match = re.match(
            r"^use\s+(.+?)\s+from\s+(?:the\s+)?(?:module\s+)?[\"']?([A-Za-z0-9_\.\-\/]+)[\"']?(?:\s+module)?$",
            text,
            re.IGNORECASE,
        )
        if use_from_match:
            raw_names = use_from_match.group(1).strip()
            mod_name = use_from_match.group(2).strip()
            name_parts = split_natural_args(raw_names)
            names_list: list[tuple[str, Optional[str]]] = []
            for item in name_parts:
                alias_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)$", item, re.IGNORECASE)
                if alias_match:
                    names_list.append((alias_match.group(1), alias_match.group(2)))
                else:
                    names_list.append((item.strip(), None))
            return UseFromModuleStmt(line=line_no, module=mod_name, names=names_list), index + 1

        # 2. 'from "shapes" use Circle and Rectangle'
        from_use_match = re.match(
            r"^from\s+[\"']?([A-Za-z0-9_\.\-\/]+)[\"']?\s+use\s+(.+)$",
            text,
            re.IGNORECASE,
        )
        if from_use_match:
            mod_name = from_use_match.group(1).strip()
            raw_names = from_use_match.group(2).strip()
            name_parts = split_natural_args(raw_names)
            names_list = []
            for item in name_parts:
                alias_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)$", item, re.IGNORECASE)
                if alias_match:
                    names_list.append((alias_match.group(1), alias_match.group(2)))
                else:
                    names_list.append((item.strip(), None))
            return UseFromModuleStmt(line=line_no, module=mod_name, names=names_list), index + 1

        # 3. 'use the "shapes" module' / 'use "shapes"'
        use_module_match = re.match(
            r"^use\s+(?:the\s+)?[\"']?([A-Za-z0-9_\.\-\/]+)[\"']?(?:\s+module)?(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$",
            text,
            re.IGNORECASE,
        )
        if use_module_match:
            mod_name = use_module_match.group(1).strip()
            alias = use_module_match.group(2)
            return UseModuleStmt(line=line_no, module=mod_name, alias=alias), index + 1

        # 4. Standard 'import ... from ...' synonym
        import_syn_match = re.match(
            r"^import\s+(.+?)\s+from\s+[\"']?([A-Za-z0-9_\.\-\/]+)[\"']?$",
            text,
            re.IGNORECASE,
        )
        if import_syn_match:
            raw_names = import_syn_match.group(1).strip()
            mod_name = import_syn_match.group(2).strip()
            name_parts = [n.strip() for n in raw_names.split(",") if n.strip()]
            names_list = []
            for item in name_parts:
                alias_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)$", item, re.IGNORECASE)
                if alias_match:
                    names_list.append((alias_match.group(1), alias_match.group(2)))
                else:
                    names_list.append((item.strip(), None))
            return UseFromModuleStmt(line=line_no, module=mod_name, names=names_list), index + 1

        # --- Error Handling: Try / Handle / Finally / Raise (Part 12 & Part 1) ---
        if re.match(r"^try:$", text, re.IGNORECASE):
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            handlers: list[HandleClause] = []
            finally_body: Optional[list[Any]] = None

            while True:
                peek = self.peek_next_non_blank(next_index)
                if peek is None:
                    break
                peek_index, peek_no, peek_text, peek_indent = peek
                if peek_indent != indent:
                    break

                # 'handle DivisionError as e:' or 'handle any error as e:'
                handle_match = re.match(
                    r"^handle\s+(?:any\s+error|([A-Za-z_][A-Za-z0-9_]*))\s+as\s+([A-Za-z_][A-Za-z0-9_]*):$",
                    peek_text,
                    re.IGNORECASE,
                )
                if handle_match:
                    err_type = handle_match.group(1)  # None if "any error"
                    var_name = handle_match.group(2)
                    h_body, next_index = self.parse_child_block(peek_index + 1, indent, peek_no)
                    handlers.append(HandleClause(line=peek_no, error_type=err_type, var_name=var_name, body=h_body))
                    continue

                # 'finally:'
                if re.match(r"^finally:$", peek_text, re.IGNORECASE):
                    finally_body, next_index = self.parse_child_block(peek_index + 1, indent, peek_no)
                    break
                break

            if not handlers and finally_body is None:
                raise SyntaxTppError("A 'try' block must have at least one 'handle' clause or a 'finally' clause.", line_no)

            return TryStmt(line=line_no, body=body, handlers=handlers, finally_body=finally_body), next_index

        # 'raise the error <expr>' / 'raise <expr>' / 'throw <expr>'
        raise_match = re.match(r"^(?:raise\s+the\s+error|raise|throw)\s+(.+)$", text, re.IGNORECASE)
        if raise_match:
            return RaiseStmt(line=line_no, expr=raise_match.group(1).strip()), index + 1

        # --- Testing Suite / Test blocks ---
        suite_match = re.match(r"^suite\s+(.+):$", text, re.IGNORECASE)
        if suite_match:
            suite_name = parse_quoted_string(suite_match.group(1).strip(), line_no, "Suite name")
            suite_body, next_index = self.parse_child_block(index + 1, indent, line_no)
            tests = [stmt for stmt in suite_body if isinstance(stmt, TestStmt)]
            invalid = [stmt for stmt in suite_body if not isinstance(stmt, TestStmt)]
            if invalid:
                raise SyntaxTppError("A test suite may only contain test blocks.", line_no)
            return TestSuiteStmt(line=line_no, name=suite_name, tests=tests), next_index

        # 'test "name":' or 'test "name" expecting an error:'
        test_exp_match = re.match(r"^test\s+(.+?)(?:\s+expecting\s+(?:an?\s+error|([A-Za-z_][A-Za-z0-9_]*)))?:$", text, re.IGNORECASE)
        if test_exp_match:
            raw_name = test_exp_match.group(1).strip()
            exp_err = test_exp_match.group(2) or ("Error" if "expecting an error" in text.lower() else None)
            test_name = parse_quoted_string(raw_name, line_no, "Test name")
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return TestStmt(line=line_no, name=test_name, body=body, expected_error=exp_err), next_index

        expect_type_match = re.match(r"^expect\s+type\s+of\s+(.+)\s+to\s+be\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if expect_type_match:
            return (
                ExpectTypeStmt(
                    line=line_no,
                    expr=expect_type_match.group(1).strip(),
                    expected_type=expect_type_match.group(2).strip(),
                ),
                index + 1,
            )

        expect_range_match = re.match(r"^expect\s+(.+)\s+to\s+be\s+between\s+(.+)\s+and\s+(.+)$", text, re.IGNORECASE)
        if expect_range_match:
            return (
                ExpectRangeStmt(
                    line=line_no,
                    expr=expect_range_match.group(1).strip(),
                    low_expr=expect_range_match.group(2).strip(),
                    high_expr=expect_range_match.group(3).strip(),
                ),
                index + 1,
            )

        expect_equal_match = re.match(r"^expect\s+(.+)\s+to\s+be\s+(.+)$", text, re.IGNORECASE)
        if expect_equal_match:
            return (
                ExpectEqualStmt(
                    line=line_no,
                    left_expr=expect_equal_match.group(1).strip(),
                    right_expr=expect_equal_match.group(2).strip(),
                ),
                index + 1,
            )

        describe_match = re.match(r"^describe\s*:\s*(.+)$", text, re.IGNORECASE)
        if describe_match:
            return DescribeStmt(line=line_no, description=describe_match.group(1).strip()), index + 1

        fuzzy_stmt = self.try_parse_fuzzy_statement(text, line_no)
        if fuzzy_stmt is not None:
            return fuzzy_stmt, index + 1

        # GUI Stmts
        create_window_match = re.match(
            r"^create\s+window\s+titled\s+(.+?)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?$",
            text,
            re.IGNORECASE,
        )
        if create_window_match:
            return (
                CreateWindowStmt(
                    line=line_no,
                    title_expr=create_window_match.group(1).strip(),
                    window_name=create_window_match.group(2),
                ),
                index + 1,
            )

        set_window_size_match = re.match(
            r"^set\s+window\s+size\s+to\s+(.+)\s+by\s+(.+?)(?:\s+for\s+([A-Za-z_][A-Za-z0-9_]*))?$",
            text,
            re.IGNORECASE,
        )
        if set_window_size_match:
            return (
                SetWindowSizeStmt(
                    line=line_no,
                    width_expr=set_window_size_match.group(1).strip(),
                    height_expr=set_window_size_match.group(2).strip(),
                    window_name=set_window_size_match.group(3),
                ),
                index + 1,
            )

        create_button_match = re.match(
            r"^create\s+button\s+(.+?)(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?(?:\s+in\s+window\s+([A-Za-z_][A-Za-z0-9_]*))?$",
            text,
            re.IGNORECASE,
        )
        if create_button_match:
            return (
                CreateButtonStmt(
                    line=line_no,
                    label_expr=create_button_match.group(1).strip(),
                    button_name=create_button_match.group(2),
                    window_name=create_button_match.group(3),
                ),
                index + 1,
            )

        on_click_match = re.match(
            r"^on\s+button\s+click(?:\s+for\s+([A-Za-z_][A-Za-z0-9_]*))?:$",
            text,
            re.IGNORECASE,
        )
        if on_click_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return (
                OnButtonClickStmt(line=line_no, button_name=on_click_match.group(1), body=body),
                next_index,
            )

        show_window_match = re.match(r"^show\s+window(?:\s+([A-Za-z_][A-Za-z0-9_]*))?$", text, re.IGNORECASE)
        if show_window_match:
            return ShowWindowStmt(line=line_no, window_name=show_window_match.group(1)), index + 1

        import_from_match = re.match(
            r"^bring\s+in\s+([A-Za-z_][A-Za-z0-9_]*)\s+from\s+([A-Za-z_][A-Za-z0-9_\.]*)\s*(?:as\s+([A-Za-z_][A-Za-z0-9_]*))?$",
            text,
            re.IGNORECASE,
        )
        if import_from_match:
            return (
                ImportFromStmt(
                    line=line_no,
                    name=import_from_match.group(1),
                    module=import_from_match.group(2),
                    alias=import_from_match.group(3),
                ),
                index + 1,
            )

        import_module_alias_match = re.match(
            r"^bring\s+in\s+([A-Za-z_][A-Za-z0-9_\.]*)\s+as\s+([A-Za-z_][A-Za-z0-9_]*)$",
            text,
            re.IGNORECASE,
        )
        if import_module_alias_match:
            return (
                ImportModuleStmt(
                    line=line_no,
                    module=import_module_alias_match.group(1),
                    alias=import_module_alias_match.group(2),
                ),
                index + 1,
            )

        import_module_match = re.match(r"^bring\s+in\s+([A-Za-z_][A-Za-z0-9_\.]*)$", text, re.IGNORECASE)
        if import_module_match:
            return ImportModuleStmt(line=line_no, module=import_module_match.group(1), alias=None), index + 1

        if_match = re.match(r"^if\s+(.+):$", text, re.IGNORECASE)
        if if_match:
            branches: list[tuple[str, list[Any]]] = []
            condition = if_match.group(1).strip()
            if not condition:
                raise SyntaxTppError("I expected a condition after 'if'.", line_no)
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            branches.append((condition, body))

            else_body: list[Any] = []
            while True:
                peek = self.peek_next_non_blank(next_index)
                if peek is None:
                    break
                peek_index, peek_no, peek_text, peek_indent = peek
                if peek_indent != indent:
                    break
                but_if_match = re.match(r"^(?:but\s+if|otherwise\s+if)\s+(.+):$", peek_text, re.IGNORECASE)
                if but_if_match:
                    next_condition = but_if_match.group(1).strip()
                    if not next_condition:
                        raise SyntaxTppError("I expected a condition after 'otherwise if'.", peek_no)
                    next_body, next_index = self.parse_child_block(peek_index + 1, indent, peek_no)
                    branches.append((next_condition, next_body))
                    continue
                if re.match(r"^otherwise:$", peek_text, re.IGNORECASE):
                    else_body, next_index = self.parse_child_block(peek_index + 1, indent, peek_no)
                break

            return IfStmt(line=line_no, branches=branches, else_body=else_body), next_index

        while_match = re.match(r"^(?:keep\s+doing\s+while|while)\s+(.+):$", text, re.IGNORECASE)
        if while_match:
            condition = while_match.group(1).strip()
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return WhileStmt(line=line_no, condition=condition, body=body), next_index

        foreach_match = re.match(r"^for\s+each\s+([A-Za-z_][A-Za-z0-9_]*)(?:,\s*([A-Za-z_][A-Za-z0-9_]*))?\s+in\s+(.+):$", text, re.IGNORECASE)
        if foreach_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            if foreach_match.group(2):
                return (
                    ForEachStmt(
                        line=line_no,
                        index_var=foreach_match.group(1),
                        var_name=foreach_match.group(2),
                        iterable_expr=foreach_match.group(3).strip(),
                        body=body,
                    ),
                    next_index,
                )
            return (
                ForEachStmt(
                    line=line_no,
                    var_name=foreach_match.group(1),
                    iterable_expr=foreach_match.group(3).strip(),
                    body=body,
                ),
                next_index,
            )

        repeat_until_match = re.match(r"^repeat\s+until\s+(.+):$", text, re.IGNORECASE)
        if repeat_until_match:
            cond = repeat_until_match.group(1).strip()
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return WhileStmt(line=line_no, condition=f"not ({cond})", body=body), next_index

        match_stmt = self.parse_match_statement(text, index, indent)
        if match_stmt is not None:
            return match_stmt

        repeat_match = re.match(r"^repeat\s+(.+?)\s+times:$", text, re.IGNORECASE)
        if repeat_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return RepeatStmt(line=line_no, count_expr=repeat_match.group(1).strip(), body=body), next_index

        count_match = re.match(
            r"^count\s+from\s+(.+?)\s+to\s+(.+?)\s+as\s+([A-Za-z_][A-Za-z0-9_]*):$",
            text,
            re.IGNORECASE,
        )
        if count_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return (
                CountStmt(
                    line=line_no,
                    var_name=count_match.group(3),
                    start_expr=count_match.group(1).strip(),
                    end_expr=count_match.group(2).strip(),
                    body=body,
                ),
                next_index,
            )

        if text.lower() in {"stop the loop", "stop loop", "break"}:
            return BreakStmt(line=line_no), index + 1

        if text.lower() in {"skip to the next", "skip", "continue"}:
            return ContinueStmt(line=line_no), index + 1

        if text.lower() in {"do nothing", "pass", "end"}:
            return PassStmt(line=line_no), index + 1

        function_stmt = self.parse_function_statement(text, index, indent)
        if function_stmt is not None:
            return function_stmt

        if re.match(r"^give\s+back\s+nothing$", text, re.IGNORECASE):
            return ReturnStmt(line=line_no, expr=None), index + 1

        return_expr_match = re.match(r"^(?:give\s+back|return)\s+(.+)$", text, re.IGNORECASE)
        if return_expr_match:
            return ReturnStmt(line=line_no, expr=return_expr_match.group(1).strip()), index + 1

        say_match = re.match(r"^say\s+(.+)$", text, re.IGNORECASE)
        if say_match:
            parts = [piece for piece in split_top_level(say_match.group(1).strip(), " then ") if piece]
            if not parts:
                raise SyntaxTppError("I expected something after 'say'.", line_no)
            return SayStmt(line=line_no, parts=parts), index + 1

        ask_into_match = re.match(r"^ask\s+into\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if ask_into_match:
            return AskStmt(line=line_no, target=ask_into_match.group(1), prompt_expr=None), index + 1

        ask_match = re.match(r"^ask\s+(.+)\s+into\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if ask_match:
            return (
                AskStmt(line=line_no, target=ask_match.group(2), prompt_expr=ask_match.group(1).strip()),
                index + 1,
            )

        if re.match(r"^let\s+([A-Za-z_][A-Za-z0-9_]*)\s+be\s*$", text, re.IGNORECASE):
            raise SyntaxTppError("I expected a value after 'let'.", line_no)

        # LetStmt with optional type annotation: 'let x be 4 as a number'
        let_typed_match = re.match(r"^let\s+([A-Za-z_][A-Za-z0-9_]*)\s+be\s+(.+?)\s+as\s+(a\s+.+|an\s+.+|text|nothing|boolean|number|whole\s+number|record|list.*)$", text, re.IGNORECASE)
        if let_typed_match:
            var_name = let_typed_match.group(1)
            raw_expr = let_typed_match.group(2).strip()
            raw_type = let_typed_match.group(3).strip()
            type_ann = parse_type_annotation(raw_type, line_no)
            return LetStmt(line=line_no, name=var_name, expr=raw_expr, type_annotation=type_ann), index + 1

        let_match = re.match(r"^let\s+([A-Za-z_][A-Za-z0-9_]*)\s+be\s+(.+)$", text, re.IGNORECASE)
        if let_match:
            return LetStmt(line=line_no, name=let_match.group(1), expr=let_match.group(2).strip()), index + 1

        change_my_match = re.match(r"^change\s+my\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(.+)$", text, re.IGNORECASE)
        if change_my_match:
            return ChangeStmt(line=line_no, name=change_my_match.group(1), expr=change_my_match.group(2).strip()), index + 1

        if re.match(r"^change\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s*$", text, re.IGNORECASE):
            raise SyntaxTppError("I expected a value after 'change'.", line_no)

        change_dot_match = re.match(r"^change\s+([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(.+)$", text, re.IGNORECASE)
        if change_dot_match:
            return (
                DictSetStmt(
                    line=line_no,
                    key_expr=f'"{change_dot_match.group(2)}"',
                    map_name=change_dot_match.group(1),
                    value_expr=change_dot_match.group(3).strip(),
                ),
                index + 1,
            )

        change_subscript_match = re.match(r"^change\s+([A-Za-z_][A-Za-z0-9_]*)\[(.+?)\]\s+to\s+(.+)$", text, re.IGNORECASE)
        if change_subscript_match:
            return (
                DictSetStmt(
                    line=line_no,
                    key_expr=change_subscript_match.group(2).strip(),
                    map_name=change_subscript_match.group(1),
                    value_expr=change_subscript_match.group(3).strip(),
                ),
                index + 1,
            )

        change_match = re.match(r"^change\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(.+)$", text, re.IGNORECASE)
        if change_match:
            return ChangeStmt(line=line_no, name=change_match.group(1), expr=change_match.group(2).strip()), index + 1

        dict_dot_match = re.match(r"^set\s+([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(.+)$", text, re.IGNORECASE)
        if dict_dot_match:
            return (
                DictSetStmt(
                    line=line_no,
                    key_expr=f'"{dict_dot_match.group(2)}"',
                    map_name=dict_dot_match.group(1),
                    value_expr=dict_dot_match.group(3).strip(),
                ),
                index + 1,
            )

        dict_subscript_match = re.match(r"^set\s+([A-Za-z_][A-Za-z0-9_]*)\[(.+?)\]\s+to\s+(.+)$", text, re.IGNORECASE)
        if dict_subscript_match:
            return (
                DictSetStmt(
                    line=line_no,
                    key_expr=dict_subscript_match.group(2).strip(),
                    map_name=dict_subscript_match.group(1),
                    value_expr=dict_subscript_match.group(3).strip(),
                ),
                index + 1,
            )

        dict_set_match = re.match(r"^set\s+the\s+(.+)\s+of\s+([A-Za-z_][A-Za-z0-9_]*)\s+to\s+(.+)$", text, re.IGNORECASE)
        if dict_set_match:
            return (
                DictSetStmt(
                    line=line_no,
                    key_expr=dict_set_match.group(1).strip(),
                    map_name=dict_set_match.group(2),
                    value_expr=dict_set_match.group(3).strip(),
                ),
                index + 1,
            )

        add_set_match = re.match(r"^add\s+(.+)\s+to\s+set\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if add_set_match:
            return (
                AddToStmt(
                    line=line_no,
                    value_expr=add_set_match.group(1).strip(),
                    target_name=add_set_match.group(2),
                    force_set=True,
                ),
                index + 1,
            )

        add_match = re.match(r"^add\s+(.+)\s+to\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if add_match:
            return (
                AddToStmt(
                    line=line_no,
                    value_expr=add_match.group(1).strip(),
                    target_name=add_match.group(2),
                    force_set=False,
                ),
                index + 1,
            )

        remove_set_match = re.match(r"^remove\s+(.+)\s+from\s+set\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if remove_set_match:
            return (
                RemoveFromStmt(
                    line=line_no,
                    value_expr=remove_set_match.group(1).strip(),
                    target_name=remove_set_match.group(2),
                    force_set=True,
                ),
                index + 1,
            )

        remove_match = re.match(r"^remove\s+(.+)\s+from\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if remove_match:
            return (
                RemoveFromStmt(
                    line=line_no,
                    value_expr=remove_match.group(1).strip(),
                    target_name=remove_match.group(2),
                    force_set=False,
                ),
                index + 1,
            )

        class_match = re.match(r"^create\s+class\s+([A-Za-z_][A-Za-z0-9_]*):$", text, re.IGNORECASE)
        if class_match:
            class_name = class_match.group(1)
            class_indent, member_start = self.require_child_indent(index + 1, indent, line_no)
            init_method: Optional[FunctionDefStmt] = None
            methods: list[FunctionDefStmt] = []

            current = member_start
            while current < len(self.lines):
                member_no, member_raw = self.lines[current]
                if member_raw.strip() == "":
                    current += 1
                    continue
                member_indent = self.count_indent(member_raw, member_no)
                if member_indent < class_indent:
                    break
                if member_indent > class_indent:
                    raise SyntaxTppError("Indentation looks incorrect inside class body.", member_no)

                member_text = member_raw.strip()
                init_match = re.match(r"^when\s+created\s+with\s+(.+):$", member_text, re.IGNORECASE)
                if init_match:
                    if init_method is not None:
                        raise SyntaxTppError("Class constructor is already defined.", member_no)
                    params, _, _ = self.parse_typed_params(init_match.group(1).strip(), member_no)
                    init_body, after_init = self.parse_child_block(current + 1, class_indent, member_no)
                    init_method = FunctionDefStmt(line=member_no, name="__init__", params=params, body=init_body)
                    current = after_init
                    continue

                method_stmt = self.parse_function_statement(member_text, current, class_indent)
                if method_stmt is not None:
                    method_node, after_method = method_stmt
                    methods.append(method_node)
                    current = after_method
                    continue

                raise SyntaxTppError(
                    "Inside a class, I only understand 'when created ...' and 'define ...'.",
                    member_no,
                )

            return ClassDefStmt(line=line_no, name=class_name, init_method=init_method, methods=methods), current

        remember_match = re.match(r"^remember\s+([A-Za-z_][A-Za-z0-9_]*)$", text, re.IGNORECASE)
        if remember_match:
            return RememberStmt(line=line_no, name=remember_match.group(1)), index + 1

        if text.lower().startswith("call ") or text.lower().startswith("run "):
            return ExprStmt(line=line_no, expr=text), index + 1

        raise self.build_unknown_statement_error(text, line_no)

    def parse_match_statement(self, text: str, index: int, indent: int) -> Optional[tuple[Any, int]]:
        match_head = re.match(r"^match\s+(.+?)(?:\s+as)?:\s*$", text, re.IGNORECASE)
        if not match_head:
            return None
        line_no = self.lines[index][0]
        expr = match_head.group(1).strip()
        cases: list[MatchWhenClause] = []
        otherwise_body: Optional[list[Any]] = None

        child_indent, curr_idx = self.require_child_indent(index + 1, indent, line_no)
        while curr_idx < len(self.lines):
            peek = self.peek_next_non_blank(curr_idx)
            if peek is None:
                break
            p_idx, p_no, p_text, p_indent = peek
            if p_indent < child_indent:
                break
            if p_indent != child_indent:
                raise SyntaxTppError("Inconsistent indentation in match cases.", p_no)

            # 'when <pattern> [if <guard>]:'
            when_match = re.match(r"^when\s+(.+?)(?:\s+if\s+(.+?))?(?:\s+then)?:\s*$", p_text, re.IGNORECASE)
            if when_match:
                pat = when_match.group(1).strip()
                guard = when_match.group(2).strip() if when_match.group(2) else None
                case_body, curr_idx = self.parse_child_block(p_idx + 1, p_indent, p_no)
                cases.append(MatchWhenClause(line=p_no, pattern=pat, body=case_body, guard_expr=guard))
                continue

            if re.match(r"^(?:otherwise|else):\s*$", p_text, re.IGNORECASE):
                otherwise_body, curr_idx = self.parse_child_block(p_idx + 1, p_indent, p_no)
                break

            raise SyntaxTppError(f"Expected 'when <pattern>:' or 'otherwise:' in match block, got '{p_text}'.", p_no)

        if not cases and otherwise_body is None:
            raise SyntaxTppError("Match block must contain at least one 'when' clause.", line_no)

        return MatchStmt(line=line_no, expr=expr, cases=cases, otherwise_body=otherwise_body), curr_idx

    def parse_function_statement(self, text: str, index: int, indent: int) -> Optional[tuple[FunctionDefStmt, int]]:
        line_no = self.lines[index][0]

        # 1. 'define <name> with <params> [, giving back <type>] [as]:'
        fn_as_match = re.match(
            r"^define\s+([A-Za-z_][A-Za-z0-9_]*)\s+with\s+(.+?)(?:,\s*giving\s+back\s+(.+?))?(?:\s+as)?:$",
            text,
            re.IGNORECASE,
        )
        if fn_as_match:
            fn_name = fn_as_match.group(1)
            raw_params = fn_as_match.group(2).strip()
            raw_ret = fn_as_match.group(3).strip() if fn_as_match.group(3) else None
            params, p_types, p_defaults = self.parse_typed_params(raw_params, line_no)
            ret_type = parse_type_annotation(raw_ret, line_no) if raw_ret else None
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return (
                FunctionDefStmt(
                    line=line_no,
                    name=fn_name,
                    params=params,
                    body=body,
                    return_type=ret_type,
                    param_types=p_types,
                    param_defaults=p_defaults,
                ),
                next_index,
            )

        # 2. 'define function <name> with <params> [, giving back <type>]:'
        function_with_match = re.match(
            r"^define\s+function\s+([A-Za-z_][A-Za-z0-9_]*)\s+with\s+(.+?)(?:,\s*giving\s+back\s+(.+?))?:$",
            text,
            re.IGNORECASE,
        )
        if function_with_match:
            fn_name = function_with_match.group(1)
            raw_params = function_with_match.group(2).strip()
            raw_ret = function_with_match.group(3).strip() if function_with_match.group(3) else None
            params, p_types, p_defaults = self.parse_typed_params(raw_params, line_no)
            ret_type = parse_type_annotation(raw_ret, line_no) if raw_ret else None
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return (
                FunctionDefStmt(
                    line=line_no,
                    name=fn_name,
                    params=params,
                    body=body,
                    return_type=ret_type,
                    param_types=p_types,
                    param_defaults=p_defaults,
                ),
                next_index,
            )

        # 3. 'define <name> that takes <params>:'
        takes_match = re.match(
            r"^define\s+([A-Za-z_][A-Za-z0-9_]*)\s+that\s+takes\s+(.+):$",
            text,
            re.IGNORECASE,
        )
        if takes_match:
            params, p_types, p_defaults = self.parse_typed_params(takes_match.group(2).strip(), line_no)
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return (
                FunctionDefStmt(
                    line=line_no,
                    name=takes_match.group(1),
                    params=params,
                    body=body,
                    param_types=p_types,
                    param_defaults=p_defaults,
                ),
                next_index,
            )

        # 4. 'define function <name>:'
        function_plain_match = re.match(r"^define\s+function\s+([A-Za-z_][A-Za-z0-9_]*):$", text, re.IGNORECASE)
        if function_plain_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return FunctionDefStmt(line=line_no, name=function_plain_match.group(1), params=[], body=body), next_index

        # 5. 'define <name> with no inputs:'
        no_inputs_match = re.match(
            r"^define\s+([A-Za-z_][A-Za-z0-9_]*)\s+with\s+no\s+inputs:$",
            text,
            re.IGNORECASE,
        )
        if no_inputs_match:
            body, next_index = self.parse_child_block(index + 1, indent, line_no)
            return FunctionDefStmt(line=line_no, name=no_inputs_match.group(1), params=[], body=body), next_index

        return None

    def parse_typed_params(
        self,
        params_text: str,
        line_no: int,
    ) -> tuple[list[str], dict[str, TypeAnnotation | UnionTypeAnnotation], dict[str, str]]:
        lowered = params_text.lower()
        if lowered in {"no inputs", "nothing"}:
            return [], {}, {}

        raw_parts = split_natural_args(params_text)
        params: list[str] = []
        param_types: dict[str, TypeAnnotation | UnionTypeAnnotation] = {}
        param_defaults: dict[str, str] = {}

        for part in raw_parts:
            # Pattern: '<name> as <type> defaulting to <default>'
            p_match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)(?:\s+as\s+(.+?))?(?:\s+defaulting\s+to\s+(.+))?$",
                part.strip(),
                re.IGNORECASE,
            )
            if p_match:
                name = p_match.group(1)
                type_str = p_match.group(2)
                default_str = p_match.group(3)
                if not is_identifier(name):
                    raise SyntaxTppError(f"'{name}' is not a valid parameter name.", line_no)
                params.append(name)
                if type_str:
                    ann = parse_type_annotation(type_str.strip(), line_no)
                    if ann:
                        param_types[name] = ann
                if default_str:
                    param_defaults[name] = default_str.strip()
            else:
                if not is_identifier(part.strip()):
                    raise SyntaxTppError(f"'{part.strip()}' is not a valid parameter name.", line_no)
                params.append(part.strip())

        return params, param_types, param_defaults

    def parse_param_text(self, params_text: str, line_no: int) -> list[str]:
        params, _, _ = self.parse_typed_params(params_text, line_no)
        return params

    def parse_child_block(self, index: int, parent_indent: int, header_line: int) -> tuple[list[Any], int]:
        child_indent, child_start = self.require_child_indent(index, parent_indent, header_line)
        return self.parse_block(child_start, child_indent)

    def require_child_indent(self, index: int, parent_indent: int, header_line: int) -> tuple[int, int]:
        next_info = self.peek_next_non_blank(index)
        if next_info is None:
            if self.config.repl_mode:
                raise IncompleteBlockError("I expected an indented block after ':'.", header_line)
            raise SyntaxTppError("I expected an indented block after ':'.", header_line)

        next_index, next_line, _next_text, next_indent = next_info
        if next_indent <= parent_indent:
            if self.config.repl_mode:
                raise IncompleteBlockError("I expected an indented block after ':'.", header_line)
            raise SyntaxTppError(
                "Indentation looks incorrect here. Expected an indented block.",
                next_line,
                suggestion="Indent the block by at least one level.",
            )
        return next_indent, next_index

    def peek_next_non_blank(self, index: int) -> Optional[tuple[int, int, str, int]]:
        current = index
        while current < len(self.lines):
            line_no, raw = self.lines[current]
            stripped = raw.strip()
            if stripped == "" or stripped.startswith("#"):
                current += 1
                continue
            indent = self.count_indent(raw, line_no)
            return current, line_no, stripped, indent
        return None

    @staticmethod
    def count_indent(raw: str, line_no: int) -> int:
        if "\t" in raw:
            raise SyntaxTppError(
                "Indentation looks incorrect here. Use spaces instead of tabs.",
                line_no,
                suggestion="Replace tab characters with spaces.",
            )
        return len(raw) - len(raw.lstrip(" "))

    def try_parse_register_keyword(self, text: str, line_no: int) -> Optional[RegisterKeywordStmt]:
        register_match = re.match(r"^register\s+keyword\s+(.+?)(?:\s+as\s+(.+))?$", text, re.IGNORECASE)
        if not register_match:
            return None

        phrase_raw = register_match.group(1).strip()
        template_raw = register_match.group(2).strip() if register_match.group(2) else None

        phrase = parse_quoted_string(phrase_raw, line_no, "Keyword phrase")
        template = parse_quoted_string(template_raw, line_no, "Keyword template") if template_raw else None
        return RegisterKeywordStmt(line=line_no, phrase=phrase, template=template)

    def try_parse_fuzzy_statement(self, text: str, line_no: int) -> Optional[Any]:
        if not self.fuzzy_mode:
            return None

        is_like_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+is\s+like\s+(.+)$", text, re.IGNORECASE)
        if is_like_match:
            return SmartAssignStmt(line=line_no, name=is_like_match.group(1), expr=is_like_match.group(2).strip())

        increase_match = re.match(r"^increase\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", text, re.IGNORECASE)
        if increase_match:
            name = increase_match.group(1)
            return ChangeStmt(line=line_no, name=name, expr=f"{name} plus ({increase_match.group(2).strip()})")

        decrease_match = re.match(r"^decrease\s+([A-Za-z_][A-Za-z0-9_]*)\s+by\s+(.+)$", text, re.IGNORECASE)
        if decrease_match:
            name = decrease_match.group(1)
            return ChangeStmt(line=line_no, name=name, expr=f"{name} minus ({decrease_match.group(2).strip()})")

        smaller_match = re.match(r"^make\s+([A-Za-z_][A-Za-z0-9_]*)\s+smaller$", text, re.IGNORECASE)
        if smaller_match:
            name = smaller_match.group(1)
            return ChangeStmt(line=line_no, name=name, expr=f"{name} minus 1")

        bigger_match = re.match(r"^make\s+([A-Za-z_][A-Za-z0-9_]*)\s+(?:bigger|larger)$", text, re.IGNORECASE)
        if bigger_match:
            name = bigger_match.group(1)
            return ChangeStmt(line=line_no, name=name, expr=f"{name} plus 1")

        if self.intent_mode:
            assign_match = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", text)
            if assign_match:
                return SmartAssignStmt(line=line_no, name=assign_match.group(1), expr=assign_match.group(2).strip())

        return None

    def apply_plugin_rewrites(self, text: str, line_no: int) -> str:
        current = text
        for _ in range(DEFAULT_REWRITE_LIMIT):
            rewritten = self.apply_single_plugin_rewrite(current)
            if rewritten == current:
                return current
            current = rewritten
        raise SyntaxTppError("Plugin rewrite recursion detected.", line_no)

    def apply_single_plugin_rewrite(self, text: str) -> str:
        lowered = normalize_phrase(text)
        for phrase in self._plugin_phrases_sorted:
            if not self._starts_with_phrase(lowered, phrase):
                continue
            template = self.plugin_rewrites[phrase]

            phrase_words = phrase.split()
            raw_words = text.strip().split()
            if len(raw_words) < len(phrase_words):
                continue
            rest = " ".join(raw_words[len(phrase_words) :]).strip()
            if "{rest}" in template or "{0}" in template:
                res = template.replace("{rest}", rest).replace("{0}", rest)
                return res.strip()
            return f"{template} {rest}".strip()
        return text

    @staticmethod
    def _starts_with_phrase(text: str, phrase: str) -> bool:
        if not text.startswith(phrase):
            return False
        if len(text) == len(phrase):
            return True
        return text[len(phrase)].isspace() or text[len(phrase)] in ":("

    def build_unknown_statement_error(self, text: str, line_no: int) -> SyntaxTppError:
        stripped = text.strip()
        lowered = stripped.lower()

        for phrase in sorted(self.plugin_keywords, key=len, reverse=True):
            if self._starts_with_phrase(lowered, phrase) and phrase not in self.plugin_rewrites:
                return SyntaxTppError(
                    f"Keyword '{phrase}' is registered but has no behavior.",
                    line_no,
                    suggestion="Register it with: register keyword \"...\" as \"...\"",
                    source_line=text,
                    file_path=self.file_path,
                )

        if "=" in stripped and all(op not in stripped for op in ("==", "!=", ">=", "<=")):
            return SyntaxTppError(
                "I expected natural assignment words.",
                line_no,
                suggestion="Try 'let name be value' or 'change name to value'.",
                source_line=text,
                file_path=self.file_path,
            )

        parts = stripped.split()
        first_word = parts[0].lower() if parts else ""

        starters = self.statement_starters()
        suggestion = suggest_closest(first_word, starters)
        if suggestion:
            return SyntaxTppError(
                f"I don't understand '{first_word}'.",
                line_no,
                suggestion=f"Did you mean '{suggestion}'?",
                source_line=text,
                file_path=self.file_path,
            )

        assignment_shape = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s+.+$", stripped)
        if assignment_shape and first_word not in starters:
            variable = assignment_shape.group(1)
            return SyntaxTppError(
                f"I don't understand '{stripped}'.",
                line_no,
                fix_preview=f"let {variable} be ...",
                source_line=text,
                file_path=self.file_path,
            )

        return SyntaxTppError(
            f"I don't understand '{stripped}'.",
            line_no,
            source_line=text,
            file_path=self.file_path,
        )

    def statement_starters(self) -> set[str]:
        starters = set(CORE_STATEMENT_STARTERS)
        starters.update({"use", "export", "try", "handle", "finally", "raise", "throw", "import", "from"})
        for phrase in self.plugin_keywords:
            if phrase:
                starters.add(phrase.split()[0])
        return starters
