// t8: four-step progress bar driven by State.step.
import type { State } from "../api";

const STEPS: { key: State["step"]; label: string; hint: string }[] = [
  { key: "stock", label: "Stock", hint: "Count what's on the shelf" },
  { key: "forecast", label: "Forecast", hint: "See what bookings will use" },
  { key: "basket", label: "Basket", hint: "Review suppliers" },
  { key: "order", label: "Order", hint: "Approve and track incoming" },
];

export function Stepper({ step }: { step: State["step"] }) {
  const cur = STEPS.findIndex((s) => s.key === step);
  return (
    <ol className="grid grid-cols-2 gap-2 sm:grid-cols-4" aria-label="Progress">
      {STEPS.map((s, i) => {
        const done = i < cur;
        const active = i === cur;
        return (
          <li
            key={s.key}
            aria-current={active ? "step" : undefined}
            className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
              active
                ? "border-teal-600 bg-teal-50"
                : done
                  ? "border-slate-200 bg-white"
                  : "border-slate-200 bg-slate-50 opacity-70"
            }`}
          >
            <span
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
                active ? "bg-teal-600 text-white" : done ? "bg-teal-100 text-teal-800" : "bg-slate-200 text-slate-600"
              }`}
            >
              {done ? "✓" : i + 1}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-semibold text-slate-900">{s.label}</span>
              <span className="block truncate text-xs text-slate-500">{s.hint}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
