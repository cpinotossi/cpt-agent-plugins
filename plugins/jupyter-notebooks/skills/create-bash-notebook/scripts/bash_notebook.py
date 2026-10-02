#!/usr/bin/env python3
"""Create, extend, check, and run Jupyter notebooks that use the Bash kernel.

Commands:
  create    create a new notebook with Bash kernel metadata
  add-cell  append or insert a cell (code cells always get languageId shellscript)
  check     verify metadata, cell IDs, and language IDs; repair with --fix
  kernel    verify that the "bash" kernelspec belongs to this Python environment
  run       execute the notebook in a fresh Bash kernel

create, add-cell, and check only need the standard library. kernel and run need
jupyter_client and nbclient from the environment that hosts the Bash kernel.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from pathlib import Path

KERNEL_NAME = "bash"
CELL_LANGUAGE = "shellscript"
KERNELSPEC = {"display_name": "Bash", "language": "bash", "name": KERNEL_NAME}
LANGUAGE_INFO = {
    "codemirror_mode": "shell",
    "file_extension": ".sh",
    "mimetype": "text/x-sh",
    "name": "bash",
}


def new_id() -> str:
    return uuid.uuid4().hex[:8]


def to_source(text: str) -> list[str]:
    return text.splitlines(keepends=True)


def code_cell(text: str) -> dict:
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": new_id(),
        "metadata": {"vscode": {"languageId": CELL_LANGUAGE}},
        "outputs": [],
        "source": to_source(text),
    }


def markdown_cell(text: str) -> dict:
    return {
        "cell_type": "markdown",
        "id": new_id(),
        "metadata": {},
        "source": to_source(text),
    }


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save(path: Path, notebook: dict) -> None:
    # Same layout as Jupyter and VS Code: indent=1, UTF-8, trailing newline.
    text = json.dumps(notebook, indent=1, ensure_ascii=False) + "\n"
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    os.replace(tmp, path)


def read_text_arg(source: str | None, source_file: str | None) -> str:
    if source is not None:
        return source
    if source_file == "-":
        return sys.stdin.read()
    return Path(source_file).read_text(encoding="utf-8")


def find_problems(notebook: dict) -> list[str]:
    problems = []
    if notebook.get("nbformat") != 4 or notebook.get("nbformat_minor", 0) < 5:
        problems.append("nbformat must be 4 and nbformat_minor >= 5 (cell IDs).")
    metadata = notebook.get("metadata", {})
    if metadata.get("kernelspec") != KERNELSPEC:
        problems.append(f"metadata.kernelspec is {metadata.get('kernelspec')!r}, expected {KERNELSPEC!r}.")
    if metadata.get("language_info", {}).get("name") != LANGUAGE_INFO["name"]:
        problems.append("metadata.language_info.name must be 'bash'.")
    seen = set()
    for number, cell in enumerate(notebook.get("cells", []), start=1):
        cell_id = cell.get("id")
        if not cell_id:
            problems.append(f"Cell {number}: id is missing.")
        elif cell_id in seen:
            problems.append(f"Cell {number}: id {cell_id!r} is duplicated.")
        seen.add(cell_id)
        if cell.get("cell_type") == "code":
            language = cell.get("metadata", {}).get("vscode", {}).get("languageId")
            if language != CELL_LANGUAGE:
                problems.append(
                    f"Cell {number}: metadata.vscode.languageId is {language!r}, expected 'shellscript'."
                )
    return problems


def fix(notebook: dict) -> None:
    notebook["nbformat"] = 4
    notebook["nbformat_minor"] = max(5, notebook.get("nbformat_minor", 0))
    metadata = notebook.setdefault("metadata", {})
    metadata["kernelspec"] = dict(KERNELSPEC)
    metadata["language_info"] = {**metadata.get("language_info", {}), **LANGUAGE_INFO}
    seen = set()
    for cell in notebook.setdefault("cells", []):
        if not cell.get("id") or cell["id"] in seen:
            cell["id"] = new_id()
        seen.add(cell["id"])
        if cell.get("cell_type") == "code":
            cell.setdefault("metadata", {}).setdefault("vscode", {})["languageId"] = CELL_LANGUAGE


def validate_schema(notebook: dict) -> list[str]:
    try:
        import nbformat
    except ImportError:
        print("Note: nbformat is not installed, schema validation skipped.", file=sys.stderr)
        return []
    try:
        nbformat.validate(nbformat.from_dict(notebook))
    except nbformat.ValidationError as error:
        return [f"nbformat: {error.message}"]
    return []


def report(path: Path, notebook: dict) -> int:
    problems = find_problems(notebook) + validate_schema(notebook)
    if problems:
        print(f"ERROR {path}:")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    code = sum(1 for c in notebook.get("cells", []) if c.get("cell_type") == "code")
    print(f"OK {path}: kernel bash, {code} code cell(s) with languageId shellscript")
    return 0


def cmd_create(args: argparse.Namespace) -> int:
    path = Path(args.notebook)
    if path.suffix != ".ipynb":
        raise SystemExit("Error: file name must end with .ipynb.")
    if path.exists() and not args.force:
        raise SystemExit(f"Error: {path} exists. Use --force to overwrite.")
    cells = []
    if args.title:
        cells.append(markdown_cell(f"# {args.title}\n"))
    cells.append(code_cell(args.first_cell))
    notebook = {
        "cells": cells,
        "metadata": {"kernelspec": dict(KERNELSPEC), "language_info": dict(LANGUAGE_INFO)},
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    save(path, notebook)
    print(f"Created: {path}")
    return report(path, notebook)


def cmd_add_cell(args: argparse.Namespace) -> int:
    path = Path(args.notebook)
    notebook = load(path)
    text = read_text_arg(args.source, args.source_file)
    cell = markdown_cell(text) if args.markdown else code_cell(text)
    cells = notebook.setdefault("cells", [])
    if args.after_id:
        index = next((i for i, c in enumerate(cells) if c.get("id") == args.after_id), None)
        if index is None:
            raise SystemExit(f"Error: no cell with id {args.after_id!r}.")
        cells.insert(index + 1, cell)
    elif args.index is not None:
        cells.insert(args.index, cell)
    else:
        cells.append(cell)
    save(path, notebook)
    print(f"Inserted cell {cell['id']} ({cell['cell_type']}) into {path}")
    return report(path, notebook)


def cmd_check(args: argparse.Namespace) -> int:
    status = 0
    for name in args.notebooks:
        path = Path(name)
        notebook = load(path)
        if args.fix and find_problems(notebook):
            fix(notebook)
            save(path, notebook)
            print(f"Repaired: {path}")
        status |= report(path, notebook)
    return status


def is_inside(child: str, parent: str) -> bool:
    child_real = os.path.normcase(os.path.realpath(child))
    parent_real = os.path.normcase(os.path.realpath(parent))
    return os.path.commonpath([child_real, parent_real]) == parent_real


def cmd_kernel(_: argparse.Namespace) -> int:
    try:
        from jupyter_client.kernelspec import KernelSpecManager, NoSuchKernel
    except ImportError:
        print("ERROR: jupyter_client is missing in this Python. Run the setup script.")
        return 1
    try:
        spec = KernelSpecManager().get_kernel_spec(KERNEL_NAME)
    except NoSuchKernel:
        print("ERROR: kernelspec 'bash' not found. Run the setup script.")
        return 1
    argv = spec.argv or [""]
    # A venv python is often a symlink to the system python, so resolve only its directory.
    executable_dir = os.path.dirname(os.path.abspath(argv[0])) if argv[0] else ""
    problems = []
    if not is_inside(spec.resource_dir, sys.prefix):
        problems.append(f"Kernelspec lives outside this environment: {spec.resource_dir}")
    if not executable_dir or not is_inside(executable_dir, sys.prefix):
        problems.append(f"Kernel starts a foreign Python: {argv[0] or '<empty>'}")
    if argv[1:3] != ["-m", "bash_kernel"]:
        problems.append(f"Kernelspec does not start bash_kernel: {argv}")
    print(f"Environment: {sys.prefix}")
    print(f"Kernelspec:  {spec.resource_dir}")
    print(f"Command:     {' '.join(argv)}")
    if problems:
        for problem in problems:
            print(f"ERROR: {problem}")
        print(
            "Fix: run 'python -m bash_kernel.install --sys-prefix' inside the environment "
            "and remove foreign specs with 'jupyter kernelspec remove bash'."
        )
        return 1
    print("OK: kernel 'bash' belongs to this environment.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    try:
        import nbformat
        from nbclient import NotebookClient
        from nbclient.exceptions import CellExecutionError
    except ImportError:
        print("ERROR: nbclient is missing in this Python. Run the setup script.")
        return 1
    path = Path(args.notebook).resolve()
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        kernel_name=KERNEL_NAME,
        timeout=args.timeout,
        allow_errors=False,
        resources={"metadata": {"path": str(path.parent)}},
    )
    try:
        client.execute()
    except CellExecutionError as error:
        failed = next(
            (c for c in notebook.cells if any(o.get("output_type") == "error" for o in c.get("outputs", []))),
            None,
        )
        where = f"cell {failed.get('id')}:\n{failed.source}" if failed else "unknown cell"
        detail = f"{error.ename}: {error.evalue}" if error.ename else f"exit code {error.evalue}"
        print(f"ERROR in {where.rstrip()}\n-> {detail}")
        return 1
    # bash_kernel silently restarts the shell after 'exit' or a 'set -e' failure; all state is lost.
    restarted = [
        c.get("id")
        for c in notebook.cells
        if any("Restarting Bash" in str(o.get("text", "")) for o in c.get("outputs", []))
    ]
    if restarted:
        print(
            f"ERROR: Bash restarted in cell(s) {', '.join(restarted)} "
            "(top-level exit, set -e, or set -u). Shell state was lost."
        )
        return 1
    if args.inplace:
        nbformat.write(notebook, path)
        print(f"Saved outputs to {path}")
    print(f"OK: {path.name} ran completely in kernel 'bash'.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    create = sub.add_parser("create", help="create a new Bash notebook")
    create.add_argument("notebook")
    create.add_argument("--title", help="H1 heading of the first markdown cell")
    create.add_argument("--first-cell", default='echo "Bash $BASH_VERSION"\n', help="content of the first code cell")
    create.add_argument("--force", action="store_true", help="overwrite an existing file")
    create.set_defaults(func=cmd_create)

    add = sub.add_parser("add-cell", help="insert a cell")
    add.add_argument("notebook")
    src = add.add_mutually_exclusive_group(required=True)
    src.add_argument("--source", help="cell content as text")
    src.add_argument("--source-file", help="read cell content from a file, '-' reads stdin")
    add.add_argument("--markdown", action="store_true", help="markdown cell instead of code cell")
    pos = add.add_mutually_exclusive_group()
    pos.add_argument("--after-id", help="insert after the cell with this id")
    pos.add_argument("--index", type=int, help="insert at this position (0-based)")
    add.set_defaults(func=cmd_add_cell)

    check = sub.add_parser("check", help="check notebooks")
    check.add_argument("notebooks", nargs="+")
    check.add_argument("--fix", action="store_true", help="repair findings")
    check.set_defaults(func=cmd_check)

    kernel = sub.add_parser("kernel", help="verify the kernel belongs to this environment")
    kernel.set_defaults(func=cmd_kernel)

    run = sub.add_parser("run", help="execute the notebook in the Bash kernel")
    run.add_argument("notebook")
    run.add_argument("--timeout", type=int, default=600, help="seconds per cell")
    run.add_argument("--inplace", action="store_true", help="write outputs back to the notebook")
    run.set_defaults(func=cmd_run)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
