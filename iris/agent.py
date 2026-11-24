"""Sourcing agent for Iris: shortage in, ranked supplier basket out; rejection reruns.

The agent builds one `SupplierSearchRequest` per shortage, calls the read-only
`search_suppliers` tool, and turns the ranked result into a `Proposal`. Every
number in a proposal is computed in code. A model, when configured, only plans
the search text and rephrases the computed reason; both are checked and fall back
to deterministic templates.

Rejecting a proposal excludes the rejected offers (plus anything the feedback
rules out, such as a supplier or a budget) for the affected SKUs and searches
again. Untouched lines are kept. Every revision is kept in `SourcingAgent.history`.
Approval and ordering live in iris/orders.py; nothing here can place an order.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from typing import Callable, Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

from iris.data import PRODUCTS, ProductSpec
from iris.sourcing import (
    TZ,
    RankedOffer,
    SearchConstraints,
    SearchResult,
    SupplierAdapter,
    SupplierSearchRequest,
    aware,
    search_suppliers,
)

LLM = Callable[[str, str], str]  # (system, user) -> text


class Shortage(BaseModel):
    """One forecast line with uncovered demand. Accepts t2's field names too."""

    model_config = {"populate_by_name": True, "extra": "ignore"}

    sku: str
    required_qty: float = Field(validation_alias=AliasChoices("required_qty", "uncovered", "uncovered_qty", "shortfall"))
    need_by: datetime = Field(validation_alias=AliasChoices("need_by", "first_at_risk_time", "at_risk_time"))
    first_at_risk_booking_id: Optional[str] = Field(
        default=None, validation_alias=AliasChoices("first_at_risk_booking_id", "first_at_risk_booking", "first_at_risk"))
    affected_booking_ids: list[str] = Field(
        default_factory=list, validation_alias=AliasChoices("affected_booking_ids", "contributing_booking_ids", "booking_ids"))
    weekly_demand: Optional[float] = Field(default=None, validation_alias=AliasChoices("weekly_demand", "usage_7d", "seven_day_usage"))
    on_hand: Optional[float] = None
    inbound: float = Field(default=0.0, validation_alias=AliasChoices("inbound", "incoming", "inbound_qty"))

    @classmethod
    def coerce(cls, obj) -> "Shortage":
        if isinstance(obj, Shortage):
            return obj
        if isinstance(obj, dict):
            return cls.model_validate(obj)
        return cls.model_validate(obj, from_attributes=True)


class ProposalLine(BaseModel):
    sku: str
    product: str
    unit: str
    shortage: Shortage
    status: Literal["proposed", "kept", "unmet"]
    selected: Optional[RankedOffer] = None
    alternative: Optional[RankedOffer] = None  # next best on-time option
    late_option: Optional[RankedOffer] = None  # cheapest late option, with what it leaves uncovered
    leads: list[RankedOffer] = Field(default_factory=list)
    reason: str
    constraints: SearchConstraints = Field(default_factory=SearchConstraints)
    query: str = ""
    sources: list[str] = Field(default_factory=list)

    @property
    def line_total(self) -> float:
        return (self.selected.delivered_cost or 0.0) if self.selected else 0.0


class Proposal(BaseModel):
    basket_id: str
    revision: int
    created_at: datetime
    lines: list[ProposalLine]
    status: Literal["proposed", "rejected", "approved"] = "proposed"
    feedback: list[str] = Field(default_factory=list)  # all feedback so far, oldest first
    excluded_offer_ids: list[str] = Field(default_factory=list)
    changed_skus: list[str] = Field(default_factory=list)  # lines re-sourced in this revision

    @property
    def total(self) -> float:
        return round(sum(l.line_total for l in self.lines), 2)

    @property
    def unmet(self) -> list[ProposalLine]:
        return [l for l in self.lines if l.status == "unmet"]


# --------------------------------------------------------------------------- feedback rules

_MONEY = r"£?\s?(\d+(?:\.\d{1,2})?)"


def constraints_from_feedback(feedback: str, base: SearchConstraints, suppliers: list[str]) -> SearchConstraints:
    """Deterministic reading of merchant feedback into hard constraints."""
    c = base.model_copy(deep=True)
    text = (feedback or "").lower()
    if not text:
        return c
    m = re.search(rf"(?:under|below|max(?:imum)?|less than|no more than|budget(?: of)?)\s*{_MONEY}", text)
    if m:
        c.max_total = float(m.group(1))
    for s in suppliers:
        name = s.lower()
        if name not in text:
            continue
        before = text[: text.index(name)]
        if re.search(r"(?:not|no|avoid|never|don't use|dont use|exclude|without)\W+(?:\w+\W+){0,2}$", before):
            if s not in c.excluded_suppliers:
                c.excluded_suppliers.append(s)
        elif re.search(r"(?:prefer|use|only|from)\W+(?:\w+\W+){0,2}$", before):
            if s not in c.preferred_suppliers:
                c.preferred_suppliers.append(s)
    return c


# --------------------------------------------------------------------------- reasons


def _when(dt: Optional[datetime]) -> str:
    return aware(dt).astimezone(TZ).strftime("%a %d %b %H:%M") if dt else "unknown"


def _qty(q: float, unit: str) -> str:
    return f"{q:g} ml" if unit == "ml" else f"{q:g} g" if unit == "g" else f"{q:g}"


def template_reason(line: ProposalLine) -> str:
    s, sel, late = line.shortage, line.selected, line.late_option
    booking = f"booking {s.first_at_risk_booking_id}" if s.first_at_risk_booking_id else "the first booking at risk"
    short = f"{_qty(s.required_qty, line.unit)} short before {booking} ({_when(s.need_by)})"
    if sel is None:
        msg = f"No verified offer arrives in time: {short}."
        if late and late.delivered_cost is not None:
            msg += (f" Fallback: {late.offer.supplier} arrives {_when(late.offer.eta)}, after that booking, "
                    f"£{late.delivered_cost:.2f} delivered.")
        return msg
    o = sel.offer
    msg = (f"{sel.packs} × {o.title} from {o.supplier}: £{sel.delivered_cost:.2f} delivered, arrives "
           f"{_when(o.eta)}, covering {_qty(s.required_qty, line.unit)} short before {booking} ({_when(s.need_by)}).")
    if late and late.delivered_cost is not None and sel.delivered_cost is not None and late.delivered_cost < sel.delivered_cost:
        msg += (f" {late.offer.supplier} is £{sel.delivered_cost - late.delivered_cost:.2f} cheaper but arrives "
                f"{_when(late.offer.eta)}, too late for that booking.")
    return msg


def grounded_reason(line: ProposalLine, llm: Optional[LLM]) -> str:
    """Template reason, optionally rephrased by a model. Rejected if it adds numbers or drops the supplier."""
    base = template_reason(line)
    if llm is None:
        return base
    system = ("You rewrite a supplier recommendation for a busy shop owner in one or two plain sentences. "
              "Use only the facts given. Do not add numbers, suppliers or claims.")
    try:
        out = (llm(system, base) or "").strip()
    except Exception:
        return base
    allowed = set(re.findall(r"\d+(?:\.\d+)?", base))
    used = set(re.findall(r"\d+(?:\.\d+)?", out))
    supplier = line.selected.offer.supplier if line.selected else None
    if not out or len(out) > 400 or not used <= allowed or (supplier and supplier not in out):
        return base
    return out


def plan_query(spec: ProductSpec, region: str, llm: Optional[LLM]) -> str:
    base = f'"{spec.brand} {spec.product}"' + (f" {spec.item_size:g}{spec.unit}" if spec.unit != "unit" else "") + f" {region}"
    if llm is None:
        return base
    try:
        q = (llm("Write one web search query to find UK suppliers selling exactly this product. Reply with the query only.",
                 json.dumps({"brand": spec.brand, "product": spec.product, "size": f"{spec.item_size:g} {spec.unit}",
                             "region": region})) or "").strip().strip('"')
    except Exception:
        return base
    # Must stay on the exact product.
    if q and spec.brand.lower() in q.lower() and (spec.unit == "unit" or f"{spec.item_size:g}" in q) and len(q) < 200:
        return q
    return base


def nebius_llm() -> Optional[LLM]:
    """Small Nebius Token Factory text client, or None when not configured."""
    key = os.getenv("NEBIUS_API_KEY")
    model = os.getenv("IRIS_TEXT_MODEL")
    if not key or not model:
        return None
    from openai import OpenAI

    client = OpenAI(api_key=key, base_url=os.getenv("NEBIUS_BASE_URL") or "https://api.tokenfactory.nebius.com/v1/",
                    timeout=15.0)

    def call(system: str, user: str) -> str:
        r = client.chat.completions.create(model=model, temperature=0, max_tokens=200,
                                           messages=[{"role": "system", "content": system},
                                                     {"role": "user", "content": user}])
        return r.choices[0].message.content or ""

    return call


# --------------------------------------------------------------------------- agent


class SourcingAgent:
    def __init__(self, adapters: Optional[list[SupplierAdapter]] = None, llm: Optional[LLM] = None,
                 products: Optional[dict[str, ProductSpec]] = None, region: str = "UK"):
        self.adapters = adapters
        self.llm = llm
        self.products = products or PRODUCTS
        self.region = region
        self.history: list[Proposal] = []

    # one shortage -> one line
    def source_line(self, shortage, now: datetime, constraints: Optional[SearchConstraints] = None) -> ProposalLine:
        s = Shortage.coerce(shortage)
        spec = self.products[s.sku]
        c = constraints or SearchConstraints(region=self.region)
        query = plan_query(spec, c.region, self.llm)
        req = SupplierSearchRequest(sku=s.sku, query=query, required_qty=s.required_qty, need_by=s.need_by, constraints=c)
        res: SearchResult = search_suppliers(req, adapters=self.adapters, now=now, spec=spec)
        on_time = [r for r in res.ranked if r.on_time]
        late = [r for r in res.ranked if r.on_time is False]
        line = ProposalLine(
            sku=s.sku, product=spec.display, unit=spec.unit, shortage=s,
            status="proposed" if on_time else "unmet",
            selected=on_time[0] if on_time else None,
            alternative=on_time[1] if len(on_time) > 1 else None,
            late_option=min(late, key=lambda r: r.delivered_cost or float("inf")) if late else None,
            leads=res.leads, reason="", constraints=c, query=query, sources=res.sources,
        )
        line.reason = grounded_reason(line, self.llm)
        return line

    def propose(self, shortages, now: Optional[datetime] = None,
                constraints: Optional[SearchConstraints] = None) -> Proposal:
        now = now or datetime.now(TZ).replace(tzinfo=None)
        lines = [self.source_line(s, now, constraints) for s in shortages if Shortage.coerce(s).required_qty > 0]
        p = Proposal(basket_id=f"bkt-{uuid.uuid4().hex[:8]}", revision=1, created_at=now, lines=lines,
                     changed_skus=[l.sku for l in lines])
        self.history.append(p)
        return p

    def reject(self, proposal: Proposal, feedback: str = "", skus: Optional[list[str]] = None,
               offer_ids: Optional[list[str]] = None, now: Optional[datetime] = None) -> Proposal:
        """New revision: rejected offers and feedback constraints applied to the affected SKUs."""
        now = now or datetime.now(TZ).replace(tzinfo=None)
        if proposal.status == "approved":
            raise ValueError("approved proposals can't be rejected")
        affected = set(skus or [l.sku for l in proposal.lines])
        rejected = set(offer_ids or [l.selected.offer.offer_id for l in proposal.lines
                                     if l.sku in affected and l.selected])
        excluded = sorted(set(proposal.excluded_offer_ids) | rejected)
        new_lines = []
        for l in proposal.lines:
            if l.sku not in affected:
                new_lines.append(l.model_copy(update={"status": "kept" if l.status == "proposed" else l.status}))
                continue
            suppliers = sorted({r.offer.supplier for r in ([l.selected, l.alternative, l.late_option] + l.leads) if r})
            c = constraints_from_feedback(feedback, l.constraints, suppliers)
            c.excluded_offer_ids = sorted(set(c.excluded_offer_ids) | set(excluded))
            new_lines.append(self.source_line(l.shortage, now, c))
        rev = Proposal(
            basket_id=proposal.basket_id, revision=proposal.revision + 1, created_at=now, lines=new_lines,
            feedback=proposal.feedback + ([feedback] if feedback else []),
            excluded_offer_ids=excluded, changed_skus=sorted(affected),
        )
        proposal.status = "rejected"
        self.history.append(rev)
        return rev

    def latest(self, basket_id: str) -> Optional[Proposal]:
        return next((p for p in reversed(self.history) if p.basket_id == basket_id), None)


def diff(old: Proposal, new: Proposal) -> list[str]:
    """Plain-English changes between two revisions, for the 'what changed' panel."""
    before = {l.sku: l for l in old.lines}
    out = []
    for l in new.lines:
        o = before.get(l.sku)
        a = o.selected.offer.supplier if o and o.selected else "nothing"
        b = l.selected.offer.supplier if l.selected else "nothing"
        if a != b:
            out.append(f"{l.product}: {a} → {b}")
    out.append(f"Basket total: £{old.total:.2f} → £{new.total:.2f}")
    return out


def to_order_lines(proposal: Proposal) -> list:
    """Agent proposal -> iris.orders.ProposalLine list, for OrderBook.propose()."""
    from iris.orders import ProposalLine as OrderLine

    out = []
    for l in proposal.lines:
        if not l.selected:
            continue
        o, r = l.selected.offer, l.selected
        out.append(OrderLine(
            sku=l.sku, offer_id=o.offer_id, supplier=o.supplier, packs=r.packs,
            units_per_pack=o.base_units_per_pack(), pack_price=o.pack_price, shipping=o.shipping or 0.0,
            eta=o.eta, source=o.evidence.url or o.evidence.label, reason=l.reason, on_time=bool(r.on_time)))
    return out
