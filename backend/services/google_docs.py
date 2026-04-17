"""
google_docs.py — fetch + parse a Google Doc into structured sections.

Each section is split at every Heading 1 / Heading 2 boundary and carries:
  {
      section_id:   str   ← slugified heading text
      heading:      str   ← original heading text
      content:      str   ← full text under this heading
      hash:         str   ← md5(content) for change-detection
      tables:       list  ← inline tables converted to Markdown
      links:        list  ← [{text, url}] hyperlinks in the section
  }
"""

import hashlib
import re
import logging
from functools import lru_cache

from google.oauth2 import service_account
from googleapiclient.discovery import build

from core.config import settings

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/documents.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

HEADING_STYLES = {"HEADING_1", "HEADING_2"}


# ── Auth ─────────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_service():
    """Build and cache an authenticated Google Docs service client."""
    creds = service_account.Credentials.from_service_account_file(
        settings.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
    )
    return build("docs", "v1", credentials=creds, cache_discovery=False)


# ── Fetch ─────────────────────────────────────────────────────────────────────

def fetch_doc(doc_id: str) -> dict:
    """Fetch raw document JSON from the Google Docs API."""
    service = _get_service()
    doc = service.documents().get(documentId=doc_id).execute()
    logger.info(f"Fetched Google Doc: {doc.get('title', doc_id)}")
    return doc


# ── Helpers ──────────────────────────────────────────────────────────────────

def _slugify(text: str) -> str:
    """Convert heading text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text or "untitled"


def _para_text(para: dict) -> str:
    """Extract plain text from a paragraph element."""
    parts = []
    for elem in para.get("elements", []):
        tr = elem.get("textRun", {})
        parts.append(tr.get("content", ""))
    return "".join(parts)


def _para_style(para: dict) -> str:
    """Return the named style of a paragraph (e.g. HEADING_1, NORMAL_TEXT)."""
    return para.get("paragraphStyle", {}).get("namedStyleType", "NORMAL_TEXT")


def _para_links(para: dict) -> list[dict]:
    """Extract [{text, url}] hyperlinks from a paragraph."""
    links = []
    for elem in para.get("elements", []):
        tr = elem.get("textRun", {})
        url = tr.get("textStyle", {}).get("link", {}).get("url")
        if url:
            links.append({"text": tr.get("content", "").strip(), "url": url})
    return links


def _table_to_markdown(table: dict) -> str:
    """Convert a Google Docs table element to a Markdown table string."""
    rows = table.get("tableRows", [])
    if not rows:
        return ""

    md_rows = []
    for row_idx, row in enumerate(rows):
        cells = []
        for cell in row.get("tableCells", []):
            cell_text = " ".join(
                _para_text(p.get("paragraph", {}))
                for p in cell.get("content", [])
                if "paragraph" in p
            ).strip().replace("\n", " ")
            cells.append(cell_text)
        md_rows.append("| " + " | ".join(cells) + " |")
        if row_idx == 0:
            md_rows.append("| " + " | ".join(["---"] * len(cells)) + " |")

    return "\n".join(md_rows)


# ── Parse ─────────────────────────────────────────────────────────────────────

def parse_into_sections(doc_json: dict) -> list[dict]:
    """
    Walk the document body and split at every Heading 1 / Heading 2 boundary.
    Returns a list of section dicts.
    """
    body_content = doc_json.get("body", {}).get("content", [])

    sections: list[dict] = []
    current_heading = "Introduction"
    current_lines: list[str] = []
    current_tables: list[str] = []
    current_links: list[dict] = []

    def _flush(heading: str, lines: list, tables: list, links: list):
        content = "\n".join(lines).strip()
        sections.append({
            "section_id": _slugify(heading),
            "heading": heading,
            "content": content,
            "hash": hashlib.md5(content.encode("utf-8")).hexdigest(),
            "tables": list(tables),
            "links": list(links),
        })

    for block in body_content:
        if "paragraph" in block:
            para = block["paragraph"]
            style = _para_style(para)
            text = _para_text(para).rstrip("\n")

            if style in HEADING_STYLES and text.strip():
                if current_lines or current_tables:
                    _flush(current_heading, current_lines, current_tables, current_links)
                current_heading = text.strip()
                current_lines = []
                current_tables = []
                current_links = []
            else:
                if text.strip():
                    current_lines.append(text)
                current_links.extend(_para_links(para))

        elif "table" in block:
            md = _table_to_markdown(block["table"])
            if md:
                current_tables.append(md)
                current_lines.append(md)

    if current_lines or current_tables:
        _flush(current_heading, current_lines, current_tables, current_links)

    logger.info(f"Parsed {len(sections)} sections from doc")
    return sections


def extract_tables(doc_json: dict) -> list[str]:
    """Return all tables in the document as Markdown strings."""
    tables = []
    for block in doc_json.get("body", {}).get("content", []):
        if "table" in block:
            md = _table_to_markdown(block["table"])
            if md:
                tables.append(md)
    return tables


def extract_links(doc_json: dict) -> list[dict]:
    """Return all hyperlinks [{text, url}] from the document."""
    links = []
    for block in doc_json.get("body", {}).get("content", []):
        if "paragraph" in block:
            links.extend(_para_links(block["paragraph"]))
    return links


def extract_doc_id(url: str) -> str:
    """Extract Google Doc ID from a standard Google Docs URL."""
    match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
    if not match:
        raise ValueError(f"Could not extract doc ID from URL: {url}")
    return match.group(1)
