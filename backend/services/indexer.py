from pinecone import Pinecone, ServerlessSpec
from core.config import settings
from services.embedder import embedder

_pc = None
_index = None

# In-memory document registry — resets on restart, sufficient for assessment
_document_registry: dict[str, dict] = {}


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
            "metadata": {**metadatas[i], "text": texts[i]}
        }
        for i in range(len(ids))
    ]

    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        _get_index().upsert(
            vectors=vectors[i:i + batch_size],
            namespace=settings.PINECONE_NAMESPACE_CHUNKS
        )

    # Register document in memory
    first_meta = metadatas[0]
    uid = first_meta["upload_id"]
    if uid not in _document_registry:
        _document_registry[uid] = {
            "upload_id": uid,
            "document_name": first_meta["source_file"],
            "file_type": first_meta["file_type"],
            "pages": set(),
            "chunks": 0,
        }
    for meta in metadatas:
        _document_registry[uid]["pages"].add(meta["page"])
        _document_registry[uid]["chunks"] += 1

    return len(chunks)


def add_page_summary(summary_id: str, summary_text: str, metadata: dict):
    embedding = embedder.embed_one(summary_text)
    _get_index().upsert(
        vectors=[{
            "id": summary_id,
            "values": embedding,
            "metadata": {**metadata, "text": summary_text}
        }],
        namespace=settings.PINECONE_NAMESPACE_PAGES
    )


def query_page_index(query_embedding: list[float], upload_ids: list[str] | None, top_k: int) -> list[dict]:
    filter_dict = {"upload_id": {"$in": upload_ids}} if upload_ids else None

    results = _get_index().query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.PINECONE_NAMESPACE_PAGES,
        filter=filter_dict
    )

    return [
        {
            "id": match["id"],
            "text": match["metadata"].get("text", ""),
            "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
            "score": round(match["score"], 4)
        }
        for match in results["matches"]
    ]


def query_chunks(query_embedding: list[float], page_filters: list[dict], top_k: int) -> list[dict]:
    if not page_filters:
        return []

    if len(page_filters) > 1:
        filter_dict = {
            "$or": [
                {"$and": [
                    {"upload_id": {"$eq": pf["upload_id"]}},
                    {"page": {"$eq": pf["page"]}}
                ]}
                for pf in page_filters
            ]
        }
    else:
        filter_dict = {
            "$and": [
                {"upload_id": {"$eq": page_filters[0]["upload_id"]}},
                {"page": {"$eq": page_filters[0]["page"]}}
            ]
        }

    results = _get_index().query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        namespace=settings.PINECONE_NAMESPACE_CHUNKS,
        filter=filter_dict
    )

    return [
        {
            "id": match["id"],
            "text": match["metadata"].get("text", ""),
            "metadata": {k: v for k, v in match["metadata"].items() if k != "text"},
            "score": round(match["score"], 4)
        }
        for match in results["matches"]
    ]


def get_all_documents() -> list[dict]:
    return [
        {**v, "pages": len(v["pages"])}
        for v in _document_registry.values()
    ]