# SYNTHETIC FIXTURE: equivalent local refactor.
"""Pure synthetic cancellation model; no payments or persistence."""
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Order:
    status: str
    days_since_purchase: int
    total_cents: int


@dataclass(frozen=True)
class Cancellation:
    status: str
    refund_cents: int
    error: Optional[str]


def cancel_order(order: Order) -> Cancellation:
    purchase = order
    if (not isinstance(purchase.status, str) or purchase.status not in {"pending", "shipped", "cancelled"}
            or type(purchase.days_since_purchase) is not int or purchase.days_since_purchase < 0
            or type(purchase.total_cents) is not int or purchase.total_cents <= 0):
        raise ValueError("invalid_order")
    if purchase.status == "cancelled":
        return Cancellation("cancelled", 0, None)
    if purchase.status == "shipped":
        return Cancellation("rejected", 0, "not_pending")
    if purchase.days_since_purchase > 7:
        return Cancellation("rejected", 0, "window_expired")
    return Cancellation("cancelled", purchase.total_cents, None)
