"""
Testes do fluxo de upload de video pelo atleta + fila de analise do treinador.
A analise pesada (pose) e stubada; aqui validamos o plumbing (criar, listar,
disparar, concluir, apagar) e o gate.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _client():
    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "t.sqlite")
    con = sqlite3.connect(dbp)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.commit(); con.close()
    os.environ["MDLUCCA_DB"] = dbp
    os.environ["MDLUCCA_DEV"] = "1"
    for m in list(sys.modules):
        if m.startswith("app."):
            del sys.modules[m]
    from fastapi.testclient import TestClient
    from app.api import app
    return TestClient(app)


def test_upload_queue_and_analyze(monkeypatch):
    c = _client()
    a = c.post("/athletes", json={"name": "Ze", "body_mass_kg": 80, "height_m": 1.8}).json()
    aid = a["id"]

    # atleta envia o video
    r = c.post(f"/athletes/{aid}/uploads",
               files={"file": ("v.mp4", b"fake-bytes", "video/mp4")},
               data={"exercise": "Agacho", "load_kg": "100"})
    assert r.status_code == 200
    up = r.json()
    assert up["status"] == "queued" and up["athlete_id"] == aid
    uid = up["id"]

    assert any(u["id"] == uid for u in c.get("/uploads").json())
    assert c.get(f"/athletes/{aid}/uploads").json()[0]["id"] == uid
    assert c.get(f"/uploads/{uid}").json()["status"] == "queued"

    # treinador dispara: worker stubado + thread sincrona
    import app.api as api

    def fake_worker(u):
        con = api.db.connect_rw()
        con.execute("UPDATE upload SET status='done', session_id=999 WHERE id=?", (u,))
        con.commit(); con.close()

    class FakeThread:
        def __init__(self, target=None, args=(), daemon=None):
            self._t, self._a = target, args

        def start(self):
            self._t(*self._a)

    monkeypatch.setattr(api, "_pose_model", lambda: "modelo.task")
    monkeypatch.setattr(api, "_analyze_worker", fake_worker)
    monkeypatch.setattr(api.threading, "Thread", FakeThread)

    resp = c.post(f"/uploads/{uid}/analyze")
    assert resp.status_code == 200 and resp.json()["status"] == "processing"
    done = c.get(f"/uploads/{uid}").json()
    assert done["status"] == "done" and done["session_id"] == 999

    assert c.post(f"/uploads/{uid}/delete").status_code == 200
    assert c.get(f"/uploads/{uid}").status_code == 404


def test_analyze_without_model_503(monkeypatch):
    c = _client()
    a = c.post("/athletes", json={"name": "Ana", "body_mass_kg": 60}).json()
    up = c.post(f"/athletes/{a['id']}/uploads",
                files={"file": ("v.mp4", b"x", "video/mp4")}).json()
    import app.api as api
    monkeypatch.setattr(api, "_pose_model", lambda: None)      # sem modelo no servidor
    assert c.post(f"/uploads/{up['id']}/analyze").status_code == 503


def test_upload_unknown_athlete_404():
    c = _client()
    r = c.post("/athletes/9999/uploads",
               files={"file": ("v.mp4", b"x", "video/mp4")})
    assert r.status_code == 404


if __name__ == "__main__":
    print("rode com pytest")
