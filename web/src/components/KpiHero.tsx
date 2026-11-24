// t8: the headline numbers from State.kpis.
import type { Kpis } from "./basketTypes";
import { gbp, when } from "./OfferCard";

function Tile({ label, value, sub, tone, dark = false }: { label: string; value: string; sub?: string; tone: "red" | "green" | "slate"; dark?: boolean }) {
  const pill = {
    red: dark ? "bg-[#ff8a7a] text-zinc-900" : "bg-red-100 text-red-700",
    green: "bg-[#d9f36a] text-zinc-900",
    slate: dark ? "bg-white/10 text-zinc-300" : "bg-[#ece8ff] text-[#5b4bc4]",
  };
  const word = { red: "at risk", green: "covered", slate: "info" };
  return (
    <div className={`flex min-h-[150px] flex-col justify-between rounded-[28px] p-6 ${dark ? "bg-zinc-900 text-white" : "bg-white text-zinc-900"}`}>
      <div className="flex items-center justify-between gap-2">
        <span className={`text-sm font-medium ${dark ? "text-zinc-300" : "text-zinc-500"}`}>{label}</span>
        <span className={`rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${pill[tone]}`}>{word[tone]}</span>
      </div>
      <div className={`mt-4 whitespace-nowrap font-semibold tabular-nums tracking-tight ${String(value).length > 6 ? "text-3xl xl:text-4xl" : "text-4xl xl:text-5xl"}`}>{value}</div>
      {sub && <div className={`mt-2 text-sm ${dark ? "text-zinc-400" : "text-zinc-500"}`}>{sub}</div>}
    </div>
  );
}

export function KpiHero({ kpis }: { kpis: Kpis }) {
  const ro = kpis.first_run_out;
  const covered = kpis.hero_covered;
  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4" aria-label="Key numbers">
      {covered ? (
        <Tile label="Bookings protected" value={String(kpis.bookings_protected)} sub={`${gbp(kpis.revenue_covered)} booking revenue covered`} tone="green" dark />
      ) : (
        <Tile
          label="Bookings at risk"
          value={String(kpis.bookings_at_risk)}
          sub={kpis.bookings_at_risk ? "can't be served with current stock" : "all bookings covered"}
          tone={kpis.bookings_at_risk ? "red" : "green"}
          dark
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
