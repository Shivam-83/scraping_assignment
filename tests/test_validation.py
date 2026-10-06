"""Unit tests for record validation in processing/validation.py."""

import pytest
from processing import ScrapedRecord
from processing.validation import validate_record


def test_valid_book_record() -> None:
    record = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        name_or_title="A Light in the Attic",
        price=51.77,
        rating=3,
    )
    errors = validate_record(record)
    assert errors == []


def test_valid_quote_record() -> None:
    record = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/1/",
        name_or_title="The world as we have created it is a process of our thinking.",
        author="Albert Einstein",
        tags="change;deep-thoughts;thinking;world",
        price=None,
        rating=None,
    )
    errors = validate_record(record)
    assert errors == []


def test_unknown_source() -> None:
    record = ScrapedRecord(
        source="Unknown Source",
        source_url="https://example.com/item/1",
        name_or_title="Valid Title",
    )
    assert validate_record(record) == ["unknown_source"]


def test_missing_name_or_title() -> None:
    record_none = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item/index.html",
        name_or_title="",
    )
    assert validate_record(record_none) == ["missing_name"]

    record_whitespace = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item/index.html",
        name_or_title="   \n\t  ",
    )
    assert validate_record(record_whitespace) == ["missing_name"]


def test_invalid_source_url() -> None:
    record_relative = ScrapedRecord(
        source="Books to Scrape",
        source_url="catalogue/page-2.html",
        name_or_title="A Title",
    )
    assert validate_record(record_relative) == ["invalid_url"]

    record_ftp = ScrapedRecord(
        source="Books to Scrape",
        source_url="ftp://books.toscrape.com/item",
        name_or_title="A Title",
    )
    assert validate_record(record_ftp) == ["invalid_url"]


def test_invalid_price() -> None:
    # Negative price
    rec_neg = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        price=-1.0,
    )
    assert validate_record(rec_neg) == ["invalid_price"]

    # String price (uncleaned)
    rec_str = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        price="£50.00",
    )
    assert validate_record(rec_str) == ["invalid_price"]

    # Boolean price
    rec_bool = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        price=True,  # type: ignore
    )
    assert validate_record(rec_bool) == ["invalid_price"]


def test_invalid_rating() -> None:
    # Out of range ratings
    for invalid_val in [0, 6, -1, 10]:
        rec = ScrapedRecord(
            source="Books to Scrape",
            source_url="https://books.toscrape.com/catalogue/item",
            name_or_title="A Title",
            rating=invalid_val,
        )
        assert validate_record(rec) == ["invalid_rating"]

    # Float rating
    rec_float = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        rating=3.5,  # type: ignore
    )
    assert validate_record(rec_float) == ["invalid_rating"]

    # Word rating (uncleaned)
    rec_str = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        rating="Three",
    )
    assert validate_record(rec_str) == ["invalid_rating"]

    # Boolean rating
    rec_bool = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/item",
        name_or_title="A Title",
        rating=True,  # type: ignore
    )
    assert validate_record(rec_bool) == ["invalid_rating"]


def test_multiple_validation_errors() -> None:
    record = {
        "source": "Invalid Source",
        "source_url": "ftp://not-http.com",
        "name_or_title": "",
        "price": -10.0,
        "rating": 7,
    }
    errors = validate_record(record)
    assert "unknown_source" in errors
    assert "missing_name" in errors
    assert "invalid_url" in errors
    assert "invalid_price" in errors
    assert "invalid_rating" in errors
    assert len(errors) == 5


def test_record_immutability_during_validation() -> None:
    record = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/item",
        name_or_title="Test Title",
        price=19.99,
        rating=4,
    )
    snapshot = record.to_dict()
    validate_record(record)
    assert record.to_dict() == snapshot
