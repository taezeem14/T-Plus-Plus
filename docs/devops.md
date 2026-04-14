# T++ DevOps and Release Automation

## Continuous Validation Workflow

File: `.github/workflows/ci.yml`

Trigger:

- push
- pull_request

Validation stages:

1. Install package with `pip install .`
2. Compile check with `python -m compileall -q tpp`
3. Lint with `ruff check tpp tests scripts`
4. CLI validation script (`python scripts/ci_validate.py`)
5. Python integration tests (`pytest -q tests/test_cli_integration.py`)

Matrix:

- Ubuntu: Python 3.10, 3.11, 3.12, 3.13
- Windows: Python 3.12

Artifacts:

- `.ci-artifacts` logs are uploaded for every job run.

## Release Workflow

File: `.github/workflows/release.yml`

Trigger:

- tag push matching `v*`
- manual dispatch (`workflow_dispatch`)

Release stages:

1. Build artifacts with `python -m build`
2. Validate with `python -m twine check dist/*`
3. Smoke-test built wheel (`tpp --version`, `tpp run`, `tpp test`, `scripts/ci_validate.py`)
4. Generate release changelog from git commits
5. Publish GitHub Release with wheel and sdist assets
6. Optionally publish to PyPI

Optional PyPI behavior:

- Set workflow input `publish_to_pypi=true`, or
- Set repository variable `TPP_PUBLISH_PYPI=true`

## Local Equivalents

```powershell
python -m pip install -e .[dev]
python -m compileall -q tpp
ruff check tpp tests scripts
python scripts/ci_validate.py
pytest -q tests/test_cli_integration.py
```
