# Iris: 3-minute demo script

Before going on stage: `streamlit run app.py`, click **Reset demo** in the sidebar, live search **off**. Have `demo/stocktake.png` ready, and the backup recording or screenshots in `demo/` in case the laptop fails.

| Time | Say | Do |
|---|---|---|
| 0:00 | "Barbershops run out of the product they need for the bookings they already have. Textured crops are up, the clay runs out on Friday, and the owner finds out mid-cut." | App open on section 1 |
| 0:20 | "Iris starts from what's booked. A stock count is just a photo of the count sheet. A Nebius vision model reads it, and the owner confirms before anything changes." | Photo tab → upload `stocktake.png` → **Read photo** → point at the review rows and the note (Nebius VLM or replay) → **Confirm counts** |
| 0:50 | "Bookings times product recipes gives 7-day demand, and we project the stock in time order. The first booking we can't serve is Friday 11:00, a textured crop. Twenty-two bookings are at risk." | Scroll to section 2, point at the red banner and the chart |
| 1:15 | "The sourcing agent calls one typed, read-only supplier search tool. We adapted that pattern from NVIDIA's Retail Shopping Assistant. The rules are enforced in code: same product, same size, delivered before Friday." | **Run Iris** → open *Offers considered* → point at CutPrice (£6.55 cheaper but LATE: arrives Mon, misses the Friday bookings) and the leads (wrong size, no ETA) |
| 1:45 | "Say I don't trust BarberSupply. I reject with a reason, and Iris searches again without them. Still no order." | Type "not BarberSupply, they were late last time" → **Reject and search again** → point at r2, SalonDirect, the feedback caption and *Simulated orders: 0* |
| 2:10 | "Only the owner's approval places an order. One click gives one order, and the stock shows as incoming, separate from what's on the shelf. Clicking again doesn't duplicate it." | **Approve r2** → the green "Covered" banner → **Approve r2 again** → still 1 order |
| 2:35 | "What works: photo and text intake, the forecast, evidence-checked sourcing, and reject, retry, approve. Bookings and orders are simulated. Next: real Fresha bookings and agentic checkout with suppliers." | Section 4: bookings protected and revenue covered |

Fallbacks: if Nebius is down, the photo path uses the labelled replay (the review note says REPLAY). If the photo upload misbehaves, use the **Pasted text** tab: `1 x Brand X Matte Clay 100 ml, 380 neck strips`.
