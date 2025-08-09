# supreme-research-mcp
Base template for a simple Python project using [uv](https://docs.astral.sh/uv/).

## Description
A simple CLI example that runs instantly after cloning, or can be installed globally for use anywhere.

---

## 🚀 Run Without Installing
Clone the repository and run the project directly with `uv`:

```bash
git clone https://github.com/YOURNAME/supreme-research-mcp.git
cd supreme-research-mcp
uv run supreme-research-mcp
```
This will:

Create an isolated virtual environment in .venv (if it doesn’t already exist)

Install any dependencies from pyproject.toml

Run the supreme-research-mcp CLI

🌍 Install Globally
If you want to use the CLI anywhere on your system without uv run:

```bash
git clone https://github.com/YOURNAME/supreme-research-mcp.git
cd supreme-research-mcp
uv pip install .
```
Then run:

```bash
supreme-research-mcp
```
from any directory.

🗑️ Uninstall
```bash
uv pip uninstall supreme-research-mcp
```
