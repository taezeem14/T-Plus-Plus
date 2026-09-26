from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SynonymEntry:
    natural_spelling: str
    symbol_spelling: str
    category: str
    description: str
    source: str = "core"  # "core" or plugin name


# Canonical Centralized Table of Synonym Mappings in T++
SYNONYM_TABLE: list[SynonymEntry] = [
    # --- Operators & Arithmetic ---
    SynonymEntry("plus", "+", "arithmetic", "Addition operator"),
    SynonymEntry("minus", "-", "arithmetic", "Subtraction operator"),
    SynonymEntry("times", "*", "arithmetic", "Multiplication operator"),
    SynonymEntry("multiplied by", "*", "arithmetic", "Multiplication phrase"),
    SynonymEntry("divided by", "/", "arithmetic", "Division operator"),
    SynonymEntry("modulo", "%", "arithmetic", "Modulo remainder operator"),
    SynonymEntry("mod", "%", "arithmetic", "Modulo remainder short form"),
    SynonymEntry("to the power of", "**", "arithmetic", "Exponentiation operator"),
    SynonymEntry("raised to the power of", "**", "arithmetic", "Exponentiation phrase"),
    SynonymEntry("raised to", "**", "arithmetic", "Exponentiation short phrase"),

    # --- Comparisons ---
    SynonymEntry("is equal to", "==", "comparison", "Equality comparison"),
    SynonymEntry("equal to", "==", "comparison", "Equality comparison without is"),
    SynonymEntry("is the same as", "==", "comparison", "Equality phrase"),
    SynonymEntry("is not equal to", "!=", "comparison", "Inequality comparison"),
    SynonymEntry("not equal to", "!=", "comparison", "Inequality comparison without is"),
    SynonymEntry("does not equal", "!=", "comparison", "Inequality phrase"),
    SynonymEntry("is different from", "!=", "comparison", "Inequality difference phrase"),
    SynonymEntry("is not", "!=", "comparison", "Inequality comparison short form"),
    SynonymEntry("is greater than", ">", "comparison", "Strictly greater than"),
    SynonymEntry("greater than", ">", "comparison", "Strictly greater than without is"),
    SynonymEntry("is less than", "<", "comparison", "Strictly less than"),
    SynonymEntry("less than", "<", "comparison", "Strictly less than without is"),
    SynonymEntry("is at least", ">=", "comparison", "Greater than or equal to"),
    SynonymEntry("at least", ">=", "comparison", "Greater than or equal to without is"),
    SynonymEntry("is at most", "<=", "comparison", "Less than or equal to"),
    SynonymEntry("at most", "<=", "comparison", "Less than or equal to without is"),
    SynonymEntry("is greater than or equal to", ">=", "comparison", "Greater than or equal to long form"),
    SynonymEntry("greater than or equal to", ">=", "comparison", "Greater than or equal to without is"),
    SynonymEntry("is less than or equal to", "<=", "comparison", "Less than or equal to long form"),
    SynonymEntry("less than or equal to", "<=", "comparison", "Less than or equal to without is"),
    SynonymEntry("is in", "in", "comparison", "Membership test"),
    SynonymEntry("is not in", "not in", "comparison", "Non-membership test"),

    # --- Control Flow ---
    SynonymEntry("otherwise if", "else if", "control_flow", "Else-if branch"),
    SynonymEntry("otherwise", "else", "control_flow", "Else fallback branch"),
    SynonymEntry("stop the loop", "break", "control_flow", "Loop break"),
    SynonymEntry("skip to the next", "continue", "control_flow", "Loop continue"),
    SynonymEntry("give back", "return", "control_flow", "Function return"),
    SynonymEntry("do nothing", "pass", "control_flow", "No-op statement"),

    # --- Collections & Access ---
    SynonymEntry("a list containing", "[...]", "literal", "List literal long form"),
    SynonymEntry("a record with", "{...}", "literal", "Record literal long form"),
    SynonymEntry("a set containing", "{...}", "literal", "Set literal long form"),
    SynonymEntry("nothing", "none", "literal", "Empty/null value"),
]


class SynonymRegistry:
    """Provides lookup and validation for natural phrases and their symbol synonyms."""

    def __init__(self) -> None:
        self._entries: list[SynonymEntry] = list(SYNONYM_TABLE)
        self._natural_to_symbol: dict[str, str] = {e.natural_spelling: e.symbol_spelling for e in self._entries}
        self._symbol_to_natural: dict[str, str] = {e.symbol_spelling: e.natural_spelling for e in self._entries}

    def register(self, entry: SynonymEntry) -> None:
        self._entries.append(entry)
        self._natural_to_symbol[entry.natural_spelling] = entry.symbol_spelling
        self._symbol_to_natural[entry.symbol_spelling] = entry.natural_spelling

    def get(self, natural: str) -> Optional[SynonymEntry]:
        low = natural.lower().strip()
        for e in self._entries:
            if e.natural_spelling.lower() == low:
                return e
        return None

    def get_symbol_for(self, natural: str) -> Optional[str]:
        return self._natural_to_symbol.get(natural.lower().strip())

    def get_natural_for(self, symbol: str) -> Optional[str]:
        return self._symbol_to_natural.get(symbol.strip())

    def all_entries(self) -> list[SynonymEntry]:
        return list(self._entries)


GLOBAL_SYNONYMS = SynonymRegistry()
