from __future__ import annotations

import re
from dataclasses import dataclass

from tpp.core.ast_nodes import Token
from tpp.core.errors import RuntimeTppError
from tpp.parser.synonyms import GLOBAL_SYNONYMS


@dataclass
class LexerStats:
    cache_hits: int = 0
    cache_misses: int = 0


class ExpressionTokenizer:
    """Tokenizer that understands multi-word English operators and natural possessive access."""

    PHRASE_OPS: list[tuple[tuple[str, ...], str]] = [
        (("to", "the", "power", "of"), "**"),
        (("raised", "to", "the", "power", "of"), "**"),
        (("raised", "to"), "**"),
        (("multiplied", "by"), "*"),
        (("divided", "by"), "/"),
        (("is", "greater", "than", "or", "equal", "to"), ">="),
        (("is", "less", "than", "or", "equal", "to"), "<="),
        (("is", "the", "same", "as"), "=="),
        (("is", "different", "from"), "!="),
        (("does", "not", "equal"), "!="),
        (("is", "greater", "than"), ">"),
        (("is", "less", "than"), "<"),
        (("is", "at", "least"), ">="),
        (("is", "at", "most"), "<="),
        (("is", "not", "equal", "to"), "!="),
        (("is", "not"), "!="),
        (("is", "equal", "to"), "=="),
        (("is", "not", "in"), "not in"),
        (("is", "in"), "in"),
        (("greater", "than", "or", "equal", "to"), ">="),
        (("less", "than", "or", "equal", "to"), "<="),
        (("greater", "than"), ">"),
        (("less", "than"), "<"),
        (("not", "equal", "to"), "!="),
        (("equal", "to"), "=="),
        (("at", "least"), ">="),
        (("at", "most"), "<="),
    ]

    WORD_OPS = {
        "plus": "+",
        "minus": "-",
        "times": "*",
        "modulo": "%",
        "mod": "%",
        "and": "and",
        "or": "or",
        "not": "not",
        "in": "in",
        "is": "==",
    }

    SYMBOLS = set("()[]{}.,:")

    def __init__(self) -> None:
        self._sorted_phrases = sorted(self.PHRASE_OPS, key=lambda pair: len(pair[0]), reverse=True)
        self._python_expr_cache: dict[str, str] = {}
        self.stats = LexerStats()

    def clear_cache(self) -> None:
        self._python_expr_cache.clear()
        self.stats = LexerStats()

    def preprocess_natural_sugar(self, text: str) -> str:
        """Preprocesses natural possessive phrases (person's name -> person.name) and between,
        ensuring string literals are protected from accidental mutation."""
        # Protect string literals from being rewritten
        string_placeholders: list[str] = []

        def _mask_string(match: re.Match[str]) -> str:
            idx = len(string_placeholders)
            string_placeholders.append(match.group(0))
            return f"\x00TPPSTR{idx}\x00"

        # Mask string literals in a single regex pass
        masked = re.sub(r'("(?:\\.|[^"\\])*"|(?<![A-Za-z0-9_\)\]])\'(?:\\.|[^\'\\])*\')', _mask_string, text)

        # 1. Possessive sugar: 'person's name' or "item's is_done" -> 'person.name'
        # Handle 's identifier
        processed = re.sub(r"([A-Za-z0-9_\)\]\x00])'s\s+([A-Za-z_][A-Za-z0-9_]*)", r"\1.\2", masked)

        # 2. Desugar 'X is between Y and Z' -> '(Y <= X <= Z)' for all occurrences
        while True:
            between_match = re.search(
                r"([A-Za-z0-9_\.\(\)\[\]\x00]+)\s+is\s+between\s+(.+?)\s+and\s+([A-Za-z0-9_\.\(\)\[\]\x00]+)",
                processed,
            )
            if not between_match:
                break
            var_part = between_match.group(1).strip()
            low_part = between_match.group(2).strip()
            high_part = between_match.group(3).strip()
            repl = f"({low_part} <= {var_part} <= {high_part})"
            processed = processed[:between_match.start()] + repl + processed[between_match.end():]

        # Restore string literals in reverse order
        for idx in range(len(string_placeholders) - 1, -1, -1):
            processed = processed.replace(f"\x00TPPSTR{idx}\x00", string_placeholders[idx])

        return processed

    def tokenize(self, text: str, line: int) -> list[Token]:
        preprocessed = self.preprocess_natural_sugar(text)
        raw: list[Token] = []
        i = 0
        while i < len(preprocessed):
            ch = preprocessed[i]
            if ch.isspace():
                i += 1
                continue
            if ch in ("\"", "'"):
                start = i
                quote = ch
                i += 1
                escaped = False
                while i < len(preprocessed):
                    curr = preprocessed[i]
                    if curr == quote and not escaped:
                        i += 1
                        break
                    escaped = curr == "\\" and not escaped
                    if curr != "\\":
                        escaped = False
                    i += 1
                else:
                    raise RuntimeTppError("Unterminated string literal.", line)
                raw.append(Token("string", preprocessed[start:i], line, start + 1))
                continue
            if ch.isdigit():
                start = i
                has_dot = False
                while i < len(preprocessed) and (preprocessed[i].isdigit() or (preprocessed[i] == "." and not has_dot)):
                    if preprocessed[i] == ".":
                        # Lookahead: is the next character a digit?
                        if i + 1 < len(preprocessed) and preprocessed[i + 1].isdigit():
                            has_dot = True
                        else:
                            break
                    i += 1
                raw.append(Token("number", preprocessed[start:i], line, start + 1))
                continue
            if ch.isalpha() or ch == "_":
                start = i
                while i < len(preprocessed) and (preprocessed[i].isalnum() or preprocessed[i] == "_"):
                    i += 1
                raw.append(Token("word", preprocessed[start:i], line, start + 1))
                continue
            if preprocessed.startswith("**", i):
                raw.append(Token("op", "**", line, i + 1))
                i += 2
                continue
            if preprocessed.startswith(">=", i) or preprocessed.startswith("<=", i) or preprocessed.startswith("!=", i) or preprocessed.startswith("==", i):
                raw.append(Token("op", preprocessed[i : i + 2], line, i + 1))
                i += 2
                continue
            if ch in "+-*/%><":
                raw.append(Token("op", ch, line, i + 1))
                i += 1
                continue
            if ch in self.SYMBOLS:
                raw.append(Token("symbol", ch, line, i + 1))
                i += 1
                continue
            raise RuntimeTppError(f"Unexpected character '{ch}' in expression.", line)

        return self._merge_multi_word_tokens(raw)

    def _merge_multi_word_tokens(self, raw: list[Token]) -> list[Token]:
        merged: list[Token] = []
        i = 0
        while i < len(raw):
            token = raw[i]
            if token.kind != "word":
                merged.append(token)
                i += 1
                continue

            matched = False
            for phrase_words, replacement in self._sorted_phrases:
                end = i + len(phrase_words)
                if end > len(raw):
                    continue
                phrase_slice = raw[i:end]
                if not all(piece.kind == "word" for piece in phrase_slice):
                    continue
                lowered = tuple(piece.value.lower() for piece in phrase_slice)
                if lowered == phrase_words:
                    merged.append(Token("op", replacement, token.line, token.col))
                    i = end
                    matched = True
                    break

            if matched:
                continue

            word_lower = token.value.lower()
            syn_symbol = GLOBAL_SYNONYMS.get_symbol_for(word_lower)
            if word_lower in self.WORD_OPS:
                merged.append(Token("op", self.WORD_OPS[word_lower], token.line, token.col))
            elif syn_symbol is not None:
                merged.append(Token("op", syn_symbol, token.line, token.col))
            elif word_lower == "true":
                merged.append(Token("name", "True", token.line, token.col))
            elif word_lower == "false":
                merged.append(Token("name", "False", token.line, token.col))
            elif word_lower in {"none", "nothing"}:
                merged.append(Token("name", "None", token.line, token.col))
            else:
                merged.append(Token("name", token.value, token.line, token.col))
            i += 1

        return merged

    def to_python_expression(self, text: str, line: int) -> str:
        cached = self._python_expr_cache.get(text)
        if cached is not None:
            self.stats.cache_hits += 1
            return cached

        self.stats.cache_misses += 1
        tokens = self.tokenize(text, line)
        py_expr = " ".join(token.value for token in tokens)
        self._python_expr_cache[text] = py_expr
        return py_expr


def normalize_assignment_sugar(line: str) -> str:
    """Intent-mode helper for x = y syntax."""
    assignment = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", line.strip())
    if assignment:
        return f"{assignment.group(1)} is like {assignment.group(2)}"
    return line
