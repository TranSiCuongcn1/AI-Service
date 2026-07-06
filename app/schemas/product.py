from typing import Any

from pydantic import BaseModel, Field


class Product(BaseModel):
    product_id: str
    name: str
    category: str
    brand: str | None = None
    price: float | None = None
    description: str | None = None
    specs: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    image_url: str | None = None
    is_active: bool = True


class ProductListResponse(BaseModel):
    items: list[Product]
    total: int


class ProductSyncResponse(BaseModel):
    message: str
    product_id: str
    action: str


class ProductDeactivateResponse(BaseModel):
    message: str
    product_id: str
