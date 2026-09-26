from __future__ import annotations

import pytest
from tpp.api import execute_json_request
from tpp.core.errors import KeyNotFoundTppError, SecurityTppError
from tpp.runtime import EngineConfig, RuntimeEngine


def test_multiline_statements() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let items be [\n"
        "    1,\n"
        "    2,\n"
        "    3\n"
        "]\n"
        "let person be {\n"
        '    "name": "Bob",\n'
        "    \"age\": 25\n"
        "}\n"
        "let total be 10 + \\\n"
        "    20 + \\\n"
        "    30\n"
        "let commented be [\n"
        "    100, # first item\n"
        "    200  # second item\n"
        "]\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("items", 1) == [1, 2, 3]
    assert engine.global_scope.get("person", 1) == {"name": "Bob", "age": 25}
    assert engine.global_scope.get("total", 1) == 60
    assert engine.global_scope.get("commented", 1) == [100, 200]


def test_string_interpolation_and_escaping() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let count be 42\n"
        'let msg be "count is {count}, escaped: {{literal}}"\n'
        'let quote be "it\'s a wonderful day"\n'
        'let text_between be "score is between 10 and 20"\n'
    )
    engine.run_source(source)
    assert engine.global_scope.get("msg", 1) == "count is 42, escaped: {literal}"
    assert engine.global_scope.get("quote", 1) == "it's a wonderful day"
    assert engine.global_scope.get("text_between", 1) == "score is between 10 and 20"


def test_multiple_is_between() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let a be 3\n"
        "let b be 15\n"
        "let in_range be a is between 1 and 5 and b is between 10 and 20\n"
        "let out_range be a is between 10 and 20 and b is between 10 and 20\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("in_range", 1) is True
    assert engine.global_scope.get("out_range", 1) is False


def test_dictionary_access_and_modification() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        'let user be a record with name as "Alice" and age as 30\n'
        'set user["city"] to "Wonderland"\n'
        'set user.hobby to "reading"\n'
        'change user["age"] to 31\n'
        'change user.name to "Bob"\n'
        'set the status of user to "active"\n'
    )
    engine.run_source(source)
    user = engine.global_scope.get("user", 1)
    assert user["city"] == "Wonderland"
    assert user["hobby"] == "reading"
    assert user["age"] == 31
    assert user["name"] == "Bob"
    assert user["status"] == "active"


def test_dict_key_not_found_error() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        'let person be a record with name as "Alice"\n'
        "let x be person.missing_key\n"
    )
    with pytest.raises(KeyNotFoundTppError):
        engine.run_source(source)


def test_security_attribute_blocked() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        'let s be "hello"\n'
        "let danger be s.__class__\n"
    )
    with pytest.raises(SecurityTppError):
        engine.run_source(source)


def test_pattern_matching_expanded() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "let r_bool be 0\n"
        "match false:\n"
        "    when true:\n"
        "        change r_bool to 1\n"
        "    when false:\n"
        "        change r_bool to 2\n"
        "\n"
        'let r_type be ""\n'
        "match 42:\n"
        "    when a text:\n"
        '        change r_type to "text"\n'
        "    when a number:\n"
        '        change r_type to "number"\n'
        "\n"
        'let r_typed_bind be ""\n'
        'match "hello world":\n'
        "    when val as a text:\n"
        "        change r_typed_bind to val\n"
        "\n"
        'let r_or be ""\n'
        'match "yes":\n'
        '    when "y" or "yes":\n'
        '        change r_or to "confirmed"\n'
        "\n"
        "let r_empty be false\n"
        "match []:\n"
        "    when []:\n"
        "        change r_empty to true\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("r_bool", 1) == 2
    assert engine.global_scope.get("r_type", 1) == "number"
    assert engine.global_scope.get("r_typed_bind", 1) == "hello world"
    assert engine.global_scope.get("r_or", 1) == "confirmed"
    assert engine.global_scope.get("r_empty", 1) is True


def test_exception_propagation_and_signals() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        "define compute with x as a number, giving back a number as:\n"
        "    try:\n"
        "        if x is greater than 0:\n"
        "            give back x times 2\n"
        "        give back 0\n"
        "    handle any error as e:\n"
        "        give back -1\n"
        "let res be call compute with 10\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("res", 1) == 20

    # Finally executes even when return occurs
    source_finally = (
        "let fin_flag be false\n"
        "define test_fin with no inputs:\n"
        "    try:\n"
        "        give back 99\n"
        "    finally:\n"
        "        change fin_flag to true\n"
        "let res_fin be call test_fin with no inputs\n"
    )
    engine.run_source(source_finally)
    assert engine.global_scope.get("res_fin", 1) == 99
    assert engine.global_scope.get("fin_flag", 1) is True


def test_stdlib_crypto_and_text_hash() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        'use base64_encode and base64_decode and hash_sha256 and hash_md5 from "text"\n'
        'let enc be call base64_encode with "hello world"\n'
        "let dec be call base64_decode with enc\n"
        'let h256 be call hash_sha256 with "hello world"\n'
        'let hmd5 be call hash_md5 with "hello world"\n'
        'use sha256 from "crypto"\n'
        'let h_crypto be call sha256 with "hello world"\n'
    )
    engine.run_source(source)
    assert engine.global_scope.get("dec", 1) == "hello world"
    assert engine.global_scope.get("h256", 1) == engine.global_scope.get("h_crypto", 1)
    assert len(engine.global_scope.get("h256", 1)) == 64
    assert len(engine.global_scope.get("hmd5", 1)) == 32


def test_stdlib_math_and_collections_expanded() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    source = (
        'use variance and standard_deviation and clamp and factorial and gcd and lcm from "math"\n'
        "let v be call variance with [10, 20, 30]\n"
        "let sd be call standard_deviation with [10, 20, 30]\n"
        "let clamped be call clamp with 15 and 0 and 10\n"
        "let f be call factorial with 5\n"
        "let g be call gcd with 24 and 36\n"
        "let l be call lcm with 4 and 6\n"
        'use sample and shuffle and first and last and count_occurrences from "collections"\n'
        "let items be [1, 2, 3, 4, 5]\n"
        "let sampled be call sample with items and 3\n"
        "let shuffled be call shuffle with items\n"
        "let f_item be call first with items\n"
        "let l_item be call last with items\n"
        "let count_2 be call count_occurrences with [1, 2, 2, 3] and 2\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("v", 1) == 100.0
    assert abs(engine.global_scope.get("sd", 1) - 10.0) < 1e-9
    assert engine.global_scope.get("clamped", 1) == 10
    assert engine.global_scope.get("f", 1) == 120
    assert engine.global_scope.get("g", 1) == 12
    assert engine.global_scope.get("l", 1) == 12
    assert len(engine.global_scope.get("sampled", 1)) == 3
    assert sorted(engine.global_scope.get("shuffled", 1)) == [1, 2, 3, 4, 5]
    assert engine.global_scope.get("f_item", 1) == 1
    assert engine.global_scope.get("l_item", 1) == 5
    assert engine.global_scope.get("count_2", 1) == 2


def test_json_api_expanded() -> None:
    # 1. AST mode
    ast_res = execute_json_request({
        "mode": "ast",
        "source": "let x be 10 plus 20",
    })
    assert ast_res["ok"] is True
    assert "ast" in ast_res
    assert ast_res["ast"]["type"] == "Program"

    # 2. Check mode
    check_res = execute_json_request({
        "mode": "check",
        "source": "let x be 10\nlet y be x plus 2\n",
    })
    assert check_res["ok"] is True
    assert "diagnostics" in check_res
    assert len(check_res["diagnostics"]) == 0

    # 3. Format mode
    fmt_res = execute_json_request({
        "mode": "format",
        "source": "LET   x   BE   42\n",
    })
    assert fmt_res["ok"] is True
    assert "formatted" in fmt_res
    assert fmt_res["formatted"] == "let x BE 42\n"

    # 4. Run mode with variables and initial_scope
    run_res = execute_json_request({
        "mode": "run",
        "source": "let y be x times 3\nlet msg be \"hello\"",
        "initial_scope": {"x": 7},
        "return_ast": True,
        "return_formatted": True,
    })
    assert run_res["ok"] is True
    assert run_res["scope"]["x"] == 7
    assert run_res["scope"]["y"] == 21
    assert run_res["scope"]["msg"] == "hello"
    assert "ast" in run_res
    assert "formatted" in run_res
