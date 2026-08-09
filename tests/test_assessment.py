"""
Testes da AVALIACAO COMPLETA unificada: classificacao de movimento, score de
qualidade e o endpoint /sessions/{id}/assessment (+ persistencia e markdown).
"""
import json
import math
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import classify as Clf  # noqa: E402
from app import quality as Qual  # noqa: E402


def _squat_hip(cycles=2, fs=30.0):
    """Sinal de quadril tipo agachamento: 175 -> 90 -> 175, ROM grande, lento."""
    t, y = [], []
    per = 90  # frames por ciclo (3 s a 30 fps)
    for c in range(cycles):
        for i in range(per):
            p = i / per
            hip = 175 - 85 * math.sin(math.pi * p)   # desce e sobe
            t.append((c * per + i) / fs); y.append(hip)
    return y, t


def test_classify_squat():
    y, t = _squat_hip()
    r = Clf.classify_movement(y, t)
    assert r["pattern"] in ("agachamento", "agachamento_forca")
    assert r["rom_quadril_graus"] > 70


def test_classify_hops():
    # 4 ciclos curtos de baixa amplitude (hops reativos) -> hopping/pliometrico
    t, y = [], []
    per = 40
    for c in range(4):
        for i in range(per):
            p = i / per
            y.append(160 - 18 * math.sin(math.pi * p)); t.append((c * per + i) / 40.0)
    r = Clf.classify_movement(y, t)
    assert r["pattern"] in ("hopping_repetido", "pliometrico")


def test_quality_penalties():
    good = Qual.quality_report(n_frames=200, fps=60, is_calibrated=True)
    assert good["level"] == "excelente" and not good["warnings"]
    bad = Qual.quality_report(n_frames=15, fps=12, is_calibrated=False, detected_ratio=0.7)
    assert bad["score"] < 70 and len(bad["warnings"]) >= 3


def _seed_session(dbp):
    con = sqlite3.connect(dbp)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.execute("INSERT INTO athlete (id,name,body_mass_kg,height_m) VALUES (1,'Zé',80,1.8)")
    con.execute("INSERT INTO session (id,athlete_id,exercise,load_kg,gravity,pose_source,meta) "
                "VALUES (1,1,'Agachamento',100,9.81,'mediapipe',?)",
                (json.dumps({"fps": 30.0, "pose_detected_frames": 180}),))
    y, t = _squat_hip()
    con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt,is_slowmo_2x) "
                "VALUES (9,1,9,'Sessão completa','composite',?,?,0)", (len(y), 1 / 30))
    for nm, arr in [("t", t), ("hip_angle", y),
                    ("knee_angle", [v * 0.9 for v in y]),
                    ("elbow_angle", [80] * len(y))]:
        con.execute("INSERT INTO series (submovement_id,name,unit,n,samples) VALUES (9,?,?,?,?)",
                    (nm, "-", len(arr), json.dumps(arr)))
    for i, pw in enumerate([500, 460], 1):     # 2 reps com pico de potencia
        con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt,"
                    "is_slowmo_2x) VALUES (?,?,?,?,'pull',90,?,0)", (i, 1, i, f"Rep {i}", 1 / 30))
        con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,value_num) "
                    "VALUES (1,?,'peaks','power_peak',?)", (i, pw))
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


def test_assessment_endpoint_and_persist():
    dbp = os.path.join(tempfile.mkdtemp(), "t.sqlite")
    _seed_session(dbp)
    c = _client(dbp)
    a = c.get("/sessions/1/assessment").json()
    assert a["classification"]["pattern"] in ("agachamento", "agachamento_forca")
    assert a["quality"]["level"] in ("excelente", "bom")
    assert any(ch["metric"] == "hip_extension_deg" for ch in a["literature_checks"])
    assert a["n_reps"] == 2

    r = c.post("/sessions/1/assessment").json()
    rid = r["analysis_run_id"]
    assert c.get(f"/assessments/{rid}").json()["quality_level"] in ("excelente", "bom")
    md = c.get(f"/assessments/{rid}/report.md").text
    assert "Relatório de Avaliação Biomecânica" in md and "Classificação" in md


if __name__ == "__main__":
    print("rode com pytest")
