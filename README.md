# Web Scraping ETL Pipeline

## 1. Project Overview

A Python-based Extract-Transform-Load (ETL) pipeline that scrapes two public training websites, cleans and validates the collected data, removes duplicates, and consolidates the results into a single CSV dataset with an accompanying JSON summary report and a structured log file.

The entire pipeline runs from a single command (`python main.py`) and produces all required output files automatically.

## 2. Objective

Demonstrate a complete, production-style data pipeline that:

- Extracts structured data from two HTML sources using BeautifulSoup.
- Transforms raw scraped values through cleaning, validation, and deduplication.
- Loads the final consolidated dataset into a CSV file.
- Reports runtime statistics in a machine-readable JSON summary.
- Logs every significant event to both the console and a persistent log file.
- Includes offline unit tests for all transformation logic.

## 3. Data Sources

| Source | URL | Content |
|--------|-----|---------|
| Books to Scrape | https://books.toscrape.com/ | Fictional bookstore catalog with titles, prices, and star ratings |
| Quotes to Scrape | https://quotes.toscrape.com/ | Collection of famous quotes with authors and tags |

Both sites are static HTML designed for scraping practice. They require no authentication, no JavaScript execution, and no API keys.

## 4. Python Version

Developed and tested with **Python 3.11**. Compatible with Python 3.10+.

## 5. Dependencies

All dependencies are listed in `requirements.txt`:

| Package | Minimum Version | Purpose |
|---------|----------------|---------|
| `requests` | ≥ 2.31 | HTTP client with session management and retries |
| `beautifulsoup4` | ≥ 4.12 | HTML parsing |
| `lxml` | ≥ 5.0 | Fast HTML parser backend for BeautifulSoup |
| `pytest` | ≥ 8.0 | Unit test framework |

No additional packages are required. The pipeline does not use Selenium, Playwright, Scrapy, pandas, or any other heavyweight framework.

## 6. Installation and Setup

```bash
# Clone or unzip the project
cd scraping_assignment

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 7. How to Run

### Basic Execution (Default)

```bash
python main.py
```

This runs the complete ETL pipeline across both sources (`Books to Scrape` and `Quotes to Scrape`) using settings loaded from `config.json`.

### Command-Line Arguments (CLI Overrides)

The pipeline supports flexible CLI arguments via Python standard library `argparse`. Command-line arguments take precedence over `config.json` values:

```bash
# Display CLI help and available options
python main.py --help

# Scrape Books to Scrape only
python main.py --source books

# Scrape Quotes to Scrape only
python main.py --source quotes

# Scrape both sources explicitly
python main.py --source all

# Override request delay (e.g. 1.0 second between pages)
python main.py --delay 1.0

# Override request timeout (e.g. 15 seconds)
python main.py --timeout 15

# Direct output CSV and JSON report to a custom directory
python main.py --output custom_results

# Resume interrupted crawl from the last successfully completed page
python main.py --resume

# Discard/reset all stored checkpoint files and start fresh
python main.py --reset-checkpoint

# Combine options: resume Quotes crawl with custom output directory
python main.py --source quotes --resume --output output/quotes_resumed
```

### Unit Tests Only

```bash
pytest
```

Tests run entirely offline — they do not make any HTTP requests.

### Running with Docker (Bonus Feature 5)

The project includes containerization support for isolated, reproducible execution on any machine running Docker without needing a local Python environment.

```bash
# 1. Build the Docker image (uses python:3.12-slim)
docker build -t scraper-pipeline .

# 2. Run the complete pipeline inside the container
docker run --rm scraper-pipeline

# 3. Run with volume mounts to persist output files to your host machine
# Windows PowerShell:
docker run --rm -v "${PWD}/output:/app/output" -v "${PWD}/logs:/app/logs" scraper-pipeline

# Linux / macOS:
docker run --rm -v "$(pwd)/output:/app/output" -v "$(pwd)/logs:/app/logs" scraper-pipeline

# 4. Pass CLI arguments to run specific configurations
docker run --rm scraper-pipeline python main.py --source quotes --delay 1.0
```


## 8. Project Structure

```
scraping_assignment/
├── main.py                          # Pipeline entry point — the only file needed to run
├── config.py                        # Strongly-typed configuration system and validation
├── config.json                      # Configurable settings (timeouts, delays, toggles, paths)
├── Dockerfile                       # Container definition (Python 3.12-slim base, pip install, entrypoint)
├── .dockerignore                    # Excludes venv, pycache, git, logs, output, and checkpoints
├── requirements.txt                 # Python dependencies
├── pytest.ini                       # pytest configuration (sets pythonpath and testpaths)
├── README.md                        # This file
├── AI_USAGE.md                      # AI tool usage disclosure
│
├── scrapers/
│   ├── __init__.py                  # Exports BaseScraper, BooksScraper, QuotesScraper
│   ├── base_scraper.py              # Shared HTTP client: sessions, retries, rate limiting, lxml parsing
│   ├── books_scraper.py             # Books to Scrape: extracts title, price, rating, book URL
│   └── quotes_scraper.py           # Quotes to Scrape: extracts quote text, author, tags, page URL
│
├── processing/
│   ├── __init__.py                  # ScrapedRecord dataclass, RECORD_FIELDS, package-level exports
│   ├── checkpoint.py                # Checkpoint persistence, state recovery, and cache cleanup
│   ├── cleaning.py                  # Pure cleaning functions: text, price, rating, tags, URLs, quotes
│   ├── data_quality.py              # Post-pipeline dataset quality audit and completeness profiling
│   ├── validation.py                # Rule-based record validation returning machine-readable reasons
│   └── deduplication.py             # SHA-256 fingerprinting and duplicate partitioning
│
├── tests/
│   ├── test_checkpoint.py           # Tests for checkpoint save/load, clear, corruption recovery
│   ├── test_cleaning.py             # Tests for all cleaning functions and clean_record
│   ├── test_cli.py                  # Tests for CLI argument parsing, flags, and overrides
│   ├── test_config.py               # Tests for JSON configuration loading, validation, and defaults
│   ├── test_data_quality.py         # Tests for quality report generation, completeness %, defect checks
│   ├── test_validation.py           # Tests for valid records, each rejection reason, immutability
│   └── test_deduplication.py        # Tests for fingerprint equivalence, partitioning, edge cases
│
├── checkpoints/                     # Created automatically by the pipeline
│   ├── books_checkpoint.json        # Saved progress for Books scraper (cleared on completion)
│   └── quotes_checkpoint.json       # Saved progress for Quotes scraper (cleared on completion)
│
├── output/                          # Created automatically by the pipeline
│   ├── final_dataset.csv            # Consolidated dataset (both sources, UTF-8)
│   ├── summary_report.json          # Runtime statistics (actual counts, not hard-coded)
│   └── data_quality_report.json     # Post-pipeline dataset quality and completeness metrics
│
└── logs/                            # Created automatically by the pipeline
    └── scraper.log                  # Timestamped log of the entire pipeline run
```

## 8.1 Configuration System (`config.json` & `config.py`)

All runtime settings are extracted from Python source code into a JSON-based configuration file (`config.json`), parsed and validated through `config.py`.

### Available Settings

| Setting Key | Type | Default | Description & Constraints |
|-------------|------|---------|---------------------------|
| `request_timeout` | `float` | `10.0` | HTTP request timeout in seconds. Must be a positive number (`> 0`). |
| `request_delay` | `float` | `0.5` | Polite delay between consecutive requests in seconds. Must be non-negative (`>= 0`). |
| `max_retries` | `int` | `3` | Maximum HTTP retries on transient errors (429, 500, 502, 503, 504). Must be integer (`>= 0`). |
| `enable_books_scraper` | `bool` | `true` | When `false`, skips scraping Books to Scrape. |
| `enable_quotes_scraper` | `bool` | `true` | When `false`, skips scraping Quotes to Scrape. |
| `csv_output_path` | `string` | `"output/final_dataset.csv"` | Output destination for consolidated CSV. Resolved via `pathlib.Path`. |
| `summary_report_path` | `string` | `"output/summary_report.json"` | Output destination for summary report JSON. Resolved via `pathlib.Path`. |
| `log_file_path` | `string` | `"logs/scraper.log"` | Output destination for log file. Resolved via `pathlib.Path`. |

### Example `config.json`

```json
{
  "request_timeout": 10.0,
  "request_delay": 0.5,
  "max_retries": 3,
  "enable_books_scraper": true,
  "enable_quotes_scraper": true,
  "csv_output_path": "output/final_dataset.csv",
  "summary_report_path": "output/summary_report.json",
  "log_file_path": "logs/scraper.log"
}
```

### Validation & Error Handling

- **Fail-Fast Validation:** If `config.json` contains malformed JSON, invalid data types (e.g., negative timeout, non-integer retries, string booleans), or blank path strings, `load_config()` raises a clear `ValueError` with a descriptive message before any network or processing activity begins.
- **Sensible Defaults:** If `config.json` is missing or keys are omitted, `config.py` supplies production-ready defaults via the `AppConfig` dataclass.
- **Path Resolution:** Relative paths are automatically resolved relative to the project root directory using `pathlib.Path`.

## 8.2 Checkpoint & Resume System (`processing/checkpoint.py`)

The pipeline includes built-in checkpoint and resume support to ensure resilience against network outages, process termination, or machine reboots.

### How It Works

1. **Automatic Directory Management:** The `checkpoints/` directory is created automatically on demand.
2. **Source Isolation:** Books and Quotes maintain separate checkpoints (`books_checkpoint.json` and `quotes_checkpoint.json`). If one source is interrupted, the other remains completely unaffected.
3. **Safe State Persistence:** Checkpoints are updated **only after** each page is successfully fetched, parsed, and its records added to memory.
4. **State Payload:** Each checkpoint file records:
   - `source`: The identifier of the scraper (`Books to Scrape` or `Quotes to Scrape`).
   - `next_url`: The exact pagination URL to scrape on the next iteration.
   - `pages_visited`: The count of pages processed up to that point.
   - `updated_at`: An ISO 8601 UTC timestamp of the last successful page save.
   - `record_count`: Number of raw records collected so far.
   - `records`: The list of raw serialized `ScrapedRecord` objects collected so far.
5. **Natural Termination Cleanup:** Once a scraper processes its last page and encounters no further pagination link, the corresponding checkpoint file is automatically deleted.
6. **Graceful Corruption Recovery:** If a checkpoint file contains malformed JSON or an invalid schema, `load_checkpoint()` logs an error explaining the issue and falls back to starting a fresh crawl from page 1 without crashing the pipeline.
7. **CLI Controls:**
   - Run `python main.py --resume` to detect and continue from saved checkpoints.
   - Run `python main.py --reset-checkpoint` to explicitly purge all saved checkpoints and force a fresh run.
   - When running standard `python main.py` without `--resume`, existing checkpoints are detected and reported in the startup log, but a fresh crawl runs as normal.
8. **Deduplication Safety:** Because all raw records are passed through the pipeline's deterministic SHA-256 deduplication phase, resuming never causes duplicate entries in the final dataset.

## 8.3 Docker Containerization (`Dockerfile` & `.dockerignore`)

The pipeline includes full Docker containerization for self-contained, reproducible deployments:

- **Base Image:** `python:3.12-slim` provides a modern Python 3.12 runtime with a minimal footprint (~150MB).
- **Environment Flags:** Sets `PYTHONDONTWRITEBYTECODE=1` to avoid bytecode clutter and `PYTHONUNBUFFERED=1` to ensure realtime stdout/stderr streaming in container logs.
- **Efficient Layer Caching:** `requirements.txt` is copied and installed prior to copying project source code, ensuring dependency layers are cached across code changes.
- **Clean Image Context:** `.dockerignore` prevents host virtual environments (`venv/`), cached bytecode (`__pycache__/`), version control history (`.git/`), test caches (`.pytest_cache/`), and prior host outputs/logs/checkpoints from bloating the container image.
- **Runtime Directories:** `output/`, `logs/`, and `checkpoints/` directories are ensured inside the image.
- **Default Entrypoint:** `CMD ["python", "main.py"]` executes the full ETL pipeline by default. Host volumes can be mounted to `/app/output` and `/app/logs` to access outputs outside the container.


## 9. Source HTML Structure

### Books to Scrape

Each book is an `<article class="product_pod">` containing:

| Field | Selector | Notes |
|-------|----------|-------|
| Title | `h3 a[title]` | The `title` attribute holds the full un-truncated title |
| Book URL | `h3 a[href]` | Relative URL resolved with `urljoin` against current page |
| Price | `p.price_color` | Text like `£51.77` — currency symbol stripped during cleaning |
| Star rating | `p.star-rating` | CSS class list includes the word rating (e.g., `star-rating Three`) |

**Not extracted:** `category` and `description` are not scraped because the catalog listing pages do not expose them. Extracting them would require visiting each individual book's detail page, which was not implemented. These fields are stored as `None` in the output CSV.

### Quotes to Scrape

Each quote is a `<div class="quote">` containing:

| Field | Selector | Notes |
|-------|----------|-------|
| Quote text | `span.text` | Includes surrounding typographic curly quotes (`\u201c...\u201d`) |
| Author | `small.author` | Plain text |
| Tags | `div.tags a.tag` | Multiple `<a>` elements; joined with `;` during extraction |

**Source URL:** Each quote record stores the page URL where it was found (e.g., `https://quotes.toscrape.com/page/3/`), not an individual quote detail URL.

## 10. Pagination Approach

Both scrapers use identical dynamic pagination logic:

1. Start at the source's root URL.
2. Parse the current page with BeautifulSoup + lxml.
3. Extract all items from the page.
4. Look for `li.next a` — if found, resolve its `href` with `urllib.parse.urljoin` and continue.
5. If no next link exists, stop. This is recorded as natural pagination termination.

**No page counts are hard-coded.** The number of pages and records collected depends entirely on what the website serves at runtime.

## 11. Common Data Model

All records from both sources are stored in a single `ScrapedRecord` dataclass defined in `processing/__init__.py`:

```python
@dataclass
class ScrapedRecord:
    source: str                        # "Books to Scrape" or "Quotes to Scrape"
    source_url: str                    # Absolute URL where the record was found
    name_or_title: str                 # Book title or quote text
    category: Optional[str] = None     # Not populated (see Section 9)
    price: Optional[float|str] = None  # Raw string before cleaning, float after
    rating: Optional[int|str] = None   # Raw word before cleaning, int after
    author: Optional[str] = None       # Quote author (None for books)
    tags: Optional[str] = None         # Semicolon-separated tags (None for books)
    description: Optional[str] = None  # Not populated (see Section 9)
    scraped_at: Optional[str] = None   # ISO 8601 UTC timestamp, auto-generated
```

The CSV column order matches `RECORD_FIELDS`: `source`, `source_url`, `name_or_title`, `category`, `price`, `rating`, `author`, `tags`, `description`, `scraped_at`.

## 12. Cleaning Approach

Cleaning is implemented as small, pure, independently testable functions in `processing/cleaning.py`:

| Function | Behavior |
|----------|----------|
| `clean_text(value)` | Replaces non-breaking spaces (`\xa0`), collapses all whitespace, strips leading/trailing spaces. Returns `None` for empty results. |
| `strip_quotes(value)` | Removes surrounding typographic curly quotes (`\u201c \u201d \u2018 \u2019`), straight quotes (`" '`), and guillemets (`\u00ab \u00bb`). |
| `clean_price(value)` | Extracts a numeric value from strings like `"£51.77"` or `"Â£1,234.56"` using regex. Strips currency symbols and commas. Returns a `float` rounded to 2 decimal places, or `None`. |
| `clean_rating(value)` | Maps word strings to integers: One→1, Two→2, Three→3, Four→4, Five→5. Accepts case-insensitive input. Returns `None` for unmappable values. |
| `clean_tags(value)` | Splits on `;` or `,`, cleans each tag, lowercases, deduplicates, sorts alphabetically, and re-joins with `;`. |
| `normalize_url(value)` | Validates that a URL uses `http://` or `https://` scheme and has a network location. Returns `None` for invalid URLs. |

The `clean_record()` function applies source-specific rules:

- **Books:** Cleans `name_or_title`, `price`, `rating`, and `source_url`. Sets `author` and `tags` to `None`.
- **Quotes:** Cleans `name_or_title` then strips curly quotes, cleans `author`, normalizes `tags`. Sets `price` and `rating` to `None`.

## 13. Validation Approach

Validation is implemented in `processing/validation.py` as `validate_record(record)`. It returns a list of machine-readable rejection reason strings. An empty list means the record is valid.

| Rule | Condition | Rejection Reason |
|------|-----------|-----------------|
| Source | Must be `"Books to Scrape"` or `"Quotes to Scrape"` | `unknown_source` |
| Name/title | Must not be empty or whitespace-only | `missing_name` |
| Source URL | Must start with `http://` or `https://` | `invalid_url` |
| Price (if present) | Must be numeric and ≥ 0 | `invalid_price` |
| Rating (if present) | Must be an integer between 1 and 5 inclusive | `invalid_rating` |

Validation is read-only — it never modifies records. A single record can accumulate multiple rejection reasons. Boolean values are explicitly rejected for `price` and `rating` to prevent `True`/`False` from passing numeric checks.

## 14. Deduplication Approach

Deduplication is implemented in `processing/deduplication.py`.

### Fingerprint Construction

A deterministic SHA-256 fingerprint is computed for each record. Before hashing, all values are:

1. Lowercased
2. Stripped of all punctuation (regex: `[^\w\s]`)
3. Collapsed to single spaces and trimmed

**Source-specific fingerprint rules:**

| Source | Fingerprint Payload |
|--------|-------------------|
| Books to Scrape | `normalized_source \| normalized_title` |
| Quotes to Scrape | `normalized_source \| normalized_author \| first_50_normalized_chars_of_quote` |

The 50-character prefix for quotes ensures that two quotes with different endings but the same opening text and author are treated as the same quote.

### Examples treated as equivalent (same fingerprint)

For Books with the same source:
- `"Example Book Title"`
- `"  Example   Book  Title  "`
- `"EXAMPLE BOOK TITLE"`
- `"Example: Book Title!"`

### Partitioning

`find_duplicates(records)` returns two lists:
- **unique_records** — first occurrence of each fingerprint (preserves insertion order)
- **duplicate_records** — all subsequent records with an already-seen fingerprint

## 15. Error Handling and Retries

### HTTP retries

`BaseScraper` configures `requests.Session` with `urllib3.util.Retry`:
- **Max retries:** 3
- **Backoff factor:** 1.0 (exponential: 1s, 2s, 4s)
- **Retry status codes:** 429, 500, 502, 503, 504
- **Retry methods:** GET, HEAD only

### Rate limiting

A configurable delay (default: 0.5 seconds) is enforced between consecutive HTTP requests to avoid overloading target servers.

### Per-record error handling

If a single HTML element fails to parse (e.g., missing `<h3 a>` tag), the error is logged as a WARNING and that record is skipped. The scraper continues processing remaining items on the page.

### Per-source isolation

Each scraper runs inside its own `try/except` block in `main.py`. If one scraper fails entirely (e.g., the website is unreachable), the other scraper still runs, and the pipeline continues with whatever data was collected.

## 16. Logging

Logging is configured in `main.py` via `setup_logging()`. All events are written to two destinations simultaneously:

| Destination | Format |
|-------------|--------|
| Console (`stdout`) | Timestamped, level-tagged, logger-named |
| `logs/scraper.log` | Same format, UTF-8 encoded, append mode |

### Log levels used

| Level | Events |
|-------|--------|
| `INFO` | Each page visited, records extracted per page, pipeline phase transitions, completion |
| `WARNING` | Rejected records (with rejection reasons), malformed individual elements |
| `ERROR` | Failed HTTP requests (after retries exhausted), unrecoverable scraper exceptions |
| `DEBUG` | Rate-limit sleeps, HTTP response codes |

Log format: `2026-10-06 08:01:45 [INFO] ETLPipeline: Starting Python Web Scraping ETL Pipeline`

Logs do not contain raw HTML content or any sensitive information.

## 17. Output Files

### `output/final_dataset.csv`

- UTF-8 encoded with a header row.
- Contains deduplicated, validated records from both sources.
- Columns: `source`, `source_url`, `name_or_title`, `category`, `price`, `rating`, `author`, `tags`, `description`, `scraped_at`.
- `None` values are written as empty strings.
- Float prices are formatted to 2 decimal places.
- The actual number of rows depends on how many records the websites serve at runtime.

### `output/summary_report.json`

- UTF-8 encoded, indented with 4 spaces.
- All values are computed from the actual pipeline run — nothing is hard-coded.

### `output/data_quality_report.json`

- UTF-8 encoded JSON report profiling post-pipeline dataset quality.
- Measures total volume, source distribution, field-level missing counts, completeness percentages (overall and source-segmented), and confirms validity and uniqueness.

### `logs/scraper.log`

- Append-mode log file, UTF-8 encoded.
- Contains timestamped entries for every pipeline phase.

All output directories (`output/`, `logs/`) are created automatically by the pipeline if they do not exist.

## 18. Summary Report Metrics

The JSON summary report (`output/summary_report.json`) contains the following fields:

```json
{
    "collected_per_source": {
        "Books to Scrape": <int>,
        "Quotes to Scrape": <int>
    },
    "cleaned_per_source": {
        "Books to Scrape": <int>,
        "Quotes to Scrape": <int>
    },
    "rejected_by_reason": {},
    "duplicates_detected": <int>,
    "final_record_count": <int>,
    "start_time": "<ISO 8601 UTC>",
    "end_time": "<ISO 8601 UTC>",
    "duration_seconds": <float>
}
```

Every value is populated dynamically from the actual pipeline execution. The `final_record_count` reflects the exact number of rows written to the CSV.

## 18.1 Data Quality Report Metrics (`output/data_quality_report.json`)

The Data Quality Report evaluates the final, standardized dataset after cleaning, validation, and deduplication have finished.

### What the Quality Report Measures

1. **Volume & Distribution:** Total rows and record count segmented by source (`Books to Scrape` vs. `Quotes to Scrape`).
2. **Field Completeness:** For each schema field, records the number of populated entries, missing entries, and completeness percentage (`(populated / total) * 100`).
3. **Source-Segmented Completeness:** Breaks down field completeness per source (e.g. shows that `price` is 100% complete for books and expectedly 0% for quotes; `author` is 100% complete for quotes).
4. **Post-Pipeline Validity Verification:** Uses the existing validation rules to verify that zero invalid URLs, invalid prices, invalid ratings, or missing titles slipped into the final dataset.
5. **Post-Pipeline Uniqueness Verification:** Runs deduplication fingerprinting over the final records to confirm that duplicate count is 0 (`is_fully_deduplicated: true`).

### Example Structure

> [!NOTE]
> Below is an illustrative example of the JSON schema and structure. Actual values are calculated dynamically from runtime data.

```json
{
    "total_records": 1099,
    "records_by_source": {
        "Books to Scrape": 1000,
        "Quotes to Scrape": 99
    },
    "field_completeness": {
        "source": { "populated_count": 1099, "missing_count": 0, "completeness_pct": 100.0 },
        "source_url": { "populated_count": 1099, "missing_count": 0, "completeness_pct": 100.0 },
        "name_or_title": { "populated_count": 1099, "missing_count": 0, "completeness_pct": 100.0 },
        "price": { "populated_count": 1000, "missing_count": 99, "completeness_pct": 91.0 },
        "rating": { "populated_count": 1000, "missing_count": 99, "completeness_pct": 91.0 },
        "author": { "populated_count": 99, "missing_count": 1000, "completeness_pct": 9.0 },
        "tags": { "populated_count": 96, "missing_count": 1003, "completeness_pct": 8.73 },
        "category": { "populated_count": 0, "missing_count": 1099, "completeness_pct": 0.0 },
        "description": { "populated_count": 0, "missing_count": 1099, "completeness_pct": 0.0 },
        "scraped_at": { "populated_count": 1099, "missing_count": 0, "completeness_pct": 100.0 }
    },
    "completeness_by_source": {
        "Books to Scrape": {
            "price": { "populated_count": 1000, "missing_count": 0, "completeness_pct": 100.0 },
            "rating": { "populated_count": 1000, "missing_count": 0, "completeness_pct": 100.0 }
        },
        "Quotes to Scrape": {
            "author": { "populated_count": 99, "missing_count": 0, "completeness_pct": 100.0 },
            "tags": { "populated_count": 96, "missing_count": 3, "completeness_pct": 96.97 }
        }
    },
    "validity_summary": {
        "invalid_url_count": 0,
        "invalid_price_count": 0,
        "invalid_rating_count": 0,
        "unknown_source_count": 0,
        "missing_name_count": 0
    },
    "uniqueness_summary": {
        "duplicate_count": 0,
        "is_fully_deduplicated": true
    }
}
```

## 19. Assumptions

1. **Static HTML:** Both target websites serve static HTML that does not require JavaScript rendering.
2. **Stable selectors:** The HTML structure (CSS classes and element hierarchy) used for parsing will remain consistent across runs.
3. **Catalog-only scraping:** Book data is extracted from listing/catalog pages only. Individual book detail pages are not visited, so `category` and `description` are not available.
4. **No authentication:** Neither site requires login, cookies, or API tokens.
5. **UTF-8 throughout:** All input HTML and output files use UTF-8 encoding.
6. **Reasonable volume:** The websites contain a manageable number of pages that can be scraped within a few minutes with polite rate limiting.

## 20. Known Limitations

1. **No category or description for books.** These fields exist on individual book detail pages but are not scraped because the implementation only processes catalog listing pages. Adding this would require an additional HTTP request per book (up to ~1000 extra requests).
2. **Full crawl by default with checkpoint resume:** Standard runs scrape all pages from scratch. However, interrupted runs can be resumed from the exact next page using `--resume`, preserving previously collected raw records.
3. **Tags may be empty for some quotes.** A small number of quotes on the source website genuinely have no tags. These are preserved as empty values, not treated as errors.
4. **Quote source URL is the page URL,** not a unique permalink per quote. The website does not provide individual quote detail pages on the main listing.
5. **No concurrent scraping.** Both sources are scraped sequentially. Parallelism was not implemented.
6. **Rate limiting is time-based,** not adaptive. The fixed 0.5-second delay does not adjust based on server response times.
7. **Duplicate detection is approximate for quotes.** Using only the first 50 normalized characters means two genuinely different quotes that happen to share the same 50-character prefix and author would be treated as duplicates. This is a deliberate trade-off for robustness.

## 21. Testing Instructions

```bash
# Activate your virtual environment first
pytest
```

### Test coverage

| Test File | Module Under Test | What It Tests |
|-----------|-------------------|---------------|
| `tests/test_checkpoint.py` | `processing/checkpoint.py` | Checkpoint directory auto-creation, isolated source checkpoints, save and load round-trip, next URL / page tracking, natural clearing, corrupted JSON recovery, and invalid schema detection |
| `tests/test_cleaning.py` | `processing/cleaning.py` | Whitespace normalization, non-breaking spaces, curly quote stripping, price extraction (currency symbols, commas), rating word-to-int mapping, tag cleaning/sorting, URL validation, source-specific `clean_record` logic |
| `tests/test_cli.py` | `main.py` | CLI argument parsing, `--source` filtering (books, quotes, all), `--delay` and `--timeout` overrides, `--output` directory redirection, bounds validation and error handling |
| `tests/test_config.py` | `config.py` | JSON configuration loading, default values fallback, custom setting overrides, type validation (timeout, delay, retries, booleans, paths), fail-fast errors on invalid data, path resolution |
| `tests/test_data_quality.py` | `processing/data_quality.py` | Quality report generation on empty datasets, clean mixed datasets, field completeness percentages, source-level breakdowns, defect counts, duplicate detection |
| `tests/test_validation.py` | `processing/validation.py` | Valid book and quote records, each rejection reason (`unknown_source`, `missing_name`, `invalid_url`, `invalid_price`, `invalid_rating`), multiple simultaneous errors, boolean edge cases, record immutability during validation |
| `tests/test_deduplication.py` | `processing/deduplication.py` | Case-insensitive matching, whitespace normalization, punctuation removal, identical records, quote fingerprint with author + 50-char prefix, cross-source fingerprint isolation, mixed-source partitioning, no-duplicate input |

All tests are fully offline — no HTTP requests are made. Tests use `ScrapedRecord` instances and plain dictionaries directly.

## 22. AI Usage Summary

AI tools were used to assist with:

- Project scaffolding and directory structure.
- Implementation of scraper classes, cleaning functions, validation rules, and deduplication logic.
- Unit test creation covering normal, edge, and error cases.
- Pipeline orchestration in `main.py`.
- Documentation and README authoring.

All generated code was reviewed, tested, and verified against the live websites. Detailed phase-by-phase AI usage is documented in `AI_USAGE.md`.
