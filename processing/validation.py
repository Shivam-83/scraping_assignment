"""Data validation module providing rule-based record verification."""

from typing import Any, List

ALLOWED_SOURCES = {"Books to Scrape", "Quotes to Scrape"}


def validate_record(record: Any) -> List[str]:
    """Validate a cleaned record against business rules.

    Args:
        record: ScrapedRecord or dictionary containing record fields.

    Returns:
        List[str]: A list of machine-readable error reasons. An empty list means the record is valid.
    """
    errors: List[str] = []

    def get_field(name: str) -> Any:
        if isinstance(record, dict):
            return record.get(name)
        return getattr(record, name, None)

    # 1. Source check
    source = get_field("source")
    if source not in ALLOWED_SOURCES:
        errors.append("unknown_source")

    # 2. Name or title check (must not be empty)
    name_or_title = get_field("name_or_title")
    if not isinstance(name_or_title, str) or not name_or_title.strip():
        errors.append("missing_name")

    # 3. Source URL check (must start with http:// or https://)
    source_url = get_field("source_url")
    if not isinstance(source_url, str) or not (
        source_url.startswith("http://") or source_url.startswith("https://")
    ):
        errors.append("invalid_url")

    # 4. Price check (if present, must be numeric and >= 0)
    price = get_field("price")
    if price is not None:
        if isinstance(price, bool) or not isinstance(price, (int, float)) or price < 0:
            errors.append("invalid_price")

    # 5. Rating check (if present, must be integer between 1 and 5)
    rating = get_field("rating")
    if rating is not None:
        if isinstance(rating, bool) or not isinstance(rating, int) or not (1 <= rating <= 5):
            errors.append("invalid_rating")

    return errors
