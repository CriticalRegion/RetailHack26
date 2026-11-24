// State slices used by the basket screens (contracts/api.md). Structural types, so the
// app's own State type from api.ts can be passed in directly.

export interface Booking {
  id: string;
  time: string;
  service: string;
}

export interface ProposalLine {
  sku: string;
  product: string;
  unit: string;
  offer_id: string;
  supplier: string;
  packs: number;
  units_per_pack: number;
  pack_price: number;
  shipping: number;
  total: number;
  eta: string;
  source: string;
  reason: string;
}

export interface Proposal {
  basket_id: string;
  revision: number;
  status: "proposed" | "approved" | "rejected" | "superseded";
  total: number;
  feedback: string;
  excluded_offer_ids: string[];
  change_note: string;
  lines: ProposalLine[];
}

export interface OfferOption {
  tag: "selected" | "alternative" | "late" | "lead";
  offer_id: string;
  supplier: string;
  listing: string;
  packs: number | null;
  delivered_cost: number | null;
  per_100ml: number | null;
  eta: string | null;
  on_time: boolean | null;
  misses_bookings: number;
  evidence_url: string | null;
  evidence_label: string;
  issues: string[];
}

export interface OfferBlock {
  sku: string;
  product: string;
  unit: string;
  status: "proposed" | "kept" | "unmet";
  reason: string;
  query: string;
  options: OfferOption[];
}

export interface HistoryRow {
  revision: number;
  status: string;
  total: number;
  lines: string[];
  note: string;
}

export interface Order {
  order_id: string;
  revision: number;
  total: number;
  created_at: string;
  status: "pending" | "received";
  lines: { sku: string; product: string; packs: number; units: number; unit: string; supplier: string; eta: string }[];
}

export interface Kpis {
  bookings_at_risk: number;
  first_run_out: Booking | null;
  hero_covered: boolean;
  basket_total: number | null;
  bookings_protected: number;
  revenue_covered: number;
  orders: number;
}
