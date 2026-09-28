"""
HTTP scraper for medical document sources.

Downloads raw HTML from configured sources with polite rate limiting
and stores it to disk for downstream parsing.
"""

import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path

import requests
import yaml
from requests.exceptions import RequestException

from src.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedDocument:
    """A document successfully downloaded from a source."""

    source: str
    title: str
    url: str
    category: str
    raw_html: str
    saved_path: Path


@dataclass
class ScrapeError:
    """A document that failed to download."""

    source: str
    title: str
    url: str
    error: str


class DocumentScraper:
    """
    Scrapes medical documents from configured web sources.

    Uses polite defaults: identifiable user agent, configurable delay
    between requests, and per-source directory structure.
    """

    def __init__(self, raw_data_dir: Path | None = None) -> None:
        settings = get_settings()
        self.raw_data_dir = raw_data_dir or Path(settings.raw_data_directory)
        self.timeout = settings.scraper_timeout_seconds
        self.delay = settings.scraper_delay_seconds
        self.user_agent = settings.scraper_user_agent
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

    def load_sources(self, sources_path: Path) -> list[dict]:
        """Load the source registry from YAML."""
        with sources_path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("sources", [])

    def scrape_url(
        self,
        url: str,
        source: str,
        title: str,
        category: str = "general",
    ) -> ScrapedDocument | ScrapeError:
        """
        Download a single URL and save its HTML to disk.

        Returns ScrapedDocument on success or ScrapeError on failure.
        Never raises — errors are captured for batch reporting.
        """
        try:
            response = requests.get(
                url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except RequestException as e:
            logger.warning("Failed to scrape %s: %s", url, e)
            return ScrapeError(source=source, title=title, url=url, error=str(e))

        source_dir = self.raw_data_dir / source
        source_dir.mkdir(parents=True, exist_ok=True)

        # Use URL hash as filename to avoid collisions from same-title docs
        url_hash = hashlib.sha256(url.encode()).hexdigest()[:16]
        filename = f"{url_hash}.html"
        saved_path = source_dir / filename

        saved_path.write_text(response.text, encoding="utf-8")

        logger.info("Scraped %s → %s", url, saved_path)

        return ScrapedDocument(
            source=source,
            title=title,
            url=url,
            category=category,
            raw_html=response.text,
            saved_path=saved_path,
        )

    def scrape_all(
        self, sources_path: Path
    ) -> tuple[list[ScrapedDocument], list[ScrapeError]]:
        """
        Scrape all documents defined in the source registry.

        Applies a delay between requests to be polite to servers.
        Returns (successes, failures) so callers can report both.
        """
        sources = self.load_sources(sources_path)
        successes: list[ScrapedDocument] = []
        failures: list[ScrapeError] = []

        for source_config in sources:
            source_name = source_config["name"]
            documents = source_config.get("documents", [])

            logger.info("Scraping %d documents from %s", len(documents), source_name)

            for doc in documents:
                result = self.scrape_url(
                    url=doc["url"],
                    source=source_name,
                    title=doc["title"],
                    category=doc.get("category", "general"),
                )

                if isinstance(result, ScrapedDocument):
                    successes.append(result)
                else:
                    failures.append(result)

                time.sleep(self.delay)

        logger.info(
            "Scraping complete: %d successes, %d failures",
            len(successes), len(failures),
        )
        return successes, failures