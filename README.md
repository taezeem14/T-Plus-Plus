# T++ Language Platform

T++ is a human-first programming language ecosystem where code reads like structured English and executes through a deterministic runtime.

This repository ships T++ as an installable developer tool with:

- a real terminal CLI (tpp)
- a modular parser and runtime architecture
- a native standard library layer
- plugin system v3
- a web-based IDE backend and frontend

## Install

Install from local source:

```powershell
pip install .
```

After install, use the CLI directly:

```powershell
tpp --version
tpp run examples/hello.tpp
```

## Core Commands

```powershell
tpp run file.tpp
tpp repl
tpp test tests/regression.tpp
tpp doctor
tpp plugin install examples/sample_plugin.json
tpp plugin list
tpp api --serve
```

Backward compatibility remains available:

```powershell
python tpp.py examples/hello.tpp
python tpp.py --test tests/regression.tpp
```

## Web IDE

Start backend + IDE page:

```powershell
tpp api --serve --host 127.0.0.1 --port 8787
```

Open:

- http://127.0.0.1:8787/

Execution endpoint:

- POST /run
- JSON body example:

```json
{
	"source": "let x be 5\nsay x",
	"mode": "run"
}
```

## Architecture

- tpp/core: AST, constants, diagnostics, shared helpers
- tpp/parser: lexer, strict/fuzzy/intent parser, semantic analysis, optimizer
- tpp/runtime: independent AST expression evaluator and execution engine
- tpp/stdlib: native modules (math, text, system, time)
- tpp/gui: declarative GUI runtime abstraction
- tpp/plugins: metadata-validated plugin system with transform pipeline
- tpp/cli: modern command layer and legacy compatibility path
- tpp/api: JSON execution API and web IDE server

## Examples

- examples/hello.tpp
- examples/math.tpp
- examples/gui.tpp
- examples/plugin_demo.tpp

Run plugin demo:

```powershell
tpp run examples/plugin_demo.tpp --plugin examples/sample_plugin.json
```

## Config (.tppconfig)

Optional JSON config in project root:

```json
{
	"parser_mode": "fuzzy",
	"plugins": ["sample_plugin.json"],
	"strict_semantic_resolution": false,
	"no_python_bridge": false
}
```

CLI flags always override config values.

## Validation and CI

This repository includes production-ready GitHub Actions workflows:

- `.github/workflows/ci.yml`: continuous validation for push and pull request
- `.github/workflows/release.yml`: tag-based release build + GitHub Release + optional PyPI publish

CI validates:

- package installation (`pip install .`)
- compile checks (`python -m compileall -q tpp`)
- linting (`ruff check tpp tests scripts`)
- required CLI contract (`tpp --version`, `run`, `test`, `repl`, `plugin install/list`)
- `tpp doctor` diagnostics

## Release Process

Create a semantic version tag:

```powershell
git tag v3.1.1
git push origin v3.1.1
```

The release workflow will:

- build wheel + sdist
- run `twine check`
- run smoke tests against built wheel
- generate release notes from git history
- publish a GitHub release with artifacts

Optional PyPI publish:

- run release workflow manually with `publish_to_pypi=true`, or
- set repository variable `TPP_PUBLISH_PYPI=true` for tag pushes

## Developer Workflow

```powershell
python -m pip install -e .[dev]
pre-commit install
python scripts/ci_validate.py
pytest -q tests/test_cli_integration.py
```

## Security Notes

- Python module bridging is allow-listed
- system stdlib file operations are workspace-sandboxed
- plugin Python hooks are namespace-restricted

## Project Layout

- tpp/
- examples/
- tests/
- docs/
- README.md
- pyproject.toml

## Publish Readiness

This codebase is structured for GitHub publishing and pip installation.

For documentation details:

- docs/language-guide.md
- docs/plugin-guide.md
- docs/web-ide.md
- docs/devops.md
