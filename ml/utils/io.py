"""File/logging I/O helpers.

Centralises filesystem I/O so the rest of the platform never touches
``Path``/``open`` directly. All writes are atomic (write-to-temp then
rename) so a crash mid-write never corrupts an artifact — important for
the experiment registry and the digital twin history store.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

logger = logging.getLogger(__name__)


def ensure_dir(path: str | Path) -> Path:
    """Create a directory (and parents) if missing; return it as a Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write(path: str | Path, content: str | bytes) -> Path:
    """Write ``content`` to ``path`` atomically via a temp file + rename."""
    p = Path(path)
    ensure_dir(p.parent)
    fd, tmp = tempfile.mkstemp(dir=str(p.parent), suffix=".tmp")
    try:
        mode = "wb" if isinstance(content, bytes) else "w"
        with os.fdopen(fd, mode, encoding=None if isinstance(content, bytes) else "utf-8") as fh:
            fh.write(content)
        os.replace(tmp, p)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise
    return p


def save_json(path: str | Path, obj: Any, indent: int = 2) -> Path:
    """Atomically serialise ``obj`` to JSON."""
    return atomic_write(path, json.dumps(obj, indent=indent, default=str))


def load_json(path: str | Path) -> Any:
    """Load a JSON file as a Python object."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def save_dataframe(
    df: pd.DataFrame,
    path: str | Path,
    format: str = "parquet",
) -> Path:
    """Persist a DataFrame to the requested format (auto-detected).

    Supported formats: ``parquet``, ``csv``, ``json``, ``feather``.
    """
    p = Path(path)
    ensure_dir(p.parent)
    fmt = (format or p.suffix.lstrip(".")).lower()
    if fmt == "csv":
        df.to_csv(p, index=False)
    elif fmt == "parquet":
        df.to_parquet(p, index=False)
    elif fmt == "json":
        df.to_json(p, orient="records", lines=True)
    elif fmt == "feather":
        df.to_feather(p)
    else:
        raise ValueError(f"unsupported dataframe format: {fmt}")
    return p


def load_dataframe(path: str | Path, format: Optional[str] = None) -> pd.DataFrame:
    """Load a DataFrame from disk, auto-detecting the format from suffix."""
    p = Path(path)
    fmt = (format or p.suffix.lstrip(".")).lower()
    if fmt == "csv":
        return pd.read_csv(p)
    if fmt == "parquet":
        return pd.read_parquet(p)
    if fmt == "json":
        return pd.read_json(p, orient="records", lines=True)
    if fmt == "feather":
        return pd.read_feather(p)
    raise ValueError(f"unsupported dataframe format: {fmt}")
