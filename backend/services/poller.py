"""
poller.py — background polling loop for live Google Docs sync.
"""

import asyncio
import logging

from core.config import settings
from services.sync import run_sync

logger = logging.getLogger(__name__)

_watched_docs: set[str] = set()
_poller_task: asyncio.Task | None = None


def register_doc(doc_id: str) -> None:
    _watched_docs.add(doc_id)
    logger.info(f"[poller] Registered doc_id={doc_id} for polling")


def unregister_doc(doc_id: str) -> None:
    _watched_docs.discard(doc_id)
    logger.info(f"[poller] Unregistered doc_id={doc_id}")


def watched_docs() -> set[str]:
    return set(_watched_docs)


async def _poll_loop() -> None:
    interval = settings.POLL_INTERVAL_SECONDS
    logger.info(f"[poller] Loop started — interval={interval}s")

    while True:
        await asyncio.sleep(interval)

        if not _watched_docs:
            continue

        for doc_id in list(_watched_docs):
            try:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, run_sync, doc_id)
                changes = result["added"] + result["updated"] + result["deleted"]
                if changes:
                    logger.info(
                        f"[poller] doc={doc_id} synced — "
                        f"{changes} change(s) detected"
                    )
            except Exception as exc:
                logger.error(f"[poller] Sync failed for doc={doc_id}: {exc}")


def start_poller() -> None:
    global _poller_task
    if _poller_task is None or _poller_task.done():
        _poller_task = asyncio.ensure_future(_poll_loop())
        logger.info("[poller] Background task scheduled")


def stop_poller() -> None:
    global _poller_task
    if _poller_task and not _poller_task.done():
        _poller_task.cancel()
        logger.info("[poller] Background task cancelled")
