from fastapi import APIRouter, HTTPException
from services.indexer import get_all_documents
from models.schemas import DocumentInfo

router = APIRouter()


@router.get("/documents", response_model=list[DocumentInfo])
async def list_documents():
    try:
        docs = get_all_documents()
        return [DocumentInfo(**d) for d in docs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")