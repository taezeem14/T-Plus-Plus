# T++

> Human-first programming, engineered for real-world software.

[![PyPI version](https://img.shields.io/pypi/v/tpp-language?style=for-the-badge)](https://pypi.org/project/tpp-language/)
[![Python](https://img.shields.io/pypi/pyversions/tpp-language?style=for-the-badge)](https://pypi.org/project/tpp-language/)
[![CI](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/release.yml?style=for-the-badge&label=Release)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-see%20repository-blue?style=for-the-badge)](https://github.com/taezeem14/T-Plus-Plus)

T++ is a next-generation language platform that lets developers write expressive, natural syntax while keeping deterministic runtime behavior, modern tooling, and production CI discipline.

Current stable release: `3.1.3`

Download from PyPI:

```bash
pip install tpp-language
```

## Why T++

- Natural language syntax that remains readable to humans and executable by machines.
- Full CLI workflow for run, repl, test, plugin management, API serving, and diagnostics.
- Extensible plugin system with keyword rewrites and transform hooks.
- Built-in web IDE backend and JSON execution API.
- PyPI distribution for immediate adoption: `pip install tpp-language`.

## Features

- Human-first syntax with strict, fuzzy, and intent parsing modes.
- Modular architecture: parser, runtime engine, stdlib, API, CLI, plugins.
- Test blocks and suites directly in `.tpp` source.
- Configurable project behavior via `.tppconfig`.
- CI/CD-ready repository with matrix validation and release automation.

## Installation

```bash
pip install tpp-language
```

Verify install:

```bash
tpp --version
tpp doctor
```

Local development install:

```bash
python -m pip install -e .[dev]
```

## Usage

Run a script:

```bash
tpp run examples/hello.tpp
```

Start interactive REPL:

```bash
tpp repl
```

Run regression tests:

```bash
tpp test tests/regression.tpp
```

Plugin workflow:

```bash
tpp plugin install examples/sample_plugin.json
tpp plugin list
tpp run examples/plugin_demo.tpp --plugin examples/sample_plugin.json
```

Start API + Web IDE:

```bash
tpp api --serve --host 127.0.0.1 --port 8787
```

Open `http://127.0.0.1:8787/` in your browser.

## Architecture Overview

```text
tpp/
	core/      -> AST, constants, diagnostics, utilities
	parser/    -> lexer, parser, semantic analyzer, optimizer
	runtime/   -> engine, evaluator, environment, interop, profiler
	stdlib/    -> native modules (math, text, system, time)
	plugins/   -> plugin loading, metadata, transforms
	cli/       -> command surface (run/repl/test/plugin/api/doctor)
	api/       -> JSON execution API + web IDE server
```

Design goal: natural syntax at the top, predictable execution at the core.

## Examples

Simple script:

```tpp
say "Hello from T++"
let name be "Developer"
say "Welcome" then name
```

Natural arithmetic and expectations:

```tpp
let x be 4
increase x by 6
expect x to be 10
```

API payload:

```json
{
	"source": "let x be 5\nsay x",
	"mode": "run"
}
```

## Roadmap

- Richer language server and editor integration.
- Expanded standard library and package ecosystem.
- Advanced plugin marketplace and sharing model.
- Enhanced debugging and profiling introspection.
- Cloud-hosted collaborative web IDE experience.

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
