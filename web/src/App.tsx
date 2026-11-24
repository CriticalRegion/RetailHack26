// t8: app shell. Renders State, calls an action, replaces State with the response.
// No business logic here (contracts/api.md).
import { useCallback, useEffect, useState } from "react";
import { api, ApiError, getMode, type State } from "./api";
import { Basket } from "./components/Basket";
import { Intake } from "./components/Intake";
import { KpiHero } from "./components/KpiHero";
import { Stepper } from "./components/Stepper";
import Timeline from "./components/Timeline";

type Toast = NonNullable<State["flash"]>;

const toastTone: Record<Toast["kind"], string> = {
  success: "bg-emerald-500",
  info: "bg-zinc-400",
  warning: "bg-amber-500",
  error: "bg-red-500",
};

export default function App() {
  const [state, setState] = useState<State | null>(null);
  const [busy, setBusy] = useState(false);
  const [toast, setToast] = useState<Toast | null>(null);

  const run = useCallback(async (fn: () => Promise<State>) => {
    setBusy(true);
    try {
      const s = await fn();
      setState(s);
      if (s.flash) setToast(s.flash);
    } catch (e) {
      setToast({ kind: "error", msg: e instanceof ApiError ? e.message : String(e) });
    } finally {
      setBusy(false);
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
    return <main className="grid min-h-screen place-items-center text-sm text-zinc-500">Loading Iris…</main>;
  }

  const hero = state.forecast.find((f) => f.hero);
  const others = state.forecast.filter((f) => !f.hero);
  const mock = getMode() === "mock";

  return (
    <div className="min-h-screen bg-[#ecebe7]">
      <header className="sticky top-0 z-40 bg-[#ecebe7]/85 backdrop-blur">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-6 py-3">
          <div>
            <h1 className="flex items-center gap-2 text-lg font-semibold tracking-tight text-zinc-900">
              <span className="relative inline-block h-6 w-6 rounded-full bg-zinc-900"><span className="absolute right-1 top-1 h-1.5 w-1.5 rounded-full bg-[#d9f36a]" /></span>
              Iris <span className="text-sm font-normal text-zinc-500">· never run out of what's booked</span>
            </h1>
            <p className="mt-0.5 text-xs text-zinc-500">
              {state.shop.name} · {new Date(state.shop.clock).toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })} ({state.shop.tz})
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {mock && (
              <span className="inline-flex items-center rounded-full bg-amber-50 px-1.5 py-0.5 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20" title="API not reachable: showing recorded mocks">
                MOCK DATA
              </span>
            )}
            <label className="flex h-8 items-center gap-2 rounded-full border border-zinc-200 bg-white px-3 text-sm font-medium text-zinc-800 shadow-xs">
              <input type="checkbox" checked={state.live_search} disabled={busy || mock} onChange={(e) => run(() => api.live(e.target.checked))} />
              Live supplier search
              <span className={`inline-flex items-center rounded-full px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset ${state.live_search ? "bg-emerald-50 text-emerald-700 ring-emerald-600/20" : "bg-zinc-50 text-zinc-600 ring-zinc-500/10"}`}>
                {state.live_search ? "Tavily + Nebius" : "labelled fixture"}
              </span>
            </label>
            <button disabled={busy} onClick={() => run(api.reset)} className="h-8 rounded-full border border-zinc-200 bg-white px-3 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40">
              Reset demo
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-8 px-6 py-8">
        <Stepper step={state.step} />
        <KpiHero kpis={state.kpis} />

        <Intake
          state={state}
          busy={busy}
          onSample={(b) => run(() => api.intakeSample(b))}
          onPhoto={(f) => run(() => api.intakePhoto(f))}
          onText={(t) => run(() => api.intakeText(t))}
          onConfirm={(rows) => run(() => api.confirmStock(rows))}
          onClear={() => run(api.clearReview)}
        />

        <section aria-labelledby="fc-h" className="space-y-4">
          <h2 id="fc-h" className="text-base font-semibold tracking-tight text-zinc-900">2 · Run-out forecast (next 7 days)</h2>
          {hero && <Timeline line={hero} firstRunOut={state.kpis.first_run_out} height={300} />}
          {hero && Object.keys(hero.contributing).length > 0 && (
            <p className="text-sm text-zinc-600">
              {hero.name} demand comes from{" "}
              {Object.entries(hero.contributing).map(([svc, n], i, a) => (
                <span key={svc}>
                  {n} × {svc.toLowerCase()}
                  {i < a.length - 1 ? ", " : ""}
                </span>
              ))}
              .
            </p>
          )}
          <div className="grid gap-6 md:grid-cols-2">
            {others.map((f) => (
              <Timeline key={f.sku} line={f} height={200} />
            ))}
          </div>
        </section>

        <section aria-label="Supplier basket and order" id="basket">
          <Basket
            proposal={state.proposal}
            offers={state.offers}
            history={state.history}
            orders={state.orders}
            kpis={state.kpis}
            busy={busy}
            onRun={() => run(api.run)}
            onReject={(rev, fb) => run(() => api.reject(rev, fb))}
            onApprove={(rev) => run(() => api.approve(rev))}
            onReceived={(id) => run(() => api.received(id))}
          />
        </section>
      </main>

      {toast && (
        <div role="status" aria-live="polite" className="fixed bottom-4 right-4 z-50 max-w-sm rounded-[28px] border border-white bg-white px-4 py-3 shadow-card">
          <div className="flex items-start gap-3">
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${toastTone[toast.kind]}`} />
            <span className="text-sm text-zinc-800">{toast.msg}</span>
            <button onClick={() => setToast(null)} className="ml-auto text-sm text-zinc-500 hover:text-zinc-900" aria-label="Dismiss">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}
