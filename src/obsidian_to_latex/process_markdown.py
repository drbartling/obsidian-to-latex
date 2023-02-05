import logging
import re
from pathlib import Path
from typing import List, Optional, Tuple

import pydantic
from pydantic.dataclasses import dataclass

from obsidian_to_latex import obsidian_path

_DEPTH = 1
_CODE_BLOCK = False
_LIST_DEPTH: List["Indent"] = []
_FILE: List[Path] = []


@dataclass
class Indent:
    list_type: str
    depth: str


@pydantic.validate_arguments
def obsidian_to_tex(input_text: str) -> str:
    lines = input_text.splitlines()
    lines = [_line_to_tex(i, l) for i, l in enumerate(lines)]
    text = "\n".join(lines)
    text = text + cleanup()
    return text


@pydantic.validate_arguments
def _line_to_tex(lineno: int, line: str) -> str:
    try:
        return line_to_tex(line)
    except Exception:  # pragma: no cover
        logging.getLogger(__name__).error(
            "Failed to parse `%s:%s`", _FILE[-1], lineno
        )
        raise


@pydantic.validate_arguments
def line_to_tex(
    line: str,
) -> str:
    # pylint: disable=too-many-return-statements
    if is_end_of_list(line):
        lines = end_lists()
        lines.append(line_to_tex(line))
        line = "\n".join(lines)
        return line

    if is_code_block_toggle(line):
        return toggle_code_block(line)
    if _CODE_BLOCK:
        return line
    if is_embedded(line):
        return embed_file(line)
    if line.startswith("#"):
        return line_to_section(line)
    if is_numbered_list_item(line):
        return numbered_list_item(line)
    if is_bullet_list_item(line):
        return bullet_list_item(line)
    line = string_to_tex(line)
    return line


@pydantic.validate_arguments
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
    line = string_to_tex(line)
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
    _FILE.append(file)
    _DEPTH += 1
    try:
        result = obsidian_to_tex(text)
    finally:
        _DEPTH -= 1
        _FILE.pop()
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
        r"!\[\[([\s_a-zA-Z0-9.]*)(?:\|)?([0-9]+)?(?:x)?([0-9]+)?\]\]", line
    )
    if not m:  # pragma: no cover
        raise Exception(line)
    file_name, width, height = m.groups()
    return include_image(obsidian_path.find_file(file_name), width, height)


@pydantic.validate_arguments
def include_image(
    image_path: Path, width: Optional[int], height: Optional[int]
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


@pydantic.validate_arguments
def is_code_block_toggle(line: str) -> bool:
    return line.startswith("```")


@pydantic.validate_arguments
def toggle_code_block(line: str) -> str:
    global _CODE_BLOCK  # pylint: disable=global-statement
    if not _CODE_BLOCK:
        _CODE_BLOCK = True
        lang = line[3:]
        lines = [
            R"",
            R"\begin{minipage}{\columnwidth}",
            R"\begin{minted}[bgcolor=bg]" f"{{{lang}}}",
        ]
        return "\n".join(lines)

    _CODE_BLOCK = False
    lines = [
        R"\end{minted}",
        R"\end{minipage}",
    ]
    return "\n".join(lines)


@pydantic.validate_arguments
def sanitize_special_characters(line: str) -> str:
    return re.sub(r"([&$_#%{}])(?!.*`)", r"\\\1", line)


@pydantic.validate_arguments
def is_end_of_list(line: str) -> bool:
    return _LIST_DEPTH and not is_list(line)


@pydantic.validate_arguments
def is_list(line: str) -> bool:
    return is_numbered_list_item(line) or is_bullet_list_item(line)


@pydantic.validate_arguments
def is_numbered_list_item(line: str) -> bool:
    return re.match(r"\s*[0-9]+\.", line)


@pydantic.validate_arguments
def numbered_list_item(line: str) -> str:
    indent, number, text = re.match(r"(\s*)([0-9])+\.\s+(.*)", line).groups()
    sanitized_text = string_to_tex(text)
    list_line = R"\item " + sanitized_text
    if line_depth(indent) > total_depth():
        new_indent = indent.replace(total_indent(), "", 1)
        _LIST_DEPTH.append(Indent("legal", new_indent))
        start_num = int(number)
        start_text = "" if start_num == 1 else f"[start={start_num}]"
        lines = [R"\begin{legal}" + start_text, list_line]
        list_line = "\n".join(lines)
    if line_depth(indent) < total_depth():
        indent = _LIST_DEPTH.pop()
        lines = [f"\\end{{{indent.list_type}}}", list_line]
        list_line = "\n".join(lines)

    assert _LIST_DEPTH, _LIST_DEPTH
    return list_line


@pydantic.validate_arguments
def is_bullet_list_item(line: str) -> bool:
    return re.match(r"\s*-", line)


@pydantic.validate_arguments
def bullet_list_item(line: str) -> str:
    indent, text = re.match(r"(\s*)-\s+(.*)", line).groups()
    sanitized_text = string_to_tex(text)
    list_line = R"\item " + sanitized_text
    if line_depth(indent) > total_depth():
        new_indent = indent.replace(total_indent(), "", 1)
        _LIST_DEPTH.append(Indent("itemize", new_indent))
        lines = [R"\begin{itemize}", list_line]
        list_line = "\n".join(lines)
    if line_depth(indent) < total_depth():
        indent = _LIST_DEPTH.pop()
        lines = [f"\\end{{{indent.list_type}}}", list_line]
        list_line = "\n".join(lines)

    assert _LIST_DEPTH, _LIST_DEPTH
    return list_line


@pydantic.validate_arguments
def line_depth(indent: str) -> int:
    return len(indent)


@pydantic.validate_arguments
def total_depth() -> int:
    if not _LIST_DEPTH:
        return -1
    return sum(line_depth(i.depth) for i in _LIST_DEPTH)


@pydantic.validate_arguments
def total_indent() -> str:
    if not _LIST_DEPTH:
        return ""
    return "".join([i.depth for i in _LIST_DEPTH])


@pydantic.validate_arguments
def cleanup():
    assert not _CODE_BLOCK, _CODE_BLOCK
    lines = [""]

    lines.extend(end_lists())

    assert not _LIST_DEPTH, _LIST_DEPTH
    return "\n".join(lines)


@pydantic.validate_arguments
def end_lists():
    lines = []
    while _LIST_DEPTH:
        indent = _LIST_DEPTH.pop()
        lines.append(f"\\end{{{indent.list_type}}}")
    return lines


@pydantic.validate_arguments
def string_to_tex(unprocessed_text: str) -> str:
    logging.getLogger(__name__).debug("unprocessed_text %s", unprocessed_text)
    processed_text = ""

    while unprocessed_text:
        char = unprocessed_text[0]
        unprocessed_text = unprocessed_text[1:]
        if char == "`":
            pt, unprocessed_text = split_verbatim(unprocessed_text)
            processed_text += pt
        elif char == "[":
            pt, unprocessed_text = split_link(unprocessed_text)
            processed_text += pt
        elif char == "^":
            pt, unprocessed_text = split_reference(unprocessed_text)
            processed_text += pt
        else:
            processed_text += sanitize_special_characters(char)

    return processed_text


@pydantic.validate_arguments
def split_verbatim(text: str) -> Tuple[str, str]:
    processed_text = R"\verb`"
    verb_text, unprocessed_text = re.match(r"(.*?`)(.*)", text).groups()
    processed_text += verb_text
    return (processed_text, unprocessed_text)


@pydantic.validate_arguments
def split_link(text: str) -> Tuple[str, str]:
    return (
        split_markdown_link(text)
        or split_paragraph_link(text)
        or (R"\[", text)
    )


@pydantic.validate_arguments
def split_markdown_link(text: str) -> Tuple[str, str]:
    m = re.match(r"(.*?)\]\((.*?)\)(.*)", text)
    if not m:
        return None
    disp_text, link, unprocessed_text = m.groups()
    disp_text = sanitize_special_characters(disp_text)
    processed_text = f"\\href{{{link}}}{{{disp_text}}}"
    return (processed_text, unprocessed_text)


@pydantic.validate_arguments
def split_paragraph_link(text: str) -> Tuple[str, str]:
    m = re.match(r"\[#\^([a-zA-Z0-9-]+)\|?(.+)\]\](.*)", text)
    if not m:
        return None
    link, disp_text, unprocessed_text = m.groups()
    disp_text = sanitize_special_characters(disp_text)
    processed_text = f"\\hyperref[{link}]{{{disp_text}}}"
    return (processed_text, unprocessed_text)


@pydantic.validate_arguments
def split_reference(text: str) -> Tuple[str, str]:
    m = re.match(r"([a-zA-Z0-9-]+)$", text)
    if not m:
        return R"\textasciicircum{}", text
    ref_text = m.groups()[0]
    return f"\\label{{{ref_text}}}", ""
