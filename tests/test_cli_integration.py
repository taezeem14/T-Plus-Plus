from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _tpp_command_prefix() -> list[str]:
    exe = shutil.which("tpp")
    if exe:
        return [exe]
    return [sys.executable, "-m", "tpp"]


def _run_tpp(args: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("PYTHONUTF8", "1")

    return subprocess.run(
        _tpp_command_prefix() + args,
        cwd=REPO_ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        env=env,
    )


def _output(result: subprocess.CompletedProcess[str]) -> str:
    return (result.stdout or "") + (result.stderr or "")


def test_version_command() -> None:
    result = _run_tpp(["--version"])
    assert result.returncode == 0, _output(result)
    assert "T++ Interpreter" in _output(result)


def test_run_examples() -> None:
    hello = _run_tpp(["run", "examples/hello.tpp"])
    assert hello.returncode == 0, _output(hello)
    assert "Hello from T++" in _output(hello)

    math = _run_tpp(["run", "examples/math.tpp"])
    assert math.returncode == 0, _output(math)
    assert "add" in _output(math)


def test_regression_suite() -> None:
    result = _run_tpp(["test", "tests/regression.tpp"])
    assert result.returncode == 0, _output(result)
    assert "Overall test summary" in _output(result)


def test_plugin_install_and_list(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir(parents=True, exist_ok=True)

    install = _run_tpp(["plugin", "install", "examples/sample_plugin.json", "--to", str(plugin_dir)])
    assert install.returncode == 0, _output(install)

    listed = _run_tpp(["plugin", "list", "--dir", str(plugin_dir)])
    assert listed.returncode == 0, _output(listed)
    assert "sample_plugin.json" in _output(listed)


def test_repl_scripted_input_accepts_exit() -> None:
    result = _run_tpp(["repl"], input_text="let x be 5\nsay x\nexit\n")
    assert result.returncode == 0, _output(result)
    assert "5" in _output(result)


def test_doctor_command() -> None:
    result = _run_tpp(["doctor"])
    assert result.returncode == 0, _output(result)
    assert "T++ Doctor" in _output(result)
