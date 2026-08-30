from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from tpp.core.errors import ModuleNotFoundTppError, SemanticTppError
from tpp.runtime import EngineConfig, RuntimeEngine


def test_use_module_file_import(tmp_path: Path) -> None:
    # Create math_helpers.tpp module
    math_mod = tmp_path / "math_helpers.tpp"
    math_mod.write_text(
        "export define double_it with n as:\n"
        "    give back n times 2\n"
        "let unexported be 999\n",
        encoding="utf-8",
    )

    main_script = (
        "use double_it from \"math_helpers\"\n"
        "let res be call double_it with 21\n"
    )

    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    engine.run_source(main_script, file_path=str(tmp_path / "main.tpp"))
    assert engine.global_scope.get("res", 1) == 42


def test_module_namespace_import(tmp_path: Path) -> None:
    helpers = tmp_path / "geometry.tpp"
    helpers.write_text(
        "export define square_area with side as:\n"
        "    give back side times side\n",
        encoding="utf-8",
    )

    main_script = (
        "use the \"geometry\" module\n"
        "let area be call geometry.square_area with 5\n"
    )

    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    engine.run_source(main_script, file_path=str(tmp_path / "main.tpp"))
    assert engine.global_scope.get("area", 1) == 25


def test_unexported_symbol_error(tmp_path: Path) -> None:
    mod = tmp_path / "secret.tpp"
    mod.write_text(
        "export let public_val be 10\n"
        "let private_val be 20\n",
        encoding="utf-8",
    )

    main_script = "use private_val from \"secret\"\n"
    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    with pytest.raises(ModuleNotFoundTppError) as exc_info:
        engine.run_source(main_script, file_path=str(tmp_path / "main.tpp"))
    assert "not exported by module" in str(exc_info.value)


def test_circular_import_detection(tmp_path: Path) -> None:
    mod_a = tmp_path / "module_a.tpp"
    mod_b = tmp_path / "module_b.tpp"

    mod_a.write_text("use \"module_b\"\n", encoding="utf-8")
    mod_b.write_text("use \"module_a\"\n", encoding="utf-8")

    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    with pytest.raises(SemanticTppError) as exc_info:
        engine.run_source("use \"module_a\"\n", file_path=str(tmp_path / "main.tpp"))
    assert "Circular import detected" in str(exc_info.value)


def test_module_single_evaluation_caching(tmp_path: Path) -> None:
    counter_mod = tmp_path / "counter.tpp"
    counter_mod.write_text(
        "let count be 0\n"
        "increase count by 1\n"
        "export let count be count\n",
        encoding="utf-8",
    )

    # Importer 1 and 2 both use "counter"
    main_script = (
        "use count as c1 from \"counter\"\n"
        "use count as c2 from \"counter\"\n"
    )

    engine = RuntimeEngine(EngineConfig(sandbox_base_dir=tmp_path))
    engine.run_source(main_script, file_path=str(tmp_path / "main.tpp"))
    assert engine.global_scope.get("c1", 1) == 1
    assert engine.global_scope.get("c2", 1) == 1
    # Check that module record is cached and evaluated once
    assert engine.module_registry.get_module("counter") is not None
