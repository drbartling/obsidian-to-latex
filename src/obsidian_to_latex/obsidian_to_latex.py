import re
import shutil
import subprocess
from pathlib import Path

import click
import pydantic


@click.command
@click.argument(
    "filename",
    type=click.Path(path_type=Path, resolve_path=True),
)
@pydantic.validate_arguments
def main(filename: Path):  # pragma: no cover
    with open(filename, "r", encoding="UTF-8") as f:
        text = f.read()
    latex = obsidian_to_tex(text)
    temp_dir = filename.parent / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_file = temp_dir / "body.tex"

    with open(temp_file, "w", encoding="UTF-8") as f:
        f.write(latex)

    latex_wrapper = Path(__file__).parent / "document.tex"
    temp_wrapper = temp_dir / latex_wrapper.name

    with open(latex_wrapper, "r", encoding="UTF-8") as f:
        wrapper_text = f.read()
    wrapper_text = wrapper_text.replace("TheTitleOfTheDocument", "Super User Guide")

    with open(temp_wrapper, "w", encoding="UTF-8") as f:
        f.write(wrapper_text)
    subprocess.run(
        ["pdflatex", temp_wrapper, "-shell-escape"],
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
    subprocess.run(
        ["pdflatex", temp_wrapper, "-shell-escape"],
        check=False,
        capture_output=False,
        cwd=temp_wrapper.parent,
    )
    temp_pdf = temp_wrapper.with_suffix(".pdf")
    out_dir = filename.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    print(out_dir)
    out_pdf = (out_dir / filename.name).with_suffix(".pdf")
    print(out_pdf)
    shutil.copy(temp_pdf, out_pdf)


def obsidian_to_tex(input_text: str) -> str:
    lines = input_text.splitlines()
    lines = [line_to_tex(l) for l in lines]
    text = "\n".join(lines)
    text += "\n"
    return text


def line_to_tex(line: str) -> str:
    if line.startswith("#"):
        section_lookup = {
            1: "section",
            2: "subsection",
            3: "subsubsection",
            4: "paragraph",
            5: "subparagraph",
        }
        m = re.match(r"(^#*)\s*(.*)", line)
        subsection_depth = len(m.group(1))
        section_text = section_lookup[subsection_depth]
        line = m.group(2)
        line = line.replace("#", R"\#")
        return f"\\{section_text}{{{line}}}"
    line = line.replace("#", R"\#")
    return line
