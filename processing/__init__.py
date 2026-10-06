"""Processing package containing pipeline record models and transformations."""

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

RECORD_FIELDS: List[str] = [
    "source",
    "source_url",
    "name_or_title",
    "category",
    "price",
    "rating",
    "author",
    "tags",
    "description",
    "scraped_at",
]


@dataclass
class ScrapedRecord:
    """Unified data model representing an extracted item from either scraper source."""

    source: str
    source_url: str
    name_or_title: str
    category: Optional[str] = None
    price: Optional[Union[float, str]] = None
    rating: Optional[Union[int, str]] = None
    author: Optional[str] = None
    tags: Optional[str] = None
    description: Optional[str] = None
    scraped_at: Optional[str] = None

    def __post_init__(self) -> None:
        if self.scraped_at is None:
            self.scraped_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert record to Python dictionary."""
        return asdict(self)

    def to_csv_row(self) -> Dict[str, str]:
        """Convert record into a CSV row dictionary where None is mapped to an empty string."""
        row: Dict[str, str] = {}
        for field in RECORD_FIELDS:
            val = getattr(self, field)
            if val is None:
                row[field] = ""
            elif isinstance(val, float):
                row[field] = f"{val:.2f}"
            else:
                row[field] = str(val)
        return row


from processing.checkpoint import (
    clear_all_checkpoints,
    clear_checkpoint,
    get_checkpoint_path,
    has_checkpoint,
    load_checkpoint,
    save_checkpoint,
)
from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)
from processing.data_quality import generate_data_quality_report
from processing.deduplication import find_duplicates, make_fingerprint
from processing.validation import validate_record

__all__ = [
    "RECORD_FIELDS",
    "ScrapedRecord",
    "clean_price",
    "clean_rating",
    "clean_record",
    "clean_tags",
    "clean_text",
    "clear_all_checkpoints",
    "clear_checkpoint",
    "find_duplicates",
    "generate_data_quality_report",
    "get_checkpoint_path",
    "has_checkpoint",
    "load_checkpoint",
    "make_fingerprint",
    "normalize_url",
    "save_checkpoint",
    "strip_quotes",
    "validate_record",
]
