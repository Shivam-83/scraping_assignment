"""Scraper implementation for Books to Scrape."""

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

DEFAULT_BOOKS_URL = "https://books.toscrape.com/"


from processing.checkpoint import (
    clear_checkpoint,
    has_checkpoint,
    load_checkpoint,
    save_checkpoint,
)

SOURCE_NAME = "Books to Scrape"


class BooksScraper(BaseScraper):
    """Scrapes book catalog records from Books to Scrape via dynamic pagination."""

    def __init__(
        self,
        base_url: str = DEFAULT_BOOKS_URL,
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

    def _parse_product_pod(self, pod: Tag, current_url: str) -> Optional[ScrapedRecord]:
        """Extract raw book attributes from a single product_pod container."""
        # 1. Title and Product URL
        title_tag = pod.select_one("h3 a")
        if not title_tag:
            logger.warning("Missing 'h3 a' element in product_pod on %s", current_url)
            return None

        # Title: Prefer 'title' attribute (contains full un-truncated title), fallback to text
        raw_title = title_tag.get("title")
        if not raw_title:
            raw_title = title_tag.get_text(strip=True)

        # URL: Resolve relative link against current page URL
        rel_href = title_tag.get("href")
        book_url = urljoin(current_url, rel_href) if rel_href else current_url

        # 2. Raw Price
        price_tag = pod.select_one("p.price_color")
        raw_price = price_tag.get_text(strip=True) if price_tag else None

        # 3. Raw Rating
        rating_tag = pod.select_one("p.star-rating")
        raw_rating = None
        if rating_tag:
            classes = rating_tag.get("class", [])
            star_classes = [c for c in classes if c != "star-rating"]
            if star_classes:
                raw_rating = star_classes[0]

        return ScrapedRecord(
            source=SOURCE_NAME,
            source_url=book_url,
            name_or_title=raw_title or "",
            price=raw_price,
            rating=raw_rating,
            category=None,
            author=None,
            tags=None,
            description=None,
        )

    def scrape(self) -> List[ScrapedRecord]:
        """Execute full pagination crawl across Books to Scrape catalog.

        Returns:
            List[ScrapedRecord]: Extracted raw book records.
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

        logger.info("Starting Books to Scrape crawl at %s", current_url)

        while current_url:
            try:
                soup = self.get_soup(current_url)
            except (requests.RequestException, requests.HTTPError) as exc:
                logger.error(
                    "Page request failed after retries for %s: %s. Stopping Books scraper.",
                    current_url,
                    exc,
                )
                break
            except Exception as exc:
                logger.error(
                    "Unexpected error fetching %s: %s. Stopping Books scraper.",
                    current_url,
                    exc,
                )
                break

            self.pages_visited += 1

            # Extract book items from current page
            pods = soup.select("article.product_pod")
            logger.info(
                "Visiting page %d: %s (extracted %d books)",
                self.pages_visited,
                current_url,
                len(pods),
            )

            for pod in pods:
                try:
                    record = self._parse_product_pod(pod, current_url)
                    if record:
                        records.append(record)
                except Exception as exc:
                    logger.warning(
                        "Error parsing individual book pod on %s: %s",
                        current_url,
                        exc,
                    )
                    continue

            # Pagination: discover next link dynamically
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
            "Books scraper finished. Visited %d pages, collected %d raw records.",
            self.pages_visited,
            len(records),
        )
        return records
