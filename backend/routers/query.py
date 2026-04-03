from fastapi import APIRouter, HTTPException
from backend.services.retriever import retrieve_and_answer
from backend.models.schemas import QueryRequest, QueryResponse

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
async def query_documents(body: QueryRequest):
    question = body.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    if len(question) > 1000:
        raise HTTPException(status_code=400, detail="Question exceeds 1000 character limit.")

    try:
        return retrieve_and_answer(question, body.upload_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")