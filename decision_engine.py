# DEPRECATED — replaced by decision_agent.py

from catalog import available_alternatives, is_catalog_product_name
from models import AnalysisResponse, Decision, Issue, OrderInput
from risk_engine import delay_factor, score_order


def confidence_for_order(order: OrderInput) -> float:
    confidence = 0.95
    if not is_catalog_product_name(order.product_name, order.product_type):
        confidence -= 0.25
    if order.product_type == "etc":
        confidence -= 0.20
    if order.inventory_status == "medium":
        confidence -= 0.05
    return round(max(0.0, min(1.0, confidence)), 3)


def decide_from_score(risk_score: float, confidence: float,issue:str) -> Decision:
    if issue == "normal" and risk_score < 0.5:
        return "none"
    if confidence<0.75 and issue!="normal":
        return "escalate"
    if risk_score >= 0.75:
        return "notify_and_offer_alternative"
    return "none"


def issue_for_order(order: OrderInput, risk_score: float) -> Issue:
    if delay_factor(order.days_since_order, order.expected_delivery_days) > 0:
        return "delay"
    if order.inventory_status == "low" and risk_score >= 0.5:
        return "cancellation_risk"
    return "normal"


def deterministic_analysis(order: OrderInput) -> AnalysisResponse:
    risk_score = score_order(order)
    confidence = confidence_for_order(order)
    decision = decide_from_score(risk_score, confidence,issue)
    issue = issue_for_order(order, risk_score)

    alternatives = available_alternatives(order.product_type, order.product_name)
    alternative_product = None
    if decision == "notify_and_offer_alternative" and alternatives:
        alternative_product = alternatives[0]["name"]
   
    return AnalysisResponse(
        risk_score=risk_score,
        confidence=confidence,
        issue=issue,
        decision=decision,
        message_en=default_message_en(order, decision, alternative_product),
        message_ar=default_message_ar(order, decision, alternative_product),
        alternative_product=alternative_product,
        reason="low confidence" if confidence < 0.75 else None,
    )


def insufficient_data_response(reason: str = "insufficient data") -> AnalysisResponse:
    return AnalysisResponse(
        risk_score=0.0,
        confidence=0.0,
        issue="normal",
        decision="escalate",
        message_en="We need a support review because key order details are missing.",
        message_ar="نحتاج إلى مراجعة من فريق الدعم لأن بعض تفاصيل الطلب الأساسية غير متوفرة.",
        alternative_product=None,
        reason=reason,
    )


def default_message_en(
    order: OrderInput, decision: Decision, alternative_product: str | None
) -> str:
    if decision == "notify_and_offer_alternative" and alternative_product:
        return (
            f"Your {order.product_name} may be delayed .We're proactively addressing a potential delay.. "
            f"We can offer {alternative_product} as an available alternative."
        )
    if decision == "notify":
        return f"Your {order.product_name} order may need attention. We will keep you updated."
    if decision == "escalate":
        return "We are sending this order to support for a quick review."
    return "Your order is progressing normally."


def default_message_ar(
    order: OrderInput, decision: Decision, alternative_product: str | None
) -> str:
    if decision == "notify_and_offer_alternative" and alternative_product:
        return (
            f"قد يتأخر طلب {order.product_name}. "
            f"يمكننا توفير {alternative_product} كبديل متاح."
        )
    if decision == "notify":
        return f"قد يحتاج طلب {order.product_name} إلى متابعة. سنبقيك على اطلاع."
    if decision == "escalate":
        return "سنرسل هذا الطلب إلى فريق الدعم لمراجعته بسرعة."
    return "طلبك يسير بشكل طبيعي."
