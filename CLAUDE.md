# Iris project context

**Iris** forecasts consumable shortages from bookings and a merchant's stocktake, sources matching products, and simulates replenishment after merchant approval. See `IRIS.md` for the architecture, input and output contracts, blueprint references, owners, demo and acceptance checks. BuilderBase submission is due at **20:00 London time on 24 November 2026**. Om or Abhi publishes the initial idea docs.

Build the barbershop workflow first. The bookings branch maps service types to recipes and computes seven-day product quantities. The stock branch routes a photo to a Nebius-hosted VLM and text to a Nebius-hosted LLM, then presents matching, editable stock observations for confirmation. Reconcile the branches in code before sourcing.

Adapt the NVIDIA Retail Shopping Assistant's typed catalog search for supplier offers and the Retail Catalog Enrichment visual analysis pattern for stock observations. Keep sourcing tools read-only. Use Tavily for public listing discovery when available and a labelled fixture for a repeatable demo. Validate product identity, prices, pack counts and arrival evidence in code. Use AI for extraction, query planning and grounded explanations.

A rejected proposal reruns sourcing with the merchant's feedback and rejected offers. Approval of the current reviewed revision is the only route to the simulated order and incoming-stock update. Preserve idempotency and the difference between received and pending stock. Keep keys out of the repo and use synthetic customer data and staged photos. If time gets tight, preserve both intake routes, the forecast, supplier evidence and the reject/retry/approve flow.

Run the app with `streamlit run app.py` once implementation starts. See `.hackathon/PLAN.md` for deadline and ownership.
