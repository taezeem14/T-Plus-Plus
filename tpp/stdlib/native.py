from __future__ import annotations

import datetime
import json
import math
import os
import random
import re
import time as pytime
from pathlib import Path
from typing import Any, Callable, Optional

from tpp.core.errors import SecurityTppError, TypeTppError


class NativeModule:
    def __init__(self, name: str, members: dict[str, Any]) -> None:
        self.__name = name
        self.__members = members

    @property
    def name(self) -> str:
        return self.__name

    @property
    def members(self) -> list[str]:
        return list(self.__members.keys())

    def has_member(self, key: str) -> bool:
        return key in self.__members

    def member(self, key: str) -> Any:
        return self.__members[key]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.__members)

    def __getattr__(self, item: str) -> Any:
        if item in self.__members:
            return self.__members[item]
        raise AttributeError(f"{self.__name} has no attribute {item}")

    def __repr__(self) -> str:
        return f"<NativeModule {self.__name}>"


def _safe_divide(a: float, b: float) -> float:
    if b == 0:
        raise ZeroDivisionError("Cannot divide by zero")
    return a / b


def _safe_sleep(seconds: float) -> None:
    if seconds < 0:
        raise ValueError("Sleep duration must be non-negative")
    if seconds > 30:
        raise ValueError("Sleep duration is capped at 30 seconds for safety")
    pytime.sleep(seconds)


def _resolve_path(base_dir: Path, raw_path: str) -> Path:
    requested = Path(raw_path)
    if requested.is_absolute():
        resolved = requested.resolve()
    else:
        resolved = (base_dir / requested).resolve()

    base_resolved = base_dir.resolve()
    try:
        resolved.relative_to(base_resolved)
    except ValueError as exc:
        raise SecurityTppError(f"System module cannot access path '{raw_path}' outside workspace sandbox '{base_resolved}'.") from exc
    return resolved


def _is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


# ==========================================
# 1. MATH MODULE
# ==========================================
def build_math_module() -> NativeModule:
    def _average(items: list[float]) -> float:
        if not items:
            return 0.0
        return sum(items) / len(items)

    def _median(items: list[float]) -> float:
        if not items:
            return 0.0
        s = sorted(items)
        n = len(s)
        mid = n // 2
        if n % 2 == 1:
            return float(s[mid])
        return (s[mid - 1] + s[mid]) / 2.0

    return NativeModule(
        "math",
        {
            "add": lambda a, b: a + b,
            "subtract": lambda a, b: a - b,
            "multiply": lambda a, b: a * b,
            "divide": _safe_divide,
            "power": lambda a, b: a**b,
            "sqrt": math.sqrt,
            "square_root": math.sqrt,
            "sin": math.sin,
            "sine": math.sin,
            "cos": math.cos,
            "cosine": math.cos,
            "tan": math.tan,
            "tangent": math.tan,
            "log": lambda n, base=math.e: math.log(n, base),
            "floor": math.floor,
            "round_down": math.floor,
            "ceil": math.ceil,
            "round_up": math.ceil,
            "round": lambda n, decimals=0: round(n, decimals) if decimals > 0 else round(n),
            "round_number": lambda n, decimals=0: round(n, decimals) if decimals > 0 else round(n),
            "abs": abs,
            "absolute_value": abs,
            "average": _average,
            "median": _median,
            "sum": sum,
            "sum_items": sum,
            "min": min,
            "min_item": min,
            "max": max,
            "max_item": max,
            "is_even": lambda n: n % 2 == 0,
            "is_odd": lambda n: n % 2 != 0,
            "is_prime": _is_prime,
            "random_number": lambda low=0.0, high=1.0: random.uniform(low, high),
            "random_integer": lambda low=1, high=100: random.randint(low, high),
            "pi": math.pi,
            "tau": math.tau,
            "e": math.e,
        },
    )


# ==========================================
# 2. TEXT MODULE
# ==========================================
def build_text_module() -> NativeModule:
    def _format_currency(amount: float, symbol: str = "$") -> str:
        return f"{symbol}{amount:,.2f}"

    def _format_number(amount: float, decimals: int = 2) -> str:
        return f"{amount:,.{decimals}f}"

    return NativeModule(
        "text",
        {
            "upper": lambda s: str(s).upper(),
            "uppercase": lambda s: str(s).upper(),
            "lower": lambda s: str(s).lower(),
            "lowercase": lambda s: str(s).lower(),
            "title": lambda s: str(s).title(),
            "capitalized": lambda s: str(s).capitalize(),
            "strip": lambda s, chars=None: str(s).strip(str(chars) if chars is not None else None),
            "trimmed": lambda s, chars=None: str(s).strip(str(chars) if chars is not None else None),
            "padded": lambda s, length, fill=" ": str(s).rjust(int(length), str(fill)),
            "replace": lambda s, old, new: str(s).replace(str(old), str(new)),
            "contains": lambda s, needle: str(needle) in str(s),
            "position_of": lambda s, sub: str(s).find(str(sub)),
            "split": lambda s, sep=None: str(s).split(sep),
            "join": lambda sep, items: str(sep).join(str(item) for item in items),
            "format": lambda template, *args, **kwargs: str(template).format(*args, **kwargs),
            "format_number": _format_number,
            "format_currency": _format_currency,
            "length": lambda s: len(str(s)),
            "length_of": lambda s: len(str(s)),
            "reversed": lambda s: str(s)[::-1],
            "reversed_text": lambda s: str(s)[::-1],
            "starts_with": lambda s, prefix: str(s).startswith(str(prefix)),
            "ends_with": lambda s, suffix: str(s).endswith(str(suffix)),
            "matches_pattern": lambda s, pattern: bool(re.search(str(pattern), str(s))),
            "words_in": lambda s: [w for w in re.split(r"\s+", str(s).strip()) if w],
        },
    )


# ==========================================
# 3. COLLECTIONS MODULE
# ==========================================
def build_collections_module() -> NativeModule:
    def _map(fn: Callable[[Any], Any], items: list[Any]) -> list[Any]:
        return [fn(item) for item in items]

    def _filter(fn: Callable[[Any], bool], items: list[Any]) -> list[Any]:
        return [item for item in items if fn(item)]

    def _reduce(fn: Callable[[Any, Any], Any], items: list[Any], initial: Any = None) -> Any:
        if not items:
            return initial
        it = iter(items)
        acc = initial if initial is not None else next(it)
        for val in it:
            acc = fn(acc, val)
        return acc

    def _group_by(fn: Callable[[Any], Any], items: list[Any]) -> dict[Any, list[Any]]:
        result: dict[Any, list[Any]] = {}
        for item in items:
            key = fn(item)
            result.setdefault(key, []).append(item)
        return result

    def _flatten(nested: list[Any]) -> list[Any]:
        res = []
        for item in nested:
            if isinstance(item, (list, tuple)):
                res.extend(_flatten(list(item)))
            else:
                res.append(item)
        return res

    def _chunk(items: list[Any], size: int) -> list[list[Any]]:
        s = max(1, int(size))
        return [items[i : i + s] for i in range(0, len(items), s)]

    return NativeModule(
        "collections",
        {
            "map_items": _map,
            "filter_items": _filter,
            "reduce_items": _reduce,
            "sort_items": lambda items, key=None, reverse=False: sorted(items, key=key, reverse=reverse),
            "group_by": _group_by,
            "union": lambda a, b: list(set(a) | set(b)),
            "intersection": lambda a, b: list(set(a) & set(b)),
            "difference": lambda a, b: list(set(a) - set(b)),
            "flatten": _flatten,
            "zip_items": lambda a, b: [list(pair) for pair in zip(a, b)],
            "take_first": lambda items, n: items[: int(n)],
            "take_last": lambda items, n: items[-int(n) :] if int(n) > 0 else [],
            "unique_items": lambda items: list(dict.fromkeys(items)),
            "chunk_items": _chunk,
        },
    )


# ==========================================
# 4. SYSTEM MODULE (SANDBOXED FILE I/O)
# ==========================================
def build_system_module(base_dir: Path) -> NativeModule:
    def read_text(path: str, encoding: str = "utf-8") -> str:
        resolved = _resolve_path(base_dir, path)
        return resolved.read_text(encoding=encoding)

    def write_text(path: str, content: str, encoding: str = "utf-8") -> str:
        resolved = _resolve_path(base_dir, path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(str(content), encoding=encoding)
        return str(resolved)

    def append_text(path: str, content: str, encoding: str = "utf-8") -> str:
        resolved = _resolve_path(base_dir, path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("a", encoding=encoding) as f:
            f.write(str(content))
        return str(resolved)

    def list_dir(path: str = ".") -> list[str]:
        resolved = _resolve_path(base_dir, path)
        return sorted(entry.name + ("/" if entry.is_dir() else "") for entry in resolved.iterdir())

    def read_json(path: str, encoding: str = "utf-8") -> Any:
        return json.loads(read_text(path, encoding))

    def write_json(path: str, payload: Any, encoding: str = "utf-8") -> str:
        return write_text(path, json.dumps(payload, indent=2), encoding)

    return NativeModule(
        "system",
        {
            "cwd": lambda: str(base_dir.resolve()),
            "exists": lambda path: _resolve_path(base_dir, path).exists(),
            "file_exists": lambda path: _resolve_path(base_dir, path).exists(),
            "read_text": read_text,
            "read_file": read_text,
            "write_text": write_text,
            "write_file": write_text,
            "append_text": append_text,
            "append_file": append_text,
            "list_dir": list_dir,
            "list_files": list_dir,
            "read_json": read_json,
            "write_json": write_json,
            "get_env": lambda key, default=None: os.environ.get(str(key), default),
            "allowlisted_env_var": lambda key, default=None: os.environ.get(str(key), default),
            "command_line_arguments": lambda: list(os.sys.argv[1:] if hasattr(os, "sys") else []),
        },
    )


# ==========================================
# 5. TIME MODULE
# ==========================================
def build_time_module() -> NativeModule:
    def _shift_time(
        iso_str: Optional[str] = None,
        days: int = 0,
        hours: int = 0,
        minutes: int = 0,
        seconds: int = 0,
    ) -> str:
        base = datetime.datetime.fromisoformat(iso_str.replace("Z", "+00:00")) if iso_str else datetime.datetime.now(datetime.timezone.utc)
        shifted = base + datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
        return shifted.isoformat()

    def _diff_seconds(t1_iso: str, t2_iso: str) -> float:
        d1 = datetime.datetime.fromisoformat(t1_iso.replace("Z", "+00:00"))
        d2 = datetime.datetime.fromisoformat(t2_iso.replace("Z", "+00:00"))
        return abs((d1 - d2).total_seconds())

    return NativeModule(
        "time",
        {
            "now": lambda: pytime.time(),
            "current_moment": lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "timestamp": lambda: pytime.time(),
            "timestamp_now": lambda: pytime.time(),
            "millis": lambda: int(pytime.time() * 1000),
            "sleep": _safe_sleep,
            "sleep_seconds": _safe_sleep,
            "iso_now": lambda: datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "format_moment": lambda dt_iso, fmt="%Y-%m-%d %H:%M:%S": datetime.datetime.fromisoformat(str(dt_iso).replace("Z", "+00:00")).strftime(fmt),
            "parse_moment": lambda s, fmt="%Y-%m-%d %H:%M:%S": datetime.datetime.strptime(str(s), fmt).isoformat(),
            "time_difference": _diff_seconds,
            "shift_time": _shift_time,
        },
    )


# ==========================================
# 6. JSON MODULE
# ==========================================
def build_json_module() -> NativeModule:
    return NativeModule(
        "json",
        {
            "parse": lambda s: json.loads(str(s)),
            "parse_json": lambda s: json.loads(str(s)),
            "stringify": lambda obj, indent=None: json.dumps(obj, indent=indent),
            "to_json": lambda obj, indent=None: json.dumps(obj, indent=indent),
        },
    )


# ==========================================
# 7. VALIDATE MODULE
# ==========================================
def build_validate_module() -> NativeModule:
    email_regex = re.compile(r"^[\w\.\+\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z0-9\-\.]+$")

    def _is_valid_number(val: Any) -> bool:
        try:
            float(val)
            return True
        except (ValueError, TypeError):
            return False

    return NativeModule(
        "validate",
        {
            "is_valid_email": lambda s: bool(email_regex.match(str(s).strip())),
            "is_valid_number": _is_valid_number,
            "is_within_range": lambda v, low, high: low <= float(v) <= high,
            "is_not_nothing": lambda v: v is not None and type(v).__name__ != "TppNothing",
            "is_empty": lambda v: len(v) == 0 if hasattr(v, "__len__") else v is None,
        },
    )


def create_native_stdlib_registry(base_dir: Optional[Path] = None) -> dict[str, NativeModule]:
    effective_base = base_dir if base_dir is not None else Path.cwd()
    return {
        "math": build_math_module(),
        "text": build_text_module(),
        "collections": build_collections_module(),
        "system": build_system_module(effective_base),
        "time": build_time_module(),
        "json": build_json_module(),
        "validate": build_validate_module(),
    }
