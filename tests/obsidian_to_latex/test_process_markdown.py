# pylint: disable=protected-access
from pathlib import Path
from unittest import mock

import devtools
import pydantic
import pytest

from obsidian_to_latex import obsidian_path, process_markdown


@pytest.fixture(autouse=True)
def setup_teardown():
    process_markdown._DEPTH = 1
    process_markdown._CODE_BLOCK = False
    yield
    process_markdown._DEPTH = 1
    process_markdown._CODE_BLOCK = False


obsidian_to_tex_params = [
    (
        (
            "# User Guide\n"
            "This is a summary of the user guide.\n"
            "## Getting Started\n"
            "Start by installing.  Then run the program."
        ),
        (
            "\n"
            "This is a summary of the user guide.\n"
            R"\section{Getting Started}"
            "\n"
            "Start by installing.  Then run the program."
        ),
    ),
    (
        (
            "# User Guide\n"
            "Here's how to add a section header:\n"
            "```markdown\n"
            "## A Section Header\n"
            "```\n"
            "That looks like this:\n"
            "## A Section Header\n"
        ),
        (
            "\n"
            "Here's how to add a section header:\n\n"
            R"\begin{minipage}{\columnwidth}"
            "\n"
            R"\begin{minted}[bgcolor=bg]{markdown}"
            "\n"
            R"## A Section Header"
            "\n"
            R"\end{minted}"
            "\n"
            R"\end{minipage}"
            "\n"
            "That looks like this:\n"
            R"\section{A Section Header}"
        ),
    ),
    (
        ("1. Here's a list\n2. With a second item\n"),
        (
            R"\begin{legal}"
            "\n"
            R"\item Here's a list"
            "\n"
            R"\item With a second item"
            "\n"
            R"\end{legal}"
        ),
    ),
    (
        ("- Here's a list\n- With a second item\n"),
        (
            R"\begin{itemize}"
            "\n"
            R"\item Here's a list"
            "\n"
            R"\item With a second item"
            "\n"
            R"\end{itemize}"
        ),
    ),
    (
        (
            "We're about to have a list:\n"
            "- Here's a list\n"
            "- With a second item\n"
            "See list above.\n"
        ),
        (
            "We're about to have a list:\n"
            R"\begin{itemize}"
            "\n"
            R"\item Here's a list"
            "\n"
            R"\item With a second item"
            "\n"
            R"\end{itemize}"
            "\n"
            "See list above."
        ),
    ),
    (
        ("We're about to have a list:\n- Here's a list with_underscores\n"),
        (
            "We're about to have a list:\n"
            R"\begin{itemize}"
            "\n"
            R"\item Here's a list with\_underscores"
            "\n"
            R"\end{itemize}"
        ),
    ),
    (
        (
            "We're about to have a list:\n"
            "1. Here's a list with_underscores\n"
        ),
        (
            "We're about to have a list:\n"
            R"\begin{legal}"
            "\n"
            R"\item Here's a list with\_underscores"
            "\n"
            R"\end{legal}"
        ),
    ),
    (
        (
            "1. Install the provided license file anywhere on your system\n"
            "2. Set `DECATECH_LICENSE_FILE` to the location of your license file\n"
        ),
        (
            R"\begin{legal}"
            "\n"
            R"\item Install the provided license file anywhere on your system"
            "\n"
            R"\item Set `DECATECH\_LICENSE\_FILE` to the location of your license file"
            "\n"
            R"\end{legal}"
        ),
    ),
    (
        ("2. This list startswith 2\n3. And ends with 3\n"),
        (
            R"\begin{legal}[start=2]"
            "\n"
            R"\item This list startswith 2"
            "\n"
            R"\item And ends with 3"
            "\n"
            R"\end{legal}"
        ),
    ),
    (
        ("- This list has depth\n  - So deep\n"),
        (
            R"\begin{itemize}"
            "\n"
            R"\item This list has depth"
            "\n"
            R"\begin{itemize}"
            "\n"
            R"\item So deep"
            "\n"
            R"\end{itemize}"
            "\n"
            R"\end{itemize}"
        ),
    ),
    (
        ("- This list has depth\n  - So deep\n- And Shallow again"),
        (
            R"\begin{itemize}"
            "\n"
            R"\item This list has depth"
            "\n"
            R"\begin{itemize}"
            "\n"
            R"\item So deep"
            "\n"
            R"\end{itemize}"
            "\n"
            R"\item And Shallow again"
            "\n"
            R"\end{itemize}"
        ),
    ),
    (
        (
            "1. This numbered list has depth\n  1. So deep\n2. And Shallow again"
        ),
        (
            R"\begin{legal}"
            "\n"
            R"\item This numbered list has depth"
            "\n"
            R"\begin{legal}"
            "\n"
            R"\item So deep"
            "\n"
            R"\end{legal}"
            "\n"
            R"\item And Shallow again"
            "\n"
            R"\end{legal}"
        ),
    ),
]


@pytest.mark.parametrize("input_text, expected", obsidian_to_tex_params)
def test_obsidian_to_tex(input_text, expected):
    result = process_markdown.obsidian_to_tex(input_text)
    devtools.debug(result)
    devtools.debug(expected)
    assert result == expected, result


line_to_latex_params = [
    ("A Normal Line", "A Normal Line"),
    ("# A Title", R""),  # Title at top of markdown becomes document title
    ("## A section Header", R"\section{A section Header}"),
    (
        "### A sub section Header",
        R"\subsection{A sub section Header}",
    ),
    (
        "#### A sub sub section",
        R"\subsubsection{A sub sub section}",
    ),
    (
        "##### A 'paragraph'",
        R"\paragraph{A 'paragraph'}",
    ),
    (
        "###### A 'sub paragraph'",
        R"\subparagraph{A 'sub paragraph'}",
    ),
    (
        "## This section is #1",
        R"\section{This section is \#1}",
    ),
    (
        "Normal text is almost #1, it's #2",
        R"Normal text is almost \#1, it's \#2",
    ),
    (
        "Normal text is almost #1, it's #2",
        R"Normal text is almost \#1, it's \#2",
    ),
]


@pytest.mark.parametrize("input_text, expected", line_to_latex_params)
def test_line_to_tex(input_text, expected):
    result = process_markdown.line_to_tex(input_text)
    assert result == expected


is_embedded_params = [
    ("Hello", False),
    ("![[Hello]]", True),
    ("![[Hello]", False),
]


@pytest.mark.parametrize("markdown_line, expected", is_embedded_params)
def test_is_embedded(markdown_line, expected):
    result = process_markdown.is_embedded(markdown_line)
    assert result == expected


is_image_params = [
    ("", False),
    ("![[Hello]]", False),
    ("![[Hello.png]]", True),
    ("![[Hello.png|123]]", True),
    ("![[Hello.png|123x234]]", True),
    ("![[Hello.png|123X234]]", False),
]


@pytest.mark.parametrize("input_text, expected", is_image_params)
def test_is_image(input_text, expected):
    result = process_markdown.is_image(input_text)
    assert result == expected


embed_markdown_params = [
    (
        "![[Hello]]",
        ["# Hello\nlorem ipsum\n"],
        "\\section{Hello}\nlorem ipsum",
    ),
    (
        "![[Hello]]",
        [
            "# Hello\nlorem ipsum\n![[World]]\n",
            "# World\ndolor sit\n",
        ],
        "\\section{Hello}\nlorem ipsum\n\\subsection{World}\ndolor sit",
    ),
    (
        "![[Hello]]",
        [
            "# Hello\nlorem ipsum\n![[World.bmp]]\n",
        ],
        "\\section{Hello}\nlorem ipsum\n"
        R"\includegraphics[width=\columnwidth,keepaspectratio]"
        f"{{{obsidian_path.format_path(Path('World').absolute())}}}",
    ),
]


@pytest.mark.parametrize(
    "input_text, open_reads, expected", embed_markdown_params
)
def test_embed_markdown(input_text, open_reads, expected):
    with mock.patch("obsidian_to_latex.obsidian_path.find_file") as mock_find:
        mock_find.return_value = Path("World.md").absolute()
        with mock.patch(
            "builtins.open", get_mock_open(open_reads)
        ) as _open_mock:
            result = process_markdown.embed_markdown(input_text)

    assert result == expected


@pydantic.validate_arguments
def get_mock_open(file_contents: list[str]):
    reads = 0

    def open_mock(*_args, **_kwargs):
        nonlocal reads
        content = file_contents[reads]
        reads += 1
        return mock.mock_open(read_data=content).return_value

    return mock.MagicMock(side_effect=open_mock)


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
        process_markdown.VAULT_ROOT = Path.cwd()
        mock_find.return_value = found_path
        result = process_markdown.embed_image(input_text)
    assert result == expected


create_links_params = [
    ("", ""),
    (
        R"Text with a [[#^para-ref|link]]",
        R"Text with a \hyperref[para-ref]{link}",
    ),
]


@pytest.mark.parametrize("input_text, expected", create_links_params)
def test_create_links(input_text, expected):
    result = process_markdown.create_links(input_text)
    assert result == expected


create_references_params = [
    ("", ""),
    ("plain text", "plain text"),
    ("plain text ^ref-abc123", "plain text \\label{ref-abc123}"),
    ("^project-example", "\\label{project-example}"),
]


@pytest.mark.parametrize("input_text, expected", create_references_params)
def test_create_references(input_text, expected):
    result = process_markdown.create_references(input_text)
    assert result == expected
