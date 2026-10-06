"""Unit tests for deduplication module in processing/deduplication.py."""

import pytest
from processing import ScrapedRecord
from processing.deduplication import find_duplicates, make_fingerprint


def test_books_casing_and_whitespace_equivalence() -> None:
    rec1 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/example_1/index.html",
        name_or_title="Example Book Title",
        price=10.0,
    )
    rec2 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/example_2/index.html",
        name_or_title="  Example   Book  Title  ",
        price=12.0,
    )
    rec3 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/example_3/index.html",
        name_or_title="EXAMPLE BOOK TITLE",
        price=15.0,
    )
    rec_punct = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/example_4/index.html",
        name_or_title="Example: Book Title!",
        price=15.0,
    )

    fp1 = make_fingerprint(rec1)
    fp2 = make_fingerprint(rec2)
    fp3 = make_fingerprint(rec3)
    fp_punct = make_fingerprint(rec_punct)

    assert fp1 == fp2 == fp3 == fp_punct


def test_identical_records() -> None:
    rec1 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/exact_match/index.html",
        name_or_title="Exact Match Title",
        price=10.0,
    )
    rec2 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/exact_match/index.html",
        name_or_title="Exact Match Title",
        price=10.0,
    )
    uniques, duplicates = find_duplicates([rec1, rec2])
    assert len(uniques) == 1
    assert len(duplicates) == 1
    assert duplicates[0] == rec2


def test_quotes_fingerprint_uses_author_and_first_50_chars() -> None:
    long_quote_a = (
        "The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking. (Extra text)"
    )
    long_quote_b = (
        "The world as we have created it is a process of our thinking. It cannot be changed without changing our thinking. (Different ending)"
    )

    rec1 = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/1/",
        name_or_title=long_quote_a,
        author="Albert Einstein",
    )
    rec2 = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/2/",
        name_or_title=long_quote_b,
        author="Albert Einstein",
    )
    rec_diff_author = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/1/",
        name_or_title=long_quote_a,
        author="Someone Else",
    )

    # First 50 normalized characters of both quotes are identical
    assert make_fingerprint(rec1) == make_fingerprint(rec2)
    # Different author must yield a different fingerprint
    assert make_fingerprint(rec1) != make_fingerprint(rec_diff_author)


def test_different_sources_produce_different_fingerprints() -> None:
    rec_book = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/item",
        name_or_title="Common Title",
    )
    rec_quote = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/item",
        name_or_title="Common Title",
        author="Author",
    )
    assert make_fingerprint(rec_book) != make_fingerprint(rec_quote)


def test_find_duplicates_partitions_correctly() -> None:
    rec_a = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/1",
        name_or_title="Book Alpha",
    )
    rec_b = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/2",
        name_or_title="Book Beta",
    )
    # Duplicate of Alpha with different case and spacing
    rec_a_dup = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/3",
        name_or_title="  book   alpha  ",
    )
    rec_c = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/1",
        name_or_title="A unique quote text",
        author="Famous Author",
    )
    # Duplicate of Quote C with surrounding quotes and extra whitespace
    rec_c_dup = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/2",
        name_or_title="“A unique quote text”",
        author="Famous Author",
    )

    input_records = [rec_a, rec_b, rec_a_dup, rec_c, rec_c_dup]

    uniques, duplicates = find_duplicates(input_records)

    assert len(uniques) == 3
    assert len(duplicates) == 2

    assert uniques == [rec_a, rec_b, rec_c]
    assert duplicates == [rec_a_dup, rec_c_dup]


def test_find_duplicates_with_no_duplicates() -> None:
    rec1 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/1",
        name_or_title="Unique Book 1",
    )
    rec2 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/2",
        name_or_title="Unique Book 2",
    )
    uniques, duplicates = find_duplicates([rec1, rec2])
    assert len(uniques) == 2
    assert len(duplicates) == 0
