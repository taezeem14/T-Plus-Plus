from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Optional

from tpp.core.constants import VERSION
from tpp.core.errors import IncompleteBlockError, render_error
from tpp.runtime.engine import EngineConfig, RuntimeEngine
from tpp.runtime.environment import Scope


class ReplStyle:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"


def _paint(text: str, color: str) -> str:
    if os.getenv("NO_COLOR") or not sys.stdout.isatty():
        return text
    return f"{color}{text}{ReplStyle.RESET}"


class ReplSession:
    def __init__(self, engine: Optional[RuntimeEngine] = None, history_file: Optional[Path] = None) -> None:
        self.engine = engine or RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
        self.history_file = history_file or (Path.cwd() / ".tpp_history")
        self.buffer: list[str] = []

    def _setup_history(self) -> None:
        try:
            import readline
            if self.history_file.exists():
                readline.read_history_file(self.history_file)
        except Exception:
            pass

    def _save_history(self) -> None:
        try:
            import readline
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            readline.write_history_file(self.history_file)
        except Exception:
            pass

    def print_banner(self) -> None:
        print(_paint(f"T++ Interactive Shell v{VERSION}", ReplStyle.BOLD))
        print(_paint("Type ':help' or ':?' for commands, ':quit' or 'exit' to exit.\n", ReplStyle.DIM))

    def handle_meta_command(self, cmd_line: str) -> bool:
        """Handles commands starting with ':' or 'exit'. Returns True if handled, False to continue."""
        raw = cmd_line.strip()
        if raw.lower() in {"exit", "quit", ":quit", ":q", ":exit"}:
            return True

        if raw in {":help", ":?", ":h"}:
            self.print_help()
            return False

        if raw.startswith(":type "):
            expr = raw[6:].strip()
            self.cmd_type(expr)
            return False

        if raw.startswith(":doc "):
            symbol = raw[5:].strip()
            self.cmd_doc(symbol)
            return False

        if raw in {":env", ":vars", ":scope"}:
            self.cmd_env()
            return False

        if raw.startswith(":load "):
            file_path = raw[6:].strip()
            self.cmd_load(file_path)
            return False

        if raw in {":clear", ":reset"}:
            self.cmd_clear()
            return False

        print(_paint(f"Unknown meta-command '{raw}'. Type ':help' for available commands.", ReplStyle.YELLOW))
        return False

    def print_help(self) -> None:
        print(_paint("--- T++ REPL Commands ---", ReplStyle.BOLD))
        print(f"  {_paint(':type <expr>', ReplStyle.CYAN):<25} Inspect type and evaluated value of an expression")
        print(f"  {_paint(':doc <symbol>', ReplStyle.CYAN):<25} Show documentation/info for a function or module")
        print(f"  {_paint(':env / :vars', ReplStyle.CYAN):<25} List all bound variables in the current session")
        print(f"  {_paint(':load <file>', ReplStyle.CYAN):<25} Load and execute a .tpp file into this session")
        print(f"  {_paint(':clear', ReplStyle.CYAN):<25} Reset interactive session scope")
        print(f"  {_paint(':help / :?', ReplStyle.CYAN):<25} Display this help reference")
        print(f"  {_paint(':quit / :exit', ReplStyle.CYAN):<25} Exit the REPL")
        print(_paint("-------------------------", ReplStyle.DIM))

    def cmd_type(self, expr: str) -> None:
        if not expr:
            print(_paint("Usage: :type <expression>", ReplStyle.YELLOW))
            return
        try:
            val = self.engine.evaluate_expression(expr, self.engine.global_scope, line=1)
            t_name = type(val).__name__
            print(f"{_paint(expr, ReplStyle.BOLD)} : {_paint(t_name, ReplStyle.GREEN)} = {val!r}")
        except Exception as exc:
            print(_paint(render_error(exc, debug_trace=self.engine.config.debug_trace), ReplStyle.RED))

    def cmd_doc(self, symbol: str) -> None:
        if not symbol:
            print(_paint("Usage: :doc <symbol>", ReplStyle.YELLOW))
            return

        # Check native stdlib
        for mod_name, mod in self.engine.native_stdlib.items():
            if symbol == mod_name:
                print(_paint(f"Native Stdlib Module '{mod_name}'", ReplStyle.BOLD))
                print(f"Members: {', '.join(sorted(mod.members))}")
                return
            if mod.has_member(symbol):
                member = mod.member(symbol)
                doc = getattr(member, "__doc__", None) or "Native standard library member."
                print(_paint(f"{mod_name}.{symbol}", ReplStyle.BOLD))
                print(f"Documentation: {doc}")
                return

        # Check session scope
        if symbol in self.engine.global_scope.values:
            val = self.engine.global_scope.values[symbol]
            val_type = type(val).__name__
            print(f"{_paint(symbol, ReplStyle.BOLD)} ({val_type}) = {val!r}")
            return

        print(_paint(f"No documentation found for symbol '{symbol}'.", ReplStyle.YELLOW))

    def cmd_env(self) -> None:
        items = self.engine.global_scope.values
        if not items:
            print(_paint("No variables currently defined in session.", ReplStyle.DIM))
            return

        print(_paint(f"--- Scope ({len(items)} bindings) ---", ReplStyle.BOLD))
        for k in sorted(items.keys()):
            v = items[k]
            print(f"  {_paint(k, ReplStyle.CYAN)} ({type(v).__name__}) = {v!r}")

    def cmd_load(self, file_path_str: str) -> None:
        p = Path(file_path_str.strip("\"'"))
        if not p.exists():
            print(_paint(f"File '{p}' does not exist.", ReplStyle.RED))
            return
        try:
            source = p.read_text(encoding="utf-8")
            self.engine.run_source(source, file_path=str(p.resolve()))
            print(_paint(f"Loaded and executed '{p}' successfully.", ReplStyle.GREEN))
        except Exception as exc:
            print(_paint(render_error(exc, debug_trace=self.engine.config.debug_trace), ReplStyle.RED))

    def cmd_clear(self) -> None:
        self.engine.global_scope = Scope()
        self.buffer.clear()
        print(_paint("Session scope cleared.", ReplStyle.GREEN))

    def run_interactive(self) -> int:
        self._setup_history()
        self.print_banner()

        while True:
            prompt = _paint(">> ", ReplStyle.CYAN) if not self.buffer else _paint(".. ", ReplStyle.YELLOW)
            try:
                line = input(prompt)
            except (EOFError, KeyboardInterrupt):
                print()
                self._save_history()
                return 0

            stripped = line.strip()
            if not self.buffer and (stripped.startswith(":") or stripped.lower() in {"exit", "quit"}):
                should_exit = self.handle_meta_command(stripped)
                if should_exit:
                    self._save_history()
                    return 0
                continue

            if not self.buffer and stripped == "":
                continue

            self.buffer.append(line)
            source = "\n".join(self.buffer)

            # Auto-detect multiline block header
            if stripped.endswith(":") and len(self.buffer) == 1:
                continue

            try:
                self.engine.run_source(source, repl_mode=True)
            except IncompleteBlockError:
                continue
            except Exception as exc:
                print(_paint(render_error(exc, debug_trace=self.engine.config.debug_trace), ReplStyle.RED))
                self.buffer.clear()
                continue

            self.buffer.clear()


def run_repl(engine: Optional[RuntimeEngine] = None) -> int:
    session = ReplSession(engine=engine)
    return session.run_interactive()
