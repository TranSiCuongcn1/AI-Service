from fastapi import FastAPI

from app.routes.health import router as health_router
from app.routes.products import router as products_router
from app.routes.search import router as search_router


app = FastAPI(
    title="AI Service",
    description="AI service for ecommerce product search, recommendation, and chatbot.",
    version="0.1.0",
)

app.include_router(health_router, prefix="/api/v1/ai", tags=["health"])
app.include_router(products_router, prefix="/api/v1/ai", tags=["products"])
app.include_router(search_router, prefix="/api/v1/ai", tags=["search"])


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "ai-service",
        "message": "Open /docs for API documentation.",
    }
