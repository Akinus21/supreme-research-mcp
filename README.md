# supreme_research_mcp
Base template for a simple Python project using [uv](https://docs.astral.sh/uv/).

## Description
A simple CLI example that runs instantly after cloning, or can be installed globally for use anywhere.

---

## 🚀 Run Without Installing
Clone the repository and run the project directly with `uv`:

```bash
git clone https://github.com/YOURNAME/supreme_research_mcp.git
cd supreme_research_mcp
uv run supreme_research_mcp
```
This will:

Create an isolated virtual environment in .venv (if it doesn’t already exist)

Install any dependencies from pyproject.toml

Run the supreme_research_mcp CLI

🌍 Install Globally
If you want to use the CLI anywhere on your system without uv run:

```bash
git clone https://github.com/YOURNAME/supreme_research_mcp.git
cd supreme_research_mcp
uv pip install .
```
Then run:

```bash
supreme_research_mcp
```
from any directory.

🗑️ Uninstall
```bash
uv pip uninstall supreme_research_mcp
```
