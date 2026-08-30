from __future__ import annotations

from pathlib import Path
from io import StringIO
import sys
import pytest

from tpp.cli.repl import ReplSession
from tpp.runtime import EngineConfig, RuntimeEngine


def test_repl_handle_meta_commands(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    session = ReplSession()

    # :help
    assert session.handle_meta_command(":help") is False
    captured = capsys.readouterr()
    assert "T++ REPL Commands" in captured.out

    # :type
    session.handle_meta_command(":type 10 + 20")
    captured = capsys.readouterr()
    assert "int" in captured.out

    # :doc
    session.handle_meta_command(":doc math")
    captured = capsys.readouterr()
    assert "Native Stdlib Module 'math'" in captured.out

    # :env
    session.engine.global_scope.define("user_count", 42)
    session.handle_meta_command(":env")
    captured = capsys.readouterr()
    assert "user_count" in captured.out

    # :load
    script = tmp_path / "load_test.tpp"
    script.write_text("let from_file be 999\n", encoding="utf-8")
    session.handle_meta_command(f":load {script}")
    assert session.engine.global_scope.get("from_file", 1) == 999

    # :clear
    session.handle_meta_command(":clear")
    assert "from_file" not in session.engine.global_scope.values

    # :quit
    assert session.handle_meta_command(":quit") is True
    assert session.handle_meta_command("exit") is True
