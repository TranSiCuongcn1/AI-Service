import json
from pathlib import Path
from typing import Any

from app.schemas.product import Product


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTS_FILE = PROJECT_ROOT / "data" / "products.json"


def load_products() -> list[Product]:
    with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
        raw_products: list[dict[str, Any]] = json.load(file)

    return [Product(**product) for product in raw_products]


def save_products(products: list[Product]) -> None:
    raw_products = [product.model_dump() for product in products]

    with PRODUCTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(raw_products, file, ensure_ascii=False, indent=2)
        file.write("\n")


def list_active_products() -> list[Product]:
    return [product for product in load_products() if product.is_active]


def upsert_product(product: Product) -> str:
    products = load_products()

    for index, current_product in enumerate(products):
        if current_product.product_id == product.product_id:
            products[index] = product
            save_products(products)
            return "updated"

    products.append(product)
    save_products(products)
    return "created"


def deactivate_product(product_id: str) -> bool:
    products = load_products()

    for index, product in enumerate(products):
        if product.product_id == product_id:
            products[index] = product.model_copy(update={"is_active": False})
            save_products(products)
            return True

    return False
