// The owner's to-do: one plain decision. "Order this, from them, for this much, arriving then"
// with Order / Try a different supplier. Alternatives are one-line verdicts, not tables.
import { useState } from "react";
import type { State } from "../api";
import { Badge, Button, Card, Spinner, gbp, num, when } from "./ui";

const day = (iso: string) => new Date(iso).toLocaleDateString("en-GB", { weekday: "long" });
const hm = (iso: string) => new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });

export function Todo({
  state,
  busy,
  pending,
  onRun,
  onApprove,
  onReject,
  onReceived,
}: {
  state: State;
  busy: boolean;
  pending: string | null;
  onRun: () => void;
  onApprove: (rev: number) => void;
  onReject: (rev: number, fb: string) => void;
  onReceived: (id: string) => void;
}) {
  const [asking, setAsking] = useState(false);
  const [fb, setFb] = useState("");
  const k = state.kpis;
  const hero = state.forecast.find((f) => f.hero);
  const p = state.proposal;
  const order = state.orders[state.orders.length - 1];
  const risk = hero?.first_at_risk ?? k.first_run_out;
  const services = hero ? Object.entries(hero.contributing).map(([s, n]) => `${n} ${s.toLowerCase()}${n === 1 ? "" : "s"}`).join(", ") : "";

  // Done: ordered
  if (p?.status === "approved" && order) {
    const l = order.lines[0];
    return (
      <Card data-testid="order-confirm" className="overflow-hidden">
        <div className="border-l-4 border-emerald-600 px-6 py-5">
          <div className="text-[12.5px] font-semibold text-emerald-700">Done · order placed (simulated)</div>
          <h3 className="mt-1 text-[22px] font-semibold leading-snug tracking-tight text-stone-900">
            {l.supplier} delivers {num(l.units, l.unit)} on {day(l.eta)} at {hm(l.eta)}
          </h3>
          <p className="mt-1.5 text-[14px] text-stone-600">
            That's before {risk ? `${day(risk.time)} ${hm(risk.time)}` : "the first appointment at risk"}, so all <b className="text-stone-900">{k.bookings_protected} appointments</b> go ahead · {gbp(k.revenue_covered)} of bookings covered.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-2 text-[12.5px] text-stone-500">
            <span>Order {order.order_id} · {gbp(order.total)}</span>
            <span data-testid="order-count">· {state.orders.length} {state.orders.length === 1 ? "order" : "orders"} in total</span>
            <Badge tone={order.status === "pending" ? "amber" : "emerald"} dot>{order.status === "pending" ? "on its way" : "delivered"}</Badge>
          </div>
          <div className="mt-4 flex flex-wrap gap-2">
            {order.status === "pending" && <Button size="sm" disabled={busy} onClick={() => onReceived(order.order_id)}>Mark as delivered</Button>}
            <Button size="sm" variant="ghost" disabled={busy} onClick={() => onApprove(p.revision)} data-testid="approve-again">
              Approve r{p.revision} again (duplicate test)
            </Button>
          </div>
        </div>
      </Card>
    );
  }

  // Nothing to do
  if (!p && (!hero || !hero.first_at_risk)) {
    return (
      <Card className="px-6 py-6">
        <div className="text-[12.5px] font-semibold text-emerald-700">Nothing to order</div>
        <h3 className="mt-1 text-[20px] font-semibold tracking-tight text-stone-900">You have enough for every appointment this week.</h3>
      </Card>
    );
  }

  // Problem found, no suggestion yet
  if (!p && hero && risk) {
    return (
      <Card className="overflow-hidden">
        <div className="border-l-4 border-rose-600 px-6 py-5">
          <div className="text-[12.5px] font-semibold text-rose-700">To do · order more {hero.name}</div>
          <h3 className="mt-1 text-[22px] font-semibold leading-snug tracking-tight text-stone-900">
            You'll run out on {day(risk.time)} at {hm(risk.time)}
          </h3>
          <p className="mt-1.5 text-[14px] leading-relaxed text-stone-600">
            You have {num(hero.on_hand, hero.unit)} and this week's appointments need {num(hero.usage, hero.unit)} ({services}).
            Without more, <b className="text-stone-900">{hero.at_risk_count} appointments</b> can't be done, starting with {risk.id} ({risk.service.toLowerCase()}).
          </p>
          <Button variant="primary" size="lg" className="mt-5" disabled={busy} onClick={onRun} data-testid="run">
            {pending === "run" ? <Spinner /> : null}
            Run Iris: find suppliers
          </Button>
          <p className="mt-2 text-[12px] text-stone-500">Iris looks for the same product and size, and only suggests suppliers that deliver before {day(risk.time)}.</p>
        </div>
      </Card>
    );
  }

  if (!p) return null;
  const block = state.offers.find((b) => b.sku === hero?.sku) ?? state.offers[0];
  const line = p.lines[0];
  const others = (block?.options ?? []).filter((o) => o.tag !== "lead" && o.offer_id !== line?.offer_id);
  const leads = (block?.options ?? []).filter((o) => o.tag === "lead").length;
  const open = p.status === "proposed";

  return (
    <Card data-testid="basket" className="overflow-hidden">
      <div className="border-l-4 border-[#404e3b] px-6 py-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="text-[12.5px] font-semibold text-[#404e3b]">Iris suggests</div>
          <span className="text-[11.5px] text-stone-400">suggestion {p.revision}</span>
        </div>

        {p.feedback && (
          <div data-testid="revision-diff" className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-[12.5px] text-amber-950 ring-1 ring-amber-200">
            You said “{p.feedback}”. {p.change_note.split(" · ").join(" · ")}. Nothing was ordered.
          </div>
        )}

        {line ? (
          <>
            <h3 className="mt-2 text-[22px] font-semibold leading-snug tracking-tight text-stone-900">
              Order {line.packs} × {block?.options.find((o) => o.offer_id === line.offer_id)?.listing ?? line.product} from {line.supplier}
            </h3>
            <div className="mt-3 grid grid-cols-3 gap-3">
              <div className="rounded-lg bg-[#eef0eb] px-3 py-2.5">
                <div className="text-[11.5px] text-stone-500">You pay</div>
                <div data-testid="basket-total" className="text-[20px] font-semibold tabular-nums text-stone-900">{gbp(p.total)}</div>
                <div className="text-[11px] text-stone-500">incl. delivery</div>
              </div>
              <div className="rounded-lg bg-[#eef0eb] px-3 py-2.5">
                <div className="text-[11.5px] text-stone-500">Arrives</div>
                <div className="text-[20px] font-semibold text-stone-900">{new Date(line.eta).toLocaleDateString("en-GB", { weekday: "short" })} {hm(line.eta)}</div>
                <div className="text-[11px] text-emerald-700">in time for {risk ? `${new Date(risk.time).toLocaleDateString("en-GB", { weekday: "short" })} ${hm(risk.time)}` : "the week"}</div>
              </div>
              <div className="rounded-lg bg-[#eef0eb] px-3 py-2.5">
                <div className="text-[11.5px] text-stone-500">You get</div>
                <div className="text-[20px] font-semibold tabular-nums text-stone-900">{num(line.packs * line.units_per_pack, line.unit)}</div>
                <div className="text-[11px] text-stone-500">covers {hero?.at_risk_count ?? k.bookings_at_risk} appointments</div>
              </div>
            </div>
            <p className="mt-3 text-[13px] leading-relaxed text-stone-600">{line.reason}</p>
          </>
        ) : (
          <div data-testid="unmet" className="mt-2">
            <h3 className="text-[20px] font-semibold tracking-tight text-stone-900">No supplier can deliver in time</h3>
            <p className="mt-1 text-[13px] text-stone-600">{block?.reason}</p>
            <div data-testid="basket-empty" className="sr-only">Basket is empty.</div>
          </div>
        )}

        {open && (
          <div className="mt-5 flex flex-wrap items-start gap-2">
            <Button variant="approve" size="lg" disabled={busy || !line} onClick={() => onApprove(p.revision)} data-testid="approve">
              {pending === "approve" ? <Spinner /> : null}
              Approve r{p.revision} · {gbp(p.total)}
            </Button>
            {!asking ? (
              <Button size="lg" disabled={busy} onClick={() => setAsking(true)}>Try a different supplier</Button>
            ) : (
              <form
                className="flex min-w-[280px] flex-1 gap-2"
                onSubmit={(e) => {
                  e.preventDefault();
                  onReject(p.revision, fb);
                  setFb("");
                  setAsking(false);
                }}
              >
                <input
                  autoFocus
                  value={fb}
                  onChange={(e) => setFb(e.target.value)}
                  aria-label="Reject with feedback"
                  placeholder="What's wrong with this one? e.g. not BarberHub, they were late last time"
                  className="h-12 min-w-0 flex-1 rounded-lg border-0 bg-[#eef0eb] px-3.5 text-[13px] text-stone-800 ring-1 ring-inset ring-[#d5d9d1] placeholder:text-stone-400 focus:outline-none focus:ring-2 focus:ring-stone-400"
                />
                <Button type="submit" size="lg" variant="danger" disabled={busy} data-testid="reject">
                  {pending === "reject" ? <Spinner /> : null}
                  Reject &amp; search again
                </Button>
              </form>
            )}
          </div>
        )}
      </div>

      {others.length > 0 && (
        <div className="border-t border-[#e6e8e3] px-6 py-4">
          <div className="mb-2 text-[12px] font-medium text-stone-500">Other options Iris checked</div>
          <ul className="space-y-1.5 text-[13px]">
            {others.map((o) => {
              const ruledOut = p.excluded_offer_ids.includes(o.offer_id);
              return (
                <li key={o.offer_id} data-testid={`offer-${o.offer_id}`} className="flex flex-wrap items-baseline gap-x-2">
                  <span className={`font-semibold ${ruledOut ? "text-stone-400 line-through" : "text-stone-900"}`}>{o.supplier}</span>
                  <span className="tabular-nums text-stone-600">{gbp(o.delivered_cost)}</span>
                  <span className="text-stone-400">·</span>
                  <span className={o.on_time === false ? "text-amber-700" : "text-stone-600"}>
                    {ruledOut
                      ? "you ruled this out"
                      : o.on_time === false
                        ? `arrives ${when(o.eta)}, too late for ${o.misses_bookings} appointments`
                        : `also on time, arrives ${when(o.eta)}`}
                  </span>
                </li>
              );
            })}
          </ul>
          {leads > 0 && <p className="mt-2 text-[12px] text-stone-400">+ {leads} listings ignored (wrong size or no delivery date)</p>}
        </div>
      )}
    </Card>
  );
}
