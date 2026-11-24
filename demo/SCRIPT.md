# Iris: 3-minute demo script (presenter: Abhi)

Use the **React UI**. If anything breaks on stage, switch to the **Streamlit fallback** below: same story, same numbers.

## React UI

**Before going on stage (demo laptop):** `./scripts/dev.sh` (API :8000 + web http://localhost:5173), click **Reset demo** (top right), live supplier search **off**. Have `demo/screens/` open in a second tab as a last-resort backup.

| Time | Say | Do |
|---|---|---|
| 0:00 | "This is for the owner of a barbershop. They already know next week's demand, because it's in the booking book. But they still find out the clay is gone mid-cut." | Page top: point at **22 bookings at risk · runs out Fri 27 11:00** |
| 0:20 | "Iris starts with a stock count. It's just a photo of the count sheet, read by a vision model on Nebius Token Factory. Nothing changes until the owner ticks the rows." | **Use sample photo**. *Live it takes ~15 s: say "it's reading labels and counts" while it loads; if it hangs past 20 s, switch to **Pasted text** → **Read text** (~8 s).* Tick both rows → **Confirm 2 counts** |
| 0:50 | "Bookings times each service's product recipe gives the week's demand, projected in time order. The red marker is the first booking we can't serve: Friday at 11, a textured crop. Twenty-two bookings are at risk, £602 of revenue." | Point at the run-out chart: red marker, line dropping below zero |
| 1:15 | "Iris's sourcing agent calls one typed, read-only supplier search tool, a pattern from NVIDIA's Retail Shopping Assistant. The rules live in code: same product, same size, delivered before Friday. It proposes BarberHub at £26.50." | **Run Iris: find suppliers** → basket r1. Point at the **LATE · misses 16 bookings** card: "BulkBarber is cheapest per 100 ml, £9 against £13.25, but it arrives Monday, so it can't win." |
| 1:45 | "Say I don't trust BarberHub. I reject with a reason, and Iris searches again without them. Note: still no order." | Type `not BarberHub, they were late last time` → **Reject & search again** → r2 ShearCo £37.95, the change note, "no order placed" |
| 2:10 | "Only the owner's approval places an order. One click, one order, and the stock shows as incoming, separate from what's on the shelf. And if I click again, nothing is duplicated." | **Approve r2 · £37.95** → order PO-BARBER-W48-r2, "22 bookings protected · £602" → **Approve r2 again (duplicate test)** → toast "Still 1 order" |
| 2:35 | "What works today: photo and text intake on Nebius, the forecast, evidence-checked sourcing, and reject, retry, approve. Bookings and orders are simulated. What we learned: let the AI read and explain, but keep the maths and the order button in code. Next: real Fresha bookings and agentic checkout with suppliers." | Scroll back to the chart: the line with the order stays above zero |

**If asked:** answers to likely judge questions are in `demo/QA.md`.

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
