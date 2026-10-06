"""Unit tests for data quality reporting in processing/data_quality.py."""

from processing import ScrapedRecord
from processing.data_quality import generate_data_quality_report


def test_empty_records() -> None:
    report = generate_data_quality_report([])
    assert report["total_records"] == 0
    assert report["records_by_source"] == {}
    assert report["uniqueness_summary"]["duplicate_count"] == 0
    assert report["uniqueness_summary"]["is_fully_deduplicated"] is True
    assert report["field_completeness"]["name_or_title"]["completeness_pct"] == 0.0


def test_clean_records_quality() -> None:
    rec1 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/book1/index.html",
        name_or_title="Clean Book One",
        price=19.99,
        rating=4,
    )
    rec2 = ScrapedRecord(
        source="Quotes to Scrape",
        source_url="https://quotes.toscrape.com/page/1/",
        name_or_title="Clean Quote One",
        author="Clean Author",
        tags="inspiration;life",
    )

    report = generate_data_quality_report([rec1, rec2])

    assert report["total_records"] == 2
    assert report["records_by_source"]["Books to Scrape"] == 1
    assert report["records_by_source"]["Quotes to Scrape"] == 1

    # 100% of records have name_or_title and source_url
    assert report["field_completeness"]["name_or_title"]["completeness_pct"] == 100.0
    assert report["field_completeness"]["source_url"]["completeness_pct"] == 100.0

    # 50% have price (1 book, 1 quote)
    assert report["field_completeness"]["price"]["populated_count"] == 1
    assert report["field_completeness"]["price"]["completeness_pct"] == 50.0

    # Source-specific completeness
    assert (
        report["completeness_by_source"]["Books to Scrape"]["price"]["completeness_pct"]
        == 100.0
    )
    assert (
        report["completeness_by_source"]["Quotes to Scrape"]["price"]["completeness_pct"]
        == 0.0
    )

    # Validity
    assert report["validity_summary"]["invalid_url_count"] == 0
    assert report["validity_summary"]["invalid_price_count"] == 0
    assert report["validity_summary"]["invalid_rating_count"] == 0
    assert report["validity_summary"]["missing_name_count"] == 0

    # Uniqueness
    assert report["uniqueness_summary"]["duplicate_count"] == 0
    assert report["uniqueness_summary"]["is_fully_deduplicated"] is True


def test_quality_report_detects_defects() -> None:
    invalid_url_rec = ScrapedRecord(
        source="Books to Scrape",
        source_url="invalid-url-path",
        name_or_title="Defective Book",
        price=10.0,
        rating=3,
    )
    invalid_price_rec = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/book2/index.html",
        name_or_title="Negative Price Book",
        price=-5.0,
        rating=3,
    )
    invalid_rating_rec = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/book3/index.html",
        name_or_title="Bad Rating Book",
        price=15.0,
        rating=9,
    )

    report = generate_data_quality_report(
        [invalid_url_rec, invalid_price_rec, invalid_rating_rec]
    )

    assert report["validity_summary"]["invalid_url_count"] == 1
    assert report["validity_summary"]["invalid_price_count"] == 1
    assert report["validity_summary"]["invalid_rating_count"] == 1


def test_quality_report_detects_duplicates() -> None:
    rec1 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/dup/index.html",
        name_or_title="Identical Book",
        price=10.0,
    )
    rec2 = ScrapedRecord(
        source="Books to Scrape",
        source_url="https://books.toscrape.com/catalogue/dup/index.html",
        name_or_title="Identical Book",
        price=10.0,
    )

    report = generate_data_quality_report([rec1, rec2])

    assert report["uniqueness_summary"]["duplicate_count"] == 1
    assert report["uniqueness_summary"]["is_fully_deduplicated"] is False
