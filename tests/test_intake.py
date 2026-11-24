from iris import intake
from iris.intake import Observation, to_rows, extract_text, extract_photo, route


def test_route():
    assert route("photo") == "vlm" and route("text") == "llm"


def test_text_fallback_converts_items_to_ml(monkeypatch):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    rows = {r["sku"]: r for r in extract_text("2 x Northline Matte Clay 100 ml, 35 neck strips")}
    assert rows["clay-matte-100ml"]["quantity"] == 200 and rows["clay-matte-100ml"]["confirm"]
    assert rows["neck-strips"]["quantity"] == 35
    assert "FALLBACK" in rows["neck-strips"]["note"]


def test_unknown_and_unreadable_rows_are_not_confirmed():
    rows = to_rows([Observation(raw_label="mystery pomade", count=3),
                    Observation(raw_label="matte clay", count=None, ambiguity="blurry")], intake.PRODUCTS, "t")
    assert rows[0]["sku"] == "?" and not rows[0]["confirm"]
    assert rows[1]["sku"] == "clay-matte-100ml" and rows[1]["quantity"] is None and not rows[1]["confirm"]


def test_model_sku_outside_catalog_is_rematched():
    rows = to_rows([Observation(raw_label="Northline matte clay", sku="CLAY-XL", count=1)], intake.PRODUCTS, "t")
    assert rows[0]["sku"] == "clay-matte-100ml" and rows[0]["quantity"] == 100


def test_photo_replay_without_vision(monkeypatch):
    monkeypatch.delenv("IRIS_VISION_MODEL", raising=False)
    rows = extract_photo(b"fake")
    assert rows[0]["quantity"] == 120 and "REPLAY" in rows[0]["note"]


def test_llm_path_uses_model_json(monkeypatch):
    monkeypatch.setattr(intake.llm, "text_ready", lambda: True)
    monkeypatch.setattr(intake.llm, "text_model", lambda: "m")
    monkeypatch.setattr(intake.llm, "chat_json", lambda s, u: {"items": [
        {"raw_label": "2 tubs clay", "sku": "clay-matte-100ml", "count": 2, "count_unit": "item"}]})
    assert extract_text("whatever")[0]["quantity"] == 200


def test_lenient_parse_of_drifting_model_json():
    obs = intake._parse_items({"items": [
        {"raw_label": "Northline Matte Clay", "sku": "clay-matte-100ml", "count": "120 ml", "count_unit": "ml"},
        {"raw_label": "Neck strips", "count": "400", "count_unit": "strips", "extra": 1}]})
    rows = to_rows(obs, intake.PRODUCTS, "t")
    assert [r["quantity"] for r in rows] == [120, 400]


def test_guessed_counts_are_never_auto_confirmed(monkeypatch):
    monkeypatch.setattr(intake.llm, "text_ready", lambda: True)
    monkeypatch.setattr(intake.llm, "text_model", lambda: "m")
    monkeypatch.setattr(intake.llm, "chat_json", lambda s, u: {"items": [
        {"raw_label": "2 tubs clay", "sku": "clay-matte-100ml", "count": 2},                     # no unit
        {"raw_label": "clay", "sku": "clay-matte-100ml", "count": "1 full + 1 open"},           # two numbers
        {"raw_label": "neck strips", "sku": "neck-strips", "count": 400, "count_unit": "base"}]})  # clean
    rows = extract_text("whatever")
    assert [r["confirm"] for r in rows] == [False, False, True]


def test_rule_fallback_does_not_tick_complex_phrases(monkeypatch):
    monkeypatch.delenv("NEBIUS_API_KEY", raising=False)
    rows = extract_text("1 full Northline matte clay 100ml + 1 open about 20% left, 4 boxes of 100 neck strips, 380 neck strips")
    assert [r["confirm"] for r in rows] == [False, False, True]


def test_model_none_ambiguity_is_clear():
    obs = intake._parse_items({"items": [{"raw_label": "clay", "sku": "clay-matte-100ml", "count": 120,
                                          "count_unit": "base", "ambiguity": "none"}]})
    assert to_rows(obs, intake.PRODUCTS, "t")[0]["confirm"]
