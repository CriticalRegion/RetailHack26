// The week as a shop owner sees it: their appointment book, day by day. For the hero product:
// how many appointments use it each day, which can't be done, and when a delivery lands.
import type { State } from "../api";

const dayKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

export function Week({ state }: { state: State }) {
  const hero = state.forecast.find((f) => f.hero);
  if (!hero) return null;
  const start = new Date(state.shop.clock);
  start.setHours(0, 0, 0, 0);
  const days = Array.from({ length: 7 }, (_, i) => new Date(start.getTime() + i * 86400000));

  // Each step in the no-order projection after "now" is one appointment using the product.
  const appts = hero.series_without_order.slice(1).map((p) => ({ t: new Date(p.time), short: p.projected < 0 }));
  const nowShortByDay: Record<string, number> = {};
  hero.at_risk.forEach((b) => {
    const k = dayKey(new Date(b.time));
    nowShortByDay[k] = (nowShortByDay[k] ?? 0) + 1;
  });
  const ordered = state.kpis.orders > 0;
  const delivery = state.orders.flatMap((o) => (o.status === "pending" ? o.lines : [])).find((l) => l.sku === hero.sku);
  const runOut = hero.first_at_risk ?? (ordered ? state.kpis.first_run_out : null);

  return (
    <div className="rounded-xl border border-[#d5d9d1] bg-[#f8f8f6]">
      <div className="flex flex-wrap items-baseline justify-between gap-2 px-6 pt-5">
        <h3 className="text-[15px] font-semibold tracking-tight text-stone-900">Your week · {hero.name}</h3>
        <p className="text-[12.5px] text-stone-500">appointments that use it, day by day</p>
      </div>
      <div className="grid grid-cols-7 gap-2 p-4">
        {days.map((d) => {
          const k = dayKey(d);
          const list = appts.filter((a) => dayKey(a.t) === k);
          const total = list.length;
          const shortWithout = list.filter((a) => a.short).length;
          const short = nowShortByDay[k] ?? 0;
          const saved = ordered ? shortWithout - short : 0;
          const isRunOut = runOut && dayKey(new Date(runOut.time)) === k;
          const isDelivery = delivery && dayKey(new Date(delivery.eta)) === k;
          const closed = total === 0;
          const tone = short > 0 ? "border-rose-300 bg-rose-50" : saved > 0 ? "border-emerald-300 bg-emerald-50" : "border-[#d5d9d1] bg-[#f8f8f6]";
          return (
            <div key={k} className={`flex min-h-[132px] flex-col rounded-lg border p-3 ${tone}`}>
              <div className="flex items-baseline justify-between">
                <span className="text-[13px] font-semibold text-stone-900">{d.toLocaleDateString("en-GB", { weekday: "short" })}</span>
                <span className="text-[12px] text-stone-500">{d.getDate()}</span>
              </div>
              <div className="mt-2 text-[24px] font-semibold leading-none tabular-nums text-stone-900">{closed ? "–" : total}</div>
              <div className="text-[11.5px] text-stone-500">{closed ? "no appointments" : total === 1 ? "appointment" : "appointments"}</div>
              <div className="mt-auto space-y-1 pt-2 text-[11.5px] font-medium leading-tight">
                {isDelivery && <div className="text-emerald-800">Delivery {new Date(delivery!.eta).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}</div>}
                {isRunOut && !ordered && <div className="text-rose-700">Runs out {new Date(runOut!.time).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}</div>}
                {short > 0 && <div className="text-rose-700">{short} can't be done</div>}
                {saved > 0 && <div className="text-emerald-800">{saved} saved by order</div>}
                {!closed && short === 0 && saved === 0 && <div className="text-stone-500">Covered</div>}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
