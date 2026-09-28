"""
HTML parser that extracts clean, sectioned text from medical documents.

Different sources have different HTML structures, so we use a
source-specific parser dispatch pattern. Each parser extracts:
- The main body text
- Sections with headings (overview, dosage, side effects, etc.)
- Metadata (title, source)
"""

import logging
import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)


# Standard section names we normalize headings to
SECTION_KEYWORDS = {
    "overview": ["overview", "about", "what is", "description", "introduction"],
    "uses": ["uses", "used for", "indications", "why is this"],
    "dosage": ["dosage", "dose", "how to use", "how to take", "administration"],
    "side_effects": ["side effects", "adverse", "warnings"],
    "precautions": ["precautions", "before taking", "who can", "who cannot"],
    "interactions": ["interactions", "other drugs", "avoid"],
    "storage": ["storage", "store"],
    "symptoms": ["symptoms", "signs"],
    "causes": ["causes", "why"],
    "treatment": ["treatment", "therapy", "how is it treated"],
}


@dataclass
class ParsedSection:
    """A logical section of a parsed document."""

    heading: str
    normalized_section: str  # one of SECTION_KEYWORDS keys, or "general"
    text: str


@dataclass
class ParsedDocument:
    """A cleanly parsed medical document."""

    source: str
    title: str
    url: str
    category: str
    sections: list[ParsedSection] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        """Concatenated text of all sections."""
        return "\n\n".join(f"## {s.heading}\n{s.text}" for s in self.sections)


def normalize_section_name(heading: str) -> str:
    """Map a heading to a normalized section key."""
    heading_lower = heading.lower().strip()
    for key, keywords in SECTION_KEYWORDS.items():
        if any(kw in heading_lower for kw in keywords):
            return key
    return "general"


def clean_text(text: str) -> str:
    """Normalize whitespace and remove control characters."""
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    return text.strip()


class HtmlParser:
    """
    Parses HTML documents from medical sources into clean sectioned text.

    Uses a dispatch pattern: each source has its own parsing strategy
    because HTML structure varies significantly across sites.
    """

    def parse(
        self,
        html: str,
        source: str,
        title: str,
        url: str,
        category: str = "general",
    ) -> ParsedDocument:
        """
        Parse an HTML document into structured sections.

        Dispatches to source-specific parser or falls back to generic.
        """
        soup = BeautifulSoup(html, "lxml")

        parser_fn = {
            "medlineplus": self._parse_medlineplus,
            "nhs": self._parse_nhs,
        }.get(source, self._parse_generic)

        sections = parser_fn(soup)

        # Filter out empty sections
        sections = [s for s in sections if s.text and len(s.text) > 20]

        return ParsedDocument(
            source=source,
            title=title,
            url=url,
            category=category,
            sections=sections,
        )

    def _parse_medlineplus(self, soup: BeautifulSoup) -> list[ParsedSection]:
        """
        Parse MedlinePlus drug information pages.

        Structure: sections are inside <section> or <div> with <h2> headings.
        """
        sections: list[ParsedSection] = []
        for header in soup.find_all(["h2", "h3"]):
            heading = clean_text(header.get_text())
            if not heading:
                continue

            # Collect text from siblings until the next header of same/higher level
            body_parts: list[str] = []
            for sibling in header.find_next_siblings():
                if isinstance(sibling, Tag) and sibling.name in ("h2", "h3"):
                    break
                text = clean_text(sibling.get_text())
                if text:
                    body_parts.append(text)

            body = " ".join(body_parts)
            if body:
                sections.append(
                    ParsedSection(
                        heading=heading,
                        normalized_section=normalize_section_name(heading),
                        text=body,
                    )
                )

        return sections

    def _parse_nhs(self, soup: BeautifulSoup) -> list[ParsedSection]:
        """
        Parse NHS medicine/condition pages.

        Structure: <h2> headings inside <article> or main content div.
        """
        # NHS uses <main> for main content
        main = soup.find("main") or soup

        sections: list[ParsedSection] = []
        for header in main.find_all(["h2", "h3"]):
            heading = clean_text(header.get_text())
            if not heading:
                continue

            body_parts: list[str] = []
            for sibling in header.find_next_siblings():
                if isinstance(sibling, Tag) and sibling.name in ("h2", "h3"):
                    break
                text = clean_text(sibling.get_text())
                if text:
                    body_parts.append(text)

            body = " ".join(body_parts)
            if body:
                sections.append(
                    ParsedSection(
                        heading=heading,
                        normalized_section=normalize_section_name(heading),
                        text=body,
                    )
                )

        return sections

    def _parse_generic(self, soup: BeautifulSoup) -> list[ParsedSection]:
        """
        Generic fallback parser using semantic HTML structure.
        """
        # Remove scripts, styles, nav, footer
        for tag in soup.find_all(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        sections: list[ParsedSection] = []
        for header in soup.find_all(["h1", "h2", "h3"]):
            heading = clean_text(header.get_text())
            if not heading:
                continue

            body_parts: list[str] = []
            for sibling in header.find_next_siblings():
                if isinstance(sibling, Tag) and sibling.name in ("h1", "h2", "h3"):
                    break
                text = clean_text(sibling.get_text())
                if text:
                    body_parts.append(text)

            body = " ".join(body_parts)
            if body:
                sections.append(
                    ParsedSection(
                        heading=heading,
                        normalized_section=normalize_section_name(heading),
                        text=body,
                    )
                )

        # If no sections found, capture the body as one general section
        if not sections:
            body_text = clean_text(soup.get_text())
            if body_text:
                sections.append(
                    ParsedSection(
                        heading="Content",
                        normalized_section="general",
                        text=body_text,
                    )
                )

        return sections