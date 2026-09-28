"""Tests for the document scraper."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from src.ingestion.scraper import DocumentScraper, ScrapedDocument, ScrapeError


@pytest.fixture
def temp_raw_dir(tmp_path: Path) -> Path:
    """Temporary directory for scraped HTML."""
    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    return raw_dir


@pytest.fixture
def sources_yaml(tmp_path: Path) -> Path:
    """A minimal sources.yaml for testing."""
    sources = {
        "sources": [
            {
                "name": "test_source",
                "base_url": "https://example.com",
                "license": "Test",
                "documents": [
                    {
                        "title": "Test Doc 1",
                        "url": "https://example.com/doc1",
                        "category": "medication",
                    },
                    {
                        "title": "Test Doc 2",
                        "url": "https://example.com/doc2",
                        "category": "condition",
                    },
                ],
            }
        ]
    }
    path = tmp_path / "sources.yaml"
    path.write_text(yaml.safe_dump(sources))
    return path


class TestScraperInit:
    """Test scraper initialization."""

    def test_creates_raw_directory(self, tmp_path: Path):
        raw_dir = tmp_path / "new_raw"
        DocumentScraper(raw_data_dir=raw_dir)
        assert raw_dir.exists()

    def test_uses_config_defaults(self, temp_raw_dir: Path):
        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        assert scraper.timeout > 0
        assert scraper.delay >= 0
        assert "MedGuard" in scraper.user_agent


class TestLoadSources:
    """Test source registry loading."""

    def test_loads_sources_from_yaml(self, temp_raw_dir: Path, sources_yaml: Path):
        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        sources = scraper.load_sources(sources_yaml)
        assert len(sources) == 1
        assert sources[0]["name"] == "test_source"
        assert len(sources[0]["documents"]) == 2


class TestScrapeUrl:
    """Test scraping a single URL."""

    @patch("src.ingestion.scraper.requests.get")
    def test_successful_scrape(self, mock_get: MagicMock, temp_raw_dir: Path):
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test content</body></html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        result = scraper.scrape_url(
            url="https://example.com/test",
            source="test_source",
            title="Test",
        )

        assert isinstance(result, ScrapedDocument)
        assert result.source == "test_source"
        assert result.title == "Test"
        assert "Test content" in result.raw_html
        assert result.saved_path.exists()

    @patch("src.ingestion.scraper.requests.get")
    def test_scrape_saves_html_to_source_directory(
        self, mock_get: MagicMock, temp_raw_dir: Path
    ):
        mock_response = MagicMock()
        mock_response.text = "<html>test</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        result = scraper.scrape_url(
            url="https://example.com/test",
            source="medlineplus",
            title="Test",
        )

        assert isinstance(result, ScrapedDocument)
        assert (temp_raw_dir / "medlineplus").exists()
        assert result.saved_path.parent.name == "medlineplus"

    @patch("src.ingestion.scraper.requests.get")
    def test_scrape_failure_returns_error(
        self, mock_get: MagicMock, temp_raw_dir: Path
    ):
        import requests
        mock_get.side_effect = requests.RequestException("Connection failed")

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        result = scraper.scrape_url(
            url="https://example.com/fail",
            source="test",
            title="Fail",
        )

        assert isinstance(result, ScrapeError)
        assert "Connection failed" in result.error

    @patch("src.ingestion.scraper.requests.get")
    def test_different_urls_get_different_filenames(
        self, mock_get: MagicMock, temp_raw_dir: Path
    ):
        mock_response = MagicMock()
        mock_response.text = "<html>content</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        r1 = scraper.scrape_url("https://example.com/a", "test", "A")
        r2 = scraper.scrape_url("https://example.com/b", "test", "B")

        assert isinstance(r1, ScrapedDocument)
        assert isinstance(r2, ScrapedDocument)
        assert r1.saved_path != r2.saved_path


class TestScrapeAll:
    """Test batch scraping."""

    @patch("src.ingestion.scraper.requests.get")
    @patch("src.ingestion.scraper.time.sleep")  # skip delays in tests
    def test_scrape_all_processes_all_documents(
        self,
        mock_sleep: MagicMock,
        mock_get: MagicMock,
        temp_raw_dir: Path,
        sources_yaml: Path,
    ):
        mock_response = MagicMock()
        mock_response.text = "<html>ok</html>"
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        successes, failures = scraper.scrape_all(sources_yaml)

        assert len(successes) == 2
        assert len(failures) == 0

    @patch("src.ingestion.scraper.requests.get")
    @patch("src.ingestion.scraper.time.sleep")
    def test_scrape_all_captures_partial_failures(
        self,
        mock_sleep: MagicMock,
        mock_get: MagicMock,
        temp_raw_dir: Path,
        sources_yaml: Path,
    ):
        import requests

        # First call succeeds, second fails
        def side_effect(*args, **kwargs):
            if "doc1" in args[0]:
                r = MagicMock()
                r.text = "<html>ok</html>"
                r.raise_for_status = MagicMock()
                return r
            raise requests.RequestException("Network error")

        mock_get.side_effect = side_effect

        scraper = DocumentScraper(raw_data_dir=temp_raw_dir)
        successes, failures = scraper.scrape_all(sources_yaml)

        assert len(successes) == 1
        assert len(failures) == 1