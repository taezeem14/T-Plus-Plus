from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class Token:
    kind: str
    value: str
    line: int
    col: int


@dataclass
class Program:
    statements: list[Any]


# --- Type System AST Nodes (Part 3) ---

@dataclass
class TypeAnnotation:
    line: int
    name: str  # "number", "whole number", "text", "boolean", "nothing", "list", "record", "function", or custom
    is_optional: bool = False
    element_type: Optional[TypeAnnotation] = None
    param_types: Optional[list[TypeAnnotation]] = None
    return_type: Optional[TypeAnnotation] = None

    def __str__(self) -> str:
        if self.name == "list" and self.element_type:
            res = f"a list of {self.element_type}"
        elif self.name == "function" and self.return_type:
            params_str = " and ".join(str(p) for p in (self.param_types or []))
            res = f"a function that takes {params_str} and gives back {self.return_type}"
        elif self.name in {"number", "whole number", "boolean", "record", "list"}:
            res = f"a {self.name}"
        else:
            res = self.name
        if self.is_optional and not res.endswith("or nothing"):
            res += " or nothing"
        return res


@dataclass
class UnionTypeAnnotation:
    line: int
    types: list[TypeAnnotation]

    def __str__(self) -> str:
        return " or ".join(str(t) for t in self.types)


@dataclass
class RecordTypeDefStmt:
    line: int
    name: str
    parent_type: Optional[str] = None
    fields: list[tuple[str, Optional[TypeAnnotation | UnionTypeAnnotation], Optional[str]]] = field(default_factory=list)


# --- Module & Package AST Nodes (Part 10) ---

@dataclass
class ImportModuleStmt:
    line: int
    module: str
    alias: Optional[str] = None


@dataclass
class ImportFromStmt:
    line: int
    name: str
    module: str
    alias: Optional[str] = None


@dataclass
class UseModuleStmt:
    line: int
    module: str
    alias: Optional[str] = None


@dataclass
class UseFromModuleStmt:
    line: int
    module: str
    names: list[tuple[str, Optional[str]]] = field(default_factory=list)


@dataclass
class ExportStmt:
    line: int
    statement: Any


# --- Error Handling AST Nodes (Part 12 & Part 1) ---

@dataclass
class HandleClause:
    line: int
    error_type: Optional[str]  # None means "any error"
    var_name: str
    body: list[Any]


@dataclass
class TryStmt:
    line: int
    body: list[Any]
    handlers: list[HandleClause]
    finally_body: Optional[list[Any]] = None


@dataclass
class RaiseStmt:
    line: int
    expr: str


# --- Core Language Statements ---

@dataclass
class SayStmt:
    line: int
    parts: list[str]


@dataclass
class AskStmt:
    line: int
    target: str
    prompt_expr: Optional[str]


@dataclass
class LetStmt:
    line: int
    name: str
    expr: str
    type_annotation: Optional[TypeAnnotation | UnionTypeAnnotation] = None


@dataclass
class SmartAssignStmt:
    line: int
    name: str
    expr: str


@dataclass
class ChangeStmt:
    line: int
    name: str
    expr: str


@dataclass
class IfStmt:
    line: int
    branches: list[tuple[str, list[Any]]]
    else_body: list[Any]


@dataclass
class WhileStmt:
    line: int
    condition: str
    body: list[Any]


@dataclass
class ForEachStmt:
    line: int
    var_name: str
    iterable_expr: str
    body: list[Any]
    index_var: Optional[str] = None


@dataclass
class RepeatStmt:
    line: int
    count_expr: str
    body: list[Any]


@dataclass
class CountStmt:
    line: int
    var_name: str
    start_expr: str
    end_expr: str
    body: list[Any]


@dataclass
class BreakStmt:
    line: int


@dataclass
class ContinueStmt:
    line: int


@dataclass
class PassStmt:
    line: int


@dataclass
class FunctionDefStmt:
    line: int
    name: str
    params: list[str]
    body: list[Any]
    return_type: Optional[TypeAnnotation | UnionTypeAnnotation] = None
    param_types: dict[str, TypeAnnotation | UnionTypeAnnotation] = field(default_factory=dict)
    param_defaults: dict[str, str] = field(default_factory=dict)


@dataclass
class ReturnStmt:
    line: int
    expr: Optional[str]


@dataclass
class ExprStmt:
    line: int
    expr: str


@dataclass
class AddToStmt:
    line: int
    value_expr: str
    target_name: str
    force_set: bool


@dataclass
class RemoveFromStmt:
    line: int
    value_expr: str
    target_name: str
    force_set: bool


@dataclass
class DictSetStmt:
    line: int
    key_expr: str
    map_name: str
    value_expr: str


@dataclass
class ClassDefStmt:
    line: int
    name: str
    init_method: Optional[FunctionDefStmt]
    methods: list[FunctionDefStmt]


@dataclass
class RememberStmt:
    line: int
    name: str


# --- Testing AST Nodes ---

@dataclass
class TestStmt:
    line: int
    name: str
    body: list[Any]
    expected_error: Optional[str] = None  # for 'test "..." expecting an error' or expecting <ErrorType>


@dataclass
class TestSuiteStmt:
    line: int
    name: str
    tests: list[TestStmt]


@dataclass
class ExpectEqualStmt:
    line: int
    left_expr: str
    right_expr: str


@dataclass
class ExpectTypeStmt:
    line: int
    expr: str
    expected_type: str


@dataclass
class ExpectRangeStmt:
    line: int
    expr: str
    low_expr: str
    high_expr: str


# --- Extension & GUI AST Nodes ---

@dataclass
class RegisterKeywordStmt:
    line: int
    phrase: str
    template: Optional[str]


@dataclass
class DescribeStmt:
    line: int
    description: str


@dataclass
class CreateWindowStmt:
    line: int
    title_expr: str
    window_name: Optional[str]


@dataclass
class SetWindowSizeStmt:
    line: int
    width_expr: str
    height_expr: str
    window_name: Optional[str]


@dataclass
class CreateButtonStmt:
    line: int
    label_expr: str
    button_name: Optional[str]
    window_name: Optional[str]


@dataclass
class OnButtonClickStmt:
    line: int
    button_name: Optional[str]
    body: list[Any]


@dataclass
class ShowWindowStmt:
    line: int
    window_name: Optional[str]


# --- Pattern Matching AST Nodes (Part 2) ---

@dataclass
class MatchWhenClause:
    line: int
    pattern: str
    body: list[Any]
    guard_expr: Optional[str] = None


@dataclass
class MatchStmt:
    line: int
    expr: str
    cases: list[MatchWhenClause]
    otherwise_body: Optional[list[Any]] = None
