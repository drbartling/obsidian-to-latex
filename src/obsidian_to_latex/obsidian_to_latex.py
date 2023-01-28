import os
import re
import shutil
import subprocess
from pathlib import Path

import click
import pydantic

VAULT_ROOT = None


@click.command
@click.argument(
    "filename",
    type=click.Path(path_type=Path, resolve_path=True),
)
@pydantic.validate_arguments
def main(filename: Path):  # pragma: no cover
    global VAULT_ROOT
    VAULT_ROOT = get_vault_root(filename)
    print("VAULT_ROOT", VAULT_ROOT)

    with open(filename, "r", encoding="UTF-8") as f:
        text = f.read()
    latex = obsidian_to_tex(text)
    title = get_title(text)
    temp_dir = filename.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "body.tex"

    with open(temp_file, "w", encoding="UTF-8") as f:
        f.write(latex)

    latex_wrapper = Path(__file__).parent / "document.tex"
    temp_wrapper = temp_dir / latex_wrapper.name

    with open(latex_wrapper, "r", encoding="UTF-8") as f:
        wrapper_text = f.read()
    wrapper_text = wrapper_text.replace("TheTitleOfTheDocument", title)

    with open(temp_wrapper, "w", encoding="UTF-8") as f:
        f.write(wrapper_text)
    subprocess.run(
        ["pdflatex", temp_wrapper, "-shell-escape", "-draftmode"],
        check=False,
        capture_output=False,
        cwd=temp_wrapper.parent,
    )
    subprocess.run(
        ["pdflatex", temp_wrapper, "-shell-escape", "-draftmode"],
        check=False,
        capture_output=False,
        cwd=temp_wrapper.parent,
    )
    subprocess.run(
        ["pdflatex", temp_wrapper, "-shell-escape"],
        check=False,
        capture_output=False,
        cwd=temp_wrapper.parent,
    )
    temp_pdf = temp_wrapper.with_suffix(".pdf")
    out_dir = filename.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = (out_dir / filename.name).with_suffix(".pdf")
    shutil.copy(temp_pdf, out_pdf)


def get_vault_root(path: Path) -> Path:
    if (path / ".obsidian").exists():
        return path
    return get_vault_root(path.parent)


def obsidian_to_tex(input_text: str) -> str:
    lines = input_text.splitlines()
    lines = [line_to_tex(l) for l in lines]
    text = "\n".join(lines)
    text += "\n"
    return text


def line_to_tex(line: str) -> str:
    if line.startswith("#"):
        return line_to_section(line)
    line = line.replace("#", R"\#")
    if line.startswith("![["):
        return include_doc(line)
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
    return f"\\{section_text}{{{line}}}"


def include_doc(line: str, depth=1) -> str:
    m = re.match(r"!\[\[(.*)\]\]", line)
    if not m:
        raise Exception(line)
    file_name = m.group(1) + ".md"

    for root, dirs, files in os.walk(VAULT_ROOT):
        if file_name in files:
            file = Path(os.path.join(root, file_name))
            break

    with open(file, "r", encoding="UTF-8") as f:
        text = f.read()

    lines = text.splitlines()
    for i in range(len(lines)):
        if lines[i].startswith("#"):
            lines[i] = "#" + lines[i]
    text = "\n".join(lines)
    return obsidian_to_tex(text)


def get_title(text: str) -> str:
    line = text.splitlines()[0]
    m = re.match(r"(^#*)\s*(.*)", line)
    if not m:
        return None
    title = m.group(2)
    return title
