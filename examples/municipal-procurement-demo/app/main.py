"""Local demonstration with no outbound client, provider credentials, or production connector."""
from app.security import RequestSizeLimit

import json, os, secrets, sqlite3, uuid, hashlib
from pathlib import Path
from contextlib import contextmanager
from datetime import datetime, timezone
from copy import deepcopy
from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, ConfigDict
from .domain import SCENARIOS, EVIDENCE, evaluate

ROOT = Path(__file__).resolve().parent.parent
DB = Path(os.environ.get("PUG_MUNICIPAL_DB", str(ROOT / "data" / "municipal.db")))
TOKEN = secrets.token_urlsafe(32)
app = FastAPI(
    title="PUG | Municipal procurement demonstration",
    version="1.0.0",
    description="Synthetic local records. Simulated downstream inbox; no SAP, docusign, email, payments or production access. Local reviewer persona is not enterprise authentication.",
)
app.add_middleware(
    TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost", "testserver"]
)
app.add_middleware(RequestSizeLimit)
app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")
app.mount("/docs-assets", StaticFiles(directory=ROOT / "docs"), name="docs-assets")
key_header = APIKeyHeader(name="X-Demo-Token", auto_error=False)


def authorized(key=Depends(key_header)):
    if not key or not secrets.compare_digest(key, TOKEN):
        raise HTTPException(403, "Local session token required; copy it from API lab.")


AUTH = [Depends(authorized)]


@app.middleware("http")
async def boundary(request: Request, call_next):
    if request.url.path.startswith("/api/"):
        origin = request.headers.get("origin")
        if (
            origin and origin != str(request.base_url).rstrip("/")
        ) or request.headers.get("sec-fetch-site") == "cross-site":
            return JSONResponse({"detail": "Foreign origin rejected"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        if request.url.path != "/docs"
        else "frame-ancestors 'none'"
    )
    return response


@contextmanager
def db():
    DB.parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB, timeout=20)
    c.row_factory = sqlite3.Row
    try:
        c.executescript(
            "CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY,cohort TEXT,kind TEXT,version INTEGER,status TEXT,payload TEXT); CREATE TABLE IF NOT EXISTS plans(id TEXT PRIMARY KEY,record_id TEXT,version INTEGER,state TEXT,payload TEXT,digest TEXT); CREATE TABLE IF NOT EXISTS inbox(command_id TEXT PRIMARY KEY,payload TEXT,digest TEXT,received_at TEXT); CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY AUTOINCREMENT,time TEXT,subject TEXT,event TEXT);"
        )
        c.execute("BEGIN IMMEDIATE")
        yield c
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()


def stamp():
    return datetime.now(timezone.utc).isoformat()


def audit(c, subject, event):
    c.execute(
        "INSERT INTO audit(time,subject,event) VALUES(?,?,?)", (stamp(), subject, event)
    )


def fetch(c, table, key):
    r = c.execute(f"SELECT * FROM {table} WHERE id=?", (key,)).fetchone()
    if not r:
        raise HTTPException(404, "Record or plan not found")
    d = dict(r)
    if table == "records":
        d = {**json.loads(d.pop("payload")), **d}
    return d


def digest(s):
    return hashlib.sha256(s.encode()).hexdigest()


def enrich(r):
    return {**r, "evaluation": evaluate(r)}


@app.get("/", response_class=HTMLResponse)
def home():
    return (ROOT / "app/static/index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "mode": "synthetic_local",
        "external_calls": 0,
        "schema_version": "1.0",
    }


@app.get("/api/catalog", dependencies=AUTH)
def catalog():
    return {
        "scenarios": SCENARIOS,
        "evidence_labels": EVIDENCE,
        "sources": json.loads((ROOT / "docs/sources.json").read_text(encoding="utf-8")),
    }


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Seed(Strict):
    count: int = Field(default=12, ge=4, le=10000)


@app.post("/api/seed", dependencies=AUTH)
def seed(body: Seed):
    with db() as c:
        if c.execute("SELECT count(*) FROM records").fetchone()[0]:
            raise HTTPException(409, "Export and reset the current cohort first")
        cohort = "MUN-DEMO-" + uuid.uuid4().hex[:8]
        for i in range(body.count):
            kind = list(SCENARIOS)[i % 4]
            data = deepcopy(SCENARIOS[kind])
            data.update(
                {
                    "supplier": "Civic Demo Services " + str(1 + i % 17),
                    "synthetic": True,
                    "policy_review": "required before real use",
                    "fixture_revision": "municipal-v1",
                }
            )
            c.execute(
                "INSERT INTO records VALUES(?,?,?,?,?,?)",
                (f"MUN-{i + 1:05}", cohort, kind, 1, "review", json.dumps(data)),
            )
        audit(
            c,
            cohort,
            f"Seeded {body.count} deterministic synthetic fixtures; no external requests",
        )
        return {"cohort": cohort, "count": body.count}


@app.get("/api/state", dependencies=AUTH)
def state(q: str = "", kind: str = "", page: int = 1):
    if page < 1 or len(q) > 100 or kind not in ["", *SCENARIOS]:
        raise HTTPException(422, "Invalid filter")
    with db() as c:
        # Search literal text; wildcard characters are escaped.
        term = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        where = "WHERE (?='' OR kind=?) AND (id LIKE ? ESCAPE '\\' OR payload LIKE ? ESCAPE '\\')"
        params = (kind, kind, "%" + term + "%", "%" + term + "%")
        total = c.execute("SELECT count(*) FROM records").fetchone()[0]
        filtered = c.execute(
            "SELECT count(*) FROM records " + where, params
        ).fetchone()[0]
        rows = c.execute(
            "SELECT id FROM records " + where + " ORDER BY id LIMIT 12 OFFSET ?",
            (*params, (page - 1) * 12),
        ).fetchall()
        co = c.execute("SELECT cohort FROM records LIMIT 1").fetchone()
        return {
            "count": total,
            "filtered": filtered,
            "page": page,
            "pages": max(1, (filtered + 11) // 12),
            "cohort": co[0] if co else None,
            "records": [enrich(fetch(c, "records", r[0])) for r in rows],
            "plans": [
                dict(r)
                for r in c.execute("SELECT * FROM plans ORDER BY rowid DESC LIMIT 100")
            ],
            "audit": [
                dict(r)
                for r in c.execute("SELECT * FROM audit ORDER BY seq DESC LIMIT 30")
            ],
            "delivered": c.execute("SELECT count(*) FROM inbox").fetchone()[0],
            "external_calls": 0,
        }


@app.get("/api/records/{rid}", dependencies=AUTH)
def record(rid: str):
    with db() as c:
        r = enrich(fetch(c, "records", rid))
        r["plans"] = [
            dict(p)
            for p in c.execute(
                "SELECT * FROM plans WHERE record_id=? ORDER BY rowid DESC", (rid,)
            )
        ]
        return r


class Review(Strict):
    version: int = Field(ge=1)
    evidence: dict[str, bool]
    submitted_index: str | None = Field(default=None, pattern=r"^\d{1,2}(\.\d{1,4})?$")
    invoice_cents: int | None = Field(default=None, ge=1, le=1000000000)
    elapsed_hours: int | None = Field(default=None, ge=0, le=168)
    contact_hour: int | None = Field(default=None, ge=0, le=168)
    form_hour: int | None = Field(default=None, ge=0, le=168)
    notice_days: int | None = Field(default=None, ge=0, le=365)


@app.put("/api/records/{rid}/review", dependencies=AUTH)
def review(rid: str, b: Review):
    with db() as c:
        r = fetch(c, "records", rid)
        if r["version"] != b.version:
            raise HTTPException(409, "Version changed; reload record")
        if r["status"] in ("delivered", "unknown"):
            raise HTTPException(
                409, "Delivered fixture is immutable; reset cohort to repeat"
            )
        if set(b.evidence) != set(r["evidence"]):
            raise HTTPException(422, "Evidence keys must match this scenario")
        allowed = {
            "pricing": {"submitted_index"},
            "invoice": {"invoice_cents"},
            "emergency": {"elapsed_hours", "contact_hour", "form_hour"},
            "renewal": {"notice_days"},
        }[r["kind"]]
        submitted = b.model_fields_set - {"version", "evidence"}
        if not submitted <= allowed:
            raise HTTPException(422, "Inputs do not belong to this scenario")
        for k in submitted:
            v = getattr(b, k)
            if v is None and k not in ("contact_hour", "form_hour"):
                raise HTTPException(422, "Required input cannot be null")
            r["inputs"][k] = v
        r["evidence"] = b.evidence
        payload = {
            k: v
            for k, v in r.items()
            if k not in ("id", "cohort", "kind", "version", "status")
        }
        c.execute(
            "UPDATE records SET payload=?,version=version+1 WHERE id=?",
            (json.dumps(payload), rid),
        )
        c.execute(
            "UPDATE plans SET state='stale' WHERE record_id=? AND state IN ('prepared','approved')",
            (rid,),
        )
        audit(c, rid, "Saved simulated reviewer evidence; invalidated prior approvals")
        return enrich(fetch(c, "records", rid))


class Plan(Strict):
    record_id: str


@app.post("/api/plans", dependencies=AUTH)
def prepare(b: Plan):
    with db() as c:
        r = fetch(c, "records", b.record_id)
        result = evaluate(r)
        if r["status"] in ("delivered", "unknown"):
            raise HTTPException(
                409, "Already delivered; reconcile or replay its command"
            )
        if not result["ready"]:
            raise HTTPException(
                409,
                {
                    "message": "Evidence or arithmetic blockers remain",
                    "blockers": result["blockers"],
                },
            )
        if c.execute(
            "SELECT 1 FROM plans WHERE record_id=? AND state IN ('prepared','approved')",
            (r["id"],),
        ).fetchone():
            raise HTTPException(409, "Existing plan requires action")
        pid = "CMD-" + uuid.uuid4().hex[:12]
        payload = json.dumps(
            {
                "schema_version": "1.0",
                "command_id": pid,
                "source_record_id": r["id"],
                "cohort": r["cohort"],
                "expected_version": r["version"],
                "operation": r["operation"],
                "destination": "local_procurement_inbox",
                "evidence": r["evidence"],
                "inputs": r["inputs"],
                "evaluation": result,
                "synthetic": True,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        c.execute(
            "INSERT INTO plans VALUES(?,?,?,?,?,?)",
            (pid, r["id"], r["version"], "prepared", payload, digest(payload)),
        )
        audit(c, r["id"], "Prepared immutable command " + pid)
        return fetch(c, "plans", pid)


@app.post("/api/plans/{pid}/approve", dependencies=AUTH)
def approve(pid: str):
    with db() as c:
        p = fetch(c, "plans", pid)
        r = fetch(c, "records", p["record_id"])
        if p["state"] != "prepared" or p["version"] != r["version"]:
            raise HTTPException(409, "Prepared current-version plan required")
        c.execute("UPDATE plans SET state='approved' WHERE id=?", (pid,))
        audit(
            c,
            r["id"],
            "Demo reviewer approved " + pid + "; persona is not an identity boundary",
        )
        return fetch(c, "plans", pid)


class Execute(Strict):
    lose_response: bool = False


@app.post("/api/plans/{pid}/execute", dependencies=AUTH)
def execute(pid: str, b: Execute):
    with db() as c:
        p = fetch(c, "plans", pid)
        r = fetch(c, "records", p["record_id"])
        prior = c.execute("SELECT * FROM inbox WHERE command_id=?", (pid,)).fetchone()
        if prior:
            if prior["digest"] != p["digest"]:
                raise HTTPException(
                    409, "Receipt digest mismatch; stop for investigation"
                )
            audit(c, r["id"], "Replay suppressed for " + pid)
            return {**p, "duplicate_suppressed": True}
        if p["state"] != "approved" or r["version"] != p["version"]:
            raise HTTPException(409, "Current reviewed approval required")
        if digest(p["payload"]) != p["digest"]:
            raise HTTPException(409, "Payload digest mismatch")
        c.execute(
            "INSERT INTO inbox VALUES(?,?,?,?)",
            (pid, p["payload"], p["digest"], stamp()),
        )
        target = "unknown" if b.lose_response else "delivered"
        c.execute("UPDATE plans SET state=? WHERE id=?", (target, pid))
        c.execute("UPDATE records SET status=? WHERE id=?", (target, r["id"]))
        audit(
            c,
            r["id"],
            "Inbox accepted "
            + pid
            + "; "
            + (
                "response-loss simulation requires reconciliation"
                if b.lose_response
                else "receipt verified"
            ),
        )
        return fetch(c, "plans", pid)


@app.post("/api/plans/{pid}/reconcile", dependencies=AUTH)
def reconcile(pid: str):
    with db() as c:
        p = fetch(c, "plans", pid)
        receipt = c.execute("SELECT * FROM inbox WHERE command_id=?", (pid,)).fetchone()
        if p["state"] != "unknown" or not receipt or receipt["digest"] != p["digest"]:
            raise HTTPException(409, "No matching unknown receipt")
        c.execute("UPDATE plans SET state='delivered' WHERE id=?", (pid,))
        c.execute("UPDATE records SET status='delivered' WHERE id=?", (p["record_id"],))
        audit(
            c,
            p["record_id"],
            "Reconciled existing receipt " + pid + " without a second insertion",
        )
        return fetch(c, "plans", pid)


@app.get("/api/export", dependencies=AUTH)
def export():
    with db() as c:
        return {
            "schema_version": "1.0",
            "mode": "synthetic_local",
            "external_calls": 0,
            "records": [
                fetch(c, "records", r[0]) for r in c.execute("SELECT id FROM records")
            ],
            "plans": [dict(r) for r in c.execute("SELECT * FROM plans")],
            "inbox": [dict(r) for r in c.execute("SELECT * FROM inbox")],
            "audit": [dict(r) for r in c.execute("SELECT * FROM audit")],
        }


@app.get("/api/reset-manifest", dependencies=AUTH)
def manifest():
    with db() as c:
        ids = [r[0] for r in c.execute("SELECT id FROM records ORDER BY id")]
        co = c.execute("SELECT cohort FROM records LIMIT 1").fetchone()
        return {
            "cohort": co[0] if co else None,
            "record_count": len(ids),
            "record_ids": ids,
            "manifest_hash": digest(json.dumps(ids)),
            "audit_retained": True,
            "scope": "local owned cohort only",
        }


class Reset(Strict):
    cohort: str
    manifest_hash: str
    confirmation: str


@app.post("/api/reset", dependencies=AUTH)
def reset(b: Reset):
    with db() as c:
        ids = [
            r[0]
            for r in c.execute(
                "SELECT id FROM records WHERE cohort=? ORDER BY id", (b.cohort,)
            )
        ]
        if not ids or not b.cohort.startswith("MUN-DEMO-"):
            raise HTTPException(404, "Owned cohort not found")
        if b.confirmation != "RESET " + b.cohort or b.manifest_hash != digest(
            json.dumps(ids)
        ):
            raise HTTPException(
                409, "Exact manifest and typed cohort confirmation required"
            )
        c.execute(
            "DELETE FROM inbox WHERE command_id IN (SELECT id FROM plans WHERE record_id IN (SELECT id FROM records WHERE cohort=?))",
            (b.cohort,),
        )
        c.execute(
            "DELETE FROM plans WHERE record_id IN (SELECT id FROM records WHERE cohort=?)",
            (b.cohort,),
        )
        c.execute("DELETE FROM records WHERE cohort=?", (b.cohort,))
        audit(c, b.cohort, f"Reset {len(ids)} local owned fixtures; audit retained")
        return {"removed": len(ids), "external_calls": 0}
