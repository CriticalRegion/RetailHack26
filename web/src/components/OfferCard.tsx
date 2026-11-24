import type { RankedOffer } from "./basketTypes";

export const gbp = (n?: number | null) => (n == null ? "–" : `£${n.toFixed(2)}`);

export const when = (iso?: string | null) =>
  iso
    ? new Date(iso).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit", timeZone: "Europe/London" })
    : "unknown";

export function per100(r: RankedOffer): number | null {
  return r.delivered_cost != null && r.covered_qty > 0 ? (r.delivered_cost / r.covered_qty) * 100 : null;
}

type Tag = "selected" | "alternative" | "late" | "lead";

const TAG_STYLE: Record<Tag, string> = {
  selected: "border-emerald-500 ring-1 ring-emerald-500/30",
  alternative: "border-slate-200",
  late: "border-amber-300",
  lead: "border-dashed border-slate-300 opacity-80",
};

function TimeBadge({ r, missed }: { r: RankedOffer; missed?: number }) {
  if (!r.eligible) return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">lead only</span>;
  if (r.on_time === true)
    return <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-medium text-emerald-700">on time</span>;
  if (r.on_time === false)
    return (
      <span className="rounded-full bg-amber-50 px-2 py-0.5 text-xs font-medium text-amber-800">
        late{missed != null ? ` · misses ${missed} bookings` : ""}
      </span>
    );
  return <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600">ETA unknown</span>;
}

export function OfferCard({
  r,
  tag,
  unit,
  reason,
  missed,
  compact = false,
}: {
  r: RankedOffer;
  tag: Tag;
  unit: string;
  reason?: string;
  missed?: number;
  compact?: boolean;
}) {
  const o = r.offer;
  const p100 = unit === "ml" ? per100(r) : null;
  const ev = o.evidence;
  return (
    <div className={`rounded-xl border bg-white p-4 ${TAG_STYLE[tag]}`} data-testid={`offer-${o.offer_id}`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-slate-900">{o.supplier}</span>
            {tag === "selected" && (
              <span className="rounded bg-emerald-600 px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white">
                proposed
              </span>
            )}
            <TimeBadge r={r} missed={missed} />
          </div>
          <div className="truncate text-sm text-slate-600">{o.title}</div>
        </div>
        {r.eligible && (
          <div className="text-right">
            <div className="text-xl font-bold tabular-nums text-slate-900">{gbp(r.delivered_cost)}</div>
            <div className="text-xs text-slate-500">delivered</div>
          </div>
        )}
      </div>

      {r.eligible ? (
        <dl className={`mt-3 grid ${compact ? "grid-cols-3" : "grid-cols-4"} gap-2 text-sm`}>
          <div>
            <dt className="text-xs text-slate-500">Packs</dt>
            <dd className="font-medium tabular-nums">{r.packs}</dd>
          </div>
          <div>
            <dt className="text-xs text-slate-500">Pack + ship</dt>
            <dd className="tabular-nums">
              {gbp(o.pack_price)} + {gbp(o.shipping ?? 0)}
            </dd>
          </div>
          {p100 != null && (
            <div>
              <dt className="text-xs text-slate-500">Per 100 ml</dt>
              <dd className="tabular-nums">{gbp(p100)}</dd>
            </div>
          )}
          <div>
            <dt className="text-xs text-slate-500">Arrives</dt>
            <dd className="tabular-nums">{when(o.eta)}</dd>
          </div>
        </dl>
      ) : (
        <p className="mt-2 text-sm text-slate-600">{r.issues.join("; ")}</p>
      )}

      {reason && !compact && <p className="mt-3 text-sm leading-relaxed text-slate-700">{reason}</p>}

      <div className="mt-2 text-xs text-slate-400">
        evidence:{" "}
        {ev.url ? (
          <a className="underline hover:text-slate-600" href={ev.url} target="_blank" rel="noreferrer">
            {ev.label || ev.url}
          </a>
        ) : (
          <span>
            {ev.source === "fixture" ? "labelled fixture · " : ""}
            {ev.label}
          </span>
        )}
      </div>
    </div>
  );
}
