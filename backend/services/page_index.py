"""
page_index.py — two-stage retrieval with query expansion.

Stage 1: embed question → query page/section-index → identify top sections
Stage 2: filter chunks by those sections → retrieve precise chunks
"""

import logging
from uuid import uuid4

from groq import Groq
from core.config import settings
from services.indexer import add_page_summary, query_page_index, query_chunks
from services.embedder import embedder

logger = logging.getLogger(__name__)

_groq = None


def _get_groq():
    global _groq
    if _groq is None:
        _groq = Groq(api_key=settings.GROQ_API_KEY)
    return _groq


def _summarize_page(page_text: str, source_file: str, page_num: int) -> str:
    prompt = (
        f"In one sentence, summarize what the following page from '{source_file}' "
        f"(page {page_num}) covers. "
        f"Be specific about topics, names, dates, or legal concepts mentioned.\n\n"
        f"{page_text[:2000]}"
    )
    response = _get_groq().chat.completions.create(
        model=settings.SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def _summarize_section(section_text: str, heading: str, doc_id: str) -> str:
    prompt = (
        f"In one sentence, summarize what the section titled '{heading}' "
        f"from document '{doc_id}' covers. "
        f"Be specific about topics, names, dates, or key concepts mentioned.\n\n"
        f"{section_text[:2000]}"
    )
    response = _get_groq().chat.completions.create(
        model=settings.SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def build_page_index(page_texts: list[dict]):
    """Build page-level summaries for file-uploaded documents."""
    for page in page_texts:
        summary = _summarize_page(page["text"], page["source_file"], page["page"])
        summary_id = str(uuid4())
        add_page_summary(
            summary_id=summary_id,
            summary_text=summary,
            metadata={
                "upload_id": page["upload_id"],
                "doc_id": page["upload_id"],
                "source_file": page["source_file"],
                "section_id": f"p{page['page']}",
                "heading": f"Page {page['page']}",
                "page": page["page"],
                "file_type": page.get("file_type", "file"),
            },
        )


def build_section_index(section_entries: list[dict]):
    """Build section-level summaries for Google Docs."""
    for entry in section_entries:
        summary = _summarize_section(
            entry["text"], entry["heading"], entry["doc_id"]
        )
        summary_id = str(uuid4())
        add_page_summary(
            summary_id=summary_id,
            summary_text=summary,
            metadata={
                "upload_id": entry["upload_id"],
                "doc_id": entry["doc_id"],
                "source_file": entry["source_file"],
                "section_id": entry["section_id"],
                "heading": entry["heading"],
                "page": 0,
                "file_type": "gdoc",
            },
        )


def _expand_query(question: str) -> list[str]:
    try:
        prompt = (
            f"Generate 3 different search queries to find document passages that answer this question. "
            f"Write queries as keyword-rich statements (not questions), one per line, no numbering or explanation.\n\n"
            f"Question: {question}"
        )
        response = _get_groq().chat.completions.create(
            model=settings.SUMMARY_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=120,
            temperature=0.3,
        )
        expanded = response.choices[0].message.content.strip().split("\n")
        variants = [q.strip() for q in expanded if q.strip()]
        logger.info(f"Query expansion: {variants}")
        return [question] + variants[:3]
    except Exception as e:
        logger.warning(f"Query expansion failed, using original: {e}")
        return [question]


def _merge_page_results(all_results: list[list[dict]]) -> list[dict]:
    best: dict[str, dict] = {}
    for results in all_results:
        for r in results:
            meta = r["metadata"]
            section_id = meta.get("section_id") or f"p{meta.get('page', 0)}"
            key = f"{meta.get('upload_id', '')}::{section_id}"
            if key not in best or r["score"] > best[key]["score"]:
                best[key] = r
    return sorted(best.values(), key=lambda x: x["score"], reverse=True)


def two_stage_retrieve(
    question: str, upload_ids: list[str] | None
) -> tuple[list[dict], list[str]]:
    query_variants = _expand_query(question)
    all_embeddings = [embedder.embed_one(q) for q in query_variants]

    all_page_results = [
        query_page_index(
            query_embedding=emb,
            upload_ids=upload_ids,
            top_k=settings.TOP_K_PAGES,
        )
        for emb in all_embeddings
    ]
    merged = _merge_page_results(all_page_results)[: settings.TOP_K_PAGES]

    pages_identified: list[str] = []
    page_filters: list[dict] = []

    for r in merged:
        meta = r["metadata"]
        upload_id = meta.get("upload_id", "")
        section_id = meta.get("section_id")
        heading = meta.get("heading", "")
        page = meta.get("page", 0)
        source_file = meta.get("source_file", "")
        file_type = meta.get("file_type", "")

        if file_type == "gdoc" or (section_id and not section_id.startswith("p")):
            label = heading or section_id or "?"
            pages_identified.append(label)
            page_filters.append({"upload_id": upload_id, "section_id": section_id})
        else:
            label = f"{source_file}:p{page}"
            pages_identified.append(label)
            page_filters.append({"upload_id": upload_id, "page": page})

    if not page_filters:
        return [], []

    stage2 = query_chunks(
        query_embedding=all_embeddings[0],
        page_filters=page_filters,
        top_k=settings.TOP_K_CHUNKS,
    )

    return stage2, pages_identified