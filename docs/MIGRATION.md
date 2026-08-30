# T++ 3.1.x to 3.2.0 Migration Guide

T++ 3.2.0 is **100% backward compatible** with all existing 3.1.x scripts, test suites, CLI commands, and JSON API payloads. All previous syntax patterns continue to work without modification.

This guide highlights the new features, deprecation notices, and recommended upgrades for existing codebases.

---

## 1. Type Annotations & Static Checking

In 3.1.x, types were dynamic without language-level syntax for signatures. In 3.2.0:
- You can annotate variable declarations: `let x be 10 as a whole number`.
- You can annotate function parameters and return types: `define calculate with n as a number, giving back a number as:`.
- Run static type checking in CI using `tpp check <file>` with zero runtime overhead.

---

## 2. Standard Library Expansion & Sandboxing

In 3.1.x, standard functions were imported directly from Python bridges or minimal modules. In 3.2.0:
- Prefer the sandboxed `use ... from "module"` syntax over raw Python bridges.
- Use the 7 canonical standard library modules: `math`, `text`, `collections`, `system`, `time`, `json`, `validate`.
- File I/O operations (`system` module) are automatically restricted to the workspace root to prevent unintended directory traversal.

---

## 3. Developer Tooling Upgrades

Replace ad-hoc scripts with native CLI subcommands:
- **Code formatting**: Run `tpp fmt <file> --write` (or `tpp fmt <file> --check` in pre-commit hooks).
- **Static verification**: Run `tpp check <file>`.
- **Documentation**: Run `tpp doc <file> -o README.md` to automatically generate documentation from your source files.
- **Language Server**: Configure your IDE / VS Code to use `tpp lsp` for live diagnostics and autocompletion.

---

## 4. Public Python Embedding API

If your application embedded T++ via internal `RuntimeEngine` references, upgrade to the clean top-level API:

```python
import tpp

# Previous (still works):
# from tpp.runtime.engine import RuntimeEngine
# engine = RuntimeEngine()

# Recommended 3.2.0:
engine = tpp.run_source("let x be 42\n", initial_scope={"count": 10})
val = tpp.eval_expr("10 plus 25")
```
