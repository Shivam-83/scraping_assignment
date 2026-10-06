"""Unit tests for CLI argument parsing in main.py."""

from pathlib import Path
import pytest

from main import build_cli_parser, resolve_config_from_args


def test_cli_default_args() -> None:
    parser = build_cli_parser()
    args = parser.parse_args([])
    config = resolve_config_from_args(args)

    assert args.source == "all"
    assert config.enable_books_scraper is True
    assert config.enable_quotes_scraper is True


def test_cli_source_books_only() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--source", "books"])
    config = resolve_config_from_args(args)

    assert config.enable_books_scraper is True
    assert config.enable_quotes_scraper is False


def test_cli_source_quotes_only() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--source", "quotes"])
    config = resolve_config_from_args(args)

    assert config.enable_books_scraper is False
    assert config.enable_quotes_scraper is True


def test_cli_overrides_delay_and_timeout() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--delay", "1.5", "--timeout", "25.0"])
    config = resolve_config_from_args(args)

    assert config.request_delay == 1.5
    assert config.request_timeout == 25.0


def test_cli_overrides_output_dir() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--output", "custom_results"])
    config = resolve_config_from_args(args)

    assert config.csv_output_path.parent.name == "custom_results"
    assert config.csv_output_path.name == "final_dataset.csv"
    assert config.summary_report_path.parent.name == "custom_results"
    assert config.summary_report_path.name == "summary_report.json"


def test_cli_invalid_delay_raises_error() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--delay", "-0.5"])
    with pytest.raises(ValueError, match="--delay must be non-negative"):
        resolve_config_from_args(args)


def test_cli_invalid_timeout_raises_error() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--timeout", "0"])
    with pytest.raises(ValueError, match="--timeout must be positive"):
        resolve_config_from_args(args)


def test_cli_unknown_source_rejected() -> None:
    parser = build_cli_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--source", "unknown"])


def test_cli_resume_flag() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--resume"])
    config = resolve_config_from_args(args)
    assert config.resume is True


def test_cli_reset_checkpoint_flag() -> None:
    parser = build_cli_parser()
    args = parser.parse_args(["--reset-checkpoint"])
    config = resolve_config_from_args(args)
    assert args.reset_checkpoint is True
