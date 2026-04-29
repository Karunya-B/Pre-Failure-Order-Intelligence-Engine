# Pre-Failure Order Intelligence Engine

A decision-first FastAPI prototype for Mumzworld-style e-commerce that detects risky orders before customers contact support. It returns structured JSON with risk score, confidence, issue type, decision, bilingual messages, alternative product suggestions, and explainable risk factors.

## Problem Statement

Mumzworld sells baby and mother essentials where delays or cancellations can quickly damage customer trust. This project identifies risky orders early and decides whether to do nothing, monitor internally, notify the customer, offer an alternative, or escalate.

## Key Features

- FastAPI backend
- Minimal frontend demo served at `/`
- Swagger docs at `/docs`
- Deterministic risk scoring
- Explainable risk factors
- Confidence scoring
- Future risk simulation
- Monitor state for medium-risk orders
- Minor delay, delay, severe delay, and cancellation risk classification
- Catalog-safe alternative recommendation
- Optional Gemini-powered bilingual English/Arabic message generation
- Deterministic fallback messages if Gemini is unavailable
- Optional Postgres support with in-memory/default fallback

## Architecture

```text
Frontend `/`
-> POST `/analyze-order`
-> Pydantic validation
-> risk_agent.analyze()
-> decision_agent.decide()
-> optional Gemini bilingual message generation
-> strict JSON response
```

Gemini does not decide `risk_score`, `confidence`, `issue`, `decision`, `alternative_product`, or `risk_factors`. Those fields are deterministic and guarded. Gemini only improves customer-facing message text when available.

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
product_delay_rate * 0.20
customer_risk * 0.20
```

Scores are clamped between `0` and `1`.

## Issue Types

- `normal`: no current delay or cancellation signal
- `minor_delay`: delayed by less than one day
- `delay`: delayed by one to less than three days
- `severe_delay`: delayed by three or more days
- `cancellation_risk`: low inventory with elevated risk

## Decisions

- `none`: no proactive action needed
- `monitor`: internal watch state for medium-risk orders
- `notify`: proactively notify the customer
- `notify_and_offer_alternative`: notify and suggest a same-category catalog alternative
- `escalate`: send to support when uncertainty or invalid input requires review

`monitor` is internal, so `message_en` and `message_ar` are returned as `null`.

## Environment Variables

Create `.env` from `.env.example`:

```env
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://user:password@localhost:5432/mumzworld
```

- `GEMINI_API_KEY` is optional.
- If the Gemini key is missing, invalid, quota-limited, or model-unavailable, deterministic fallback messages are used.
- `DATABASE_URL` is optional.
- If the database is unavailable, the app falls back to in-memory/default catalog and risk signals.

## Run Locally

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open frontend:

```text
http://127.0.0.1:8000/
```

Open Swagger:

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
  "issue": "severe_delay",
  "decision": "notify_and_offer_alternative",
  "message_en": "Your order may be delayed. We can offer an available alternative.",
  "message_ar": "قد يتأخر طلبك. يمكننا توفير بديل متاح.",
  "alternative_product": "Gentle Start Infant Formula 400g",
  "risk_factors": [
    {"factor": "critical_product", "impact": 0.25},
    {"factor": "delay_days", "impact": 0.25},
    {"factor": "low_inventory", "impact": 0.30}
  ]
}
```

## Run Test Cases

Start server:

```bash
uvicorn main:app --reload
```

In another terminal:

```bash
python test_api_cases.py
```

The test script sends 12 sample order payloads to `/analyze-order` and checks issue/decision outputs, validation fallback behavior, uncertainty behavior, and risk-factor quality.

## Evals

The system was evaluated with 12 API test cases covering:

- safe orders
- monitor decisions
- minor delays
- normal delays
- severe delays
- cancellation risk
- unknown products
- invalid product types
- unsupported regions
- complainant customers
- low inventory edge cases

### Rubric

Each case checks:

- valid JSON response
- correct issue classification
- correct decision
- `risk_score` between `0` and `1`
- `confidence` between `0` and `1`
- meaningful `risk_factors`
- no customer message for monitor decisions
- safe fallback for invalid inputs

### Test Summary Table

| Case | Scenario | Expected |
|---|---|---|
| T01 | Safe toy order | normal + none |
| T02 | Critical product, no delay | normal + monitor |
| T03 | Minor delay | minor_delay + monitor |
| T04 | Normal delay | delay + notify |
| T05 | Severe delay | severe_delay |
| T06 | Low inventory formula | cancellation_risk |
| T07 | High-risk delayed formula | notify_and_offer_alternative |
| T08 | Unknown product | lower confidence, no crash |
| T09 | Invalid product type | validation fallback / escalate |
| T10 | Low inventory toy | low_inventory risk factor |
| T11 | Complainant delayed diapers | higher customer sensitivity |
| T12 | Unsupported region | validation fallback / escalate |

Current eval result: run `python test_api_cases.py` after starting the server and update this line with `Passed X/12`.

### Known Eval Limitations

- `product_delay_rate` and `customer_risk` are rule-based defaults, not learned from real historical data.
- Some issue priority choices are subjective. For example, delayed low-inventory orders may be classified as either `severe_delay` or `cancellation_risk` depending on priority.
- Gemini output depends on key, quota, and model availability, so deterministic fallback messages are used for reliability.

## Tradeoffs

I chose a pre-failure order intelligence engine instead of a chatbot because order delay/cancellation risk is high-leverage for baby and mother e-commerce.

I used deterministic scoring instead of a neural model because the prototype has no real historical delivery outcomes. Rule-based scoring makes the system explainable, debuggable, and safe for a short take-home.

Gemini is optional and only used for bilingual message generation. Core decisions remain deterministic so the system still works without Gemini.

### What I Cut

- real warehouse integration
- real customer history learning
- ML training on order outcomes
- scheduled background monitoring
- full analytics dashboard

### What I Would Build Next

- real outcome storage
- dynamic `product_delay_rate`
- dynamic `customer_risk`
- ML model
- scheduled monitoring
- analytics dashboard

## Tooling

This project was built with heavy AI-assisted development.

Tools used:

- ChatGPT: problem framing, architecture planning, debugging, test-case design, README drafting, and reasoning through risk logic.
- Codex / AI coding assistant: code cleanup, frontend generation, deployment setup, and documentation updates.
- Gemini API: optional bilingual English/Arabic customer-facing message generation.
- FastAPI + Pydantic: API layer and structured validation.
- GitHub + Render or deployment platform: hosting/deployment.

How AI was used:

- pair-programming
- prompt iteration
- debugging logs
- generating initial code
- manually testing and modifying final logic

Where I overruled or modified AI output:

- Added `monitor` as an internal state instead of notifying customers too early.
- Made monitor messages `null`.
- Added `minor_delay` and `severe_delay`.
- Removed `high_inventory` from `risk_factors`.
- Kept Gemini out of deterministic decisions.
- Added fallback behavior for invalid/missing/quota-limited Gemini access.
- Fixed environment-variable loading to avoid stale system keys.

What worked:

- AI was useful for scaffolding FastAPI, frontend, evals, and documentation.

What did not work:

- Some generated code mixed old and new Gemini SDK styles.
- Some early eval expectations did not match final issue priority.
- Environment-variable loading needed manual debugging.

Final human decision:

Core risk scoring and decisions remain deterministic; Gemini is only a controlled text-generation layer.

## Deployment

Build command:

```bash
pip install -r requirements.txt
```

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Environment variables:

```text
GEMINI_API_KEY
DATABASE_URL
```

Frontend is served by FastAPI at `/`, so only one deployed service is required.

## Known Limitations

- `product_delay_rate` and `customer_risk` currently use rule-based defaults.
- The system does not yet learn from real historical delivery outcomes.
- No real warehouse, carrier, or logistics integration.
- Gemini output depends on API key, quota, and model availability.
- This is a prototype, not a production logistics system.

## Future Improvements

- Store real delivery outcomes and compute `product_delay_rate` dynamically.
- Compute `customer_risk` from complaints, cancellations, and delay history.
- Train logistic regression or gradient boosting on historical order outcomes.
- Add scheduled re-checking for monitor-state orders.
- Add dashboard analytics.
- Add Docker, migrations, and async DB access.

## Security Notes

- `.env` should never be committed.
- `.env.example` is safe to commit.
- API keys should be set through local `.env` or deployment platform environment variables.
- The app should not log full API keys.
