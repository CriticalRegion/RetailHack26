from fastapi.testclient import TestClient

import server


def test_demo_path_through_api():
    c = TestClient(server.app)
    s = c.post("/api/reset").json()
    assert s["step"] == "forecast" and s["proposal"] is None
    s = c.post("/api/stock/confirm", json={"rows": [{"sku": "clay-matte-100ml", "quantity": 120, "confirm": True}]}).json()
    assert s["kpis"]["bookings_at_risk"] > 0 and s["kpis"]["first_run_out"]["id"]
    s = c.post("/api/run").json()
    r1 = s["proposal"]
    assert r1["status"] == "proposed" and r1["lines"] and s["offers"]
    s = c.post("/api/reject", json={"revision": r1["revision"], "feedback": "not BarberHub"}).json()
    r2 = s["proposal"]
    assert r2["revision"] == r1["revision"] + 1 and s["kpis"]["orders"] == 0
    assert r2["lines"][0]["supplier"] != r1["lines"][0]["supplier"]
    s = c.post("/api/approve", json={"revision": r2["revision"]}).json()
    assert s["kpis"]["orders"] == 1 and s["step"] == "order" and s["kpis"]["bookings_protected"] > 0
    s = c.post("/api/approve", json={"revision": r2["revision"]}).json()
    assert s["kpis"]["orders"] == 1 and "already exists" in s["flash"]["msg"]


def test_stale_reject_is_409():
    c = TestClient(server.app)
    c.post("/api/reset")
    c.post("/api/run")
    c.post("/api/reject", json={"revision": 1, "feedback": "x"})
    assert c.post("/api/reject", json={"revision": 1, "feedback": "x"}).status_code == 409
