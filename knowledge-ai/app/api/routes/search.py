
from functools import lru_cache

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.embedding import EmbeddingService
from app.services.vector_store import VectorStore


router = APIRouter(prefix="/search", tags=["Semantic Search"])


@lru_cache(maxsize=1)
def get_embedding_service():
    return EmbeddingService()


@lru_cache(maxsize=1)
def get_vector_store():
    return VectorStore()


class SearchRequest(BaseModel):

    question: str = Field(min_length=3, max_length=2000)

    top_k: int = Field(default=5, ge=1, le=20)


@router.post("/")
async def semantic_search(request: SearchRequest):

    try:

        embedding_service = get_embedding_service()
        vector_store = get_vector_store()

        query_embedding = (
            embedding_service.generate_query_embedding(
                request.question
            )
        )

        results = vector_store.search(
            query_embedding=query_embedding,
            top_k=request.top_k
        )

        return {
            "success": True,
            "question": request.question,
            "total_results": len(results),
            "results": results
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(error)}"
        )
