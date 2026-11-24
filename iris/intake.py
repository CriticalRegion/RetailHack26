"""Stock intake: modality router (photo -> VLM, text -> LLM), shared extraction schema, validation and SKU matching.

Both paths return review rows for the app's data editor:
    {"confirm", "raw label", "sku", "quantity", "unit", "note"}
Quantities are absolute on-hand counts in the SKU's base unit (ml for clay, units for strips).
Nothing here changes stock: the merchant confirms rows in the app first.
If the Nebius call is not configured or fails, a labelled fallback runs (rule parser for text,
replay for the staged photo) so the demo path still works.
"""
from __future__ import annotations

import re
from typing import Literal, Optional

from pydantic import BaseModel, Field

from iris import llm
from iris.sourcing import PRODUCTS, ProductSpec

Route = Literal["vlm", "llm"]


class Observation(BaseModel):
    """One candidate stock observation from either model."""
    raw_label: str
    sku: Optional[str] = None
    count: Optional[float] = Field(default=None, description="number observed, null if unreadable")
    count_unit: Literal["item", "base"] = "item"  # item = tubs/boxes/strips, base = ml or units already
    evidence: str = ""
    ambiguity: str = ""


def route(kind: str) -> Route:
    """Explicit modality dispatcher: the UI knows the input type."""
    return "vlm" if kind in ("photo", "image") else "llm"


def _catalog(products: dict[str, ProductSpec]) -> str:
    return "\n".join(f"- sku={p.sku}: {p.brand} {p.product} {p.item_size:g} {p.unit} per item; aliases: {', '.join(p.aliases)}"
                     for p in products.values())


SCHEMA = ('Return only JSON: {"items":[{"raw_label":str,"sku":str|null,"count":number|null,'
          '"count_unit":"item"|"base","evidence":str,"ambiguity":str}]}. '
          'Prefer count_unit "base": the TOTAL in the catalog base unit. For ml products: full items x item size, '
          'plus open items x the stated % left x item size (1 full + 1 open at 20% of 100 ml = 120). '
          'For unit products: individual pieces (4 boxes of 100 = 400). '
          'Use count_unit "item" only for a plain item count with no conversion info. '
          'Use sku only from the catalog; null if unsure. If a count is unreadable, count=null and explain in ambiguity. '
          'Never guess a number you cannot see or read.')


def match_sku(label: str, products: dict[str, ProductSpec]) -> Optional[str]:
    low = label.lower()
    for p in products.values():
        if any(a in low for a in p.aliases) or p.product.lower() in low:
            return p.sku
    return None


MAX_PLAUSIBLE = {"ml": 3000, "unit": 2000, "units": 2000}  # a barbershop shelf; above this needs a human look


def to_rows(obs: list[Observation], products: dict[str, ProductSpec], source: str,
            auto_confirm: bool = True) -> list[dict]:
    """Validate observations in code and convert to base-unit review rows."""
    rows = []
    for o in obs:
        sku = o.sku if o.sku in products else match_sku(o.raw_label, products)
        spec = products.get(sku) if sku else None
        qty = o.count
        notes = [source]
        if spec and qty is not None:
            if qty < 0:
                qty, notes = None, notes + ["negative count rejected"]
            elif o.count_unit == "item" and spec.unit == "ml":
                qty = qty * spec.item_size
            if qty is not None and qty > MAX_PLAUSIBLE.get(spec.unit, 5000):
                notes.append(f"implausible count {qty:g} - check it")
                o = o.model_copy(update={"ambiguity": o.ambiguity or "implausible count"})
        if o.sku and o.sku not in products:
            notes.append(f"model SKU '{o.sku}' not in catalog")
        if not sku:
            notes.append("unmatched - pick a SKU")
        if qty is None:
            notes.append("count unknown - enter it")
        if o.ambiguity:
            notes.append(o.ambiguity)
        rows.append({"confirm": auto_confirm and bool(sku and qty is not None and not o.ambiguity), "raw label": o.raw_label,
                     "sku": sku or "?", "quantity": qty, "unit": spec.unit if spec else "?",
                     "note": "; ".join(notes)})
    return rows


def _num(v) -> Optional[float]:
    """Lenient number: 120, "120", "120 ml", "1,200" -> float; anything else -> None."""
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        return float(v)
    m = re.search(r"\d+(?:[.,]\d+)*", str(v or ""))
    return float(m.group(0).replace(",", "")) if m else None


def _clean(it: dict) -> dict:
    """Models drift from the schema (string counts, odd count_unit, extra keys): coerce before validating."""
    it = {k: it.get(k) for k in ("raw_label", "sku", "count", "count_unit", "evidence", "ambiguity")}
    it["raw_label"] = str(it.get("raw_label") or "")[:120] or "(no label)"
    raw_count, unit = it.get("count"), str(it.get("count_unit") or "").lower()
    it["count"] = _num(raw_count)
    guessed = it["count"] is not None and (
        isinstance(raw_count, str) and len(re.findall(r"\d+", raw_count)) > 1  # "1 full + 1 open"
        or unit not in ("item", "items", "tub", "tubs", "box", "boxes", "pot", "pots", "base", "ml", "unit", "units"))
    it["count_unit"] = "item" if unit in ("item", "items", "tub", "tubs", "box", "boxes", "pot", "pots") else "base"
    it["sku"] = str(it["sku"]) if it.get("sku") else None
    it["evidence"] = str(it.get("evidence") or "")
    # A guess is never auto-confirmed: to_rows leaves ambiguous rows unticked for the merchant.
    amb = str(it.get("ambiguity") or "").strip()
    if amb.lower().strip(".") in ("none", "n/a", "na", "null", "no", "-", "clear"):
        amb = ""  # models write "none" for "no ambiguity"
    it["ambiguity"] = amb or ("model output unclear - check the count" if guessed else "")
    return it


def _parse_items(data: dict) -> list[Observation]:
    out = []
    items = data.get("items") or []
    for it in items if isinstance(items, list) else []:
        if isinstance(it, dict):
            out.append(Observation(**_clean(it)))
    return out


# ------------------------------------------------------------------ text path (LLM)
def rule_parse(text: str) -> list[Observation]:
    """Deterministic fallback: '2 x Matte Clay 100 ml, 35 neck strips'."""
    obs = []
    for part in re.split(r"[,\n;]+", text):
        part = part.strip()
        if not part:
            continue
        m = re.match(r"(\d+(?:\.\d+)?)\s*[x×]?\s*(.*)", part, re.I)
        # Counts other than sizes ("100 ml"): more than one means a phrase the rules can't read safely
        counts = re.findall(r"\b\d+(?:\.\d+)?\b(?!\s*(?:ml|g|l)\b)", part, re.I)
        amb = "no count found" if not m else ("several numbers - check the count" if len(counts) > 1 else "")
        obs.append(Observation(raw_label=part, count=float(m.group(1)) if m else None, count_unit="item",
                               evidence="rule parser", ambiguity=amb))
    return obs


def extract_text(text: str, products: dict[str, ProductSpec] = PRODUCTS) -> list[dict]:
    if llm.text_ready():
        try:
            data = llm.chat_json(f"You extract stock counts for a barbershop.\nCatalog:\n{_catalog(products)}\n{SCHEMA}",
                                 f"Stock notes:\n{text}")
            return to_rows(_parse_items(data), products, f"Nebius LLM {llm.text_model()}")
        except Exception as e:  # noqa: BLE001
            return to_rows(rule_parse(text), products, f"FALLBACK rule parser ({type(e).__name__})")
    return to_rows(rule_parse(text), products, "FALLBACK rule parser (no Nebius text model)")


# ------------------------------------------------------------------ photo path (VLM)
REPLAY = [  # labelled replay of the staged shelf photo, used when the VLM is not available
    Observation(raw_label="Northline Matte Clay 100ml x1 + 1 open (~20%)", sku="clay-matte-100ml", count=120,
                count_unit="base", evidence="replay of staged photo"),
    Observation(raw_label="Neck strips box (4 x 100)", sku="neck-strips", count=400, count_unit="base",
                evidence="replay of staged photo"),
]


def extract_photo(img, products: dict[str, ProductSpec] = PRODUCTS) -> list[dict]:
    """img: Streamlit UploadedFile, bytes, or None."""
    data = img.getvalue() if hasattr(img, "getvalue") else img
    mime = getattr(img, "type", None) or "image/png"
    if data and llm.vision_ready():
        prompt = (f"This is a barbershop stocktake photo (shelf or count sheet). Read visible product labels and counts.\n"
                  f"Catalog:\n{_catalog(products)}\n{SCHEMA}")
        try:
            # VLM rows are never pre-ticked: the merchant confirms each count read from a photo.
            return to_rows(_parse_items(llm.vision_json(prompt, data, mime)), products,
                           f"Nebius VLM {llm.vision_model()} - tick to confirm", auto_confirm=False)
        except Exception as e:  # noqa: BLE001
            return to_rows(REPLAY, products, f"REPLAY staged photo ({type(e).__name__})")
    return to_rows(REPLAY, products, "REPLAY staged photo (no Nebius vision model)")


def extract(kind: str, payload, products: dict[str, ProductSpec] = PRODUCTS) -> list[dict]:
    return extract_photo(payload, products) if route(kind) == "vlm" else extract_text(payload, products)
