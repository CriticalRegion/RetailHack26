// t10: run-out timeline. Pure rendering of State.forecast[i]; no business logic.
// Solid line = projected stock with pending orders. Dashed line = without the order (shown once an
// order changes the projection). Red marker = first booking that can't be served. Red band = below zero.
import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceArea,
  ReferenceDot,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export type TimelineBooking = { id: string; time: string; service: string };
export type TimelinePoint = { time: string; projected: number };
export type TimelineForecast = {
  sku: string;
  name: string;
  unit: string;
  hero: boolean;
  uncovered: number;
  first_at_risk: TimelineBooking | null;
  at_risk_count: number;
  covered_by_order: boolean;
  series: TimelinePoint[];
  series_without_order: TimelinePoint[];
};

type Props = {
  line: TimelineForecast;
  /** kpis.first_run_out: keeps the original run-out marker visible after an order covers it */
  firstRunOut?: TimelineBooking | null;
  height?: number;
};

const ms = (iso: string) => new Date(iso).getTime(); // ISO local London; the browser's zone only shifts both axes equally
const toPts = (s: TimelinePoint[]) => s.map((p) => ({ t: ms(p.time), v: p.projected }));
const day = (t: number) => new Date(t).toLocaleDateString("en-GB", { weekday: "short", day: "numeric" });
const when = (t: number) =>
  new Date(t).toLocaleString("en-GB", { weekday: "short", hour: "2-digit", minute: "2-digit" });
const unitLabel = (u: string) => (u === "unit" || u === "units" ? "" : ` ${u}`);

/** First point where the with-order series departs from the baseline: the delivery landing. */
function arrival(withOrder: TimelinePoint[], without: TimelinePoint[]): number | null {
  for (let i = 0; i < withOrder.length; i++) {
    const a = withOrder[i];
    const b = without[i];
    if (!b || a.time !== b.time || a.projected !== b.projected) return ms(a.time);
  }
  return null;
}

export default function Timeline({ line, firstRunOut, height = 280 }: Props) {
  const withOrder = toPts(line.series);
  const without = toPts(line.series_without_order);
  const orderLands = line.covered_by_order || withOrder.length !== without.length
    ? arrival(line.series, line.series_without_order)
    : null;
  const marker = line.first_at_risk ?? (line.covered_by_order && line.hero ? firstRunOut ?? null : null);
  const markerT = marker ? ms(marker.time) : null;
  const all = [...withOrder, ...(orderLands ? without : [])];
  const minV = Math.min(0, ...all.map((p) => p.v));
  const maxV = Math.max(...all.map((p) => p.v));
  const step = maxV - minV > 300 ? 100 : 50;
  const pad = Math.max(10, (maxV - minV) * 0.08);
  const lo = minV < 0 ? Math.floor((minV - pad) / step) * step : 0;
  const hi = Math.ceil((maxV + pad) / step) * step;
  const ticks = Array.from(new Set(withOrder.map((p) => new Date(p.t).setHours(0, 0, 0, 0)))).filter(
    (t) => t >= withOrder[0].t - 86_400_000,
  );
  const u = unitLabel(line.unit);
  const status = line.first_at_risk
    ? `Runs out ${when(ms(line.first_at_risk.time))} · ${line.first_at_risk.id} ${line.first_at_risk.service.toLowerCase()} · ${line.at_risk_count} bookings at risk`
    : line.covered_by_order
      ? "Covered: the order lands before the first booking at risk"
      : "Enough stock for the next 7 days";

  return (
    <figure className="w-full rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900">
      <figcaption className="mb-2 flex flex-wrap items-baseline justify-between gap-2">
        <span className="font-semibold text-slate-900 dark:text-slate-100">{line.name}</span>
        <span
          className={
            line.first_at_risk
              ? "rounded-full bg-red-50 px-2.5 py-0.5 text-sm font-medium text-red-700 dark:bg-red-950 dark:text-red-300"
              : "rounded-full bg-emerald-50 px-2.5 py-0.5 text-sm font-medium text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300"
          }
        >
          {status}
        </span>
      </figcaption>
      <div style={{ height }} aria-label={`${line.name} projected stock over the next 7 days. ${status}`} role="img">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart margin={{ top: 16, right: 16, bottom: 4, left: 4 }}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" vertical={false} />
            <XAxis
              dataKey="t"
              type="number"
              scale="time"
              domain={[withOrder[0]?.t ?? "dataMin", "dataMax"]}
              ticks={ticks}
              tickFormatter={day}
              tick={{ fontSize: 12, fill: "#64748b" }}
              allowDuplicatedCategory={false}
            />
            <YAxis
              dataKey="v"
              domain={[lo, hi]}
              ticks={Array.from({ length: Math.round((hi - lo) / step) + 1 }, (_, i) => lo + i * step)}
              tick={{ fontSize: 12, fill: "#64748b" }}
              tickFormatter={(v: number) => `${v}${u}`}
              width={64}
            />
            {minV < 0 && <ReferenceArea y1={lo} y2={0} fill="#ef4444" fillOpacity={0.12} />}
            <ReferenceLine y={0} stroke="#94a3b8" />
            <Tooltip
              labelFormatter={(t) => when(Number(t))}
              formatter={(v: number, name: string) => [`${v}${u}`, name]}
            />
            {orderLands && (
              <Line
                data={without}
                dataKey="v"
                name="Without the order"
                type="stepAfter"
                stroke="#ef4444"
                strokeDasharray="6 4"
                strokeWidth={2}
                dot={false}
                isAnimationActive={false}
              />
            )}
            <Line
              data={withOrder}
              dataKey="v"
              name={orderLands ? "With the order" : "Projected stock"}
              type="stepAfter"
              stroke="#0f766e"
              strokeWidth={2.5}
              dot={false}
              isAnimationActive={false}
            />
            {orderLands && (
              <ReferenceLine
                x={orderLands}
                stroke="#0f766e"
                strokeDasharray="2 3"
                label={{ value: `order lands ${when(orderLands)}`, position: "insideBottomRight", fill: "#14b8a6", fontSize: 12, fontWeight: 600 }}
              />
            )}
            {markerT !== null && marker && (
              <>
                <ReferenceLine
                  x={markerT}
                  stroke="#dc2626"
                  strokeWidth={1.5}
                  label={{
                    value: `${line.first_at_risk ? "first at risk" : "was at risk"}: ${when(markerT)} · ${marker.id}`,
                    position: "insideTopRight",
                    fill: "#dc2626",
                    fontSize: 12,
                    fontWeight: 600,
                  }}
                />
                <ReferenceDot x={markerT} y={0} r={6} fill="#dc2626" stroke="#fff" strokeWidth={2} />
              </>
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500 dark:text-slate-400">
        <span className="flex items-center gap-1.5">
          <span className="inline-block h-0.5 w-5 bg-teal-700" /> {orderLands ? "with the order" : "projected stock"}
        </span>
        {orderLands && (
          <span className="flex items-center gap-1.5">
            <span className="inline-block w-5 border-t-2 border-dashed border-red-500" /> without the order
          </span>
        )}
        {markerT !== null && (
          <span className="flex items-center gap-1.5">
            <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-600" /> first booking that can't be served
          </span>
        )}
      </div>
    </figure>
  );
}
