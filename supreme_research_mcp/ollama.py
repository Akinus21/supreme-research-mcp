# ollama.py

import asyncio
import json
from akinus_utils.logger import local as log

async def generate_search_queries(original_query: str) -> list[str]:
    response_text = ""
    prompt = f"""
Given the user query below, generate exactly 3 distinct, concise, and focused search queries that capture the intent and keywords needed to find relevant scholarly or trusted sources.  
Return only the queries as a JSON list of strings.

User query:
\"\"\"{original_query}\"\"\"

Search queries:"""

    try:
        response_text = await ollama_query(prompt)
        queries = json.loads(response_text)
        if isinstance(queries, list) and all(isinstance(q, str) for q in queries):
            return queries
    except Exception:
        await log("ERROR", "ollama.py", f"Failed to parse Ollama response: {response_text}")
        pass

    # fallback parse lines
    lines = [line.strip('- ').strip() for line in response_text.strip().splitlines() if line.strip()]
    if len(lines) >= 3:
        return lines[:3]
    return [original_query] * 3

async def ollama_query(prompt: str, model: str = "qwen2.5:1.5b") -> str:
    proc = await asyncio.create_subprocess_exec(
        "ollama", "chat", model, "--prompt", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {stderr.decode()}")
    return stdout.decode()