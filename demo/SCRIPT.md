# Iris: 3-minute demo script

Two versions. Use **React UI** if the 19:15 go/no-go is green, otherwise the **Streamlit fallback** below. Same story, same numbers.

## React UI (if go at 19:15)

Before going on stage: `.venv/bin/uvicorn server:app --port 8000`, then in `web/`: `npm run dev` (http://localhost:5173). Call `POST /api/reset` (or the reset button), live search **off**. Backup: the Streamlit fallback and the screenshots in `demo/`.

| Time | Say | Do |
|---|---|---|
| 0:00 | "Barbershops run out of the product they need for the bookings they already have. Textured crops are up, the clay runs out on Friday, and the owner finds out mid-cut." | Stepper on **Stock** |
| 0:20 | "A stock count is just a photo of the count sheet. A Nebius vision model reads it, and the owner confirms before anything changes." | **Use sample photo** → point at the review rows and the LIVE/REPLAY badge → tick the rows → **Confirm** |
| 0:50 | "Bookings times product recipes gives 7-day demand, projected in time order. The red dot is the first booking we can't serve: Friday 11:00, a textured crop. Twenty-two bookings are at risk." | Stepper moves to **Forecast**: point at the KPI hero, then the red marker on the run-out chart |
| 1:15 | "The sourcing agent calls one typed, read-only supplier search tool, adapted from NVIDIA's Retail Shopping Assistant. Code enforces same product, same size, delivered before Friday." | **Run Iris** → basket r1: BarberHub £26.50 → point at the late-but-cheaper card (BulkBarber, misses bookings) and the evidence labels |
| 1:45 | "Say I don't trust BarberHub. I reject with a reason, and Iris searches again without them. Still no order." | Type "not BarberHub, they were late last time" → **Reject** → r2: ShearCo £37.95, the change note, *no order placed* |
| 2:10 | "Only the owner's approval places an order. One click, one order, and the stock shows as incoming. Clicking again doesn't duplicate it." | **Approve** → order PO-BARBER-W48-r2 → back on the chart: dashed red line without the order, green line with it, "order lands Thu 09:00" → **Approve** again → still 1 order |
| 2:35 | "What works: photo and text intake, the forecast, evidence-checked sourcing, and reject, retry, approve. Bookings and orders are simulated. Next: real Fresha bookings and agentic checkout with suppliers." | KPI hero: 22 bookings protected · £602 covered |

## Streamlit fallback

Before going on stage: `streamlit run app.py`, click **Reset demo** in the sidebar, live search **off**. Have `demo/stocktake.png` ready, and the backup recording or screenshots in `demo/` in case the laptop fails.

| Time | Say | Do |
|---|---|---|
| 0:00 | "Barbershops run out of the product they need for the bookings they already have. Textured crops are up, the clay runs out on Friday, and the owner finds out mid-cut." | App open on section 1 |
| 0:20 | "Iris starts from what's booked. A stock count is just a photo of the count sheet. A Nebius vision model reads it, and the owner confirms before anything changes." | Photo tab → upload `stocktake.png` → **Read photo** → point at the review rows and the note (Nebius VLM or replay) → **Confirm counts** |
| 0:50 | "Bookings times product recipes gives 7-day demand, and we project the stock in time order. The first booking we can't serve is Friday 11:00, a textured crop. Twenty-two bookings are at risk." | Scroll to section 2, point at the red banner and the chart |
| 1:15 | "The sourcing agent calls one typed, read-only supplier search tool. We adapted that pattern from NVIDIA's Retail Shopping Assistant. The rules are enforced in code: same product, same size, delivered before Friday." | **Run Iris** → open *Offers considered* → point at the bulk seller (cheaper per ml but LATE, misses bookings) and the leads (wrong size, no ETA) |
| 1:45 | "Say I don't trust BarberHub. I reject with a reason, and Iris searches again without them. Still no order." | Type "not BarberHub, they were late last time" → **Reject and search again** → point at r2, ShearCo, the feedback caption and *Simulated orders: 0* |
| 2:10 | "Only the owner's approval places an order. One click gives one order, and the stock shows as incoming, separate from what's on the shelf. Clicking again doesn't duplicate it." | **Approve r2** → the green "Covered" banner → **Approve r2 again** → still 1 order |
| 2:35 | "What works: photo and text intake, the forecast, evidence-checked sourcing, and reject, retry, approve. Bookings and orders are simulated. Next: real Fresha bookings and agentic checkout with suppliers." | Section 4: bookings protected and revenue covered |

Fallbacks: if Nebius is down, the photo path uses the labelled replay (the review note says REPLAY). If the photo upload misbehaves, use the **Pasted text** tab: `1 x Northline Matte Clay 100 ml, 380 neck strips`.
