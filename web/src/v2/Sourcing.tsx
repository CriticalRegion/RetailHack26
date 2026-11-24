// Supplier sourcing: offers Iris compared (with evidence), the basket the merchant approves or
// rejects with feedback, and the simulated order. All numbers come from the API.
import { useState } from "react";
import type { State } from "../api";
import type { OfferBlock, OfferOption } from "../components/basketTypes";
import { Badge, Button, Card, CardHeader, Spinner, gbp, num, when } from "./ui";

const TAG: Record<OfferOption["tag"], { label: string; tone: "indigo" | "stone" | "amber" | "rose" }> = {
  selected: { label: "Recommended", tone: "indigo" },
  alternative: { label: "Alternative", tone: "stone" },
  late: { label: "Late", tone: "amber" },
  lead: { label: "Lead", tone: "stone" },
};

function OfferTile({ o, excluded }: { o: OfferOption; excluded: boolean }) {
  const t = TAG[o.tag];
  const late = o.on_time === false;
  return (
    <div
      data-testid={`offer-${o.offer_id}`}
      className={`relative flex flex-col rounded-lg bg-white p-4 ring-1 ${
        excluded ? "opacity-50 ring-stone-200" : o.tag === "selected" ? "ring-1 ring-stone-900" : late ? "ring-amber-200" : "ring-stone-200"
      }`}
    >
      <div className="flex items-center justify-between gap-2">
        <Badge tone={excluded ? "rose" : t.tone}>{excluded ? "Excluded by you" : t.label}</Badge>
        {o.on_time === true && <Badge tone="emerald" dot>On time</Badge>}
        {late && <Badge tone="amber" dot>Misses {o.misses_bookings} bookings</Badge>}
      </div>
      <div className={`mt-3 text-[15px] font-semibold text-stone-900 ${excluded ? "line-through" : ""}`}>{o.supplier}</div>
      <div className="truncate text-[12px] text-stone-500" title={o.listing}>{o.listing}</div>
      <div className="mt-4 grid grid-cols-3 gap-2 text-[12px]">
        <div>
          <div className="text-stone-500">Delivered</div>
          <div className="text-[17px] font-semibold tabular-nums text-stone-900">{gbp(o.delivered_cost)}</div>
        </div>
        <div>
          <div className="text-stone-500">Per 100 ml</div>
          <div className="text-[17px] font-semibold tabular-nums text-stone-900">{o.per_100ml != null ? gbp(o.per_100ml) : "—"}</div>
        </div>
        <div>
          <div className="text-stone-500">Arrives</div>
          <div className={`text-[15px] font-semibold tabular-nums ${late ? "text-amber-700" : "text-stone-900"}`}>{when(o.eta)}</div>
        </div>
      </div>
      <div className="mt-auto pt-3 text-[11px] text-stone-400">
        {o.evidence_url ? (
          <a href={o.evidence_url} target="_blank" rel="noreferrer" className="underline decoration-stone-300 hover:text-stone-700">evidence ↗</a>
        ) : (
          <span title={o.evidence_label}>{o.evidence_label.startsWith("FIXTURE") ? "labelled fixture listing" : o.evidence_label}</span>
        )}
      </div>
    </div>
  );
}

function OfferBlockView({ b, excluded, atRisk }: { b: OfferBlock; excluded: string[]; atRisk: string }) {
  const main = b.options.filter((o) => o.tag !== "lead");
  const leads = b.options.filter((o) => o.tag === "lead");
  return (
    <div>
      <div className="mb-3 flex flex-wrap items-baseline justify-between gap-2">
        <div className="text-[14px] font-semibold text-stone-900">{b.product}</div>
        <div className="text-[12px] text-stone-500">needed before {atRisk}</div>
      </div>
      {b.status === "unmet" && (
        <div data-testid="unmet" className="mb-3 rounded-xl bg-rose-50 px-4 py-3 text-[13px] text-rose-800 ring-1 ring-rose-200">
          <b>No on-time offer left.</b> {b.reason}
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2">
        {main.map((o) => (
          <OfferTile key={o.offer_id} o={o} excluded={excluded.includes(o.offer_id)} />
        ))}
      </div>
      {b.status !== "unmet" && b.reason && (
        <p className="mt-3 rounded-xl bg-stone-50 px-4 py-3 text-[13px] leading-relaxed text-stone-700 ring-1 ring-stone-200">
          <span className="font-semibold">Why: </span>{b.reason}
        </p>
      )}
      {leads.length > 0 && (
        <details className="group mt-3 text-[12.5px] text-stone-600">
          <summary className="cursor-pointer select-none text-stone-500 hover:text-stone-800">
            {leads.length} more {leads.length === 1 ? "listing" : "listings"} kept as leads (wrong size, no delivery date…)
          </summary>
          <ul className="mt-2 space-y-1.5">
            {leads.map((o) => (
              <li key={o.offer_id} className="flex flex-wrap items-center gap-2 rounded-lg bg-stone-50 px-3 py-2 ring-1 ring-stone-100">
                <span className="font-semibold text-stone-800">{o.supplier}</span>
                <span className="truncate text-stone-500">{o.listing}</span>
                <span className="ml-auto text-amber-700">{o.issues.join("; ")}</span>
              </li>
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export function Sourcing({
  state,
  busy,
  pending,
  onRun,
  onReject,
  onApprove,
  onEdit,
  onRemove,
  onReceived,
}: {
  state: State;
  busy: boolean;
  pending: string | null;
  onRun: () => void;
  onReject: (rev: number, fb: string) => void;
  onApprove: (rev: number) => void;
  onEdit: (sku: string, packs: number) => void;
  onRemove: (sku: string) => void;
  onReceived: (id: string) => void;
}) {
  const [fb, setFb] = useState("");
  const p = state.proposal;
  const k = state.kpis;
  const short = state.forecast.some((f) => f.uncovered > 0);
  const atRisk = (sku: string) => {
    const f = state.forecast.find((x) => x.sku === sku);
    const b = f?.first_at_risk ?? k.first_run_out;
    return b ? `${when(b.time)} (${b.id} ${b.service.toLowerCase()})` : "the end of the week";
  };

  if (!p) {
    return (
      <Card className="overflow-hidden">
        <div className="flex flex-col items-start gap-5 p-8 md:flex-row md:items-center md:justify-between">
          <div className="max-w-xl">
            <div className="text-[12px] font-medium text-stone-500">Step 3 · Supplier search</div>
            <h3 className="mt-1 text-xl font-semibold tracking-tight text-stone-900">
              {short ? "Find the same product, delivered before it runs out" : "Nothing to order this week"}
            </h3>
            <p className="mt-1.5 text-[14px] text-stone-500">
              {short
                ? "Iris searches suppliers for the exact SKU and size, checks price and delivery evidence in code, and only proposes offers that arrive in time."
                : "Every booking in the next 7 days is covered by the stock you have."}
            </p>
          </div>
          {short && (
            <Button variant="primary" size="lg" disabled={busy} onClick={onRun} data-testid="run">
              {pending === "run" ? <Spinner /> : null}
              Run Iris: find suppliers
            </Button>
          )}
        </div>
      </Card>
    );
  }

  const open = p.status === "proposed";
  const approved = p.status === "approved";
  const order = state.orders[state.orders.length - 1];

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
      <Card className="min-w-0">
        <CardHeader
          title="Offers Iris compared"
          sub={state.live_search ? "Live search (Tavily) + labelled fixture" : "Labelled fixture offers · repeatable demo"}
          right={<Badge tone="stone">{state.offers.reduce((n, b) => n + b.options.length, 0)} listings</Badge>}
        />
        <div className="space-y-8 px-6 pb-6 pt-5">
          {state.offers.map((b) => (
            <OfferBlockView key={b.sku} b={b} excluded={p.excluded_offer_ids} atRisk={atRisk(b.sku)} />
          ))}
        </div>
      </Card>

      <div className="space-y-6 lg:sticky lg:top-6 lg:self-start">
        <Card data-testid="basket">
          <div className="flex items-center justify-between px-6 pt-5">
            <div className="flex items-center gap-2">
              <h3 className="text-[15px] font-semibold tracking-tight text-stone-900">Basket</h3>
              <Badge tone="dark">r{p.revision}</Badge>
              <Badge tone={approved ? "emerald" : open ? "indigo" : "stone"} dot>{p.status}</Badge>
            </div>
          </div>
          <div className="px-6 pt-3">
            <div data-testid="basket-total" className="text-[40px] font-semibold leading-none tracking-tight tabular-nums text-stone-900">{gbp(p.total)}</div>
            <div className="mt-1 text-[12.5px] text-stone-500">delivered, incl. shipping · {approved ? "ordered" : "no order placed yet"}</div>
          </div>

          {(p.feedback || p.change_note) && (
            <div data-testid="revision-diff" className="mx-6 mt-4 rounded-xl bg-amber-50 px-4 py-3 text-[12.5px] text-amber-950 ring-1 ring-amber-200">
              <div className="font-semibold">Revised after your feedback</div>
              {p.feedback && <div className="mt-1 italic">“{p.feedback}”</div>}
              {p.change_note && (
                <ul className="mt-2 space-y-0.5">
                  {p.change_note.split(" · ").map((c) => (
                    <li key={c}>→ {c}</li>
                  ))}
                </ul>
              )}
            </div>
          )}

          <div className="mt-4 divide-y divide-stone-100 border-y border-stone-100">
            {p.lines.length === 0 && (
              <div data-testid="basket-empty" className="px-6 py-4 text-[13px] text-stone-500">Basket is empty.</div>
            )}
            {p.lines.map((l) => (
              <div key={l.sku} className="px-6 py-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="truncate text-[13.5px] font-semibold text-stone-900">{l.supplier}</div>
                    <div className="truncate text-[12px] text-stone-500">{l.product}</div>
                  </div>
                  <div className="text-right">
                    <div className="text-[14px] font-semibold tabular-nums text-stone-900">{gbp(l.total)}</div>
                    <div className="text-[11.5px] text-stone-500">arrives {when(l.eta)}</div>
                  </div>
                </div>
                <div className="mt-2 flex items-center justify-between text-[12px] text-stone-600">
                  <span>
                    {l.packs} × pack of {num(l.units_per_pack, l.unit)} = <b className="text-stone-900">{num(l.packs * l.units_per_pack, l.unit)}</b>
                  </span>
                  {open && (
                    <span className="flex items-center gap-1">
                      <button disabled={busy || l.packs <= 1} onClick={() => onEdit(l.sku, l.packs - 1)} aria-label={`One pack fewer of ${l.product}`} className="h-6 w-6 rounded-md ring-1 ring-stone-200 hover:bg-stone-50 disabled:opacity-30">−</button>
                      <button disabled={busy} onClick={() => onEdit(l.sku, l.packs + 1)} aria-label={`One pack more of ${l.product}`} className="h-6 w-6 rounded-md ring-1 ring-stone-200 hover:bg-stone-50 disabled:opacity-30">+</button>
                      <button disabled={busy} onClick={() => onRemove(l.sku)} className="ml-1 rounded-md px-1.5 py-0.5 text-rose-600 hover:bg-rose-50 disabled:opacity-30">Remove</button>
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>

          <div className="space-y-3 p-6">
            {open && (
              <>
                <Button variant="approve" size="lg" className="w-full" disabled={busy || p.lines.length === 0} onClick={() => onApprove(p.revision)} data-testid="approve">
                  {pending === "approve" ? <Spinner /> : null}
                  Approve r{p.revision} · {gbp(p.total)}
                </Button>
                <form
                  className="space-y-2"
                  onSubmit={(e) => {
                    e.preventDefault();
                    onReject(p.revision, fb);
                    setFb("");
                  }}
                >
                  <input
                    value={fb}
                    onChange={(e) => setFb(e.target.value)}
                    aria-label="Reject with feedback"
                    placeholder="Why? e.g. not BarberHub, they were late last time"
                    className="h-10 w-full rounded-xl border-0 bg-stone-50 px-3.5 text-[13px] text-stone-800 ring-1 ring-inset ring-stone-200 placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-rose-300"
                  />
                  <Button type="submit" variant="danger" className="w-full" disabled={busy} data-testid="reject">
                    {pending === "reject" ? <Spinner /> : null}
                    Reject &amp; search again
                  </Button>
                </form>
              </>
            )}
            {approved && (
              <Button variant="secondary" className="w-full" disabled={busy} onClick={() => onApprove(p.revision)} data-testid="approve-again">
                Approve r{p.revision} again (duplicate test)
              </Button>
            )}
          </div>
        </Card>

        {order && (
          <Card data-testid="order-confirm" className="overflow-hidden">
            <div className="border-b border-stone-200 px-6 py-5">
              <div className="flex items-center justify-between">
                <div className="text-[12px] font-semibold text-emerald-700">Simulated order placed</div>
                <span data-testid="order-count" className="rounded bg-stone-100 px-1.5 py-0.5 text-[11px] font-medium text-stone-600">
                  {state.orders.length} {state.orders.length === 1 ? "order" : "orders"}
                </span>
              </div>
              <div className="mt-1 text-[15px] font-semibold tracking-tight text-stone-900">{order.order_id}</div>
              <div className="mt-3 text-[26px] font-semibold leading-none tabular-nums text-stone-900">{k.bookings_protected} bookings protected</div>
              <div className="mt-1 text-[13px] text-stone-500">{gbp(k.revenue_covered)} booking revenue covered · estimate, separate from the supplier price</div>
            </div>
            <div className="space-y-2 px-6 py-4 text-[13px] text-stone-700">
              {order.lines.map((l) => (
                <div key={l.sku}>
                  {l.packs} {l.packs === 1 ? "pack" : "packs"} = <b>{num(l.units, l.unit)}</b> of {l.product} from {l.supplier}, arriving {when(l.eta)}.
                </div>
              ))}
              <div className="flex items-center justify-between pt-2">
                <Badge tone={order.status === "pending" ? "amber" : "emerald"} dot>
                  {order.status === "pending" ? "Incoming, not on-hand yet" : "Received into stock"}
                </Badge>
                {order.status === "pending" && (
                  <Button size="sm" disabled={busy} onClick={() => onReceived(order.order_id)}>Mark received</Button>
                )}
              </div>
            </div>
          </Card>
        )}

        {state.history.length > 1 && (
          <Card>
            <CardHeader title="Revision history" />
            <ol className="space-y-3 px-6 pb-5 pt-3">
              {state.history.map((h) => (
                <li key={h.revision} className="flex gap-3 text-[12.5px]">
                  <span className={`mt-1 h-2 w-2 shrink-0 rounded-full ${h.status === "approved" ? "bg-emerald-500" : h.status === "proposed" ? "bg-stone-900" : "bg-stone-300"}`} />
                  <div className="min-w-0">
                    <div className="font-semibold text-stone-800">
                      r{h.revision} · {h.status} · {gbp(h.total)}
                    </div>
                    <div className="truncate text-stone-500">{h.lines.join(", ") || "(empty)"}</div>
                    {h.note && <div className="text-stone-400">{h.note}</div>}
                  </div>
                </li>
              ))}
            </ol>
          </Card>
        )}
      </div>
    </div>
  );
}
