"""
Testes da EVOLUCAO DO ATLETA: progresso entre sessoes usando as mesmas metricas
padronizadas do laudo. Duas sessoes do mesmo atleta -> dois pontos ordenados.
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def _seed_two_sessions(dbp):
    con = sqlite3.connect(dbp)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.execute("INSERT INTO athlete (id,name,body_mass_kg,height_m) VALUES (1,'Zé',80,1.8)")
    for sid, cap, pp in [(1, "2026-01-10", 500), (2, "2026-02-20", 560)]:
        con.execute("INSERT INTO session (id,athlete_id,exercise,load_kg,gravity,pose_source,"
                    "captured_at,meta) VALUES (?,1,'Agachamento',100,9.81,'mediapipe',?,?)",
                    (sid, cap, json.dumps({"fps": 30.0, "pose_detected_frames": 180})))
        con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt,"
                    "frame_start,frame_end) VALUES (?,?,9,'Sessão','composite',180,?,0,179)",
                    (sid * 10, sid, 1 / 30))
        for i, p in enumerate([pp, pp - 40], 1):   # 2 reps -> permite fadiga/CV
            rid = sid * 10 + i
            con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt,"
                        "frame_start,frame_end) VALUES (?,?,?,?,'pull',90,?,0,89)",
                        (rid, sid, i, f"Rep {i}", 1 / 30))
            con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,value_num) "
                        "VALUES (?,?,'peaks','P_peak',?)", (sid, rid, p))
            con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,value_num) "
                        "VALUES (?,?,'peaks','F_peak',?)", (sid, rid, p * 2))
    con.commit(); con.close()


def _client(dbp):
    os.environ["MDLUCCA_DB"] = dbp
    os.environ["MDLUCCA_DEV"] = "1"
    for m in list(sys.modules):
        if m.startswith("app."):
            del sys.modules[m]
    from fastapi.testclient import TestClient
    from app.api import app
    return TestClient(app)


def test_evolution_orders_and_best_rep():
    dbp = os.path.join(tempfile.mkdtemp(), "e.sqlite")
    _seed_two_sessions(dbp)
    c = _client(dbp)
    ev = c.get("/athletes/1/evolution").json()
    assert ev["n_sessions"] == 2
    p = ev["points"]
    # ordenado por data (jan antes de fev)
    assert p[0]["session_id"] == 1 and p[1]["session_id"] == 2
    # "melhor rep" = maximo entre as reps (500 e 560)
    assert p[0]["P_peak"] == 500 and p[1]["P_peak"] == 560
    assert p[1]["F_peak"] == 1120
    # pagina HTML de evolucao renderiza
    html = c.get("/athletes/1/evolution.html")
    assert html.status_code == 200 and "Evolução do atleta" in html.text


if __name__ == "__main__":
    print("rode com pytest")
