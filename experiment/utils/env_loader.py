import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv


def load_env(dotenv_path: Optional[str]) -> None:
    """
    Load environment variables from a .env file if provided.

    - Accepts absolute or relative paths.
    - Silently does nothing if file does not exist.
    """
    if not dotenv_path:
        return
    p = Path(dotenv_path)
    if not p.is_absolute():
        # Resolve relative to the current file's project root (exp/ directory)
        base = Path(__file__).resolve().parents[1]
        p = (base / dotenv_path).resolve()
    if p.exists():
        load_dotenv(p.as_posix())
    # Do not raise if missing; AWS default credentials chain may still work
