from services.page_index import two_stage_retrieve
from services.llm import generate_answer, build_sources
from models.schemas import QueryResponse, RetrievalMeta


def retrieve_and_answer(question: str, upload_ids: list[str] | None) -> QueryResponse:
    chunks, pages_identified = two_stage_retrieve(question, upload_ids)

    answer = generate_answer(question, chunks)
    sources = build_sources(chunks)

    return QueryResponse(
        answer=answer,
        sources=sources,
        retrieval_meta=RetrievalMeta(
            pages_identified=pages_identified,
            chunks_retrieved=len(chunks),
            strategy="two-stage PageIndex",
        ),
    )