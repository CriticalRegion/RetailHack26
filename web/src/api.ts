// API client for server.py (contracts/api.md). Every call returns the full State.
// If the API can't be reached, the app falls back to the recorded mocks in src/mock/,
// walking through them in demo order, so the UI still works on a laptop without Python.
import type { Booking, HistoryRow, Kpis, OfferBlock, Order, Proposal } from "./components/basketTypes";
import m0 from "./mock/0-initial.json";
import m1 from "./mock/1-review.json";
import m2 from "./mock/2-confirmed.json";
import m3 from "./mock/3-proposal-r1.json";
import m4 from "./mock/4-proposal-r2.json";
import m5 from "./mock/5-ordered.json";

export type { Booking };

export type ForecastEntry = {
  sku: string;
  name: string;
  unit: string;
  hero: boolean;
  usage: number;
  on_hand: number;
  incoming: number;
  uncovered: number;
  first_at_risk: Booking | null;
  at_risk_count: number;
  at_risk: Booking[];
  contributing: Record<string, number>;
  covered_by_order: boolean;
  series: { time: string; projected: number }[];
  series_without_order: { time: string; projected: number }[];
};

export type ReviewRow = {
  confirm: boolean;
  raw_label: string;
  sku: string;
  quantity: number | null;
  unit: string;
  note: string;
};

export type State = {
  shop: { name: string; clock: string; tz: string };
  intake: { text_model: string | null; vision_model: string | null };
  live_search: boolean;
  products: { sku: string; name: string; unit: string }[];
  stock: { sku: string; name: string; unit: string; on_hand: number; incoming: number }[];
  review: ReviewRow[];
  review_source: string;
  forecast: ForecastEntry[];
  kpis: Kpis;
  step: "stock" | "forecast" | "basket" | "order";
  proposal: Proposal | null;
  offers: OfferBlock[];
  history: HistoryRow[];
  orders: Order[];
  flash: null | { kind: "success" | "info" | "warning" | "error"; msg: string };
};

export const API: string = (import.meta.env.VITE_API as string | undefined) ?? "http://localhost:8000";

export class ApiError extends Error {}

// ------------------------------------------------------------------ mock fallback
const MOCKS = [m0, m1, m2, m3, m4, m5] as unknown as State[];
let mockIdx = 0;
const mockStep: Record<string, number> = {
  "/api/state": -1, // stay
  "/api/reset": 0,
  "/api/intake/sample": 1,
  "/api/intake/text": 1,
  "/api/intake/photo": 1,
  "/api/review/clear": 0,
  "/api/stock/confirm": 2,
  "/api/run": 3,
  "/api/reject": 4,
  "/api/approve": 5,
};

function fromMock(path: string): State {
  const key = path.split("?")[0];
  const next = mockStep[key];
  if (next !== undefined && next >= 0) {
    // approve twice stays on the ordered state, like the real idempotent approve
    mockIdx = key === "/api/approve" && mockIdx === 5 ? 5 : next;
  }
  const s = structuredClone(MOCKS[mockIdx]);
  if (key === "/api/approve" && mockIdx === 5 && next === 5) {
    s.flash = s.flash ?? { kind: "info", msg: "Already approved: still one order." };
  }
  return s;
}

// ------------------------------------------------------------------ transport
export type Mode = "api" | "mock";
let mode: Mode = "api";
let live = false; // true after the first successful API response
export const getMode = () => mode;

async function call(path: string, init?: RequestInit): Promise<State> {
  if (mode === "mock") return fromMock(path);
  let res: Response;
  try {
    res = await fetch(`${API}${path}`, init);
  } catch {
    // Server not running at first load: demo on the recorded mocks. Once live, never switch silently:
    // a dropped request mid-demo must show an error, not a recorded "order placed".
    if (live) throw new ApiError("API not reachable - is the server still running? (nothing was changed)");
    mode = "mock";
    return fromMock(path);
  }
  live = true;
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* not json */
    }
    throw new ApiError(detail);
  }
  return (await res.json()) as State;
}

const post = (path: string, body?: unknown) =>
  call(path, {
    method: "POST",
    headers: body === undefined ? undefined : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

export const api = {
  state: () => call("/api/state"),
  reset: () => post("/api/reset"),
  live: (on: boolean) => post("/api/live", { on }),
  intakeText: (text: string) => post("/api/intake/text", { text }),
  intakePhoto: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return call("/api/intake/photo", { method: "POST", body: fd });
  },
  intakeSample: (blurry = false) => post(`/api/intake/sample?blurry=${blurry}`),
  clearReview: () => post("/api/review/clear"),
  confirmStock: (rows: { sku: string; quantity: number | null; confirm: boolean }[]) =>
    post("/api/stock/confirm", { rows }),
  run: () => post("/api/run"),
  reject: (revision: number, feedback: string) => post("/api/reject", { revision, feedback }),
  approve: (revision: number) => post("/api/approve", { revision }),
  editLine: (sku: string, packs: number) => post("/api/line/edit", { sku, packs }),
  removeLine: (sku: string) => post("/api/line/remove", { sku }),
  received: (order_id: string) => post("/api/received", { order_id }),
};

export const samplePhotoUrl = (blurry = false) =>
  mode === "api" ? `${API}/api/sample-photo?blurry=${blurry}` : null;
