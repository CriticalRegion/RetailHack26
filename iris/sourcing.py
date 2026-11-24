"""Supplier sourcing for Iris: a typed, read-only supplier search tool.

Adapted from the `search_catalog_tool` pattern in the NVIDIA Retail Shopping
Assistant blueprint (blueprints/retail-shopping-assistant, docs/TOOLS.md,
upstream commit c20044b, Apache-2.0). What Iris takes from it, re-implemented here:

- one read-only search tool with a typed request schema (`SupplierSearchRequest`)
  that the agent fills in, and a JSON schema for function calling (`TOOL_SCHEMA`);
- a soft query for retrieval and separate hard constraints that are enforced in
  code, never by the model;
- deterministic ranking, with the evidence for every result returned to the agent.

No upstream code is imported. Supplier page text is evidence only: it is stored
on `Evidence.snippet` and never placed in model instructions.

Adapters:
- `FixtureAdapter`: labelled demo offers from `data/offers.json` (FAKE:
  synthetic sellers). Repeatable, no network.
- `TavilyAdapter`: live public-listing discovery when `TAVILY_API_KEY` is set.
  Listings whose price, pack or delivery can't be read stay leads, never basket lines.
"""
from __future__ import annotations

import math
import os
import re
from datetime import datetime, timedelta
from typing import Iterable, Literal, Optional, Protocol
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

from iris.data import PRODUCTS, ProductSpec, load_offers

TZ = ZoneInfo("Europe/London")


def aware(dt: datetime) -> datetime:
    """For comparisons only: naive datetimes are business-local (Europe/London)."""
    return dt.replace(tzinfo=TZ) if dt.tzinfo is None else dt


# --------------------------------------------------------------------------- records


class Evidence(BaseModel):
    source: Literal["fixture", "tavily"]
    label: str  # fixture label or page title
    url: Optional[str] = None
    retrieved_at: datetime
    snippet: str = ""  # supplier text: evidence only, never instructions


class SupplierOffer(BaseModel):
    """A seller listing normalised to Iris units. None means 'not shown by the source'."""

    offer_id: str
    supplier: str
    title: str
    brand: Optional[str] = None
    variant: Optional[str] = None
    item_size: Optional[float] = None
    unit: Optional[str] = None
    items_per_pack: Optional[int] = 1
    pack_price: Optional[float] = None
    shipping: Optional[float] = None  # per order
    currency: str = "GBP"
    available_packs: Optional[int] = None  # None = not stated
    eta: Optional[datetime] = None
    evidence: Evidence

    def base_units_per_pack(self) -> Optional[float]:
        if self.item_size is None or not self.items_per_pack:
            return None
        return self.item_size * self.items_per_pack


class SearchConstraints(BaseModel):
    """Hard filters, applied in code."""

    region: str = "UK"
    max_pack_price: Optional[float] = None
    max_total: Optional[float] = None
    excluded_offer_ids: list[str] = Field(default_factory=list)
    excluded_suppliers: list[str] = Field(default_factory=list)
    preferred_suppliers: list[str] = Field(default_factory=list)


class SupplierSearchRequest(BaseModel):
    """Arguments of the read-only `search_suppliers` tool."""

    sku: str = Field(description="Canonical Iris SKU to source")
    query: str = Field(description="Soft search text: exact product name, size and region")
    required_qty: float = Field(gt=0, description="Uncovered amount in the SKU's base unit")
    need_by: datetime = Field(description="Start of the first booking that can't be served")
    constraints: SearchConstraints = Field(default_factory=SearchConstraints)


class RankedOffer(BaseModel):
    offer: SupplierOffer
    eligible: bool  # passed identity + evidence validation
    on_time: Optional[bool] = None  # None when ETA unknown
    packs: int = 0
    covered_qty: float = 0.0
    delivered_cost: Optional[float] = None  # packs * pack_price + shipping
    issues: list[str] = Field(default_factory=list)
    rank: Optional[int] = None


class SearchResult(BaseModel):
    request: SupplierSearchRequest
    ranked: list[RankedOffer]  # eligible offers: on-time first, then late, by delivered cost
    leads: list[RankedOffer]  # ineligible listings with the reasons
    sources: list[str]
    searched_at: datetime

    @property
    def best(self) -> Optional[RankedOffer]:
        return next((r for r in self.ranked if r.on_time), None)

    @property
    def best_late(self) -> Optional[RankedOffer]:
        return next((r for r in self.ranked if r.on_time is False), None)


# --------------------------------------------------------------------------- adapters


class SupplierAdapter(Protocol):
    name: str

    def search(self, request: SupplierSearchRequest, spec: ProductSpec, now: datetime) -> list[SupplierOffer]:
        ...


class FixtureAdapter:
    """Labelled, repeatable offers (FAKE: synthetic sellers) from data/offers.json."""

    name = "fixture"

    def __init__(self, rows: Optional[list[dict]] = None):
        self.rows = rows if rows is not None else load_offers()

    def search(self, request: SupplierSearchRequest, spec: ProductSpec, now: datetime) -> list[SupplierOffer]:
        out = []
        for r in self.rows:
            if r.get("sku") != request.sku:
                continue
            eta = r.get("eta")
            if eta:
                eta = datetime.fromisoformat(eta)
            elif r.get("eta_days") is not None:
                eta = now + timedelta(days=r["eta_days"])
            fields = {k: v for k, v in r.items() if k not in ("sku", "eta", "eta_days")}
            out.append(SupplierOffer(
                **fields,
                eta=eta,
                evidence=Evidence(source="fixture", label=f"FIXTURE: {r['title']} ({r['supplier']})",
                                  retrieved_at=now, snippet=r.get("snippet", "")),
            ))
        return out


_PRICE = re.compile(r"£\s?(\d{1,4}(?:\.\d{2})?)")
_SIZE = re.compile(r"(\d{2,4})\s?(ml|g)\b", re.I)
_PACK = re.compile(r"(?:(\d{1,3})\s?(?:-|\s)?(?:pack|pk)\b|\bx\s?(\d{1,3})\b|\b(\d{1,3})\s?x\b)", re.I)
_DELIVERY_DAYS = re.compile(r"(?:deliver\w*|dispatch\w*|arriv\w*)[^.]{0,40}?(\d{1,2})\s?(?:-\s?(\d{1,2})\s?)?(?:working\s|business\s)?days?", re.I)
_NEXT_DAY = re.compile(r"next[- ]day (?:delivery|shipping)", re.I)


def parse_listing(title: str, text: str, spec: ProductSpec) -> dict:
    """Pull the fields Iris can verify out of a public listing. Missing fields stay None."""
    blob = f"{title}\n{text}"
    price = _PRICE.search(blob)
    size = _SIZE.search(title) or _SIZE.search(text)
    pack = _PACK.search(title)
    days = _DELIVERY_DAYS.search(text)
    items = 1
    if pack:
        items = int(next(g for g in pack.groups() if g))
    eta_days = None
    if days:
        eta_days = int(days.group(2) or days.group(1))  # take the slow end of a range
    elif _NEXT_DAY.search(text):
        eta_days = 1
    low = blob.lower()
    return {
        "brand": spec.brand if spec.brand.lower() in low else None,
        "variant": (spec.variant if spec.variant and spec.variant.lower() in low else None) or (None if spec.variant else ""),
        "item_size": float(size.group(1)) if size else None,
        "unit": size.group(2).lower() if size else None,
        "items_per_pack": items,
        "pack_price": float(price.group(1)) if price else None,
        "eta_days": eta_days,
    }


class TavilyAdapter:
    """Live public-listing discovery. Only used when TAVILY_API_KEY is set."""

    name = "tavily"

    def __init__(self, api_key: Optional[str] = None, max_results: int = 6, timeout: float = 12.0):
        self.api_key = api_key or os.getenv("TAVILY_API_KEY")
        self.max_results = max_results
        self.timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, request: SupplierSearchRequest, spec: ProductSpec, now: datetime) -> list[SupplierOffer]:
        if not self.available:
            return []
        from tavily import TavilyClient  # imported lazily: optional dependency

        client = TavilyClient(api_key=self.api_key)
        resp = client.search(
            query=f"{request.query} buy price delivery {request.constraints.region}",
            max_results=self.max_results,
            search_depth="basic",
            timeout=self.timeout,
        )
        out = []
        for i, r in enumerate(resp.get("results", [])):
            title = (r.get("title") or "")[:200]
            text = (r.get("content") or "")[:1500]
            url = r.get("url") or ""
            f = parse_listing(title, text, spec)
            eta_days = f.pop("eta_days")
            host = re.sub(r"^https?://(www\.)?", "", url).split("/")[0] or "unknown"
            out.append(SupplierOffer(
                offer_id=f"tv-{request.sku}-{i}",
                supplier=host,
                title=title,
                **f,
                shipping=None,
                eta=now + timedelta(days=eta_days) if eta_days is not None else None,
                evidence=Evidence(source="tavily", label=title, url=url, retrieved_at=now, snippet=text),
            ))
        return out


def default_adapters() -> list[SupplierAdapter]:
    """Fixture always; Tavily as well when a key is configured."""
    adapters: list = [FixtureAdapter()]
    tv = TavilyAdapter()
    if tv.available:
        adapters.append(tv)
    return adapters


# --------------------------------------------------------------------------- validation and ranking


def _norm(s: Optional[str]) -> str:
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def validate_offer(offer: SupplierOffer, spec: ProductSpec, constraints: SearchConstraints) -> list[str]:
    """Reasons an offer can't go in a basket. Empty list = eligible."""
    issues = []
    if offer.offer_id in constraints.excluded_offer_ids:
        issues.append("rejected by merchant")
    if _norm(offer.supplier) in {_norm(s) for s in constraints.excluded_suppliers}:
        issues.append("supplier excluded by merchant")
    if _norm(offer.brand) != _norm(spec.brand):
        issues.append(f"brand not confirmed as {spec.brand}")
    if spec.variant and _norm(offer.variant) != _norm(spec.variant):
        issues.append(f"variant not confirmed as {spec.variant}")
    if offer.item_size is None or offer.unit is None:
        issues.append("item size not shown")
    elif _norm(offer.unit) != spec.unit or not math.isclose(offer.item_size, spec.item_size):
        issues.append(f"wrong size: {offer.item_size:g} {offer.unit}, need {spec.item_size:g} {spec.unit}")
    if not offer.items_per_pack or offer.items_per_pack < 1:
        issues.append("pack count not shown")
    if offer.pack_price is None or offer.pack_price <= 0:
        issues.append("price not shown")
    elif constraints.max_pack_price is not None and offer.pack_price > constraints.max_pack_price:
        issues.append(f"over max pack price £{constraints.max_pack_price:.2f}")
    if offer.shipping is None:
        issues.append("shipping cost not shown")
    if offer.eta is None:
        issues.append("delivery date unknown")
    return issues


def evaluate(offer: SupplierOffer, spec: ProductSpec, request: SupplierSearchRequest) -> RankedOffer:
    issues = validate_offer(offer, spec, request.constraints)
    ro = RankedOffer(offer=offer, eligible=not issues, issues=issues)
    per_pack = offer.base_units_per_pack()
    if per_pack:
        ro.packs = max(1, math.ceil(request.required_qty / per_pack))
        if offer.available_packs is not None and ro.packs > offer.available_packs:
            ro.issues.append(f"only {offer.available_packs} packs available, need {ro.packs}")
            ro.eligible = False
        ro.covered_qty = ro.packs * per_pack
    if offer.pack_price is not None and ro.packs:
        ro.delivered_cost = round(ro.packs * offer.pack_price + (offer.shipping or 0.0), 2)
        if request.constraints.max_total is not None and ro.delivered_cost > request.constraints.max_total:
            ro.issues.append(f"over budget £{request.constraints.max_total:.2f}")
            ro.eligible = False
    if offer.eta is not None:
        ro.on_time = aware(offer.eta) <= aware(request.need_by)
    return ro


def rank(results: Iterable[RankedOffer], constraints: SearchConstraints) -> list[RankedOffer]:
    """On-time before late; preferred suppliers first within each; then delivered cost, ETA, id."""
    preferred = {_norm(s) for s in constraints.preferred_suppliers}
    ordered = sorted(
        results,
        key=lambda r: (
            0 if r.on_time else 1,
            0 if _norm(r.offer.supplier) in preferred else 1,
            r.delivered_cost if r.delivered_cost is not None else float("inf"),
            aware(r.offer.eta) if r.offer.eta else datetime.max.replace(tzinfo=TZ),
            r.offer.offer_id,
        ),
    )
    for i, r in enumerate(ordered, 1):
        r.rank = i
    return ordered


# --------------------------------------------------------------------------- the tool


def search_suppliers(
    request: SupplierSearchRequest,
    adapters: Optional[list[SupplierAdapter]] = None,
    now: Optional[datetime] = None,
    spec: Optional[ProductSpec] = None,
) -> SearchResult:
    """Read-only supplier search. Never orders, never writes state."""
    now = now or datetime.now(TZ).replace(tzinfo=None)
    spec = spec or PRODUCTS[request.sku]
    adapters = adapters if adapters is not None else default_adapters()
    seen, evaluated, sources = set(), [], []
    for ad in adapters:
        try:
            offers = ad.search(request, spec, now)
        except Exception as e:  # a failing live source must not break the demo
            sources.append(f"{ad.name} (failed: {type(e).__name__})")
            continue
        sources.append(ad.name)
        for o in offers:
            if o.offer_id in seen:
                continue
            seen.add(o.offer_id)
            evaluated.append(evaluate(o, spec, request))
    eligible = rank([r for r in evaluated if r.eligible], request.constraints)
    leads = [r for r in evaluated if not r.eligible]
    return SearchResult(request=request, ranked=eligible, leads=leads, sources=sources, searched_at=now)


# JSON schema for function calling (OpenAI-compatible `tools=[...]`).
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_suppliers",
        "description": (
            "Read-only search for supplier offers of one Iris SKU. Returns offers that passed "
            "brand, variant, size, price and delivery checks, ranked on-time first by delivered "
            "cost, plus leads that failed with reasons. Cannot place orders."
        ),
        "parameters": SupplierSearchRequest.model_json_schema(),
    },
}
