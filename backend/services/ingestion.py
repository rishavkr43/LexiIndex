import fitz
import pandas as pd
from io import BytesIO
from uuid import uuid4
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.core.config import settings


def _get_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ".", " ", ""],
    )


def _chunk_page(text: str, metadata: dict) -> list[dict]:
    splitter = _get_splitter()
    chunks = splitter.split_text(text)
    return [
        {
            "id": str(uuid4()),
            "text": chunk,
            "metadata": {**metadata, "chunk_index": i},
        }
        for i, chunk in enumerate(chunks)
        if chunk.strip()
    ]


def parse_pdf(file_bytes: bytes, filename: str, upload_id: str) -> tuple[list[dict], list[dict]]:
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    all_chunks = []
    page_texts = []

    for page_num, page in enumerate(doc, start=1):
        text = page.get_text().strip()
        if not text:
            continue

        page_texts.append({
            "page": page_num,
            "text": text,
            "source_file": filename,
            "upload_id": upload_id,
        })

        chunks = _chunk_page(text, {
            "source_file": filename,
            "upload_id": upload_id,
            "page": page_num,
            "file_type": "pdf",
        })
        all_chunks.extend(chunks)

    return all_chunks, page_texts


def parse_txt(file_bytes: bytes, filename: str, upload_id: str) -> tuple[list[dict], list[dict]]:
    text = file_bytes.decode("utf-8", errors="ignore")
    lines = text.split("\n")
    page_size = 50
    pages = [lines[i:i+page_size] for i in range(0, len(lines), page_size)]

    all_chunks = []
    page_texts = []

    for page_num, page_lines in enumerate(pages, start=1):
        page_text = "\n".join(page_lines).strip()
        if not page_text:
            continue

        page_texts.append({
            "page": page_num,
            "text": page_text,
            "source_file": filename,
            "upload_id": upload_id,
        })

        chunks = _chunk_page(page_text, {
            "source_file": filename,
            "upload_id": upload_id,
            "page": page_num,
            "file_type": "txt",
        })
        all_chunks.extend(chunks)

    return all_chunks, page_texts


def parse_csv(file_bytes: bytes, filename: str, upload_id: str) -> tuple[list[dict], list[dict]]:
    df = pd.read_csv(BytesIO(file_bytes))
    rows_per_page = 20
    all_chunks = []
    page_texts = []

    for page_num, start in enumerate(range(0, len(df), rows_per_page), start=1):
        chunk_df = df.iloc[start:start+rows_per_page]
        page_text = "\n".join(
            ", ".join(f"{col}: {val}" for col, val in row.items())
            for _, row in chunk_df.iterrows()
        )

        if not page_text.strip():
            continue

        page_texts.append({
            "page": page_num,
            "text": page_text,
            "source_file": filename,
            "upload_id": upload_id,
        })

        chunks = _chunk_page(page_text, {
            "source_file": filename,
            "upload_id": upload_id,
            "page": page_num,
            "file_type": "csv",
        })
        all_chunks.extend(chunks)

    return all_chunks, page_texts


def parse_excel(file_bytes: bytes, filename: str, upload_id: str) -> tuple[list[dict], list[dict]]:
    df = pd.read_excel(BytesIO(file_bytes))
    rows_per_page = 20
    all_chunks = []
    page_texts = []

    for page_num, start in enumerate(range(0, len(df), rows_per_page), start=1):
        chunk_df = df.iloc[start:start+rows_per_page]
        page_text = "\n".join(
            ", ".join(f"{col}: {val}" for col, val in row.items())
            for _, row in chunk_df.iterrows()
        )

        if not page_text.strip():
            continue

        page_texts.append({
            "page": page_num,
            "text": page_text,
            "source_file": filename,
            "upload_id": upload_id,
        })

        chunks = _chunk_page(page_text, {
            "source_file": filename,
            "upload_id": upload_id,
            "page": page_num,
            "file_type": "xlsx",
        })
        all_chunks.extend(chunks)

    return all_chunks, page_texts


PARSERS = {
    "pdf": parse_pdf,
    "txt": parse_txt,
    "csv": parse_csv,
    "xlsx": parse_excel,
    "xls": parse_excel,
}


def ingest(file_bytes: bytes, filename: str, upload_id: str) -> tuple[list[dict], list[dict]]:
    ext = filename.rsplit(".", 1)[-1].lower()
    parser = PARSERS.get(ext)
    if not parser:
        raise ValueError(f"Unsupported file type: .{ext}")
    return parser(file_bytes, filename, upload_id)