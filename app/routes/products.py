from fastapi import APIRouter, HTTPException

from app.schemas.product import (
    Product,
    ProductDeactivateResponse,
    ProductListResponse,
    ProductSyncResponse,
)
from app.services.product_store import (
    deactivate_product,
    list_active_products,
    upsert_product,
)


router = APIRouter()


@router.get("/products", response_model=ProductListResponse)
def get_products() -> ProductListResponse:
    products = list_active_products()

    return ProductListResponse(
        items=products,
        total=len(products),
    )


@router.post("/products/sync", response_model=ProductSyncResponse)
def sync_product(product: Product) -> ProductSyncResponse:
    action = upsert_product(product)

    return ProductSyncResponse(
        message="Product synced successfully",
        product_id=product.product_id,
        action=action,
    )


@router.patch("/products/{product_id}/deactivate", response_model=ProductDeactivateResponse)
def deactivate_product_by_id(product_id: str) -> ProductDeactivateResponse:
    was_deactivated = deactivate_product(product_id)

    if not was_deactivated:
        raise HTTPException(status_code=404, detail="Product not found")

    return ProductDeactivateResponse(
        message="Product deactivated successfully",
        product_id=product_id,
    )
