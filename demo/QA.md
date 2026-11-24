# Iris: judge Q&A (say it out loud)

**1. What is live and what is simulated?**
Live: the photo is read by a Nebius Token Factory vision model (`google/gemma-3-27b-it`) and pasted text by an LLM (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`). Simulated: bookings are synthetic and orders are simulated, so no real customers, payments or purchases.

**2. Are the supplier offers real?**
By default a labelled fixture, so the demo repeats exactly. A toggle turns on live Tavily search. Live listings without a readable price, pack size or delivery date are kept as leads, never proposed.

**3. Why not let the LLM pick the supplier?**
Because it can't be trusted with money or dates. Code computes demand, shortage, packs, cost and ETA, enforces same product and size and on-time delivery, and ranks deterministically. The AI reads the photo, plans the search and explains the result.

**4. What if the photo is blurry or the count is wrong?**
Nothing changes until the owner confirms. Guessed or unclear counts are never auto-ticked, so the owner has to tick or correct each row before it reaches the forecast.

**5. How would it plug into Fresha?**
Today it takes bookings plus a recipe per service (for example textured crop uses a set amount of clay). Next step is reading real bookings from Fresha's API in place of the synthetic file. The forecast code doesn't change.

**6. BulkBarber is cheaper per ml, so why does it lose?**
BulkBarber is £9.00 per 100 ml against BarberHub's £13.25, but it arrives Monday 30. That misses 16 at-risk bookings, so it is shown as LATE and can't win.

**7. What stops duplicate orders?**
Approval is idempotent per approved revision. Approving r2 twice still gives one order, PO-BARBER-W48-r2, and the stock shows as incoming, separate from on-hand.

**8. Data and privacy?**
All data is synthetic and the photo is staged. API keys live in `.env` and are never committed. Supplier page text is treated as evidence, not as instructions, and it never reaches write tools.

**9. Which NVIDIA blueprints did you use, and how?**
We reimplemented the patterns and imported no upstream code. Reference copies with commits are in `blueprints/README.md`.
- Retail Shopping Assistant `c20044b`: typed, read-only search tool.
- Retail Catalog Enrichment `debc251`: visual product attributes from the photo.
- Multi-Agent Warehouse `a6404ed`: forecast kept separate from replenishment.
- Retail Agentic Commerce `83c5f22`: merchant-controlled order lifecycle.

**10. Does it work for other businesses, and what's next?**
Yes. A tattoo studio or nail salon only needs different service recipes and product data on the same schema. Next: real Fresha bookings, supplier checkout via ACP/UCP, a received-stock workflow, and tattoo and nail presets.
