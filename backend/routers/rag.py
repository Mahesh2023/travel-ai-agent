"""
RAG router for knowledge base queries
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from rag.retrieval import TravelRAGRetrieval

router = APIRouter()

class QueryRequest(BaseModel):
    query: str
    document_types: Optional[List[str]] = None
    filters: Optional[dict] = None

@router.post("/query")
async def query_knowledge_base(request: QueryRequest):
    """Query travel knowledge base using RAG"""
    try:
        rag = TravelRAGRetrieval()
        result = rag.query(
            query=request.query,
            document_types=request.document_types,
            filters=request.filters
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/embed")
async def embed_document(document_type: str, content: str, metadata: dict):
    """Embed and store document in vector database"""
    try:
        from rag.embeddings import TravelEmbeddings
        embeddings = TravelEmbeddings()
        result = embeddings.embed_and_store(
            document_type=document_type,
            content=content,
            metadata=metadata
        )
        return {"message": "Document embedded successfully", "id": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
