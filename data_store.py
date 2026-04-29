import logging
from difflib import SequenceMatcher

from catalog import CATALOG, products_by_category as synthetic_products_by_category
from db import get_connection

logger = logging.getLogger(__name__)


def normalize_text(text: str | None) -> str:
    return (text or "").strip().lower()


def normalize_category(category: str | None) -> str:
    if not category:
        return ""
    category = category.strip().lower()
    category = category.replace("-", "_")
    return category


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def products_by_category(category: str | None) -> list[dict]:
    category = normalize_category(category)
    if not category:
        return []

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT product_id, name, category, availability
                    FROM products
                    WHERE category = %s
                    """,
                    (category,),
                )
                rows = cur.fetchall()
                if rows:
                    return [_product_from_row(row) for row in rows]
    except Exception as exc:
        logger.warning("Product category lookup failed, using synthetic fallback: %s", exc)

    return synthetic_products_by_category(category)


def get_product(name: str | None, category: str | None) -> dict | None:
    name = normalize_text(name)
    category = normalize_category(category)
    products = products_by_category(category)

    if not name or not products:
        return None

    for product in products:
        if normalize_text(product["name"]) == name:
            return {**product, "_match_type": "exact"}

    for product in products:
        product_name = normalize_text(product["name"])
        if name in product_name or product_name in name:
            return {**product, "_match_type": "partial"}

    best_match = None
    best_score = 0.0
    for product in products:
        product_name = normalize_text(product["name"])
        score = similarity(name, product_name)
        if score > best_score:
            best_score = score
            best_match = product

    if best_score >= 0.6:
        return {**best_match, "_match_type": "fuzzy"}

    return None


def get_alternatives(category: str, exclude_name: str | None = None) -> list[dict]:
    category = normalize_category(category)
    exclude_name = normalize_text(exclude_name)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT product_id, name, category, availability
                    FROM products
                    WHERE category = %s
                    AND availability = 'in_stock'
                    AND LOWER(name) <> LOWER(%s)
                    """,
                    (category, exclude_name),
                )
                return [_product_from_row(row) for row in cur.fetchall()]
    except Exception as exc:
        logger.warning("Alternative lookup failed, using synthetic fallback: %s", exc)
        return [
            product
            for product in CATALOG
            if product["category"] == category
            and product["availability"] == "in_stock"
            and normalize_text(product["name"]) != exclude_name
        ]


def get_product_delay_rate(category: str) -> float:
    category = normalize_category(category)
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT AVG(
                        CASE
                            WHEN delay_days <= 0 THEN 0.0
                            WHEN delay_days >= 3 THEN 1.0
                            ELSE delay_days / 3.0
                        END
                    )
                    FROM orders
                    WHERE category = %s
                    """,
                    (category,),
                )
                value = cur.fetchone()[0]
                if value is None:
                    return 0.2
                return round(max(0.0, min(1.0, float(value))), 3)
    except Exception as exc:
        logger.warning("Delay rate lookup failed, using default: %s", exc)
        return 0.2


def get_customer_risk(customer_history: str | None) -> float:
    return {
        "new": 0.1,
        "frequent_buyer": 0.3,
        "complainant": 0.6,
    }.get(normalize_text(customer_history) or "new", 0.1)


def _product_from_row(row: tuple) -> dict:
    product_id, name, category, availability = row
    return {
        "product_id": product_id,
        "name": name,
        "category": category,
        "availability": availability,
    }
