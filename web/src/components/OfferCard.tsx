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
  selected: "border-zinc-900/15 shadow-card",
  alternative: "border-zinc-200 shadow-xs",
  late: "border-zinc-200 shadow-xs",
  lead: "border-dashed border-zinc-200 bg-zinc-50/50",
};

function Badge({ o }: { o: OfferOption }) {
  if (o.tag === "lead")
    return <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-zinc-50 text-zinc-600 ring-zinc-500/10">lead only</span>;
  if (o.on_time === true)
    return <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-emerald-50 text-emerald-700 ring-emerald-600/20">On time</span>;
  if (o.on_time === false)
    return (
      <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-amber-50 text-amber-800 ring-amber-600/20">
        LATE · misses {o.misses_bookings} bookings
      </span>
    );
  return <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-zinc-50 text-zinc-600 ring-zinc-500/10">ETA unknown</span>;
}

export function OfferCard({ o, reason, compact = false }: { o: OfferOption; reason?: string; compact?: boolean }) {
  const isLead = o.tag === "lead";
  return (
    <div className={`rounded-lg border bg-white p-5 ${CARD[o.tag]}`} data-testid={`offer-${o.offer_id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-semibold text-zinc-900">{o.supplier}</span>
            {o.tag === "selected" && (
              <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-zinc-900 text-white ring-zinc-900">
                Proposed
              </span>
            )}
            {o.tag === "alternative" && <span className="text-xs text-zinc-500">alternative</span>}
            <Badge o={o} />
          </div>
          <div className="truncate text-sm text-zinc-600">{o.listing}</div>
        </div>
        {!isLead && (
          <div className="shrink-0 text-right">
            <div className={`${compact ? "text-lg" : "text-2xl"} font-semibold tracking-tight tabular-nums text-zinc-900`}>
              {gbp(o.delivered_cost)}
            </div>
            <div className="text-xs text-zinc-500">delivered</div>
          </div>
        )}
      </div>

      {isLead ? (
        <p className="mt-2 text-sm text-zinc-600">Not eligible: {o.issues.join("; ") || "unverified listing"}</p>
      ) : (
        <dl className="mt-4 grid grid-cols-3 gap-4 border-t border-zinc-100 pt-4 text-sm">
          <div>
            <dt className="text-xs text-zinc-500">Packs</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-zinc-900">{o.packs ?? "–"}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Per 100 ml</dt>
            <dd className="mt-0.5 font-medium tabular-nums text-zinc-900">{gbp(o.per_100ml)}</dd>
          </div>
          <div>
            <dt className="text-xs text-zinc-500">Arrives</dt>
            <dd className={`mt-0.5 font-medium tabular-nums ${o.on_time === false ? "text-amber-700" : "text-zinc-900"}`}>{when(o.eta)}</dd>
          </div>
        </dl>
      )}

      {reason && !compact && <p className="mt-4 text-sm leading-relaxed text-zinc-600">{reason}</p>}

      <div className="mt-3 truncate text-xs text-zinc-400">
        evidence:{" "}
        {o.evidence_url ? (
          <a className="underline hover:text-zinc-600" href={o.evidence_url} target="_blank" rel="noreferrer">
            {o.evidence_label || o.evidence_url}
          </a>
        ) : (
          <span>{o.evidence_label}</span>
        )}
      </div>
    </div>
  );
}
