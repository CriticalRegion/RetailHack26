import type { OfferOption } from "./basketTypes";

export const gbp = (n?: number | null) => (n == null ? "–" : `£${n.toFixed(2)}`);

// Server times are London-local ISO without offset ("2026-11-27T11:00"): format without TZ conversion.
const DAYS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"];
export function when(iso?: string | null): string {
  if (!iso) return "unknown";
  const [d, t = "00:00"] = iso.split("T");
  const [y, m, day] = d.split("-").map(Number);
  const wd = DAYS[new Date(Date.UTC(y, m - 1, day)).getUTCDay()];
  return `${wd} ${day} ${t.slice(0, 5)}`;
}

const CARD: Record<OfferOption["tag"], string> = {
  selected: "border-emerald-500 ring-2 ring-emerald-500/20",
  alternative: "border-slate-200",
  late: "border-amber-300 bg-amber-50/30",
  lead: "border-dashed border-slate-300 opacity-75",
};

function Badge({ o }: { o: OfferOption }) {
  if (o.tag === "lead")
    return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">lead only</span>;
  if (o.on_time === true)
    return <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-medium text-emerald-800">on time</span>;
  if (o.on_time === false)
    return (
      <span className="rounded-full bg-amber-100 px-2 py-0.5 text-xs font-semibold text-amber-900">
        LATE · misses {o.misses_bookings} bookings
      </span>
    );
  return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">ETA unknown</span>;
}

export function OfferCard({ o, reason, compact = false }: { o: OfferOption; reason?: string; compact?: boolean }) {
  const isLead = o.tag === "lead";
  return (
    <div className={`rounded-xl border bg-white p-4 ${CARD[o.tag]}`} data-testid={`offer-${o.offer_id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-slate-900">{o.supplier}</span>
            {o.tag === "selected" && (
              <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                proposed
              </span>
            )}
            {o.tag === "alternative" && <span className="text-xs text-slate-500">alternative</span>}
            <Badge o={o} />
          </div>
          <div className="truncate text-sm text-slate-600">{o.listing}</div>
        </div>
        {!isLead && (
          <div className="shrink-0 text-right">
            <div className={`${compact ? "text-lg" : "text-2xl"} font-bold tabular-nums text-slate-900`}>
              {gbp(o.delivered_cost)}
            </div>
            <div className="text-xs text-slate-500">delivered</div>
          </div>
        )}
      </div>

      {isLead ? (
        <p className="mt-2 text-sm text-slate-600">Not eligible: {o.issues.join("; ") || "unverified listing"}</p>
      ) : (
        <dl className="mt-3 grid grid-cols-3 gap-2 text-sm">
          <div>
            <dt className="text-xs text-slate-500">Packs</dt>
            <dd className="font-medium tabular-nums">{o.packs ?? "–"}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Per 100 ml</dt>
            <dd className="tabular-nums">{gbp(o.per_100ml)}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Arrives</dt>
            <dd className={`tabular-nums ${o.on_time === false ? "font-semibold text-amber-800" : ""}`}>{when(o.eta)}</dd>
          </div>
        </dl>
      )}

      {reason && !compact && <p className="mt-3 text-sm leading-relaxed text-slate-700">{reason}</p>}

      <div className="mt-2 truncate text-xs text-slate-400">
        evidence:{" "}
        {o.evidence_url ? (
          <a className="underline hover:text-slate-600" href={o.evidence_url} target="_blank" rel="noreferrer">
            {o.evidence_label || o.evidence_url}
          </a>
        ) : (
          <span>{o.evidence_label}</span>
        )}
      </div>
    </div>
  );
}
