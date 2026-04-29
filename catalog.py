CATALOG = [
    {
        "product_id": "BF-001",
        "name": "Gentle Start Infant Formula 400g",
        "category": "baby_formula",
        "availability": "in_stock",
    },
    {
        "product_id": "BF-002",
        "name": "Comfort Care Follow-On Formula 800g",
        "category": "baby_formula",
        "availability": "low_stock",
    },
    {
        "product_id": "BF-003",
        "name": "Soft Tummy Toddler Milk 900g",
        "category": "baby_formula",
        "availability": "in_stock",
    },
    {
        "product_id": "DP-001",
        "name": "CloudFit Diapers Size 1 Pack",
        "category": "diapers",
        "availability": "in_stock",
    },
    {
        "product_id": "DP-002",
        "name": "DryNest Diapers Size 3 Jumbo",
        "category": "diapers",
        "availability": "low_stock",
    },
    {
        "product_id": "DP-003",
        "name": "NightSoft Diapers Size 5 Pack",
        "category": "diapers",
        "availability": "in_stock",
    },
    {
        "product_id": "DP-004",
        "name": "EcoHug Training Pants Medium",
        "category": "diapers",
        "availability": "in_stock",
    },
    {
        "product_id": "TY-001",
        "name": "Rainbow Rattle Set",
        "category": "toys",
        "availability": "in_stock",
    },
    {
        "product_id": "TY-002",
        "name": "Soft Blocks Activity Kit",
        "category": "toys",
        "availability": "low_stock",
    },
    {
        "product_id": "TY-003",
        "name": "Bedtime Plush Moon",
        "category": "toys",
        "availability": "in_stock",
    },
    {
        "product_id": "ST-001",
        "name": "MetroFold Compact Stroller",
        "category": "stroller",
        "availability": "in_stock",
    },
    {
        "product_id": "ST-002",
        "name": "TrailLite Travel Stroller",
        "category": "stroller",
        "availability": "low_stock",
    },
    {
        "product_id": "ST-003",
        "name": "TwinEase Double Stroller",
        "category": "stroller",
        "availability": "in_stock",
    },
    {
        "product_id": "FD-001",
        "name": "PurePear Baby Food Pouches",
        "category": "baby_food",
        "availability": "in_stock",
    },
    {
        "product_id": "FD-002",
        "name": "TinyHarvest Veggie Meals",
        "category": "baby_food",
        "availability": "low_stock",
    },
    {
        "product_id": "WL-001",
        "name": "WaterSoft Baby Wipes 6 Pack",
        "category": "wipes",
        "availability": "in_stock",
    },
    {
        "product_id": "WL-002",
        "name": "Sensitive Care Wipes Travel Pack",
        "category": "wipes",
        "availability": "low_stock",
    },
    {
        "product_id": "BT-001",
        "name": "EasyLatch Feeding Bottle 250ml",
        "category": "bottles",
        "availability": "in_stock",
    },
    {
        "product_id": "BT-002",
        "name": "WarmSip Anti-Colic Bottle Set",
        "category": "bottles",
        "availability": "in_stock",
    },
    {
        "product_id": "NM-001",
        "name": "CozyNest Nursing Pillow",
        "category": "nursing",
        "availability": "in_stock",
    },
    {
        "product_id": "NM-002",
        "name": "CalmFlow Breast Pump Kit",
        "category": "nursing",
        "availability": "low_stock",
    },
    {
        "product_id": "SK-001",
        "name": "TenderTouch Baby Lotion",
        "category": "skincare",
        "availability": "in_stock",
    },
    {
        "product_id": "SK-002",
        "name": "MildBubble Baby Wash",
        "category": "skincare",
        "availability": "in_stock",
    },
    {
        "product_id": "CR-001",
        "name": "SnugRide Infant Car Seat",
        "category": "car_seat",
        "availability": "low_stock",
    },
    {
        "product_id": "CR-002",
        "name": "GrowSafe Convertible Car Seat",
        "category": "car_seat",
        "availability": "in_stock",
    },
]


def products_by_category(category: str) -> list[dict]:
    return [product for product in CATALOG if product["category"] == category]


def available_alternatives(category: str, current_product_name: str | None = None) -> list[dict]:
    current = (current_product_name or "").strip().lower()
    return [
        product
        for product in products_by_category(category)
        if product["availability"] == "in_stock"
        and product["name"].strip().lower() != current
    ]


def is_catalog_product_name(name: str | None, category: str | None = None) -> bool:
    if not name:
        return False
    normalized = name.strip().lower()
    products = products_by_category(category) if category else CATALOG
    return any(product["name"].strip().lower() == normalized for product in products)
