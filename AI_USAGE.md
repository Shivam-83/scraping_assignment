# AI Usage Disclosure

## 1. AI Tools Used

| Tool | Role |
|------|------|
| ChatGPT (OpenAI) | Assignment document understanding, phase-wise breakdown, prompt creation |
| Google Gemini (via Antigravity IDE) | Code generation, debugging, documentation, test writing |

Two AI tools were used in a complementary workflow. ChatGPT was used first to carefully read and understand the assignment requirements document, break the work into numbered phases, and craft detailed implementation prompts with explicit constraints and acceptance criteria. These prompts were then given to Google Gemini within the Antigravity IDE, which operated as an interactive pair-programming partner with access to the filesystem, terminal, and browser for implementation and verification.

## 2. What AI Was Used For

AI assistance was used across every phase of this project:

- **Assignment understanding (ChatGPT):** Reading and interpreting the assignment requirements document, identifying deliverables, constraints, and edge cases.
- **Phase planning (ChatGPT):** Breaking the full assignment into numbered implementation phases (Phases 1–13), each with a clear scope and explicit acceptance criteria.
- **Prompt engineering (ChatGPT):** Writing detailed, constraint-driven prompts for each phase — specifying what to build, what not to hard-code, which selectors to use, and how to handle errors.
- **Project scaffolding (Gemini):** Directory structure, `requirements.txt`, `pytest.ini`, package `__init__.py` files.
- **HTML inspection (Gemini):** Fetching live pages from both target websites, identifying CSS selectors and pagination structure.
- **Implementation (Gemini):** All Python modules — `BaseScraper`, `BooksScraper`, `QuotesScraper`, cleaning functions, validation, deduplication, and the `main.py` pipeline orchestrator.
- **Unit tests (Gemini):** All test files (`test_cleaning.py`, `test_validation.py`, `test_deduplication.py`).
- **Documentation (Gemini):** `README.md` and this `AI_USAGE.md`.
- **Verification (Gemini):** A data-quality verification script was used to validate the final CSV output against 13 quality checks.

## 3. Representative Prompts

The assignment was broken into phases using ChatGPT. Each phase produced a detailed prompt that was then given to Gemini for implementation. The following are representative:

**Phase 1 — Project setup (ChatGPT → Gemini):**
> "Read the assignment requirements carefully and implement ONLY what is required. Build a Python ETL pipeline that scrapes Books to Scrape and Quotes to Scrape, cleans the data, validates records, detects and removes duplicates, consolidates both sources into one CSV, generates a JSON summary report using actual runtime statistics, generates a log file, and includes unit tests. Create the project structure with all necessary directories and skeleton files. Do not proceed to implementation in this phase."

**Phase 5 — Books scraper (ChatGPT → Gemini):**
> "Implement Phase 5: Books to Scrape scraper only. Start from https://books.toscrape.com/. Use BeautifulSoup with lxml. Extract every book from each page. Extract: title, book URL, price, rating. Store raw values before cleaning. Set source = 'Books to Scrape'. Follow li.next > a dynamically. Use urllib.parse.urljoin for relative URLs. Never hard-code page count. Continue until there is no next link. If one record fails to parse, log it and continue. If a page request fails after retries, log the error and stop this source without crashing the whole program."

**Phase 7 — Data cleaning (ChatGPT → Gemini):**
> "Implement Phase 7: data cleaning. Create small, pure, independently testable functions: clean_text, strip_quotes, clean_price, clean_rating, clean_tags, normalize_url. clean_price: convert values such as '£51.77' to numeric 51.77. clean_rating: map One→1, Two→2, Three→3, Four→4, Five→5. clean_tags: clean whitespace, normalize to lowercase, sort tags, join using semicolon."

**Phase 9 — Deduplication (ChatGPT → Gemini):**
> "Implement Phase 9: duplicate detection. For Books: source + title/name_or_title. For Quotes: source + author + first 50 characters of quote/name_or_title. Before hashing: lowercase, remove punctuation, collapse whitespace, normalize formatting. Use SHA-256. The logic must treat 'Example Book Title', '  Example Book Title  ', and 'EXAMPLE BOOK TITLE' as equivalent for the same source."

**Phase 10 — Pipeline (ChatGPT → Gemini):**
> "Implement Phase 10: complete main.py pipeline. main.py must be the ONLY file required to run the complete application. Never hard-code total records, rejected counts, duplicate counts, final record count, or duration. All statistics must come from the actual pipeline run. For every rejected record: count rejection reasons, log a WARNING, do not crash."

**Data-quality verification (ChatGPT → Gemini):**
> "Perform a data-quality verification of the generated final_dataset.csv. Check file exists, UTF-8 readable, expected columns, both sources present, valid URLs, populated fields, no duplicate fingerprints, row count matches summary. Do not modify the dataset. Report all problems found."

All prompts were crafted in ChatGPT with explicit requirements, constraints, and acceptance criteria, then executed in Gemini one phase at a time to keep changes reviewable.

## 4. Which Parts Were AI-Assisted

| Component | File(s) | AI-Assisted |
|-----------|---------|-------------|
| Project structure | All directories, `requirements.txt`, `pytest.ini` | Yes |
| Configuration system | `config.py`, `config.json` | Yes |
| Base HTTP client | `scrapers/base_scraper.py` | Yes |
| Books scraper | `scrapers/books_scraper.py` | Yes |
| Quotes scraper | `scrapers/quotes_scraper.py` | Yes |
| Data model | `processing/__init__.py` | Yes |
| Cleaning functions | `processing/cleaning.py` | Yes |
| Validation rules | `processing/validation.py` | Yes |
| Deduplication logic | `processing/deduplication.py` | Yes |
| Data quality audit | `processing/data_quality.py` | Yes |
| Checkpoint & resume system | `processing/checkpoint.py` | Yes |
| Docker containerization | `Dockerfile`, `.dockerignore` | Yes |
| Pipeline orchestration | `main.py` | Yes |
| Unit tests | `tests/test_cleaning.py`, `tests/test_cli.py`, `tests/test_config.py`, `tests/test_data_quality.py`, `tests/test_validation.py`, `tests/test_deduplication.py`, `tests/test_checkpoint.py` | Yes |
| README | `README.md` | Yes |
| AI disclosure | `AI_USAGE.md` | Yes |

All code in this project was generated with AI assistance.

## 5. Changes Made After Reviewing AI Output

During the iterative development process, the following corrections and refinements were applied after reviewing AI-generated code:

- **Windows console encoding:** The initial verification script failed on Windows due to Unicode box-drawing characters. A `sys.stdout` wrapper with `utf-8` encoding was added.
- **Hard-coded statistics removal:** Early versions of the summary report writer were reviewed to ensure no placeholder values (e.g., `1000`, `100`, `1100`) were baked into the code. All metrics were traced back to runtime-computed variables.
- **Boolean edge cases in validation:** The validation function was updated to explicitly reject Python `bool` values for `price` and `rating` fields, since `isinstance(True, int)` returns `True` in Python.
- **Book detail page decision:** The initial plan considered scraping individual book detail pages for `category` and `description`. This was scoped out — the implementation only processes catalog listing pages, and this design decision is documented in the README.
- **Log file mode:** The log file handler was set to append mode (`"a"`) rather than write mode (`"w"`) so that successive runs preserve history.
- **Windows atomic file renaming:** Checkpoint saving initially used temporary file renaming (`os.replace`), which can raise `[WinError 5] Access is denied` on Windows if background search indexing or antivirus holds an open file handle. Checkpoint writes were updated to write directly with defensive error handling to prevent filesystem locks from interrupting the scraping loop.

## 6. Incorrect or Incomplete Suggestions Discovered

- **UTF-8 console output:** The AI did not initially account for Windows `cp1252` console encoding limitations when using Unicode characters in print output. This caused a `UnicodeEncodeError` that required a targeted fix.
- **Scraper `__init__.py` imports:** The initial empty `__init__.py` files required manual iteration to establish the correct import structure (circular import avoidance between `processing/__init__.py` and `processing/cleaning.py`).
- **Duplicate count assumption:** The websites themselves were not assumed to contain duplicates. During testing, one duplicate book was detected across the 1000-book catalog — this was a genuine duplicate on the live site, not a bug in the scraper.

## 7. How the Final Implementation Was Tested and Verified

### Unit tests

All processing logic was tested with `pytest`:
- **54 tests** across 7 test files, all passing.
- Tests are fully offline — no HTTP requests.
- Coverage includes normal cases, edge cases (empty values, booleans, whitespace-only strings), deliberate duplicates, configuration validation, CLI argument handling, data quality metrics, and checkpoint serialization / resume state.

```
tests/test_checkpoint.py     —  5 tests (save/load, next URL, clean wipe, corruption fallback, schema validation)
tests/test_cleaning.py       — 11 tests (whitespace, prices, ratings, tags, URLs, quote stripping)
tests/test_cli.py            — 10 tests (source filtering, delays/timeouts, output dirs, resume flags, bounds validation)
tests/test_config.py         —  9 tests (defaults, JSON parsing, validation, path resolution, syntax errors)
tests/test_data_quality.py   —  4 tests (completeness %, source breakdown, defect detection, duplicate check)
tests/test_validation.py     —  9 tests (valid records, each rejection reason, multiple errors, immutability)
tests/test_deduplication.py  —  6 tests (case/whitespace/punctuation equivalence, partitioning, cross-source)
```

### End-to-end pipeline execution

The full pipeline was run against the live websites via `python main.py`. The output was verified:

- Both scrapers completed with natural pagination termination.
- `output/final_dataset.csv` was produced with the correct column structure and UTF-8 encoding.
- `output/summary_report.json` was produced with all metrics computed from actual runtime data.
- `logs/scraper.log` contained timestamped entries for every page visit and pipeline phase.

### Data-quality verification

A separate read-only verification script checked the final CSV against 13 quality criteria:

1. File exists and is UTF-8 readable.
2. All 10 expected columns present.
3. Both sources appear in the dataset.
4. All `source_url` values are valid HTTP/HTTPS URLs.
5. All `name_or_title` values are populated.
6. All book prices are numeric and non-negative.
7. All book ratings are integers between 1 and 5.
8. All quote authors are populated.
9. All populated quote tags use semicolon-separated format.
10. All rows have `scraped_at` timestamps in ISO 8601 format.
11. No duplicate fingerprints remain in the final dataset.
12. The CSV row count matches the `final_record_count` in `summary_report.json`.

**Result:** All 13 checks passed. One non-blocking observation: 3 of 100 quotes have legitimately empty tags on the source website.

### Cross-validation

The mathematical relationship `collected - rejected - duplicates = final_count` was verified against the summary report to confirm internal consistency of all pipeline metrics.

---

All code was reviewed, tested against live websites, and verified for correctness before submission.
