import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.core.config import settings, CHROMA_PATH
from backend.services.embedder import embedder


client = chromadb.PersistentClient(
    path=str(CHROMA_PATH),
    settings=ChromaSettings(anonymized_telemetry=False),
)

chunks_col = client.get_or_create_collection(
    name=settings.CHUNKS_COLLECTION,
    metadata={"hnsw:space": "cosine"},
)

page_index_col = client.get_or_create_collection(
    name=settings.PAGE_INDEX_COLLECTION,
    metadata={"hnsw:space": "cosine"},
)


def add_chunks(chunks: list[dict]) -> int:
    if not chunks:
        return 0

    ids = [c["id"] for c in chunks]
    texts = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    embeddings = embedder.embed(texts)

    chunks_col.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
    )
    return len(chunks)


def add_page_summary(summary_id: str, summary_text: str, metadata: dict):
    embedding = embedder.embed_one(summary_text)
    page_index_col.upsert(
        ids=[summary_id],
        documents=[summary_text],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def query_page_index(query_embedding: list[float], upload_ids: list[str] | None, top_k: int) -> list[dict]:
    where = {"upload_id": {"$in": upload_ids}} if upload_ids else None
    results = page_index_col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, page_index_col.count() or 1),
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return _unpack(results)


def query_chunks(query_embedding: list[float], page_filters: list[dict], top_k: int) -> list[dict]:
    if not page_filters:
        return []

    where = {
        "$or": [
            {"$and": [
                {"upload_id": {"$eq": pf["upload_id"]}},
                {"page": {"$eq": pf["page"]}},
            ]}
            for pf in page_filters
        ]
    } if len(page_filters) > 1 else {
        "$and": [
            {"upload_id": {"$eq": page_filters[0]["upload_id"]}},
            {"page": {"$eq": page_filters[0]["page"]}},
        ]
    }

    results = chunks_col.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, chunks_col.count() or 1),
        where=where,
        include=["documents", "metadatas", "distances"],
    )
    return _unpack(results)


def get_all_documents() -> list[dict]:
    results = chunks_col.get(include=["metadatas"])
    seen = {}
    for meta in results["metadatas"]:
        uid = meta["upload_id"]
        if uid not in seen:
            seen[uid] = {
                "upload_id": uid,
                "document_name": meta["source_file"],
                "file_type": meta["file_type"],
                "pages": set(),
                "chunks": 0,
            }
        seen[uid]["pages"].add(meta["page"])
        seen[uid]["chunks"] += 1

    return [
        {**v, "pages": len(v["pages"])}
        for v in seen.values()
    ]


def _unpack(results: dict) -> list[dict]:
    out = []
    ids = results.get("ids", [[]])[0]
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for i, doc_id in enumerate(ids):
        out.append({
            "id": doc_id,
            "text": docs[i],
            "metadata": metas[i],
            "score": round(1 - distances[i], 4),
        })
    return out