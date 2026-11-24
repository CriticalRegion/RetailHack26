// Shapes for the basket screens. They mirror iris.agent / iris.sourcing pydantic dumps
// (Proposal, ProposalLine, RankedOffer, SupplierOffer) and iris.orders.Order.
// If contracts/api.md differs, adapt in api.ts, not in the components.

export interface Evidence {
  source: string; // "fixture" | "tavily"
  label: string;
  url?: string | null;
}

export interface SupplierOffer {
  offer_id: string;
  supplier: string;
  title: string;
  pack_price?: number | null;
  shipping?: number | null;
  items_per_pack?: number | null;
  item_size?: number | null;
  eta?: string | null; // ISO
  evidence: Evidence;
}

export interface RankedOffer {
  offer: SupplierOffer;
  eligible: boolean;
  on_time?: boolean | null;
  packs: number;
  covered_qty: number;
  delivered_cost?: number | null;
  issues: string[];
}

export interface Shortage {
  sku: string;
  required_qty: number;
  need_by: string; // ISO
  first_at_risk_booking_id?: string | null;
  affected_booking_ids: string[];
}

export interface BasketLine {
  sku: string;
  product: string;
  unit: string;
  status: "proposed" | "kept" | "unmet";
  shortage: Shortage;
  selected?: RankedOffer | null;
  alternative?: RankedOffer | null;
  late_option?: RankedOffer | null;
  leads: RankedOffer[];
  reason: string;
}

export interface Proposal {
  basket_id: string;
  revision: number;
  status: "proposed" | "rejected" | "approved" | "superseded";
  lines: BasketLine[];
  total: number;
  feedback: string[];
  excluded_offer_ids: string[];
  changes?: string[]; // plain-English diff vs previous revision (iris.agent.diff)
}

export interface OrderLine {
  sku: string;
  supplier: string;
  packs: number;
  units: number;
  eta: string;
}

export interface Order {
  order_id: string;
  revision: number;
  total: number;
  lines: OrderLine[];
  created: boolean; // false = re-approval returned the existing order
  order_count: number; // total simulated orders after this call
  bookings_protected?: number;
  revenue_covered?: number;
}
