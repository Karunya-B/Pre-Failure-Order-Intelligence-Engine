import json
import logging
import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

try:
    from google import genai
except ModuleNotFoundError:
    genai = None

from catalog import available_alternatives
from catalog import CATALOG
from decision_agent import decide
from models import AnalysisResponse, OrderInput
from risk_agent import analyze

ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=True)

logger = logging.getLogger(__name__)
GEMINI_MODEL = "gemini-2.5-flash"

SYSTEM_INSTRUCTION = """You are an AI order intelligence engine.
Return ONLY valid JSON.
Do not include explanations.

Rules:
- Do not hallucinate products
- Use only provided catalog
- If uncertain, escalate
- Arabic must be natural, not literal
- Keep messages concise and helpful"""
def analyze_with_gemini(order: OrderInput) -> AnalysisResponse:
    order_dict = order.model_dump()

    # 1. Run your deterministic risk engine first
    risk_output = analyze(order_dict)

    # 2. Build baseline response from your decision engine
    baseline = AnalysisResponse.model_validate(
        decide(order_dict, risk_output, CATALOG)
    )

    if baseline.decision not in {"notify", "notify_and_offer_alternative", "escalate"}:
        return baseline

    # 4. Filter catalog alternatives
    filtered_catalog = available_alternatives(
        order.product_type,
        order.product_name
    )

    api_key = os.getenv("GEMINI_API_KEY")
    api_key = api_key.strip() if api_key else None
    logger.info("Gemini .env path: %s", ENV_PATH)
    logger.info("Gemini key loaded: %s", bool(api_key))

    if not api_key or genai is None:
        return baseline

    prompt = build_prompt(order, baseline, filtered_catalog)

    for _ in range(2):
        try:
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=prompt,
            )

            parsed = parse_json_response(response.text)
            guarded = enforce_guardrails(parsed, baseline, filtered_catalog)
            return AnalysisResponse.model_validate(guarded)

        except Exception as exc:
            logger.warning("Gemini client failed: %s", exc)
            prompt += "\n\nPrevious response was invalid. Return only valid JSON matching the schema."

    return baseline


def build_prompt(
    order: OrderInput, baseline: AnalysisResponse, filtered_catalog: list[dict[str, Any]]
) -> str:
    payload = {
        "system_instruction": SYSTEM_INSTRUCTION,
        "order_data": order.model_dump(),
        "computed_risk_score": baseline.risk_score,
        "computed_confidence": baseline.confidence,
        "decision": baseline.decision,
        "issue": baseline.issue,
        "filtered_catalog_same_category_only": filtered_catalog,
        "required_output_schema": {
            "risk_score": "float",
            "confidence": "float",
            "issue": "normal | minor_delay | delay | severe_delay | cancellation_risk",
            "decision": "notify | notify_and_offer_alternative | monitor | escalate | none",
            "message_en": "string",
            "message_ar": "string",
            "alternative_product": "string or null",
            "risk_factors": [{"factor": "string", "impact": "float"}],
        },
        "hard_constraints": [
            "Return JSON only.",
            "Do not change risk_score, confidence, issue, or decision.",
            "Decision is already computed by decide_from_score and must not be changed.",
            "alternative_product must be null or one of the provided catalog names.",
        ],
    }
    return json.dumps(payload, ensure_ascii=False)


def parse_json_response(text: str) -> dict[str, Any]:
    cleaned = text.strip()
    # Strip markdown code fences: ```json ... ```
    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Try to extract the first JSON object from the text
        obj_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if obj_match:
            return json.loads(obj_match.group(0))
        raise


def enforce_guardrails(
    candidate: dict[str, Any],
    baseline: AnalysisResponse,
    filtered_catalog: list[dict[str, Any]],
) -> dict[str, Any]:
    allowed_names = {product["name"] for product in filtered_catalog}
    alternative = candidate.get("alternative_product")

    if alternative and alternative not in allowed_names:
        candidate["message_en"] = baseline.message_en
        candidate["message_ar"] = baseline.message_ar

    candidate["risk_score"] = baseline.risk_score
    candidate["confidence"] = baseline.confidence
    candidate["issue"] = baseline.issue
    candidate["decision"] = baseline.decision
    candidate["alternative_product"] = baseline.alternative_product
    candidate["risk_factors"] = [factor.model_dump() for factor in baseline.risk_factors]
    return candidate
