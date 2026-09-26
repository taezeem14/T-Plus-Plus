from __future__ import annotations

import io
import json
import time
from contextlib import redirect_stdout
from typing import Any

from tpp.core.errors import TppError, render_error
from tpp.parser.semantic import SemanticAnalyzer, SemanticConfig
from tpp.runtime.engine import EngineConfig, RuntimeEngine
from tpp.tools.formatter import format_tpp_source


def ast_to_dict(node: Any) -> Any:
    """Recursively serializes AST nodes into a JSON-compatible tree."""
    if node is None or isinstance(node, (str, int, float, bool)):
        return node
    if isinstance(node, (list, tuple)):
        return [ast_to_dict(item) for item in node]
    if isinstance(node, dict):
        return {str(k): ast_to_dict(v) for k, v in node.items()}
    if hasattr(node, "__dataclass_fields__"):
        result: dict[str, Any] = {"type": node.__class__.__name__, "node_type": node.__class__.__name__}
        for field_name in node.__dataclass_fields__:
            val = getattr(node, field_name)
            result[field_name] = ast_to_dict(val)
        return result
    if hasattr(node, "__dict__"):
        result = {"type": node.__class__.__name__, "node_type": node.__class__.__name__}
        for k, v in node.__dict__.items():
            if not k.startswith("_"):
                result[k] = ast_to_dict(v)
        return result
    return str(node)


def get_ast_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Parses source code and returns the AST serialized as JSON."""
    parser_mode = str(payload.get("parser_mode", "fuzzy"))
    source = str(payload.get("source", ""))
    debug_trace = bool(payload.get("debug_trace", False))
    optimize = bool(payload.get("optimize", False))

    try:
        engine = RuntimeEngine(
            EngineConfig(
                parser_mode=parser_mode,
                optimize=optimize,
            )
        )
        program = engine.parse_source(source)
        tree = ast_to_dict(program)
        return {
            "ok": True,
            "ast": tree,
            "statement_count": len(program.statements),
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": render_error(exc, debug_trace=debug_trace),
            "line": getattr(exc, "line", None),
            "column": getattr(exc, "column", None),
            "hint": getattr(exc, "suggestion", None),
        }


def check_code_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Checks syntax and types, returning diagnostics with line/col and hints."""
    parser_mode = str(payload.get("parser_mode", "fuzzy"))
    strict_types = bool(payload.get("strict_types", False))
    strict_semantic = bool(payload.get("strict_semantic_resolution", False))
    source = str(payload.get("source", ""))
    lines = source.splitlines()

    diagnostics: list[dict[str, Any]] = []
    inferred_types: dict[str, str] = {}

    try:
        engine = RuntimeEngine(
            EngineConfig(
                parser_mode=parser_mode,
                strict_semantic_resolution=strict_semantic,
                strict_types=strict_types,
                enforce_types=strict_types,
                optimize=False,
            )
        )
        program = engine.parse_source(source)
        analyzer = SemanticAnalyzer(
            SemanticConfig(
                strict_variable_resolution=strict_semantic,
                strict_types=strict_types,
            )
        )
        inferred_types = analyzer.analyze(program)
    except TppError as exc:
        line_val = getattr(exc, "line", None) or 1
        col_val = getattr(exc, "column", None) or 1
        line_idx = max(0, line_val - 1)
        line_len = len(lines[line_idx]) if line_idx < len(lines) else 1
        diagnostics.append(
            {
                "line": line_val,
                "column": col_val,
                "end_line": line_val,
                "end_column": max(col_val + 1, line_len + 1),
                "message": getattr(exc, "message", str(exc)),
                "severity": "error",
                "hint": getattr(exc, "suggestion", None),
                "category": getattr(exc, "category", "SyntaxError"),
            }
        )
    except Exception as exc:
        diagnostics.append(
            {
                "line": 1,
                "column": 1,
                "end_line": 1,
                "end_column": 1,
                "message": f"Syntax error: {exc}",
                "severity": "error",
                "hint": None,
                "category": "Error",
            }
        )

    return {
        "ok": len(diagnostics) == 0,
        "diagnostics": diagnostics,
        "inferred_types": inferred_types,
        "source_lines": len(lines),
    }


def format_code_response(payload: dict[str, Any]) -> dict[str, Any]:
    """Formats T++ code and returns the formatted string."""
    source = str(payload.get("source", ""))
    try:
        formatted = format_tpp_source(source)
        return {
            "ok": True,
            "formatted": formatted,
            "modified": formatted != source,
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
            "formatted": source,
            "modified": False,
        }


def get_examples_catalog() -> dict[str, Any]:
    """Returns a curated catalog of 8+ rich T++ examples across categories."""
    catalog = [
        {
            "id": "basics",
            "title": "Basics & Arithmetic",
            "category": "Basics",
            "description": "Variables, arithmetic calculations, tax computation, and natural formatted printing.",
            "source": (
                '# T++ Basics: Variables, math calculations, and formatted output\n'
                'let greeting be "Welcome to T++!"\n'
                'say greeting\n\n'
                'let price be 49.99\n'
                'let tax_rate be 0.08\n'
                'let total be price plus (price times tax_rate)\n\n'
                'say "Base price:" then price\n'
                'say "Total with 8% tax:" then total\n'
            ),
        },
        {
            "id": "control_flow",
            "title": "Control Flow & Loops",
            "category": "Control Flow",
            "description": "Conditional branching (if/otherwise if/otherwise), count loops, and while loops.",
            "source": (
                '# Control Flow: Conditionals and Loops\n'
                'let score be 85\n\n'
                'if score >= 90:\n'
                '    say "Grade: A (Excellent)"\n'
                'otherwise if score >= 80:\n'
                '    say "Grade: B (Great job!)"\n'
                'otherwise:\n'
                '    say "Grade: Keep practicing!"\n\n'
                'say "--- Counting from 1 to 5 ---"\n'
                'count from 1 to 5 as i:\n'
                '    say "Step" then i\n\n'
                'let countdown be 3\n'
                'while countdown > 0:\n'
                '    say "Countdown:" then countdown\n'
                '    decrease countdown by 1\n\n'
                'say "Liftoff!"\n'
            ),
        },
        {
            "id": "pattern_matching",
            "title": "Pattern Matching",
            "category": "Pattern Matching",
            "description": "Expressive structural pattern matching over status codes and values.",
            "source": (
                '# Expressive Pattern Matching in T++\n'
                'define handle_status with code:\n'
                '    match code:\n'
                '        when 200:\n'
                '            say "200 OK: Operation completed successfully."\n'
                '        when 201:\n'
                '            say "201 Created: New resource provisioned."\n'
                '        when 400:\n'
                '            say "400 Bad Request: Invalid input parameters."\n'
                '        when 404:\n'
                '            say "404 Not Found: Requested resource does not exist."\n'
                '        when 500:\n'
                '            say "500 Internal Error: Server failure detected."\n'
                '        otherwise:\n'
                '            say "Unknown status code:" then code\n\n'
                'call handle_status with 200\n'
                'call handle_status with 404\n'
                'call handle_status with 500\n'
                'call handle_status with 418\n'
            ),
        },
        {
            "id": "collections",
            "title": "Collections & Comprehensions",
            "category": "Collections & Comprehensions",
            "description": "Working with lists, filter comprehensions, transformations, and record objects.",
            "source": (
                '# Collections & Comprehensions in T++\n'
                'let numbers be a list containing 1 and 2 and 3 and 4 and 5 and 6 and 7 and 8 and 9 and 10\n'
                'say "All numbers:" then numbers\n\n'
                'let evens be the items in numbers where item % 2 == 0\n'
                'say "Even numbers:" then evens\n\n'
                'let doubled be a list containing x times 2 for each x in numbers if x > 4\n'
                'say "Doubled (for x > 4):" then doubled\n\n'
                'let student be a record with name as "Alex" and course as "Computer Science" and gpa as 3.9\n'
                'say "Student profile:" then student\n'
                'say "Student name:" then student.name\n'
                'say "Student GPA:" then student.gpa\n'
            ),
        },
        {
            "id": "algorithms",
            "title": "Fibonacci & Prime Detection",
            "category": "Algorithms",
            "description": "Recursive Fibonacci sequence generation paired with standard library prime checking.",
            "source": (
                '# Algorithms: Recursive Fibonacci & Prime Number Check\n'
                'use math\n\n'
                'define fibonacci with n as:\n'
                '    if n <= 0:\n'
                '        give back 0\n'
                '    otherwise if n == 1:\n'
                '        give back 1\n'
                '    otherwise:\n'
                '        let a be call fibonacci with (n - 1)\n'
                '        let b be call fibonacci with (n - 2)\n'
                '        give back a plus b\n\n'
                'say "Fibonacci sequence and prime detection:"\n'
                'count from 1 to 8 as i:\n'
                '    let val be call fibonacci with i\n'
                '    let is_p be call math.is_prime with val\n'
                '    say "Fib(" then i then ") =" then val then (if is_p: " [PRIME]" otherwise: "")\n'
            ),
        },
        {
            "id": "classes_oop",
            "title": "Classes & OOP",
            "category": "Classes & OOP",
            "description": "Class definitions, constructors (when created with), fields (remember), and methods.",
            "source": (
                '# Object-Oriented Programming in T++\n'
                'create class BankAccount:\n'
                '    when created with owner and balance:\n'
                '        remember owner\n'
                '        remember balance\n'
                '        say "Account opened for" then owner\n\n'
                '    define deposit with amount:\n'
                '        if amount <= 0:\n'
                '            say "Deposit must be greater than zero."\n'
                '            give back balance\n'
                '        increase balance by amount\n'
                '        say "Deposited $" then amount then " | Balance: $" then balance\n'
                '        give back balance\n\n'
                '    define withdraw with amount:\n'
                '        if amount > balance:\n'
                '            say "Insufficient funds!"\n'
                '            give back balance\n'
                '        decrease balance by amount\n'
                '        say "Withdrew $" then amount then " | Balance: $" then balance\n'
                '        give back balance\n\n'
                'let acct be call BankAccount with "Sarah Connor", 100\n'
                'call deposit on acct with 75\n'
                'call withdraw on acct with 50\n'
                'call withdraw on acct with 200\n'
            ),
        },
        {
            "id": "error_handling",
            "title": "Error Handling & Safety",
            "category": "Error Handling",
            "description": "Robust error handling with try, handle clauses, custom error raising, and finally blocks.",
            "source": (
                '# Error Handling with Try, Handle, and Finally\n'
                'define safe_divide with a and b:\n'
                '    try:\n'
                '        if b == 0:\n'
                '            raise "ZeroDivisionError: denominator cannot be zero."\n'
                '        let result be a / b\n'
                '        say a then "/" then b then "=" then result\n'
                '        give back result\n'
                '    handle Error as err:\n'
                '        say "Caught error safely:" then err\n'
                '        give back nothing\n'
                '    finally:\n'
                '        say "Division clean-up completed."\n\n'
                'say "--- Case 1: Valid calculation ---"\n'
                'call safe_divide with 100 and 4\n\n'
                'say "--- Case 2: Zero denominator ---"\n'
                'call safe_divide with 50 and 0\n'
            ),
        },
        {
            "id": "system_stdlib",
            "title": "Standard Library Showcase",
            "category": "System & Stdlib",
            "description": "Leveraging T++ stdlib modules: text, math, json, time, and validate.",
            "source": (
                '# Standard Library Modules: text, math, json, time, validate\n'
                'use text\n'
                'use math\n'
                'use json\n'
                'use time\n'
                'use validate\n\n'
                '# 1. Text transformations\n'
                'let banner be call text.upper with "welcome to the modern t++ ide!"\n'
                'say banner\n\n'
                '# 2. Math utilities\n'
                'let hypotenuse be call math.sqrt with (3 times 3 plus 4 times 4)\n'
                'say "Hypotenuse of 3 and 4:" then hypotenuse\n'
                'say "Cosine of 0 rad:" then call math.cos with 0\n\n'
                '# 3. JSON serialization\n'
                'let config be a record with title as "T++ Web IDE", version as "2.0", fast as true\n'
                'let json_str be call json.stringify with config, 2\n'
                'say "Serialized configuration:"\n'
                'say json_str\n\n'
                '# 4. Form validation\n'
                'let email be "developer@tplusplus.lang"\n'
                'let is_valid be call validate.is_valid_email with email\n'
                'say "Email:" then email then "valid?" then is_valid\n'
            ),
        },
        {
            "id": "test_suite",
            "title": "Built-in Test Suite",
            "category": "Basics",
            "description": "Native declarative testing syntax with suite, test blocks, and expectations.",
            "source": (
                '# Built-in Declarative Test Suite\n'
                'suite "Calculator and Assertion Suite":\n'
                '    test "arithmetic operations":\n'
                '        expect 2 plus 3 to be 5\n'
                '        expect 100 / 4 to be 25\n\n'
                '    test "range validation":\n'
                '        let score be 88\n'
                '        expect score to be between 80 and 100\n\n'
                '    test "string and types":\n'
                '        let msg be "Hello World"\n'
                '        expect type of msg to be str\n\n'
                'say "Select Mode: \'Test\' in the top bar to run test suite assertions!"\n'
            ),
        },
    ]

    return {
        "ok": True,
        "count": len(catalog),
        "categories": [
            "Basics",
            "Control Flow",
            "Pattern Matching",
            "Collections & Comprehensions",
            "Algorithms",
            "Classes & OOP",
            "Error Handling",
            "System & Stdlib",
        ],
        "examples": catalog,
    }


def get_stdlib_catalog() -> dict[str, Any]:
    """Returns standard library modules, member functions, signatures, and docstrings."""
    modules = [
        {
            "name": "math",
            "description": "Mathematical operations, trigonometry, statistical calculations, and constants.",
            "members": [
                {"name": "add", "signature": "add(a, b)", "doc": "Returns sum of a and b."},
                {"name": "subtract", "signature": "subtract(a, b)", "doc": "Returns difference of a and b."},
                {"name": "multiply", "signature": "multiply(a, b)", "doc": "Returns product of a and b."},
                {"name": "divide", "signature": "divide(a, b)", "doc": "Safely divides a by b (raises on zero)."},
                {"name": "power", "signature": "power(a, b)", "doc": "Computes a raised to power b."},
                {"name": "sqrt", "signature": "sqrt(n)", "doc": "Returns square root of n."},
                {"name": "square_root", "signature": "square_root(n)", "doc": "Alias for sqrt."},
                {"name": "sin", "signature": "sin(angle)", "doc": "Computes sine of angle in radians."},
                {"name": "cos", "signature": "cos(angle)", "doc": "Computes cosine of angle in radians."},
                {"name": "tan", "signature": "tan(angle)", "doc": "Computes tangent of angle in radians."},
                {"name": "log", "signature": "log(n, base=e)", "doc": "Computes logarithm with given base."},
                {"name": "floor", "signature": "floor(n)", "doc": "Rounds down to nearest integer."},
                {"name": "ceil", "signature": "ceil(n)", "doc": "Rounds up to nearest integer."},
                {"name": "round", "signature": "round(n, decimals=0)", "doc": "Rounds number to decimal precision."},
                {"name": "round_number", "signature": "round_number(n, decimals=0)", "doc": "Alias for round."},
                {"name": "abs", "signature": "abs(n)", "doc": "Returns absolute value of n."},
                {"name": "average", "signature": "average(items)", "doc": "Computes arithmetic mean of a list."},
                {"name": "median", "signature": "median(items)", "doc": "Computes median of a list."},
                {"name": "sum", "signature": "sum(items)", "doc": "Sums all items in list."},
                {"name": "min", "signature": "min(items)", "doc": "Returns minimum element in list."},
                {"name": "max", "signature": "max(items)", "doc": "Returns maximum element in list."},
                {"name": "is_even", "signature": "is_even(n)", "doc": "True if integer n is even."},
                {"name": "is_odd", "signature": "is_odd(n)", "doc": "True if integer n is odd."},
                {"name": "is_prime", "signature": "is_prime(n)", "doc": "True if integer n is prime."},
                {"name": "random_number", "signature": "random_number(low=0.0, high=1.0)", "doc": "Random float in range."},
                {"name": "random_integer", "signature": "random_integer(low=1, high=100)", "doc": "Random int in range."},
            ],
            "constants": [
                {"name": "pi", "value": 3.141592653589793, "doc": "Ratio of a circle circumference to diameter."},
                {"name": "tau", "value": 6.283185307179586, "doc": "Circle constant equal to 2*pi."},
                {"name": "e", "value": 2.718281828459045, "doc": "Euler's number (base of natural log)."},
            ],
        },
        {
            "name": "text",
            "description": "String manipulation, case transformations, search, split/join, and formatting.",
            "members": [
                {"name": "upper", "signature": "upper(s)", "doc": "Converts string to uppercase."},
                {"name": "lower", "signature": "lower(s)", "doc": "Converts string to lowercase."},
                {"name": "title", "signature": "title(s)", "doc": "Converts string to Title Case."},
                {"name": "capitalized", "signature": "capitalized(s)", "doc": "Capitalizes first letter of string."},
                {"name": "strip", "signature": "strip(s, chars=None)", "doc": "Trims leading and trailing whitespace."},
                {"name": "trimmed", "signature": "trimmed(s, chars=None)", "doc": "Alias for strip."},
                {"name": "padded", "signature": "padded(s, length, fill=' ')", "doc": "Pads string to length."},
                {"name": "replace", "signature": "replace(s, old, new)", "doc": "Replaces occurrences of old with new."},
                {"name": "contains", "signature": "contains(s, needle)", "doc": "True if needle is in string."},
                {"name": "position_of", "signature": "position_of(s, sub)", "doc": "Index of substring or -1."},
                {"name": "split", "signature": "split(s, sep=None)", "doc": "Splits string by delimiter."},
                {"name": "join", "signature": "join(sep, items)", "doc": "Joins elements of items with sep."},
                {"name": "format", "signature": "format(template, *args, **kwargs)", "doc": "Formats string template."},
                {"name": "format_number", "signature": "format_number(amount, decimals=2)", "doc": "Formats number with commas."},
                {"name": "format_currency", "signature": "format_currency(amount, symbol='$')", "doc": "Formats number as currency."},
                {"name": "length", "signature": "length(s)", "doc": "Returns character count of string."},
                {"name": "reversed", "signature": "reversed(s)", "doc": "Reverses order of characters in string."},
                {"name": "starts_with", "signature": "starts_with(s, prefix)", "doc": "True if string begins with prefix."},
                {"name": "ends_with", "signature": "ends_with(s, suffix)", "doc": "True if string ends with suffix."},
                {"name": "matches_pattern", "signature": "matches_pattern(s, pattern)", "doc": "True if string matches regex."},
                {"name": "words_in", "signature": "words_in(s)", "doc": "Splits string into word tokens."},
            ],
            "constants": [],
        },
        {
            "name": "collections",
            "description": "Functional utilities, transformations, sorting, grouping, and set logic.",
            "members": [
                {"name": "map_items", "signature": "map_items(fn, items)", "doc": "Maps function fn over every item."},
                {"name": "filter_items", "signature": "filter_items(fn, items)", "doc": "Filters items matching predicate fn."},
                {"name": "reduce_items", "signature": "reduce_items(fn, items, initial=None)", "doc": "Reduces list with accumulator."},
                {"name": "sort_items", "signature": "sort_items(items, key=None, reverse=False)", "doc": "Sorts items in ascending order."},
                {"name": "group_by", "signature": "group_by(fn, items)", "doc": "Groups items into record by key fn."},
                {"name": "union", "signature": "union(a, b)", "doc": "Set union of two collections."},
                {"name": "intersection", "signature": "intersection(a, b)", "doc": "Set intersection of two collections."},
                {"name": "difference", "signature": "difference(a, b)", "doc": "Set difference of items in a not in b."},
                {"name": "flatten", "signature": "flatten(nested)", "doc": "Flattens nested lists into single list."},
                {"name": "zip_items", "signature": "zip_items(a, b)", "doc": "Pairs corresponding elements into lists."},
                {"name": "take_first", "signature": "take_first(items, n)", "doc": "Returns first n elements."},
                {"name": "take_last", "signature": "take_last(items, n)", "doc": "Returns last n elements."},
                {"name": "unique_items", "signature": "unique_items(items)", "doc": "Deduplicates list preserving order."},
                {"name": "chunk_items", "signature": "chunk_items(items, size)", "doc": "Partitions list into chunks."},
            ],
            "constants": [],
        },
        {
            "name": "system",
            "description": "Workspace-sandboxed file reading/writing, directories, and environment.",
            "members": [
                {"name": "cwd", "signature": "cwd()", "doc": "Returns active workspace directory."},
                {"name": "exists", "signature": "exists(path)", "doc": "True if file or directory exists."},
                {"name": "read_text", "signature": "read_text(path, encoding='utf-8')", "doc": "Reads file as text string."},
                {"name": "write_text", "signature": "write_text(path, content, encoding='utf-8')", "doc": "Writes string into file."},
                {"name": "append_text", "signature": "append_text(path, content, encoding='utf-8')", "doc": "Appends string to file."},
                {"name": "list_dir", "signature": "list_dir(path='.')", "doc": "Lists directory entries."},
                {"name": "read_json", "signature": "read_json(path)", "doc": "Reads and parses JSON file."},
                {"name": "write_json", "signature": "write_json(path, payload)", "doc": "Serializes payload to JSON file."},
                {"name": "get_env", "signature": "get_env(key, default=None)", "doc": "Reads environment variable."},
                {"name": "command_line_arguments", "signature": "command_line_arguments()", "doc": "CLI arguments passed to script."},
            ],
            "constants": [],
        },
        {
            "name": "time",
            "description": "Timestamps, ISO 8601 formatting, date math, and sleep execution.",
            "members": [
                {"name": "now", "signature": "now()", "doc": "Current UNIX epoch timestamp in seconds."},
                {"name": "millis", "signature": "millis()", "doc": "Current timestamp in milliseconds."},
                {"name": "current_moment", "signature": "current_moment()", "doc": "Current UTC moment in ISO 8601."},
                {"name": "iso_now", "signature": "iso_now()", "doc": "Alias for current_moment."},
                {"name": "sleep", "signature": "sleep(seconds)", "doc": "Pauses execution for duration."},
                {"name": "format_moment", "signature": "format_moment(dt_iso, fmt='%Y-%m-%d %H:%M:%S')", "doc": "Formats ISO timestamp."},
                {"name": "parse_moment", "signature": "parse_moment(s, fmt='%Y-%m-%d %H:%M:%S')", "doc": "Parses formatted datetime string."},
                {"name": "time_difference", "signature": "time_difference(t1_iso, t2_iso)", "doc": "Difference in seconds between two ISO strings."},
                {"name": "shift_time", "signature": "shift_time(iso_str=None, days=0, hours=0, minutes=0, seconds=0)", "doc": "Offsets a datetime by time delta."},
            ],
            "constants": [],
        },
        {
            "name": "json",
            "description": "Standard JSON decoding and encoding.",
            "members": [
                {"name": "parse", "signature": "parse(s)", "doc": "Parses JSON string into record, list, or primitive."},
                {"name": "parse_json", "signature": "parse_json(s)", "doc": "Alias for parse."},
                {"name": "stringify", "signature": "stringify(obj, indent=None)", "doc": "Serializes object to JSON string."},
                {"name": "to_json", "signature": "to_json(obj, indent=None)", "doc": "Alias for stringify."},
            ],
            "constants": [],
        },
        {
            "name": "validate",
            "description": "Validation helpers for emails, ranges, numbers, and null checks.",
            "members": [
                {"name": "is_valid_email", "signature": "is_valid_email(s)", "doc": "Validates RFC 5322 email address format."},
                {"name": "is_valid_number", "signature": "is_valid_number(val)", "doc": "True if value is parsable as a number."},
                {"name": "is_within_range", "signature": "is_within_range(v, low, high)", "doc": "True if low <= v <= high."},
                {"name": "is_not_nothing", "signature": "is_not_nothing(v)", "doc": "True if value is not nothing or null."},
                {"name": "is_empty", "signature": "is_empty(v)", "doc": "True if collection or string is empty."},
            ],
            "constants": [],
        },
    ]

    return {
        "ok": True,
        "count": len(modules),
        "modules": modules,
    }


def execute_json_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Primary handler executing requests across run, test, ast, check, fmt, and manifest modes."""
    mode = str(payload.get("mode", "run"))

    if mode in {"ast", "parse"}:
        return get_ast_response(payload)
    if mode in {"check", "diagnostics"}:
        return check_code_response(payload)
    if mode in {"fmt", "format"}:
        return format_code_response(payload)
    if mode == "examples":
        return get_examples_catalog()
    if mode == "stdlib":
        return get_stdlib_catalog()

    parser_mode = str(payload.get("parser_mode", "fuzzy"))
    debug_trace = bool(payload.get("debug_trace", False))
    profiling = bool(payload.get("profiling", False))
    strict_types = bool(payload.get("strict_types", False))
    strict_semantic = bool(payload.get("strict_semantic_resolution", False))

    engine = RuntimeEngine(
        EngineConfig(
            parser_mode=parser_mode,
            debug_trace=debug_trace,
            profiling=profiling,
            optimize=bool(payload.get("optimize", True)),
            strict_semantic_resolution=strict_semantic,
            strict_types=strict_types,
            enforce_types=strict_types,
            allow_python_bridge=bool(payload.get("allow_python_bridge", True)),
        )
    )

    for plugin_path in payload.get("plugins", []) or []:
        engine.load_plugin(str(plugin_path))

    initial_scope = payload.get("initial_scope") or payload.get("scope") or {}
    if isinstance(initial_scope, dict):
        for k, v in initial_scope.items():
            engine.global_scope.define(str(k), v)

    source = str(payload.get("source", ""))
    out = io.StringIO()
    response: dict[str, Any] = {"ok": True, "mode": mode}
    start_time = time.perf_counter()

    try:
        with redirect_stdout(out):
            if mode == "run":
                engine.run_source(source)
                if payload.get("return_ast"):
                    response["ast"] = get_ast_response(payload).get("ast")
                if payload.get("return_diagnostics"):
                    response["diagnostics"] = check_code_response(payload).get("diagnostics")
                if payload.get("return_formatted"):
                    response["formatted"] = format_code_response(payload).get("formatted")
                # Extract evaluated variables from global scope
                vars_list = []
                for name, val in engine.global_scope.values.items():
                    if name.startswith("__"):
                        continue
                    val_type = type(val).__name__
                    if hasattr(val, "record_type_name"):
                        val_type = getattr(val, "record_type_name")
                    elif hasattr(val, "klass"):
                        val_type = getattr(val.klass, "name", "Instance")
                    elif hasattr(val, "name") and type(val).__name__ in {"TppClass", "TppFunction", "NativeModule"}:
                        val_type = type(val).__name__
                    elif isinstance(val, bool):
                        val_type = "boolean"
                    elif isinstance(val, int):
                        val_type = "whole number"
                    elif isinstance(val, float):
                        val_type = "number"
                    elif isinstance(val, str):
                        val_type = "text"
                    elif isinstance(val, list):
                        val_type = "list"
                    elif isinstance(val, dict):
                        val_type = "record"
                    elif val is None or type(val).__name__ == "TppNothing":
                        val_type = "nothing"

                    try:
                        if isinstance(val, (int, float, bool, str)):
                            display_val = val
                        elif isinstance(val, (list, dict)):
                            display_val = json.loads(json.dumps(val, default=str))
                        else:
                            display_val = repr(val)
                    except Exception:
                        display_val = str(val)

                    inferred = engine.parser_semantic.inferred_types.get(name)
                    vars_list.append(
                        {
                            "name": name,
                            "type": inferred or val_type,
                            "runtime_type": val_type,
                            "value": display_val,
                            "repr": repr(val) if not isinstance(val, (int, float, str, bool)) else str(val),
                        }
                    )

                response["variables"] = sorted(vars_list, key=lambda v: v["name"])
                response["scope"] = {v["name"]: v["value"] for v in vars_list}
            elif mode == "test":
                program = engine.parse_source(source)
                results, passed, failed = engine.run_tests(program, verbose=False)
                response["tests"] = [
                    {
                        "name": item.name,
                        "passed": item.passed,
                        "duration_ms": item.duration_ms,
                        "details": item.details,
                    }
                    for item in results
                ]
                response["summary"] = {"passed": passed, "failed": failed}
                response["ok"] = failed == 0
            elif mode == "manifest":
                response["manifest"] = engine.manifest()
            else:
                raise ValueError(f"Unsupported api mode '{mode}'")
    except Exception as exc:
        response["ok"] = False
        response["error"] = render_error(exc, debug_trace=debug_trace)
        if isinstance(exc, TppError):
            response["error_category"] = exc.category
            response["line"] = getattr(exc, "line", None)
            response["column"] = getattr(exc, "column", None)
            response["hint"] = getattr(exc, "suggestion", None)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
    response["duration_ms"] = round(elapsed_ms, 2)
    response["stdout"] = out.getvalue()
    if profiling:
        response["profiling"] = engine.profiler.report()
    return response


def execute_json_payload_text(payload_text: str) -> str:
    payload = json.loads(payload_text)
    result = execute_json_request(payload)
    return json.dumps(result, indent=2)
