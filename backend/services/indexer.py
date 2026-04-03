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
                dimension=384,  # MiniLM 384-dim models (L3/L6)
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

    # Prepare vectors for Pinecone
    vectors = [
        {
            "id": ids[i],
            "values": embeddings[i],
            "metadata": {**metadatas[i], "text": texts[i]}
        }
        for i in range(len(ids))
    ]

    # Upsert in batches of 100
    batch_size = 100
    for i in range(0, len(vectors), batch_size):
        batch = vectors[i:i + batch_size]
        _get_index().upsert(vectors=batch, namespace=settings.PINECONE_NAMESPACE_CHUNKS)

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

    # Build Pinecone filter for multiple pages
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
    # Pinecone doesn't have a direct "get all" method, so we'll use stats
    # This is a limitation - we'll need to track documents separately
    # For now, return empty list (you could add a metadata tracking system)
    
    # Alternative: Query with a dummy vector and high top_k, then aggregate
    # But this is not ideal for large datasets
    
    # Better approach: Use a separate lightweight DB (like SQLite) for metadata
    # For now, returning empty to keep it simple
    return []
