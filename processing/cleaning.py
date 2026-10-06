"""Data cleaning module providing pure, testable functions and record standardization."""

from typing import Any, List, Optional
from urllib.parse import urlparse
import re

from processing import ScrapedRecord

RATING_MAP = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
}


def clean_text(value: Optional[str]) -> Optional[str]:
    """Clean string values by normalizing whitespace, tabs, newlines, and non-breaking spaces.

    Returns None for empty or whitespace-only values.
    """
    if value is None:
        return None
    # Replace non-breaking spaces
    cleaned = value.replace("\xa0", " ").replace("\u00a0", " ")
    # Collapse multiple whitespaces/tabs/newlines into a single space
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned if cleaned else None


def strip_quotes(value: Optional[str]) -> Optional[str]:
    """Strip leading and trailing curly or straight quotation marks from text."""
    if value is None:
        return None
    text = value.strip()
    # Strip opening/closing typographic quotes (“ ” ‘ ’ « ») and straight quotes (" ')
    quote_chars = "“”\"'‘’«»"
    return text.strip(quote_chars).strip() if text else None


def clean_price(value: Any) -> Optional[float]:
    """Extract and parse floating-point numeric price from string representations.

    Handles currency symbols, non-breaking spaces, encoding artifacts (e.g. Â£), and commas.
    Returns None if no valid numeric value can be parsed.
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return round(float(value), 2)

    text = str(value).replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None

    try:
        return round(float(match.group(1)), 2)
    except (ValueError, TypeError):
        return None


def clean_rating(value: Any) -> Optional[int]:
    """Map word ratings ('One', 'Two', 'Three', 'Four', 'Five') to integers 1-5.

    Returns None if value cannot be mapped to a valid 1-5 rating.
    """
    if value is None:
        return None
    if isinstance(value, int) and 1 <= value <= 5:
        return value
    if isinstance(value, str):
        val_lower = value.strip().lower()
        if val_lower in RATING_MAP:
            return RATING_MAP[val_lower]
        if val_lower.isdigit():
            num = int(val_lower)
            if 1 <= num <= 5:
                return num
    return None


def clean_tags(value: Any) -> Optional[str]:
    """Clean whitespace, lowercase, sort alphabetically, and join tags with semicolons.

    Accepts semicolon/comma-delimited strings or iterables of tags.
    Returns None if no tags remain.
    """
    if value is None:
        return None

    raw_tags: List[str] = []
    if isinstance(value, str):
        parts = re.split(r"[;,]", value)
        raw_tags = parts
    elif isinstance(value, (list, tuple, set)):
        raw_tags = [str(item) for item in value]
    else:
        raw_tags = [str(value)]

    cleaned_list = []
    for tag in raw_tags:
        cleaned_tag = clean_text(tag)
        if cleaned_tag:
            cleaned_list.append(cleaned_tag.lower())

    unique_sorted = sorted(set(cleaned_list))
    return ";".join(unique_sorted) if unique_sorted else None


def normalize_url(value: Optional[str]) -> Optional[str]:
    """Ensure URL is a complete absolute HTTP/HTTPS URL.

    Returns None if value is empty, malformed, or does not use http/https scheme.
    """
    if value is None:
        return None
    url_str = value.strip()
    if not url_str:
        return None

    try:
        parsed = urlparse(url_str)
        if parsed.scheme.lower() in ("http", "https") and parsed.netloc:
            return url_str
    except Exception:
        return None

    return None


def clean_record(record: ScrapedRecord) -> ScrapedRecord:
    """Transform raw ScrapedRecord into standardized cleaned record according to source rules."""
    cleaned_source = clean_text(record.source) or ""
    cleaned_url = normalize_url(record.source_url) or record.source_url

    if cleaned_source == "Books to Scrape":
        return ScrapedRecord(
            source=cleaned_source,
            source_url=cleaned_url,
            name_or_title=clean_text(record.name_or_title) or "",
            category=clean_text(record.category),
            price=clean_price(record.price),
            rating=clean_rating(record.rating),
            author=None,
            tags=None,
            description=clean_text(record.description),
            scraped_at=record.scraped_at,
        )
    elif cleaned_source == "Quotes to Scrape":
        quote_text = clean_text(record.name_or_title)
        stripped_quote = strip_quotes(quote_text) if quote_text else ""
        return ScrapedRecord(
            source=cleaned_source,
            source_url=cleaned_url,
            name_or_title=stripped_quote,
            category=None,
            price=None,
            rating=None,
            author=clean_text(record.author),
            tags=clean_tags(record.tags),
            description=None,
            scraped_at=record.scraped_at,
        )
    else:
        return ScrapedRecord(
            source=cleaned_source,
            source_url=cleaned_url,
            name_or_title=clean_text(record.name_or_title) or "",
            category=clean_text(record.category),
            price=clean_price(record.price),
            rating=clean_rating(record.rating),
            author=clean_text(record.author),
            tags=clean_tags(record.tags),
            description=clean_text(record.description),
            scraped_at=record.scraped_at,
        )
