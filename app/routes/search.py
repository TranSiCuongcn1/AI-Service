from fastapi import APIRouter

from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import search_products


router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    results = search_products(query=request.query, limit=request.limit)

    return SearchResponse(
        query=request.query,
        results=results,
    )

