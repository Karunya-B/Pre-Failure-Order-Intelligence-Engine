# Pre-Failure Order Intelligence Engine

A FastAPI backend prototype that detects order risk before customers contact support. It returns structured JSON with risk score, confidence, issue type, decision, bilingual messages, alternatives, and explainable risk factors.

## Problem Statement

Customers lose trust when baby and mother essentials are delayed, cancelled, or refunded late. This system predicts order risk early and decides whether to do nothing, monitor, notify, offer an alternative, or escalate before the customer contacts support.

## Key Features

- FastAPI `POST /analyze-order` endpoint
- Deterministic risk scoring
- Explainable `risk_factors`
- Confidence scoring
- Future risk simulation
- Internal `monitor` state for medium-risk orders
- Cancellation, minor-delay, delay, and severe-delay classification
- Catalog-safe alternative recommendation
- Optional Gemini bilingual message generation
- Deterministic fallback if Gemini is missing, invalid, quota-limited, or unavailable
- Optional Postgres data layer with in-memory/default fallback

## Architecture

```text
POST /analyze-order
-> Pydantic validation
-> risk_agent.analyze()
-> decision_agent.decide()
-> optional Gemini message generation
-> strict JSON response
```

`decision_engine.py` is deprecated and not used by the runtime path.

## Risk Scoring

Base score:

```text
criticality * 0.25
+ delay * 0.25
+ inventory * 0.30
+ customer_sensitivity * 0.20
```

Additional signals:

```text
+ product_delay_rate * 0.20
+ customer_risk * 0.20
```

Scores are clamped between `0` and `1`. The risk agent also simulates near-term future risk and uses the higher of current and future risk.

## Issue Classification

- `normal`: no current delay or cancellation signal
- `minor_delay`: delayed by less than one day
- `delay`: delayed by one to less than three days
- `severe_delay`: delayed by three or more days
- `cancellation_risk`: low inventory with elevated risk

## Decisions

- `none`: no action needed
- `monitor`: internal watch state for medium-risk orders
- `notify`: proactively notify the customer
- `notify_and_offer_alternative`: notify and suggest a same-category catalog alternative
- `escalate`: send to support when uncertainty or missing data requires review

`monitor` is internal; no customer message is sent, so `message_en` and `message_ar` are `null`.

## Environment Variables

Create a local `.env` from `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/mumzworld
```

Both values are optional:

- Missing or invalid `GEMINI_API_KEY` returns deterministic fallback messages.
- Missing `DATABASE_URL` falls back to the in-memory catalog and default risk signals.

The runtime loads `.env` from the project root. `.env.example` is only a template and is never used for runtime secrets.

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open:

```text
http://127.0.0.1:8000/docs
```

## Example Request

```json
{
  "order_id": "T07",
  "product_type": "baby_formula",
  "product_name": "gentle start formula",
  "days_since_order": 6,
  "expected_delivery_days": 2,
  "inventory_status": "low",
  "region": "Dubai",
  "customer_history": "frequent_buyer"
}
```

## Example Response

```json
{
  "risk_score": 1.0,
  "confidence": 0.82,
  "issue": "cancellation_risk",
  "decision": "notify_and_offer_alternative",
  "message_en": "Your gentle start formula order may be delayed. We can offer Gentle Start Infant Formula 400g as an available alternative.",
  "message_ar": "قد يتأخر طلب gentle start formula. يمكننا توفير Gentle Start Infant Formula 400g كبديل متاح.",
  "alternative_product": "Gentle Start Infant Formula 400g",
  "risk_factors": [
    {"factor": "critical_product", "impact": 0.25},
    {"factor": "delay_days", "impact": 0.25},
    {"factor": "low_inventory", "impact": 0.3}
  ]
}
```

## Run Test Cases

Start the server:

```bash
uvicorn main:app --reload
```

In another terminal:

```bash
python test_api_cases.py
```

The script sends eight requests to `http://127.0.0.1:8000/analyze-order`, prints each payload and response, compares expected fields, and summarizes pass/fail counts.

## Known Limitations

- `product_delay_rate` and `customer_risk` currently use rule-based defaults when no database history exists.
- There is no real historical learning yet.
- There is no full logistics, courier, warehouse, refund, or payment integration.
- Gemini is optional and depends on API key validity, quota, and model availability.
- This is a prototype, not a production logistics system.

## Future Improvements

- Store delivery outcomes and compute `product_delay_rate` dynamically.
- Compute `customer_risk` from complaints, cancellations, delays, and refunds.
- Train an ML model using historical outcomes.
- Add dashboard/frontend for monitoring risk queues.
- Add async DB layer, migrations, and Docker.
- Add scheduled monitoring for `monitor` state orders.
