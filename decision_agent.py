"""Decision Agent — decides action and generates bilingual messages using Gemini LLM."""

import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

try:
    from google import genai
except ModuleNotFoundError:
    genai = None

logger = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = (
    "You are an AI order intelligence engine.\n"
    "Return ONLY valid JSON. Do not include explanations.\n"
    "Rules:\n"
    "- Do not hallucinate products\n"
    "- Use only provided catalog\n"
    "- If uncertain, escalate\n"
    "- Arabic must be natural, not literal\n"
    "- Keep messages concise and helpful"
)

SCHEMA_KEYS = {
    "risk_score",
    "confidence",
    "issue",
    "decision",
    "message_en",
    "message_ar",
    "alternative_product",
    "risk_factors",
}


def _filter_catalog(catalog: list, category: str, current_name: str | None = None) -> list:
    current = (current_name or "").strip().lower()
    return [
        p for p in catalog
        if p["category"] == category
        and p["availability"] == "in_stock"
        and p["name"].strip().lower() != current
    ]


def decide_from_score(risk_score: float, confidence: float, issue: str) -> str:
    if issue == "normal" and risk_score < 0.4:
        return "none"
    if risk_score >= 0.75:
        return "notify_and_offer_alternative"
    if 0.4 <= risk_score <= 0.6:
        return "monitor"
    if risk_score >= 0.5:
        return "notify"
    if confidence < 0.75 and issue != "normal":
        return "escalate"
    return "none"


def _default_messages(
    order: dict, decision: str, alt: str | None
) -> tuple[str | None, str | None]:
    name = order.get("product_name", "your product")
    if decision == "notify_and_offer_alternative" and alt:
        return (
            f"Your {name} order may be delayed. We can offer {alt} as an available alternative.",
            f"قد يتأخر طلب {name}. يمكننا توفير {alt} كبديل متاح.",
        )
    if decision == "notify":
        return (
            f"Your {name} order may need attention. We will keep you updated.",
            f"قد يحتاج طلب {name} إلى متابعة. سنبقيك على اطلاع.",
        )
    if decision == "escalate":
        return (
            "We are sending this order to support for a quick review.",
            "سنرسل هذا الطلب إلى فريق الدعم لمراجعته بسرعة.",
        )
    if decision == "monitor":
        return None, None
    return ("Your order is progressing normally.", "طلبك يسير بشكل طبيعي.")


def _build_prompt(order: dict, risk: dict, decision: str, filtered: list) -> str:
    payload = {
        "system_instruction": SYSTEM_INSTRUCTION,
        "order_data": order,
        "computed_risk_score": risk["risk_score"],
        "computed_confidence": risk["confidence"],
        "decision": decision,
        "issue": risk["issue"],
        "filtered_catalog_same_category_only": filtered,
        "required_output_schema": {
            "risk_score": "float", "confidence": "float",
            "issue": "normal | minor_delay | delay | severe_delay | cancellation_risk",
            "decision": "notify | notify_and_offer_alternative | monitor | escalate | none",
            "message_en": "string", "message_ar": "string",
            "alternative_product": "string or null",
            "risk_factors": [{"factor": "string", "impact": "float"}],
        },
        "hard_constraints": [
            "Return JSON only.",
            "Do not change risk_score, confidence, issue, or decision.",
            "Decision is already computed by decide_from_score and must not be changed.",
            "alternative_product must be null or one of the provided catalog names.",
            "Do not add any extra fields.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def _parse_json(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
    if fence:
        cleaned = fence.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        obj = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if obj:
            return json.loads(obj.group(0))
        raise


def _enforce_guardrails(
    candidate: dict,
    risk: dict,
    decision: str,
    filtered: list,
    deterministic_alt: str | None,
) -> dict:
    allowed_names = {p["name"] for p in filtered}
    candidate["risk_score"] = risk["risk_score"]
    candidate["confidence"] = risk["confidence"]
    candidate["issue"] = risk["issue"]
    candidate["decision"] = decision
    candidate["risk_factors"] = risk.get("risk_factors", [])
    alt = candidate.get("alternative_product")
    if alt and alt not in allowed_names:
        logger.warning("Gemini returned invalid alternative: %s", alt)
    candidate["alternative_product"] = deterministic_alt
    return {k: candidate[k] for k in SCHEMA_KEYS if k in candidate}


def decide(order: dict, risk_output: dict, catalog: list) -> dict:
    """Decide action and generate bilingual response. Uses Gemini LLM with deterministic fallback."""
    logger.debug("Using decision_agent.decide")
    score = risk_output["risk_score"]
    conf = risk_output["confidence"]
    issue = risk_output["issue"]
    decision = decide_from_score(score, conf, issue)

    filtered = _filter_catalog(catalog, order.get("product_type", ""), order.get("product_name"))
    alt = filtered[0]["name"] if filtered and decision == "notify_and_offer_alternative" else None

    msg_en, msg_ar = _default_messages(order, decision, alt)
    fallback = {
        "risk_score": score, "confidence": conf, "issue": issue,
        "decision": decision, "message_en": msg_en, "message_ar": msg_ar,
        "alternative_product": alt,
        "risk_factors": risk_output.get("risk_factors", []),
    }

    api_key = os.getenv("GEMINI_API_KEY")
    api_key = api_key.strip() if api_key else None

    logger.info("Gemini .env path: %s", ENV_PATH)
    logger.info("Gemini key loaded: %s", bool(api_key))
    

    if not api_key:
        return fallback

    if decision not in {"notify", "notify_and_offer_alternative", "escalate"}:
        return fallback

    if genai is None:
        return fallback

    prompt = _build_prompt(order, risk_output, decision, filtered)

    for attempt in range(2):
        try:
            client = genai.Client(api_key=api_key)
            resp = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            parsed = _parse_json(resp.text)
            result = _enforce_guardrails(parsed, risk_output, decision, filtered, alt)

            for k in fallback:
                if k not in result:
                    result[k] = fallback[k]

            return result

        except Exception as e:
            logger.warning("Gemini attempt %d failed: %s", attempt + 1, e)

            msg = str(e)
            if (
                "API_KEY_INVALID" in msg
                or "API key not valid" in msg
                or "INVALID_ARGUMENT" in msg
                or "RESOURCE_EXHAUSTED" in msg
                or "NOT_FOUND" in msg
                or "429" in msg
                or "404" in msg
            ):
                logger.warning("Gemini unavailable; returning deterministic fallback.")
                return fallback

            prompt += "\n\nPrevious response was invalid. Return only valid JSON."

    return fallback
