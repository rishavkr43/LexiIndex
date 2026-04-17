"""
indexer.py — Pinecone upsert / query / delete operations.

Every vector carries structured metadata:
  { doc_id, section_id, content_hash, heading, chunk_index,
    source_file, upload_id, page, file_type }
"""

from pinecone import Pinecone, ServerlessSpec
from core.config import settings
from services.embedder import embedder

_pc = None
_index = None


def _get_index():
    global _pc, _index
    if _index is None:
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        index_name = settings.PINECONE_INDEX_NAME
        if index_name not in _pc.list_indexes().names():
            _pc.create_index(
                name=index_name,
                dimension=384,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud="aws",
                    region=settings.PINECONE_ENVIRONMENT
                )
            )
        _index = _pc.Index(index_name)
    return _index


def add_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    embeddings = embedder.embed(texts)

    vectors = [
        {
            "id": ids[i],
            "values": embeddings[i],
            "metadata": {**metadatas[i], "text": texts[i]},
        }
        for i in range(len(ids))
    ]

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i : i + batch_size]
        _get_index().upsert(
            vectors=batch, namespace=settings.PINECONE_NAMESPACE_CHUNKS
        )

    return len(chunks)


def add_page_summary(summary_id: str, summary_text: str, metadata: dict):
    embedding = embedder.embed_one(summary_text)
    _get_index().upsert(
        vectors=[
            {
                "id": summary_id,
                "values": embedding,
                "metadata": {**metadata, "text": summary_text},
            }
        ],
        namespace=settings.PINECONE_NAMESPACE_PAGES,
    )


def delete_section(doc_id: str, section_id: str) -> None:
    """Delete all vectors for a doc_id + section_id pair from both namespaces."""
    index = _get_index()
    filter_dict = {
        "$and": [
            {"doc_id": {"$eq": doc_id}},
            {"section_id": {"$eq": section_id}},
        ]
    }
    index.delete(filter=filter_dict, namespace=settings.PINECONE_NAMESPACE_CHUNKS)
    index.delete(filter=filter_dict, namespace=settings.PINECONE_NAMESPACE_PAGES)


def get_all_hashes(doc_id: str) -> dict[str, str]:
    """Return {section_id: content_hash} for all stored vectors of a doc."""
    index = _get_index()
    try:
        dummy = [0.0] * 384
        results = index.query(
            vector=dummy,
            top_k=10_000,
            include_metadata=True,
            include_values=False,
            namespace=settings.PINECONE_NAMESPACE_CHUNKS,
            filter={"doc_id": {"$eq": doc_id}},
        )
        hashes: dict[str, str] = {}
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            sid = meta.get("section_id")
            chash = meta.get("content_hash")
            if sid and chash and sid not in hashes:
                hashes[sid] = chash
        return hashes
    except Exception:
        return {}


def query_page_index(
    query_embedding: list[float],
    upload_ids: list[str] | None,
    top_k: int,
) -> list[dict]:
    filter_dict = {"upload_id": {"$in": upload_ids}} if upload_ids else None

    results = _get_index().query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.PINECONE_NAMESPACE_PAGES,
        filter=filter_dict,
    )

    return [
        {
            "id": match["id"],
            "text": match["metadata"].get("text", ""),
            "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
            "score": round(match["score"], 4),
        }
        for match in results["matches"]
    ]


def query_chunks(
    query_embedding: list[float],
    page_filters: list[dict],
    top_k: int,
) -> list[dict]:
    """Handles both section_id (gdoc) and page (file upload) filters."""
    if not page_filters:
        return []

    def _build_clause(pf: dict) -> dict:
        clauses = [{"upload_id": {"$eq": pf["upload_id"]}}]
        if "section_id" in pf:
            clauses.append({"section_id": {"$eq": pf["section_id"]}})
        elif "page" in pf:
            clauses.append({"page": {"$eq": pf["page"]}})
        return {"$and": clauses}

    if len(page_filters) > 1:
        filter_dict = {"$or": [_build_clause(pf) for pf in page_filters]}
    else:
        filter_dict = _build_clause(page_filters[0])

    results = _get_index().query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.PINECONE_NAMESPACE_CHUNKS,
        filter=filter_dict,
    )

    return [
        {
            "id": match["id"],
            "text": match["metadata"].get("text", ""),
            "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
            "score": round(match["score"], 4),
        }
        for match in results["matches"]
    ]


def get_all_documents() -> list[dict]:
    return []
