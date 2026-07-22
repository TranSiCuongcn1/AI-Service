from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.product_repository import list_active_products_safe
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import search_products

router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(request: SearchRequest, db: Session = Depends(get_db)) -> SearchResponse:
    products = list_active_products_safe(db)
    results = search_products(products=products, query=request.query, limit=request.limit)

    return SearchResponse(
        query=request.query,
        results=results,
    )
