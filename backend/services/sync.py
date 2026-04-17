"""
sync.py — hash diff engine + re-indexing logic for Google Docs live RAG.
"""

import logging
from datetime import datetime, timezone
from typing import TypedDict

from services.google_docs import fetch_doc, parse_into_sections
from services.indexer import get_all_hashes, delete_section, add_chunks
from services.page_index import build_section_index
from services.ingestion import chunk_gdoc_section

logger = logging.getLogger(__name__)


class SyncResult(TypedDict):
    doc_id: str
    synced_at: str
    added: int
    updated: int
    deleted: int
    total_sections: int


_sync_registry: dict[str, SyncResult] = {}


def get_last_sync(doc_id: str) -> SyncResult | None:
    return _sync_registry.get(doc_id)


def get_all_syncs() -> dict[str, SyncResult]:
    return dict(_sync_registry)


def get_stored_hashes(doc_id: str) -> dict[str, str]:
    return get_all_hashes(doc_id)


def diff(
    old_hashes: dict[str, str],
    new_sections: list[dict],
) -> tuple[list[dict], list[dict], list[str]]:
    new_by_id = {s["section_id"]: s for s in new_sections}

    to_add: list[dict] = []
    to_update: list[dict] = []
    to_delete: list[str] = []

    for section_id, section in new_by_id.items():
        if section_id not in old_hashes:
            to_add.append(section)
        elif old_hashes[section_id] != section["hash"]:
            to_update.append(section)

    for section_id in old_hashes:
        if section_id not in new_by_id:
            to_delete.append(section_id)

    return to_add, to_update, to_delete


def run_sync(doc_id: str) -> SyncResult:
    logger.info(f"[sync] Starting sync for doc_id={doc_id}")

    doc_json = fetch_doc(doc_id)
    new_sections = parse_into_sections(doc_json)

    old_hashes = get_stored_hashes(doc_id)
    to_add, to_update, to_delete = diff(old_hashes, new_sections)

    logger.info(
        f"[sync] doc={doc_id} — "
        f"add={len(to_add)}, update={len(to_update)}, delete={len(to_delete)}"
    )

    for section_id in to_delete:
        delete_section(doc_id, section_id)

    for section in to_update:
        delete_section(doc_id, section["section_id"])

    sections_to_index = to_add + to_update
    all_chunks: list[dict] = []
    page_entries: list[dict] = []

    for section in sections_to_index:
        chunks = chunk_gdoc_section(section, doc_id)
        all_chunks.extend(chunks)
        page_entries.append({
            "section_id": section["section_id"],
            "heading": section["heading"],
            "text": section["content"],
            "doc_id": doc_id,
            "upload_id": doc_id,
            "source_file": doc_id,
        })

    if all_chunks:
        add_chunks(all_chunks)

    if page_entries:
        build_section_index(page_entries)

    result: SyncResult = {
        "doc_id": doc_id,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "added": len(to_add),
        "updated": len(to_update),
        "deleted": len(to_delete),
        "total_sections": len(new_sections),
    }
    _sync_registry[doc_id] = result
    logger.info(f"[sync] Complete: {result}")
    return result
