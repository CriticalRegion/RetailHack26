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
    <section className="rounded-[28px] border border-white bg-white p-5 shadow-card" data-testid="order-confirm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-medium text-zinc-500"><span className="h-1.5 w-1.5 rounded-full bg-emerald-500" />Simulated order placed</div>
          <div className="mt-1 text-xl font-semibold tracking-tight text-zinc-900">{order.order_id}</div>
          <div className="text-sm text-zinc-600">
            r{order.revision} · {gbp(order.total)} · {order.status === "pending" ? "pending delivery" : "received"}
          </div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-semibold tracking-tight tabular-nums text-zinc-900" data-testid="order-count">
            {kpis.orders}
          </div>
          <div className="text-xs text-zinc-500">simulated order{kpis.orders === 1 ? "" : "s"}</div>
        </div>
      </div>

      <ul className="mt-4 space-y-1 border-t border-zinc-100 pt-4 text-sm text-zinc-600">
        {order.lines.map((l) => (
          <li key={l.sku}>
            {l.packs} pack{l.packs === 1 ? "" : "s"} = <span className="font-medium">{l.units} {l.unit}</span> of {l.product}{" "}
            from <span className="font-medium">{l.supplier}</span>, arriving {when(l.eta)}.
            {order.status === "pending" && <span className="text-zinc-500"> Counted as incoming, not on-hand.</span>}
          </li>
        ))}
      </ul>

      {kpis.bookings_protected > 0 && (
        <p className="mt-4 rounded-full bg-emerald-50 px-3 py-2.5 text-sm font-medium text-emerald-800 ring-1 ring-inset ring-emerald-600/20">
          {kpis.bookings_protected} bookings protected · {gbp(kpis.revenue_covered)} booking revenue covered
          <span className="block text-xs font-normal text-zinc-500">estimate, separate from the supplier price</span>
        </p>
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {onApproveAgain && (
          <button
            type="button"
            onClick={onApproveAgain}
            disabled={busy}
            data-testid="approve-again"
            className="rounded-full border border-zinc-200 bg-white px-3 h-8 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50 disabled:opacity-40"
          >
            Approve r{order.revision} again (duplicate test)
          </button>
        )}
        {onReceived && order.status === "pending" && (
          <button
            type="button"
            onClick={() => onReceived(order.order_id)}
            disabled={busy}
            className="rounded-full border border-zinc-200 bg-white px-3 h-8 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50 disabled:opacity-40"
          >
            Mark received
          </button>
        )}
      </div>
    </section>
  );
}
