import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

import risk_agent
from catalog import CATALOG
from db import initialize_database
from decision_agent import decide
from models import AnalysisResponse, OrderInput

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pre-Failure Order Intelligence Engine",
    description="Decision-first order risk analysis with bilingual JSON output.",
    version="0.2.0",
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.on_event("startup")
def startup() -> None:
    try:
        initialize_database()
        logger.info("Postgres tables ready and product catalog seeded")
    except Exception as exc:
        logger.warning("Postgres startup skipped: %s", exc)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    response = {
        "risk_score": 0.0,
        "confidence": 0.0,
        "issue": "normal",
        "decision": "escalate",
        "message_en": "We need a support review because key order details are missing.",
        "message_ar": "نحتاج إلى مراجعة من فريق الدعم لأن بعض تفاصيل الطلب الأساسية غير متوفرة.",
        "alternative_product": None,
        "risk_factors": [],
    }
    logger.info(
        "risk_score=%.3f issue=%s decision=%s confidence=%.3f",
        0.0, "normal", "escalate", 0.0,
    )
    return JSONResponse(status_code=200, content=response)


@app.post("/analyze-order", response_model=AnalysisResponse)
async def analyze_order(order: OrderInput) -> dict:
    order_dict = order.model_dump()

    risk_output = risk_agent.analyze(order_dict)
    logger.info(
        "risk_score=%.3f issue=%s confidence=%.3f",
        risk_output["risk_score"], risk_output["issue"], risk_output["confidence"],
    )

    final = decide(order_dict, risk_output, CATALOG)
    logger.info(
        "risk_score=%.3f issue=%s decision=%s confidence=%.3f",
        final["risk_score"], final["issue"], final["decision"], final["confidence"],
    )

    return final
