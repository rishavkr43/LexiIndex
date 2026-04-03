from groq import Groq
from backend.core.config import settings
from backend.models.schemas import ChunkSource

_groq = Groq(api_key=settings.GROQ_API_KEY)

_SYSTEM_PROMPT = """You are a legal document assistant for a law firm.
You answer questions strictly based on the document context provided below.
Rules you must follow:
- Only use information present in the provided context.
- For every factual claim, cite the source document and page number in brackets, e.g. [case_file.pdf, p.4].
- If the answer is not found in the context, respond exactly with: "The information is not available in the uploaded documents."
- Do not speculate, infer beyond the text, or use external knowledge.
- Be concise and precise."""


def _build_context_block(chunks: list[dict]) -> str:
    blocks = []
    for c in chunks:
        meta = c["metadata"]
        label = f"[{meta['source_file']}, p.{meta['page']}]"
        blocks.append(f"{label}\n{c['text']}")
    return "\n\n---\n\n".join(blocks)


def generate_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "The information is not available in the uploaded documents."

    context = _build_context_block(chunks)
    user_message = f"Context:\n{context}\n\nQuestion: {question}"

    response = _groq.chat.completions.create(
        model=settings.LLM_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ],
        max_tokens=1024,
        temperature=0.1,
    )
    return response.choices[0].message.content.strip()


def build_sources(chunks: list[dict]) -> list[ChunkSource]:
    return [
        ChunkSource(
            text=c["text"],
            source_file=c["metadata"]["source_file"],
            page=c["metadata"]["page"],
            chunk_index=c["metadata"]["chunk_index"],
            score=c["score"],
        )
        for c in chunks
    ]