"""Data quality analysis module for evaluating post-pipeline datasets."""

from typing import Any, Dict, List, Union

from processing import RECORD_FIELDS, ScrapedRecord
from processing.deduplication import find_duplicates
from processing.validation import validate_record


def _is_missing(value: Any) -> bool:
    """Determine whether a field value is null or empty."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    return False


def _get_field(record: Any, field_name: str) -> Any:
    """Extract field value from ScrapedRecord or dictionary."""
    if isinstance(record, dict):
        return record.get(field_name)
    return getattr(record, field_name, None)


def generate_data_quality_report(
    records: List[Union[ScrapedRecord, Dict[str, Any]]],
) -> Dict[str, Any]:
    """Analyze the final standardized dataset and generate a comprehensive quality report.

    Args:
        records: List of cleaned, validated, and deduplicated records.

    Returns:
        Dict[str, Any]: Detailed metrics covering completeness, validity, and uniqueness.
    """
    total_records = len(records)

    # 1. Source distribution
    records_by_source: Dict[str, int] = {}
    for rec in records:
        src = str(_get_field(rec, "source") or "Unknown")
        records_by_source[src] = records_by_source.get(src, 0) + 1

    # 2. Overall field completeness
    overall_field_metrics: Dict[str, Dict[str, Any]] = {}
    for field in RECORD_FIELDS:
        missing_count = sum(1 for rec in records if _is_missing(_get_field(rec, field)))
        populated_count = total_records - missing_count
        completeness_pct = (
            round((populated_count / total_records) * 100, 2)
            if total_records > 0
            else 0.0
        )
        overall_field_metrics[field] = {
            "populated_count": populated_count,
            "missing_count": missing_count,
            "completeness_pct": completeness_pct,
        }

    # 3. Source-specific field completeness
    completeness_by_source: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for src_name, src_total in records_by_source.items():
        src_records = [
            r for r in records if str(_get_field(r, "source") or "Unknown") == src_name
        ]
        completeness_by_source[src_name] = {}
        for field in RECORD_FIELDS:
            src_missing = sum(1 for r in src_records if _is_missing(_get_field(r, field)))
            src_populated = src_total - src_missing
            src_pct = (
                round((src_populated / src_total) * 100, 2)
                if src_total > 0
                else 0.0
            )
            completeness_by_source[src_name][field] = {
                "populated_count": src_populated,
                "missing_count": src_missing,
                "completeness_pct": src_pct,
            }

    # 4. Validity checks using existing validation logic
    invalid_url_count = 0
    invalid_price_count = 0
    invalid_rating_count = 0
    unknown_source_count = 0
    missing_name_count = 0

    for rec in records:
        errors = validate_record(rec)
        if "invalid_url" in errors:
            invalid_url_count += 1
        if "invalid_price" in errors:
            invalid_price_count += 1
        if "invalid_rating" in errors:
            invalid_rating_count += 1
        if "unknown_source" in errors:
            unknown_source_count += 1
        if "missing_name" in errors:
            missing_name_count += 1

    # 5. Duplicate check using existing deduplication logic
    _, duplicates = find_duplicates(records)
    duplicate_count = len(duplicates)

    return {
        "total_records": total_records,
        "records_by_source": records_by_source,
        "field_completeness": overall_field_metrics,
        "completeness_by_source": completeness_by_source,
        "validity_summary": {
            "invalid_url_count": invalid_url_count,
            "invalid_price_count": invalid_price_count,
            "invalid_rating_count": invalid_rating_count,
            "unknown_source_count": unknown_source_count,
            "missing_name_count": missing_name_count,
        },
        "uniqueness_summary": {
            "duplicate_count": duplicate_count,
            "is_fully_deduplicated": duplicate_count == 0,
        },
    }
