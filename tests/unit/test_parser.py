"""Tests for the HTML parser."""

import pytest

from src.ingestion.parser import (
    HtmlParser,
    clean_text,
    normalize_section_name,
)


class TestNormalizeSectionName:
    """Test section heading normalization."""

    @pytest.mark.parametrize("heading,expected", [
        ("Overview", "overview"),
        ("About Ibuprofen", "overview"),
        ("What is Aspirin?", "overview"),
        ("Uses", "uses"),
        ("Why is this medication prescribed?", "uses"),
        ("Dosage", "dosage"),
        ("How to Use", "dosage"),
        ("Side Effects", "side_effects"),
        ("Warnings", "side_effects"),
        ("Drug Interactions", "interactions"),
        ("Storage", "storage"),
        ("Random Heading", "general"),
    ])
    def test_normalization(self, heading, expected):
        assert normalize_section_name(heading) == expected


class TestCleanText:
    """Test text cleaning utility."""

    def test_collapses_whitespace(self):
        assert clean_text("hello   world\n\t\ttest") == "hello world test"

    def test_strips_control_chars(self):
        assert clean_text("hello\x00world") == "helloworld"

    def test_strips_leading_trailing_whitespace(self):
        assert clean_text("  hello  ") == "hello"


class TestHtmlParserGeneric:
    """Test the generic HTML parser fallback."""

    def test_parse_simple_html(self):
        html = """
        <html>
          <body>
            <h2>Overview</h2>
            <p>Ibuprofen is a pain reliever used to treat headaches.</p>
            <h2>Side Effects</h2>
            <p>Common side effects include nausea and stomach upset symptoms.</p>
          </body>
        </html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "unknown", "Ibuprofen", "http://test.com")

        assert doc.title == "Ibuprofen"
        assert doc.source == "unknown"
        assert len(doc.sections) == 2
        assert doc.sections[0].normalized_section == "overview"
        assert doc.sections[1].normalized_section == "side_effects"

    def test_empty_sections_filtered(self):
        html = """
        <html><body>
          <h2>Empty</h2>
          <p></p>
          <h2>Real Section</h2>
          <p>This is a real section with sufficient text content for the parser.</p>
        </body></html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "unknown", "Test", "http://test.com")

        assert len(doc.sections) == 1
        assert doc.sections[0].heading == "Real Section"

    def test_removes_scripts_and_styles(self):
        html = """
        <html>
          <head>
            <script>alert('hacked')</script>
            <style>body { color: red; }</style>
          </head>
          <body>
            <h2>Content</h2>
            <p>Real medical content about treatment and recovery outcomes.</p>
          </body>
        </html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "unknown", "Test", "http://test.com")

        for section in doc.sections:
            assert "alert" not in section.text
            assert "color: red" not in section.text

    def test_full_text_property(self):
        html = """
        <html><body>
          <h2>Section One</h2>
          <p>Content of section one with sufficient length here.</p>
          <h2>Section Two</h2>
          <p>Content of section two with sufficient length here.</p>
        </body></html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "unknown", "Test", "http://test.com")
        text = doc.full_text
        assert "Section One" in text
        assert "Section Two" in text


class TestHtmlParserMedlinePlus:
    """Test the MedlinePlus-specific parser."""

    def test_parses_medlineplus_structure(self):
        html = """
        <html><body>
          <h1>IBUPROFEN</h1>
          <h2>Why is this medication prescribed?</h2>
          <p>Ibuprofen is used to relieve pain from various conditions.</p>
          <p>It also reduces fever and treats inflammation effectively.</p>
          <h2>How should this medicine be used?</h2>
          <p>Take ibuprofen as directed on the label or by your doctor.</p>
        </body></html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "medlineplus", "Ibuprofen", "http://test.com")

        assert len(doc.sections) == 2
        assert doc.sections[0].normalized_section == "uses"
        assert doc.sections[1].normalized_section == "dosage"


class TestHtmlParserNhs:
    """Test the NHS-specific parser."""

    def test_parses_nhs_structure(self):
        html = """
        <html><body>
          <main>
            <h1>Ibuprofen for adults</h1>
            <h2>About ibuprofen for adults</h2>
            <p>Ibuprofen is a common painkiller used across the UK.</p>
            <h2>Key facts</h2>
            <p>It usually works within 20 to 30 minutes after taking it.</p>
          </main>
        </body></html>
        """
        parser = HtmlParser()
        doc = parser.parse(html, "nhs", "Ibuprofen", "http://nhs.uk/test")

        assert len(doc.sections) >= 1
        assert any(s.normalized_section == "overview" for s in doc.sections)