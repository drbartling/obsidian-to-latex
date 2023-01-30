import re
from pathlib import Path

import pydantic

from obsidian_to_latex import obsidian_path

_DEPTH = 1
_CODE_BLOCK = False


def obsidian_to_tex(input_text: str) -> str:
    lines = input_text.splitlines()
    lines = [line_to_tex(l) for l in lines]
    text = "\n".join(lines)
    return text


def line_to_tex(line: str) -> str:
    if is_code_block_toggle(line):
        return toggle_code_block(line)
    if _CODE_BLOCK:
        return line
    if line.startswith("#"):
        return line_to_section(line)
    if is_embedded(line):
        return embed_file(line)
    line = create_links(line)
    line = create_references(line)
    line = line.replace("#", R"\#")
    line = line.replace("_", R"\_")
    return line


def line_to_section(line: str) -> str:
    assert line.startswith("#"), line
    section_lookup = {
        2: "section",
        3: "subsection",
        4: "subsubsection",
        5: "paragraph",
        6: "subparagraph",
    }
    m = re.match(r"(^#*)\s*(.*)", line)
    subsection_depth = len(m.group(1))
    if subsection_depth not in section_lookup:
        return ""
    section_text = section_lookup[subsection_depth]
    line = m.group(2)
    line = line.replace("#", R"\#")
    line = line.replace("_", R"\_")
    return f"\\{section_text}{{{line}}}"


@pydantic.validate_arguments
def is_embedded(line: str) -> bool:
    return line.startswith("![[") and line.endswith("]]")


@pydantic.validate_arguments
def embed_file(line: str) -> str:
    if is_markdown(line):
        return embed_markdown(line)
    if is_image(line):
        return embed_image(line)
    raise Exception(f"Unable to embed {line}")  # pragma: no cover


@pydantic.validate_arguments
def is_markdown(line: str) -> bool:
    m = re.match(r"!\[\[(.*)\]\]", line)
    file_name = m.group(1)
    return Path(file_name).suffix == ""


@pydantic.validate_arguments
def embed_markdown(line: str) -> str:
    global _DEPTH  # pylint: disable=global-statement
    m = re.match(r"!\[\[(.*)\]\]", line)
    file_name = m.group(1)
    assert is_markdown(line), line

    file_name = file_name + ".md"
    file = obsidian_path.find_file(file_name)

    with open(file, "r", encoding="UTF-8") as f:
        text = f.read()
    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("#"):
            lines[i] = "#" * _DEPTH + l
    text = "\n".join(lines)
    _DEPTH += 1
    result = obsidian_to_tex(text)
    _DEPTH -= 1
    return result


@pydantic.validate_arguments
def is_image(line: str) -> bool:
    m = re.match(r"!\[\[([\s_a-zA-Z0-9.]*)(\|)?([0-9x]+)?\]\]", line)
    if not m:
        return False
    file_name = m.group(1)
    return Path(file_name).suffix.lower() in [".png", ".bmp"]


@pydantic.validate_arguments
def embed_image(line: str) -> str:
    assert is_image(line), line
    m = re.match(
        r"!\[\[([\s_a-zA-Z0-9.]*)(\|)?([0-9]+)?(x)?([0-9]+)?\]\]", line
    )
    if not m:  # pragma: no cover
        raise Exception(line)
    file_name = m.group(1)
    width = m.group(3)
    height = m.group(5)
    return include_image(obsidian_path.find_file(file_name), width, height)


@pydantic.validate_arguments
def include_image(
    image_path: Path, width: int | None, height: int | None
) -> str:
    width_text = R"\columnwidth" if width is None else f"{int(width/2)}pt"
    height_text = (
        R"keepaspectratio" if height is None else f"height={int(height/2)}pt"
    )

    image_path = image_path.with_suffix("")
    image_path = obsidian_path.format_path(image_path)
    return (
        f"\\includegraphics[width={width_text},{height_text}]{{{image_path}}}"
    )


def is_code_block_toggle(line: str) -> bool:
    return line.startswith("```")


def toggle_code_block(line: str) -> str:
    global _CODE_BLOCK  # pylint: disable=global-statement
    if not _CODE_BLOCK:
        _CODE_BLOCK = True
        lang = line[3:]
        return R"\begin{minted}" f"{{{lang}}}"

    _CODE_BLOCK = False
    return R"\end{minted}"


@pydantic.validate_arguments
def create_links(line: str) -> str:
    "[[#^para-ref|link]]"
    return re.sub(
        r"\[\[#\^([a-zA-Z0-9-]+)(\|)?(.+)\]\]", r"\\hyperref[\1]{\3}", line
    )


@pydantic.validate_arguments
def create_references(line: str) -> str:
    return re.sub(r"\^([0-9a-zA-Z-]+)", r"\\label{\1}", line)
