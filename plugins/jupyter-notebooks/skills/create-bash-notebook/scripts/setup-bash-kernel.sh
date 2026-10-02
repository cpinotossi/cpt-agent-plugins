#!/usr/bin/env bash
# Creates a Python environment and registers the Jupyter Bash kernel inside it.
# Linux, macOS, and WSL. Usage: setup-bash-kernel.sh [--venv PATH] [--python PYTHON]
set -euo pipefail

venv=".venv"
python_bin="python3"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --venv) venv="$2"; shift 2 ;;
    --python) python_bin="$2"; shift 2 ;;
    -h|--help) sed -n '2,3p' "$0"; exit 0 ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$(uname -s)" in
  Linux|Darwin) ;;
  *) echo "bash_kernel only runs on Linux, macOS, or WSL (pexpect.spawn)." >&2; exit 1 ;;
esac

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -x "$venv/bin/python" ]]; then
  echo "Creating environment: $venv"
  if ! "$python_bin" -m venv "$venv"; then
    echo "venv failed. On Debian/Ubuntu: sudo apt install python3-venv" >&2
    exit 1
  fi
fi

py="$venv/bin/python"
"$py" -m pip install --quiet --upgrade pip
"$py" -m pip install --quiet bash_kernel nbformat nbclient
# --sys-prefix writes the kernelspec to <venv>/share/jupyter/kernels/bash and
# records this environment's Python as the kernel command.
"$py" -m bash_kernel.install --sys-prefix
"$py" "$script_dir/bash_notebook.py" kernel
