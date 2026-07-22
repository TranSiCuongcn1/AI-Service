import json
import logging
import re
import unicodedata

from app.schemas.product import Product
from app.schemas.search import SearchResult
from app.services.embedding_service import generate_embedding
from app.services.product_content import build_content_text, build_specs, build_tags

logger = logging.getLogger("ai-service.search")

MIN_TOKEN_LENGTH = 2
# "tai" is intentionally NOT a stopword because of "tai nghe" (headphones)
STOPWORDS = {
    "bang",
    "bi",
    "cac",
    "cho",
    "co",
    "cua",
    "de",
    "den",
    "duoc",
    "la",
    "mot",
    "nhung",
    "theo",
    "tu",
    "va",
    "voi",
}

CATEGORY_SYNONYMS = {
    "tai nghe": ["headphone", "tai nghe", "earphone", "airpods"],
    "laptop": ["laptop", "may tinh xach tay", "notebook", "macbook"],
    "dien thoai": ["phone", "dien thoai", "smartphone", "iphone", "samsung"],
    "chuot": ["mouse", "chuot"],
    "ban phim": ["keyboard", "ban phim"],
    "man hinh": ["monitor", "man hinh", "display"],
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.lower().strip())
    without_marks = "".join(
        char for char in normalized if not unicodedata.combining(char)
    )

    return without_marks.replace("đ", "d")


def tokenize(query: str) -> list[str]:
    tokens = re.split(r"[^0-9a-z]+", normalize_text(query))

    return list(
        dict.fromkeys(
            token
            for token in tokens
            if len(token) >= MIN_TOKEN_LENGTH and token not in STOPWORDS
        )
    )


def normalize_parts(parts: list[str]) -> str:
    return normalize_text(" ".join(part for part in parts if part))


def calculate_keyword_score(
    product: Product,
    query_tokens: list[str],
    raw_query: str = "",
) -> float:
    score = 0.0
    normalized_q = normalize_text(raw_query)
    norm_title = normalize_parts([product.title])
    norm_cat = normalize_parts([product.category_name or ""])
    norm_tags = normalize_parts(build_tags(product))

    # 1. Exact phrase matching boost (e.g. "tai nghe" matching title, category, or tags)
    if normalized_q and len(normalized_q) >= 3:
        if normalized_q in norm_title:
            score += 20.0
        elif normalized_q in norm_cat or normalized_q in norm_tags:
            score += 15.0

    # 2. Category Synonyms boost
    for cat_key, synonyms in CATEGORY_SYNONYMS.items():
        if cat_key in normalized_q:
            for syn in synonyms:
                if syn in norm_cat or syn in norm_title or syn in norm_tags:
                    score += 15.0
                    break

    # 3. Exact Word Token matching (prevents substring mismatch like "on" in "phong")
    weighted_fields = [
        (4, set(tokenize(product.title))),
        (3, set(tokenize(f"{product.category_name or ''} {product.brand or ''}"))),
        (3, set(tokenize(" ".join(build_tags(product))))),
        (
            1,
            set(
                tokenize(
                    f"{product.description or ''} {product.detailed_review or ''} {json.dumps(build_specs(product), ensure_ascii=False)}"
                )
            ),
        ),
    ]

    for token in query_tokens:
        for weight, field_tokens in weighted_fields:
            if token in field_tokens:
                score += weight

    return score


def calculate_cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0

    dot = sum(a * b for a, b in zip(v1, v2))
    norm_a = sum(a * a for a in v1) ** 0.5
    norm_b = sum(b * b for b in v2) ** 0.5

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot / (norm_a * norm_b))


def search_products(products: list[Product], query: str, limit: int) -> list[SearchResult]:
    """Hybrid Search combining Keyword Match Score and Dense Vector Cosine Similarity."""
    query_tokens = tokenize(query)

    query_vector: list[float] = []
    try:
        query_vector = generate_embedding(query)
    except Exception as exc:
        logger.warning("Could not generate query embedding for query '%s': %s", query, exc)

    scored_results: list[tuple[float, Product]] = []

    for product in products:
        kw_score = calculate_keyword_score(product, query_tokens, raw_query=query)

        vector_sim = 0.0
        if query_vector:
            product_text = build_content_text(product)
            try:
                prod_vector = generate_embedding(product_text)
                vector_sim = calculate_cosine_similarity(query_vector, prod_vector)
            except Exception:
                pass

        # Hybrid score formula
        hybrid_score = (kw_score * 1.5) + (vector_sim * 10.0 if vector_sim > 0.3 else 0.0)

        if hybrid_score > 0.5:
            scored_results.append((round(hybrid_score, 2), product))

    scored_results.sort(
        key=lambda item: (
            -item[0],
            -item[1].average_rating,
            -(item[1].quantity_sold or 0),
            item[1].discounted_price or item[1].original_price or 0,
            item[1].title,
        )
    )

    return [
        SearchResult(
            product_id=product.product_id,
            title=product.title,
            category_id=product.category_id,
            category_name=product.category_name,
            brand=product.brand,
            original_price=product.original_price,
            discounted_price=product.discounted_price,
            average_rating=product.average_rating,
            image_url=product.image_url,
            score=score,
        )
        for score, product in scored_results[:limit]
    ]
