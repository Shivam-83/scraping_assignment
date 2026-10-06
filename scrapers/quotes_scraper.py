"""Scraper implementation for Quotes to Scrape."""

import logging
from typing import List, Optional
from urllib.parse import urljoin

from bs4 import Tag
import requests

from config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_REQUEST_TIMEOUT,
)
from processing import ScrapedRecord
from scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

DEFAULT_QUOTES_URL = "https://quotes.toscrape.com/"


from processing.checkpoint import (
    clear_checkpoint,
    has_checkpoint,
    load_checkpoint,
    save_checkpoint,
)

SOURCE_NAME = "Quotes to Scrape"


class QuotesScraper(BaseScraper):
    """Scrapes quote records from Quotes to Scrape via dynamic pagination."""

    def __init__(
        self,
        base_url: str = DEFAULT_QUOTES_URL,
        delay: float = DEFAULT_REQUEST_DELAY,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: Optional[str] = None,
        resume: bool = False,
    ) -> None:
        super().__init__(
            base_url=base_url,
            delay=delay,
            timeout=timeout,
            max_retries=max_retries,
            user_agent=user_agent,
        )
        self.resume = resume
        self.pages_visited: int = 0
        self.stopped_naturally: bool = False

    def _parse_quote_item(self, quote_tag: Tag, current_url: str) -> Optional[ScrapedRecord]:
        """Extract raw quote fields from a div.quote container."""
        # 1. Quote text
        text_el = quote_tag.select_one("span.text")
        raw_text = text_el.get_text() if text_el else None
        if not raw_text:
            logger.warning("Missing or empty quote text on page %s", current_url)

        # 2. Author
        author_el = quote_tag.select_one("small.author")
        raw_author = author_el.get_text(strip=True) if author_el else None

        # 3. Tags (semicolon-separated raw tag texts)
        tag_elements = quote_tag.select("div.tags a.tag")
        raw_tags = ";".join(t.get_text(strip=True) for t in tag_elements) if tag_elements else None

        return ScrapedRecord(
            source=SOURCE_NAME,
            source_url=current_url,
            name_or_title=raw_text or "",
            author=raw_author,
            tags=raw_tags,
            category=None,
            price=None,
            rating=None,
            description=None,
        )

    def scrape(self) -> List[ScrapedRecord]:
        """Execute full pagination crawl across Quotes to Scrape.

        Returns:
            List[ScrapedRecord]: Extracted raw quote records.
        """
        records: List[ScrapedRecord] = []
        current_url: Optional[str] = self.base_url
        self.pages_visited = 0
        self.stopped_naturally = False

        # Attempt to resume from checkpoint if requested
        if self.resume and has_checkpoint(SOURCE_NAME):
            try:
                ckpt = load_checkpoint(SOURCE_NAME)
                if ckpt and ckpt.get("next_url"):
                    current_url = ckpt["next_url"]
                    self.pages_visited = ckpt.get("pages_visited", 0)
                    records = ckpt.get("records", [])
                    logger.info(
                        "Resuming %s from checkpoint at page %d, next URL: %s (%d records restored).",
                        SOURCE_NAME,
                        self.pages_visited,
                        current_url,
                        len(records),
                    )
            except ValueError as exc:
                logger.error(
                    "Checkpoint for %s is corrupted: %s. Starting fresh crawl.",
                    SOURCE_NAME,
                    exc,
                )

        logger.info("Starting Quotes to Scrape crawl at %s", current_url)

        while current_url:
            try:
                soup = self.get_soup(current_url)
            except (requests.RequestException, requests.HTTPError) as exc:
                logger.error(
                    "Page request failed after retries for %s: %s. Stopping Quotes scraper.",
                    current_url,
                    exc,
                )
                break
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching %s: %s. Stopping Quotes scraper.",
                    current_url,
                    exc,
                )
                break

            self.pages_visited += 1

            quote_tags = soup.select("div.quote")
            logger.info(
                "Visiting page %d: %s (extracted %d quotes)",
                self.pages_visited,
                current_url,
                len(quote_tags),
            )

            for quote_tag in quote_tags:
                try:
                    record = self._parse_quote_item(quote_tag, current_url)
                    if record:
                        records.append(record)
                except Exception as exc:
                    logger.warning(
                        "Error parsing individual quote tag on %s: %s",
                        current_url,
                        exc,
                    )
                    continue

            # Pagination: discover next page link dynamically
            next_link = soup.select_one("li.next a")
            if next_link and next_link.get("href"):
                next_href = next_link["href"].strip()
                current_url = urljoin(current_url, next_href)
                # Persist checkpoint state after page has been successfully processed
                try:
                    save_checkpoint(
                        source=SOURCE_NAME,
                        next_url=current_url,
                        pages_visited=self.pages_visited,
                        records=records,
                    )
                except Exception as exc:
                    logger.warning("Could not persist checkpoint for %s: %s", SOURCE_NAME, exc)
            else:
                logger.info(
                    "No next-page link found on page %d (%s). Natural pagination termination reached.",
                    self.pages_visited,
                    current_url,
                )
                self.stopped_naturally = True
                current_url = None
                # Clear checkpoint on natural successful completion
                try:
                    clear_checkpoint(SOURCE_NAME)
                except Exception as exc:
                    logger.warning("Could not clear checkpoint for %s: %s", SOURCE_NAME, exc)

        logger.info(
            "Quotes scraper finished. Visited %d pages, collected %d raw records.",
            self.pages_visited,
            len(records),
        )
        return records
