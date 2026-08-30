from __future__ import annotations

import re
from typing import Any, Optional

from tpp.core.ast_nodes import TypeAnnotation, UnionTypeAnnotation
from tpp.core.errors import TypeTppError


class TppNothing:
    """Singleton representing the 'nothing' value in T++."""
    _instance: Optional[TppNothing] = None

    def __new__(cls) -> TppNothing:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self) -> str:
        return "nothing"

    def __str__(self) -> str:
        return "nothing"

    def __bool__(self) -> bool:
        return False


NOTHING = TppNothing()


def parse_type_annotation(text: str, line: int = 1) -> Optional[TypeAnnotation | UnionTypeAnnotation]:
    """Parses a natural language type annotation string into a TypeAnnotation or UnionTypeAnnotation."""
    cleaned = text.strip()
    if not cleaned:
        return None

    # Check for 'or' union (e.g. 'a number or nothing', 'text or a number')
    if " or " in cleaned:
        parts = [p.strip() for p in cleaned.split(" or ")]
        parsed_types: list[TypeAnnotation] = []
        for part in parts:
            ann = parse_type_annotation(part, line)
            if isinstance(ann, TypeAnnotation):
                parsed_types.append(ann)
            elif isinstance(ann, UnionTypeAnnotation):
                parsed_types.extend(ann.types)
        if len(parsed_types) == 1:
            return parsed_types[0]
        return UnionTypeAnnotation(line=line, types=parsed_types)

    # Function type: 'a function that takes <types> and gives back <type>'
    fn_match = re.match(r"^a\s+function\s+that\s+takes\s+(.+?)\s+and\s+gives\s+back\s+(.+)$", cleaned, re.IGNORECASE)
    if fn_match:
        raw_params = fn_match.group(1).strip()
        raw_ret = fn_match.group(2).strip()
        param_parts = [p.strip() for p in re.split(r"\s+and\s+", raw_params)]
        param_types = [parse_type_annotation(p, line) for p in param_parts]
        valid_params = [p for p in param_types if isinstance(p, TypeAnnotation)]
        ret_type = parse_type_annotation(raw_ret, line)
        ret_ann = ret_type if isinstance(ret_type, TypeAnnotation) else None
        return TypeAnnotation(line=line, name="function", param_types=valid_params, return_type=ret_ann)

    # List of type: 'a list of <type>'
    list_of_match = re.match(r"^a\s+list\s+of\s+(.+)$", cleaned, re.IGNORECASE)
    if list_of_match:
        elem_text = list_of_match.group(1).strip()
        elem_ann = parse_type_annotation(elem_text, line)
        return TypeAnnotation(
            line=line,
            name="list",
            element_type=elem_ann if isinstance(elem_ann, TypeAnnotation) else None,
        )

    # Base types
    lowered = cleaned.lower()
    if lowered.startswith("a ") or lowered.startswith("an "):
        lowered = lowered.split(" ", 1)[1]

    if lowered in {"number", "num", "float"}:
        return TypeAnnotation(line=line, name="number")
    if lowered in {"whole number", "int", "integer"}:
        return TypeAnnotation(line=line, name="whole number")
    if lowered in {"text", "str", "string"}:
        return TypeAnnotation(line=line, name="text")
    if lowered in {"boolean", "bool"}:
        return TypeAnnotation(line=line, name="boolean")
    if lowered in {"nothing", "none"}:
        return TypeAnnotation(line=line, name="nothing")
    if lowered in {"list", "array"}:
        return TypeAnnotation(line=line, name="list")
    if lowered in {"record", "map", "dict"}:
        return TypeAnnotation(line=line, name="record")
    if lowered in {"function", "fn"}:
        return TypeAnnotation(line=line, name="function")

    # Custom type / record name
    return TypeAnnotation(line=line, name=cleaned.strip())


def is_value_compatible_with_type(val: Any, type_ann: TypeAnnotation | UnionTypeAnnotation) -> bool:
    """Checks if a runtime value is compatible with a given type annotation."""
    if isinstance(type_ann, UnionTypeAnnotation):
        return any(is_value_compatible_with_type(val, t) for t in type_ann.types)

    if not isinstance(type_ann, TypeAnnotation):
        return True

    name = type_ann.name

    # Check 'nothing'
    if val is None or isinstance(val, TppNothing):
        return name == "nothing" or type_ann.is_optional

    if name == "nothing":
        return val is None or isinstance(val, TppNothing)

    # 'whole number': Must be int, not bool, strictly rejecting float
    if name == "whole number":
        return isinstance(val, int) and not isinstance(val, bool)

    # 'number': int or float, but not bool (since bool is a subclass of int in Python)
    if name == "number":
        return (isinstance(val, (int, float)) and not isinstance(val, bool))

    # 'text'
    if name == "text":
        return isinstance(val, str)

    # 'boolean'
    if name == "boolean":
        return isinstance(val, bool)

    # 'list'
    if name == "list":
        if not isinstance(val, (list, tuple)):
            return False
        if type_ann.element_type:
            return all(is_value_compatible_with_type(item, type_ann.element_type) for item in val)
        return True

    # 'record'
    if name == "record":
        return isinstance(val, dict) or hasattr(val, "fields")

    # 'function'
    if name == "function":
        return callable(val)

    # Custom nominal type (e.g. TppInstance with matching class/record name)
    if hasattr(val, "record_type_name"):
        return getattr(val, "record_type_name") == name
    if hasattr(val, "cls_name"):
        return getattr(val, "cls_name") == name

    # Default fallback for untyped / custom
    return True


def check_type_or_raise(
    val: Any,
    type_ann: Optional[TypeAnnotation | UnionTypeAnnotation],
    var_or_param_name: str,
    line: Optional[int] = None,
    source_line: Optional[str] = None,
) -> None:
    """Validates that a value matches the annotation, raising a clear TypeTppError if not."""
    if type_ann is None:
        return

    if not is_value_compatible_with_type(val, type_ann):
        val_type_str = type(val).__name__
        if isinstance(val, bool):
            val_type_str = "a boolean"
        elif isinstance(val, int):
            val_type_str = "a whole number"
        elif isinstance(val, float):
            val_type_str = "a number (float)"
        elif isinstance(val, str):
            val_type_str = "text"
        elif val is None or isinstance(val, TppNothing):
            val_type_str = "nothing"
        elif isinstance(val, list):
            val_type_str = "a list"
        elif isinstance(val, dict):
            val_type_str = "a record"

        raise TypeTppError(
            f"Type mismatch for '{var_or_param_name}': expected {type_ann}, but got {val_type_str} ({repr(val)}).",
            line=line,
            suggestion=f"Provide a value compatible with {type_ann}.",
            source_line=source_line,
        )
