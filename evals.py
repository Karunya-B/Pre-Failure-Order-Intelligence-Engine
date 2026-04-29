from pydantic import ValidationError

import decision_agent
import risk_agent
from catalog import CATALOG
from models import OrderInput


TEST_CASES = [
    {
        "name": "normal toys in stock",
        "expected_positive": False,
        "input": {
            "order_id": "EVAL-001", "product_type": "toys",
            "product_name": "Rainbow Rattle Set", "days_since_order": 1,
            "expected_delivery_days": 3, "inventory_status": "high",
            "region": "Dubai", "customer_history": "new",
        },
    },
    {
        "name": "critical delayed formula",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-002", "product_type": "baby_formula",
            "product_name": "Gentle Start Infant Formula 400g", "days_since_order": 6,
            "expected_delivery_days": 2, "inventory_status": "low",
            "region": "Abu Dhabi", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "medium risk diapers",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-003", "product_type": "diapers",
            "product_name": "DryNest Diapers Size 3 Jumbo", "days_since_order": 3,
            "expected_delivery_days": 3, "inventory_status": "medium",
            "region": "Riyadh", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "stroller delayed low stock",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-004", "product_type": "stroller",
            "product_name": "TrailLite Travel Stroller", "days_since_order": 7,
            "expected_delivery_days": 4, "inventory_status": "low",
            "region": "Doha", "customer_history": "new",
        },
    },
    {
        "name": "formula low stock not delayed",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-005", "product_type": "baby_formula",
            "product_name": "Comfort Care Follow-On Formula 800g", "days_since_order": 1,
            "expected_delivery_days": 3, "inventory_status": "low",
            "region": "Dubai", "customer_history": "new",
        },
    },
    {
        "name": "baby food normal",
        "expected_positive": False,
        "input": {
            "order_id": "EVAL-006", "product_type": "baby_food",
            "product_name": "PurePear Baby Food Pouches", "days_since_order": 1,
            "expected_delivery_days": 2, "inventory_status": "high",
            "region": "Dubai", "customer_history": "new",
        },
    },
    {
        "name": "wipes delayed medium stock",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-007", "product_type": "wipes",
            "product_name": "Sensitive Care Wipes Travel Pack", "days_since_order": 5,
            "expected_delivery_days": 3, "inventory_status": "medium",
            "region": "Abu Dhabi", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "unknown catalog product escalates",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-008", "product_type": "diapers",
            "product_name": "Mystery Diaper Pack", "days_since_order": 2,
            "expected_delivery_days": 2, "inventory_status": "high",
            "region": "Riyadh", "customer_history": "new",
        },
    },
    {
        "name": "missing field adversarial",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-009", "product_type": "baby_formula",
            "product_name": "Gentle Start Infant Formula 400g", "days_since_order": 4,
            "inventory_status": "low", "region": "Dubai", "customer_history": "new",
        },
    },
    {
        "name": "vague etc input",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-010", "product_type": "etc",
            "product_name": "Need baby item", "days_since_order": 2,
            "expected_delivery_days": 3, "inventory_status": "medium",
            "region": "Doha", "customer_history": "new",
        },
    },
    {
        "name": "car seat low stock frequent",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-011", "product_type": "car_seat",
            "product_name": "SnugRide Infant Car Seat", "days_since_order": 3,
            "expected_delivery_days": 4, "inventory_status": "low",
            "region": "Dubai", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "skincare normal",
        "expected_positive": False,
        "input": {
            "order_id": "EVAL-012", "product_type": "skincare",
            "product_name": "TenderTouch Baby Lotion", "days_since_order": 1,
            "expected_delivery_days": 2, "inventory_status": "high",
            "region": "Abu Dhabi", "customer_history": "new",
        },
    },
    {
        "name": "bottles delayed high stock",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-013", "product_type": "bottles",
            "product_name": "EasyLatch Feeding Bottle 250ml", "days_since_order": 5,
            "expected_delivery_days": 2, "inventory_status": "high",
            "region": "Riyadh", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "nursing low stock",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-014", "product_type": "nursing",
            "product_name": "CalmFlow Breast Pump Kit", "days_since_order": 2,
            "expected_delivery_days": 3, "inventory_status": "low",
            "region": "Doha", "customer_history": "new",
        },
    },
    {
        "name": "diapers delayed high stock",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-015", "product_type": "diapers",
            "product_name": "CloudFit Diapers Size 1 Pack", "days_since_order": 5,
            "expected_delivery_days": 3, "inventory_status": "high",
            "region": "Dubai", "customer_history": "frequent_buyer",
        },
    },
    {
        "name": "toys low stock but not urgent",
        "expected_positive": True,
        "input": {
            "order_id": "EVAL-016", "product_type": "toys",
            "product_name": "Soft Blocks Activity Kit", "days_since_order": 2,
            "expected_delivery_days": 3, "inventory_status": "low",
            "region": "Riyadh", "customer_history": "frequent_buyer",
        },
    },
]


ESCALATION_RESPONSE = {
    "risk_score": 0.0, "confidence": 0.0, "issue": "normal",
    "decision": "escalate", "message_en": "Insufficient data.",
    "message_ar": "بيانات غير كافية.", "alternative_product": None,
}


def run_case(case: dict) -> dict:
    try:
        order = OrderInput.model_validate(case["input"])
        order_dict = order.model_dump()
        risk_output = risk_agent.analyze(order_dict)
        response = decision_agent.decide(order_dict, risk_output, CATALOG)
    except ValidationError:
        response = ESCALATION_RESPONSE

    return {
        "name": case["name"],
        "expected_positive": case["expected_positive"],
        "predicted_positive": response["decision"] != "none",
        "decision": response["decision"],
        "risk_score": response["risk_score"],
        "confidence": response["confidence"],
    }


def compute_metrics(results: list[dict]) -> dict:
    tp = sum(r["expected_positive"] and r["predicted_positive"] for r in results)
    fp = sum(not r["expected_positive"] and r["predicted_positive"] for r in results)
    tn = sum(not r["expected_positive"] and not r["predicted_positive"] for r in results)
    fn = sum(r["expected_positive"] and not r["predicted_positive"] for r in results)

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    fp_rate = fp / (fp + tn) if fp + tn else 0.0
    fn_rate = fn / (fn + tp) if fn + tp else 0.0

    return {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "false_positives": fp,
        "false_negatives": fn,
        "false_positive_rate": round(fp_rate, 3),
        "false_negative_rate": round(fn_rate, 3),
        "target_fp_lt_15_pct": fp_rate < 0.15,
    }


def main() -> None:
    results = [run_case(case) for case in TEST_CASES]
    metrics = compute_metrics(results)

    print("=" * 70)
    print("  PRE-FAILURE ORDER INTELLIGENCE ENGINE — EVALUATION SUITE")
    print("=" * 70)

    for i, r in enumerate(results, 1):
        ok = r["expected_positive"] == r["predicted_positive"]
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {i:02d}. {r['name']:<35s} "
            f"score={r['risk_score']:.3f}  decision={r['decision']}"
        )

    print("-" * 70)
    print("  METRICS")
    print("-" * 70)
    print(f"  Precision ............ {metrics['precision']:.3f}")
    print(f"  Recall ............... {metrics['recall']:.3f}")
    print(f"  False positives ...... {metrics['false_positives']}")
    print(f"  False negatives ...... {metrics['false_negatives']}")
    print(f"  FP rate .............. {metrics['false_positive_rate']:.1%}")
    print(f"  FN rate .............. {metrics['false_negative_rate']:.1%}")
    print(f"  FP < 15% target ...... {'MET' if metrics['target_fp_lt_15_pct'] else 'NOT MET'}")
    print(f"  FN = 0 target ........ {'MET' if metrics['false_negatives'] == 0 else 'NOT MET'}")
    print("=" * 70)


if __name__ == "__main__":
    main()
