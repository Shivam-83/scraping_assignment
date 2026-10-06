"""Configuration module for the web scraping ETL pipeline."""

from dataclasses import dataclass
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

# Sensible default values
DEFAULT_REQUEST_TIMEOUT: float = 10.0
DEFAULT_REQUEST_DELAY: float = 0.5
DEFAULT_MAX_RETRIES: int = 3
DEFAULT_ENABLE_BOOKS_SCRAPER: bool = True
DEFAULT_ENABLE_QUOTES_SCRAPER: bool = True
DEFAULT_CSV_OUTPUT_PATH: Path = BASE_DIR / "output" / "final_dataset.csv"
DEFAULT_SUMMARY_REPORT_PATH: Path = BASE_DIR / "output" / "summary_report.json"
DEFAULT_DATA_QUALITY_REPORT_PATH: Path = BASE_DIR / "output" / "data_quality_report.json"
DEFAULT_LOG_FILE_PATH: Path = BASE_DIR / "logs" / "scraper.log"


@dataclass
class AppConfig:
    """Strongly-typed application configuration with path resolution."""

    request_timeout: float = DEFAULT_REQUEST_TIMEOUT
    request_delay: float = DEFAULT_REQUEST_DELAY
    max_retries: int = DEFAULT_MAX_RETRIES
    enable_books_scraper: bool = DEFAULT_ENABLE_BOOKS_SCRAPER
    enable_quotes_scraper: bool = DEFAULT_ENABLE_QUOTES_SCRAPER
    csv_output_path: Path = DEFAULT_CSV_OUTPUT_PATH
    summary_report_path: Path = DEFAULT_SUMMARY_REPORT_PATH
    data_quality_report_path: Path = DEFAULT_DATA_QUALITY_REPORT_PATH
    log_file_path: Path = DEFAULT_LOG_FILE_PATH
    resume: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary with string path representations."""
        return {
            "request_timeout": self.request_timeout,
            "request_delay": self.request_delay,
            "max_retries": self.max_retries,
            "enable_books_scraper": self.enable_books_scraper,
            "enable_quotes_scraper": self.enable_quotes_scraper,
            "csv_output_path": str(self.csv_output_path),
            "summary_report_path": str(self.summary_report_path),
            "data_quality_report_path": str(self.data_quality_report_path),
            "log_file_path": str(self.log_file_path),
            "resume": self.resume,
        }


def _resolve_path(raw_path: Union[str, Path], base_dir: Path = BASE_DIR) -> Path:
    """Resolve a path against base_dir if it is relative."""
    p = Path(raw_path)
    if not p.is_absolute():
        return (base_dir / p).resolve()
    return p.resolve()


def validate_config_data(data: Dict[str, Any]) -> None:
    """Validate configuration dictionary keys and types.

    Raises:
        ValueError: If any configuration value is invalid with a clear error description.
    """
    if not isinstance(data, dict):
        raise ValueError(
            f"Configuration root must be a JSON object (dictionary), got {type(data).__name__}"
        )

    # Validate request_timeout: positive number
    if "request_timeout" in data:
        val = data["request_timeout"]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or val <= 0:
            raise ValueError(
                f"Invalid configuration 'request_timeout': must be a positive number (> 0), got {val!r}"
            )

    # Validate request_delay: non-negative number
    if "request_delay" in data:
        val = data["request_delay"]
        if isinstance(val, bool) or not isinstance(val, (int, float)) or val < 0:
            raise ValueError(
                f"Invalid configuration 'request_delay': must be a non-negative number (>= 0), got {val!r}"
            )

    # Validate max_retries: non-negative integer
    if "max_retries" in data:
        val = data["max_retries"]
        if isinstance(val, bool) or not isinstance(val, int) or val < 0:
            raise ValueError(
                f"Invalid configuration 'max_retries': must be a non-negative integer (>= 0), got {val!r}"
            )

    # Validate enable_books_scraper: boolean
    if "enable_books_scraper" in data:
        val = data["enable_books_scraper"]
        if not isinstance(val, bool):
            raise ValueError(
                f"Invalid configuration 'enable_books_scraper': must be a boolean (true/false), got {val!r}"
            )

    # Validate enable_quotes_scraper: boolean
    if "enable_quotes_scraper" in data:
        val = data["enable_quotes_scraper"]
        if not isinstance(val, bool):
            raise ValueError(
                f"Invalid configuration 'enable_quotes_scraper': must be a boolean (true/false), got {val!r}"
            )

    # Validate file path settings: non-empty strings
    path_keys = (
        "csv_output_path",
        "summary_report_path",
        "data_quality_report_path",
        "log_file_path",
    )
    for key in path_keys:
        if key in data:
            val = data[key]
            if not isinstance(val, str) or not val.strip():
                raise ValueError(
                    f"Invalid configuration '{key}': must be a non-empty string path, got {val!r}"
                )


def load_config(config_path: Optional[Union[str, Path]] = None) -> AppConfig:
    """Load, validate, and parse configuration from a JSON file.

    If the specified or default file does not exist, default settings are returned.
    If the file exists and contains invalid settings, raises ValueError with a clear message.

    Args:
        config_path: Optional explicit path to JSON config file.

    Returns:
        AppConfig: Validated application configuration instance.

    Raises:
        ValueError: On JSON parsing error or invalid configuration value.
    """
    target_path = Path(config_path) if config_path else BASE_DIR / "config.json"

    if not target_path.exists():
        logger.info("Config file '%s' not found. Using default settings.", target_path)
        return AppConfig()

    try:
        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Configuration syntax error in '{target_path}': {exc}"
        ) from exc
    except Exception as exc:
        raise ValueError(
            f"Failed to read configuration file '{target_path}': {exc}"
        ) from exc

    validate_config_data(data)

    csv_path = _resolve_path(data.get("csv_output_path", DEFAULT_CSV_OUTPUT_PATH))
    summary_path = _resolve_path(data.get("summary_report_path", DEFAULT_SUMMARY_REPORT_PATH))
    quality_path = _resolve_path(
        data.get("data_quality_report_path", DEFAULT_DATA_QUALITY_REPORT_PATH)
    )
    log_path = _resolve_path(data.get("log_file_path", DEFAULT_LOG_FILE_PATH))

    return AppConfig(
        request_timeout=float(data.get("request_timeout", DEFAULT_REQUEST_TIMEOUT)),
        request_delay=float(data.get("request_delay", DEFAULT_REQUEST_DELAY)),
        max_retries=int(data.get("max_retries", DEFAULT_MAX_RETRIES)),
        enable_books_scraper=bool(data.get("enable_books_scraper", DEFAULT_ENABLE_BOOKS_SCRAPER)),
        enable_quotes_scraper=bool(data.get("enable_quotes_scraper", DEFAULT_ENABLE_QUOTES_SCRAPER)),
        csv_output_path=csv_path,
        summary_report_path=summary_path,
        data_quality_report_path=quality_path,
        log_file_path=log_path,
    )
