import os
from pathlib import Path
from datetime import datetime
import asyncio

# Define paths
BASE_DIR = Path(__file__).resolve().parent
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "logger.log"  # changed from server.logs to logger.log
MAX_LOG_SIZE = 2 * 1024 * 1024  # 2MB in bytes

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Message types and their priorities
LOG_LEVELS = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50
}

# Async-safe log function
log_lock = asyncio.Lock()

def rotate_log_file():
    """Check log size and rotate if necessary."""
    if LOG_FILE.exists() and LOG_FILE.stat().st_size > MAX_LOG_SIZE:
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        rotated_file = LOGS_DIR / f"{timestamp}.log"
        LOG_FILE.rename(rotated_file)
        LOG_FILE.touch()  # Create a new empty log file

def _write_log_line(line: str):
    """Blocking I/O to write the log line."""
    rotate_log_file()
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)

async def log(message_type: str, script: str, message: str):
    """
    Write a log line to logger.log in the format:
    priority timestamp: message type: script name: Message
    """
    priority = LOG_LEVELS.get(message_type.upper(), 20)  # Default to INFO
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{priority} {timestamp}: {message_type.upper()}: {script}: {message}\n"

    async with log_lock:
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, _write_log_line, line)
