"""t4 acceptance: shortage in -> ranked basket out; rejection excludes the offer and reruns."""
from datetime import datetime, timedelta

from iris.agent import Shortage, SourcingAgent, constraints_from_feedback, diff
from iris.sourcing import (
    PRODUCTS,
    TOOL_SCHEMA,
    TZ,
    FixtureAdapter,
    SearchConstraints,
    SupplierSearchRequest,
    TavilyAdapter,
    parse_listing,
    search_suppliers,
)

NOW = datetime(2026, 11, 24, 9, 0, tzinfo=TZ)  # Tue 09:00
FRIDAY = NOW + timedelta(days=3, hours=1)  # Fri 10:00 textured crop booking

CLAY = {"sku": "clay-matte-100ml", "uncovered": 450, "first_at_risk_time": FRIDAY,
        "first_at_risk_booking": "bk-017", "contributing_booking_ids": ["bk-017", "bk-021"],
        "weekly_demand": 750, "on_hand": 300}


def agent():
    return SourcingAgent(adapters=[FixtureAdapter()], llm=None)


def test_search_filters_and_ranks():
    req = SupplierSearchRequest(sku="clay-matte-100ml", query="Northline Matte Clay 100ml UK",
                                required_qty=450, need_by=FRIDAY)
    res = search_suppliers(req, adapters=[FixtureAdapter()], now=NOW)
    ids = [r.offer.offer_id for r in res.ranked]
    # on-time first by delivered cost, then the late one
    assert ids == ["fx-clay-barberhub", "fx-clay-shearco", "fx-clay-bulkbarber"]
    assert [r.on_time for r in res.ranked] == [True, True, False]
    best = res.best
    assert best.packs == 5 and best.covered_qty == 500 and best.delivered_cost == 61.0
    # wrong size and unknown delivery stay leads with reasons
    leads = {r.offer.offer_id: r.issues for r in res.leads}
    assert any("wrong size" in i for i in leads["fx-clay-wrongsize"])
    assert "delivery date unknown" in leads["fx-clay-noeta"]
    assert "shipping cost not shown" in leads["fx-clay-noeta"]


def test_shortage_to_ranked_basket():
    p = agent().propose([CLAY], now=NOW)
    assert p.revision == 1 and p.status == "proposed"
    (line,) = p.lines
    assert line.status == "proposed"
    assert line.selected.offer.supplier == "BarberHub"
    assert line.alternative.offer.supplier == "ShearCo Supply"
    assert line.late_option.offer.supplier == "BulkBarber Wholesale"
    assert line.shortage.first_at_risk_booking_id == "bk-017"
    assert "bk-017" in line.reason and "BarberHub" in line.reason
    assert p.total == 61.0


def test_cheaper_late_offer_explained():
    # 600 ml needed: BulkBarber's 6-pack (£54) is cheaper than 6 pots at BarberHub (£72.50) but late
    p = agent().propose([{**CLAY, "uncovered": 600}], now=NOW)
    line = p.lines[0]
    assert line.selected.delivered_cost > line.late_option.delivered_cost
    assert "cheaper but arrives" in line.reason and "too late" in line.reason


def test_reject_excludes_offer_and_reruns():
    a = agent()
    p1 = a.propose([CLAY], now=NOW)
    p2 = a.reject(p1, feedback="BarberHub was late last time", now=NOW)
    assert p1.status == "rejected" and p2.revision == 2 and p2.basket_id == p1.basket_id
    assert "fx-clay-barberhub" in p2.excluded_offer_ids
    assert p2.lines[0].selected.offer.supplier == "ShearCo Supply"
    assert p2.feedback == ["BarberHub was late last time"]
    assert len(a.history) == 2  # both revisions kept
    assert any("BarberHub → ShearCo Supply" in d for d in diff(p1, p2))


def test_reject_until_unmet_shows_need():
    a = agent()
    p = a.propose([CLAY], now=NOW)
    p = a.reject(p, now=NOW)
    p = a.reject(p, now=NOW)
    line = p.lines[0]
    assert line.status == "unmet" and line.selected is None
    assert "No verified offer arrives in time" in line.reason
    assert line.late_option.offer.supplier == "BulkBarber Wholesale"
    assert p.total == 0


def test_reject_one_sku_keeps_other_line():
    a = agent()
    strips = {"sku": "neck-strips", "required_qty": 120, "need_by": FRIDAY}
    p1 = a.propose([CLAY, strips], now=NOW)
    p2 = a.reject(p1, skus=["clay-matte-100ml"], now=NOW)
    by = {l.sku: l for l in p2.lines}
    assert by["neck-strips"].status == "kept"
    assert by["neck-strips"].selected.offer.offer_id == p1.lines[1].selected.offer.offer_id
    assert by["clay-matte-100ml"].selected.offer.supplier == "ShearCo Supply"
    assert p2.changed_skus == ["clay-matte-100ml"]


def test_feedback_rules():
    c = constraints_from_feedback("Don't use ShearCo Supply, keep it under £50",
                                  SearchConstraints(), ["ShearCo Supply", "BarberHub"])
    assert c.excluded_suppliers == ["ShearCo Supply"] and c.max_total == 50.0
    c = constraints_from_feedback("prefer ShearCo Supply", SearchConstraints(), ["ShearCo Supply"])
    assert c.preferred_suppliers == ["ShearCo Supply"]


def test_feedback_budget_reruns_within_budget():
    a = agent()
    p1 = a.propose([{**CLAY, "uncovered": 600}], now=NOW)  # BarberHub £72.50
    p2 = a.reject(p1, feedback="too pricey, max £70", now=NOW)
    line = p2.lines[0]
    # ShearCo 2x3-pack = £70.95 is over budget too, so nothing on time qualifies
    assert line.status == "unmet"


def test_no_shortage_no_search():
    p = agent().propose([{**CLAY, "uncovered": 0}], now=NOW)
    assert p.lines == []


def test_llm_reason_rejected_when_it_invents_numbers():
    fake = lambda system, user: "BarberHub is the best at £1.00."  # noqa: E731
    p = SourcingAgent(adapters=[FixtureAdapter()], llm=fake).propose([CLAY], now=NOW)
    assert "£61.00" in p.lines[0].reason  # fell back to the template


def test_failing_live_adapter_does_not_break_search():
    class Boom:
        name = "tavily"

        def search(self, *a):
            raise TimeoutError

    p = SourcingAgent(adapters=[FixtureAdapter(), Boom()], llm=None).propose([CLAY], now=NOW)
    assert p.lines[0].selected.offer.supplier == "BarberHub"
    assert "tavily (failed: TimeoutError)" in p.lines[0].sources


def test_parse_listing_fields():
    spec = PRODUCTS["clay-matte-100ml"]
    f = parse_listing("Northline Matte Clay 100ml 3 Pack", "Only £31.50. Delivery in 2-3 working days.", spec)
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
        sku = "clay-matte-100ml"
        uncovered = 200.0
        first_at_risk_time = FRIDAY
        first_at_risk_booking = "bk-017"
        contributing_booking_ids = ["bk-017"]

    s = Shortage.coerce(Line())
    assert s.required_qty == 200 and s.first_at_risk_booking_id == "bk-017"


def test_to_order_lines_feeds_orderbook():
    from iris.agent import to_order_lines
    from iris.orders import OrderBook

    p = agent().propose([CLAY], now=NOW)
    lines = to_order_lines(p)
    assert lines[0].offer_id == "fx-clay-barberhub" and lines[0].units == 500 and lines[0].total == 61.0
    book = OrderBook()
    prop = book.propose("B1", lines)
    _, created = book.approve("B1", prop.revision, NOW)
    _, again = book.approve("B1", prop.revision, NOW)
    assert created and not again
