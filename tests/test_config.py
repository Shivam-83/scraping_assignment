"""Unit tests for config module in config.py."""

import json
from pathlib import Path
import pytest

from config import (
    DEFAULT_CSV_OUTPUT_PATH,
    DEFAULT_LOG_FILE_PATH,
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_REQUEST_TIMEOUT,
    DEFAULT_SUMMARY_REPORT_PATH,
    AppConfig,
    load_config,
    validate_config_data,
)


def test_default_config() -> None:
    config = AppConfig()
    assert config.request_timeout == DEFAULT_REQUEST_TIMEOUT
    assert config.request_delay == DEFAULT_REQUEST_DELAY
    assert config.max_retries == DEFAULT_MAX_RETRIES
    assert config.enable_books_scraper is True
    assert config.enable_quotes_scraper is True
    assert config.csv_output_path == DEFAULT_CSV_OUTPUT_PATH
    assert config.summary_report_path == DEFAULT_SUMMARY_REPORT_PATH
    assert config.log_file_path == DEFAULT_LOG_FILE_PATH


def test_load_config_non_existent_file(tmp_path: Path) -> None:
    non_existent = tmp_path / "missing_config.json"
    config = load_config(non_existent)
    assert config.request_timeout == DEFAULT_REQUEST_TIMEOUT
    assert config.max_retries == DEFAULT_MAX_RETRIES


def test_load_config_valid_custom_file(tmp_path: Path) -> None:
    custom_json = tmp_path / "custom_config.json"
    data = {
        "request_timeout": 15.0,
        "request_delay": 1.2,
        "max_retries": 5,
        "enable_books_scraper": False,
        "enable_quotes_scraper": True,
        "csv_output_path": "custom_output/data.csv",
        "summary_report_path": "custom_output/report.json",
        "log_file_path": "custom_logs/run.log",
    }
    custom_json.write_text(json.dumps(data), encoding="utf-8")

    config = load_config(custom_json)
    assert config.request_timeout == 15.0
    assert config.request_delay == 1.2
    assert config.max_retries == 5
    assert config.enable_books_scraper is False
    assert config.enable_quotes_scraper is True
    assert config.csv_output_path.name == "data.csv"
    assert config.summary_report_path.name == "report.json"
    assert config.log_file_path.name == "run.log"


def test_validate_invalid_timeout() -> None:
    with pytest.raises(ValueError, match="request_timeout"):
        validate_config_data({"request_timeout": 0})

    with pytest.raises(ValueError, match="request_timeout"):
        validate_config_data({"request_timeout": -5.0})

    with pytest.raises(ValueError, match="request_timeout"):
        validate_config_data({"request_timeout": True})

    with pytest.raises(ValueError, match="request_timeout"):
        validate_config_data({"request_timeout": "invalid"})


def test_validate_invalid_delay() -> None:
    with pytest.raises(ValueError, match="request_delay"):
        validate_config_data({"request_delay": -0.1})

    with pytest.raises(ValueError, match="request_delay"):
        validate_config_data({"request_delay": True})


def test_validate_invalid_retries() -> None:
    with pytest.raises(ValueError, match="max_retries"):
        validate_config_data({"max_retries": -1})

    with pytest.raises(ValueError, match="max_retries"):
        validate_config_data({"max_retries": 2.5})  # type: ignore

    with pytest.raises(ValueError, match="max_retries"):
        validate_config_data({"max_retries": True})


def test_validate_invalid_booleans() -> None:
    with pytest.raises(ValueError, match="enable_books_scraper"):
        validate_config_data({"enable_books_scraper": "true"})

    with pytest.raises(ValueError, match="enable_quotes_scraper"):
        validate_config_data({"enable_quotes_scraper": 1})


def test_validate_invalid_paths() -> None:
    with pytest.raises(ValueError, match="csv_output_path"):
        validate_config_data({"csv_output_path": ""})

    with pytest.raises(ValueError, match="summary_report_path"):
        validate_config_data({"summary_report_path": "   "})


def test_load_config_malformed_json(tmp_path: Path) -> None:
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{ this is not valid json }", encoding="utf-8")
    with pytest.raises(ValueError, match="Configuration syntax error"):
        load_config(bad_json)
