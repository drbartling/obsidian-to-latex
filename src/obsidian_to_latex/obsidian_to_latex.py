import re
import shutil
import subprocess
from pathlib import Path

import click
import pydantic

from obsidian_to_latex import obsidian_path, process_markdown


@click.command
@click.argument(
    "filename",
    type=click.Path(path_type=Path, resolve_path=True),
)
@pydantic.validate_arguments
def main(filename: Path):  # pragma: no cover
    obsidian_path.VAULT_ROOT = get_vault_root(filename)

    with open(filename, "r", encoding="UTF-8") as f:
        text = f.read()
    latex = process_markdown.obsidian_to_tex(text)
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
        [
            "latexmk",
            "-pdf",
            "-g",
            '-latexoption="-shell-escape -file-line-error -halt-on-error"',
            temp_wrapper,
        ],
        check=False,
        capture_output=False,
        cwd=temp_wrapper.parent,
    )
    temp_pdf = temp_wrapper.with_suffix(".pdf")
    out_dir = filename.parent / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_pdf = (out_dir / filename.name).with_suffix(".pdf")
    shutil.copy(temp_pdf, out_pdf)


def get_vault_root(path: Path) -> Path:  # pragma: no cover
    if (path / ".obsidian").exists():
        return path
    if path.parent == path:
        raise FileNotFoundError("Unable to locate `.obsidian` folder")
    return get_vault_root(path.parent)


def get_title(text: str) -> str:  # pragma: no cover
    line = text.splitlines()[0]
    m = re.match(r"(^#*)\s*(.*)", line)
    if not m:
        return None
    title = m.group(2)
    return title
