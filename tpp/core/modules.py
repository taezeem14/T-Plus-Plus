from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from tpp.core.errors import ModuleNotFoundTppError, SemanticTppError


@dataclass
class ModuleRecord:
    module_name: str
    file_path: Optional[Path]
    exports: dict[str, Any] = field(default_factory=dict)
    all_symbols: dict[str, Any] = field(default_factory=dict)
    is_native: bool = False
    is_evaluated: bool = False


class ModuleRegistry:
    """Manages loaded T++ modules, caching, resolution, and circular dependency checks."""

    def __init__(self, workspace_root: Optional[Path] = None) -> None:
        self.workspace_root = (workspace_root or Path.cwd()).resolve()
        self.modules: dict[str, ModuleRecord] = {}
        self.loading_stack: list[str] = []

    def resolve_module_path(self, module_name: str, importing_file: Optional[Path] = None) -> Optional[Path]:
        """Resolves a module name or relative path to a .tpp file."""
        clean_name = module_name.strip("\"' ")

        # 1. Check relative to importing file
        if importing_file is not None:
            parent = importing_file.parent if importing_file.is_file() else importing_file
            candidate = (parent / clean_name).resolve()
            if candidate.is_file():
                return candidate
            candidate_tpp = (parent / f"{clean_name}.tpp").resolve()
            if candidate_tpp.is_file():
                return candidate_tpp

        # 2. Check relative to workspace root
        candidate = (self.workspace_root / clean_name).resolve()
        if candidate.is_file():
            return candidate
        candidate_tpp = (self.workspace_root / f"{clean_name}.tpp").resolve()
        if candidate_tpp.is_file():
            return candidate_tpp

        # 3. Check modules/ subdirectory in workspace
        candidate_sub = (self.workspace_root / "modules" / f"{clean_name}.tpp").resolve()
        if candidate_sub.is_file():
            return candidate_sub

        return None

    def begin_loading(self, module_name: str, line: Optional[int] = None) -> None:
        """Tracks the loading stack for circular import detection."""
        if module_name in self.loading_stack:
            cycle = " -> ".join(self.loading_stack + [module_name])
            raise SemanticTppError(
                f"Circular import detected: {cycle}",
                line=line,
                suggestion="Refactor shared symbols into a separate module to break the import cycle.",
            )
        self.loading_stack.append(module_name)

    def finish_loading(self, module_name: str) -> None:
        if self.loading_stack and self.loading_stack[-1] == module_name:
            self.loading_stack.pop()

    def register_module(self, record: ModuleRecord) -> None:
        self.modules[record.module_name] = record

    def get_module(self, module_name: str) -> Optional[ModuleRecord]:
        clean_name = module_name.strip("\"' ")
        return self.modules.get(clean_name)
