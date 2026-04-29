from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


ProductType = Literal[
    "baby_formula",
    "diapers",
    "toys",
    "stroller",
    "baby_food",
    "wipes",
    "bottles",
    "nursing",
    "skincare",
    "car_seat",
    "etc",
]
InventoryStatus = Literal["high", "medium", "low"]
Region = Literal["Dubai", "Abu Dhabi", "Riyadh", "Doha"]
CustomerHistory = Literal["new", "frequent_buyer", "complainant"]
Decision = Literal["notify", "notify_and_offer_alternative", "monitor", "escalate", "none"]
Issue = Literal[
    "normal",
    "minor_delay",
    "delay",
    "severe_delay",
    "cancellation_risk",
]

class RiskFactor(BaseModel):
    factor: str
    impact: float = Field(ge=0, le=1)


class OrderInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    order_id: str = Field(min_length=1)
    product_type: ProductType
    product_name: str = Field(min_length=1)
    days_since_order: float = Field(ge=0)
    expected_delivery_days: float = Field(gt=0)
    inventory_status: InventoryStatus
    region: Region
    customer_history: CustomerHistory

    @field_validator("product_type", mode="before")
    @classmethod
    def normalize_product_type(cls, value: str) -> str:
        if not value:
            return ""
        return value.strip().lower().replace("-", "_")

    @field_validator("product_name", mode="before")
    @classmethod
    def normalize_product_name(cls, value: str) -> str:
        if not value:
            return ""
        return value.strip().lower()

    @field_validator("inventory_status", "customer_history", mode="before")
    @classmethod
    def normalize_simple_text(cls, value: str) -> str:
        if not value:
            return ""
        return value.strip().lower()


class Product(BaseModel):
    product_id: str
    name: str
    category: str
    availability: Literal["in_stock", "low_stock"]


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    risk_score: float = Field(ge=0, le=1)
    confidence: float = Field(ge=0, le=1)
    issue: Issue
    decision: Decision
    message_en: Optional[str] = None
    message_ar: Optional[str] = None
    alternative_product: Optional[str] = None
    risk_factors: list[RiskFactor]
