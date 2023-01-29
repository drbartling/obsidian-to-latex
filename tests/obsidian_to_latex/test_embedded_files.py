from pathlib import Path
from unittest import mock

import pytest

from obsidian_to_latex import embedded_files, obsidian_path

is_embedded_params = [
    ("Hello", False),
    ("![[Hello]]", True),
    ("![[Hello]", False),
]


@pytest.mark.parametrize("markdown_line, expected", is_embedded_params)
def test_is_embedded(markdown_line, expected):
    result = embedded_files.is_embedded(markdown_line)
    assert expected == result


embed_markdown_params = [
    (
        "![[Hello]]",
        ["# Hello\nlorem ipsum\n"],
        "\\section{Hello}\nlorem ipsum\n",
    ),
]


@pytest.mark.parametrize("line, expected", embed_markdown_params)
def test_embed_markdown(line, expected):
    with mock.patch("obsidian_to_latex.obsidian_path.find_file") as mock_find:
        mock_find.return_value = Path("hello.md").absolute()
        with mock.patch(
            "obsidian_to_latex.open",
            mock.mock_open(),
        ) as m:
            m.return_value.side_effect = ["# Hello\nlorem ipsum\n"]
            result = embedded_files.embed_markdown(line)
    assert result == expected


embed_image_params = [
    (
        "![[foo.png]]",
        Path("images/foo.png").absolute(),
        "\\includegraphics[width=\\columnwidth,keepaspectratio]"
        f"{{{obsidian_path.format_path(Path('images/foo').absolute())}}}",
    ),
    (
        "![[bar.bmp]]",
        Path("resources/bar.bmp").absolute(),
        "\\includegraphics[width=\\columnwidth,keepaspectratio]"
        f"{{{obsidian_path.format_path(Path('resources/bar').absolute())}}}",
    ),
    (
        "![[bar.bmp|500]]",
        Path("resources/bar.bmp").absolute(),
        "\\includegraphics[width=250pt,keepaspectratio]"
        f"{{{obsidian_path.format_path(Path('resources/bar').absolute())}}}",
    ),
    (
        "![[bar.bmp|500x100]]",
        Path("resources/bar.bmp").absolute(),
        "\\includegraphics[width=250pt,height=50pt]"
        f"{{{obsidian_path.format_path(Path('resources/bar').absolute())}}}",
    ),
]


@pytest.mark.parametrize(
    "input_text, found_path, expected", embed_image_params
)
def test_embed_image(input_text, found_path, expected):
    with mock.patch("obsidian_to_latex.obsidian_path.find_file") as mock_find:
        embedded_files.VAULT_ROOT = Path.cwd()
        mock_find.return_value = found_path
        result = embedded_files.embed_image(input_text)
    assert result == expected
