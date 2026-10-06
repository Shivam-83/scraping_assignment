"""Checkpoint management module for state persistence and interrupted crawl recovery."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from processing import ScrapedRecord

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent
CHECKPOINTS_DIR = BASE_DIR / "checkpoints"


def get_checkpoint_dir() -> Path:
    """Ensure and return the checkpoints directory path."""
    CHECKPOINTS_DIR.mkdir(parents=True, exist_ok=True)
    return CHECKPOINTS_DIR


def _sanitize_source_slug(source: str) -> str:
    """Map source name to filename slug."""
    if "book" in source.lower():
        return "books"
    if "quote" in source.lower():
        return "quotes"
    return "".join(c if c.isalnum() else "_" for c in source.lower()).strip("_")


def get_checkpoint_path(source: str) -> Path:
    """Return the checkpoint JSON file path for a specific source."""
    slug = _sanitize_source_slug(source)
    return get_checkpoint_dir() / f"{slug}_checkpoint.json"


def has_checkpoint(source: str) -> bool:
    """Check if a checkpoint file exists for the given source."""
    return get_checkpoint_path(source).is_file()


def save_checkpoint(
    source: str,
    next_url: Optional[str],
    pages_visited: int,
    records: List[ScrapedRecord],
) -> Path:
    """Persist scraper progress and collected records to JSON checkpoint file.

    Args:
        source: Name of the scraper source.
        next_url: Discovered next-page URL to resume from (or None if completed).
        pages_visited: Number of pages processed up to this point.
        records: List of ScrapedRecord objects collected so far.

    Returns:
        Path: Target checkpoint file path.
    """
    path = get_checkpoint_path(source)
    payload: Dict[str, Any] = {
        "source": source,
        "next_url": next_url,
        "pages_visited": pages_visited,
        "records_count": len(records),
        "records": [rec.to_dict() for rec in records],
    }

    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        logger.debug(
            "Checkpoint saved for %s at page %d (%d records) -> %s",
            source,
            pages_visited,
            len(records),
            path.name,
        )
    except Exception as exc:
        logger.warning(
            "Could not save checkpoint for %s to %s: %s",
            source,
            path,
            exc,
        )
    return path


def load_checkpoint(source: str) -> Optional[Dict[str, Any]]:
    """Load and validate checkpoint state from disk.

    Returns:
        Optional[Dict[str, Any]]: Validated checkpoint dictionary containing
            'next_url', 'pages_visited', and deserialized 'records'.
            Returns None if no checkpoint exists.

    Raises:
        ValueError: If checkpoint file exists but is corrupted or contains invalid data.
    """
    path = get_checkpoint_path(source)
    if not path.is_file():
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        raise ValueError(
            f"Checkpoint file '{path}' is corrupt or unreadable: {exc}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"Checkpoint in '{path}' is not a JSON object.")

    required_keys = {"source", "next_url", "pages_visited", "records"}
    missing = required_keys - set(data.keys())
    if missing:
        raise ValueError(
            f"Checkpoint in '{path}' is missing required fields: {', '.join(sorted(missing))}"
        )

    if not isinstance(data["records"], list):
        raise ValueError(f"Checkpoint 'records' in '{path}' must be a list.")

    deserialized_records: List[ScrapedRecord] = []
    for idx, r in enumerate(data["records"]):
        if not isinstance(r, dict):
            raise ValueError(
                f"Checkpoint record #{idx} in '{path}' is not a valid dictionary."
            )
        try:
            deserialized_records.append(ScrapedRecord(**r))
        except TypeError as exc:
            raise ValueError(
                f"Checkpoint record #{idx} in '{path}' has invalid schema: {exc}"
            ) from exc

    return {
        "source": data["source"],
        "next_url": data["next_url"],
        "pages_visited": int(data.get("pages_visited", 0)),
        "records": deserialized_records,
    }


def clear_checkpoint(source: str) -> bool:
    """Remove checkpoint file upon successful source completion."""
    path = get_checkpoint_path(source)
    if path.is_file():
        try:
            path.unlink()
            logger.info("Cleared checkpoint for %s (%s).", source, path.name)
            return True
        except OSError as exc:
            logger.warning("Could not delete checkpoint %s: %s", path, exc)
            return False
    return False


def clear_all_checkpoints() -> int:
    """Remove all existing checkpoint files in the checkpoints directory."""
    chk_dir = get_checkpoint_dir()
    count = 0
    for chk_file in chk_dir.glob("*_checkpoint.json"):
        try:
            chk_file.unlink()
            count += 1
        except OSError as exc:
            logger.warning("Could not delete checkpoint %s: %s", chk_file, exc)
    logger.info("Cleared %d checkpoint file(s).", count)
    return count
