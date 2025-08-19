# 🧠 Supreme Research MCP

Welcome to **Supreme Research MCP** – your ultimate multi-source, AI-augmented research assistant! 🚀

Leverage multiple search engines and scholarly databases simultaneously, extract rich content from any web resource or PDF, and refine results using semantic embeddings. Perfect for researchers, students, or curious minds.

---

## 🎯 Features

* 🔎 Multi-source search: Brave, DuckDuckGo, OpenAlex, arXiv, Core, CrossRef
* 📝 Automatic content extraction from URLs (HTML & PDF)
* ⏱ Timeout-safe extraction (max 15 seconds)
* 🧩 Embedding-based result refinement
* 📊 Preview and filter low-quality content
* 🤖 MCP integration for advanced LLM query expansion

---

## ⚙️ Installation

1. Clone the repository:

```bash
git clone <repo_url>
cd <repo_folder>
```

2. Install dependencies (ensure Python 3.11+):

```bash
pip install -r requirements.txt
```

3. Ensure `uv` is installed for running MCP commands:

```bash
pip install uv
```

---

## 🚀 Usage

### Single Command Usage

Use `uv run` to execute the research function directly from the command line:

```bash
uv run supreme_research_mcp run_deep_research --query "What is the capital of New York State?" --limit 5
```

* `--query`: Your research query
* `--limit`: Maximum number of results per search engine

### MCP Mode (LLM-augmented)

While running in MCP mode, the tool can expand queries, perform multi-source searches, and refine results automatically. 

### Examples of LLM-augmented queries

* `"Impact of climate change on polar bear populations"`
* `"Latest AI breakthroughs in natural language processing"`
* `"Open access COVID-19 research papers 2025"`

The system will automatically expand the query, run searches across all sources, fetch URLs, extract content (HTML/PDF), and refine results.

---

## 📌 Output Structure

Each result contains:

* `title`: Title of the paper or web page
* `url`: Source URL
* `source`: Search engine or database
* `subquery`: Expanded query used
* `text`: Extracted content
* `chars`: Number of characters extracted
* `extraction_error` (optional): Error message if extraction failed

---

## 🖼 Preview & Filtering

Low-quality results (less than 50 characters) are automatically filtered out. You can preview results using:

```python
print_results(results)
```

---

## ⚡ Refinement

Results are refined using embedding-based similarity, with configurable parameters:

* `top_k`: Number of top results to keep
* `chunk_size`: Text chunk size for embeddings
* `overlap`: Overlap size between chunks

This ensures the most relevant information is presented.

---

## 📝 Notes

* PDF and web content extraction is timeout-protected (15 seconds per URL)
* Supports HTML and PDF extraction with multiple strategies
* Designed for asynchronous execution to maximize efficiency

---

© 2025 **Akinus21**
