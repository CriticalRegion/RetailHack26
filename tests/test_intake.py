from iris import intake
from iris.intake import Observation, to_rows, extract_text, extract_photo, route


def test_route():
    assert route("photo") == "vlm" and route("text") == "llm"


def test_text_fallback_converts_items_to_ml(monkeypatch):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    rows = {r["sku"]: r for r in extract_text("2 x Northline Matte Clay 100 ml, 35 neck strips")}
    assert rows["CLAY-MATTE-100"]["quantity"] == 200 and rows["CLAY-MATTE-100"]["confirm"]
    assert rows["NECK-STRIP"]["quantity"] == 35
    assert "FALLBACK" in rows["NECK-STRIP"]["note"]


def test_unknown_and_unreadable_rows_are_not_confirmed():
    rows = to_rows([Observation(raw_label="mystery pomade", count=3),
                    Observation(raw_label="matte clay", count=None, ambiguity="blurry")], intake.PRODUCTS, "t")
    assert rows[0]["sku"] == "?" and not rows[0]["confirm"]
    assert rows[1]["sku"] == "CLAY-MATTE-100" and rows[1]["quantity"] is None and not rows[1]["confirm"]


def test_model_sku_outside_catalog_is_rematched():
    rows = to_rows([Observation(raw_label="Northline matte clay", sku="CLAY-XL", count=1)], intake.PRODUCTS, "t")
    assert rows[0]["sku"] == "CLAY-MATTE-100" and rows[0]["quantity"] == 100


def test_photo_replay_without_vision(monkeypatch):
    monkeypatch.delenv("IRIS_VISION_MODEL", raising=False)
    rows = extract_photo(b"fake")
    assert rows[0]["quantity"] == 120 and "REPLAY" in rows[0]["note"]


def test_llm_path_uses_model_json(monkeypatch):
    monkeypatch.setattr(intake.llm, "text_ready", lambda: True)
    monkeypatch.setattr(intake.llm, "text_model", lambda: "m")
    monkeypatch.setattr(intake.llm, "chat_json", lambda s, u: {"items": [
        {"raw_label": "2 tubs clay", "sku": "CLAY-MATTE-100", "count": 2, "count_unit": "item"}]})
    assert extract_text("whatever")[0]["quantity"] == 200
