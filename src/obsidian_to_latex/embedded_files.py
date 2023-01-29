import re
from pathlib import Path

import pydantic

from obsidian_to_latex import obsidian_path, obsidian_to_latex


@pydantic.validate_arguments
def is_embedded(line: str) -> bool:
    return line.startswith("![[") and line.endswith("]]")


@pydantic.validate_arguments
# pylint: disable=dangerous-default-value
def embed_markdown(line: str, depth={}) -> str:
    if not depth:
        depth["depth"] = 1
    m = re.match(r"!\[\[(.*)\]\]", line)
    file_name = m.group(1)
    assert not Path(file_name).suffix, line

    file_name = file_name + ".md"
    file = obsidian_path.find_file(file_name)

    with open(file, "r", encoding="UTF-8") as f:
        text = f.read()

    lines = text.splitlines()
    for i, l in enumerate(lines):
        if l.startswith("#"):
            lines[i] = "#" * depth["depth"] + l
    text = "\n".join(lines)
    depth["depth"] += 1
    out_text = obsidian_to_latex.obsidian_to_tex(text)
    depth["depth"] -= 1
    return out_text


@pydantic.validate_arguments
def embed_image(line: str) -> str:
    m = re.match(
        r"!\[\[([\s_a-zA-Z0-9.]*)(\|)?([0-9]+)?(x)?([0-9]+)?\]\]", line
    )
    if not m:
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
