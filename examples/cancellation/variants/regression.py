# SYNTHETIC FIXTURE: deliberately wrong; never use as the approved implementation.
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
    if (not isinstance(order.status, str) or order.status not in {"pending", "shipped", "cancelled"}
            or type(order.days_since_purchase) is not int or order.days_since_purchase < 0
            or type(order.total_cents) is not int or order.total_cents <= 0):
        raise ValueError("invalid_order")
    if order.status == "cancelled":
        return Cancellation("cancelled", 0, None)
    if order.status == "shipped":
        return Cancellation("rejected", 0, "not_pending")
    if order.days_since_purchase >= 7:
        return Cancellation("rejected", 0, "window_expired")
    return Cancellation("cancelled", order.total_cents * 80 // 100, None)
