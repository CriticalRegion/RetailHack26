"""Canonical Iris data: products, service recipes, demo clock and fixture loaders (t1).

Times are naive datetimes in business-local time (Europe/London), matching app.py.

Where the other records live:
- forecast line: `iris.calc.ForecastLine`
- supplier offer / ranked offer / search tool: `iris.sourcing`
- sourcing proposal (agent side): `iris.agent.Proposal`
- approved proposal, order, inbound line: `iris.orders`
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

BUSINESS_TZ = "Europe/London"
DEMO_NOW = datetime(2026, 11, 24, 9, 0)  # Tue 24 Nov 2026 09:00, fixed demo clock
HORIZON_DAYS = 7
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

HERO_SKU = "clay-matte-100ml"


class ProductSpec(BaseModel):
    """A stocked product. Supplier offers must match brand, variant and item size."""

    sku: str
    name: str
    brand: str
    product: str
    variant: str = ""  # "" = any variant
    item_size: float  # base units per item: 100 (ml) per tub, 1 per strip
    unit: Literal["ml", "g", "unit"]
    aliases: list[str] = Field(default_factory=list)

    @property
    def display(self) -> str:
        return self.name


PRODUCTS: dict[str, ProductSpec] = {
    "clay-matte-100ml": ProductSpec(
        sku="clay-matte-100ml", name="Northline Matte Clay 100 ml", brand="Northline", product="Matte Clay",
        variant="Matte", item_size=100, unit="ml", aliases=["matte clay", "northline clay", "matte clay 100ml"]),
    "neck-strips": ProductSpec(
        sku="neck-strips", name="Barberline Neck Strips", brand="Barberline", product="Neck Strips",
        item_size=1, unit="unit", aliases=["neck strip", "neck paper"]),
}


def _load(name: str):
    return json.loads((DATA_DIR / name).read_text())


def _dt(s: str) -> datetime:
    return datetime.fromisoformat(s)


def load_recipes() -> dict[str, dict]:
    """service -> {"price": GBP, "recipe": {sku: qty in base unit}}"""
    return _load("recipes.json")


def load_bookings() -> list[dict]:
    """[{id, service, time (datetime), status, notes}]"""
    return [{**b, "time": _dt(b["time"])} for b in _load("bookings.json")]


def load_stocktake() -> dict[str, float]:
    """Seeded confirmed on-hand per SKU, in base units."""
    return {k: float(v) for k, v in _load("stocktake.json").items()}


def load_offers() -> list[dict]:
    """Labelled supplier fixture rows (see iris.sourcing.FixtureAdapter)."""
    return _load("offers.json")
