from pathlib import Path
from akinus_utils.logger import local as log
from akinus_utils.app_details import PROJECT_ROOT

def write_data(data):
    DATA_DIR = PROJECT_ROOT / "data"
    DATA_FILE = DATA_DIR / "data.txt"

    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_FILE, 'w') as file:
        file.write(data)