"""
gdoc.py — API endpoints for Google Doc connection and sync status.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.google_docs import extract_doc_id
from services.sync import run_sync, get_last_sync, get_all_syncs
from services.poller import register_doc, watched_docs

logger = logging.getLogger(__name__)

router = APIRouter()


class ConnectGDocRequest(BaseModel):
    url: str


class ConnectGDocResponse(BaseModel):
    doc_id: str
    message: str
    sections_indexed: int
    added: int


class SyncStatusResponse(BaseModel):
    doc_id: str
    synced_at: str
    added: int
    updated: int
    deleted: int
    total_sections: int


@router.post("/connect-gdoc", response_model=ConnectGDocResponse)
async def connect_gdoc(body: ConnectGDocRequest):
    try:
        doc_id = extract_doc_id(body.url.strip())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        result = run_sync(doc_id)
    except Exception as e:
        logger.error(f"Initial sync failed for {doc_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index Google Doc: {str(e)}"
        )

    register_doc(doc_id)

    return ConnectGDocResponse(
        doc_id=doc_id,
        message="Google Doc connected and indexed successfully.",
        sections_indexed=result["total_sections"],
        added=result["added"],
    )


@router.get("/sync-status", response_model=list[SyncStatusResponse])
async def sync_status():
    all_syncs = get_all_syncs()
    if not all_syncs:
        return []
    return [SyncStatusResponse(**sync) for sync in all_syncs.values()]


@router.get("/sync-status/{doc_id}", response_model=SyncStatusResponse)
async def sync_status_for_doc(doc_id: str):
    result = get_last_sync(doc_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No sync record found for doc_id={doc_id}"
        )
    return SyncStatusResponse(**result)


@router.get("/watched-docs")
async def list_watched_docs():
    return {"watched": list(watched_docs())}
