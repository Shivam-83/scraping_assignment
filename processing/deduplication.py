"""Data deduplication module providing deterministic record fingerprinting and duplicate identification."""

import hashlib
import re
from typing import Any, List, Set, Tuple


def _normalize_string(value: Any) -> str:
    """Normalize string by lowercasing, removing punctuation, and collapsing whitespace."""
    if value is None:
        return ""
    text = str(value).lower()
    # Remove all punctuation and symbols
    text = re.sub(r"[^\w\s]", "", text)
    # Collapse multiple spaces/newlines/tabs into a single space
    text = re.sub(r"\s+", " ", text).strip()
    return text


def make_fingerprint(record: Any) -> str:
    """Generate a deterministic SHA-256 fingerprint for a record based on source-specific rules.

    Rules:
    - Books: source + title/name_or_title
    - Quotes: source + author + first 50 characters of quote/name_or_title
    """
    def get_field(name: str) -> Any:
        if isinstance(record, dict):
            return record.get(name)
        return getattr(record, name, None)

    raw_source = get_field("source") or ""
    source_norm = _normalize_string(raw_source)
    name_norm = _normalize_string(get_field("name_or_title"))

    if "quote" in source_norm:
        author_norm = _normalize_string(get_field("author"))
        quote_prefix = name_norm[:50]
        payload = f"{source_norm}|{author_norm}|{quote_prefix}"
    else:
        payload = f"{source_norm}|{name_norm}"

    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def find_duplicates(records: List[Any]) -> Tuple[List[Any], List[Any]]:
    """Partition input records into unique items and duplicate items based on SHA-256 fingerprint.

    Args:
        records: List of ScrapedRecord or dictionary records.

    Returns:
        Tuple[List[Any], List[Any]]: (unique_records, duplicate_records)
    """
    seen_fingerprints: Set[str] = set()
    unique_records: List[Any] = []
    duplicate_records: List[Any] = []

    for record in records:
        fp = make_fingerprint(record)
        if fp in seen_fingerprints:
            duplicate_records.append(record)
        else:
            seen_fingerprints.add(fp)
            unique_records.append(record)

    return unique_records, duplicate_records
