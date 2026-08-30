from __future__ import annotations

from pathlib import Path
import pytest

from tpp.core.errors import PluginTppError
from tpp.plugins import PluginManager
from tpp.runtime import EngineConfig, RuntimeEngine


def test_load_formalized_manifest(tmp_path: Path) -> None:
    plugin_file = Path("examples/plugins/keyword_synonym.json")
    manager = PluginManager()
    metadata = manager.load_file(plugin_file)
    assert metadata.name == "spanish_keywords"
    assert metadata.manifest_version == 1
    assert "decir" in manager.keywords


def test_plugin_keyword_and_synonym_execution() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    engine.load_plugin("examples/plugins/keyword_synonym.json")
    source = (
        "definir funcion sumar with a and b:\n"
        "    give back a mas b\n"
        "let res be call sumar with 10 and 5\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("res", 1) == 15


def test_ast_transform_plugin() -> None:
    engine = RuntimeEngine(EngineConfig(parser_mode="fuzzy"))
    engine.load_plugin("examples/plugins/ast_transform.json")
    source = (
        "define old_calculate with x as:\n"
        "    give back x times 3\n"
        "let ans be call calculate with 7\n"
    )
    engine.run_source(source)
    assert engine.global_scope.get("ans", 1) == 21
