from uuid import uuid4
from groq import Groq
from backend.core.config import settings
from backend.services.indexer import add_page_summary, query_page_index, query_chunks
from backend.services.embedder import embedder


_groq = Groq(api_key=settings.GROQ_API_KEY)


def _summarize_page(page_text: str, source_file: str, page_num: int) -> str:
    prompt = (
        f"In one sentence, summarize what the following page from '{source_file}' (page {page_num}) covers. "
        f"Be specific about topics, names, dates, or legal concepts mentioned.\n\n"
        f"{page_text[:2000]}"
    )
    response = _groq.chat.completions.create(
        model=settings.SUMMARY_MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=120,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()


def build_page_index(page_texts: list[dict]):
    for page in page_texts:
        summary = _summarize_page(page["text"], page["source_file"], page["page"])
        summary_id = str(uuid4())
        add_page_summary(
            summary_id=summary_id,
            summary_text=summary,
            metadata={
                "upload_id": page["upload_id"],
                "source_file": page["source_file"],
                "page": page["page"],
            },
        )


def two_stage_retrieve(question: str, upload_ids: list[str] | None) -> tuple[list[dict], list[str]]:
    query_embedding = embedder.embed_one(question)

    stage1 = query_page_index(
        query_embedding=query_embedding,
        upload_ids=upload_ids,
        top_k=settings.TOP_K_PAGES,
    )

    pages_identified = [
        f"{r['metadata']['source_file']}:p{r['metadata']['page']}"
        for r in stage1
    ]

    page_filters = [
        {"upload_id": r["metadata"]["upload_id"], "page": r["metadata"]["page"]}
        for r in stage1
    ]

    stage2 = query_chunks(
        query_embedding=query_embedding,
        page_filters=page_filters,
        top_k=settings.TOP_K_CHUNKS,
    )

    return stage2, pages_identified