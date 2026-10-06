"""Base scraper module providing shared HTTP client, retries, and rate limiting."""

import logging
import time
from typing import List, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from config import (
    DEFAULT_MAX_RETRIES,
    DEFAULT_REQUEST_DELAY,
    DEFAULT_REQUEST_TIMEOUT,
)
from processing import ScrapedRecord

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = (
    "AssignmentScraper/1.0 "
    "(Python Web Scraping Interview Assignment; +https://example.com/scraper)"
)
RETRY_STATUS_CODES = [429, 500, 502, 503, 504]


class BaseScraper:
    """Base scraper providing session management, rate limiting, and robust HTTP requests."""

    def __init__(
        self,
        base_url: str = "",
        delay: float = DEFAULT_REQUEST_DELAY,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        user_agent: Optional[str] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.user_agent = user_agent or DEFAULT_USER_AGENT

        self._last_request_time: Optional[float] = None
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create and configure a requests.Session with retries and default headers."""
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )

        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1.0,
            status_forcelist=RETRY_STATUS_CODES,
            raise_on_status=False,
            allowed_methods=["GET", "HEAD"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _apply_delay(self) -> None:
        """Enforce delay between consecutive HTTP requests to avoid hammering target servers."""
        if self._last_request_time is not None and self.delay > 0:
            elapsed = time.time() - self._last_request_time
            if elapsed < self.delay:
                sleep_duration = self.delay - elapsed
                logger.debug("Applying rate limit delay of %.2fs", sleep_duration)
                time.sleep(sleep_duration)
        self._last_request_time = time.time()

    def get(self, url: str) -> requests.Response:
        """Fetch URL with rate limiting, timeouts, retries, and comprehensive error handling.

        Raises:
            requests.HTTPError: When an HTTP 4xx or 5xx status code is returned after retries.
            requests.RequestException: When a network/connection error occurs.
        """
        self._apply_delay()
        logger.info("Requesting URL: %s", url)

        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.debug("Received HTTP %d for %s", response.status_code, url)
            return response
        except requests.HTTPError as exc:
            logger.error("HTTP error occurred for %s: %s", url, exc)
            raise
        except requests.RequestException as exc:
            logger.error("Network or connection error for %s: %s", url, exc)
            raise

    def get_soup(self, url: str) -> BeautifulSoup:
        """Fetch page content and return parsed BeautifulSoup object using lxml parser."""
        response = self.get(url)
        return BeautifulSoup(response.text, "lxml")

    def build_url(self, relative_path: str) -> str:
        """Safely resolve relative URL against base_url."""
        return urljoin(self.base_url + "/", relative_path.lstrip("/"))

    def scrape(self) -> List[ScrapedRecord]:
        """Subclasses should implement scraping pipeline and return a list of ScrapedRecords."""
        raise NotImplementedError("Subclasses must implement scrape()")

    def close(self) -> None:
        """Close the underlying requests session."""
        self.session.close()

    def __enter__(self) -> "BaseScraper":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
