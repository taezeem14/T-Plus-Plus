from __future__ import annotations

import pytest
from tpp.runtime import EngineConfig, RuntimeEngine


def test_string_interpolation() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let name be \"Alice\"\n"
        "let greeting be \"Hello, {name}!\"\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("greeting", 1) == "Hello, Alice!"


def test_list_and_filter_comprehensions() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let numbers be a list containing 1 and 2 and 3 and 4 and 5\n"
        "let doubled be a list containing x times 2 for each x in numbers if x is greater than 2\n"
        "let evens be the items in numbers where item % 2 == 0\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("doubled", 1) == [6, 8, 10]
    assert engine.global_scope.get("evens", 1) == [2, 4]


def test_record_literal_and_possessive_access() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let person be a record with name as \"Ana\" and age as 30\n"
        "let ana_age be person's age\n"
        "let ana_name be person.name\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("person", 1) == {"name": "Ana", "age": 30}
    assert engine.global_scope.get("ana_age", 1) == 30
    assert engine.global_scope.get("ana_name", 1) == "Ana"


def test_range_literal() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let r1 be 1 to 5\n"
        "let r2 be 1 to 9 by 2\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("r1", 1) == [1, 2, 3, 4, 5]
    assert engine.global_scope.get("r2", 1) == [1, 3, 5, 7, 9]


def test_match_statement() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "define describe_num with n as:\n"
        "    let result be \"\"\n"
        "    match n:\n"
        "        when 0:\n"
        "            change result to \"zero\"\n"
        "        when 1:\n"
        "            change result to \"one\"\n"
        "        when x if x is greater than 10:\n"
        "            change result to \"large\"\n"
        "        otherwise:\n"
        "            change result to \"other\"\n"
        "    give back result\n"
        "let r0 be call describe_num with 0\n"
        "let r1 be call describe_num with 1\n"
        "let r_large be call describe_num with 50\n"
        "let r_other be call describe_num with 5\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("r0", 1) == "zero"
    assert engine.global_scope.get("r1", 1) == "one"
    assert engine.global_scope.get("r_large", 1) == "large"
    assert engine.global_scope.get("r_other", 1) == "other"


def test_repeat_until_and_loop_synonyms() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let i be 0\n"
        "repeat until i is at least 5:\n"
        "    increase i by 1\n"
        "let stopped be 0\n"
        "while true:\n"
        "    increase stopped by 1\n"
        "    if stopped is equal to 3:\n"
        "        stop the loop\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("i", 1) == 5
    assert engine.global_scope.get("stopped", 1) == 3


def test_is_between_operator() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let x be 5\n"
        "let in_range be x is between 1 and 10\n"
        "let out_range be x is between 10 and 20\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("in_range", 1) is True
    assert engine.global_scope.get("out_range", 1) is False
