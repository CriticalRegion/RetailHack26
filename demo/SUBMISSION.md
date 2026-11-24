# BuilderBase entry (copy-paste)

**Name:** Iris

**Tagline:** Never run out of what's booked.

**Track:** Retail AI (Nebius / NVIDIA)

**Problem:** Appointment businesses consume stock during services, and they know their demand a week ahead from their bookings. Yet a barber still finds out the clay is gone in the middle of a textured crop.

**What we built:** Iris turns next week's bookings and a stock count into a time-ordered stock forecast and names the first booking that will run short (Northline Matte Clay, Fri 11:00). The count comes from a photo of the shelf, read by a Nebius-hosted vision model (`google/gemma-3-27b-it`), or from pasted notes, parsed by a Nebius-hosted LLM (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`), both through Nebius Token Factory. The owner confirms the rows before anything changes. A sourcing agent then calls a typed, read-only supplier search tool, adapted from the NVIDIA Retail Shopping Assistant's catalog-search pattern, and proposes a basket with price, delivery date and evidence. The LLM plans the search and phrases the reason; code computes every number and enforces same product and size, on-time delivery and deterministic ranking. The owner can edit, reject with feedback (Iris searches again without the rejected supplier), or approve. Approval places exactly one simulated order and tracks incoming stock separately from on-hand. The owner works in a React front end (Vite, Tailwind, Recharts run-out chart) over a small FastAPI JSON API, so all business logic stays in the tested Python modules. A Streamlit version of the same flow is the fallback.

**Demo numbers:** Iris proposes 2 x BarberHub at £26.50 (revision 1). The owner rejects it ("not BarberHub"), and revision 2 switches to ShearCo Supply at £37.95. Approving places one simulated order, PO-BARBER-W48-r2. That protects 22 bookings and covers £602 of booking revenue. Approving twice still leaves one order.

**What works:** photo/text intake with owner confirmation, 7-day forecast and first at-risk booking, supplier ranking with late-offer and wrong-size handling, reject and revised basket, idempotent approval. 17 headless acceptance checks pass (`scripts/acceptance.py`).

**Live vs simulated:**

| Part | Status |
|---|---|
| Stock photo / pasted notes | Live Nebius Token Factory (VLM `google/gemma-3-27b-it`, LLM `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`); labelled replay / rule parser if unavailable |
| Supplier offers | Labelled fixture by default (repeatable demo); live Tavily search is a toggle |
| Bookings, recipes, stock | Synthetic barbershop data, no real customers |
| Orders, payments | Simulated, no real purchasing |
| Numbers (demand, shortage, packs, cost, ETA) | Computed in code, never by the model |

**NVIDIA blueprints:** Retail Shopping Assistant `c20044b` (typed catalog tool pattern), Retail Catalog Enrichment `debc251` (visual product attributes), Multi-Agent Intelligent Warehouse `a6404ed` (forecast vs replenishment split), Retail Agentic Commerce `83c5f22` (merchant-controlled order lifecycle). All reimplemented; no upstream code imported.

**What we learned:** keep the AI on reading and explaining, and keep the arithmetic and the order button in code. A rejection loop with typed exclusions is far more reliable than letting an LLM pick suppliers.

**What's next:** real Fresha bookings, supplier checkout via ACP/UCP, received-stock workflow, tattoo and nail presets.

**Repo:** https://github.com/CriticalRegion/RetailHack26 (public). Run the React UI with `./scripts/dev.sh`, or the Streamlit fallback with `./scripts/dev.sh --streamlit`.

**Team:** Abhi, Om, CriticalRegion, Tudor
