// Iris v2 design primitives. One look everywhere: stone page, white cards, near-black for action,
// emerald = covered / on time, rose = at risk, amber = late.
import type { ReactNode } from "react";

export const gbp = (n: number | null | undefined) => (n == null ? "—" : `£${n.toFixed(2)}`);

export const when = (iso: string | null | undefined) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return `${d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric" })} ${d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
};

export const num = (n: number, unit = "") => `${Number.isInteger(n) ? n : n.toFixed(1)}${unit ? ` ${unit}` : ""}`;

export function Card({ children, className = "", ...rest }: { children: ReactNode; className?: string } & Record<string, unknown>) {
  return (
    <div
      className={`rounded-xl border border-[#d5d9d1] bg-[#f8f8f6] ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export function CardHeader({ title, sub, right }: { title: ReactNode; sub?: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 px-6 pt-5">
      <div className="min-w-0">
        <h3 className="text-[15px] font-semibold tracking-tight text-stone-900">{title}</h3>
        {sub && <p className="mt-0.5 text-[13px] text-stone-500">{sub}</p>}
      </div>
      {right && <div className="shrink-0">{right}</div>}
    </div>
  );
}

type Tone = "indigo" | "emerald" | "rose" | "amber" | "stone" | "dark";
const TONES: Record<Tone, string> = {
  indigo: "bg-[#404e3b] text-white ring-[#404e3b]",
  emerald: "bg-emerald-50 text-emerald-700 ring-emerald-600/20",
  rose: "bg-rose-50 text-rose-700 ring-rose-600/15",
  amber: "bg-amber-50 text-amber-800 ring-amber-600/20",
  stone: "bg-[#e3e7df] text-stone-600 ring-stone-500/10",
  dark: "bg-stone-900 text-white ring-stone-900",
};

export function Badge({ tone = "stone", children, dot = false }: { tone?: Tone; children: ReactNode; dot?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 whitespace-nowrap rounded px-1.5 py-0.5 text-[11px] font-medium ring-1 ring-inset ${TONES[tone]}`}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" />}
      {children}
    </span>
  );
}

type Variant = "primary" | "approve" | "secondary" | "ghost" | "danger";
const VARIANTS: Record<Variant, string> = {
  primary: "bg-[#404e3b] text-white hover:bg-[#55664f]",
  approve: "bg-emerald-700 text-white hover:bg-emerald-800",
  secondary: "bg-[#f8f8f6] text-stone-800 ring-1 ring-inset ring-[#d5d9d1] hover:bg-[#eef0eb]",
  ghost: "text-stone-600 hover:bg-[#e3e7df]",
  danger: "bg-[#f8f8f6] text-rose-700 ring-1 ring-inset ring-rose-200 hover:bg-rose-50",
};

export function Button({
  variant = "secondary",
  size = "md",
  className = "",
  children,
  ...rest
}: { variant?: Variant; size?: "sm" | "md" | "lg"; className?: string; children: ReactNode } & React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const sizes = { sm: "h-8 px-3 text-[13px]", md: "h-10 px-4 text-sm", lg: "h-12 px-5 text-[15px]" };
  return (
    <button
      className={`inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-stone-400 disabled:cursor-not-allowed disabled:opacity-40 ${sizes[size]} ${VARIANTS[variant]} ${className}`}
      {...rest}
    >
      {children}
    </button>
  );
}

export function Spinner({ className = "h-4 w-4" }: { className?: string }) {
  return <span className={`inline-block animate-spin rounded-full border-2 border-current border-r-transparent ${className}`} aria-hidden />;
}

export function Stat({ label, value, sub, tone = "stone" }: { label: string; value: ReactNode; sub?: ReactNode; tone?: Tone }) {
  const bar = { indigo: "bg-[#404e3b]", emerald: "bg-emerald-500", rose: "bg-rose-500", amber: "bg-amber-500", stone: "bg-stone-300", dark: "bg-stone-900" }[tone];
  return (
    <div className="relative min-w-0 px-6 py-5">
      <div className="flex items-center gap-2 text-[12px] font-medium text-stone-500">
        <span className={`h-2 w-2 rounded-full ${bar}`} />
        {label}
      </div>
      <div className="mt-2 truncate text-[28px] font-semibold leading-none tracking-tight text-stone-900 tabular-nums">{value}</div>
      {sub && <div className="mt-2 truncate text-[12.5px] text-stone-500">{sub}</div>}
    </div>
  );
}
