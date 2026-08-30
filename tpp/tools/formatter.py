from __future__ import annotations

import re
from pathlib import Path


KEYWORD_CANONICAL = {
    "let": "let",
    "change": "change",
    "define": "define",
    "give back": "give back",
    "say": "say",
    "ask": "ask",
    "use": "use",
    "export": "export",
    "from": "from",
    "try": "try",
    "handle": "handle",
    "finally": "finally",
    "raise": "raise",
    "match": "match",
    "when": "when",
    "otherwise": "otherwise",
    "if": "if",
    "repeat": "repeat",
    "count": "count",
    "while": "while",
    "for each": "for each",
    "test": "test",
    "create class": "create class",
}


def format_tpp_source(source: str) -> str:
    lines = source.splitlines()
    if not lines:
        return ""

    formatted_lines: list[str] = []
    consecutive_empty = 0

    for raw_line in lines:
        stripped = raw_line.strip()
        if not stripped:
            consecutive_empty += 1
            if consecutive_empty <= 2:
                formatted_lines.append("")
            continue

        consecutive_empty = 0

        # Calculate indentation depth (assuming 4 spaces per level or standard tabs/spaces)
        leading_spaces = len(raw_line) - len(raw_line.lstrip(" "))
        # Round to nearest multiple of 4 spaces
        indent_level = max(0, round(leading_spaces / 4.0)) if leading_spaces > 0 else 0
        indent_str = "    " * indent_level

        # Canonicalize leading keyword phrase
        line_content = stripped
        if not line_content.startswith("#"):
            if '"' not in line_content and "'" not in line_content:
                line_content = re.sub(r"[ \t]+", " ", line_content)

            # Check keywords
            for kw, canonical in sorted(KEYWORD_CANONICAL.items(), key=lambda k: len(k[0]), reverse=True):
                pattern = rf"^(?i:{re.escape(kw)})(\s+.*|$)"
                match = re.match(pattern, line_content)
                if match:
                    rest = match.group(1)
                    line_content = canonical + rest
                    break

            # Normalize colon at end of block header
            if line_content.endswith(" :"):
                line_content = line_content[:-2] + ":"

        formatted_lines.append(f"{indent_str}{line_content}")

    # Remove trailing empty lines and ensure single newline at EOF
    while formatted_lines and not formatted_lines[-1]:
        formatted_lines.pop()

    return "\n".join(formatted_lines) + "\n"


def format_file(file_path: str | Path, *, check_only: bool = False) -> tuple[bool, str]:
    path = Path(file_path)
    original = path.read_text(encoding="utf-8")
    formatted = format_tpp_source(original)
    is_modified = formatted != original

    if not check_only and is_modified:
        path.write_text(formatted, encoding="utf-8")

    return is_modified, formatted
