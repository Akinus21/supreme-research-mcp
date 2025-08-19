from __future__ import annotations
from akinus.utils.app_details import PROJECT_ROOT
from akinus.ai.ollama import get_relevant_text_ollama
import textwrap
from typing import List, Dict, Any, Iterable, Optional
from typing import List
from akinus.ai.ollama import ollama_query, embed_with_ollama, cosine_similarity, chunk_text
import json
import asyncio
import numpy as np
from akinus.utils.logger import log
from akinus.web.scrape.fetch import fetch_url
from akinus.web.scrape.extract.extract import async_extract_from_fetched


async def fetch_text_for_query(query: str, urls: list[str]) -> list[str]:
    """
    Given a list of URLs for a query, extract text using enhanced scraper.
    Returns a list of successfully extracted texts.
    """
    texts = []

    async def extract_and_log(url):
        fetched = await fetch_url(url)
        text = await async_extract_from_fetched(fetched)
        if text and len(text) > 50:  # sanity check for low-quality text
            texts.append(text)
        return text

    await asyncio.gather(*(extract_and_log(url) for url in urls))
    return texts

def print_results(stitched: list[dict]):
    """
    Print results nicely and save full text to PROJECT_ROOT/data/results.txt
    """
    output_file = PROJECT_ROOT / "data" / "results.txt"
    output_file.parent.mkdir(parents=True, exist_ok=True)  # ensure folder exists

    print("\n=== Top Results + Extraction ===\n")
    with open(output_file, "a", encoding="utf-8") as f:
        for i, item in enumerate(stitched, start=1):
            title = item.get("title") or "(no title)"
            url = item.get("url") or "(no url)"
            print(f"[{i}] {title}\n{url}")

            # Preview for console
            if "text" in item and item["text"]:
                preview = textwrap.shorten(item["text"].replace("\n", " "), width=500)
                print(f"Chars: {item.get('chars')}")
                print(f"Preview: {preview}")

                # Save full text to file
                f.write(f"\n\n=== {i}. {title} ===\nURL: {url}\n\n")
                f.write(item["text"])
                f.write("\n" + "="*80 + "\n")
            else:
                print(f"Extraction error: {item.get('extraction_error')}")
                f.write(f"\n\n=== {i}. {title} ===\nURL: {url}\nExtraction error: {item.get('extraction_error')}\n")
            
            print("-" * 80)

def _coerce_to_text(x: Any) -> Optional[str]:
    """Return a clean str or None."""
    if x is None:
        return None
    if isinstance(x, bytes):
        try:
            x = x.decode("utf-8", errors="ignore")
        except Exception:
            return None
    if not isinstance(x, str):
        # Some libraries might hand back objects—ignore them
        return None
    # Strip NULs and normalize whitespace a bit
    x = x.replace("\x00", "").strip()
    return x or None

def _make_text_blob(stitched: List[Dict[str, Any]]) -> str:
    """
    Build a single text blob from stitched results.
    Only include items that actually have non-empty textual content.
    """
    parts: List[str] = []
    for i, item in enumerate(stitched, start=1):
        body = _coerce_to_text(item.get("text"))
        if not body:
            continue
        title = _coerce_to_text(item.get("title")) or f"Result {i}"
        url = _coerce_to_text(item.get("url")) or ""
        source = _coerce_to_text(item.get("source")) or ""
        header_lines = [f"### {title}"]
        if source or url:
            meta = " | ".join([p for p in [source, url] if p])
            header_lines.append(meta)
        header = "\n".join(header_lines)
        parts.append(f"{header}\n\n{body}")
    return "\n\n\n".join(parts)

async def refine_results(stitched: List[Dict], query: str, top_k: int = 5, chunk_size: int = 250, overlap: int = 100, include_scores: bool = False) -> str:
    """
    Refine search results globally based on the query using Ollama embeddings.
    Each document is split into chunks, embedded, and scored. The top-k chunks 
    across all documents are returned to ensure maximum relevance.

    Args:
        stitched (List[Dict]): Combined search results, each with a 'text' field.
        query (str): The search query.
        top_k (int): Number of top relevant chunks to return globally.
        chunk_size (int): Maximum number of characters per chunk.
        overlap (int): Number of overlapping characters between chunks.
        include_scores (bool): Whether to include similarity scores in the output.

    Returns:
        str: Concatenated top-k relevant text chunks.
    """
    # Filter out entries without text
    texts = [r.get("text") for r in stitched if r.get("text")]
    if not texts:
        await log("WARNING", "refine_results", "No valid text found in stitched results for embedding.")
        return ""

    # Prepare async embedding for each text
    async def embed_chunks(text: str):
        return await get_relevant_text_ollama(
            query=query,
            text=text,
            top_k=500,  # get all chunks
            chunk_size=chunk_size,
            overlap=overlap,
            include_scores=True
        )

    results = await asyncio.gather(*(embed_chunks(text) for text in texts))

    # Flatten all chunks with their scores
    all_chunks = []
    for res in results:
        for chunk in res.split("\n\n"):
            if chunk.startswith("[Score:"):
                score_part, text_part = chunk.split("]", 1)
                score = float(score_part.replace("[Score:", "").strip())
                all_chunks.append((score, text_part.strip()))
            else:
                # fallback if scores not included
                all_chunks.append((1.0, chunk.strip()))

    # Sort globally by score
    top_chunks = sorted(all_chunks, key=lambda x: x[0], reverse=True)[:top_k or len(all_chunks)]

    # Combine final top-k chunks
    combined_text = "\n\n".join([f"[Score: {score:.4f}]\n{text}" if include_scores else text for score, text in top_chunks])

    await log("INFO", "refine_results", f"Successfully refined top-{top_k} results using Ollama embeddings.")
    return combined_text

async def expand_query_ollama(
    query: str,
    model: str = "llama3.2",
    embedding_model: str = "nomic-embed-text",
    top_k: int = 3,
    similarity_threshold: float = 0.3
) -> List[str]:
    """
    Generate up to top_k contextually similar queries using Ollama, validate relevance via embeddings,
    and provide a fallback if Ollama output is malformed or empty.

    Args:
        query (str): Original search query.
        model (str, optional): Ollama model for query expansion. Defaults to "llama3.2".
        embedding_model (str, optional): Model used for computing embeddings. Defaults to "nomic-embed-text".
        top_k (int, optional): Maximum number of queries to return. Defaults to 3.
        similarity_threshold (float, optional): Minimum cosine similarity for a generated query to be considered relevant.

    Returns:
        List[str]: List of top_k contextually similar queries that are sufficiently relevant.
    """
    # 1. Prompt Ollama to generate candidate queries
    prompt = (
        f"Take this search query and create 5 distinct, contextually similar queries "
        f"that expand on the original and provide more context. "
        f"Try to determine what the user is trying to ask, and provide queries that support that intent."
        f"Try to anticipate what follow-up questions the user might have, if the original query is answered, "
        f"then provide those questions. The queries you choose should allow the user to "
        f"complete detailed research on the original query. "
        f"Return strictly as a JSON list of strings.\n\nQuery: {query}\n\nList:"
    )
    
    try:
        response = await ollama_query(prompt, model=model)
        try:
            candidates = json.loads(response)
            if not isinstance(candidates, list):
                raise ValueError(f"Ollama response is not a list: {candidates}")
            candidates = [str(c).strip() for c in candidates if c]
        except Exception:
            # Fallback if JSON parsing fails
            candidates = [line.strip() for line in response.splitlines() if line.strip()]

        if not candidates:
            raise ValueError("Ollama returned empty candidate list")
        
        await log("INFO", "expand_query_ollama", f"Ollama generated {len(candidates)} candidate queries")
    
    except Exception as e:
        await log("WARNING", "expand_query_ollama", f"Ollama failed or returned invalid output: {e}")
        # Fallback: simple variations of the original query
        candidates = [
            f"{query} context",
            f"{query} explanation",
            f"{query} details",
            f"{query} background",
            f"{query} overview"
        ][:5]
        await log("INFO", "expand_query_ollama", f"Using fallback candidates: {candidates}")

    # 2. Compute embeddings asynchronously for query and all candidates
    async def async_embed(text: str):
        return await asyncio.to_thread(embed_with_ollama, text, model=embedding_model)

    query_emb_task = asyncio.create_task(async_embed(query))
    candidate_emb_tasks = [async_embed(c) for c in candidates]

    query_emb = await query_emb_task
    candidate_embs = await asyncio.gather(*candidate_emb_tasks)

    # 3. Score candidates by cosine similarity
    scored = []
    for cand, emb in zip(candidates, candidate_embs):
        score = cosine_similarity(query_emb, emb)
        if score >= similarity_threshold:
            scored.append((score, cand))

    # 4. Sort by similarity descending and return top_k
    scored.sort(key=lambda x: x[0], reverse=True)
    final_queries = [c for _, c in scored[:top_k]]

    await log("INFO", "expand_query_ollama", f"Returning top {len(final_queries)} queries: {final_queries}")
    return final_queries
