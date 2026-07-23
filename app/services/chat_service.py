import json
import logging
import urllib.request
from sqlalchemy.orm import Session

from app.core.config import GEMINI_API_KEY
from app.repositories.product_repository import list_active_products_safe
from app.schemas.chat import ChatResponse, RecommendedProductSummary
from app.schemas.search import SearchResult
from app.services.search_service import search_products

logger = logging.getLogger("ai-service.chat")


def format_products_context(search_results: list[SearchResult]) -> str:
    if not search_results:
        return "Không tìm thấy sản phẩm nào phù hợp trong kho."

    context_lines = []
    for idx, prod in enumerate(search_results, start=1):
        price_str = (
            f"{prod.discounted_price:,} VNĐ"
            if prod.discounted_price
            else (f"{prod.original_price:,} VNĐ" if prod.original_price else "Liên hệ")
        )
        cat = prod.category_name or "Khác"
        brand = prod.brand or "Khác"
        rating = f"{prod.average_rating:.1f}⭐" if prod.average_rating else "Chưa có đánh giá"
        context_lines.append(
            f"{idx}. [{prod.title}] - ID: {prod.product_id} | Danh mục: {cat} | Thương hiệu: {brand} | Giá: {price_str} | Đánh giá: {rating}"
        )

    return "\n".join(context_lines)


def generate_gemini_reply(user_message: str, products_context: str) -> str | None:
    """Invoke Google Gemini REST API with strict RAG context and system prompt."""
    if not GEMINI_API_KEY.strip():
        return None

    system_prompt = (
        "Bạn là Chuyên gia Tư vấn Mua sắm Công nghệ AI của hệ thống E-commerce.\n"
        "Nhiệm vụ của bạn là tư vấn thân thiện, ngắn gọn, chuyên nghiệp bằng tiếng Việt dựa TRỰC TIẾP trên danh sách sản phẩm trong kho bên dưới.\n"
        "QUY TẮC BẮT BUỘC:\n"
        "1. Chỉ gợi ý các sản phẩm có trong danh sách kho được cung cấp.\n"
        "2. Không tự bịa ra tên sản phẩm hoặc thông số không có trong danh sách.\n"
        "3. Đêu rõ ưu điểm chính của sản phẩm được chọn phù hợp với nhu cầu người dùng.\n\n"
        f"DANH SÁCH SẢN PHẨM TRONG KHO:\n{products_context}\n"
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY.strip()}"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f"{system_prompt}\nNhu cầu khách hàng: {user_message}"}
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.4,
            "maxOutputTokens": 600,
        },
    }

    try:
        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            candidates = res_data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
    except Exception as exc:
        logger.warning("Gemini API call failed (%s). Falling back to rule-based assistant.", exc)

    return None


def generate_fallback_reply(user_message: str, search_results: list[SearchResult]) -> str:
    """Deterministic, natural Vietnamese AI shopping advice fallback when LLM API key is absent or offline."""
    if not search_results:
        return (
            "Chào bạn! Rất tiếc hiện tại cửa hàng chưa tìm thấy sản phẩm đáp ứng chính xác nhu cầu này của bạn. "
            "Bạn có thể thử tìm kiếm lại với các từ khóa nhu cầu khác như 'laptop 16gb', 'tai nghe chống ồn' hoặc 'chuột không dây' nhé!"
        )

    reply_parts = [
        f"Chào bạn! Dựa trên nhu cầu '{user_message}', AI Service xin gợi ý các sản phẩm phù hợp nhất dành cho bạn:"
    ]

    for idx, prod in enumerate(search_results, start=1):
        price_str = (
            f"{prod.discounted_price:,} VNĐ"
            if prod.discounted_price
            else (f"{prod.original_price:,} VNĐ" if prod.original_price else "Liên hệ")
        )
        brand_info = f" ({prod.brand})" if prod.brand else ""
        reply_parts.append(
            f"🔹 {idx}. **{prod.title}**{brand_info}\n"
            f"   - Giá ưu đãi: {price_str}\n"
            f"   - Đánh giá: {prod.average_rating:.1f}⭐"
        )

    reply_parts.append(
        "\n💡 *Mẹo:* Bạn có thể nhấp trực tiếp vào danh sách sản phẩm gợi ý bên dưới để xem chi tiết thông số và đặt hàng!"
    )

    return "\n\n".join(reply_parts)


def process_chat_consultation(
    message: str,
    limit: int = 4,
    db: Session | None = None,
) -> ChatResponse:
    """Main RAG Chat Pipeline combining Hybrid Search retrieval and LLM/Fallback generation."""
    active_products = list_active_products_safe(db)
    search_results = search_products(products=active_products, query=message, limit=limit)

    products_context = format_products_context(search_results)
    reply = generate_gemini_reply(user_message=message, products_context=products_context)

    if not reply:
        reply = generate_fallback_reply(user_message=message, search_results=search_results)

    recommended_summaries = [
        RecommendedProductSummary(
            product_id=res.product_id,
            title=res.title,
            category_id=res.category_id,
            category_name=res.category_name,
            brand=res.brand,
            original_price=res.original_price,
            discounted_price=res.discounted_price,
            average_rating=res.average_rating,
            image_url=res.image_url,
        )
        for res in search_results
    ]

    return ChatResponse(
        reply=reply,
        recommended_products=recommended_summaries,
    )
