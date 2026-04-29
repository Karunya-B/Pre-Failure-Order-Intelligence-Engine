# DEPRECATED — replaced by risk_agent.py

from models import OrderInput


PRODUCT_CRITICALITY = {
    "baby_formula": 1.0,
    "diapers": 0.8,
    "stroller": 0.6,
}
INVENTORY_RISK = {
    "low": 1.0,
    "medium": 0.6,
    "high": 0.2,
}
CUSTOMER_SENSITIVITY = {
    "frequent_buyer": 0.8,
    "new": 0.5,
}


def delay_factor(days_since_order: float, expected_delivery_days: float) -> float:
    if days_since_order <= expected_delivery_days:
        return 0.0
    return min(1.0, (days_since_order - expected_delivery_days) / 3)


def score_order(order: OrderInput) -> float:
    criticality = PRODUCT_CRITICALITY.get(order.product_type, 0.5)
    delay = delay_factor(order.days_since_order, order.expected_delivery_days)
    inventory = INVENTORY_RISK[order.inventory_status]
    sensitivity = CUSTOMER_SENSITIVITY[order.customer_history]

    score = (
        criticality * 0.25
        + delay * 0.25
        + inventory * 0.30
        + sensitivity * 0.20
    )
    return round(max(0.0, min(1.0, score)), 3)
