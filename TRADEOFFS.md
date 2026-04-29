# Tradeoffs

## Data & Signals

- **Synthetic data only**: product catalog, order inputs, and evaluation cases are fabricated. Production requires real catalog governance and order history.
- **No real logistics feed**: scoring uses provided request fields instead of carrier tracking, warehouse events, or fulfillment SLA feeds.
- **Snapshot inventory**: `inventory_status` is a static label. Production should ingest real-time stock levels and reorder pipelines.

## Risk & Accuracy

- **False positives risk**: proactive notifications can worry customers if the signal is weak. Current weights are tuned to eliminate false negatives at the expense of potentially more notifications.
- **Deterministic guardrails first**: the LLM generates bilingual messages, but product suggestions and decisions are constrained by local rules — the model cannot override risk scores or invent products.
- **Weight tuning was manual**: weights (0.25/0.25/0.30/0.20) were calibrated against 16 evaluation cases. A production system should use historical order outcomes to learn optimal weights.

## Language Quality

- **Arabic quality depends on model**: Gemini generates natural Arabic messages when available. Production should add human review, QA, or templates for sensitive/escalated cases.
- **Fallback messages are templates**: when the Gemini API key is absent or the model fails, the system returns English/Arabic template strings — functional but less natural.

## Production Readiness

- **Need real-time system in production**: production should ingest inventory, courier SLA, payment, cancellation, and refund status continuously via event streaming.
- **In-memory catalog only**: a real system needs catalog governance, availability freshness, and category taxonomy management.
- **No authentication or rate limiting**: the prototype API is open. Production requires auth, throttling, and audit logging.
- **Single retry on LLM failure**: the system retries once on invalid JSON from Gemini, then falls back to deterministic output. Production may need more sophisticated retry/circuit-breaker patterns.
