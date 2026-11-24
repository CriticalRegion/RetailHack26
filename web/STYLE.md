# Iris UI style (Flux UI-inspired) - t15 restyle, 18:55-19:20

Visual-only: change classNames, never data-testid, button labels, props, API calls or behaviour.
Rollback point: git tag `ui-pre-restyle`.

**Palette**: neutrals are `zinc` (replace every `slate-*` with `zinc-*`). One accent: `emerald` (approve, on-time, covered).
Status colours only as small badges or dots, never as big tinted card backgrounds: amber = late, red = at risk/unmet.

**Surfaces**: page `bg-white`. Cards `rounded-lg border border-zinc-200 bg-white shadow-xs` (no ring-2, no tinted bg).
Section spacing `space-y-8`/`gap-6`; card padding `p-5`. Dividers `border-zinc-100`.

**Type** (Inter, set globally): page title `text-xl font-semibold tracking-tight text-zinc-900`;
section heading `text-base font-semibold tracking-tight text-zinc-900`; body `text-sm text-zinc-600`;
labels `text-xs font-medium text-zinc-500` (no uppercase tracking-wide shouting); numbers `tabular-nums`;
KPI values `text-3xl font-semibold tracking-tight text-zinc-900` (status shown by a badge next to it, not red text).

**Buttons** (`h-9 rounded-md px-3.5 text-sm font-medium transition-colors`):
primary `bg-zinc-900 text-white hover:bg-zinc-800`; approve `bg-emerald-600 text-white hover:bg-emerald-500`;
secondary `border border-zinc-200 bg-white text-zinc-800 shadow-xs hover:bg-zinc-50`; ghost `text-zinc-600 hover:bg-zinc-100`.
Disabled `disabled:opacity-40 disabled:cursor-not-allowed`.

**Badges**: `inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset`
emerald `bg-emerald-50 text-emerald-700 ring-emerald-600/20`; amber `bg-amber-50 text-amber-800 ring-amber-600/20`;
red `bg-red-50 text-red-700 ring-red-600/10`; neutral `bg-zinc-50 text-zinc-600 ring-zinc-500/10`.

**Inputs**: `h-9 rounded-md border border-zinc-200 bg-white px-3 text-sm shadow-xs placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-zinc-900/10 focus:border-zinc-300`.

**Charts** (Recharts): line `#18181b` (zinc-900) 1.5px, after-order line emerald `#10b981`, grid `#f4f4f5`, axis text `#71717a` 11px, at-risk marker `#ef4444`, shortage area very light `#fef2f2`.

Owners: App/Stepper/KpiHero/Timeline @criticalregion · Intake @tudor · Basket/OfferCard/OrderConfirm @abhi.
Before pushing: `npm --prefix web run build` passes + look at your section in the browser (http://localhost:5173 with the API on :8000).
