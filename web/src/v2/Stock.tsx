// Stock intake: photo -> Nebius VLM, pasted text -> Nebius LLM. Nothing changes stock until the
// merchant ticks rows and confirms.
import { useEffect, useRef, useState } from "react";
import { samplePhotoUrl, type ReviewRow, type State } from "../api";
import { Badge, Button, Card, CardHeader, Spinner, num } from "./ui";

type Row = { confirm: boolean; sku: string; quantity: number | null };

export function Stock({
  state,
  busy,
  pending,
  onSample,
  onPhoto,
  onText,
  onConfirm,
  onClear,
}: {
  state: State;
  busy: boolean;
  pending: string | null;
  onSample: (blurry: boolean) => void;
  onPhoto: (f: File) => void;
  onText: (t: string) => void;
  onConfirm: (rows: Row[]) => void;
  onClear: () => void;
}) {
  const [tab, setTab] = useState<"photo" | "text">("photo");
  const [text, setText] = useState("1 x Northline Matte Clay 100 ml, 380 neck strips");
  const [rows, setRows] = useState<Row[]>([]);
  const fileRef = useRef<HTMLInputElement>(null);
  const review: ReviewRow[] = state.review;

  useEffect(() => {
    setRows(review.map((r) => ({ confirm: r.confirm, sku: r.sku, quantity: r.quantity })));
  }, [review]);

  const ticked = rows.filter((r) => r.confirm && r.sku !== "?" && r.quantity != null).length;
  const reading = pending === "photo" || pending === "text";
  const vlm = state.intake.vision_model;
  const llm = state.intake.text_model;
  const thumb = samplePhotoUrl(false);

  return (
    <Card className="overflow-hidden" data-testid="stock">
      <CardHeader
        title="Stock count"
        sub="Snap the shelf or paste a count. You confirm every number."
        right={
          <div className="flex rounded-xl bg-stone-100 p-1 text-[13px] font-semibold">
            {(["photo", "text"] as const).map((t) => (
              <button
                key={t}
                onClick={() => setTab(t)}
                className={`rounded-lg px-3 py-1 transition-colors ${tab === t ? "bg-white text-stone-900 shadow-sm" : "text-stone-500 hover:text-stone-800"}`}
              >
                {t === "photo" ? "Photo" : "Pasted text"}
              </button>
            ))}
          </div>
        }
      />

      <div className="px-6 pb-5 pt-4">
        <div className="mb-3 flex flex-wrap gap-1.5">
          <Badge tone={vlm ? "emerald" : "stone"} dot>{vlm ? `Vision · ${vlm.split("/").pop()}` : "Vision · replay"}</Badge>
          <Badge tone={llm ? "emerald" : "stone"} dot>{llm ? `Text · ${llm.split("/").pop()}` : "Text · rules"}</Badge>
        </div>

        {tab === "photo" ? (
          <div className="flex gap-4">
            <div className="relative h-[104px] w-[150px] shrink-0 overflow-hidden rounded-xl bg-stone-100 ring-1 ring-black/5">
              {thumb ? <img src={thumb} alt="Staged stocktake photo" className="h-full w-full object-cover object-left-top" /> : <div className="grid h-full place-items-center text-xs text-stone-400">photo</div>}
              {pending === "photo" && (
                <div className="absolute inset-0 grid place-items-center bg-white/70 backdrop-blur-[1px]">
                  <Spinner className="h-5 w-5 text-stone-700" />
                </div>
              )}
            </div>
            <div className="flex min-w-0 flex-col justify-between gap-2">
              <Button variant="primary" disabled={busy} onClick={() => onSample(false)} data-testid="sample-photo">
                {pending === "photo" ? <Spinner /> : null}
                Use sample photo
              </Button>
              <div className="flex gap-2">
                <Button size="sm" disabled={busy} onClick={() => onSample(true)}>Blurry photo</Button>
                <Button size="sm" disabled={busy} onClick={() => fileRef.current?.click()}>Upload…</Button>
                <input
                  ref={fileRef}
                  type="file"
                  accept="image/png,image/jpeg"
                  className="hidden"
                  onChange={(e) => {
                    const f = e.target.files?.[0];
                    if (f) onPhoto(f);
                    e.target.value = "";
                  }}
                />
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <textarea
              value={text}
              onChange={(e) => setText(e.target.value)}
              rows={3}
              aria-label="Stock notes"
              className="w-full resize-none rounded-xl border-0 bg-stone-50 px-3.5 py-3 text-sm text-stone-800 ring-1 ring-inset ring-stone-200 placeholder:text-stone-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-stone-300"
            />
            <Button variant="primary" disabled={busy || !text.trim()} onClick={() => onText(text)}>
              {pending === "text" ? <Spinner /> : null}
              Read text
            </Button>
          </div>
        )}

        {reading && (
          <p className="mt-3 flex items-center gap-2 text-[13px] text-stone-600">
            <Spinner className="h-3.5 w-3.5" /> Reading with {pending === "photo" ? vlm ?? "the replay" : llm ?? "the rule parser"} on Nebius…
          </p>
        )}
      </div>

      {review.length > 0 && (
        <div className="border-t border-stone-100 bg-stone-50/60 px-6 py-4">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[13px] font-semibold text-stone-800">What Iris read <span className="font-normal text-stone-500">· {state.review_source}</span></p>
            <p className="text-[12px] text-stone-500">Tick the rows that are right</p>
          </div>
          <div className="space-y-2">
            {review.map((r, i) => {
              const row = rows[i] ?? { confirm: false, sku: r.sku, quantity: r.quantity };
              const set = (p: Partial<Row>) => setRows((rs) => rs.map((x, j) => (j === i ? { ...x, ...p } : x)));
              return (
                <div key={i} className={`rounded-lg bg-white p-3 ring-1 ${row.confirm ? "ring-stone-500" : "ring-stone-200"}`}>
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      aria-label={`Confirm ${r.raw_label}`}
                      checked={row.confirm}
                      onChange={(e) => set({ confirm: e.target.checked })}
                      className="h-4 w-4 shrink-0 rounded border-stone-300 accent-stone-900"
                    />
                    <div className="min-w-0 flex-1">
                      <div className="truncate text-[13px] font-semibold text-stone-900">{r.raw_label}</div>
                      <select
                        value={row.sku}
                        onChange={(e) => set({ sku: e.target.value })}
                        aria-label={`Product for ${r.raw_label}`}
                        className="mt-1 w-full truncate rounded-lg border-0 bg-stone-50 py-1 pl-2 pr-7 text-[12px] text-stone-700 ring-1 ring-inset ring-stone-200 focus:outline-none focus:ring-stone-300"
                      >
                        {state.products.map((p) => (
                          <option key={p.sku} value={p.sku}>{p.name}</option>
                        ))}
                        <option value="?">? unmatched</option>
                      </select>
                    </div>
                    <div className="flex items-baseline gap-1">
                      <input
                        type="number"
                        aria-label={`Quantity for ${r.raw_label}`}
                        value={row.quantity ?? ""}
                        placeholder="?"
                        onChange={(e) => set({ quantity: e.target.value === "" ? null : Number(e.target.value) })}
                        className="w-20 rounded-lg border-0 bg-stone-50 px-2 py-1.5 text-right text-sm font-semibold tabular-nums text-stone-900 ring-1 ring-inset ring-stone-200 focus:outline-none focus:ring-2 focus:ring-stone-300"
                      />
                      <span className="w-8 text-[11px] text-stone-500">{r.unit}</span>
                    </div>
                  </div>
                  {r.note && <p className="mt-2 pl-7 text-[11.5px] leading-snug text-stone-500">{r.note}</p>}
                </div>
              );
            })}
          </div>
          <div className="mt-3 flex gap-2">
            <Button variant="primary" disabled={busy || ticked === 0} onClick={() => onConfirm(rows)}>
              Confirm {ticked} {ticked === 1 ? "count" : "counts"}
            </Button>
            <Button variant="ghost" disabled={busy} onClick={onClear}>Discard</Button>
          </div>
        </div>
      )}

      <div className="border-t border-stone-100 px-6 py-4">
        <p className="mb-2 text-[12px] font-medium text-stone-500">On hand now</p>
        <ul className="space-y-2">
          {state.stock.map((s) => (
            <li key={s.sku} className="flex items-center justify-between gap-3 text-[13px]">
              <span className="truncate text-stone-700">{s.name}</span>
              <span className="flex items-center gap-2">
                <span className="font-semibold tabular-nums text-stone-900">{num(s.on_hand, s.unit)}</span>
                {s.incoming > 0 && <Badge tone="emerald">+{num(s.incoming, s.unit)} incoming</Badge>}
              </span>
            </li>
          ))}
        </ul>
      </div>
    </Card>
  );
}
