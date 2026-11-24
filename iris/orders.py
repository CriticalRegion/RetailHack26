"""Proposal revisions, merchant approval and simulated orders.

Only `OrderBook.approve` creates an order. It is idempotent per (basket, revision):
a second approval of the same revision returns the existing order. Approved stock
is *pending* (inbound) until `mark_received` moves it to on-hand.

Plain dataclasses on purpose: no dependency on iris.data, so it can be adapted to
the shared schemas without changing behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime
from typing import Iterable


class OrderError(Exception):
    """Approval refused (stale revision, empty basket, already rejected...)."""


@dataclass(frozen=True)
class ProposalLine:
    sku: str
    offer_id: str
    supplier: str
    packs: int
    units_per_pack: float  # base units: ml for clay, units for neck strips
    pack_price: float  # GBP
    shipping: float  # GBP per line
    eta: datetime
    source: str = ""  # evidence URL or fixture label
    reason: str = ""
    on_time: bool = True

    @property
    def units(self) -> float:
        return self.packs * self.units_per_pack

    @property
    def total(self) -> float:
        return round(self.packs * self.pack_price + (self.shipping if self.packs else 0), 2)


@dataclass
class Proposal:
    basket_id: str
    revision: int
    lines: list[ProposalLine]
    status: str = "proposed"  # proposed | approved | rejected | superseded
    feedback: str = ""  # merchant feedback that produced this revision
    excluded_offer_ids: tuple[str, ...] = ()
    change_note: str = ""  # what changed vs the previous revision
    rejection: str = ""  # reason given when this revision was rejected

    @property
    def total(self) -> float:
        return round(sum(l.total for l in self.lines), 2)


@dataclass(frozen=True)
class InboundLine:
    order_id: str
    sku: str
    qty: float
    eta: datetime
    received: bool = False


@dataclass(frozen=True)
class Order:
    order_id: str
    basket_id: str
    revision: int
    lines: tuple[ProposalLine, ...]
    total: float
    created_at: datetime


@dataclass(frozen=True)
class Rejection:
    """What sourcing needs to search again."""

    basket_id: str
    revision: int
    reason: str
    excluded_offer_ids: tuple[str, ...]
    skus: tuple[str, ...]


@dataclass
class OrderBook:
    proposals: dict[str, list[Proposal]] = field(default_factory=dict)
    orders: dict[str, Order] = field(default_factory=dict)
    inbound: list[InboundLine] = field(default_factory=list)

    # ---- proposals -------------------------------------------------------
    def latest(self, basket_id: str) -> Proposal | None:
        revs = self.proposals.get(basket_id)
        return revs[-1] if revs else None

    def history(self, basket_id: str) -> list[Proposal]:
        return list(self.proposals.get(basket_id, []))

    def propose(
        self,
        basket_id: str,
        lines: Iterable[ProposalLine],
        *,
        feedback: str = "",
        excluded_offer_ids: Iterable[str] = (),
        change_note: str = "",
    ) -> Proposal:
        """Add a new revision. An open earlier revision is superseded."""
        revs = self.proposals.setdefault(basket_id, [])
        if revs and revs[-1].status == "proposed":
            revs[-1].status = "superseded"
        prop = Proposal(
            basket_id=basket_id,
            revision=len(revs) + 1,
            lines=[l for l in lines if l.packs > 0],
            feedback=feedback,
            excluded_offer_ids=tuple(excluded_offer_ids),
            change_note=change_note,
        )
        revs.append(prop)
        return prop

    def _open(self, basket_id: str) -> Proposal:
        prop = self.latest(basket_id)
        if prop is None or prop.status != "proposed":
            raise OrderError("no open proposal to change")
        return prop

    def edit_line(self, basket_id: str, sku: str, packs: int) -> Proposal:
        """Change a line's pack count. Creates a new revision that needs its own approval."""
        prop = self._open(basket_id)
        if packs < 0:
            raise OrderError("packs cannot be negative")
        old = next((l for l in prop.lines if l.sku == sku), None)
        if old is None:
            raise OrderError(f"{sku} is not in the basket")
        if old.packs == packs:
            return prop
        lines = [replace(l, packs=packs) if l.sku == sku else l for l in prop.lines]
        note = f"{sku}: {old.packs} -> {packs} packs" if packs else f"removed {sku}"
        return self.propose(basket_id, lines, excluded_offer_ids=prop.excluded_offer_ids, change_note=note)

    def remove_line(self, basket_id: str, sku: str) -> Proposal:
        return self.edit_line(basket_id, sku, 0)

    def reject(
        self,
        basket_id: str,
        revision: int,
        reason: str = "",
        offer_ids: Iterable[str] | None = None,
    ) -> Rejection:
        """Reject a revision. Returns the exclusions and feedback for the sourcing rerun.

        offer_ids defaults to every offer in the rejected revision.
        """
        prop = self._open(basket_id)
        if prop.revision != revision:
            raise OrderError(f"revision {revision} is not the latest (r{prop.revision})")
        rejected = tuple(offer_ids) if offer_ids is not None else tuple(l.offer_id for l in prop.lines)
        prop.status = "rejected"
        prop.rejection = reason
        skus = tuple(l.sku for l in prop.lines if l.offer_id in rejected)
        return Rejection(
            basket_id=basket_id,
            revision=revision,
            reason=reason,
            excluded_offer_ids=tuple(dict.fromkeys(prop.excluded_offer_ids + rejected)),
            skus=skus,
        )

    # ---- orders ----------------------------------------------------------
    @staticmethod
    def order_id(basket_id: str, revision: int) -> str:
        return f"PO-{basket_id}-r{revision}"

    def approve(self, basket_id: str, revision: int, now: datetime) -> tuple[Order, bool]:
        """Approve the latest reviewed revision -> (order, created).

        Re-approving the same revision returns the existing order with created=False.
        The order and its pending inbound lines are written together.
        """
        oid = self.order_id(basket_id, revision)
        if oid in self.orders:
            return self.orders[oid], False
        prop = self.latest(basket_id)
        if prop is None:
            raise OrderError("nothing to approve")
        if prop.revision != revision:
            raise OrderError(f"revision {revision} is stale; review r{prop.revision} first")
        if prop.status != "proposed":
            raise OrderError(f"revision {revision} is {prop.status}")
        if not prop.lines:
            raise OrderError("basket is empty")
        order = Order(
            order_id=oid,
            basket_id=basket_id,
            revision=revision,
            lines=tuple(prop.lines),
            total=prop.total,
            created_at=now,
        )
        new_inbound = [InboundLine(oid, l.sku, l.units, l.eta) for l in prop.lines]
        # write both or neither
        self.orders[oid] = order
        self.inbound.extend(new_inbound)
        prop.status = "approved"
        return order, True

    def mark_received(self, order_id: str, on_hand: dict[str, float]) -> dict[str, float]:
        """Move an order's pending stock to on-hand. Returns the new on-hand dict. Idempotent."""
        out = dict(on_hand)
        updated = []
        for line in self.inbound:
            if line.order_id == order_id and not line.received:
                out[line.sku] = out.get(line.sku, 0) + line.qty
                line = replace(line, received=True)
            updated.append(line)
        self.inbound = updated
        return out

    # ---- views -----------------------------------------------------------
    def pending(self) -> list[InboundLine]:
        """Approved, not yet received. Feed these to the forecast at their ETA (once)."""
        return [l for l in self.inbound if not l.received]

    def pending_by_sku(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for l in self.pending():
            out[l.sku] = out.get(l.sku, 0) + l.qty
        return out
