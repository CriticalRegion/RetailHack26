import { useState } from "react";
import type { Order, Proposal } from "./basketTypes";
import { OfferCard, gbp, when } from "./OfferCard";
import { OrderConfirm } from "./OrderConfirm";

/** Supplier basket: proposed offers, reject with feedback (r1 -> r2), approve, order confirmation.
 *  Presentation only: the parent owns API calls and passes the latest proposal/order back in. */
export function Basket({
  proposal,
  previous,
  order,
  busy = false,
  error,
  atRiskTimes = [],
  onReject,
  onApprove,
}: {
  proposal: Proposal;
  previous?: Proposal | null; // revision before this one, for the "what changed" panel
  order?: Order | null;
  busy?: boolean;
  error?: string | null;
  atRiskTimes?: string[]; // ISO times of at-risk bookings, to count what a late offer misses
  onReject: (feedback: string) => void;
  onApprove: (revision: number) => void;
}) {
  const [feedback, setFeedback] = useState("");
  const [showAll, setShowAll] = useState(false);
  const open = proposal.status === "proposed" && !order;
  const orderable = proposal.lines.some((l) => l.status !== "unmet" && l.selected);
  const missedBy = (eta?: string | null) =>
    eta ? atRiskTimes.filter((t) => new Date(t) < new Date(eta)).length : undefined;

  return (
    <section className="space-y-5" data-testid="basket">
      <header className="flex flex-wrap items-baseline justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Supplier basket</h2>
          <p className="text-sm text-slate-500">
            Proposal r{proposal.revision} · <span className="uppercase">{proposal.status}</span>
          </p>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold tabular-nums" data-testid="basket-total">
            {gbp(proposal.total)}
          </div>
          <div className="text-xs text-slate-500">basket total</div>
        </div>
      </header>

      {proposal.revision > 1 && (
        <div className="rounded-xl border border-sky-200 bg-sky-50 p-4 text-sm" data-testid="revision-diff">
          <div className="font-semibold text-sky-900">
            Revised r{proposal.revision - 1} → r{proposal.revision} after your feedback
          </div>
          {proposal.feedback.length > 0 && (
            <p className="mt-1 text-sky-900">“{proposal.feedback[proposal.feedback.length - 1]}”</p>
          )}
          <ul className="mt-2 list-disc pl-5 text-sky-800">
            {(proposal.changes ?? []).map((c) => (
              <li key={c}>{c}</li>
            ))}
            {previous && !proposal.changes?.length && (
              <li>
                Basket total: {gbp(previous.total)} → {gbp(proposal.total)}
              </li>
            )}
          </ul>
          {proposal.excluded_offer_ids.length > 0 && (
            <p className="mt-2 text-xs text-sky-700">Excluded: {proposal.excluded_offer_ids.join(", ")}</p>
          )}
          {!order && <p className="mt-1 text-xs font-medium text-sky-700">No order has been placed.</p>}
        </div>
      )}

      {proposal.lines.map((l) => (
        <div key={l.sku} className="space-y-3">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-semibold text-slate-800">{l.product}</h3>
            <span className="text-sm text-slate-500">
              short {l.shortage.required_qty} {l.unit} before {when(l.shortage.need_by)}
              {l.shortage.first_at_risk_booking_id ? ` (${l.shortage.first_at_risk_booking_id})` : ""}
            </span>
          </div>

          {l.status === "unmet" || !l.selected ? (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-800" data-testid="unmet">
              <div className="font-semibold">No on-time offer left</div>
              <p className="mt-1">{l.reason}</p>
            </div>
          ) : (
            <OfferCard r={l.selected} tag="selected" unit={l.unit} reason={l.reason} />
          )}

          <div className="grid gap-3 md:grid-cols-2">
            {l.alternative && <OfferCard r={l.alternative} tag="alternative" unit={l.unit} compact />}
            {l.late_option && (
              <OfferCard
                r={l.late_option}
                tag="late"
                unit={l.unit}
                compact
                missed={missedBy(l.late_option.offer.eta)}
              />
            )}
          </div>

          {l.leads.length > 0 && (
            <div>
              <button
                type="button"
                onClick={() => setShowAll((v) => !v)}
                className="text-xs text-slate-500 underline hover:text-slate-700"
              >
                {showAll ? "Hide" : "Show"} {l.leads.length} listing{l.leads.length === 1 ? "" : "s"} kept as leads
              </button>
              {showAll && (
                <div className="mt-2 grid gap-2 md:grid-cols-2">
                  {l.leads.map((r) => (
                    <OfferCard key={r.offer.offer_id} r={r} tag="lead" unit={l.unit} compact />
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ))}

      {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}

      {open && (
        <div className="grid gap-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 md:grid-cols-2">
          <button
            type="button"
            onClick={() => onApprove(proposal.revision)}
            disabled={busy || !orderable}
            className="rounded-xl bg-emerald-600 px-4 py-3 text-base font-semibold text-white shadow-sm hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-40"
            data-testid="approve"
          >
            Approve r{proposal.revision} · {gbp(proposal.total)}
          </button>
          <form
            className="flex gap-2"
            onSubmit={(e) => {
              e.preventDefault();
              onReject(feedback.trim());
              setFeedback("");
            }}
          >
            <input
              value={feedback}
              onChange={(e) => setFeedback(e.target.value)}
              placeholder="Reject with feedback, e.g. not BarberHub, they were late last time"
              className="min-w-0 flex-1 rounded-xl border border-slate-300 bg-white px-3 text-sm focus:border-slate-500 focus:outline-none"
              aria-label="Reject with feedback"
            />
            <button
              type="submit"
              disabled={busy}
              className="rounded-xl border border-slate-300 bg-white px-4 text-sm font-medium text-slate-700 hover:bg-slate-100 disabled:opacity-40"
              data-testid="reject"
            >
              Reject &amp; search again
            </button>
          </form>
        </div>
      )}

      {order && <OrderConfirm order={order} busy={busy} onApproveAgain={() => onApprove(order.revision)} />}
    </section>
  );
}
