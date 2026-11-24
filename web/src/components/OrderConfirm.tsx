import type { Order } from "./basketTypes";
import { gbp, when } from "./OfferCard";

export function OrderConfirm({
  order,
  onApproveAgain,
  busy = false,
}: {
  order: Order;
  onApproveAgain?: () => void;
  busy?: boolean;
}) {
  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50/60 p-5" data-testid="order-confirm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Simulated order placed</div>
          <div className="mt-1 text-2xl font-bold text-slate-900">{order.order_id}</div>
          <div className="text-sm text-slate-600">
            revision r{order.revision} · {gbp(order.total)} · pending delivery
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold tabular-nums text-slate-900" data-testid="order-count">
            {order.order_count}
          </div>
          <div className="text-xs text-slate-500">order{order.order_count === 1 ? "" : "s"} total</div>
        </div>
      </div>

      <ul className="mt-4 space-y-1 text-sm text-slate-700">
        {order.lines.map((l) => (
          <li key={l.sku}>
            {l.packs} pack{l.packs === 1 ? "" : "s"} ({l.units} {l.sku.includes("clay") ? "ml" : "units"}) from{" "}
            <span className="font-medium">{l.supplier}</span>, arriving {when(l.eta)}. Counted as{" "}
            <span className="font-medium">incoming</span>, not on-hand, until received.
          </li>
        ))}
      </ul>

      {order.bookings_protected != null && (
        <p className="mt-4 rounded-lg bg-white px-3 py-2 text-sm text-emerald-800">
          {order.bookings_protected} bookings protected · estimated booking revenue covered{" "}
          {gbp(order.revenue_covered ?? 0)} (separate from supplier price)
        </p>
      )}

      {!order.created && (
        <p className="mt-3 text-sm font-medium text-slate-700" data-testid="duplicate-note">
          Already ordered: approving again returned {order.order_id}. Nothing was duplicated.
        </p>
      )}

      {onApproveAgain && (
        <button
          type="button"
          onClick={onApproveAgain}
          disabled={busy}
          className="mt-4 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
        >
          Approve r{order.revision} again (duplicate test)
        </button>
      )}
    </section>
  );
}
