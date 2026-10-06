"""Unit tests for processing/cleaning.py functions."""

import pytest
from processing import ScrapedRecord
from processing.cleaning import (
    clean_price,
    clean_rating,
    clean_record,
    clean_tags,
    clean_text,
    normalize_url,
    strip_quotes,
)


def test_clean_text_normalizes_whitespace() -> None:
    raw = "  Hello   \n\t  World  \xa0 "
    assert clean_text(raw) == "Hello World"


def test_clean_text_returns_none_for_empty() -> None:
    assert clean_text(None) is None
    assert clean_text("") is None
    assert clean_text("   \n\t  \xa0 ") is None


def test_strip_quotes_curly_and_straight() -> None:
    curly = "“The world as we have created it is a process of our thinking.”"
    assert strip_quotes(curly) == "The world as we have created it is a process of our thinking."

    straight = '"It is our choices, Harry."'
    assert strip_quotes(straight) == "It is our choices, Harry."

    single = "‘A quote with single typographic marks’"
    assert strip_quotes(single) == "A quote with single typographic marks"

    plain = "No quotes here"
    assert strip_quotes(plain) == "No quotes here"
    assert strip_quotes(None) is None


def test_clean_price_extracts_numeric_values() -> None:
    assert clean_price("£51.77") == 51.77
    assert clean_price("Â£51.77") == 51.77
    assert clean_price("£1,234.56") == 1234.56
    assert clean_price(25.5) == 25.5
    assert clean_price("10") == 10.0


def test_clean_price_invalid_returns_none() -> None:
    assert clean_price(None) is None
    assert clean_price("") is None
    assert clean_price("Free") is None
    assert clean_price("N/A") is None


def test_clean_rating_maps_words_to_integers() -> None:
    assert clean_rating("One") == 1
    assert clean_rating("Two") == 2
    assert clean_rating("Three") == 3
    assert clean_rating("Four") == 4
    assert clean_rating("Five") == 5
    assert clean_rating("three") == 3
    assert clean_rating(4) == 4


def test_clean_rating_invalid_returns_none() -> None:
    assert clean_rating(None) is None
    assert clean_rating("Zero") is None
    assert clean_rating("Six") == None
    assert clean_rating("Unknown") is None


def test_clean_tags_normalizes_lowercases_and_sorts() -> None:
    raw_str = "World; change; Deep-thoughts; thinking"
    assert clean_tags(raw_str) == "change;deep-thoughts;thinking;world"

    raw_list = ["Thinking", " Change ", "world", "change"]
    assert clean_tags(raw_list) == "change;thinking;world"

    assert clean_tags(None) is None
    assert clean_tags("") is None
    assert clean_tags("  ; ; ") is None


def test_normalize_url_valid_and_invalid() -> None:
    valid_https = "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert normalize_url(valid_https) == valid_https

    valid_http = "http://quotes.toscrape.com/page/1/"
    assert normalize_url(valid_http) == valid_http

    assert normalize_url("ftp://example.com/file") is None
    assert normalize_url("/catalogue/page-2.html") is None
    assert normalize_url("") is None
    assert normalize_url(None) is None


def test_clean_record_books() -> None:
    raw = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
        name_or_title="  A Light in the Attic \n ",
        price="Â£51.77",
        rating="Three",
        author="Ignored Author",
        tags="ignored;tags",
    )
    cleaned = clean_record(raw)
    assert cleaned.source == "Books to Scrape"
    assert cleaned.name_or_title == "A Light in the Attic"
    assert cleaned.price == 51.77
    assert cleaned.rating == 3
    assert cleaned.author is None
    assert cleaned.tags is None


def test_clean_record_quotes() -> None:
    raw = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/1/",
        name_or_title="“Life is what happens to us while we are making other plans.”",
        author="  Allen Saunders  ",
        tags="fate; Life ; choices",
        price="£10.00",
        rating="Five",
    )
    cleaned = clean_record(raw)
    assert cleaned.source == "Quotes to Scrape"
    assert cleaned.name_or_title == "Life is what happens to us while we are making other plans."
    assert cleaned.author == "Allen Saunders"
    assert cleaned.tags == "choices;fate;life"
    assert cleaned.price is None
    assert cleaned.rating is None
