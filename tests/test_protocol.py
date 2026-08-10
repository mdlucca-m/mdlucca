"""
Testes do PADRAO DE ANALISE (app/protocol.py): o laudo padronizado deve emitir
SEMPRE as mesmas metricas-chave e as mesmas checagens de literatura, na mesma
ordem, com 'N/D' quando um valor nao pode ser calculado — para qualquer sessao.
"""
import json
import os
import sqlite3
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import protocol as Proto  # noqa: E402


def test_drop_pct_and_fmt():
    assert Proto.drop_pct([100, 90, 80]) == 20.0      # (100-80)/100
    assert Proto.drop_pct([100]) is None               # precisa de >= 2
    assert Proto.drop_pct([None, None]) is None
    assert Proto.fmt_value(None) == Proto.NA
    assert Proto.fmt_value(1.239, 2) == "1.24"
    assert Proto.fmt_value(1028.0, 0) in ("1.028", "1028")


def _seed(dbp):
    con = sqlite3.connect(dbp)
    con.executescript((ROOT / "sql" / "schema.sql").read_text())
    con.execute("INSERT INTO athlete (id,name,body_mass_kg,height_m) VALUES (1,'X',80,1.8)")
    con.execute("INSERT INTO session (id,athlete_id,exercise,load_kg,gravity,pose_source,meta) "
                "VALUES (1,1,'Agachamento',100,9.81,'mediapipe',?)",
                (json.dumps({"fps": 30.0, "pose_detected_frames": 180}),))
    # sessao completa com uma serie de quadril
    con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt) "
                "VALUES (9,1,9,'Sessão','composite',180,?)", (1 / 30,))
    hip = [175 - 80 * (i % 90) / 90 for i in range(180)]
    for nm, arr in [("t", [i / 30 for i in range(180)]), ("hip_angle", hip)]:
        con.execute("INSERT INTO series (submovement_id,name,unit,n,samples) VALUES (9,?,?,?,?)",
                    (nm, "-", len(arr), json.dumps(arr)))
    # duas reps com apenas F_peak e P_peak (as demais metricas ficam N/D)
    for i, (fp, pp) in enumerate([(1000, 500), (900, 420)], 1):
        con.execute("INSERT INTO submovement (id,session_id,ordinal,label,kind,n_frames,dt) "
                    "VALUES (?,1,?,?,'pull',90,?)", (i, i, f"Rep {i}", 1 / 30))
        con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,value_num) "
                    "VALUES (1,?,'peaks','F_peak',?)", (i, fp))
        con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,value_num) "
                    "VALUES (1,?,'peaks','P_peak',?)", (i, pp))
    con.commit(); con.close()


def _assess(dbp):
    os.environ["MDLUCCA_DB"] = dbp
    os.environ["MDLUCCA_DEV"] = "1"
    for m in list(sys.modules):
        if m.startswith("app."):
            del sys.modules[m]
    from app.api import _build_assessment
    return _build_assessment(1)


def test_canonical_metrics_and_checks_always_present():
    dbp = os.path.join(tempfile.mkdtemp(), "p.sqlite")
    _seed(dbp)
    a = _assess(dbp)

    # toda rep traz TODAS as metricas canonicas (na ordem), ausentes = None
    keys = [m["key"] for m in Proto.CANONICAL_METRICS]
    for row in a["reps"]:
        assert [k for k in row.keys() if k != "rep"] == keys
    assert a["reps"][0]["F_peak"] == 1000
    assert a["reps"][0]["MPV"] is None            # nao existe -> N/D no laudo

    # checagens canonicas: sempre as 4, na ordem, mesmo sem valor
    refs = [c["metric"] for c in a["literature_checks"]]
    assert refs == [c["ref"] for c in Proto.CANONICAL_CHECKS]
    knee = next(c for c in a["literature_checks"] if c["metric"] == "knee_extension_deg")
    assert knee["value"] is None and knee["status"] == Proto.NA

    # indice de fadiga calculado a partir das reps
    assert a["fatigue"]["power_drop_pct"] == 16.0   # (500-420)/500
    assert a["protocol_version"] == Proto.PROTOCOL_VERSION


if __name__ == "__main__":
    print("rode com pytest")
