"""
Validacao das analises PROFUNDAS (app.biomech): recomputam a partir das
series brutas e conferem contra os escalares que o dashboard reportava,
onde a definicao coincide. Onde diverge por definicao (PPV usa velocidade
3D; TDF em micro-janela e sensivel), checamos apenas plausibilidade fisica.

Requer data/db.sqlite (rode: python3 scripts/ingest.py).
"""
import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import biomech as B  # noqa: E402

DB = Path(__file__).resolve().parents[1] / "data" / "db.sqlite"


def _series(sub_ordinal=1):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sub = con.execute("SELECT id FROM submovement WHERE ordinal=?", (sub_ordinal,)).fetchone()["id"]
    sm = {r["name"]: json.loads(r["samples"])
          for r in con.execute("SELECT name,samples FROM series WHERE submovement_id=?", (sub,))}
    con.close()
    return sm


def _stored(const_name, rep=1):
    """Le um escalar armazenado do JSON extraido (referencia do dashboard)."""
    d = json.loads((Path(__file__).resolve().parents[1] / "data" / "dashboard_extracted.json").read_text())
    for row in d[const_name]:
        if row.get("rep") == rep:
            return row
    return None


def test_joint_power_work_matches_stored():
    """Trabalho articular (integral da potencia) bate bem com o armazenado."""
    sm = _series(1)
    res = B.joint_power(sm["tau_hip"], sm["hip_angvel"], sm["t"])
    stored = _stored("JOINT_POWER")["hip"]
    assert abs(res["work_pos_J"] - stored["work_pos"]) < 15, (res["work_pos_J"], stored["work_pos"])
    assert abs(res["work_neg_J"] - stored["work_neg"]) < 20, (res["work_neg_J"], stored["work_neg"])
    assert abs(res["pct_concentric"] - stored["pct_concentrico"]) < 3


def test_ssc_amortization_matches():
    sm = _series(1)
    res = B.ssc(sm["hip_angle"], sm["hip_angvel"], sm["speed"], sm["t"])
    stored = _stored("SSC_RESULTS")
    assert abs(res["t_amortization_ms"] - stored["t_amortization_ms"]) < 10, res


def test_jerk_matches():
    sm = _series(1)
    res = B.jerk(sm["accel"], sm["t"])
    stored = _stored("DERIVADAS")
    # jerk de pico deve ficar proximo do valor do dashboard (mesma familia de filtro)
    assert abs(res["jerk_peak"] - stored["jerk_peak"]) / stored["jerk_peak"] < 0.15, res


def test_mcv_matches():
    sm = _series(1)
    res = B.velocity_metrics(sm["speed"], sm["tangential_accel"], sm["t"])
    stored = _stored("PROPULSIVE")
    assert abs(res["MCV_ms"] - stored["MCV"]) < 0.02, (res["MCV_ms"], stored["MCV"])


def test_impulse_work_physical():
    """Sanidade fisica: impulso positivo, trabalho positivo > 0, duracao ~7.8s."""
    sm = _series(1)
    res = B.impulse_work(sm["force"], sm["speed"], sm["power"], sm["t"], 60.0)
    assert res["impulse_total_Ns"] > 0
    assert res["work_positive_J"] > 0
    assert abs(res["duration_s"] - 7.77) < 0.2


def test_normalized_cycle_length():
    sm = _series(1)
    y = B.normalized_cycle(sm["hip_angle"], 101)
    assert len(y) == 101
    assert abs(y[0] - sm["hip_angle"][0]) < 1e-6  # extremos preservados


def test_sequencing_returns_order():
    sm = _series(1)
    joints = {j: sm[f"{j}_angvel"] for j in ("hip", "knee", "elbow", "ankle")}
    res = B.sequencing(joints, sm["t"])
    assert set(res["order"]) == {"hip", "knee", "elbow", "ankle"}
    assert len(res["events"]) == 4


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn(); print(f"PASS {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1; print(f"FAIL {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns)-failed}/{len(fns)} testes passaram")
    sys.exit(1 if failed else 0)
