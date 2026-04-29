import json
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000/analyze-order"


TEST_CASES = [
    {
        "id": "T01",
        "name": "Safe Order",
        "payload": {
            "order_id": "T01",
            "product_type": "toys",
            "product_name": "Rainbow Rattle Set",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "normal", "decision": "none"},
    },
    {
        "id": "T02",
        "name": "Critical Product No Delay",
        "payload": {
            "order_id": "T02",
            "product_type": "baby_formula",
            "product_name": "Gentle Start Infant Formula 400g",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "normal", "decision": "monitor"},
    },
    {
        "id": "T03",
        "name": "Minor Delay",
        "payload": {
            "order_id": "T03",
            "product_type": "toys",
            "product_name": "Rainbow Rattle Set",
            "days_since_order": 3.5,
            "expected_delivery_days": 3,
            "inventory_status": "medium",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "minor_delay", "decision": "monitor"},
    },
    {
        "id": "T04",
        "name": "Normal Delay",
        "payload": {
            "order_id": "T04",
            "product_type": "diapers",
            "product_name": "CloudFit Diapers Size 1 Pack",
            "days_since_order": 4,
            "expected_delivery_days": 3,
            "inventory_status": "medium",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "delay", "decision": "notify"},
    },
    {
        "id": "T05",
        "name": "Severe Delay",
        "payload": {
            "order_id": "T05",
            "product_type": "diapers",
            "product_name": "CloudFit Diapers Size 1 Pack",
            "days_since_order": 7,
            "expected_delivery_days": 3,
            "inventory_status": "medium",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "severe_delay"},
    },
    {
        "id": "T06",
        "name": "Cancellation Risk Without Delay",
        "payload": {
            "order_id": "T06",
            "product_type": "baby_formula",
            "product_name": "Gentle Start Infant Formula 400g",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "low",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"issue": "cancellation_risk"},
    },
    {
        "id": "T07",
        "name": "High-Risk Delayed Formula",
        "payload": {
            "order_id": "T07",
            "product_type": "baby_formula",
            "product_name": "gentle start formula",
            "days_since_order": 6,
            "expected_delivery_days": 2,
            "inventory_status": "low",
            "region": "Dubai",
            "customer_history": "frequent_buyer",
        },
        "expected": {
            "issue_any": {"severe_delay", "cancellation_risk"},
            "decision": "notify_and_offer_alternative",
        },
    },
    {
        "id": "T08",
        "name": "Unknown Product",
        "payload": {
            "order_id": "T08",
            "product_type": "baby_formula",
            "product_name": "unknown powder tin",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"confidence_lt": 0.9},
    },
]


def check_response(data: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures = []

    for key, expected_value in expected.items():
        if key == "issue_any":
            if data.get("issue") not in expected_value:
                failures.append(f"issue expected one of {sorted(expected_value)}, got {data.get('issue')}")
        elif key == "confidence_lt":
            if not data.get("confidence", 1) < expected_value:
                failures.append(f"confidence expected < {expected_value}, got {data.get('confidence')}")
        elif data.get(key) != expected_value:
            failures.append(f"{key} expected {expected_value}, got {data.get(key)}")

    if "risk_factors" not in data or not isinstance(data["risk_factors"], list):
        failures.append("risk_factors missing or not a list")

    return failures


def run_tests() -> None:
    passed = 0

    for case in TEST_CASES:
        print("=" * 80)
        print(f"{case['id']} - {case['name']}")
        print("Payload:")
        print(json.dumps(case["payload"], indent=2))

        try:
            response = requests.post(BASE_URL, json=case["payload"], timeout=20)
        except requests.RequestException as exc:
            print("FAIL: request failed:", exc)
            continue

        print("Response:")
        print(json.dumps(response.json() if response.content else {}, indent=2, ensure_ascii=False))

        if response.status_code != 200:
            print(f"FAIL: expected HTTP 200, got {response.status_code}")
            continue

        data = response.json()
        failures = check_response(data, case["expected"])
        if failures:
            print("FAIL:")
            for failure in failures:
                print(f"- {failure}")
            continue

        print("PASS")
        passed += 1

    print("=" * 80)
    print(f"Summary: {passed}/{len(TEST_CASES)} passed")


if __name__ == "__main__":
    run_tests()
