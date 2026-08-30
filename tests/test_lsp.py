from __future__ import annotations

from tpp.lsp.handlers import LspHandler
from tpp.lsp.protocol import Position


def test_lsp_diagnostics() -> None:
    handler = LspHandler()
    valid_source = (
        "let x be 10\n"
        "let y be x plus 5\n"
    )
    diags = handler.update_document("file:///test.tpp", valid_source)
    assert len(diags) == 0

    invalid_source = (
        "let x be\n"
    )
    diags_err = handler.update_document("file:///invalid.tpp", invalid_source)
    assert len(diags_err) > 0
    assert "expected a value after 'let'" in diags_err[0].message


def test_lsp_hover_and_completions() -> None:
    handler = LspHandler()
    source = (
        "define greet with name as a text:\n"
        "    give back \"Hello, {name}\"\n"
        "let message be call greet with \"World\"\n"
    )
    handler.update_document("file:///hover.tpp", source)

    # Hover on 'greet'
    hover = handler.get_hover("file:///hover.tpp", Position(line=0, character=8))
    assert hover is not None
    assert "define greet with name" in str(hover.contents)

    # Hover on stdlib 'math'
    hover_math = handler.get_hover("file:///hover.tpp", Position(line=0, character=0))

    # Completions
    completions = handler.get_completions("file:///hover.tpp", Position(line=2, character=0))
    labels = {c.label for c in completions}
    assert "let" in labels
    assert "greet" in labels
    assert "plus" in labels


def test_lsp_definition_and_formatting() -> None:
    handler = LspHandler()
    source = (
        "define compute with x:\n"
        "    give back x * 2\n"
        "let val be call compute with 5\n"
    )
    handler.update_document("file:///def.tpp", source)

    loc = handler.get_definition("file:///def.tpp", Position(line=2, character=17))
    assert loc is not None
    assert loc.range.start.line == 0

    # Formatting
    unformatted = "let   a   be   10\n"
    handler.update_document("file:///fmt.tpp", unformatted)
    edits = handler.get_formatting("file:///fmt.tpp")
    assert len(edits) > 0
    assert edits[0].newText == "let a be 10\n"
