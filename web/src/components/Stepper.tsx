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
    <ol className="grid grid-cols-2 gap-3 sm:grid-cols-4" aria-label="Progress">
      {STEPS.map((s, i) => {
        const done = i < cur;
        const active = i === cur;
        return (
          <li
            key={s.key}
            aria-current={active ? "step" : undefined}
            className={`flex items-center gap-3 rounded-[28px] border border-white bg-white px-3 py-2.5 shadow-xs ${active ? "" : done ? "" : "opacity-70"}`}
          >
            <span
              className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-xs font-medium ${
                active ? "bg-white text-zinc-900 ring-2 ring-zinc-900" : done ? "bg-zinc-900 text-white" : "border border-zinc-200 bg-white text-zinc-400"
              }`}
            >
              {done ? "✓" : i + 1}
            </span>
            <span className="min-w-0">
              <span className="block text-sm font-medium text-zinc-900">{s.label}</span>
              <span className="block truncate text-xs text-zinc-500">{s.hint}</span>
            </span>
          </li>
        );
      })}
    </ol>
  );
}
