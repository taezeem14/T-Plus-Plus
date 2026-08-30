from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

from tpp import __version__
from tpp.api import ApiServerConfig, serve_api
from tpp.api.json_api import execute_json_payload_text
from tpp.core.errors import IncompleteBlockError, render_error
from tpp.parser.semantic import SemanticAnalyzer, SemanticConfig
from tpp.plugins import PluginManager
from tpp.runtime.engine import EngineConfig, RuntimeEngine


GLOBAL_PLUGIN_DIR = Path.home() / ".tpp" / "plugins"
CONFIG_FILE = ".tppconfig"


class CliStyle:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"


def _supports_color() -> bool:
    if os.getenv("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


def _paint(text: str, color: str) -> str:
    if not _supports_color():
        return text
    return f"{color}{text}{CliStyle.RESET}"


def _print_info(message: str) -> None:
    print(_paint("[info]", CliStyle.CYAN), message)


def _print_ok(message: str) -> None:
    print(_paint("[ok]", CliStyle.GREEN), message)


def _print_warn(message: str) -> None:
    print(_paint("[warn]", CliStyle.YELLOW), message)


def _print_error(message: str) -> None:
    print(_paint("[error]", CliStyle.RED), message)


def _print_runtime_banner() -> None:
    divider = _paint("-" * 64, CliStyle.DIM)
    print(divider)
    print(_paint(f"T++ Runtime v{__version__}", CliStyle.BOLD))
    print("© Muhammad Taezeem Tariq Matta")
    print("Source: https://github.com/taezeem14/T-Plus-Plus")
    print(divider)


def _load_config_file() -> dict[str, Any]:
    path = Path.cwd() / CONFIG_FILE
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        _print_warn(f"Could not parse {CONFIG_FILE}: {exc}")
        return {}

    if not isinstance(data, dict):
        _print_warn(f"{CONFIG_FILE} must be a JSON object. Ignoring it.")
        return {}

    return data


def _as_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    return default


def _as_list_of_str(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    result: list[str] = []
    for item in value:
        if isinstance(item, str) and item.strip():
            result.append(item.strip())
    return result


def _resolve_plugin_path(plugin_ref: str) -> Optional[Path]:
    candidate = Path(plugin_ref)
    if candidate.exists():
        return candidate.resolve()

    if candidate.suffix.lower() != ".json":
        with_json = Path(f"{plugin_ref}.json")
        if with_json.exists():
            return with_json.resolve()
        candidate = with_json

    local = Path.cwd() / candidate.name
    if local.exists():
        return local.resolve()

    global_candidate = GLOBAL_PLUGIN_DIR / candidate.name
    if global_candidate.exists():
        return global_candidate.resolve()

    return None


def _collect_plugin_refs(args: argparse.Namespace, config: dict[str, Any]) -> list[str]:
    config_plugins = _as_list_of_str(config.get("plugins"))
    arg_plugins = list(getattr(args, "plugin", []) or [])

    seen: set[str] = set()
    merged: list[str] = []
    for plugin_ref in config_plugins + arg_plugins:
        if plugin_ref in seen:
            continue
        seen.add(plugin_ref)
        merged.append(plugin_ref)
    return merged


def _create_engine(args: argparse.Namespace, config: Optional[dict[str, Any]] = None) -> RuntimeEngine:
    config = config or {}

    parser_mode = str(config.get("parser_mode", "fuzzy"))
    if getattr(args, "strict_fuzzy", False):
        parser_mode = "strict"
    if getattr(args, "intent_mode", False):
        parser_mode = "intent"

    debug_trace = bool(getattr(args, "debug_trace", False))
    profiling = bool(getattr(args, "profile", False))

    strict_semantic = bool(getattr(args, "strict_semantic_resolution", False))
    if not strict_semantic:
        strict_semantic = _as_bool(config.get("strict_semantic_resolution"), False)

    enforce_types = bool(getattr(args, "enforce_types", False)) or bool(getattr(args, "strict_types", False))
    if not enforce_types:
        enforce_types = _as_bool(config.get("enforce_types"), False) or _as_bool(config.get("strict_types"), False)

    strict_types = bool(getattr(args, "strict_types", False))
    if not strict_types:
        strict_types = _as_bool(config.get("strict_types"), False)

    no_python_bridge = bool(getattr(args, "no_python_bridge", False))
    if not no_python_bridge:
        no_python_bridge = _as_bool(config.get("no_python_bridge"), False)

    engine = RuntimeEngine(
        EngineConfig(
            parser_mode=parser_mode,
            debug_trace=debug_trace,
            profiling=profiling,
            strict_semantic_resolution=strict_semantic,
            enforce_types=enforce_types,
            strict_types=strict_types,
            allow_python_bridge=not no_python_bridge,
        )
    )

    plugin_refs = _collect_plugin_refs(args, config)
    for plugin_ref in plugin_refs:
        resolved = _resolve_plugin_path(plugin_ref)
        if resolved is None:
            raise FileNotFoundError(
                f"Plugin '{plugin_ref}' was not found in current directory or {GLOBAL_PLUGIN_DIR}"
            )
        engine.load_plugin(str(resolved))

    return engine


def _run_source_text(engine: RuntimeEngine, source: str, *, repl_mode: bool = False) -> int:
    try:
        engine.run_source(source, repl_mode=repl_mode)
    except Exception as exc:
        _print_error(render_error(exc, debug_trace=engine.config.debug_trace))
        return 1

    if engine.config.profiling:
        print(engine.profiler.report())
    return 0


def _run_file(engine: RuntimeEngine, file_path: str, *, show_banner: bool = True) -> int:
    path = Path(file_path)
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        _print_error(f"Could not read file '{path}': {exc}")
        return 1

    if show_banner and path.suffix.lower() == ".tpp":
        _print_runtime_banner()

    code = _run_source_text(engine, source)
    if code == 0:
        _print_ok(f"Executed {path}")
    return code


def _run_pipe(engine: RuntimeEngine) -> int:
    source = sys.stdin.read()
    if not source.strip():
        return 0
    return _run_source_text(engine, source)


def _run_repl_script(engine: RuntimeEngine, scripted_input: str) -> int:
    buffer: list[str] = []

    for line in scripted_input.splitlines():
        if not buffer and line.strip().lower() == "exit":
            return 0

        if not buffer and line.strip() == "":
            continue

        buffer.append(line)
        source = "\n".join(buffer)

        try:
            engine.run_source(source, repl_mode=True)
        except IncompleteBlockError:
            continue
        except Exception as exc:
            _print_error(render_error(exc, debug_trace=engine.config.debug_trace))
            return 1

        buffer.clear()

    if buffer:
        try:
            engine.run_source("\n".join(buffer), repl_mode=True)
        except Exception as exc:
            _print_error(render_error(exc, debug_trace=engine.config.debug_trace))
            return 1

    return 0


def _setup_repl_history(history_path: Path) -> None:
    try:
        import readline

        if history_path.exists():
            readline.read_history_file(history_path)
    except Exception:
        return


def _save_repl_history(history_path: Path) -> None:
    try:
        import readline

        history_path.parent.mkdir(parents=True, exist_ok=True)
        readline.write_history_file(history_path)
    except Exception:
        return


def _run_repl(engine: RuntimeEngine) -> int:
    from tpp.cli.repl import ReplSession
    session = ReplSession(engine=engine)
    return session.run_interactive()


def _run_doctor(_args: argparse.Namespace, config: dict[str, Any]) -> int:
    failures = 0
    warnings = 0

    def run_check(label: str, check: Any, *, required: bool = True) -> None:
        nonlocal failures, warnings
        try:
            details = check()
        except Exception as exc:
            if required:
                failures += 1
                _print_error(f"{label}: {exc}")
            else:
                warnings += 1
                _print_warn(f"{label}: {exc}")
            return

        _print_ok(f"{label}: {details}")

    def check_python() -> str:
        min_version = (3, 10)
        if sys.version_info < min_version:
            raise RuntimeError(f"Python >= {min_version[0]}.{min_version[1]} is required")
        return f"Python {platform.python_version()} on {platform.system()}"

    def check_console_script() -> str:
        script = shutil.which("tpp")
        if script is not None:
            return script

        argv0 = Path(sys.argv[0])
        if argv0.name.lower().startswith("tpp") and argv0.exists():
            return str(argv0.resolve())

        raise RuntimeError("Console script was not found on PATH. Run: pip install .")

    def check_engine_health() -> str:
        engine = RuntimeEngine(EngineConfig(parser_mode=str(config.get("parser_mode", "fuzzy"))))
        engine.parse_source('let x be 1\nsay x')
        return "Runtime parser and semantic analyzer loaded"

    def check_api_health() -> str:
        payload = {"mode": "run", "source": "let x be 2\nsay x"}
        output = execute_json_payload_text(json.dumps(payload))
        data = json.loads(output)
        if not data.get("ok", False):
            raise RuntimeError(data.get("error", "JSON API execution failed"))
        return "JSON API execution path is healthy"

    def check_webide_asset() -> str:
        asset = Path(__file__).resolve().parents[1] / "api" / "webide" / "index.html"
        if not asset.exists():
            raise RuntimeError(f"Missing web IDE asset: {asset}")
        return str(asset)

    def check_plugin_dir() -> str:
        GLOBAL_PLUGIN_DIR.mkdir(parents=True, exist_ok=True)
        probe = GLOBAL_PLUGIN_DIR / ".doctor-write-test"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
        return str(GLOBAL_PLUGIN_DIR)

    def check_config_plugins() -> str:
        refs = _as_list_of_str(config.get("plugins"))
        for plugin_ref in refs:
            if _resolve_plugin_path(plugin_ref) is None:
                raise RuntimeError(f"Configured plugin not found: {plugin_ref}")
        return f"{len(refs)} configured plugins resolved"

    def check_optional_modules() -> str:
        missing: list[str] = []
        for module_name in ("readline", "tkinter"):
            try:
                __import__(module_name)
            except Exception:
                missing.append(module_name)
        if missing:
            raise RuntimeError(f"Optional modules not available: {', '.join(missing)}")
        return "readline and tkinter available"

    print(_paint(f"T++ Doctor v{__version__}", CliStyle.BOLD))

    run_check("Python runtime", check_python, required=True)
    run_check("Console script", check_console_script, required=False)
    run_check("Runtime engine", check_engine_health, required=True)
    run_check("JSON API", check_api_health, required=True)
    run_check("Web IDE assets", check_webide_asset, required=True)
    run_check("Plugin directory", check_plugin_dir, required=True)
    run_check("Config plugins", check_config_plugins, required=True)
    run_check("Optional dependencies", check_optional_modules, required=False)

    if failures:
        _print_error(f"Doctor found {failures} required issue(s) and {warnings} warning(s).")
        return 1

    if warnings:
        _print_warn(f"Doctor finished with {warnings} warning(s).")
        return 0

    _print_ok("Doctor finished with no issues.")
    return 0


def _discover_test_files(base: Path) -> list[Path]:
    direct = sorted(base.glob("*.tpp"))
    in_tests = sorted((base / "tests").glob("*.tpp")) if (base / "tests").exists() else []
    seen: set[Path] = set()
    files: list[Path] = []
    for file_path in direct + in_tests:
        resolved = file_path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        files.append(file_path)
    return files


def _run_check(args: argparse.Namespace, config: dict[str, Any]) -> int:
    path = Path(args.file)
    if not path.exists():
        _print_error(f"File '{path}' does not exist.")
        return 1
    try:
        source = path.read_text(encoding="utf-8")
        engine = _create_engine(args, config)
        program = engine.parse_source(source, file_path=str(path.resolve()))
        analyzer = SemanticAnalyzer(SemanticConfig(strict_types=getattr(args, "strict_types", False)))
        analyzer.analyze(program)
        _print_ok(f"Syntax and semantics are valid for {path}")
        return 0
    except Exception as exc:
        _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
        return 1


def _run_fmt(args: argparse.Namespace) -> int:
    from tpp.tools.formatter import format_file
    path = Path(args.file)
    if not path.exists():
        _print_error(f"File '{path}' does not exist.")
        return 1

    check_only = getattr(args, "check", False)
    is_modified, _ = format_file(path, check_only=check_only)
    if check_only:
        if is_modified:
            _print_warn(f"File '{path}' would be reformatted.")
            return 1
        _print_ok(f"File '{path}' is correctly formatted.")
        return 0

    if is_modified:
        _print_ok(f"Formatted {path}")
    else:
        _print_info(f"File '{path}' is already formatted.")
    return 0


def _run_doc(args: argparse.Namespace) -> int:
    from tpp.tools.docgen import generate_docs_for_source, generate_docs_for_stdlib
    target_path = Path(args.target)
    if target_path.exists() and target_path.is_file():
        source = target_path.read_text(encoding="utf-8")
        doc = generate_docs_for_source(source, title=target_path.stem)
    else:
        doc = generate_docs_for_stdlib(args.target)

    output_path = getattr(args, "output", None)
    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(doc, encoding="utf-8")
        _print_ok(f"Documentation written to {out_p}")
        return 0

    print(doc)
    return 0


def _run_lsp(args: argparse.Namespace) -> int:
    from tpp.lsp.server import run_lsp_server
    return run_lsp_server(stdio=getattr(args, "stdio", True), port=getattr(args, "port", None))


def _run_test_mode(args: argparse.Namespace, config: dict[str, Any]) -> int:
    file_paths = [Path(args.file)] if getattr(args, "file", None) else _discover_test_files(Path.cwd())
    if not file_paths:
        _print_error("No .tpp files found for testing.")
        return 1

    total_passed = 0
    total_failed = 0
    files_with_tests = 0
    all_results: list[Any] = []
    filter_pat = getattr(args, "filter_pattern", None)

    for file_path in file_paths:
        try:
            source = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            _print_error(f"Could not read file '{file_path}': {exc}")
            total_failed += 1
            continue

        try:
            engine = _create_engine(args, config)
            program = engine.parse_source(source)
        except Exception as exc:
            _print_error(f"{file_path}: {render_error(exc, debug_trace=getattr(args, 'debug_trace', False))}")
            total_failed += 1
            continue

        tests = engine.collect_tests(program)
        if not tests:
            continue

        if filter_pat:
            tests = [t for t in tests if filter_pat.lower() in t.name.lower()]
            if not tests:
                continue

        files_with_tests += 1
        results, passed, failed = engine.run_tests(program, verbose=False, filter_pattern=filter_pat)
        all_results.extend(results)

        if getattr(args, "as_json", False):
            continue

        if getattr(args, "test_verbose", False):
            for result in results:
                badge = _paint("PASS", CliStyle.GREEN) if result.passed else _paint("FAIL", CliStyle.RED)
                print(f"[{badge}] {result.name} ({result.duration_ms:.1f} ms)")
                if result.details:
                    print(f"       {result.details}")
        else:
            summary = _paint(f"{passed} passed", CliStyle.GREEN)
            failed_text = _paint(f"{failed} failed", CliStyle.RED if failed else CliStyle.GREEN)
            print(f"{file_path}: {summary}, {failed_text}")

        total_passed += passed
        total_failed += failed

    if getattr(args, "as_json", False):
        import dataclasses
        print(json.dumps([dataclasses.asdict(r) for r in all_results], indent=2))
        return 0 if total_failed == 0 else 1

    junit_path = getattr(args, "junit", None)
    if junit_path:
        _write_junit_report(all_results, Path(junit_path))
        _print_ok(f"Wrote JUnit test report to {junit_path}")

    if files_with_tests == 0:
        _print_warn('No test blocks found. Add tests with: test "name":')
        return 1

    total_line = f"Overall test summary: {total_passed} passed, {total_failed} failed"
    if total_failed:
        _print_error(total_line)
    else:
        _print_ok(total_line)
    return 0 if total_failed == 0 else 1


def _write_junit_report(results: list[Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    total = len(results)
    failures = sum(1 for r in results if not r.passed)
    total_time = sum(r.duration_ms for r in results) / 1000.0
    xml_lines.append(f'<testsuite name="TPPTests" tests="{total}" failures="{failures}" time="{total_time:.3f}">')
    for r in results:
        time_s = r.duration_ms / 1000.0
        xml_lines.append(f'  <testcase name="{r.name}" time="{time_s:.3f}">')
        if not r.passed:
            det = r.details or "Test assertion failed."
            xml_lines.append(f'    <failure message="Assertion Failed">{det}</failure>')
        xml_lines.append("  </testcase>")
    xml_lines.append("</testsuite>")
    output_path.write_text("\n".join(xml_lines), encoding="utf-8")


def _run_manifest(args: argparse.Namespace, config: dict[str, Any]) -> int:
    try:
        engine = _create_engine(args, config)
    except Exception as exc:
        _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
        return 1

    print(json.dumps(engine.manifest(), indent=2))
    return 0


def _run_api_payload(args: argparse.Namespace) -> int:
    if args.payload_file:
        payload_text = Path(args.payload_file).read_text(encoding="utf-8")
    else:
        payload_text = sys.stdin.read()

    if not payload_text.strip():
        _print_error("API mode expects JSON payload via stdin or --payload-file")
        return 1

    try:
        output = execute_json_payload_text(payload_text)
    except Exception as exc:
        _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
        return 1

    print(output)
    return 0


def _run_api_command(args: argparse.Namespace) -> int:
    should_serve = bool(args.serve)
    if not should_serve and not args.payload_file and sys.stdin.isatty():
        should_serve = True

    if should_serve:
        try:
            serve_api(ApiServerConfig(host=args.host, port=args.port))
            return 0
        except Exception as exc:
            _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
            return 1

    return _run_api_payload(args)


def _run_plugin_command(args: argparse.Namespace) -> int:
    manager = PluginManager()
    install_dir = Path(getattr(args, "to", None) or GLOBAL_PLUGIN_DIR)

    if args.plugin_action == "install":
        try:
            target_path = manager.install_plugin(args.source, install_dir)
        except Exception as exc:
            _print_error(render_error(exc))
            return 1
        _print_ok(f"Installed plugin to {target_path}")
        return 0

    if args.plugin_action == "list":
        directory = Path(args.dir or GLOBAL_PLUGIN_DIR)
        if not directory.exists():
            _print_warn(f"No plugin directory found at {directory}")
            return 0
        items = sorted(directory.glob("*.json"))
        if not items:
            _print_warn(f"No plugins found in {directory}")
            return 0
        for file_path in items:
            print(file_path.name)
        return 0

    _print_error("Unknown plugin action")
    return 1


def _run_bench(args: argparse.Namespace) -> int:
    try:
        from tests.perf.benchmarks import run_benchmark_suite, save_baseline
    except ImportError:
        _print_error("Benchmark suite could not be imported.")
        return 1

    _print_info("Running T++ performance benchmark suite...")
    results = run_benchmark_suite()

    if getattr(args, "save_baseline", None):
        save_baseline(results, Path(args.save_baseline))
        _print_ok(f"Saved baseline to {args.save_baseline}")

    if getattr(args, "as_json", False):
        import dataclasses
        print(json.dumps([dataclasses.asdict(r) for r in results], indent=2))
        return 0

    divider = "-" * 64
    print(divider)
    print(f"{'Benchmark Name':<28} {'Avg Duration':<16} {'Throughput':<16}")
    print(divider)
    for r in results:
        print(f"{r.name:<28} {r.avg_ms:>8.2f} ms/run   {r.ops_per_sec:>8.1f} ops/sec")
    print(divider)
    _print_ok("Benchmark suite completed successfully.")
    return 0


def _build_modern_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tpp", description="T++ language platform")
    parser.add_argument("--version", action="store_true", help="Print version")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--plugin", action="append", default=[], help="Load plugin JSON file")
    common.add_argument("--strict-fuzzy", action="store_true", dest="strict_fuzzy", help="Disable fuzzy mode")
    common.add_argument("--intent-mode", action="store_true", help="Enable intent parser mode")
    common.add_argument("--debug-trace", action="store_true", help="Show internal stack traces")
    common.add_argument("--profile", action="store_true", help="Show execution profiling summary")
    common.add_argument("--strict-semantic-resolution", action="store_true", help="Enable strict variable resolution")
    common.add_argument("--strict-types", action="store_true", help="Enable strict type checking mode")
    common.add_argument("--enforce-types", action="store_true", help="Enforce runtime type checking")
    common.add_argument("--no-python-bridge", action="store_true", help="Disable Python interop imports")

    sub = parser.add_subparsers(dest="command")

    run_parser = sub.add_parser("run", parents=[common], help="Run a T++ file")
    run_parser.add_argument("file", help="T++ source file")
    run_parser.add_argument("--no-banner", action="store_true", help="Disable runtime credit banner")

    repl_parser = sub.add_parser("repl", parents=[common], help="Start interactive shell")
    repl_parser.set_defaults(command="repl")

    test_parser = sub.add_parser("test", parents=[common], help="Run tests")
    test_parser.add_argument("file", nargs="?", help="Optional T++ test file")
    test_parser.add_argument("--test-verbose", action="store_true", help="Verbose test output")
    test_parser.add_argument("--json", action="store_true", dest="as_json", help="Output test results as JSON")
    test_parser.add_argument("--junit", help="Path to write JUnit XML test report")
    test_parser.add_argument("--filter", dest="filter_pattern", help="Filter tests by name pattern")

    check_parser = sub.add_parser("check", parents=[common], help="Statically check syntax and types")
    check_parser.add_argument("file", help="T++ source file to check")

    fmt_parser = sub.add_parser("fmt", help="Format T++ source code")
    fmt_parser.add_argument("file", help="T++ source file to format")
    fmt_parser.add_argument("--check", action="store_true", help="Check formatting without modifying file")

    doc_parser = sub.add_parser("doc", help="Generate Markdown documentation")
    doc_parser.add_argument("target", help="Source file or stdlib module name")
    doc_parser.add_argument("-o", "--output", help="Write markdown to output file")

    lsp_parser = sub.add_parser("lsp", help="Run Language Server Protocol (LSP) server")
    lsp_parser.add_argument("--stdio", action="store_true", default=True, help="Run LSP over stdio (default)")
    lsp_parser.add_argument("--port", type=int, help="Run LSP over TCP port")

    doctor_parser = sub.add_parser("doctor", help="Run environment and installation diagnostics")
    doctor_parser.set_defaults(command="doctor")

    plugin_parser = sub.add_parser("plugin", help="Plugin management commands")
    plugin_sub = plugin_parser.add_subparsers(dest="plugin_action")

    plugin_install = plugin_sub.add_parser("install", help="Install plugin JSON")
    plugin_install.add_argument("source", help="Plugin JSON path")
    plugin_install.add_argument("--to", help="Install directory (default: ~/.tpp/plugins)")

    plugin_list = plugin_sub.add_parser("list", help="List installed plugins")
    plugin_list.add_argument("--dir", help="Plugin directory (default: ~/.tpp/plugins)")

    ide_parser = sub.add_parser("ide-manifest", parents=[common], help="Print IDE manifest")
    ide_parser.set_defaults(command="ide-manifest")

    api_parser = sub.add_parser("api", help="Run JSON API request or start API server")
    api_parser.add_argument("--payload-file", help="Path to JSON payload")
    api_parser.add_argument("--serve", action="store_true", help="Start HTTP API + Web IDE server")
    api_parser.add_argument("--host", default="127.0.0.1", help="Server host")
    api_parser.add_argument("--port", type=int, default=8787, help="Server port")
    api_parser.add_argument("--debug-trace", action="store_true", help="Show internal stack traces")

    bench_parser = sub.add_parser("bench", help="Run runtime performance benchmark suite")
    bench_parser.add_argument("--json", action="store_true", dest="as_json", help="Output benchmark results as JSON")
    bench_parser.add_argument("--save-baseline", help="Save results to baseline JSON file")

    return parser


def _run_modern_cli(argv: list[str], config: dict[str, Any]) -> int:
    parser = _build_modern_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"T++ Interpreter {__version__}")
        return 0

    if args.command == "run":
        try:
            engine = _create_engine(args, config)
        except Exception as exc:
            _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
            return 1
        return _run_file(engine, args.file, show_banner=not args.no_banner)

    if args.command == "repl":
        try:
            engine = _create_engine(args, config)
        except Exception as exc:
            _print_error(render_error(exc, debug_trace=getattr(args, "debug_trace", False)))
            return 1
        if not sys.stdin.isatty():
            return _run_repl_script(engine, sys.stdin.read())
        return _run_repl(engine)

    if args.command == "test":
        return _run_test_mode(args, config)

    if args.command == "check":
        return _run_check(args, config)

    if args.command == "fmt":
        return _run_fmt(args)

    if args.command == "doc":
        return _run_doc(args)

    if args.command == "lsp":
        return _run_lsp(args)

    if args.command == "doctor":
        return _run_doctor(args, config)

    if args.command == "plugin":
        return _run_plugin_command(args)

    if args.command == "ide-manifest":
        return _run_manifest(args, config)

    if args.command == "api":
        return _run_api_command(args)

    if args.command == "bench":
        return _run_bench(args)

    parser.print_help()
    return 1


def _build_legacy_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="T++ Natural English Programming Language")
    parser.add_argument("file", nargs="?", help="T++ source file")
    parser.add_argument("--test", action="store_true", help="Run test blocks")
    parser.add_argument("--test-verbose", action="store_true", help="Verbose test output")
    parser.add_argument("--plugin", action="append", default=[], help="Load plugin JSON file")
    parser.add_argument("--strict-fuzzy", action="store_true", dest="strict_fuzzy", help="Disable fuzzy English mode")
    parser.add_argument("--intent-mode", action="store_true", help="Enable intent parsing mode")
    parser.add_argument("--ide-manifest", action="store_true", help="Print IDE integration manifest as JSON")
    parser.add_argument("--version", action="store_true", help="Print interpreter version")
    parser.add_argument("--debug-trace", action="store_true", help="Show internal stack traces")
    parser.add_argument("--profile", action="store_true", help="Show execution profiling summary")
    parser.add_argument("--strict-semantic-resolution", action="store_true", help="Enable strict variable resolution")
    parser.add_argument("--strict-types", action="store_true", help="Enable strict type checking mode")
    parser.add_argument("--enforce-types", action="store_true", help="Enforce runtime type checking")
    parser.add_argument("--no-python-bridge", action="store_true", help="Disable Python bridge imports")
    parser.add_argument("--no-banner", action="store_true", help="Disable runtime credit banner")
    parser.add_argument("--doctor", action="store_true", help="Run environment and installation diagnostics")
    return parser


def _run_legacy_cli(argv: list[str], config: dict[str, Any]) -> int:
    parser = _build_legacy_parser()
    args = parser.parse_args(argv)

    if args.version:
        print(f"T++ Interpreter {__version__}")
        return 0

    if args.ide_manifest:
        return _run_manifest(args, config)

    if args.test:
        return _run_test_mode(args, config)

    if args.doctor:
        return _run_doctor(args, config)

    try:
        engine = _create_engine(args, config)
    except Exception as exc:
        _print_error(render_error(exc, debug_trace=args.debug_trace))
        return 1

    if args.file:
        return _run_file(engine, args.file, show_banner=not args.no_banner)

    if not sys.stdin.isatty():
        return _run_pipe(engine)

    return _run_repl(engine)


def main(argv: Optional[list[str]] = None) -> int:
    argv = argv if argv is not None else sys.argv
    config = _load_config_file()

    commands = {
        "run",
        "repl",
        "test",
        "check",
        "fmt",
        "doc",
        "lsp",
        "plugin",
        "ide-manifest",
        "api",
        "doctor",
        "bench",
    }
    if len(argv) > 1 and (argv[1] in commands or argv[1] in {"-h", "--help"}):
        return _run_modern_cli(argv[1:], config)

    return _run_legacy_cli(argv[1:], config)


if __name__ == "__main__":
    raise SystemExit(main())
