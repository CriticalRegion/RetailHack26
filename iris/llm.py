"""Nebius Token Factory text and vision client (OpenAI-compatible). Bounded requests, no keys in logs."""
from __future__ import annotations

import base64
import json
import os
import re
from typing import Optional

DEFAULT_BASE = "https://api.tokenfactory.nebius.com/v1/"
TIMEOUT = 30.0


def _client(base_env: str):
    key = os.getenv("NEBIUS_API_KEY")
    if not key:
        return None
    from openai import OpenAI

    base = os.getenv(base_env) or os.getenv("NEBIUS_BASE_URL") or DEFAULT_BASE
    return OpenAI(api_key=key, base_url=base, timeout=TIMEOUT, max_retries=1)


def text_model() -> Optional[str]:
    return os.getenv("IRIS_TEXT_MODEL") or None


def vision_model() -> Optional[str]:
    return os.getenv("IRIS_VISION_MODEL") or None


def text_ready() -> bool:
    return bool(os.getenv("NEBIUS_API_KEY") and text_model())


def vision_ready() -> bool:
    return bool(os.getenv("NEBIUS_API_KEY") and vision_model())


def _parse_json(txt: str) -> dict:
    txt = (txt or "").strip()
    m = re.search(r"\{.*\}", txt, re.S)  # tolerate ```json fences or reasoning preambles
    return json.loads(m.group(0) if m else txt)


def chat_json(system: str, user: str, max_tokens: int = 800) -> dict:
    """Text LLM -> JSON object. Raises on missing config, timeout or bad JSON (callers fall back)."""
    client = _client("NEBIUS_BASE_URL")
    if client is None or not text_model():
        raise RuntimeError("Nebius text model not configured (NEBIUS_API_KEY, IRIS_TEXT_MODEL)")
    kw = dict(model=text_model(), temperature=0, max_tokens=max_tokens,
              messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
    try:
        r = client.chat.completions.create(response_format={"type": "json_object"}, **kw)
    except Exception:  # noqa: BLE001 - some models reject response_format; retry plain once
        r = client.chat.completions.create(**kw)
    return _parse_json(r.choices[0].message.content)


def vision_json(prompt: str, image: bytes, mime: str = "image/png", max_tokens: int = 800) -> dict:
    """VLM on one image -> JSON object. Raises on missing config, timeout or bad JSON (callers fall back)."""
    client = _client("IRIS_VISION_BASE_URL")
    if client is None or not vision_model():
        raise RuntimeError("Nebius vision model not configured (NEBIUS_API_KEY, IRIS_VISION_MODEL)")
    url = f"data:{mime};base64," + base64.b64encode(image).decode()
    r = client.chat.completions.create(
        model=vision_model(), temperature=0, max_tokens=max_tokens,
        messages=[{"role": "user", "content": [{"type": "text", "text": prompt},
                                               {"type": "image_url", "image_url": {"url": url}}]}])
    return _parse_json(r.choices[0].message.content)
