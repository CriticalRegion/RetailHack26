from datetime import datetime

import pytest

from iris.orders import OrderBook, OrderError, ProposalLine

NOW = datetime(2026, 11, 24, 9, 0)


def line(offer="O1", packs=2, sku="CLAY", supplier="A", price=8.5):
    return ProposalLine(sku, offer, supplier, packs, 100, price, 3.95, datetime(2026, 11, 26, 12))


def test_double_approve_creates_one_order():
    b = OrderBook()
    p = b.propose("B1", [line()])
    o1, created1 = b.approve("B1", p.revision, NOW)
    o2, created2 = b.approve("B1", p.revision, NOW)
    assert created1 and not created2 and o1 is o2
    assert len(b.orders) == 1 and b.pending_by_sku() == {"CLAY": 200}


def test_reject_then_approve_revision():
    b = OrderBook()
    p1 = b.propose("B1", [line()])
    rej = b.reject("B1", p1.revision, "slow supplier")
    assert rej.excluded_offer_ids == ("O1",) and not b.orders
    with pytest.raises(OrderError):
        b.approve("B1", 1, NOW)  # rejected revision cannot be ordered
    p2 = b.propose("B1", [line("O2", 1, supplier="B", price=24)], feedback=rej.reason,
                   excluded_offer_ids=rej.excluded_offer_ids)
    order, _ = b.approve("B1", p2.revision, NOW)
    assert order.order_id == "PO-B1-r2" and order.total == 27.95
    assert [p.status for p in b.history("B1")] == ["rejected", "approved"]


def test_edit_needs_new_approval_and_stale_is_refused():
    b = OrderBook()
    b.propose("B1", [line()])
    p2 = b.edit_line("B1", "CLAY", 3)
    assert p2.revision == 2 and p2.total == 29.45
    with pytest.raises(OrderError):
        b.approve("B1", 1, NOW)
    b.approve("B1", 2, NOW)
    assert b.pending_by_sku() == {"CLAY": 300}


def test_received_moves_pending_to_on_hand_once():
    b = OrderBook()
    p = b.propose("B1", [line()])
    o, _ = b.approve("B1", p.revision, NOW)
    on_hand = b.mark_received(o.order_id, {"CLAY": 50})
    on_hand = b.mark_received(o.order_id, on_hand)
    assert on_hand == {"CLAY": 250} and b.pending_by_sku() == {}


def test_empty_basket_refused():
    b = OrderBook()
    b.propose("B1", [line()])
    b.remove_line("B1", "CLAY")
    with pytest.raises(OrderError):
        b.approve("B1", 2, NOW)
