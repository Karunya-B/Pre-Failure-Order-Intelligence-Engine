"""Risk Agent — deterministic risk scoring. No LLM usage."""

import logging

from data_store import (
    get_customer_risk,
    get_product,
    get_product_delay_rate,
    normalize_category,
    normalize_text,
)

logger = logging.getLogger(__name__)

PRODUCT_CRITICALITY = {
    "baby_formula": 1.0,
    "diapers": 0.8,
    "stroller": 0.6,
}
INVENTORY_RISK = {"low": 1.0, "medium": 0.6, "high": 0.2}
CUSTOMER_SENSITIVITY = {"frequent_buyer": 0.8, "new": 0.5}


def _delay_factor(days: float, expected: float) -> float:
    if days <= expected:
        return 0.0
    return min(1.0, (days - expected) / 3)


def _issue(order: dict, risk_score: float) -> str:
    delay_days = order["days_since_order"] - order["expected_delivery_days"]

    if order["inventory_status"] == "low" and risk_score >= 0.5:
        return "cancellation_risk"

    if delay_days <= 0:
        return "normal"

    if delay_days < 1:
        return "minor_delay"

    if delay_days < 3:
        return "delay"

    return "severe_delay"


def confidence_for_order(order: dict, product_exists: bool, match_type: str) -> float:
    confidence = 0.9
    if not product_exists:
        confidence -= 0.1
    elif match_type == "fuzzy":
        confidence -= 0.08
    elif match_type == "partial":
        confidence -= 0.03
    if order.get("inventory_status") == "medium":
        confidence -= 0.05
    return max(0.6, round(confidence, 2))


def simulate_future_risk(order: dict, base_risk: float) -> float:
    if base_risk < 0.5 and order.get("inventory_status") != "low":
        return base_risk

    scenarios = []

    scenarios.append(base_risk + 0.05)

    if order.get("inventory_status") == "low":
        scenarios.append(base_risk + 0.2)

    if order.get("customer_history") == "complainant":
        scenarios.append(base_risk + 0.2)

    if order.get("product_type") == "baby_formula":
        scenarios.append(base_risk + 0.15)

    return min(1.0, max(scenarios))


def build_risk_factors(
    order: dict,
    criticality: float,
    delay: float,
    inventory: float,
    sensitivity: float,
    product_delay_rate: float,
    customer_risk: float,
    risk_score: float,
    future_risk: float,
) -> list[dict]:
    factors = []

    product_factor = "critical_product" if criticality >= 0.8 else "product_criticality"
    factors.append({"factor": product_factor, 
                    "impact": round(criticality * 0.25, 2)})
    if delay > 0:
        factors.append({"factor": "delay_days", 
                        "impact": round(delay * 0.25, 2)})
    inventory_status = order.get("inventory_status", "unknown")

    if inventory_status in ["low", "medium"]:
        factors.append({
            "factor": f"{inventory_status}_inventory",
            "impact": round(inventory * 0.30, 2),
        })    
    if sensitivity > 0:
        factors.append({
            "factor": "customer_sensitivity",
            "impact": round(sensitivity * 0.20, 2)
        })
    if product_delay_rate > 0:
        factors.append({
            "factor": "category_delay_history",
            "impact": round(product_delay_rate * 0.20, 2)
        })
    if customer_risk > 0.1:
        factors.append({"factor": "high_customer_risk", 
                        "impact": round(customer_risk * 0.20, 2)})
    if future_risk > risk_score:
        factors.append({"factor": "future_risk_projection", 
                        "impact": round(future_risk - risk_score, 2)})

    return factors


def analyze(order: dict) -> dict:
    """Returns {risk_score, issue, confidence, reason}."""
    order = dict(order)
    order["product_type"] = normalize_category(order.get("product_type", ""))
    order["product_name"] = normalize_text(order.get("product_name", ""))

    ptype = order.get("product_type", "")
    product = get_product(order.get("product_name"), ptype)
    product_exists = True
    match_type = "exact"
    if not product:
        product_exists = False
        match_type = "unknown"
        product = {
            "name": order.get("product_name"),
            "category": order.get("product_type"),
            "availability": order.get("inventory_status"),
        }
    else:
        match_type = product.get("_match_type", "exact")

    crit = PRODUCT_CRITICALITY.get(order.get("product_type", ""), 0.3)
    delay = _delay_factor(order.get("days_since_order", 0), order.get("expected_delivery_days", 1))
    inv = INVENTORY_RISK.get(order.get("inventory_status", "high"), 0.2)
    sens = CUSTOMER_SENSITIVITY.get(order.get("customer_history", "new"), 0.5)
    product_delay_rate = get_product_delay_rate(order.get("product_type", ""))
    customer_risk = get_customer_risk(order.get("customer_history", "new"))

    base_score = crit * 0.25 + delay * 0.25 + inv * 0.30 + sens * 0.20
    risk_score = round(
        max(0.0, min(1.0, base_score + product_delay_rate * 0.20 + customer_risk * 0.20)),
        3,
    )
    # Only run the future-risk simulation when baseline risk is elevated
    # or inventory is low; otherwise future risk equals current risk.
    if risk_score >= 0.5 or order.get("inventory_status") == "low":
        future_risk = simulate_future_risk(order, risk_score)
        final_risk = max(risk_score, future_risk)
    else:
        future_risk = risk_score
        final_risk = risk_score
    issue = _issue(order, final_risk)
    conf = confidence_for_order(order, product_exists, match_type)
    risk_factors = build_risk_factors(
        order,
        crit,
        delay,
        inv,
        sens,
        product_delay_rate,
        customer_risk,
        risk_score,
        future_risk,
    )

    logger.debug("product_exists=%s", product_exists)
    logger.debug("match_type=%s", match_type)
    logger.debug("base_risk=%.3f", risk_score)
    logger.debug("future_risk=%.3f", future_risk)
    logger.debug("final_risk=%.3f", final_risk)
    logger.debug("product_delay_rate=%.3f", product_delay_rate)
    logger.debug("customer_risk=%.3f", customer_risk)

    reasons = []
    if delay > 0:
        reasons.append("delivery delayed")
    if product_delay_rate > 0.2:
        reasons.append("category delay history")
    if customer_risk >= 0.6:
        reasons.append("high customer risk")
    if inv >= 0.8:
        reasons.append("low inventory")
    if conf < 0.75:
        reasons.append("low confidence")
    if not reasons:
        reasons.append("within normal parameters")

    return {
        "risk_score": round(final_risk, 2),
        "future_risk_score": round(future_risk, 2),
        "issue": issue,
        "confidence": round(conf, 2),
        "risk_factors": risk_factors,
        "reason": "; ".join(reasons) if reasons else "No significant risk signals",
    }
