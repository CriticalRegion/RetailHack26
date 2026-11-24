"""Iris - never run out of what's booked.

Streamlit flow: stock review -> run-out forecast -> supplier basket (approve / edit /
remove / reject with feedback) -> simulated order with pending vs on-hand stock.

Until iris.calc / iris.sourcing / iris.intake land, the app runs on the built-in
fixture forecast below. Intake is iris.intake, sourcing iris.agent, orders iris.orders.
"""
from __future__ import annotations

from datetime import datetime

import altair as alt
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

load_dotenv()  # NEBIUS_*, IRIS_*_MODEL, TAVILY_API_KEY from .env (never committed)

from iris import intake, llm  # noqa: E402
from iris.agent import SourcingAgent, diff, nebius_llm
from iris.orders import OrderBook, OrderError, ProposalLine
from iris.calc import forecast, protected_bookings, shortages  # noqa: E402
from iris.data import DEMO_NOW, HERO_SKU, load_bookings, load_stocktake  # noqa: E402
from iris.data import PRODUCTS as DATA_PRODUCTS  # noqa: E402
from iris.sourcing import TZ, FixtureAdapter, default_adapters

# ---------------------------------------------------------------- shared data (synthetic, data/*.json)
BASKET_ID = "BARBER-W48"
PRODUCTS = {k: {"name": p.name, "unit": p.unit} for k, p in DATA_PRODUCTS.items()}
HERO = HERO_SKU


def naive(dt: datetime | None) -> datetime | None:
    return dt.astimezone(TZ).replace(tzinfo=None) if dt is not None and dt.tzinfo else dt


def to_lines(ap) -> list[ProposalLine]:
    """t4 agent proposal -> order-book lines (only selected, on-time offers can be ordered)."""
    out = []
    for l in ap.lines:
        r = l.selected
        if l.status == "unmet" or r is None:
            continue
        o = r.offer
        out.append(ProposalLine(
            sku=l.sku, offer_id=o.offer_id, supplier=o.supplier, packs=r.packs,
            units_per_pack=o.base_units_per_pack(), pack_price=o.pack_price, shipping=o.shipping or 0.0,
            eta=naive(o.eta), source=o.evidence.url or o.evidence.label,
            reason=l.reason))
    return out


# ---------------------------------------------------------------- state
def init_state():
    ss = st.session_state
    if "book" not in ss:
        ss.book = OrderBook()
        ss.on_hand = load_stocktake()
        ss.bookings = load_bookings()
        ss.review = []
        ss.agent = None
        ss.agent_prop = None
        ss.flash = None


def make_agent(live: bool) -> SourcingAgent:
    if live:
        return SourcingAgent(adapters=default_adapters(), llm=nebius_llm())
    return SourcingAgent(adapters=[FixtureAdapter()], llm=None)


def do_source():
    ss = st.session_state
    fc = forecast(ss.on_hand, ss.book.pending(), ss.bookings)
    ss.agent = make_agent(ss.get("live", False))
    ss.agent_prop = ss.agent.propose(shortages(fc), now=DEMO_NOW.replace(tzinfo=TZ))
    ss.book.propose(BASKET_ID, to_lines(ss.agent_prop))


def do_reject(revision: int, reason: str):
    ss = st.session_state
    ss.book.reject(BASKET_ID, revision, reason)
    old = ss.agent_prop
    ss.agent_prop = ss.agent.reject(old, feedback=reason, now=DEMO_NOW.replace(tzinfo=TZ))
    ss.book.propose(BASKET_ID, to_lines(ss.agent_prop), feedback=reason or "rejected",
                    excluded_offer_ids=ss.agent_prop.excluded_offer_ids,
                    change_note=" · ".join(diff(old, ss.agent_prop)))


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
    st.toggle("Live search (Tavily + Nebius)", key="live",
              help="Off: labelled fixture offers, repeatable. On: live listings; unverifiable ones stay leads.")
    st.caption(f"Text intake: {'Nebius ' + llm.text_model() if llm.text_ready() else 'rule parser (fallback)'}  \n"
               f"Photo intake: {'Nebius ' + llm.vision_model() if llm.vision_ready() else 'labelled replay (fallback)'}")
    st.warning("Synthetic bookings and stock (FAKE). Supplier offers: "
               + ("live search + fixture." if ss.get("live") else "labelled fixture.")
               + " Orders are simulated.")
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
            ss.review = intake.extract("photo", img)
    with t_text:
        txt = st.text_area("Stock notes", "1 x Northline Matte Clay 100 ml, 380 neck strips", height=80)
        if st.button("Read text"):
            ss.review = intake.extract("text", txt)
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
    elif sku == HERO and baseline[sku].first_at_risk:
        st.success(f"Covered: incoming stock protects all {len(baseline[sku].at_risk)} bookings that were at risk.")
    if sku == HERO:
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

fc_before = forecast(ss.on_hand, [], ss.bookings)

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

    ap = ss.agent_prop
    for al in (ap.lines if ap else []):
        at_risk = fc_before.get(al.sku).at_risk if al.sku in fc_before else []
        if al.status == "unmet":
            st.warning(f"**{al.product}: no on-time offer left.** {al.reason}")
        with st.expander(f"Offers considered for {al.product} · search: {al.query.replace(chr(34), '')}"):
            rows = []
            for tag, r in (("selected", al.selected), ("alternative", al.alternative), ("late", al.late_option)):
                if r is None:
                    continue
                o = r.offer
                status = tag
                if r.on_time is False and o.eta:
                    status = f"LATE: misses {sum(1 for b in at_risk if b['time'] < naive(o.eta))} at-risk bookings"
                per100 = (round(r.delivered_cost / r.covered_qty * 100, 2)
                          if r.delivered_cost and r.covered_qty and al.unit == "ml" else None)
                rows.append({"supplier": o.supplier, "listing": o.title, "status": status, "packs": str(r.packs),
                             "delivered £": f"{r.delivered_cost:.2f}" if r.delivered_cost is not None else "",
                             "£ per 100 ml": f"{per100:.2f}" if per100 else "", "ETA": f"{naive(o.eta):%a %d %H:%M}" if o.eta else "unknown",
                             "evidence": o.evidence.url or o.evidence.label})
            for r in al.leads:
                o = r.offer
                rows.append({"supplier": o.supplier, "listing": o.title, "status": "lead: " + "; ".join(r.issues),
                             "packs": "", "delivered £": "", "£ per 100 ml": "",
                             "ETA": f"{naive(o.eta):%a %d %H:%M}" if o.eta else "unknown",
                             "evidence": o.evidence.url or o.evidence.label})
            if ap.excluded_offer_ids:
                st.caption("Excluded by you: " + ", ".join(ap.excluded_offer_ids))
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
            reason = st.text_input("Reject with feedback", placeholder="e.g. not BarberHub, they were late last time")
            if st.button("Reject and search again", width="stretch"):
                do_reject(prop.revision, reason)
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
        st.write(", ".join(f"{l.packs} pack(s) = {l.units:g} {PRODUCTS[l.sku]['unit']} of {PRODUCTS[l.sku]['name']} from {l.supplier} (ETA {l.eta:%a %H:%M})"
                           for l in o.lines))
        if pending and st.button("Mark received", key=f"recv_{oid}"):
            ss.on_hand = book.mark_received(oid, ss.on_hand)
            flash("success", f"{oid} received: on-hand updated, nothing left pending.")
            st.rerun()
if book.orders:
    n_prot, rev = protected_bookings(baseline, fc)
    st.success(f"{n_prot} bookings protected · estimated booking revenue covered £{rev:g} "
               f"(separate from supplier price).")
