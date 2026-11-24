"""Bookings -> seven-day product demand -> time-ordered stock projection (t2).

`forecast()` keeps the signature and `ForecastLine` shape app.py already uses, so
the t6 swap is an import change. Inbound stock counts once, at its ETA, and only
when it lands before the window ends. A delivery at the same minute as a booking
is available to that booking.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Iterable, Optional

from iris.data import DEMO_NOW, HORIZON_DAYS, PRODUCTS, load_recipes


@dataclass
class ForecastLine:
    sku: str
    usage: float  # booked usage in the window, base units
    on_hand: float  # confirmed on-hand at `now`
    incoming: float  # all pending inbound for the SKU
    uncovered: float  # deepest projected deficit = amount to buy
    first_at_risk: Optional[dict]  # first booking that can't be served
    at_risk: list[dict]  # every booking that can't be served
    contributing: dict  # service -> booking count
    series: list[tuple[datetime, float]]  # projected level after each event
    incoming_by_date: dict = field(default_factory=dict)  # eta -> qty (inside the window)


@dataclass
class BookingIssue:
    booking_id: str
    problem: str


def _recipe(recipes: dict, service: str) -> Optional[dict]:
    r = recipes.get(service)
    return r["recipe"] if r else None


def booking_issues(bookings: Iterable[dict], recipes: Optional[dict] = None) -> list[BookingIssue]:
    """Live bookings whose service has no recipe (they can't be forecast)."""
    recipes = recipes or load_recipes()
    return [BookingIssue(b["id"], f"no recipe for service '{b['service']}'")
            for b in bookings if b.get("status") == "booked" and _recipe(recipes, b["service"]) is None]


def forecast(on_hand: dict, pending: list, bookings: list[dict], now: datetime = DEMO_NOW,
             days: int = HORIZON_DAYS, recipes: Optional[dict] = None, skus: Optional[Iterable[str]] = None,
             ) -> dict[str, ForecastLine]:
    """Time-ordered projection per SKU. `pending` items need .sku, .qty, .eta (orders.InboundLine)."""
    recipes = recipes or load_recipes()
    end = now + timedelta(days=days)
    live = sorted((b for b in bookings if b.get("status") == "booked" and now <= b["time"] < end
                   and _recipe(recipes, b["service"]) is not None), key=lambda b: (b["time"], b["id"]))
    out = {}
    for sku in (skus or PRODUCTS):
        events = [(b["time"], 1, -float(_recipe(recipes, b["service"]).get(sku, 0)), b) for b in live
                  if _recipe(recipes, b["service"]).get(sku)]
        inbound = [(p.eta, 0, float(p.qty), None) for p in pending if p.sku == sku and now <= p.eta < end]
        # deliveries already due before `now` should have been received into on-hand
        events = sorted(events + inbound, key=lambda e: (e[0], e[1]))
        start = float(on_hand.get(sku, 0.0))
        level, low = start, min(0.0, start)
        series, at_risk, contributing, by_date = [(now, level)], [], {}, {}
        for t, _, delta, b in events:
            level += delta
            series.append((t, level))
            if b is None:
                by_date[t] = by_date.get(t, 0.0) + delta
                continue
            contributing[b["service"]] = contributing.get(b["service"], 0) + 1
            if level < 0:
                at_risk.append(b)
            low = min(low, level)
        out[sku] = ForecastLine(
            sku=sku,
            usage=sum(-d for _, _, d, b in events if b is not None),
            on_hand=start,
            incoming=sum(float(p.qty) for p in pending if p.sku == sku),
            uncovered=max(0.0, round(-low, 1)),
            first_at_risk=at_risk[0] if at_risk else None,
            at_risk=at_risk,
            contributing=contributing,
            series=series,
            incoming_by_date=by_date,
        )
    return out


def shortages(fc: dict[str, ForecastLine]) -> list[dict]:
    """Forecast lines with uncovered demand, in the shape iris.agent.Shortage takes."""
    return [{
        "sku": l.sku,
        "required_qty": l.uncovered,
        "need_by": l.first_at_risk["time"],
        "first_at_risk_booking_id": l.first_at_risk["id"],
        "affected_booking_ids": [b["id"] for b in l.at_risk],
        "weekly_demand": l.usage,
        "on_hand": l.on_hand,
        "inbound": l.incoming,
    } for l in fc.values() if l.uncovered > 0 and l.first_at_risk]


def protected_bookings(before: dict[str, ForecastLine], after: dict[str, ForecastLine],
                       recipes: Optional[dict] = None) -> tuple[int, float]:
    """Bookings at risk before an order but not after, counted once, and their booking revenue."""
    recipes = recipes or load_recipes()
    was = {b["id"]: b for l in before.values() for b in l.at_risk}
    still = {b["id"] for l in after.values() for b in l.at_risk}
    saved = [b for i, b in was.items() if i not in still]
    return len(saved), float(sum(recipes.get(b["service"], {}).get("price", 0) for b in saved))
