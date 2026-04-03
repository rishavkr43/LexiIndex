from fastapi import APIRouter, UploadFile, File, HTTPException
from uuid import uuid4
from backend.services.ingestion import ingest
from backend.services.indexer import add_chunks
from backend.services.page_index import build_page_index
from backend.models.schemas import UploadResponse

router = APIRouter()

ALLOWED_TYPES = {"pdf", "txt", "csv", "xlsx", "xls"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '.{ext}'. Accepted: {', '.join(ALLOWED_TYPES)}"
        )

    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File exceeds 20MB limit."
        )

    if not file_bytes.strip():
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    upload_id = str(uuid4())

    try:
        chunks, page_texts = ingest(file_bytes, file.filename, upload_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parsing failed: {str(e)}")

    if not chunks:
        raise HTTPException(
            status_code=422,
            detail="No extractable text found in the document."
        )

    try:
        chunks_created = add_chunks(chunks)
        build_page_index(page_texts)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

    return UploadResponse(
        upload_id=upload_id,
        document_name=file.filename,
        pages_processed=len(page_texts),
        chunks_created=chunks_created,
    )