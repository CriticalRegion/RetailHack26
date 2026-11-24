// Run-out chart for one SKU: projected stock (with any order) vs. without the order, the first
// booking that can't be served, and when the order lands.
import { Area, CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { ForecastEntry } from "../api";
import { when } from "./ui";

type Pt = { t: number; v: number };
const pts = (s: { time: string; projected: number }[]): Pt[] => s.map((p) => ({ t: new Date(p.time).getTime(), v: p.projected }));

export function Runout({ line, orderEta, height = 300, compact = false }: { line: ForecastEntry; orderEta?: string | null; height?: number; compact?: boolean }) {
  const withOrder = pts(line.series);
  const without = pts(line.series_without_order);
  const hasOrder = !!orderEta && without.length > 0 && JSON.stringify(withOrder) !== JSON.stringify(without);
  const all = [...withOrder, ...(hasOrder ? without : [])];
  if (all.length === 0) return null;
  const minV = Math.min(0, ...all.map((p) => p.v));
  const maxV = Math.max(...all.map((p) => p.v), 1);
  const pad = (maxV - minV) * 0.12;
  const lo = Math.floor(minV - (minV < 0 ? pad : 0));
  const hi = Math.ceil(maxV + pad);
  const t0 = all[0].t;
  const t1 = Math.max(...all.map((p) => p.t));
  const riskT = (hasOrder ? null : line.first_at_risk) ?? null;
  const wasRisk = hasOrder ? line.first_at_risk ?? null : null;
  const color = hasOrder || line.uncovered === 0 ? "#059669" : "#1c1917";
  const gid = `g-${line.sku}`;
  const ticks: number[] = [];
  for (let d = new Date(t0); d.getTime() <= t1; d.setDate(d.getDate() + 1)) {
    const m = new Date(d); m.setHours(0, 0, 0, 0);
    if (m.getTime() >= t0) ticks.push(m.getTime());
  }

  return (
    <div style={{ height }} className="w-full">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart margin={{ top: compact ? 6 : 24, right: 12, bottom: 0, left: compact ? 4 : 0 }}>
          <defs>
            <linearGradient id={gid} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.07} />
              <stop offset="100%" stopColor={color} stopOpacity={0.02} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#f0efed" vertical={false} />
          <XAxis
            type="number"
            dataKey="t"
            domain={[t0, t1]}
            scale="time"
            tickFormatter={(t: number) => new Date(t).toLocaleDateString("en-GB", { weekday: "short", day: "numeric" })}
            tick={{ fontSize: 11, fill: "#a8a29e" }}
            axisLine={false}
            tickLine={false}
            ticks={ticks}
            interval={0}
            hide={compact}
          />
          <YAxis
            domain={[lo, hi]}
            tick={{ fontSize: 11, fill: "#a8a29e" }}
            axisLine={false}
            tickLine={false}
            width={compact ? 40 : 56}
            tickFormatter={(v: number) => `${v}${compact ? "" : ` ${line.unit}`}`}
          />
          {lo < 0 && <ReferenceArea y1={lo} y2={0} fill="#f43f5e" fillOpacity={0.05} ifOverflow="extendDomain" />}
          <ReferenceLine y={0} stroke="#e7e5e4" />
          <Tooltip
            labelFormatter={(t) => when(new Date(Number(t)).toISOString().slice(0, 16))}
            formatter={(v: number, name) => [`${v} ${line.unit}`, name === "without" ? "without the order" : "projected stock"]}
            contentStyle={{ borderRadius: 12, border: "1px solid #e7e5e4", fontSize: 12, boxShadow: "0 8px 24px -12px rgba(0,0,0,.2)" }}
          />
          {hasOrder && (
            <Line data={without} dataKey="v" name="without" type="stepAfter" stroke="#f43f5e" strokeOpacity={0.55} strokeDasharray="5 5" strokeWidth={1.5} dot={false} isAnimationActive={false} />
          )}
          <Area data={withOrder} dataKey="v" name="projected" type="stepAfter" stroke={color} strokeWidth={2.25} fill={`url(#${gid})`} dot={false} isAnimationActive={false} baseValue={lo} />
          {riskT && !compact && (
            <ReferenceLine
              x={new Date(riskT.time).getTime()}
              stroke="#f43f5e"
              strokeWidth={1.5}
              label={{ value: `Runs out · ${when(riskT.time)} · ${riskT.id}`, position: "top", fill: "#e11d48", fontSize: 11, fontWeight: 600 }}
            />
          )}
          {wasRisk && !compact && (
            <ReferenceLine x={new Date(wasRisk.time).getTime()} stroke="#f43f5e" strokeOpacity={0.4} strokeDasharray="3 3"
              label={{ value: `was: ${when(wasRisk.time)}`, position: "top", fill: "#e11d48", fontSize: 11 }} />
          )}
          {hasOrder && orderEta && !compact && (
            <ReferenceLine x={new Date(orderEta).getTime()} stroke="#059669" strokeWidth={1.5}
              label={{ value: `Order lands ${when(orderEta)}`, position: "insideTopLeft", fill: "#047857", fontSize: 11, fontWeight: 600 }} />
          )}
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
