from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    product_id: str
    name: str
    category: str
    brand: str | None = None
    price: float | None = None
    score: int


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]

