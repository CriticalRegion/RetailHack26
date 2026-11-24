import { useState } from "react";
import type { HistoryRow, Kpis, OfferBlock, Order, Proposal } from "./basketTypes";
import { OfferCard, gbp, when } from "./OfferCard";
import { OrderConfirm } from "./OrderConfirm";

/** Supplier basket (demo steps 3-5). Pure: renders State slices, calls back for actions.
 *  The parent posts /api/reject, /api/approve, /api/received and replaces State with the response. */
export function Basket({
  proposal,
  offers,
  history,
  orders,
  kpis,
  busy = false,
  onRun,
  onReject,
  onApprove,
  onReceived,
}: {
  proposal: Proposal | null;
  offers: OfferBlock[];
  history: HistoryRow[];
  orders: Order[];
  kpis: Kpis;
  busy?: boolean;
  onRun?: () => void;
  onReject: (revision: number, feedback: string) => void;
  onApprove: (revision: number) => void;
  onReceived?: (orderId: string) => void;
}) {
  const [feedback, setFeedback] = useState("");
  const [showLeads, setShowLeads] = useState(false);

  if (!proposal) {
    return (
      <section className="rounded-lg border border-dashed border-zinc-200 bg-white p-8 text-center" data-testid="basket-empty">
        <p className="text-sm text-zinc-600">
          {kpis.bookings_at_risk > 0
            ? `${kpis.bookings_at_risk} bookings at risk. Let Iris find suppliers that deliver in time.`
            : "No shortages: nothing to order."}
        </p>
        {onRun && kpis.bookings_at_risk > 0 && (
          <button
            type="button"
            onClick={onRun}
            disabled={busy}
            className="mt-4 h-9 rounded-md bg-zinc-900 px-4 text-sm font-medium text-white shadow-xs transition-colors hover:bg-zinc-800 disabled:opacity-40"
            data-testid="run"
          >
            Run Iris: find suppliers
          </button>
        )}
      </section>
    );
  }

  const order = orders.find((o) => o.revision === proposal.revision) ?? null;
  const open = proposal.status === "proposed" && !order;
  const orderable = proposal.lines.length > 0;
  const leads = offers.flatMap((b) => b.options.filter((o) => o.tag === "lead"));

  return (
    <section className="space-y-5" data-testid="basket">
      <header className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold tracking-tight text-zinc-900">Supplier basket</h2>
          <p className="text-sm text-zinc-500">
            Proposal r{proposal.revision} · <span className="font-medium capitalize text-zinc-700">{proposal.status}</span>
            {kpis.orders === 0 && " · no order placed"}
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-semibold tracking-tight tabular-nums text-zinc-900" data-testid="basket-total">
            {gbp(proposal.total)}
          </div>
          <div className="text-xs text-zinc-500">basket total</div>
        </div>
      </header>

      {proposal.revision > 1 && (
        <div className="rounded-lg border border-zinc-200 bg-zinc-50/60 p-4 text-sm" data-testid="revision-diff">
          <div className="flex items-center gap-2 font-medium text-zinc-900"><span className="h-1.5 w-1.5 rounded-full bg-zinc-900" />
            r{proposal.revision - 1} rejected → r{proposal.revision}
          </div>
          {proposal.feedback && <p className="mt-1 text-zinc-600">“{proposal.feedback}”</p>}
          {proposal.change_note && (
            <ul className="mt-2 list-disc pl-5 text-zinc-600 marker:text-zinc-300">
              {proposal.change_note.split(" · ").map((c) => (
                <li key={c}>{c}</li>
              ))}
            </ul>
          )}
          {proposal.excluded_offer_ids.length > 0 && (
            <p className="mt-2 text-xs text-zinc-500">Excluded offers: {proposal.excluded_offer_ids.join(", ")}</p>
          )}
        </div>
      )}

      {offers.map((b) => {
        const sel = b.options.find((o) => o.tag === "selected");
        const others = b.options.filter((o) => o.tag === "alternative" || o.tag === "late");
        return (
          <div key={b.sku} className="space-y-3">
            <h3 className="text-sm font-semibold text-zinc-900">
              {b.product}
              {kpis.first_run_out && (
                <span className="ml-2 text-sm font-normal text-zinc-500">
                  needed before {when(kpis.first_run_out.time)} ({kpis.first_run_out.id}{" "}
                  {kpis.first_run_out.service.toLowerCase()})
                </span>
              )}
            </h3>
            {b.status === "unmet" || !sel ? (
              <div className="rounded-lg border border-zinc-200 bg-white p-4 text-sm text-zinc-700 shadow-xs" data-testid="unmet">
                <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-red-50 text-red-700 ring-red-600/10">No on-time offer left</span>
                <p className="mt-1">{b.reason}</p>
              </div>
            ) : (
              <OfferCard o={sel} reason={b.reason} />
            )}
            {others.length > 0 && (
              <div className="grid gap-3 md:grid-cols-2">
                {others.map((o) => (
                  <OfferCard key={o.offer_id} o={o} compact />
                ))}
              </div>
            )}
          </div>
        );
      })}

      {leads.length > 0 && (
        <div>
          <button
            type="button"
            onClick={() => setShowLeads((v) => !v)}
            className="text-xs font-medium text-zinc-500 hover:text-zinc-900"
          >
            {showLeads ? "Hide" : "Show"} {leads.length} listing{leads.length === 1 ? "" : "s"} kept as leads (wrong size,
            no delivery date…)
          </button>
          {showLeads && (
            <div className="mt-2 grid gap-2 md:grid-cols-2">
              {leads.map((o) => (
                <OfferCard key={o.offer_id} o={o} compact />
              ))}
            </div>
          )}
        </div>
      )}

      {open && (
        <div className="grid gap-3 rounded-lg border border-zinc-200 bg-white p-4 shadow-xs md:grid-cols-2">
          <button
            type="button"
            onClick={() => onApprove(proposal.revision)}
            disabled={busy || !orderable}
            className="h-10 rounded-md bg-emerald-600 px-4 text-sm font-medium text-white shadow-xs transition-colors hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
            data-testid="approve"
          >
            Approve r{proposal.revision} · {gbp(proposal.total)}
          </button>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              onReject(proposal.revision, feedback.trim());
              setFeedback("");
            }}
          >
            <input
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Why? e.g. not BarberHub, they were late last time"
              aria-label="Reject with feedback"
              className="h-10 min-w-0 flex-1 rounded-md border border-zinc-200 bg-white px-3 text-sm shadow-xs placeholder:text-zinc-400 focus:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-900/10"
            />
            <button
              type="submit"
              disabled={busy}
              className="h-10 rounded-md border border-zinc-200 bg-white px-3.5 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50 disabled:opacity-40"
              data-testid="reject"
            >
              Reject &amp; search again
            </button>
          </form>
        </div>
      )}

      {order && (
        <OrderConfirm
          order={order}
          kpis={kpis}
          busy={busy}
          onApproveAgain={() => onApprove(order.revision)}
          onReceived={onReceived}
        />
      )}

      {history.length > 1 && (
        <details className="text-sm text-zinc-600">
          <summary className="cursor-pointer text-zinc-500">Revision history</summary>
          <table className="mt-2 w-full text-left">
            <tbody>
              {history.map((h) => (
                <tr key={h.revision} className="border-t border-zinc-100">
                  <td className="py-1 pr-3 font-medium">r{h.revision}</td>
                  <td className="pr-3">{h.status}</td>
                  <td className="pr-3 tabular-nums">{gbp(h.total)}</td>
                  <td className="pr-3">{h.lines.join(", ")}</td>
                  <td className="text-zinc-500">{h.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </section>
  );
}
