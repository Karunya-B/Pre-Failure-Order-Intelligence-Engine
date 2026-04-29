import json
from typing import Any

import requests


BASE_URL = "http://127.0.0.1:8000/analyze-order"


TEST_CASES = [
    {
        "id": "T01",
        "name": "Safe toy order",
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
        "name": "Critical product, no delay",
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
        "expected": {"issue": "normal", "decision": "monitor", "monitor_messages_null": True},
    },
    {
        "id": "T03",
        "name": "Minor delay",
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
        "expected": {"issue": "minor_delay", "decision": "monitor", "monitor_messages_null": True},
    },
    {
        "id": "T04",
        "name": "Normal delay",
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
        "name": "Severe delay",
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
        "name": "Cancellation risk without delay",
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
        "name": "High-risk delayed formula",
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
        "name": "Unknown product confidence",
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
    {
        "id": "T09",
        "name": "Invalid product type",
        "payload": {
            "order_id": "T09",
            "product_type": "electronics",
            "product_name": "tablet",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"decision": "escalate"},
    },
    {
        "id": "T10",
        "name": "Low inventory toy",
        "payload": {
            "order_id": "T10",
            "product_type": "toys",
            "product_name": "Rainbow Rattle Set",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "low",
            "region": "Dubai",
            "customer_history": "new",
        },
        "expected": {"decision_any": {"monitor", "notify"}, "risk_factor": "low_inventory"},
    },
    {
        "id": "T11",
        "name": "Complainant delayed diapers",
        "payload": {
            "order_id": "T11",
            "product_type": "diapers",
            "product_name": "CloudFit Diapers Size 1 Pack",
            "days_since_order": 4,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "Dubai",
            "customer_history": "complainant",
        },
        "expected": {
            "issue": "delay",
            "decision_any": {"notify", "notify_and_offer_alternative"},
            "risk_factor_any": {"customer_sensitivity", "high_customer_risk"},
        },
    },
    {
        "id": "T12",
        "name": "Unsupported region",
        "payload": {
            "order_id": "T12",
            "product_type": "toys",
            "product_name": "Rainbow Rattle Set",
            "days_since_order": 1,
            "expected_delivery_days": 3,
            "inventory_status": "high",
            "region": "London",
            "customer_history": "new",
        },
        "expected": {"decision": "escalate"},
    },
]


def risk_factor_names(data: dict[str, Any]) -> set[str]:
    return {
        item.get("factor")
        for item in data.get("risk_factors", [])
        if isinstance(item, dict)
    }


def check_response(data: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    failures = []

    if not isinstance(data, dict):
        return ["response is not valid JSON object"]

    if not 0 <= data.get("risk_score", -1) <= 1:
        failures.append(f"risk_score out of range: {data.get('risk_score')}")
    if not 0 <= data.get("confidence", -1) <= 1:
        failures.append(f"confidence out of range: {data.get('confidence')}")
    if "risk_factors" not in data or not isinstance(data["risk_factors"], list):
        failures.append("risk_factors missing or not a list")

    for key, expected_value in expected.items():
        if key == "issue_any":
            if data.get("issue") not in expected_value:
                failures.append(f"issue expected one of {sorted(expected_value)}, got {data.get('issue')}")
        elif key == "decision_any":
            if data.get("decision") not in expected_value:
                failures.append(f"decision expected one of {sorted(expected_value)}, got {data.get('decision')}")
        elif key == "confidence_lt":
            if not data.get("confidence", 1) < expected_value:
                failures.append(f"confidence expected < {expected_value}, got {data.get('confidence')}")
        elif key == "risk_factor":
            if expected_value not in risk_factor_names(data):
                failures.append(f"risk_factors expected to include {expected_value}")
        elif key == "risk_factor_any":
            names = risk_factor_names(data)
            if not names.intersection(expected_value):
                failures.append(f"risk_factors expected one of {sorted(expected_value)}, got {sorted(names)}")
        elif key == "monitor_messages_null":
            if expected_value and (data.get("message_en") is not None or data.get("message_ar") is not None):
                failures.append("monitor decision should return null customer messages")
        elif data.get(key) != expected_value:
            failures.append(f"{key} expected {expected_value}, got {data.get(key)}")

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

        try:
            data = response.json()
        except ValueError:
            print("FAIL: response is not valid JSON")
            print(response.text)
            continue

        print("Response:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if response.status_code != 200:
            print(f"FAIL: expected HTTP 200, got {response.status_code}")
            continue

        failures = check_response(data, case["expected"])
        if failures:
            print("FAIL:")
            for failure in failures:
                print(f"- {failure}")
            continue

        print("PASS")
        passed += 1

    print("=" * 80)
    print(f"Summary: Passed {passed}/{len(TEST_CASES)}")


if __name__ == "__main__":
    run_tests()
