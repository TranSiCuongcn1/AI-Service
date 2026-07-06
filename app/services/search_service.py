import json
import re

from app.schemas.product import Product
from app.schemas.search import SearchResult
from app.services.product_store import list_active_products


def normalize_text(value: str) -> str:
    return value.lower().strip()


def tokenize(query: str) -> list[str]:
    return [token for token in re.split(r"\s+", normalize_text(query)) if token]


def product_to_search_text(product: Product) -> str:
    searchable_parts: list[str] = [
        product.name,
        product.category,
        product.brand or "",
        product.description or "",
        " ".join(product.tags),
        json.dumps(product.specs, ensure_ascii=False),
    ]

    return normalize_text(" ".join(searchable_parts))


def calculate_keyword_score(product: Product, query_tokens: list[str]) -> int:
    search_text = product_to_search_text(product)
    score = 0

    for token in query_tokens:
        if token in search_text:
            score += 1

    return score


def search_products(query: str, limit: int) -> list[SearchResult]:
    query_tokens = tokenize(query)
    scored_results: list[tuple[int, Product]] = []

    for product in list_active_products():
        score = calculate_keyword_score(product, query_tokens)

        if score > 0:
            scored_results.append((score, product))

    scored_results.sort(key=lambda item: (-item[0], item[1].price or 0, item[1].name))

    return [
        SearchResult(
            product_id=product.product_id,
            name=product.name,
            category=product.category,
            brand=product.brand,
            price=product.price,
            score=score,
        )
        for score, product in scored_results[:limit]
    ]
