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
  success: "border-emerald-300 bg-emerald-50 text-emerald-900",
  info: "border-sky-300 bg-sky-50 text-sky-900",
  warning: "border-amber-300 bg-amber-50 text-amber-900",
  error: "border-red-300 bg-red-50 text-red-900",
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
    return <main className="grid min-h-screen place-items-center text-slate-500">Loading Iris…</main>;
  }

  const hero = state.forecast.find((f) => f.hero);
  const others = state.forecast.filter((f) => !f.hero);
  const mock = getMode() === "mock";

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
          <div>
            <h1 className="text-xl font-bold tracking-tight">
              Iris <span className="font-normal text-slate-500">· never run out of what's booked</span>
            </h1>
            <p className="text-sm text-slate-500">
              {state.shop.name} · {new Date(state.shop.clock).toLocaleString("en-GB", { weekday: "short", day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })} ({state.shop.tz})
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2 text-sm">
            {mock && (
              <span className="rounded-full bg-amber-100 px-2.5 py-1 font-semibold text-amber-800" title="API not reachable: showing recorded mocks">
                MOCK DATA
              </span>
            )}
            <label className="flex items-center gap-2 rounded-lg border border-slate-200 px-3 py-1.5">
              <input type="checkbox" checked={state.live_search} disabled={busy || mock} onChange={(e) => run(() => api.live(e.target.checked))} />
              Live supplier search
              <span className={`rounded px-1.5 py-0.5 text-xs font-semibold ${state.live_search ? "bg-emerald-100 text-emerald-800" : "bg-slate-100 text-slate-600"}`}>
                {state.live_search ? "Tavily + Nebius" : "labelled fixture"}
              </span>
            </label>
            <button disabled={busy} onClick={() => run(api.reset)} className="rounded-lg border border-slate-300 px-3 py-1.5 hover:bg-slate-50 disabled:opacity-50">
              Reset demo
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-6xl space-y-5 px-4 py-5">
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

        <section aria-labelledby="fc-h" className="space-y-3">
          <h2 id="fc-h" className="text-lg font-semibold">2 · Run-out forecast (next 7 days)</h2>
          {hero && <Timeline line={hero} firstRunOut={state.kpis.first_run_out} height={300} />}
          {hero && Object.keys(hero.contributing).length > 0 && (
            <p className="text-sm text-slate-600">
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
          <div className="grid gap-3 md:grid-cols-2">
            {others.map((f) => (
              <Timeline key={f.sku} line={f} height={200} />
            ))}
          </div>
        </section>

        <section aria-labelledby="basket-h" className="space-y-3">
          <h2 id="basket-h" className="text-lg font-semibold">3 · Supplier basket and order</h2>
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
        <div role="status" aria-live="polite" className={`fixed bottom-4 right-4 z-50 max-w-sm rounded-xl border px-4 py-3 shadow-lg ${toastTone[toast.kind]}`}>
          <div className="flex items-start gap-3">
            <span className="text-sm">{toast.msg}</span>
            <button onClick={() => setToast(null)} className="ml-auto text-sm opacity-60 hover:opacity-100" aria-label="Dismiss">✕</button>
          </div>
        </div>
      )}
    </div>
  );
}
