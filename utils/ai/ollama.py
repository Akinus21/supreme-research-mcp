import asyncio

async def ollama_query(prompt: str, model: str = "qwen2.5:1.5b") -> str:
    proc = await asyncio.create_subprocess_exec(
        "ollama", "run", model, prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        raise RuntimeError(f"Ollama CLI error: {stderr.decode().strip()}")
    return stdout.decode().strip()