# BuilderBase entry (copy-paste)

**Name:** Iris

**Tagline:** Never run out of what's booked.

**Track:** Retail AI (Nebius / NVIDIA)

**Problem:** Appointment businesses consume stock during services, and they know their demand a week ahead from their bookings. Yet a barber still finds out the clay is gone in the middle of a textured crop.

**What we built:** Iris turns next week's bookings and a stock count (a photo read by a Nebius-hosted VLM, or pasted text read by an LLM) into a time-ordered stock forecast. It names the first booking that will run short. A sourcing agent calls a typed, read-only supplier search tool, adapted from the NVIDIA Retail Shopping Assistant's catalog-search pattern, and proposes a basket with price, delivery and evidence. Code enforces same product and size, on-time delivery, and deterministic ranking. The owner can edit, reject with feedback (Iris searches again without the rejected supplier), or approve. Approval places exactly one simulated order and tracks incoming stock separately from on-hand.

**What works:** photo/text intake with owner confirmation, 7-day forecast and first at-risk booking, supplier ranking with late-offer and wrong-size handling, reject → revised basket, idempotent approval. 17 headless acceptance checks pass (`scripts/acceptance.py`).

**Live vs simulated:** Nebius Token Factory for vision/text extraction (labelled replay if unavailable); supplier offers are a labelled fixture by default, with live Tavily discovery as a toggle; bookings are synthetic; orders are simulated.

**NVIDIA blueprints:** Retail Shopping Assistant `c20044b` (typed catalog tool pattern), Retail Catalog Enrichment `debc251` (visual product attributes), Multi-Agent Intelligent Warehouse `a6404ed` (forecast vs replenishment split), Retail Agentic Commerce `83c5f22` (merchant-controlled order lifecycle). All reimplemented; no upstream code imported.

**What we learned:** keep the AI on reading and explaining, and keep the arithmetic and the order button in code. A rejection loop with typed exclusions is far more reliable than letting an LLM pick suppliers.

**What's next:** real Fresha bookings, supplier checkout via ACP/UCP, received-stock workflow, tattoo and nail presets.

**Repo:** https://github.com/CriticalRegion/RetailHack26

**Team:** Abhi, Om, CriticalRegion, Tudor
