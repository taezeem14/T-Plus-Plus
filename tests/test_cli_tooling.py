from __future__ import annotations

import json
from pathlib import Path
import pytest

from tpp.cli.main import main


def test_cli_check_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    valid_file = tmp_path / "valid.tpp"
    valid_file.write_text("let x be 10\nlet y be x plus 2\n", encoding="utf-8")

    code = main(["tpp", "check", str(valid_file)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Syntax and semantics are valid" in captured.out

    invalid_file = tmp_path / "invalid.tpp"
    invalid_file.write_text("let x be\n", encoding="utf-8")

    code_err = main(["tpp", "check", str(invalid_file)])
    assert code_err == 1


def test_cli_fmt_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    unformatted = tmp_path / "unformatted.tpp"
    unformatted.write_text("LET   x   BE   42\n", encoding="utf-8")

    # Check mode
    code_check = main(["tpp", "fmt", str(unformatted), "--check"])
    assert code_check == 1

    # Write mode
    code_write = main(["tpp", "fmt", str(unformatted)])
    assert code_write == 0
    content = unformatted.read_text(encoding="utf-8")
    assert content == "let x BE 42\n"

    # Second check should pass
    code_check2 = main(["tpp", "fmt", str(unformatted), "--check"])
    assert code_check2 == 0


def test_cli_doc_command(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # Test stdlib doc
    code_stdlib = main(["tpp", "doc", "math"])
    assert code_stdlib == 0
    captured = capsys.readouterr()
    assert "Standard Library: `math`" in captured.out

    # Test file doc
    script = tmp_path / "math_helper.tpp"
    script.write_text(
        "# Math Helper Module\n"
        "# Provides utility functions.\n"
        "define add_five with x as a number, giving back a number as:\n"
        "    give back x plus 5\n",
        encoding="utf-8",
    )
    code_file = main(["tpp", "doc", str(script)])
    assert code_file == 0
    captured = capsys.readouterr()
    assert "Math Helper Module" in captured.out
    assert "define add_five" in captured.out


def test_cli_test_runner_extensions(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    test_file = tmp_path / "sample_test.tpp"
    test_file.write_text(
        "test \"first test\":\n"
        "    expect 2 + 2 to be 4\n"
        "test \"second test\":\n"
        "    expect 3 * 3 to be 9\n",
        encoding="utf-8",
    )

    # Test JSON output
    code_json = main(["tpp", "test", str(test_file), "--json"])
    assert code_json == 0
    captured = capsys.readouterr()
    parsed_json = json.loads(captured.out)
    assert len(parsed_json) == 2
    assert parsed_json[0]["name"] == "first test"
    assert parsed_json[0]["passed"] is True

    # Test JUnit output
    junit_report = tmp_path / "junit.xml"
    code_junit = main(["tpp", "test", str(test_file), "--junit", str(junit_report)])
    assert code_junit == 0
    assert junit_report.exists()
    junit_content = junit_report.read_text(encoding="utf-8")
    assert '<testsuite name="TPPTests" tests="2" failures="0"' in junit_content
    capsys.readouterr()

    # Test filter
    code_filter = main(["tpp", "test", str(test_file), "--filter", "first", "--json"])
    assert code_filter == 0
    captured_filter = capsys.readouterr()
    parsed_filter = json.loads(captured_filter.out)
    assert len(parsed_filter) == 1
    assert parsed_filter[0]["name"] == "first test"
