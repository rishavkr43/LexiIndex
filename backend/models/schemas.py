from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class ChunkSource(BaseModel):
    text: str
    source_file: str
    page: int
    chunk_index: int
    score: float


class RetrievalMeta(BaseModel):
    pages_identified: list[str]
    chunks_retrieved: int
    strategy: str = "two-stage PageIndex"


class UploadResponse(BaseModel):
    upload_id: str
    document_name: str
    pages_processed: int
    chunks_created: int


class DocumentInfo(BaseModel):
    upload_id: str
    document_name: str
    file_type: str
    pages: int
    chunks: int


class QueryRequest(BaseModel):
    question: str
    upload_ids: Optional[list[str]] = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[ChunkSource]
    retrieval_meta: RetrievalMeta