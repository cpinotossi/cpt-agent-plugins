---
name: create-bash-notebook
description: "Create Jupyter notebooks that run on a Bash kernel from a Python environment and add code cells as shellscript, on Linux, macOS, and Windows (WSL). WHEN: \"create bash notebook\", \"notebook with bash kernel\", \"add shell cell to notebook\", \"cell shows bash instead of shellscript\", \"bash kernel missing\", \"set up bash kernel\" - Brought to you by cpinotossi/cpt-agent-plugins"
license: MIT
metadata:
  author: cpinotossi
  version: "1.0.0"
---

# Create Bash Notebooks

This skill creates an `.ipynb` file that runs in VS Code on the Bash kernel of a Python
environment, and keeps every new code cell on the language ID `shellscript`. It is
project-agnostic. All paths below are relative to this skill's directory, written as
`<skill>`.

## What Has to Line Up

| Layer | Location | Expected value | Effect |
|---|---|---|---|
| Python environment | e.g. `.venv/` | contains `bash_kernel` | provides the kernel process |
| Kernelspec | `<env>/share/jupyter/kernels/bash/kernel.json` | `argv[0]` = the environment's Python | decides *what* executes the cells |
| Notebook metadata | `metadata.kernelspec.name` | `bash` | decides *which* kernel is requested |
| Cell metadata | `cells[].metadata.vscode.languageId` | `shellscript` | cell language in VS Code |

`language_info.name` stays `bash` because that is the kernel language. `shellscript` is
the VS Code language ID of the cell. Without it, VS Code shows the cell as `bash`.
Neither `nbformat.validate` nor VS Code reports this as an error.

## Rules for the Agent

1. Never write an `.ipynb` file by hand as JSON or with generic file tools such as
   `create_file`. Empty `source` fields and a foreign `kernelspec` are the typical
   results. Always use `<skill>/scripts/bash_notebook.py create`.
2. Insert code cells with `<skill>/scripts/bash_notebook.py add-cell`. If a VS Code
   notebook tool is used instead, set the language to `shellscript`, not `bash` or `sh`.
3. After every change, run `<skill>/scripts/bash_notebook.py check <notebook>`. On
   findings, run `check --fix` and check again.
4. Before handing over, run `<skill>/scripts/bash_notebook.py run <notebook>` with the
   environment's Python. A cell that never ran is untested.
5. Always register the kernel with `--sys-prefix`, never with `--user`. Only then does it
   belong to the environment and start that environment's Python.

## Prerequisites

| Platform | Requires |
|---|---|
| Linux | Python 3.9+ with `venv` (Debian/Ubuntu: `sudo apt install python3-venv`), Bash |
| macOS | Python 3.9+, Bash |
| Windows | WSL 2 with a Linux distribution that has Python 3.9+ |
| VS Code | **Jupyter** and **Python** extensions; on Windows also **WSL** |

> [!IMPORTANT]
> `bash_kernel` uses `pexpect.spawn` and does **not run natively on Windows**, not even
> with Git Bash. On Windows the environment lives in WSL, and VS Code works on the same
> folder through **WSL: Reopen Folder in WSL**.

## Quick Start

### Linux and macOS

```bash
# 1. Create the environment and register the kernel (in the project folder)
bash <skill>/scripts/setup-bash-kernel.sh --venv .venv

# 2. Create the notebook
.venv/bin/python <skill>/scripts/bash_notebook.py create notebooks/demo.ipynb --title "Demo"

# 3. Add a code cell (content via stdin avoids quoting problems)
cat <<'CELL' | .venv/bin/python <skill>/scripts/bash_notebook.py add-cell notebooks/demo.ipynb --source-file -
echo "Working directory: $PWD"
CELL

# 4. Check, then execute in a real Bash kernel
.venv/bin/python <skill>/scripts/bash_notebook.py check notebooks/demo.ipynb
.venv/bin/python <skill>/scripts/bash_notebook.py run notebooks/demo.ipynb
```

### Windows (PowerShell)

```powershell
# 1. Create the environment in WSL and register the kernel (in the project folder)
& <skill>\scripts\setup-bash-kernel.ps1 -Venv .venv

# 2. to 4. run inside the WSL environment
$skill = wsl wslpath -a '<skill>'
wsl --cd "$PWD" -- .venv/bin/python "$skill/scripts/bash_notebook.py" create notebooks/demo.ipynb --title "Demo"
wsl --cd "$PWD" -- .venv/bin/python "$skill/scripts/bash_notebook.py" add-cell notebooks/demo.ipynb --source 'echo "Hello from WSL"'
wsl --cd "$PWD" -- .venv/bin/python "$skill/scripts/bash_notebook.py" check notebooks/demo.ipynb
wsl --cd "$PWD" -- .venv/bin/python "$skill/scripts/bash_notebook.py" run notebooks/demo.ipynb
```

`create`, `add-cell`, and `check` only need the standard library and also run with a
Windows Python (`py <skill>\scripts\bash_notebook.py check demo.ipynb`). `kernel` and
`run` need the kernel and therefore only run in WSL.

### Select the Kernel in VS Code

1. On Windows, run **WSL: Reopen Folder in WSL** first.
2. Open the notebook and select **Select Kernel** in the top right.
3. Choose **Select Another Kernel...** > **Jupyter Kernel...** > **Bash** with the path
   `.venv/share/jupyter/kernels/bash`. **Python Environments** only offers Python
   kernels.
4. Every code cell must show **Shell Script** in its bottom right corner.
5. Run this cell to confirm which environment hosts the kernel:

   ```bash
   ps -o args= -p "$PPID"
   ```

   Expected: `<project>/.venv/bin/python -m bash_kernel -f ...`

## Script Reference

### setup-bash-kernel.sh and setup-bash-kernel.ps1

Create the environment if it is missing, install `bash_kernel`, `nbformat`, and
`nbclient`, register the kernel with `--sys-prefix`, and verify the result. Safe to run
repeatedly.

| Bash | PowerShell | Default | Meaning |
|---|---|---|---|
| `--venv PATH` | `-Venv PATH` | `.venv` | environment, relative to the current folder |
| `--python EXE` | `-Python EXE` | `python3` | Python used to create the environment |
| - | `-Distribution NAME` | default distribution | WSL distribution |

### bash_notebook.py

| Command | Purpose | Key options |
|---|---|---|
| `create NB` | create a notebook with Bash metadata and one `shellscript` cell | `--title`, `--first-cell`, `--force` |
| `add-cell NB` | insert a cell; code cells always get `shellscript` | `--source TEXT` or `--source-file FILE` (`-` = stdin), `--markdown`, `--after-id ID` or `--index N` |
| `check NB...` | verify kernelspec, language_info, cell IDs, `languageId`, and the nbformat schema | `--fix` repairs findings |
| `kernel` | verify that `bash` lives in `sys.prefix` and starts its Python | - |
| `run NB` | execute in a fresh Bash kernel; also fails on a Bash restart | `--timeout SEC`, `--inplace` saves outputs |

Exit code `0` means passed, `1` means findings.

## Rules for Cell Content

All cells share **one** running Bash process. Variables, functions, and `cd` carry over
to later cells. The start directory is the notebook's folder.

* **No top-level `exit`, `set -e`, or `set -u`.** When a command fails afterwards, Bash
  exits, the kernel only prints `Restarting Bash`, and the state of all earlier cells is
  lost. Put strict error handling in a subshell:

  ```bash
  ( set -euo pipefail; step_one; step_two )
  ```

* **Only the last command counts.** `bash_kernel` marks a cell as failed when its last
  command returns a non-zero exit code. A failure in line 1 goes unnoticed when line 2
  succeeds. Chain dependent steps with `&&`.
* **Nothing interactive.** Cells cannot read stdin; `read`, editors, and pagers block.
  Disable pagers, for example with `git --no-pager` or `PAGER=cat`.
* **Catch expected failures** so that `run` stays clean: `command || true`.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| **Bash** missing in the kernel picker | environment not registered or unknown to VS Code | run `setup-bash-kernel`; set **Python: Select Interpreter** to `.venv`; **Developer: Reload Window** |
| Windows: **Bash** missing in the picker | VS Code is not running in WSL | **WSL: Reopen Folder in WSL** |
| `module 'pexpect' has no attribute 'spawn'` | kernel started natively on Windows | create the environment in WSL |
| Cell shows `bash` instead of **Shell Script** | `metadata.vscode.languageId` missing or wrong | `check --fix` |
| `kernel` reports a foreign Python | kernelspec installed with `--user` or from another environment | `jupyter kernelspec remove bash`, then run `setup-bash-kernel` again |
| Output `Restarting Bash`, variables empty | top-level `exit`, `set -e`, or `set -u` | wrap commands in `( ... )` |
| Cell hangs until timeout | interactive command or pager | avoid stdin, disable pagers |
| `ensurepip is not available` | `python3-venv` missing | `sudo apt install python3-venv` |

> Brought to you by cpinotossi/cpt-agent-plugins
