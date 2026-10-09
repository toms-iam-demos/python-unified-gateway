import json
import pytest
from fastapi.testclient import TestClient
from app import main
from app.domain import SCENARIOS, evaluate, money
from copy import deepcopy


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(main, "DB", tmp_path / "test.db")
    with TestClient(main.app, headers={"X-Demo-Token": main.TOKEN}) as c:
        yield c


def seed(c, count=4):
    r = c.post("/api/seed", json={"count": count})
    assert r.status_code == 200
    return r.json()


def ready(c, rid="MUN-00001"):
    r = c.get("/api/records/" + rid).json()
    b = {"version": r["version"], "evidence": {k: True for k in r["evidence"]}}
    if r["kind"] == "pricing":
        b["submitted_index"] = "1.08"
    if r["kind"] == "emergency":
        b.update(contact_hour=6, form_hour=20)
    res = c.put("/api/records/" + rid + "/review", json=b)
    assert res.status_code == 200, res.text
    assert res.json()["evaluation"]["ready"]
    return res.json()


def plan(c, rid="MUN-00001"):
    p = c.post("/api/plans", json={"record_id": rid})
    assert p.status_code == 200, p.text
    return p.json()


def test_auth_and_origin(client):
    assert client.get("/api/state", headers={"X-Demo-Token": ""}).status_code == 403
    assert (
        client.post(
            "/api/seed", json={"count": 4}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.get("/api/state", headers={"Sec-Fetch-Site": "cross-site"}).status_code
        == 403
    )
    assert client.get("/", headers={"Host": "evil.example"}).status_code == 400
    assert (
        client.get("/")
        .headers["content-security-policy"]
        .find("frame-ancestors 'none'")
        >= 0
    )


def test_pricing_and_gate(client):
    seed(client)
    r = client.get("/api/records/MUN-00001").json()
    assert r["evaluation"]["metrics"] == {
        "expected_cents": 13478400,
        "submitted_cents": 14102400,
        "variance_cents": 624000,
    }
    assert client.post("/api/plans", json={"record_id": r["id"]}).status_code == 409
    ready(client)
    p = plan(client)
    assert client.post("/api/plans/" + p["id"] + "/execute", json={}).status_code == 409
    assert money(101, "1", "1.005") == 102


def test_version_invalidates_approval(client):
    seed(client)
    r = ready(client)
    p = plan(client)
    assert client.post("/api/plans/" + p["id"] + "/approve").status_code == 200
    assert (
        client.put(
            "/api/records/" + r["id"] + "/review",
            json={"version": 1, "evidence": r["evidence"]},
        ).status_code
        == 409
    )
    assert (
        client.put(
            "/api/records/" + r["id"] + "/review",
            json={
                "version": r["version"],
                "evidence": r["evidence"],
                "submitted_index": "1.13",
            },
        ).status_code
        == 200
    )
    assert client.post("/api/plans/" + p["id"] + "/execute", json={}).status_code == 409
    assert client.get("/api/state").json()["delivered"] == 0


def test_replay_and_recovery(client):
    seed(client)
    ready(client)
    p = plan(client)
    url = "/api/plans/" + p["id"]
    client.post(url + "/approve")
    assert (
        client.post(url + "/execute", json={"lose_response": True}).json()["state"]
        == "unknown"
    )
    assert client.post(url + "/execute", json={}).json()["duplicate_suppressed"]
    assert client.post(url + "/reconcile").json()["state"] == "delivered"
    assert client.post(url + "/execute", json={}).json()["duplicate_suppressed"]
    data = client.get("/api/export").json()
    assert len(data["inbox"]) == 1
    assert (
        client.put(
            "/api/records/MUN-00001/review",
            json={"version": 2, "evidence": data["records"][0]["evidence"]},
        ).status_code
        == 409
    )


def test_emergency_clock_boundaries(client):
    seed(client)
    r = client.get("/api/records/MUN-00003").json()
    assert r["evaluation"]["metrics"]["form_hour"]["status"] == "overdue"
    r["inputs"].update(elapsed_hours=24, contact_hour=8, form_hour=24)
    e = evaluate(r)
    assert e["metrics"]["contact_hour"]["status"] == "recorded"
    assert e["metrics"]["form_hour"]["status"] == "recorded"
    r["inputs"]["form_hour"] = 25
    assert "cannot be in the future" in " ".join(evaluate(r)["blockers"])
    r["inputs"].update(elapsed_hours=26, contact_hour=9, form_hour=25)
    r["evidence"] = {k: True for k in r["evidence"]}
    e = evaluate(r)
    assert e["ready"]
    assert e["metrics"]["form_hour"]["status"] == "late"
    assert (
        len(e["warnings"]) == 3
    )  # escalate lateness; do not prevent recording an overdue packet


def test_invoice_and_renewal(client):
    seed(client)
    r = client.get("/api/records/MUN-00002").json()
    r["inputs"]["invoice_cents"] = 4800001
    assert "exceeds" in " ".join(evaluate(r)["blockers"])
    r = client.get("/api/records/MUN-00004").json()
    m = evaluate(r)["metrics"]
    assert m["notice_deadline"] == "2026-10-17"
    assert m["days_to_notice"] == 10


def test_input_scope_and_unknown_fields(client):
    seed(client)
    r = ready(client)
    b = {"version": r["version"], "evidence": r["evidence"], "notice_days": 90}
    assert client.put("/api/records/" + r["id"] + "/review", json=b).status_code == 422
    assert (
        client.post(
            "/api/seed", json={"count": 4, "url": "https://example.com"}
        ).status_code
        == 422
    )
    b.pop("notice_days")
    b["evidence"] = {"invented": True}
    assert client.put("/api/records/" + r["id"] + "/review", json=b).status_code == 422


def test_scoped_reset(client):
    seed(client)
    ready(client)
    p = plan(client)
    client.post("/api/plans/" + p["id"] + "/approve")
    client.post("/api/plans/" + p["id"] + "/execute", json={})
    m = client.get("/api/reset-manifest").json()
    b = {k: m[k] for k in ("cohort", "manifest_hash")}
    b["confirmation"] = "RESET other"
    assert client.post("/api/reset", json=b).status_code == 409
    b["confirmation"] = "RESET " + m["cohort"]
    b["manifest_hash"] = "bad"
    assert client.post("/api/reset", json=b).status_code == 409
    b["manifest_hash"] = m["manifest_hash"]
    assert client.post("/api/reset", json=b).json()["removed"] == 4
    d = client.get("/api/export").json()
    assert not d["records"] and not d["plans"] and not d["inbox"]
    assert d["audit"]


def test_10000_pagination_and_reproducibility(client):
    seed(client, 10000)
    s = client.get("/api/state?page=834").json()
    assert len(s["records"]) == 4
    assert s["count"] == 10000
    assert client.get("/api/state?q=MUN-10000").json()["filtered"] == 1
    assert client.get("/api/state?kind=pricing").json()["filtered"] == 2500
    assert client.get("/api/state?q=%25").json()["filtered"] == 0
    assert len(client.get("/api/export").json()["records"]) == 10000
    assert client.post("/api/seed", json={"count": 4}).status_code == 409


def test_all_scenarios_end_to_end(client):
    seed(client)
    for i in range(1, 5):
        rid = f"MUN-{i:05}"
        ready(client, rid)
        p = plan(client, rid)
        u = "/api/plans/" + p["id"]
        assert client.post(u + "/approve").status_code == 200
        assert client.post(u + "/execute", json={}).json()["state"] == "delivered"
    assert client.get("/api/state").json()["delivered"] == 4


def test_record_retains_own_plan_beyond_dashboard_limit(client):
    seed(client, 104)
    for i in range(1, 105):
        rid = f"MUN-{i:05}"
        ready(client, rid)
        plan(client, rid)
    assert len(client.get("/api/state").json()["plans"]) == 100
    first = client.get("/api/records/MUN-00001").json()
    assert len(first["plans"]) == 1 and first["plans"][0]["state"] == "prepared"


def test_scenario_sources_resolve_to_synthetic_assumptions(client):
    catalog = client.get('/api/catalog').json()
    sources = {item['id']: item for item in catalog['sources']}
    for scenario in SCENARIOS.values():
        assert sources[scenario['source']]['classification'] == 'Synthetic design assumption'
