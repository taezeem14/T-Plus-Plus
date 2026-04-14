# Contributing to T++

## Development Setup

```powershell
python -m pip install --upgrade pip
python -m pip install -e .[dev]
pre-commit install
```

## Local Validation

```powershell
python -m compileall -q tpp
tpp doctor
python scripts/ci_validate.py
pytest -q tests/test_cli_integration.py
```

## CI and Releases

- Continuous validation workflow: .github/workflows/ci.yml
- Release workflow: .github/workflows/release.yml

Release tags must follow semantic version format:

- vX.Y.Z

Optional PyPI publish:

- Manual dispatch input: publish_to_pypi=true
- Or set repository variable: TPP_PUBLISH_PYPI=true (for tag pushes)
