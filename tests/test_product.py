"""
Testes da camada de produto: cadastro de alunos, sessao manual e link
compartilhavel (relatorio HTML). Usa um banco temporario isolado.
"""
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _fresh_db(path):
    """Cria um banco minimo com schema + 1 aluno + 1 sessao + 1 submov + metrica."""
    con = sqlite3.connect(path)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.execute("INSERT INTO athlete (id,name,body_mass_kg,height_m,bmi) "
                "VALUES (1,'Teste',80,1.8,24.7)")
    con.execute("INSERT INTO session (id,athlete_id,exercise,gravity,pose_source,"
                "n_submovements) VALUES (1,1,'Agacho',9.81,'manual',1)")
    con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,"
                "n_frames,dt,is_slowmo_2x) VALUES (1,1,1,'Rep 1','pull',100,0.02,0)")
    con.execute("INSERT INTO metric (submovement_id,session_id,analysis,name,"
                "value_num,unit) VALUES (1,1,'peaks','power_peak',1234.5,'W')")
    con.commit(); con.close()


def _client():
    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "t.sqlite")
    _fresh_db(dbp)
    os.environ["MDLUCCA_DB"] = dbp
    # importa a API depois de definir o banco
    for m in list(sys.modules):
        if m.startswith("app."):
            del sys.modules[m]
    from fastapi.testclient import TestClient
    from app.api import app
    return TestClient(app)


def test_create_athlete_computes_bmi():
    c = _client()
    r = c.post("/athletes", json={"name": "Joao", "body_mass_kg": 80, "height_m": 2.0})
    assert r.status_code == 200
    assert r.json()["bmi"] == 20.0  # 80/(2^2)


def test_create_session_and_pct():
    c = _client()
    r = c.post("/sessions", json={"athlete_id": 1, "exercise": "Supino", "load_kg": 40})
    assert r.status_code == 200
    assert r.json()["pct_bodyweight"] == 50.0  # 40/80


def test_share_and_report():
    c = _client()
    sh = c.post("/shares", json={"kind": "session", "ref_id": 1, "audience": "ambos"})
    assert sh.status_code == 200
    tok = sh.json()["token"]
    rep = c.get(f"/r/{tok}")
    assert rep.status_code == 200
    body = rep.text
    assert "Teste" in body and "1234" in body  # nome do aluno + potencia pico
    # contador de views incrementa
    assert any(s["views"] >= 1 for s in c.get("/shares").json())


def test_bad_share_ref():
    c = _client()
    r = c.post("/shares", json={"kind": "session", "ref_id": 999})
    assert r.status_code == 404


def test_demo_seed_endpoint():
    c = _client()
    r = c.post("/demo/seed", json={"athletes": 3, "reps": 4, "reset": True})
    assert r.status_code == 200
    d = r.json()
    assert d["created"] == 3
    # cada sessao veio com link absoluto de relatorio, que renderiza
    url = d["sessions"][0]["report_url"]
    assert "/r/" in url
    rep = c.get("/r/" + url.split("/r/")[1])
    assert rep.status_code == 200 and "<rect" in rep.text
    # segundo seed com reset remove os 3 anteriores
    r2 = c.post("/demo/seed", json={"athletes": 2, "reps": 3, "reset": True})
    assert r2.json()["removed"] == 3 and r2.json()["created"] == 2


def test_seed_massa_de_teste_and_reports():
    """Gera massa de teste (seed_demo) e valida o gerador de relatorio nela."""
    import importlib
    tmp = tempfile.mkdtemp()
    dbp = os.path.join(tmp, "seed.sqlite")
    con = sqlite3.connect(dbp)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    sys.path.insert(0, str(ROOT / "scripts"))
    seed_demo = importlib.import_module("seed_demo")
    recs = seed_demo.seed(con, n_athletes=3, n_reps=4, make_shares=True)
    con.close()
    assert len(recs) == 3 and all(r["reps"] == 4 for r in recs)

    os.environ["MDLUCCA_DB"] = dbp
    for m in list(sys.modules):
        if m.startswith("app."):
            del sys.modules[m]
    from fastapi.testclient import TestClient
    from app.api import app
    c = TestClient(app)

    # cada sessao gerada rende um relatorio com grafico (rect) e potencia
    for r in recs:
        rep = c.get(r["report_url"])
        assert rep.status_code == 200
        html = rep.text
        assert r["athlete"] in html
        assert html.count("<rect") == 4          # uma barra por repeticao
        assert "Potencia pico" in html

    # reset limpa toda a massa de teste
    con = sqlite3.connect(dbp)
    removed = seed_demo.clear_demo(con)
    left = con.execute("SELECT COUNT(*) FROM athlete").fetchone()[0]
    con.close()
    assert removed == 3 and left == 0


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fail = 0
    for fn in fns:
        try:
            fn(); print("PASS", fn.__name__)
        except Exception as e:  # noqa: BLE001
            fail += 1; print("FAIL", fn.__name__, e)
    print(f"\n{len(fns)-fail}/{len(fns)} ok")
    sys.exit(1 if fail else 0)
