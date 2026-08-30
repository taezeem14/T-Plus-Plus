# T++ (Antigravity 2.0 Edition)

> Human-first natural language programming, engineered for deterministic, production-grade software.

[![Python](https://img.shields.io/pypi/pyversions/tpp-language?style=for-the-badge)](https://pypi.org/project/tpp-language/)
[![CI](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/release.yml?style=for-the-badge&label=Release)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-MIT-blue?style=for-the-badge)](https://github.com/taezeem14/T-Plus-Plus)

T++ is a modern, natural-language programming language and development platform. It allows developers to write expressive, prose-like code with deterministic execution, static and gradual typing, rich visual diagnostics, an expanded standard library, and complete developer tooling.

Current Release: `3.2.0`

```bash
pip install tpp-language
```

---

## Key Highlights

- **Natural Surface Syntax & Synonyms**: Write in readable English phrases (`give back`, `is between 1 and 10`, `the items in tasks where item's is_done`, `a record with name as "Ana"`).
- **Gradual Type System**: Optional type annotations on variables (`let count be 0 as a whole number`) and functions (`define add with a as a number, giving back a number as:`).
- **Rich Visual Diagnostics**: Beautiful terminal compiler errors with line/column markers, carets, source previews, suggestions, and call stack frame tracking.
- **Sandboxed Standard Library**: 7 built-in modules (`math`, `text`, `collections`, `system`, `time`, `json`, `validate`) with path traversal protection.
- **Language Server Protocol (LSP)**: Integrated LSP server (`tpp lsp`) providing live diagnostics, hover docs, autocomplete, definition jump, and formatting for VS Code / IDEs.
- **Full Developer CLI**: Unified subcommands: `run`, `check`, `fmt`, `doc`, `repl`, `test`, `bench`, `lsp`, `api`, `doctor`, `plugin`.
- **Public Python Embedding API**: Seamless Python interop with `tpp.run_source()`, `tpp.run_file()`, and `tpp.eval_expr()`.

---

## Quick Start

### 1. Installation

```bash
pip install tpp-language
```

Verify your environment:

```bash
tpp --version
tpp doctor
```

### 2. Hello World

Create `hello.tpp`:

```tpp
let name be "Developer"
say "Hello, {name}! Welcome to T++."
```

Run it:

```bash
tpp run hello.tpp
```

---

## Language Features at a Glance

### Pattern Matching (`match`)

```tpp
match status_code:
    when 200:
        say "Success"
    when 404:
        say "Not Found"
    when x if x is at least 500:
        say "Server Error: {x}"
    otherwise:
        say "Unhandled status"
```

### Comprehensions & Collections

```tpp
let numbers be 1 to 10
let evens be a list containing x times 2 for each x in numbers if x % 2 == 0
let filtered be the items in numbers where item is greater than 5

let person be a record with name as "Alice" and role as "Admin"
say "{person's name} has role {person's role}"
```

### Error Handling (`try / handle / finally`)

```tpp
try:
    if divisor is equal to 0:
        raise the error "Cannot divide by zero"
    let result be total / divisor
handle any error as err:
    say "Caught error: " then err
finally:
    say "Execution completed."
```

### Modules & Imports

```tpp
# In math_utils.tpp
export define square with n as:
    give back n times n

# In main.tpp
use square from "./math_utils.tpp"
let val be call square with 6
```

---

## CLI Reference

| Command | Description | Example |
|---|---|---|
| `tpp run <file>` | Execute a T++ file | `tpp run app.tpp` |
| `tpp check <file>` | Statically check syntax & types | `tpp check app.tpp` |
| `tpp fmt <file>` | Auto-format source code | `tpp fmt app.tpp --write` |
| `tpp doc <file\|mod>` | Generate Markdown documentation | `tpp doc math` / `tpp doc app.tpp` |
| `tpp repl` | Start interactive shell with meta-commands | `tpp repl` |
| `tpp test [file]` | Run test blocks (supports `--json`, `--junit`) | `tpp test tests/ --json` |
| `tpp bench` | Run runtime performance benchmark suite | `tpp bench` |
| `tpp lsp` | Run Language Server Protocol server | `tpp lsp --stdio` |
| `tpp api` | Start Web IDE and JSON HTTP API | `tpp api --serve --port 8787` |
| `tpp doctor` | Run installation & environment diagnostics | `tpp doctor` |
| `tpp plugin` | Install and list extensions | `tpp plugin install plugin.json` |

---

## Interactive REPL

Launch the REPL with `tpp repl`:

```text
T++ Interactive Shell v3.2.0
Type ':help' or ':?' for commands, ':quit' or 'exit' to exit.

>> let x be 10 plus 20
>> :type x
x : int = 30
>> :doc math
Native Stdlib Module 'math'
Members: abs, absolute_value, add, average, ceil, cos, cosine, divide...
>> :env
--- Scope (1 bindings) ---
  x (int) = 30
>> :quit
```

---

## Python Embedding API

Embed T++ directly in Python applications:

```python
import tpp

# Execute source code
engine = tpp.run_source(
    "let result be a times b\n",
    initial_scope={"a": 6, "b": 7}
)
print(engine.global_scope.get("result", 1)) # 42

# Evaluate single expressions
value = tpp.eval_expr("10 plus 25") # 35
```

---

## Standard Library Reference

| Module | Key Functions & Constants |
|---|---|
| `math` | `sin`, `cos`, `tan`, `sqrt`, `log`, `floor`, `ceil`, `round`, `abs`, `average`, `median`, `is_prime`, `pi`, `e`, `tau` |
| `text` | `uppercase`, `lowercase`, `title`, `trimmed`, `replace`, `contains`, `format_currency`, `matches_pattern`, `words_in` |
| `collections` | `map_items`, `filter_items`, `reduce_items`, `group_by`, `unique_items`, `chunk_items`, `flatten`, `zip_items` |
| `system` | `read_file`, `write_file`, `append_file`, `file_exists`, `list_files`, `get_env`, `command_line_arguments` |
| `time` | `current_moment`, `format_moment`, `parse_moment`, `time_difference`, `shift_time`, `sleep_seconds`, `now` |
| `json` | `parse_json`, `to_json` |
| `validate` | `is_valid_email`, `is_valid_number`, `is_within_range`, `is_not_nothing`, `is_empty` |

---

## Documentation

- [Language Specification](docs/LANGUAGE_SPEC.md)
- [Standard Library Guide](docs/STDLIB.md)
- [Migration Guide (3.1.x to 3.2.0)](docs/MIGRATION.md)
- [Architecture Decision Records (ADRs)](docs/decisions/)

---

## License

T++ is licensed under the MIT License.
