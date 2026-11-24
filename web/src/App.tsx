// Iris v2 app shell. Renders State, calls an action, replaces State with the response.
// No business logic here (contracts/api.md).
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, getMode, type State } from "./api";
import { Runout } from "./v2/Runout";
import { Sourcing } from "./v2/Sourcing";
import { Stock } from "./v2/Stock";
import { Badge, Card, Spinner, Stat, gbp, when } from "./v2/ui";

type Toast = NonNullable<State["flash"]>;
const TOAST_DOT: Record<Toast["kind"], string> = { success: "bg-emerald-400", info: "bg-stone-400", warning: "bg-amber-400", error: "bg-rose-400" };
const STEPS = [
  { id: "stock", title: "Count stock", sub: "Photo or text, you confirm" },
  { id: "forecast", title: "Forecast", sub: "What bookings will use" },
  { id: "basket", title: "Source", sub: "Compare, reject, revise" },
  { id: "order", title: "Order", sub: "Approve, track incoming" },
] as const;

function Logo() {
  return (
    <span className="relative grid h-9 w-9 place-items-center rounded-xl bg-[#1f3b2f]">
      <span className="h-3.5 w-3.5 rounded-full bg-[#f6f8f3]" />
      <span className="absolute h-1.5 w-1.5 rounded-full bg-stone-900" />
    </span>
  );
}

function Sidebar({ state, busy, mock, onLive, onReset }: { state: State; busy: boolean; mock: boolean; onLive: (on: boolean) => void; onReset: () => void }) {
  const cur = STEPS.findIndex((s) => s.id === state.step);
  const done = (i: number) => i < cur || (state.kpis.orders > 0 && i === 3);
  return (
    <aside className="flex w-full flex-col border-r border-[#c9d3c2] bg-[#dde6d7] text-stone-600 lg:fixed lg:inset-y-0 lg:left-0 lg:z-30 lg:w-[272px] lg:overflow-y-auto">
      <div className="flex items-center gap-3 px-6 pb-6 pt-7">
        <Logo />
        <div>
          <div className="text-[16px] font-semibold tracking-tight text-stone-900">Iris</div>
          <div className="text-[12px] text-stone-400">Never run out of what's booked</div>
        </div>
      </div>

      <div className="mx-4 rounded-xl bg-[#edf2e9] px-4 py-3 ring-1 ring-[#d3dccd]">
        <div className="text-[13px] font-semibold text-stone-900">{state.shop.name}</div>
        <div className="mt-0.5 text-[12px] text-stone-400">{new Date(state.shop.clock).toLocaleString("en-GB", { weekday: "long", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}</div>
      </div>

      <nav className="mt-7 px-6" aria-label="Progress">
        <div className="mb-3 text-[11px] font-semibold text-stone-500">Workflow</div>
        <ol className="relative space-y-5">
          <span className="absolute bottom-3 left-[11px] top-3 w-px bg-stone-200" aria-hidden />
          {STEPS.map((s, i) => (
            <li key={s.id} className="relative flex gap-3">
              <span
                className={`relative z-10 grid h-6 w-6 shrink-0 place-items-center rounded-full text-[11px] font-bold ${
                  done(i) ? "bg-emerald-500 text-white" : i === cur ? "bg-[#1f3b2f] text-white" : "bg-[#e3eadf] text-stone-500"
                }`}
              >
                {done(i) ? "✓" : i + 1}
              </span>
              <div>
                <div className={`text-[13.5px] font-semibold ${i === cur || done(i) ? "text-stone-900" : "text-stone-500"}`}>{s.title}</div>
                <div className="text-[12px] text-stone-500">{s.sub}</div>
              </div>
            </li>
          ))}
        </ol>
      </nav>

      <div className="mt-auto space-y-3 px-4 pb-6 pt-8">
        <div className="rounded-xl bg-[#edf2e9] p-4 ring-1 ring-[#d3dccd]">
          <div className="mb-2 text-[11px] font-semibold text-stone-500">Models · Nebius Token Factory</div>
          <div className="space-y-1.5 text-[12px]">
            <div className="flex items-center gap-2">
              <span className={`h-1.5 w-1.5 rounded-full ${state.intake.vision_model ? "bg-emerald-400" : "bg-stone-600"}`} />
              <span className="truncate">{state.intake.vision_model?.split("/").pop() ?? "vision: labelled replay"}</span>
            </div>
            <div className="flex items-center gap-2">
              <span className={`h-1.5 w-1.5 rounded-full ${state.intake.text_model ? "bg-emerald-400" : "bg-stone-600"}`} />
              <span className="truncate">{state.intake.text_model?.split("/").pop() ?? "text: rule parser"}</span>
            </div>
          </div>
          <label className="mt-4 flex cursor-pointer items-center justify-between gap-2 border-t border-[#d3dccd] pt-3 text-[12.5px] font-medium text-stone-800">
            <span>
              Live supplier search
              <span className="block text-[11px] font-normal text-stone-500">{state.live_search ? "Tavily + Nebius" : "labelled fixture"}</span>
            </span>
            <input type="checkbox" className="peer sr-only" checked={state.live_search} disabled={busy || mock} onChange={(e) => onLive(e.target.checked)} />
            <span className="relative h-5 w-9 rounded-full bg-stone-300 transition-colors after:absolute after:left-0.5 after:top-0.5 after:h-4 after:w-4 after:rounded-full after:bg-[#f6f8f3] after:transition-transform peer-checked:bg-[#1f3b2f] peer-checked:after:translate-x-4" />
          </label>
        </div>
        {mock && (
          <div className="rounded-xl bg-amber-50 px-3 py-2 text-[12px] font-semibold text-amber-800 ring-1 ring-amber-200" title="API not reachable: showing recorded mocks">
            MOCK DATA · API offline
          </div>
        )}
        <button disabled={busy} onClick={onReset} className="w-full rounded-xl px-3 py-2 text-[13px] font-semibold text-stone-700 ring-1 ring-[#d3dccd] transition-colors hover:bg-[#edf2e9] disabled:opacity-40">
          Reset demo
        </button>
        <p className="px-1 text-[11px] leading-snug text-stone-400">Synthetic bookings and stock. Supplier orders are simulated. NVIDIA retail blueprint patterns.</p>
      </div>
    </aside>
  );
}

function Headline({ state }: { state: State }) {
  const k = state.kpis;
  const ro = k.first_run_out;
  const hero = state.forecast.find((f) => f.hero);
  const protectedNow = k.hero_covered && k.orders > 0;
  const atRisk = !protectedNow && k.bookings_at_risk > 0;
  const tone = protectedNow ? "border-emerald-600" : atRisk ? "border-rose-600" : "border-stone-300";
  return (
    <Card className="overflow-hidden">
      <div className={`relative border-l-4 ${tone} px-7 py-6`}>
        <div className="relative flex flex-wrap items-end justify-between gap-6">
          <div className="max-w-2xl">
            <div className="flex items-center gap-2 text-[12px] font-semibold text-stone-500">
              {atRisk && <span className="h-2 w-2 rounded-full bg-rose-600" />}
              {protectedNow ? "Covered" : atRisk ? "Shortage ahead" : "All clear"}
            </div>
            <h2 className="mt-1.5 text-[26px] font-semibold leading-tight tracking-tight text-stone-900">
              {protectedNow
                ? `${k.bookings_protected} bookings protected`
                : atRisk
                  ? `${k.bookings_at_risk} bookings can't be served with current stock`
                  : "Every booking this week is covered"}
            </h2>
            <p className="mt-2 text-[14.5px] text-stone-600">
              {protectedNow
                ? `The order lands before ${ro ? `${when(ro.time)} (${ro.id})` : "the first booking at risk"} · ${gbp(k.revenue_covered)} of booking revenue covered.`
                : atRisk && ro && hero
                  ? `${hero.name} runs out ${when(ro.time)}: ${ro.id}, ${ro.service.toLowerCase()}, is the first booking that can't be served.`
                  : "Iris re-checks stock against the next 7 days of bookings."}
            </p>
          </div>
          {atRisk && !state.proposal && (
            <a href="#sourcing" className="rounded-lg border border-stone-300 bg-[#f6f8f3] px-3.5 py-2 text-[13.5px] font-medium text-stone-800 hover:bg-[#edf2e9]">
              Find suppliers
            </a>
          )}
        </div>
      </div>
      <div className="grid grid-cols-2 divide-x divide-y divide-[#e1e8dc] lg:grid-cols-4 lg:divide-y-0">
        {protectedNow ? (
          <Stat label="Bookings protected" value={k.bookings_protected} sub={`${gbp(k.revenue_covered)} revenue covered`} tone="emerald" />
        ) : (
          <Stat label="Bookings at risk" value={k.bookings_at_risk} sub={k.bookings_at_risk ? "can't be served" : "none"} tone={k.bookings_at_risk ? "rose" : "emerald"} />
        )}
        <Stat label={protectedNow ? "Was going to run out" : "Runs out"} value={ro ? when(ro.time) : "—"} sub={ro ? `${ro.id} · ${ro.service.toLowerCase()}` : "not this week"} tone={ro && !protectedNow ? "rose" : "stone"} />
        <Stat label="Basket" value={k.basket_total == null ? "—" : gbp(k.basket_total)} sub="delivered, incl. shipping" tone={k.basket_total == null ? "stone" : "indigo"} />
        <Stat label="Simulated orders" value={k.orders} sub={k.orders ? "stock incoming" : "nothing ordered yet"} tone={k.orders ? "emerald" : "stone"} />
      </div>
    </Card>
  );
}

export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [busy, setBusy] = useState(false);
  const [pending, setPending] = useState<string | null>(null);
  const [toast, setToast] = useState<Toast | null>(null);

  const run = useCallback(async (fn: () => Promise<State>, name: string | null = null) => {
    setBusy(true);
    setPending(name);
    try {
      const s = await fn();
      setState(s);
      if (s.flash) setToast(s.flash);
    } catch (e) {
      setToast({ kind: "error", msg: e instanceof ApiError ? e.message : String(e) });
    } finally {
      setBusy(false);
      setPending(null);
    }
  }, []);

  useEffect(() => {
    run(api.state);
  }, [run]);

  useEffect(() => {
    if (!toast) return;
    const t = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(t);
  }, [toast]);

  if (!state) {
    return (
      <div className="grid min-h-screen place-items-center bg-[#e3eadf] text-stone-500">
        <span className="flex items-center gap-2 text-sm"><Spinner /> Loading Iris…</span>
      </div>
    );
  }

  const mock = getMode() === "mock";
  const hero = state.forecast.find((f) => f.hero);
  const others = state.forecast.filter((f) => !f.hero);
  const etaFor = (sku: string) => state.orders.flatMap((o) => (o.status === "pending" ? o.lines : [])).find((l) => l.sku === sku)?.eta ?? null;

  return (
    <div className="min-h-screen bg-[#e8eee4] lg:pl-[272px]">
      <Sidebar state={state} busy={busy} mock={mock} onLive={(on) => run(() => api.live(on))} onReset={() => run(api.reset)} />

      <main className="mx-auto max-w-[1320px] space-y-6 px-5 py-7 lg:px-10">
        <header className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <div className="text-[12.5px] font-medium text-stone-500">Old St Barbers · Replenishment</div>
            <h1 className="text-[26px] font-semibold tracking-tight text-stone-900">This week's stock</h1>
          </div>
          <div className="flex items-center gap-2">
            <Badge tone="stone">Next 7 days</Badge>
            <Badge tone={state.intake.vision_model ? "emerald" : "stone"} dot>{state.intake.vision_model ? "Nebius live" : "Replay mode"}</Badge>
          </div>
        </header>

        <Headline state={state} />

        <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_400px]">
          <div className="min-w-0 space-y-6">
            {hero && (
              <Card>
                <div className="flex flex-wrap items-start justify-between gap-3 px-6 pt-5">
                  <div>
                    <h3 className="text-[15px] font-semibold tracking-tight text-stone-900">{hero.name}</h3>
                    <p className="mt-0.5 text-[13px] text-stone-500">
                      Projected stock · {hero.usage} {hero.unit} booked this week · {hero.on_hand} on hand
                    </p>
                  </div>
                  {hero.first_at_risk ? (
                    <Badge tone="rose" dot>Short {hero.uncovered} {hero.unit} · {hero.at_risk_count} bookings</Badge>
                  ) : (
                    <Badge tone="emerald" dot>{hero.covered_by_order ? "Covered by the order" : "Covered"}</Badge>
                  )}
                </div>
                <div className="px-3 pb-2 pt-2">
                  <Runout line={hero} orderEta={etaFor(hero.sku)} height={320} />
                </div>
                {Object.keys(hero.contributing).length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 border-t border-[#e1e8dc] px-6 py-4 text-[12.5px] text-stone-500">
                    Demand comes from
                    {Object.entries(hero.contributing).map(([svc, n]) => (
                      <span key={svc} className="rounded-full bg-[#e3eadf] px-2.5 py-1 font-semibold text-stone-700">
                        {n} × {svc.toLowerCase()}
                      </span>
                    ))}
                  </div>
                )}
              </Card>
            )}
            {others.length > 0 && (
              <div className="grid gap-6 md:grid-cols-2">
                {others.map((f) => (
                  <Card key={f.sku} className="px-5 pt-4">
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="text-[13.5px] font-semibold text-stone-900">{f.name}</div>
                        <div className="text-[12px] text-stone-500">{f.usage} {f.unit} booked · {f.on_hand} on hand</div>
                      </div>
                      {f.first_at_risk ? <Badge tone="rose" dot>Runs out {when(f.first_at_risk.time)}</Badge> : <Badge tone="emerald" dot>Enough for 7 days</Badge>}
                    </div>
                    <Runout line={f} orderEta={etaFor(f.sku)} height={110} compact />
                  </Card>
                ))}
              </div>
            )}
          </div>

          <Stock
            state={state}
            busy={busy}
            pending={pending}
            onSample={(b) => run(() => api.intakeSample(b), "photo")}
            onPhoto={(f) => run(() => api.intakePhoto(f), "photo")}
            onText={(t) => run(() => api.intakeText(t), "text")}
            onConfirm={(rows) => run(() => api.confirmStock(rows))}
            onClear={() => run(api.clearReview)}
          />
        </div>

        <section id="sourcing" aria-label="Supplier basket and order" className="scroll-mt-6">
          <Sourcing
            state={state}
            busy={busy}
            pending={pending}
            onRun={() => run(api.run, "run")}
            onReject={(rev, fb) => run(() => api.reject(rev, fb), "reject")}
            onApprove={(rev) => run(() => api.approve(rev), "approve")}
            onEdit={(sku, packs) => run(() => api.editLine(sku, packs))}
            onRemove={(sku) => run(() => api.removeLine(sku))}
            onReceived={(id) => run(() => api.received(id))}
          />
        </section>
      </main>

      {toast && (
        <div role="status" aria-live="polite" className="fixed bottom-5 right-5 z-50 max-w-sm rounded-lg bg-stone-900 px-4 py-3 text-white shadow-lg">
          <div className="flex items-start gap-3">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${TOAST_DOT[toast.kind]}`} />
            <span className="text-[13.5px]">{toast.msg}</span>
            <button onClick={() => setToast(null)} className="ml-auto text-stone-400 hover:text-white" aria-label="Dismiss">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}

