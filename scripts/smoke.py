"""Smoke test: Nebius text, Nebius vision and Tavily. Prints OK/FAIL per service, never prints keys.

Run: python scripts/smoke.py          (reads .env from the repo root)
"""
import base64
import io
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DEFAULT_BASE = "https://api.tokenfactory.nebius.com/v1/"
TIMEOUT = 45
results: dict[str, str] = {}


def report(name: str, ok: bool, detail: str) -> None:
    results[name] = "OK" if ok else "FAIL"
    print(f"[{'OK  ' if ok else 'FAIL'}] {name}: {detail}")


def nebius_client(base_env: str = "NEBIUS_BASE_URL"):
    from openai import OpenAI

    key = os.getenv("NEBIUS_API_KEY")
    if not key:
        return None
    base = os.getenv(base_env) or os.getenv("NEBIUS_BASE_URL") or DEFAULT_BASE
    return OpenAI(base_url=base, api_key=key, timeout=TIMEOUT, max_retries=1)


def pick(ids: list[str], env: str, hints: list[str]) -> str | None:
    if os.getenv(env):
        return os.getenv(env)
    for h in hints:
        for i in ids:
            if h.lower() in i.lower():
                return i
    return None


def make_stock_image() -> str:
    from PIL import Image, ImageDraw

    img = Image.new("RGB", (480, 160), "white")
    d = ImageDraw.Draw(img)
    d.text((20, 30), "STOCK COUNT", fill="black")
    d.text((20, 70), "Matte Clay 100ml  x 2", fill="black")
    d.text((20, 105), "Neck strips  x 35", fill="black")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def main() -> int:
    client = nebius_client()
    ids: list[str] = []
    if client is None:
        report("nebius:models", False, "NEBIUS_API_KEY not set in .env")
    else:
        try:
            ids = sorted(m.id for m in client.models.list().data)
            nem = [i for i in ids if "nemotron" in i.lower()]
            vis = [i for i in ids if any(h in i.lower() for h in ("vl", "vision", "gemma-3", "llava", "pixtral"))]
            report("nebius:models", True, f"{len(ids)} models; nemotron={nem[:4]}; vision-ish={vis[:6]}")
        except Exception as e:  # noqa: BLE001
            report("nebius:models", False, f"{type(e).__name__}: {str(e)[:160]}")

    text_model = pick(ids, "IRIS_TEXT_MODEL", ["nemotron", "llama-3.3-70b", "qwen"])
    if client and text_model:
        try:
            r = client.chat.completions.create(
                model=text_model,
                messages=[
                    {"role": "system", "content": "Return only JSON."},
                    {"role": "user", "content": 'Parse into {"items":[{"label":str,"qty":number,"unit":str}]}: "2 x Brand X Matte Clay 100 ml, 35 neck strips"'},
                ],
                response_format={"type": "json_object"},
                max_tokens=300,
                temperature=0,
            )
            out = json.loads(r.choices[0].message.content)
            report("nebius:text", "items" in out, f"{text_model} -> {json.dumps(out)[:160]}")
        except Exception as e:  # noqa: BLE001
            report("nebius:text", False, f"{text_model}: {type(e).__name__}: {str(e)[:160]}")
    elif client:
        report("nebius:text", False, "no text model found; set IRIS_TEXT_MODEL")

    vclient = nebius_client("IRIS_VISION_BASE_URL") if client else None
    vision_model = pick(ids, "IRIS_VISION_MODEL", ["qwen2.5-vl", "vl-", "-vl", "vision", "gemma-3"])
    if vclient and vision_model:
        try:
            r = vclient.chat.completions.create(
                model=vision_model,
                messages=[{"role": "user", "content": [
                    {"type": "text", "text": "List each product and count you can read in this image, one per line."},
                    {"type": "image_url", "image_url": {"url": make_stock_image()}},
                ]}],
                max_tokens=200,
                temperature=0,
            )
            txt = (r.choices[0].message.content or "").strip()
            report("nebius:vision", "clay" in txt.lower(), f"{vision_model} -> {txt[:160]!r}")
        except Exception as e:  # noqa: BLE001
            report("nebius:vision", False, f"{vision_model}: {type(e).__name__}: {str(e)[:160]}")
    elif client:
        report("nebius:vision", False, "no vision model found; set IRIS_VISION_MODEL")

    tkey = os.getenv("TAVILY_API_KEY")
    if not tkey:
        report("tavily", False, "TAVILY_API_KEY not set in .env")
    else:
        try:
            from tavily import TavilyClient

            r = TavilyClient(api_key=tkey).search("matte clay 100ml barber supplier UK price", max_results=3)
            hits = r.get("results", [])
            report("tavily", bool(hits), f"{len(hits)} results; first={hits[0]['url'] if hits else None}")
        except Exception as e:  # noqa: BLE001
            report("tavily", False, f"{type(e).__name__}: {str(e)[:160]}")

    print("SUMMARY", json.dumps(results))
    return 0 if results and all(v == "OK" for v in results.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
