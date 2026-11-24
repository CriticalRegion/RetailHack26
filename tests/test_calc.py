"""t2 acceptance: hero clay shortfall reproduced; an edited count changes the forecast."""
from dataclasses import dataclass
from datetime import datetime

from iris.agent import SourcingAgent, to_order_lines
from iris.calc import booking_issues, forecast, protected_bookings, shortages
from iris.data import DEMO_NOW, HERO_SKU, load_bookings, load_recipes, load_stocktake
from iris.sourcing import FixtureAdapter


@dataclass
class Inbound:
    sku: str
    qty: float
    eta: datetime


def base():
    return forecast(load_stocktake(), [], load_bookings())


def test_hero_clay_shortfall():
    fc = base()
    clay = fc[HERO_SKU]
    assert clay.on_hand == 120 and clay.usage == 223
    assert clay.uncovered == 103
    assert clay.first_at_risk["id"] == "BK-030"
    assert clay.first_at_risk["time"] == datetime(2026, 11, 27, 11, 0)  # Friday textured crop
    assert clay.first_at_risk["service"] == "Textured crop"
    assert fc["neck-strips"].uncovered == 0 and fc["neck-strips"].first_at_risk is None


def test_cancelled_booking_excluded():
    ids = {b["id"] for l in base().values() for b in l.at_risk}
    assert "BK-900" not in ids


def test_edited_count_changes_forecast():
    on_hand = {**load_stocktake(), HERO_SKU: 200}
    clay = forecast(on_hand, [], load_bookings())[HERO_SKU]
    assert clay.uncovered == 23
    assert clay.first_at_risk["time"] > datetime(2026, 11, 27, 11, 0)
    enough = forecast({**load_stocktake(), HERO_SKU: 400}, [], load_bookings())[HERO_SKU]
    assert enough.uncovered == 0 and shortages({HERO_SKU: enough}) == []


def test_inbound_counts_once_at_eta():
    on_time = [Inbound(HERO_SKU, 200, datetime(2026, 11, 26, 12, 0))]
    late = [Inbound(HERO_SKU, 200, datetime(2026, 11, 30, 10, 0))]
    assert forecast(load_stocktake(), on_time, load_bookings())[HERO_SKU].uncovered == 0
    late_fc = forecast(load_stocktake(), late, load_bookings())[HERO_SKU]
    assert late_fc.first_at_risk["id"] == "BK-030" and late_fc.incoming == 200


def test_missing_recipe_flagged_not_forecast():
    bookings = load_bookings() + [{"id": "BK-X", "service": "Beard sculpt", "time": DEMO_NOW, "status": "booked"}]
    assert [i.booking_id for i in booking_issues(bookings)] == ["BK-X"]
    assert forecast(load_stocktake(), [], bookings)[HERO_SKU].usage == 223


def test_shortage_to_order_end_to_end():
    fc = base()
    (sh,) = shortages(fc)
    assert sh["need_by"] == datetime(2026, 11, 27, 11, 0) and sh["required_qty"] == 103
    p = SourcingAgent(adapters=[FixtureAdapter()]).propose([sh], now=DEMO_NOW)
    inbound = [Inbound(l.sku, l.units, l.eta) for l in to_order_lines(p)]
    after = forecast(load_stocktake(), inbound, load_bookings())
    assert after[HERO_SKU].uncovered == 0
    saved, revenue = protected_bookings(fc, after, load_recipes())
    assert saved == len(fc[HERO_SKU].at_risk) and revenue > 0
