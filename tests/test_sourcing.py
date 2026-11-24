"""t4 acceptance: shortage in -> ranked basket out; rejection excludes the offer and reruns."""
from datetime import datetime

from iris.agent import Shortage, SourcingAgent, constraints_from_feedback, diff, to_order_lines
from iris.data import DEMO_NOW, PRODUCTS
from iris.sourcing import (
    TOOL_SCHEMA,
    FixtureAdapter,
    SearchConstraints,
    SupplierSearchRequest,
    TavilyAdapter,
    parse_listing,
    search_suppliers,
)

NOW = DEMO_NOW  # Tue 24 Nov 09:00
FRIDAY = datetime(2026, 11, 27, 11, 0)  # first textured crop at risk

CLAY = {"sku": "CLAY-MATTE-100", "uncovered": 450, "first_at_risk_time": FRIDAY,
        "first_at_risk_booking": "BK-030", "contributing_booking_ids": ["BK-030", "BK-031"],
        "weekly_demand": 750, "on_hand": 300}


def agent():
    return SourcingAgent(adapters=[FixtureAdapter()], llm=None)


def test_search_filters_and_ranks():
    req = SupplierSearchRequest(sku="CLAY-MATTE-100", query="Brand X Matte Clay 100ml UK",
                                required_qty=450, need_by=FRIDAY)
    res = search_suppliers(req, adapters=[FixtureAdapter()], now=NOW)
    ids = [r.offer.offer_id for r in res.ranked]
    assert ids == ["OF-BSU-100", "OF-SD-3PK", "OF-CPW-100"]  # on time by cost, then late
    assert [r.on_time for r in res.ranked] == [True, True, False]
    best = res.best
    assert best.packs == 5 and best.covered_qty == 500 and best.delivered_cost == 46.45
    leads = {r.offer.offer_id: r.issues for r in res.leads}
    assert any("wrong size" in i for i in leads["OF-BSU-50"])
    assert "delivery date unknown" in leads["OF-MKT-100"]
    assert "shipping cost not shown" in leads["OF-MKT-100"]


def test_shortage_to_ranked_basket():
    p = agent().propose([CLAY], now=NOW)
    assert p.revision == 1 and p.status == "proposed"
    (line,) = p.lines
    assert line.status == "proposed"
    assert line.selected.offer.supplier == "BarberSupply UK"
    assert line.alternative.offer.supplier == "SalonDirect"
    assert line.late_option.offer.supplier == "CutPrice Wholesale"
    assert "BK-030" in line.reason and "BarberSupply UK" in line.reason
    assert "cheaper but arrives" in line.reason and "too late" in line.reason
    assert p.total == 46.45


def test_cheaper_option_wins_when_on_time():
    # 600 ml: SalonDirect 2 x 3-pack (£48.00) beats 6 tubs at BarberSupply UK (£54.95)
    p = agent().propose([{**CLAY, "uncovered": 600}], now=NOW)
    assert p.lines[0].selected.offer.offer_id == "OF-SD-3PK"


def test_reject_excludes_offer_and_reruns():
    a = agent()
    p1 = a.propose([CLAY], now=NOW)
    p2 = a.reject(p1, feedback="BarberSupply UK was late last time", now=NOW)
    assert p1.status == "rejected" and p2.revision == 2 and p2.basket_id == p1.basket_id
    assert "OF-BSU-100" in p2.excluded_offer_ids
    assert p2.lines[0].selected.offer.supplier == "SalonDirect"
    assert p2.feedback == ["BarberSupply UK was late last time"]
    assert len(a.history) == 2
    assert any("BarberSupply UK → SalonDirect" in d for d in diff(p1, p2))


def test_reject_until_unmet_shows_need():
    a = agent()
    p = a.propose([CLAY], now=NOW)
    p = a.reject(p, now=NOW)
    p = a.reject(p, now=NOW)
    line = p.lines[0]
    assert line.status == "unmet" and line.selected is None
    assert "No verified offer arrives in time" in line.reason
    assert line.late_option.offer.supplier == "CutPrice Wholesale"
    assert p.total == 0


def test_reject_one_sku_keeps_other_line():
    a = agent()
    strips = {"sku": "NECK-STRIP", "required_qty": 120, "need_by": FRIDAY}
    p1 = a.propose([CLAY, strips], now=NOW)
    p2 = a.reject(p1, skus=["CLAY-MATTE-100"], now=NOW)
    by = {l.sku: l for l in p2.lines}
    assert by["NECK-STRIP"].status == "kept"
    assert by["NECK-STRIP"].selected.offer.offer_id == "OF-SD-STRIP"
    assert by["CLAY-MATTE-100"].selected.offer.supplier == "SalonDirect"
    assert p2.changed_skus == ["CLAY-MATTE-100"]


def test_feedback_rules():
    c = constraints_from_feedback("Don't use SalonDirect, keep it under £50",
                                  SearchConstraints(), ["SalonDirect", "BarberSupply UK"])
    assert c.excluded_suppliers == ["SalonDirect"] and c.max_total == 50.0
    c = constraints_from_feedback("prefer SalonDirect", SearchConstraints(), ["SalonDirect"])
    assert c.preferred_suppliers == ["SalonDirect"]


def test_feedback_supplier_exclusion_reruns():
    a = agent()
    p1 = a.propose([CLAY], now=NOW)
    p2 = a.reject(p1, feedback="not SalonDirect or BarberSupply UK", now=NOW)
    # rejected offer excluded; SalonDirect excluded by feedback -> nothing on time
    assert p2.lines[0].status == "unmet"


def test_feedback_budget_reruns_within_budget():
    a = agent()
    p1 = a.propose([{**CLAY, "uncovered": 600}], now=NOW)  # SalonDirect £48.00
    p2 = a.reject(p1, feedback="too pricey, max £45", now=NOW)
    assert p2.lines[0].status == "unmet"  # BarberSupply UK £54.95 also over


def test_no_shortage_no_search():
    assert agent().propose([{**CLAY, "uncovered": 0}], now=NOW).lines == []


def test_llm_reason_rejected_when_it_invents_numbers():
    fake = lambda system, user: "BarberSupply UK is the best at £1.00."  # noqa: E731
    p = SourcingAgent(adapters=[FixtureAdapter()], llm=fake).propose([CLAY], now=NOW)
    assert "£46.45" in p.lines[0].reason


def test_failing_live_adapter_does_not_break_search():
    class Boom:
        name = "tavily"

        def search(self, *a):
            raise TimeoutError

    p = SourcingAgent(adapters=[FixtureAdapter(), Boom()], llm=None).propose([CLAY], now=NOW)
    assert p.lines[0].selected.offer.supplier == "BarberSupply UK"
    assert "tavily (failed: TimeoutError)" in p.lines[0].sources


def test_parse_listing_fields():
    spec = PRODUCTS["CLAY-MATTE-100"]
    f = parse_listing("Brand X Matte Clay 100ml 3 Pack", "Only £31.50. Delivery in 2-3 working days.", spec)
    assert f["item_size"] == 100 and f["items_per_pack"] == 3 and f["pack_price"] == 31.5 and f["eta_days"] == 3
    f = parse_listing("Matte clay 75ml", "great hold", spec)
    assert f["brand"] is None and f["pack_price"] is None and f["eta_days"] is None


def test_tavily_off_without_key(monkeypatch):
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    assert not TavilyAdapter().available


def test_tool_schema_is_function_calling_shape():
    assert TOOL_SCHEMA["function"]["name"] == "search_suppliers"
    assert "need_by" in TOOL_SCHEMA["function"]["parameters"]["properties"]


def test_shortage_accepts_object_attrs():
    class Line:
        sku = "CLAY-MATTE-100"
        uncovered = 200.0
        first_at_risk_time = FRIDAY
        first_at_risk_booking = "BK-030"
        contributing_booking_ids = ["BK-030"]

    s = Shortage.coerce(Line())
    assert s.required_qty == 200 and s.first_at_risk_booking_id == "BK-030"


def test_to_order_lines_feeds_orderbook():
    from iris.orders import OrderBook

    p = agent().propose([CLAY], now=NOW)
    lines = to_order_lines(p)
    assert lines[0].offer_id == "OF-BSU-100" and lines[0].units == 500 and lines[0].total == 46.45
    book = OrderBook()
    prop = book.propose("B1", lines)
    order, created = book.approve("B1", prop.revision, NOW)
    _, again = book.approve("B1", prop.revision, NOW)
    assert created and not again  # idempotent
