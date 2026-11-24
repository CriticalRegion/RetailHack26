// t8: the headline numbers from State.kpis.
import type { Kpis } from "./basketTypes";
import { gbp, when } from "./OfferCard";

function Tile({ label, value, sub, tone }: { label: string; value: string; sub?: string; tone: "red" | "green" | "slate" }) {
  const tones = {
    red: "bg-red-500",
    green: "bg-emerald-500",
    slate: "bg-zinc-300",
  };
  return (
    <div className="rounded-lg border border-zinc-200 bg-white p-5 shadow-xs">
      <div className="flex items-center gap-2 text-xs font-medium text-zinc-500">
        <span className={`h-1.5 w-1.5 rounded-full ${tones[tone]}`} />
        {label}
      </div>
      <div className="mt-2 text-3xl font-semibold tabular-nums tracking-tight text-zinc-900">{value}</div>
      {sub && <div className="mt-1 text-sm text-zinc-500">{sub}</div>}
    </div>
  );
}

export function KpiHero({ kpis }: { kpis: Kpis }) {
  const ro = kpis.first_run_out;
  const covered = kpis.hero_covered;
  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Key numbers">
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
