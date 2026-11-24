// t8: the headline numbers from State.kpis.
import type { Kpis } from "./basketTypes";
import { gbp, when } from "./OfferCard";

function Tile({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone: "red" | "green" | "slate" }) {
  const tones = {
    red: "border-red-200 bg-red-50 text-red-800",
    green: "border-emerald-200 bg-emerald-50 text-emerald-800",
    slate: "border-slate-200 bg-white text-slate-900",
  };
  return (
    <div className={`rounded-2xl border p-4 ${tones[tone]}`}>
      <div className="text-xs font-medium uppercase tracking-wide opacity-70">{label}</div>
      <div className="mt-1 text-2xl font-bold tabular-nums">{value}</div>
      {sub && <div className="mt-0.5 text-sm opacity-80">{sub}</div>}
    </div>
  );
}

export function KpiHero({ kpis }: { kpis: Kpis }) {
  const ro = kpis.first_run_out;
  const covered = kpis.hero_covered;
  return (
    <section className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4" aria-label="Key numbers">
      {covered ? (
        <Tile label="Bookings protected" value={String(kpis.bookings_protected)} sub={`${gbp(kpis.revenue_covered)} booking revenue covered`} tone="green" />
      ) : (
        <Tile
          label="Bookings at risk"
          value={String(kpis.bookings_at_risk)}
          sub={kpis.bookings_at_risk ? "can't be served with current stock" : "all bookings covered"}
          tone={kpis.bookings_at_risk ? "red" : "green"}
        />
      )}
      <Tile
        label={covered ? "Was going to run out" : "Runs out"}
        value={ro ? when(ro.time) : "—"}
        sub={ro ? `${ro.id} · ${ro.service.toLowerCase()}` : "not in the next 7 days"}
        tone={ro && !covered ? "red" : "slate"}
      />
      <Tile label="Basket" value={kpis.basket_total == null ? "—" : gbp(kpis.basket_total)} sub="delivered, incl. shipping" tone="slate" />
      <Tile label="Simulated orders" value={String(kpis.orders)} sub={kpis.orders ? "stock incoming" : "nothing ordered yet"} tone={kpis.orders ? "green" : "slate"} />
    </section>
  );
}
