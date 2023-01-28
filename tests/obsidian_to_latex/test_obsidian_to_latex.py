import pytest

from obsidian_to_latex import obsidian_to_latex


def test_sections():
    text_input = (
        "# User Guide\n"
        "This is a summary of the user guide.\n"
        "## Getting Started\n"
        "Start by installing.  Then run the program."
    )
    expected = (
        R"\section{User Guide}"
        "\n"
        "This is a summary of the user guide.\n"
        R"\subsection{Getting Started}"
        "\n"
        "Start by installing.  Then run the program.\n"
    )
    result = obsidian_to_latex.obsidian_to_tex(text_input)
    assert result == expected


line_to_latex_params = [
    ("A Normal Line", "A Normal Line"),
    ("# A Section Header", R"\section{A Section Header}"),
    ("## A sub section Header", R"\subsection{A sub section Header}"),
    (
        "### A sub sub section Header",
        R"\subsubsection{A sub sub section Header}",
    ),
    (
        "#### A 'paragraph'",
        R"\paragraph{A 'paragraph'}",
    ),
    (
        "##### A 'subparagraph'",
        R"\subparagraph{A 'subparagraph'}",
    ),
    (
        "# This section is #1",
        R"\section{This section is \#1}",
    ),
    (
        "Normal text is almost #1, it's #2",
        R"Normal text is almost \#1, it's \#2",
    ),
]


@pytest.mark.parametrize("input_text, expected", line_to_latex_params)
def test_line_to_tex(input_text, expected):
    result = obsidian_to_latex.line_to_tex(input_text)
    assert result == expected
