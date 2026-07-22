from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.product_repository import list_active_products_safe
from app.schemas.recommendation import RecommendationResponse
from app.services.recommendation_service import (
    recommend_accessories,
    recommend_similar_products,
)

router = APIRouter()


@router.get("/recommendations/similar/{product_id}", response_model=RecommendationResponse)
def get_similar_recommendations(
    product_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    products = list_active_products_safe(db)
    response = recommend_similar_products(products=products, target_product_id=product_id, limit=limit)

    if not response:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

    return response


@router.get("/recommendations/accessories/{product_id}", response_model=RecommendationResponse)
def get_accessory_recommendations(
    product_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    db: Session = Depends(get_db),
) -> RecommendationResponse:
    products = list_active_products_safe(db)
    response = recommend_accessories(products=products, target_product_id=product_id, limit=limit)

    if not response:
        raise HTTPException(status_code=404, detail=f"Product with ID {product_id} not found")

    return response
