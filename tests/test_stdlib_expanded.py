from __future__ import annotations

from pathlib import Path
import pytest

from tpp.core.errors import SecurityTppError
from tpp.runtime import EngineConfig, RuntimeEngine


def test_math_module() -> None:
    engine = RuntimeEngine(EngineConfig())
    source = (
        "use average and median and is_prime and square_root from \"math\"\n"
        "let nums be a list containing 10 and 20 and 30\n"
        "let avg be call average with nums\n"
        "let med be call median with nums\n"
        "let prime_check be call is_prime with 17\n"
        "let not_prime be call is_prime with 18\n"
        "let sq be call square_root with 49\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("avg", 1) == 20.0
    assert engine.global_scope.get("med", 1) == 20.0
    assert engine.global_scope.get("prime_check", 1) is True
    assert engine.global_scope.get("not_prime", 1) is False
    assert engine.global_scope.get("sq", 1) == 7.0


def test_text_module() -> None:
    engine = RuntimeEngine(EngineConfig())
    source = (
        "use trimmed and uppercase and format_currency and matches_pattern from \"text\"\n"
        "let cleaned be call trimmed with \"  hello world  \"\n"
        "let upp be call uppercase with cleaned\n"
        "let curr be call format_currency with 1234.5\n"
        "let is_alpha be call matches_pattern with \"abc123\" and \"^[a-z0-9]+$\"\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("cleaned", 1) == "hello world"
    assert engine.global_scope.get("upp", 1) == "HELLO WORLD"
    assert engine.global_scope.get("curr", 1) == "$1,234.50"
    assert engine.global_scope.get("is_alpha", 1) is True


def test_collections_module() -> None:
    engine = RuntimeEngine(EngineConfig())
    source = (
        "use unique_items and chunk_items and flatten from \"collections\"\n"
        "let dupes be a list containing 1 and 2 and 2 and 3 and 1\n"
        "let uniq be call unique_items with dupes\n"
        "let chunks be call chunk_items with uniq and 2\n"
        "let flat be call flatten with chunks\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("uniq", 1) == [1, 2, 3]
    assert engine.global_scope.get("chunks", 1) == [[1, 2], [3]]
    assert engine.global_scope.get("flat", 1) == [1, 2, 3]


def test_json_and_validate_modules() -> None:
    engine = RuntimeEngine(EngineConfig())
    source = (
        "use parse_json and to_json from \"json\"\n"
        "use is_valid_email and is_within_range from \"validate\"\n"
        "let obj be call parse_json with '{\"key\": 42}'\n"
        "let ser be call to_json with obj\n"
        "let valid_mail be call is_valid_email with \"user@example.com\"\n"
        "let invalid_mail be call is_valid_email with \"not-an-email\"\n"
        "let in_bounds be call is_within_range with 5 and 1 and 10\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("obj", 1) == {"key": 42}
    assert "key" in engine.global_scope.get("ser", 1)
    assert engine.global_scope.get("valid_mail", 1) is True
    assert engine.global_scope.get("invalid_mail", 1) is False
    assert engine.global_scope.get("in_bounds", 1) is True


def test_system_module_sandboxing(tmp_path: Path) -> None:
    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    source_safe = (
        "use write_file and read_file and file_exists from \"system\"\n"
        "let write_res be call write_file with \"output.txt\" and \"Hello Sandboxed World\"\n"
        "let exists_res be call file_exists with \"output.txt\"\n"
        "let read_res be call read_file with \"output.txt\"\n"
    )
    engine.run_source(source_safe)
    assert engine.global_scope.get("exists_res", 1) is True
    assert engine.global_scope.get("read_res", 1) == "Hello Sandboxed World"

    # Test Path Traversal rejection
    source_traversal = (
        "use read_file from \"system\"\n"
        "let secret be call read_file with \"../../etc/passwd\"\n"
    )
    with pytest.raises(SecurityTppError) as exc_info:
        engine.run_source(source_traversal)
    assert "outside workspace sandbox" in str(exc_info.value)
