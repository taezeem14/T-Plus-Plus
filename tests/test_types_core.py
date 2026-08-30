from __future__ import annotations

import pytest

from tpp.core.ast_nodes import TypeAnnotation, UnionTypeAnnotation
from tpp.core.errors import TypeTppError
from tpp.core.types import (
    NOTHING,
    TppNothing,
    check_type_or_raise,
    is_value_compatible_with_type,
    parse_type_annotation,
)
from tpp.runtime import EngineConfig, RuntimeEngine


def test_parse_type_annotations() -> None:
    t_num = parse_type_annotation("a number")
    assert isinstance(t_num, TypeAnnotation) and t_num.name == "number"

    t_int = parse_type_annotation("a whole number")
    assert isinstance(t_int, TypeAnnotation) and t_int.name == "whole number"

    t_text = parse_type_annotation("text")
    assert isinstance(t_text, TypeAnnotation) and t_text.name == "text"

    t_bool = parse_type_annotation("a boolean")
    assert isinstance(t_bool, TypeAnnotation) and t_bool.name == "boolean"

    t_opt = parse_type_annotation("a number or nothing")
    assert isinstance(t_opt, UnionTypeAnnotation)
    assert len(t_opt.types) == 2

    t_list = parse_type_annotation("a list of a number")
    assert isinstance(t_list, TypeAnnotation)
    assert t_list.name == "list" and t_list.element_type is not None and t_list.element_type.name == "number"

    t_fn = parse_type_annotation("a function that takes a number and a number and gives back a number")
    assert isinstance(t_fn, TypeAnnotation)
    assert t_fn.name == "function" and len(t_fn.param_types or []) == 2


def test_type_compatibility() -> None:
    t_num = parse_type_annotation("a number")
    assert is_value_compatible_with_type(5, t_num)
    assert is_value_compatible_with_type(5.5, t_num)
    assert not is_value_compatible_with_type("5", t_num)
    assert not is_value_compatible_with_type(True, t_num)  # bool should not satisfy number

    t_int = parse_type_annotation("a whole number")
    assert is_value_compatible_with_type(5, t_int)
    assert not is_value_compatible_with_type(5.5, t_int)
    assert not is_value_compatible_with_type(5.0, t_int)  # strict reject float

    t_text = parse_type_annotation("text")
    assert is_value_compatible_with_type("hello", t_text)
    assert not is_value_compatible_with_type(123, t_text)

    t_bool = parse_type_annotation("a boolean")
    assert is_value_compatible_with_type(True, t_bool)
    assert is_value_compatible_with_type(False, t_bool)
    assert not is_value_compatible_with_type(1, t_bool)

    t_union = parse_type_annotation("a number or nothing")
    assert is_value_compatible_with_type(42, t_union)
    assert is_value_compatible_with_type(None, t_union)
    assert is_value_compatible_with_type(NOTHING, t_union)
    assert not is_value_compatible_with_type("abc", t_union)


def test_untyped_script_runs_identically() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let x be 4\n"
        "increase x by 6\n"
        "change x to \"now text\"\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("x", 1) == "now text"


def test_enforce_types_let() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy", enforce_types=True))
    source_valid = "let x be 42 as a whole number\n"
    engine.run_source(source_valid)
    assert engine.global_scope.get("x", 1) == 42

    source_invalid = "let y be \"hello\" as a number\n"
    with pytest.raises(TypeTppError) as exc_info:
        engine.run_source(source_invalid)
    assert "Type mismatch" in str(exc_info.value)


def test_typed_function_call_and_return() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy", enforce_types=True))
    source = (
        "define add with a as a number and b as a number, giving back a number as:\n"
        "    give back a plus b\n"
        "let result be call add with 10 and 20\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("result", 1) == 30

    source_bad_param = (
        "define add with a as a number and b as a number as:\n"
        "    give back a plus b\n"
        "let bad be call add with \"invalid\" and 20\n"
    )
    with pytest.raises(TypeTppError):
        engine.run_source(source_bad_param)


def test_typed_function_defaults() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "define greet with name as text defaulting to \"World\" as:\n"
        "    give back name\n"
        "let default_val be call greet\n"
        "let custom_val be call greet with \"Alice\"\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("default_val", 1) == "World"
    assert engine.global_scope.get("custom_val", 1) == "Alice"
