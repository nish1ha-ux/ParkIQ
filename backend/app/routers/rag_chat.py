from fastapi import APIRouter, HTTPException
from app.schemas.schemas import RAGQueryRequest, RAGQueryResponse
from app.services.rag_engine import rag_engine

router = APIRouter(prefix="/rag", tags=["RAG Knowledge Assistant"])

@router.post("/chat", response_model=RAGQueryResponse)
def chat_with_rag_assistant(req: RAGQueryRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    result = rag_engine.query(req.question.strip())
    return RAGQueryResponse(**result)
