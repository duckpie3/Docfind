# Docfind

A Python script for inspecting headings and extracting passages from reStructuredText files.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)

## Setup

Create the virtual environment and install the project:

```bash
uv sync
```

Set the documentation download directory before running the inspector. If you
do not set it, the default is `/tmp/tutorials`.

```bash
export DOCUMENTATION_DOWNLOAD_DIR="$HOME/path/to/tutorials"
uv run python src/inspect_rst.py
```

On Windows PowerShell, use:

```powershell
$env:DOCUMENTATION_DOWNLOAD_DIR = "$HOME\path\to\tutorials"
uv run python src/inspect_rst.py
```