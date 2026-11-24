"""Iris API for the React UI (web/). Same logic as the Streamlit app: iris.calc / iris.agent / iris.orders / iris.intake.

Run:  .venv/Scripts/uvicorn server:app --port 8000 --reload
Contract: contracts/api.md. Every endpoint returns the full view-model State (GET /api/state shape),
so the front end only renders. Single-user demo: one in-memory session, POST /api/reset starts over.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, File, HTTPException, UploadFile  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from iris import intake, llm  # noqa: E402
from iris.agent import SourcingAgent, diff, nebius_llm  # noqa: E402
from iris.calc import forecast, protected_bookings, shortages  # noqa: E402
from iris.data import DEMO_NOW, HERO_SKU, load_bookings, load_stocktake  # noqa: E402
from iris.data import PRODUCTS as DATA_PRODUCTS  # noqa: E402
from iris.orders import OrderBook, OrderError, ProposalLine  # noqa: E402
from iris.sourcing import TZ, FixtureAdapter, default_adapters  # noqa: E402

ROOT = Path(__file__).resolve().parent
BASKET_ID = "BARBER-W48"
PRODUCTS = {k: {"sku": k, "name": p.name, "unit": p.unit} for k, p in DATA_PRODUCTS.items()}
SAMPLE_PHOTO = ROOT / "demo" / "stocktake.png"
BLURRY_PHOTO = ROOT / "demo" / "stocktake_blurry.png"

app = FastAPI(title="Iris API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ---------------------------------------------------------------- session
class Session:
    def __init__(self) -> None:
        self.book = OrderBook()
        self.on_hand: dict[str, float] = load_stocktake()
        self.bookings = load_bookings()
        self.review: list[dict] = []
        self.review_source = ""
        self.agent: Optional[SourcingAgent] = None
        self.agent_prop = None
        self.agent_prev = None
        self.last_order_created = True
        self.live = False
        self.flash: Optional[dict] = None


S = Session()


def naive(dt: Optional[datetime]) -> Optional[datetime]:
    return dt.astimezone(TZ).replace(tzinfo=None) if dt is not None and dt.tzinfo else dt


def iso(dt: Optional[datetime]) -> Optional[str]:
    dt = naive(dt)
    return dt.isoformat(timespec="minutes") if dt else None


def to_lines(ap) -> list[ProposalLine]:
    out = []
    for l in ap.lines:
        r = l.selected
        if l.status == "unmet" or r is None:
            continue
        o = r.offer
        out.append(ProposalLine(
            sku=l.sku, offer_id=o.offer_id, supplier=o.supplier, packs=r.packs,
            units_per_pack=o.base_units_per_pack(), pack_price=o.pack_price, shipping=o.shipping or 0.0,
            eta=naive(o.eta), source=o.evidence.url or o.evidence.label, reason=l.reason))
    return out


def make_agent(live: bool) -> SourcingAgent:
    if live:
        return SourcingAgent(adapters=default_adapters(), llm=nebius_llm())
    return SourcingAgent(adapters=[FixtureAdapter()], llm=None)


def say(kind: str, msg: str) -> None:
    S.flash = {"kind": kind, "msg": msg}


# ---------------------------------------------------------------- view model
def _booking(b: Optional[dict]) -> Optional[dict]:
    if not b:
        return None
    return {"id": b.get("id"), "time": iso(b.get("time")), "service": b.get("service")}


def _offer_view(tag: str, r, at_risk: list[dict], unit: str) -> dict:
    o = r.offer
    eta = naive(o.eta)
    misses = sum(1 for b in at_risk if eta and b["time"] < eta) if r.on_time is False else 0
    per100 = (round(r.delivered_cost / r.covered_qty * 100, 2)
              if r.delivered_cost and r.covered_qty and unit == "ml" else None)
    return {"tag": tag, "offer_id": o.offer_id, "supplier": o.supplier, "listing": o.title,
            "packs": r.packs or None, "delivered_cost": r.delivered_cost, "per_100ml": per100,
            "eta": iso(eta), "on_time": r.on_time, "misses_bookings": misses,
            "evidence_url": o.evidence.url, "evidence_label": o.evidence.label, "issues": list(r.issues)}


def state() -> dict:
    book = S.book
    fc = forecast(S.on_hand, book.pending(), S.bookings)
    received: dict[str, float] = {}
    for l in book.inbound:
        if l.received:
            received[l.sku] = received.get(l.sku, 0) + l.qty
    baseline = forecast({k: v - received.get(k, 0) for k, v in S.on_hand.items()}, [], S.bookings)
    fc_before = forecast(S.on_hand, [], S.bookings)
    pend = book.pending_by_sku()

    forecast_view = []
    for sku, line in fc.items():
        p = PRODUCTS[sku]
        forecast_view.append({
            "sku": sku, "name": p["name"], "unit": p["unit"], "hero": sku == HERO_SKU,
            "usage": line.usage, "on_hand": line.on_hand, "incoming": line.incoming, "uncovered": line.uncovered,
            "first_at_risk": _booking(line.first_at_risk), "at_risk_count": len(line.at_risk),
            "at_risk": [_booking(b) for b in line.at_risk],
            "contributing": line.contributing,
            "covered_by_order": bool(not line.first_at_risk and baseline[sku].first_at_risk),
            "series": [{"time": iso(t), "projected": v} for t, v in line.series],
            "series_without_order": [{"time": iso(t), "projected": v} for t, v in baseline[sku].series],
        })

    prop = book.latest(BASKET_ID)
    proposal = None
    if prop is not None:
        proposal = {
            "basket_id": BASKET_ID, "revision": prop.revision, "status": prop.status, "total": round(prop.total, 2),
            "feedback": prop.feedback, "excluded_offer_ids": list(prop.excluded_offer_ids),
            "change_note": prop.change_note,
            "lines": [{"sku": l.sku, "product": PRODUCTS[l.sku]["name"], "unit": PRODUCTS[l.sku]["unit"],
                       "offer_id": l.offer_id, "supplier": l.supplier, "packs": l.packs,
                       "units_per_pack": l.units_per_pack, "pack_price": l.pack_price, "shipping": l.shipping,
                       "total": round(l.total, 2), "eta": iso(l.eta), "source": l.source, "reason": l.reason}
                      for l in prop.lines]}

    offers = []
    ap = S.agent_prop
    for al in (ap.lines if ap else []):
        at_risk = fc_before[al.sku].at_risk if al.sku in fc_before else []
        opts = [_offer_view(tag, r, at_risk, al.unit)
                for tag, r in (("selected", al.selected), ("alternative", al.alternative), ("late", al.late_option))
                if r is not None]
        opts += [_offer_view("lead", r, at_risk, al.unit) for r in al.leads]
        offers.append({"sku": al.sku, "product": al.product, "unit": al.unit, "status": al.status,
                       "reason": al.reason, "query": al.query.replace('"', ""), "options": opts})

    history = [{"revision": p.revision, "status": p.status, "total": round(p.total, 2),
                "lines": [f"{l.supplier} × {l.packs}" for l in p.lines],
                "note": p.rejection or p.change_note or p.feedback} for p in book.history(BASKET_ID)]

    orders = []
    for oid, o in book.orders.items():
        pending = [l for l in book.inbound if l.order_id == oid and not l.received]
        orders.append({"order_id": oid, "revision": o.revision, "total": round(o.total, 2),
                       "created_at": iso(o.created_at), "status": "pending" if pending else "received",
                       "lines": [{"sku": l.sku, "product": PRODUCTS[l.sku]["name"], "packs": l.packs,
                                  "units": l.units, "unit": PRODUCTS[l.sku]["unit"], "supplier": l.supplier,
                                  "eta": iso(l.eta)} for l in o.lines]})

    n_prot, rev = protected_bookings(baseline, fc) if book.orders else (0, 0)

    # "basket": the same proposal in the shape of web/src/components/basketTypes.ts (raw agent dump)
    def agent_dump(p, status=None):
        if p is None:
            return None
        d = p.model_dump(mode="json")
        d["total"] = p.total
        if status:
            d["status"] = status
        return d

    basket = None
    if ap is not None:
        cur = agent_dump(ap, prop.status if prop is not None else None)
        cur["changes"] = diff(S.agent_prev, ap) if S.agent_prev is not None else []
        last = list(book.orders.values())[-1] if book.orders else None
        order = None
        if last is not None:
            order = {"order_id": last.order_id, "revision": last.revision, "total": round(last.total, 2),
                     "lines": [{"sku": l.sku, "supplier": l.supplier, "packs": l.packs, "units": l.units,
                                "eta": iso(l.eta)} for l in last.lines],
                     "created": S.last_order_created, "order_count": len(book.orders),
                     "bookings_protected": n_prot, "revenue_covered": rev}
        basket = {"proposal": cur, "previous": agent_dump(S.agent_prev, "rejected"), "order": order,
                  "at_risk_times": [iso(b["time"]) for b in fc_before[HERO_SKU].at_risk]}
    hero = fc[HERO_SKU]
    hero_base = baseline[HERO_SKU]
    if book.orders:
        step = "order"
    elif prop is not None:
        step = "basket"
    elif S.review:
        step = "stock"
    else:
        step = "forecast"

    out = {
        "shop": {"name": "Old St Barbers (demo)", "clock": iso(DEMO_NOW), "tz": "Europe/London"},
        "intake": {"text_model": llm.text_model() if llm.text_ready() else None,
                   "vision_model": llm.vision_model() if llm.vision_ready() else None},
        "live_search": S.live,
        "products": list(PRODUCTS.values()),
        "stock": [{"sku": s, "name": p["name"], "unit": p["unit"], "on_hand": S.on_hand.get(s, 0),
                   "incoming": pend.get(s, 0)} for s, p in PRODUCTS.items()],
        "review": [{"confirm": r["confirm"], "raw_label": r["raw label"], "sku": r["sku"],
                    "quantity": r["quantity"], "unit": r["unit"], "note": r["note"]} for r in S.review],
        "review_source": S.review_source,
        "forecast": forecast_view,
        "kpis": {
            "bookings_at_risk": sum(len(l.at_risk) for l in fc.values()),
            "first_run_out": _booking(hero.first_at_risk or hero_base.first_at_risk),
            "hero_covered": bool(book.orders and not hero.first_at_risk),
            "basket_total": proposal["total"] if proposal else None,
            "bookings_protected": n_prot, "revenue_covered": rev, "orders": len(book.orders)},
        "step": step,
        "proposal": proposal,
        "basket": basket,
        "offers": offers,
        "history": history,
        "orders": orders,
        "flash": S.flash,
    }
    S.flash = None
    return out


# ---------------------------------------------------------------- endpoints
class TextIn(BaseModel):
    text: str


class ConfirmRow(BaseModel):
    sku: str
    quantity: Optional[float] = None
    confirm: bool = True


class ConfirmIn(BaseModel):
    rows: list[ConfirmRow]


class RevisionIn(BaseModel):
    revision: int
    feedback: str = ""


class LineIn(BaseModel):
    sku: str
    packs: int = 0


class OrderIn(BaseModel):
    order_id: str


class LiveIn(BaseModel):
    on: bool


@app.get("/api/state")
def get_state():
    return state()


@app.post("/api/reset")
def reset():
    global S
    S = Session()
    return state()


@app.post("/api/live")
def set_live(body: LiveIn):
    S.live = body.on
    say("info", "Live search on: Tavily + Nebius." if body.on else "Live search off: labelled fixture offers.")
    return state()


@app.post("/api/intake/text")
def intake_text(body: TextIn):
    S.review = intake.extract("text", body.text)
    S.review_source = "text"
    return state()


def _photo(data: bytes, mime: str, label: str):
    class _F:  # quacks like Streamlit's UploadedFile for intake.extract_photo
        def __init__(self, b, t):
            self._b, self.type = b, t

        def getvalue(self):
            return self._b

    S.review = intake.extract("photo", _F(data, mime))
    S.review_source = label
    return state()


@app.post("/api/intake/photo")
async def intake_photo(file: UploadFile = File(...)):
    return _photo(await file.read(), file.content_type or "image/png", "photo")


@app.post("/api/intake/sample")
def intake_sample(blurry: bool = False):
    f = BLURRY_PHOTO if blurry else SAMPLE_PHOTO
    return _photo(f.read_bytes(), "image/png", "sample photo" + (" (blurry)" if blurry else ""))


@app.get("/api/sample-photo")
def sample_photo(blurry: bool = False):
    return FileResponse(BLURRY_PHOTO if blurry else SAMPLE_PHOTO, media_type="image/png")


@app.post("/api/stock/confirm")
def confirm(body: ConfirmIn):
    n = 0
    for r in body.rows:
        if r.confirm and r.sku in PRODUCTS and r.quantity is not None:
            S.on_hand[r.sku] = float(r.quantity)
            n += 1
    S.review = []
    say("success", f"{n} count(s) confirmed. Forecast updated.")
    return state()


@app.post("/api/review/clear")
def clear_review():
    S.review = []
    return state()


@app.post("/api/run")
def run():
    fc = forecast(S.on_hand, S.book.pending(), S.bookings)
    sh = shortages(fc)
    if not sh:
        say("info", "No shortages: nothing to order.")
        return state()
    S.agent = make_agent(S.live)
    S.agent_prev = None
    S.agent_prop = S.agent.propose(sh, now=DEMO_NOW.replace(tzinfo=TZ))
    S.book.propose(BASKET_ID, to_lines(S.agent_prop))
    say("success", "Iris found suppliers for every shortage." if S.book.latest(BASKET_ID).lines
        else "No qualifying on-time offer found.")
    return state()


@app.post("/api/reject")
def reject(body: RevisionIn):
    if S.agent is None or S.agent_prop is None:
        raise HTTPException(409, "Run Iris first.")
    try:
        S.book.reject(BASKET_ID, body.revision, body.feedback)
    except OrderError as e:
        raise HTTPException(409, str(e))
    old = S.agent_prop
    S.agent_prev = old
    S.agent_prop = S.agent.reject(old, feedback=body.feedback, now=DEMO_NOW.replace(tzinfo=TZ))
    S.book.propose(BASKET_ID, to_lines(S.agent_prop), feedback=body.feedback or "rejected",
                   excluded_offer_ids=S.agent_prop.excluded_offer_ids,
                   change_note=" · ".join(diff(old, S.agent_prop)))
    say("info", f"r{body.revision} rejected. No order placed. Searched again without the rejected offers.")
    return state()


@app.post("/api/approve")
def approve(body: RevisionIn):
    try:
        order, created = S.book.approve(BASKET_ID, body.revision, DEMO_NOW)
    except OrderError as e:
        raise HTTPException(409, str(e))
    S.last_order_created = created
    if created:
        say("success", f"Order {order.order_id} placed (simulated).")
    else:
        say("info", f"Still {len(S.book.orders)} order(s): {order.order_id} already exists, nothing duplicated.")
    return state()


@app.post("/api/line/edit")
def edit_line(body: LineIn):
    try:
        S.book.edit_line(BASKET_ID, body.sku, body.packs)
    except OrderError as e:
        raise HTTPException(409, str(e))
    say("info", "Quantity changed: the new revision needs its own approval.")
    return state()


@app.post("/api/line/remove")
def remove_line(body: LineIn):
    try:
        S.book.remove_line(BASKET_ID, body.sku)
    except OrderError as e:
        raise HTTPException(409, str(e))
    return state()


@app.post("/api/received")
def received(body: OrderIn):
    S.on_hand = S.book.mark_received(body.order_id, S.on_hand)
    say("success", f"{body.order_id} received: on-hand updated.")
    return state()
