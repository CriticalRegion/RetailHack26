"""Iris - never run out of what's booked.

Streamlit flow: stock review -> run-out forecast -> supplier basket (approve / edit /
remove / reject with feedback) -> simulated order with pending vs on-hand stock.

Until iris.calc / iris.sourcing / iris.intake land, the app runs on the built-in
FIXTURE below (labelled in the UI). t6 swaps the `forecast`, `source_offers` and
`extract_*` adapters for the real modules.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import datetime, timedelta

import altair as alt
import pandas as pd
import streamlit as st

from iris.orders import OrderBook, OrderError, ProposalLine

# ---------------------------------------------------------------- fixture (FAKE)
DEMO_NOW = datetime(2026, 11, 24, 9, 0)  # Tue 24 Nov 2026, 09:00 Europe/London
BASKET_ID = "BARBER-W48"

PRODUCTS = {
    "CLAY-MATTE-100": {"name": "Brand X Matte Clay 100 ml", "unit": "ml",
                       "aliases": ["matte clay", "clay", "brand x"]},
    "NECK-STRIP": {"name": "Neck strips", "unit": "units", "aliases": ["neck strip", "strips"]},
}
SERVICES = {  # service -> (price GBP, recipe {sku: qty in base unit})
    "Textured crop": (28, {"CLAY-MATTE-100": 6, "NECK-STRIP": 1}),
    "Skin fade": (24, {"CLAY-MATTE-100": 2, "NECK-STRIP": 1}),
    "Scissor cut": (30, {"CLAY-MATTE-100": 3, "NECK-STRIP": 1}),
}
SEED_ON_HAND = {"CLAY-MATTE-100": 120.0, "NECK-STRIP": 400.0}

_DAY_PLAN = {  # day offset from DEMO_NOW -> services in hourly slots from 09:00
    0: ["Textured crop", "Skin fade", "Textured crop", "Scissor cut", "Textured crop", "Skin fade", "Textured crop", "Scissor cut", "Skin fade"],
    1: ["Textured crop", "Skin fade", "Textured crop", "Scissor cut", "Textured crop", "Skin fade", "Textured crop", "Scissor cut", "Skin fade"],
    2: ["Skin fade", "Textured crop", "Textured crop", "Scissor cut", "Skin fade", "Textured crop", "Textured crop", "Scissor cut", "Skin fade"],
    3: ["Textured crop", "Textured crop", "Textured crop", "Skin fade", "Textured crop", "Textured crop", "Scissor cut", "Textured crop", "Skin fade"],
    4: ["Textured crop", "Textured crop", "Textured crop", "Textured crop", "Skin fade", "Textured crop", "Textured crop", "Textured crop", "Scissor cut"],
    6: ["Textured crop", "Skin fade", "Textured crop", "Scissor cut", "Textured crop", "Skin fade"],
}  # day 5 (Sunday) closed


def demo_bookings() -> list[dict]:
    out, n = [], 1
    for day, slots in _DAY_PLAN.items():
        for i, svc in enumerate(slots):
            out.append({"id": f"BK-{n:03d}", "service": svc,
                        "time": DEMO_NOW.replace(hour=9) + timedelta(days=day, hours=i), "status": "booked"})
            n += 1
    out.append({"id": "BK-900", "service": "Textured crop", "time": DEMO_NOW + timedelta(days=2, hours=2),
                "status": "cancelled"})
    return out


DEMO_OFFERS = [  # labelled fixture listings for the hero SKU
    {"offer_id": "OF-BSU-100", "supplier": "BarberSupply UK", "title": "Brand X Matte Clay 100 ml",
     "sku": "CLAY-MATTE-100", "size_ml": 100, "units_per_pack": 100, "pack_price": 8.50, "shipping": 3.95,
     "eta": datetime(2026, 11, 26, 12, 0), "source": "fixture:barbersupply-uk"},
    {"offer_id": "OF-SD-3PK", "supplier": "SalonDirect", "title": "Brand X Matte Clay 100 ml (3-pack)",
     "sku": "CLAY-MATTE-100", "size_ml": 100, "units_per_pack": 300, "pack_price": 24.00, "shipping": 0.0,
     "eta": datetime(2026, 11, 26, 16, 0), "source": "fixture:salondirect"},
    {"offer_id": "OF-CPW-100", "supplier": "CutPrice Wholesale", "title": "Brand X Matte Clay 100 ml",
     "sku": "CLAY-MATTE-100", "size_ml": 100, "units_per_pack": 100, "pack_price": 6.20, "shipping": 2.00,
     "eta": datetime(2026, 11, 30, 10, 0), "source": "fixture:cutprice-wholesale"},
    {"offer_id": "OF-BSU-50", "supplier": "BarberSupply UK", "title": "Brand X Matte Clay 50 ml",
     "sku": "CLAY-MATTE-100", "size_ml": 50, "units_per_pack": 50, "pack_price": 4.90, "shipping": 3.95,
     "eta": datetime(2026, 11, 26, 12, 0), "source": "fixture:barbersupply-uk"},
]


# ---------------------------------------------------------------- adapters
@dataclass
class ForecastLine:
    sku: str
    usage: float
    on_hand: float
    incoming: float
    uncovered: float
    first_at_risk: dict | None
    at_risk: list[dict]
    contributing: dict  # service -> booking count
    series: list[tuple[datetime, float]]


def forecast(on_hand: dict, pending: list, bookings: list[dict]) -> dict[str, ForecastLine]:
    """Time-ordered stock projection over 7 days. Inbound counts once, at its ETA."""
    end = DEMO_NOW + timedelta(days=7)
    live = sorted((b for b in bookings if b["status"] == "booked" and DEMO_NOW <= b["time"] < end),
                  key=lambda b: b["time"])
    out = {}
    for sku in PRODUCTS:
        events = [(b["time"], 1, -SERVICES[b["service"]][1].get(sku, 0), b) for b in live
                  if SERVICES[b["service"]][1].get(sku)]
        events += [(l.eta, 0, l.qty, None) for l in pending if l.sku == sku and l.eta < end]
        events.sort(key=lambda e: (e[0], e[1]))  # deliveries before a same-time booking
        level, low = on_hand.get(sku, 0.0), 0.0
        series, at_risk, contributing = [(DEMO_NOW, level)], [], {}
        for t, _, delta, b in events:
            level += delta
            series.append((t, level))
            if b is not None:
                contributing[b["service"]] = contributing.get(b["service"], 0) + 1
                if level < 0:
                    at_risk.append(b)
            low = min(low, level)
        out[sku] = ForecastLine(
            sku=sku,
            usage=sum(-d for _, _, d, b in events if b is not None),
            on_hand=on_hand.get(sku, 0.0),
            incoming=sum(l.qty for l in pending if l.sku == sku),
            uncovered=round(-low, 1),
            first_at_risk=at_risk[0] if at_risk else None,
            at_risk=at_risk,
            contributing=contributing,
            series=series,
        )
    return out


def source_offers(line: ForecastLine, excluded: set[str]) -> dict:
    """Filter + rank fixture offers for one shortage. Returns ranked/late/leads."""
    need_by = line.first_at_risk["time"]
    ranked, late, leads = [], [], []
    for o in DEMO_OFFERS:
        if o["sku"] != line.sku:
            continue
        if o["size_ml"] != 100:
            leads.append({**o, "why": f"wrong size ({o['size_ml']} ml)"})
            continue
        if o["offer_id"] in excluded:
            continue
        packs = math.ceil(line.uncovered / o["units_per_pack"])
        cand = {**o, "packs": packs, "delivered": round(packs * o["pack_price"] + o["shipping"], 2)}
        (ranked if o["eta"] <= need_by else late).append(cand)
    ranked.sort(key=lambda o: o["delivered"])
    late.sort(key=lambda o: o["delivered"])
    for o in late:
        o["missed"] = [b for b in line.at_risk if b["time"] < o["eta"]]
    return {"ranked": ranked, "late": late, "leads": leads}


def reason_for(best: dict, line: ForecastLine, late: list[dict]) -> str:
    b = line.first_at_risk
    lead = (b["time"] - best["eta"])
    hrs = int(lead.total_seconds() // 3600)
    txt = (f"Covers the {line.uncovered:g} ml gap; arrives {best['eta']:%a %H:%M}, {hrs}h before the "
           f"{b['time']:%a %H:%M} {b['service'].lower()}.")
    if late:
        c = late[0]
        txt += (f" {c['supplier']} is £{best['delivered'] - c['delivered']:.2f} cheaper but arrives "
                f"{c['eta']:%a}, after {len(c['missed'])} at-risk bookings.")
    return txt


def build_lines(fc: dict[str, ForecastLine], excluded: set[str]) -> tuple[list[ProposalLine], dict]:
    lines, detail = [], {}
    for sku, line in fc.items():
        if line.uncovered <= 0:
            continue
        res = source_offers(line, excluded)
        detail[sku] = res
        if res["ranked"]:
            best = res["ranked"][0]
            lines.append(ProposalLine(
                sku=sku, offer_id=best["offer_id"], supplier=best["supplier"], packs=best["packs"],
                units_per_pack=best["units_per_pack"], pack_price=best["pack_price"],
                shipping=best["shipping"], eta=best["eta"], source=best["source"],
                reason=reason_for(best, line, res["late"])))
    return lines, detail


def extract_text(text: str) -> list[dict]:
    """FAKE text intake: '2 x Brand X Matte Clay 100 ml, 35 neck strips' -> review rows."""
    rows = []
    for part in re.split(r"[,\n;]+", text):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(\d+(?:\.\d+)?)\s*[x×]?\s*(.*)", part, re.I)
        qty, label = (float(m.group(1)), m.group(2)) if m else (None, part)
        sku = next((s for s, p in PRODUCTS.items() if any(a in label.lower() for a in p["aliases"])), None)
        if sku == "CLAY-MATTE-100" and qty is not None:
            size = re.search(r"(\d+)\s*ml", label, re.I)
            qty = qty * (float(size.group(1)) if size else 100)
        rows.append({"confirm": sku is not None and qty is not None, "raw label": part, "sku": sku or "?",
                     "quantity": qty, "unit": PRODUCTS[sku]["unit"] if sku else "?",
                     "note": "" if sku else "unmatched - pick a SKU"})
    return rows


def extract_photo(_img) -> list[dict]:
    """FAKE photo intake: labelled replay of the staged shelf photo."""
    return [
        {"confirm": True, "raw label": "Brand X Matte Clay 100ml x1 + 1 open (~20%)", "sku": "CLAY-MATTE-100",
         "quantity": 120.0, "unit": "ml", "note": "open tub estimated"},
        {"confirm": True, "raw label": "Neck strips box (4 x 100)", "sku": "NECK-STRIP",
         "quantity": 400.0, "unit": "units", "note": ""},
    ]


# ---------------------------------------------------------------- state
def init_state():
    ss = st.session_state
    if "book" not in ss:
        ss.book = OrderBook()
        ss.on_hand = dict(SEED_ON_HAND)
        ss.bookings = demo_bookings()
        ss.review = []
        ss.detail = {}
        ss.flash = None


def do_source(feedback: str = "", excluded: tuple = (), note: str = ""):
    ss = st.session_state
    fc = forecast(ss.on_hand, ss.book.pending(), ss.bookings)
    lines, ss.detail = build_lines(fc, set(excluded))
    ss.book.propose(BASKET_ID, lines, feedback=feedback, excluded_offer_ids=excluded, change_note=note)


def flash(kind: str, msg: str):
    st.session_state.flash = (kind, msg)


# ---------------------------------------------------------------- UI
st.set_page_config(page_title="Iris", page_icon="🪞", layout="wide")
init_state()
ss = st.session_state
book: OrderBook = ss.book

with st.sidebar:
    st.markdown("### Iris")
    st.caption("Never run out of what's booked.")
    st.write(f"**Shop:** Old St Barbers (demo)  \n**Clock:** {DEMO_NOW:%a %d %b %Y %H:%M} London")
    st.warning("FIXTURE MODE: synthetic bookings, labelled supplier offers, replayed photo extraction.")
    if st.button("Reset demo", width="stretch"):
        for k in list(ss.keys()):
            del ss[k]
        st.rerun()

st.title("Iris")
st.caption("Next week's appointments + your stock count -> a supplier basket you approve.")
if ss.flash:
    getattr(st, ss.flash[0])(ss.flash[1])
    ss.flash = None

# 1. Stock ---------------------------------------------------------------------
st.header("1 · Stock count")
c1, c2 = st.columns([3, 2])
with c1:
    t_photo, t_text = st.tabs(["Photo", "Pasted text"])
    with t_photo:
        img = st.file_uploader("Stocktake photo", type=["png", "jpg", "jpeg"])
        if st.button("Read photo", disabled=img is None):
            ss.review = extract_photo(img)
    with t_text:
        txt = st.text_area("Stock notes", "1 x Brand X Matte Clay 100 ml, 380 neck strips", height=80)
        if st.button("Read text"):
            ss.review = extract_text(txt)
    if ss.review:
        st.caption("Review what Iris read. Only ticked rows overwrite on-hand stock.")
        edited = st.data_editor(pd.DataFrame(ss.review), key="review_editor", hide_index=True,
                                disabled=["raw label", "unit", "note"],
                                column_config={"sku": st.column_config.SelectboxColumn(
                                    options=list(PRODUCTS) + ["?"])})
        if st.button("Confirm counts", type="primary"):
            n = 0
            for r in edited.to_dict("records"):
                if r["confirm"] and r["sku"] in PRODUCTS and r["quantity"] is not None and not pd.isna(r["quantity"]):
                    ss.on_hand[r["sku"]] = float(r["quantity"])
                    n += 1
            ss.review = []
            flash("success", f"{n} count(s) confirmed. Forecast updated.")
            st.rerun()
with c2:
    pend = book.pending_by_sku()
    st.dataframe(pd.DataFrame([{"product": p["name"], "on hand": f"{ss.on_hand.get(s, 0):g} {p['unit']}",
                                "incoming (pending)": f"{pend.get(s, 0):g} {p['unit']}"}
                               for s, p in PRODUCTS.items()]), hide_index=True, width="stretch")

# 2. Forecast ------------------------------------------------------------------
fc = forecast(ss.on_hand, book.pending(), ss.bookings)
received = {}
for _l in book.inbound:
    if _l.received:
        received[_l.sku] = received.get(_l.sku, 0) + _l.qty
baseline = forecast({k: v - received.get(k, 0) for k, v in ss.on_hand.items()}, [], ss.bookings)  # no orders
st.header("2 · Next 7 days")
for sku, line in fc.items():
    p = PRODUCTS[sku]
    cols = st.columns(4)
    cols[0].metric(p["name"], f"{line.usage:g} {p['unit']} booked")
    cols[1].metric("On hand", f"{line.on_hand:g}")
    cols[2].metric("Incoming", f"{line.incoming:g}")
    cols[3].metric("Uncovered", f"{line.uncovered:g}", delta=None if not line.uncovered else "short",
                   delta_color="inverse")
    if line.first_at_risk:
        b = line.first_at_risk
        mix = ", ".join(f"{n} × {s.lower()}" for s, n in line.contributing.items())
        st.error(f"**Runs out {b['time']:%a %d %b %H:%M}**: {b['id']} {b['service'].lower()} can't be served. "
                 f"{len(line.at_risk)} bookings at risk. Demand comes from {mix}.")
    elif sku == "CLAY-MATTE-100" and baseline[sku].first_at_risk:
        st.success(f"Covered: incoming stock protects all {len(baseline[sku].at_risk)} bookings that were at risk.")
    if sku == "CLAY-MATTE-100":
        df = pd.DataFrame(line.series, columns=["time", "projected"])
        chart = alt.Chart(df).mark_line(interpolate="step-after").encode(
            x=alt.X("time:T", title=None), y=alt.Y("projected:Q", title=f"projected {p['unit']}"))
        zero = alt.Chart(pd.DataFrame({"y": [0]})).mark_rule(color="#c0392b", strokeDash=[4, 4]).encode(y="y:Q")
        layers = [chart, zero]
        if line.first_at_risk:
            pt = pd.DataFrame([{"time": line.first_at_risk["time"], "projected": 0,
                                "label": f"first at risk: {line.first_at_risk['time']:%a %H:%M}"}])
            layers.append(alt.Chart(pt).mark_point(color="#c0392b", size=120, filled=True).encode(
                x="time:T", y="projected:Q", tooltip=["label"]))
        st.altair_chart(alt.layer(*layers).properties(height=220), width="stretch")

# 3. Basket --------------------------------------------------------------------
st.header("3 · Supplier basket")
prop = book.latest(BASKET_ID)
short = [s for s, l in fc.items() if l.uncovered > 0]
if prop is None or prop.status in ("approved",):
    if short:
        if st.button("Run Iris: find suppliers", type="primary"):
            do_source()
            st.rerun()
    elif prop is None:
        st.info("No shortages: nothing to order.")

if prop is not None:
    st.subheader(f"Proposal r{prop.revision} · {prop.status.upper()} · £{prop.total:.2f}")
    if prop.feedback:
        st.caption(f"Revised after feedback: “{prop.feedback}” · excluded: {', '.join(prop.excluded_offer_ids)}")
    if prop.change_note:
        st.caption(f"Change: {prop.change_note}")
    if not prop.lines:
        st.warning("No qualifying on-time offer left. Unmet need shown below; late options are fallbacks only.")
    for l in prop.lines:
        with st.container(border=True):
            a, b2, c, d = st.columns([3, 2, 2, 2])
            a.markdown(f"**{PRODUCTS[l.sku]['name']}** from **{l.supplier}**  \n{l.reason}")
            a.caption(f"offer {l.offer_id} · source {l.source}")
            b2.metric("Packs", l.packs, help=f"{l.units_per_pack:g} {PRODUCTS[l.sku]['unit']} per pack")
            c.metric("Line total", f"£{l.total:.2f}", help=f"£{l.pack_price:.2f}/pack + £{l.shipping:.2f} shipping")
            d.metric("ETA", f"{l.eta:%a %H:%M}")
            if prop.status == "proposed":
                e1, e2, e3 = st.columns([2, 1, 1])
                newp = e1.number_input("Packs", 0, 50, l.packs, key=f"p_{prop.revision}_{l.sku}",
                                       label_visibility="collapsed")
                if e2.button("Save qty", key=f"s_{prop.revision}_{l.sku}", disabled=newp == l.packs):
                    book.edit_line(BASKET_ID, l.sku, int(newp))
                    flash("info", "Quantity changed: new revision needs its own approval.")
                    st.rerun()
                if e3.button("Remove", key=f"r_{prop.revision}_{l.sku}"):
                    book.remove_line(BASKET_ID, l.sku)
                    st.rerun()

    for sku, res in ss.detail.items():
        with st.expander(f"Offers considered for {PRODUCTS[sku]['name']}"):
            rows = [{"supplier": o["supplier"], "status": "on time", "packs": o["packs"], "delivered £": o["delivered"],
                     "ETA": f"{o['eta']:%a %d %H:%M}", "source": o["source"]} for o in res["ranked"]]
            rows += [{"supplier": o["supplier"], "status": f"LATE: {len(o['missed'])} bookings missed",
                      "packs": o["packs"], "delivered £": o["delivered"], "ETA": f"{o['eta']:%a %d %H:%M}",
                      "source": o["source"]} for o in res["late"]]
            rows += [{"supplier": o["supplier"], "status": f"lead only: {o['why']}", "packs": None,
                      "delivered £": None, "ETA": f"{o['eta']:%a %d %H:%M}", "source": o["source"]}
                     for o in res["leads"]]
            excl = [o for o in DEMO_OFFERS if o["offer_id"] in prop.excluded_offer_ids]
            rows += [{"supplier": o["supplier"], "status": "excluded by you", "packs": None, "delivered £": None,
                      "ETA": f"{o['eta']:%a %d %H:%M}", "source": o["source"]} for o in excl]
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")

    if prop.status == "proposed":
        ca, cr = st.columns(2)
        with ca:
            if st.button(f"Approve r{prop.revision} · £{prop.total:.2f}", type="primary",
                         disabled=not prop.lines, width="stretch"):
                try:
                    order, created = book.approve(BASKET_ID, prop.revision, DEMO_NOW)
                    flash("success", f"Order {order.order_id} placed (simulated).")
                except OrderError as e:
                    flash("error", str(e))
                st.rerun()
        with cr:
            reason = st.text_input("Reject with feedback", placeholder="e.g. BarberSupply was late last time")
            if st.button("Reject and search again", width="stretch"):
                rej = book.reject(BASKET_ID, prop.revision, reason)
                do_source(feedback=reason or "rejected", excluded=rej.excluded_offer_ids,
                          note=f"excluded {', '.join(rej.excluded_offer_ids)}")
                flash("info", f"r{prop.revision} rejected. No order placed. Searching again without the rejected offers.")
                st.rerun()
    elif prop.status == "approved":
        if st.button(f"Approve r{prop.revision} again (duplicate test)"):
            order, created = book.approve(BASKET_ID, prop.revision, DEMO_NOW)
            flash("info" if not created else "warning",
                  f"Still {len(book.orders)} order(s): {order.order_id} already exists, nothing duplicated.")
            st.rerun()

    hist = book.history(BASKET_ID)
    if len(hist) > 1:
        with st.expander("Revision history"):
            st.dataframe(pd.DataFrame([{
                "rev": p.revision, "status": p.status, "total £": p.total,
                "lines": "; ".join(f"{l.supplier} × {l.packs}" for l in p.lines) or "(empty)",
                "feedback / change": p.rejection or p.change_note or p.feedback} for p in hist]),
                hide_index=True, width="stretch")

# 4. Orders --------------------------------------------------------------------
st.header("4 · Orders and incoming stock")
st.metric("Simulated orders", len(book.orders))
if not book.orders:
    st.caption("No order yet. Only approving a proposal creates one.")
for oid, o in book.orders.items():
    with st.container(border=True):
        pending = [l for l in book.inbound if l.order_id == oid and not l.received]
        st.markdown(f"**{oid}** · r{o.revision} · £{o.total:.2f} · "
                    + ("pending delivery" if pending else "received"))
        st.write(", ".join(f"{l.packs} × {l.supplier} {PRODUCTS[l.sku]['name']} (ETA {l.eta:%a %H:%M})"
                           for l in o.lines))
        if pending and st.button("Mark received", key=f"recv_{oid}"):
            ss.on_hand = book.mark_received(oid, ss.on_hand)
            flash("success", f"{oid} received: on-hand updated, nothing left pending.")
            st.rerun()
if book.orders:
    b0, b1 = baseline["CLAY-MATTE-100"], fc["CLAY-MATTE-100"]
    protected = {b["id"] for b in b0.at_risk} - {b["id"] for b in b1.at_risk}
    rev = sum(SERVICES[b["service"]][0] for b in b0.at_risk if b["id"] in protected)
    st.success(f"{len(protected)} bookings protected · estimated booking revenue covered £{rev} "
               f"(separate from supplier price).")
