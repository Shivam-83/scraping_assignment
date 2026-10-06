"""Unit tests for checkpointing and resume support in processing/checkpoint.py."""

import json
from pathlib import Path
import pytest

from processing import ScrapedRecord
from processing.checkpoint import (
    clear_all_checkpoints,
    clear_checkpoint,
    get_checkpoint_path,
    has_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture(autouse=True)
def clean_checkpoints() -> None:
    """Clear all checkpoints before and after each test."""
    clear_all_checkpoints()
    yield
    clear_all_checkpoints()


def test_save_and_load_checkpoint() -> None:
    records = [
        ScrapedRecord(
            source="Books to Scrape",
            source_url="https://books.toscrape.com/catalogue/page-1.html",
            name_or_title="Book 1",
            price=10.0,
            rating=3,
        ),
        ScrapedRecord(
            source="Books to Scrape",
            source_url="https://books.toscrape.com/catalogue/page-1.html",
            name_or_title="Book 2",
            price=20.0,
            rating=4,
        ),
    ]

    saved_path = save_checkpoint(
        source="Books to Scrape",
        next_url="https://books.toscrape.com/catalogue/page-2.html",
        pages_visited=1,
        records=records,
    )

    assert saved_path.is_file()
    assert has_checkpoint("Books to Scrape") is True

    # Load and verify contents
    loaded = load_checkpoint("Books to Scrape")
    assert loaded is not None
    assert loaded["source"] == "Books to Scrape"
    assert loaded["next_url"] == "https://books.toscrape.com/catalogue/page-2.html"
    assert loaded["pages_visited"] == 1
    assert len(loaded["records"]) == 2
    assert isinstance(loaded["records"][0], ScrapedRecord)
    assert loaded["records"][0].name_or_title == "Book 1"
    assert loaded["records"][1].name_or_title == "Book 2"


def test_clear_checkpoint() -> None:
    records = [
        ScrapedRecord(
            source="Quotes to Scrape",
            source_url="https://quotes.toscrape.com/",
            name_or_title="Quote 1",
            author="Author 1",
        )
    ]
    save_checkpoint("Quotes to Scrape", "https://quotes.toscrape.com/page/2/", 1, records)
    assert has_checkpoint("Quotes to Scrape") is True

    cleared = clear_checkpoint("Quotes to Scrape")
    assert cleared is True
    assert has_checkpoint("Quotes to Scrape") is False
    assert load_checkpoint("Quotes to Scrape") is None


def test_clear_all_checkpoints() -> None:
    rec = [ScrapedRecord(source="Test", source_url="http://test.com", name_or_title="T")]
    save_checkpoint("Books to Scrape", "http://books.com/2", 1, rec)
    save_checkpoint("Quotes to Scrape", "http://quotes.com/2", 1, rec)

    assert has_checkpoint("Books to Scrape") is True
    assert has_checkpoint("Quotes to Scrape") is True

    count = clear_all_checkpoints()
    assert count >= 2
    assert has_checkpoint("Books to Scrape") is False
    assert has_checkpoint("Quotes to Scrape") is False


def test_corrupt_checkpoint_handling() -> None:
    path = get_checkpoint_path("Books to Scrape")
    path.write_text("{ not valid json !!!", encoding="utf-8")

    with pytest.raises(ValueError, match="corrupt or unreadable"):
        load_checkpoint("Books to Scrape")


def test_missing_fields_checkpoint_handling() -> None:
    path = get_checkpoint_path("Quotes to Scrape")
    path.write_text(json.dumps({"source": "Quotes to Scrape"}), encoding="utf-8")

    with pytest.raises(ValueError, match="missing required fields"):
        load_checkpoint("Quotes to Scrape")
