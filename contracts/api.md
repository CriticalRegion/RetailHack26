# Iris API contract (server.py ↔ web/)

Run the API: `.venv/Scripts/uvicorn server:app --port 8000 --reload` (macOS: `.venv/bin/uvicorn ...`). CORS is open.
Base URL in the web app: `import.meta.env.VITE_API ?? "http://localhost:8000"`.

**Every endpoint returns the full `State` below.** The front end never computes business logic: render `State`, call an action, replace `State` with the response.
Errors: HTTP 409 `{"detail": "..."}` (for example, rejecting a stale revision). Show `detail` as a toast.
Real samples of every step are in `web/src/mock/` (generated from the real server): `0-initial`, `1-review`, `2-confirmed`, `3-proposal-r1`, `4-proposal-r2`, `5-ordered`. **Build against these first.**

## Endpoints

| Method + path | Body | Effect |
|---|---|---|
| GET `/api/state` | none | current state |
| POST `/api/reset` | none | fresh demo session |
| POST `/api/live` | `{"on": bool}` | live supplier search (Tavily + Nebius) on/off; default off = labelled fixture |
| POST `/api/intake/text` | `{"text": "2 x Northline Matte Clay 100 ml, 35 neck strips"}` | fills `review` (LLM) |
| POST `/api/intake/photo` | multipart `file` | fills `review` (VLM) |
| POST `/api/intake/sample?blurry=false` | none | reads `demo/stocktake.png` (or the blurry one): the demo button |
| GET `/api/sample-photo?blurry=false` | none | the PNG, for a thumbnail |
| POST `/api/review/clear` | none | discard review rows |
| POST `/api/stock/confirm` | `{"rows":[{"sku","quantity","confirm"}]}` | ticked rows overwrite on-hand; forecast updates |
| POST `/api/run` | none | Iris sources suppliers → `proposal` r1 + `offers` |
| POST `/api/reject` | `{"revision": 1, "feedback": "not BarberHub"}` | rejects rN, searches again → rN+1 (no order) |
| POST `/api/approve` | `{"revision": 2}` | simulated order; repeat call is a no-op (`flash` says so) |
| POST `/api/line/edit` | `{"sku", "packs"}` | new revision needing approval |
| POST `/api/line/remove` | `{"sku"}` | removes the line (new revision) |
| POST `/api/received` | `{"order_id"}` | pending → on-hand |

## State

```ts
type Booking = { id: string; time: string /* ISO local London, "2026-11-27T11:00" */; service: string };
type State = {
  shop: { name: string; clock: string; tz: string };
  intake: { text_model: string | null; vision_model: string | null };   // null = fallback (show "REPLAY"/"RULES" badge), else "LIVE · <model>"
  live_search: boolean;
  products: { sku: string; name: string; unit: string }[];
  stock: { sku: string; name: string; unit: string; on_hand: number; incoming: number }[];
  review: { confirm: boolean; raw_label: string; sku: string /* "?" = unmatched */; quantity: number | null; unit: string; note: string }[];
  review_source: string;      // "text" | "photo" | "sample photo" | ...
  forecast: {
    sku: string; name: string; unit: string; hero: boolean;
    usage: number; on_hand: number; incoming: number; uncovered: number;
    first_at_risk: Booking | null; at_risk_count: number; at_risk: Booking[];
    contributing: Record<string, number>;          // service -> bookings
    covered_by_order: boolean;                       // true after the order protects it
    series: { time: string; projected: number }[];               // with pending orders
    series_without_order: { time: string; projected: number }[]; // baseline, for the dashed line
  }[];
  kpis: { bookings_at_risk: number; first_run_out: Booking | null; hero_covered: boolean;
          basket_total: number | null; bookings_protected: number; revenue_covered: number; orders: number };
  step: "stock" | "forecast" | "basket" | "order";   // drives the stepper
  proposal: null | {
    basket_id: string; revision: number; status: "proposed" | "approved" | "rejected" | "superseded";
    total: number; feedback: string; excluded_offer_ids: string[]; change_note: string;   // change_note: "BarberHub → ShearCo Supply · Basket total: £26.50 → £37.95"
    lines: { sku: string; product: string; unit: string; offer_id: string; supplier: string; packs: number;
             units_per_pack: number; pack_price: number; shipping: number; total: number; eta: string;
             source: string; reason: string }[];
  };
  offers: { sku: string; product: string; unit: string; status: "proposed" | "kept" | "unmet"; reason: string; query: string;
            options: { tag: "selected" | "alternative" | "late" | "lead"; offer_id: string; supplier: string; listing: string;
                       packs: number | null; delivered_cost: number | null; per_100ml: number | null; eta: string | null;
                       on_time: boolean | null; misses_bookings: number; evidence_url: string | null; evidence_label: string;
                       issues: string[] }[] }[];
  history: { revision: number; status: string; total: number; lines: string[]; note: string }[];
  orders: { order_id: string; revision: number; total: number; created_at: string; status: "pending" | "received";
            lines: { sku: string; product: string; packs: number; units: number; unit: string; supplier: string; eta: string }[] }[];
  flash: null | { kind: "success" | "info" | "warning" | "error"; msg: string };   // one-shot toast
};
```

## Demo path (what the UI must make obvious)
1. Stock: "Use sample photo" → review rows (LIVE/REPLAY badge) → Confirm → forecast moves.
2. Forecast: KPI "22 bookings at risk · runs out Fri 11:00 (BK-030 textured crop)" + run-out chart (red marker at first at-risk).
3. Run Iris → basket r1 (BarberHub £26.50) with offer cards: on-time vs **late but cheaper** (BulkBarber misses N bookings), evidence label/link, reason.
4. Reject with feedback → r2 (ShearCo £37.95), show `change_note` diff and the excluded offer, "no order placed".
5. Approve → order PO-BARBER-W48-r2, incoming stock, "22 bookings protected · £602 covered"; approve again → still 1 order.
