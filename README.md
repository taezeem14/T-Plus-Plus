# T++

> Human-first programming, engineered for real-world software.

[![PyPI version](https://img.shields.io/pypi/v/tpp-language?style=for-the-badge)](https://pypi.org/project/tpp-language/)
[![Python](https://img.shields.io/pypi/pyversions/tpp-language?style=for-the-badge)](https://pypi.org/project/tpp-language/)
[![CI](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/ci.yml?branch=main&style=for-the-badge&label=CI)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/actions/workflow/status/taezeem14/T-Plus-Plus/release.yml?style=for-the-badge&label=Release)](https://github.com/taezeem14/T-Plus-Plus/actions/workflows/release.yml)
[![License](https://img.shields.io/badge/license-see%20repository-blue?style=for-the-badge)](https://github.com/taezeem14/T-Plus-Plus)

T++ is a next-generation language platform that lets developers write expressive, natural syntax while keeping deterministic runtime behavior, modern tooling, and production CI discipline.

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

## Documentation

- Language guide: `docs/language-guide.md`
- Plugin guide: `docs/plugin-guide.md`
- Web IDE guide: `docs/web-ide.md`
- DevOps and release automation: `docs/devops.md`

## Build With T++

If you want code that reads closer to intent than syntax, start with one file:

```bash
tpp run examples/hello.tpp
```

T++ is built to feel approachable on day one and scalable by day one hundred.
