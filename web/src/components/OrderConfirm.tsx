import type { Kpis, Order } from "./basketTypes";
import { gbp, when } from "./OfferCard";

export function OrderConfirm({
  order,
  kpis,
  onApproveAgain,
  onReceived,
  busy = false,
}: {
  order: Order;
  kpis: Kpis;
  onApproveAgain?: () => void;
  onReceived?: (orderId: string) => void;
  busy?: boolean;
}) {
  return (
    <section className="rounded-2xl border border-emerald-200 bg-emerald-50/70 p-5" data-testid="order-confirm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Simulated order placed</div>
          <div className="mt-1 text-2xl font-bold text-slate-900">{order.order_id}</div>
          <div className="text-sm text-slate-600">
            r{order.revision} · {gbp(order.total)} · {order.status === "pending" ? "pending delivery" : "received"}
          </div>
        </div>
        <div className="text-right">
          <div className="text-4xl font-bold tabular-nums text-slate-900" data-testid="order-count">
            {kpis.orders}
          </div>
          <div className="text-xs text-slate-500">simulated order{kpis.orders === 1 ? "" : "s"}</div>
        </div>
      </div>

      <ul className="mt-4 space-y-1 text-sm text-slate-700">
        {order.lines.map((l) => (
          <li key={l.sku}>
            {l.packs} pack{l.packs === 1 ? "" : "s"} = <span className="font-medium">{l.units} {l.unit}</span> of {l.product}{" "}
            from <span className="font-medium">{l.supplier}</span>, arriving {when(l.eta)}.
            {order.status === "pending" && <span className="text-slate-500"> Counted as incoming, not on-hand.</span>}
          </li>
        ))}
      </ul>

      {kpis.bookings_protected > 0 && (
        <p className="mt-4 rounded-lg bg-white px-3 py-2 text-base font-medium text-emerald-800">
          {kpis.bookings_protected} bookings protected · {gbp(kpis.revenue_covered)} booking revenue covered
          <span className="block text-xs font-normal text-slate-500">estimate, separate from the supplier price</span>
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {onApproveAgain && (
          <button
            type="button"
            onClick={onApproveAgain}
            disabled={busy}
            data-testid="approve-again"
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Approve r{order.revision} again (duplicate test)
          </button>
        )}
        {onReceived && order.status === "pending" && (
          <button
            type="button"
            onClick={() => onReceived(order.order_id)}
            disabled={busy}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-50 disabled:opacity-50"
          >
            Mark received
          </button>
        )}
      </div>
    </section>
  );
}
