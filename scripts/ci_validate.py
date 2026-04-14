from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = REPO_ROOT / ".ci-artifacts"
ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)


def _slug(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", text.strip()).strip("-").lower() or "step"


def _command_prefix() -> list[str]:
    exe = shutil.which("tpp")
    if exe:
        return [exe]
    raise RuntimeError("tpp console script not found on PATH after installation")


def _run_step(
    title: str,
    command: list[str],
    *,
    input_text: str | None = None,
    expected_output: str | None = None,
) -> None:
    print(f"::group::{title}")
    print("$", " ".join(shlex.quote(part) for part in command))

    env = os.environ.copy()
    env.setdefault("NO_COLOR", "1")
    env.setdefault("PYTHONUTF8", "1")

    result = subprocess.run(
        command,
        cwd=REPO_ROOT,
        text=True,
        input=input_text,
        capture_output=True,
        check=False,
        env=env,
    )

    merged = (result.stdout or "") + (result.stderr or "")
    log_file = ARTIFACT_DIR / f"{_slug(title)}.log"
    log_file.write_text(merged, encoding="utf-8")

    print(merged)
    print(f"exit_code={result.returncode}")
    print("::endgroup::")

    if result.returncode != 0:
        raise RuntimeError(f"Step '{title}' failed with exit code {result.returncode}")

    if expected_output and expected_output not in merged:
        raise RuntimeError(f"Step '{title}' output did not contain expected text: {expected_output!r}")


def main() -> int:
    tpp = _command_prefix()
    plugin_dir = ARTIFACT_DIR / "plugins"
    if plugin_dir.exists():
        shutil.rmtree(plugin_dir)
    plugin_dir.mkdir(parents=True, exist_ok=True)

    _run_step("tpp --version", tpp + ["--version"], expected_output="T++ Interpreter")
    _run_step(
        "tpp run examples/hello.tpp",
        tpp + ["run", "examples/hello.tpp"],
        expected_output="Hello from T++",
    )
    _run_step(
        "tpp run examples/math.tpp",
        tpp + ["run", "examples/math.tpp"],
        expected_output="add",
    )
    _run_step(
        "tpp test tests/regression.tpp",
        tpp + ["test", "tests/regression.tpp"],
        expected_output="Overall test summary",
    )
    _run_step(
        "tpp plugin install",
        tpp + ["plugin", "install", "examples/sample_plugin.json", "--to", str(plugin_dir)],
        expected_output="Installed plugin",
    )
    _run_step(
        "tpp plugin list",
        tpp + ["plugin", "list", "--dir", str(plugin_dir)],
        expected_output="sample_plugin.json",
    )
    _run_step("tpp doctor", tpp + ["doctor"], expected_output="T++ Doctor")
    _run_step(
        "tpp repl scripted input",
        tpp + ["repl"],
        input_text="let x be 5\nsay x\nexit\n",
        expected_output="5",
    )

    summary_file = ARTIFACT_DIR / "summary.txt"
    summary_file.write_text("T++ CI validation completed successfully.\n", encoding="utf-8")
    print("T++ CI validation completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
