// t8: stock intake. Sample photo / upload / pasted text -> review rows -> confirm.
// The LIVE/REPLAY badge comes from State.intake (null model = labelled fallback).
import { useEffect, useState } from "react";
import { samplePhotoUrl, type ReviewRow, type State } from "../api";

function Badge({ model, kind }: { model: string | null; kind: "photo" | "text" }) {
  return model ? (
    <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-emerald-50 text-emerald-700 ring-emerald-600/20" title={model}>
      LIVE · {model.split("/").pop()}
    </span>
  ) : (
    <span className="inline-flex items-center rounded-md px-1.5 py-0.5 text-xs font-medium ring-1 ring-inset bg-amber-50 text-amber-800 ring-amber-600/20">
      {kind === "photo" ? "REPLAY" : "RULES"} · labelled fallback
    </span>
  );
}

type Props = {
  state: State;
  busy: boolean;
  onSample: (blurry: boolean) => void;
  onPhoto: (f: File) => void;
  onText: (t: string) => void;
  onConfirm: (rows: { sku: string; quantity: number | null; confirm: boolean }[]) => void;
  onClear: () => void;
};

export function Intake({ state, busy, onSample, onPhoto, onText, onConfirm, onClear }: Props) {
  const [tab, setTab] = useState<"photo" | "text">("photo");
  const [text, setText] = useState("1 x Northline Matte Clay 100 ml, 380 neck strips");
  const [rows, setRows] = useState<ReviewRow[]>(state.review);
  useEffect(() => setRows(state.review), [state.review]);
  const thumb = samplePhotoUrl(false);
  const skus = state.products.map((p) => p.sku);
  const edit = (i: number, patch: Partial<ReviewRow>) => setRows((r) => r.map((x, j) => (j === i ? { ...x, ...patch } : x)));
  const ticked = rows.filter((r) => r.confirm && r.sku !== "?" && r.quantity != null).length;

  return (
    <section className="rounded-lg border border-zinc-200 bg-white p-5 shadow-xs" aria-labelledby="intake-h">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="intake-h" className="text-base font-semibold tracking-tight text-zinc-900">1 · Stock count</h2>
        <div className="flex gap-2">
          <Badge model={state.intake.vision_model} kind="photo" />
          <Badge model={state.intake.text_model} kind="text" />
        </div>
      </div>

      <div className="mt-3 grid gap-4 md:grid-cols-[1fr_1.3fr]">
        <div>
          <div className="mb-3 inline-flex rounded-md bg-zinc-100 p-0.5 text-sm" role="tablist">
            {(["photo", "text"] as const).map((t) => (
              <button
                key={t}
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className={`rounded px-3 py-1 text-sm font-medium transition-colors ${tab === t ? "bg-white text-zinc-900 shadow-xs" : "text-zinc-500 hover:text-zinc-700"}`}
              >
                {t === "photo" ? "Photo" : "Pasted text"}
              </button>
            ))}
          </div>
          {tab === "photo" ? (
            <div className="space-y-3">
              {thumb && <img src={thumb} alt="Staged stocktake sheet" className="max-h-40 rounded-lg border border-zinc-200 object-contain" />}
              <div className="flex flex-wrap gap-2">
                <button disabled={busy} onClick={() => onSample(false)} className="h-9 rounded-md bg-zinc-900 px-3.5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40">
                  Use sample photo
                </button>
                <button disabled={busy} onClick={() => onSample(true)} className="h-9 rounded-md border border-zinc-200 bg-white px-3.5 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50 disabled:cursor-not-allowed disabled:opacity-40">
                  Blurry photo
                </button>
                <label className="inline-flex h-9 cursor-pointer items-center rounded-md border border-zinc-200 bg-white px-3.5 text-sm font-medium text-zinc-800 shadow-xs transition-colors hover:bg-zinc-50">
                  Upload…
                  <input type="file" accept="image/*" className="sr-only" onChange={(e) => e.target.files?.[0] && onPhoto(e.target.files[0])} />
                </label>
              </div>
            </div>
          ) : (
            <div className="space-y-2">
              <textarea value={text} onChange={(e) => setText(e.target.value)} rows={3} className="w-full rounded-md border border-zinc-200 bg-white px-3 py-2 text-sm shadow-xs placeholder:text-zinc-400 focus:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-900/10" aria-label="Stock notes" />
              <button disabled={busy || !text.trim()} onClick={() => onText(text)} className="h-9 rounded-md bg-zinc-900 px-3.5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40">
                Read text
              </button>
            </div>
          )}
          <table className="mt-4 w-full text-sm">
            <caption className="mb-1 text-left text-xs font-medium text-zinc-500">On hand now</caption>
            <tbody>
              {state.stock.map((s) => (
                <tr key={s.sku} className="border-t border-zinc-100">
                  <td className="py-1">{s.name}</td>
                  <td className="py-1 text-right tabular-nums">{s.on_hand} {s.unit}</td>
                  <td className="py-1 text-right text-xs text-zinc-500 tabular-nums">{s.incoming ? `+${s.incoming} incoming` : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div>
          {rows.length === 0 ? (
            <p className="rounded-lg border border-dashed border-zinc-200 p-6 text-center text-sm text-zinc-500">
              Read a photo or pasted text. Nothing changes until you confirm the rows.
            </p>
          ) : (
            <>
              <div className="mb-2 text-sm text-zinc-600">Review ({state.review_source}). Tick the rows that are right.</div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="text-left text-xs font-medium text-zinc-500">
                    <tr><th className="py-1">✓</th><th>Read as</th><th>Product</th><th className="text-right">Qty</th><th>Note</th></tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-100">
                    {rows.map((r, i) => (
                      <tr key={i} className="align-top">
                        <td className="py-1.5"><input type="checkbox" checked={r.confirm} onChange={(e) => edit(i, { confirm: e.target.checked })} aria-label={`Confirm ${r.raw_label}`} /></td>
                        <td className="py-1.5 pr-2">{r.raw_label}</td>
                        <td className="py-1.5 pr-2">
                          <select value={r.sku} onChange={(e) => edit(i, { sku: e.target.value })} className="h-7 rounded-md border border-zinc-200 bg-white px-1.5 text-xs shadow-xs focus:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-900/10">
                            {[...skus, "?"].map((s) => <option key={s} value={s}>{s === "?" ? "? unmatched" : state.products.find((p) => p.sku === s)?.name ?? s}</option>)}
                          </select>
                        </td>
                        <td className="py-1.5 text-right">
                          <input type="number" value={r.quantity ?? ""} onChange={(e) => edit(i, { quantity: e.target.value === "" ? null : Number(e.target.value) })} className="h-7 w-20 rounded-md border border-zinc-200 bg-white px-1.5 text-right text-sm tabular-nums shadow-xs focus:border-zinc-300 focus:outline-none focus:ring-2 focus:ring-zinc-900/10" aria-label={`Quantity for ${r.raw_label}`} />
                          <span className="ml-1 text-xs text-zinc-500">{r.unit}</span>
                        </td>
                        <td className="py-1.5 pl-2 text-xs text-amber-700">{r.note}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3 flex gap-2">
                <button disabled={busy || ticked === 0} onClick={() => onConfirm(rows.map(({ sku, quantity, confirm }) => ({ sku, quantity, confirm })))} className="h-9 rounded-md bg-zinc-900 px-3.5 text-sm font-medium text-white transition-colors hover:bg-zinc-800 disabled:cursor-not-allowed disabled:opacity-40">
                  Confirm {ticked} {ticked === 1 ? "count" : "counts"}
                </button>
                <button disabled={busy} onClick={onClear} className="h-9 rounded-md px-3.5 text-sm font-medium text-zinc-600 transition-colors hover:bg-zinc-100 disabled:cursor-not-allowed disabled:opacity-40">Discard</button>
              </div>
            </>
          )}
        </div>
      </div>
    </section>
  );
}
