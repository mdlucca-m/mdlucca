"""
Testes de validacao das analises padrao-ouro: recomputam metricas a partir
das series/valores brutos e comparam com o que o dashboard HTML reportava.
Executar: python3 -m pytest tests/ -q   (ou python3 tests/test_analyses.py)
"""
import json
import math
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import analyses as A  # noqa: E402

DB = Path(__file__).resolve().parents[1] / "data" / "db.sqlite"


def _con():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con


def test_cv_matches_dashboard():
    """CV recomputado bate com o cv_pct armazenado (tolerancia 0.1pp)."""
    con = _con()
    rows = con.execute(
        "SELECT metric_name, scope, values_json, cv_pct FROM consistency_source "
        "WHERE analysis='cv' AND cv_pct IS NOT NULL"
    ).fetchall()
    con.close()
    assert rows, "sem dados de consistencia"
    for r in rows:
        vals = json.loads(r["values_json"])
        got = A.coefficient_of_variation(vals)["cv_pct"]
        assert abs(got - r["cv_pct"]) < 0.1, (r["metric_name"], r["scope"], got, r["cv_pct"])


def test_grubbs_two_sided_critical_is_correct():
    """O HTML usava G_critical=1.672, que e o valor UNILATERAL de Grubbs.
    Como a estatistica usa o desvio ABSOLUTO maximo (bilateral), o valor
    critico correto para n=5, alpha=0.05 e 1.715 (tabela de Grubbs). Aqui
    validamos que a nossa implementacao produz o valor bilateral correto."""
    con = _con()
    outs = con.execute(
        "SELECT metric_name, values_json FROM consistency_source WHERE scope='grubbs_5seg'"
    ).fetchall()
    con.close()
    assert outs, "sem dados de outlier"
    for r in outs:
        vals = json.loads(r["values_json"])
        res = A.grubbs_test(vals, alpha=0.05)
        assert len(vals) == 5
        assert abs(res["G_critical"] - 1.715) < 0.01, (r["metric_name"], res["G_critical"])


def test_powerlaw_recompute():
    """Recomputa F = a*v^b a partir dos pontos e bate com o fit armazenado."""
    con = _con()
    fit = con.execute(
        "SELECT params, r2 FROM fit WHERE analysis='powerlaw' AND model='F_vs_v'"
    ).fetchone()
    pts = con.execute(
        "SELECT meta FROM fit WHERE analysis='force_velocity'"
    ).fetchone()
    con.close()
    points = json.loads(pts["meta"])["points"]
    v = [p["v"] for p in points]
    f = [p["f"] for p in points]
    got = A.powerlaw_fit(v, f)
    stored = json.loads(fit["params"])
    assert abs(got["b"] - stored["b"]) < 0.02, (got["b"], stored["b"])
    assert abs(got["r2"] - fit["r2"]) < 0.02, (got["r2"], fit["r2"])


def test_logistic_peak_positive():
    """O ajuste logistico converge e produz taxa de pico positiva na Rep 1."""
    con = _con()
    row = con.execute(
        "SELECT se_t.samples AS t, se_y.samples AS y "
        "FROM submovement s "
        "JOIN series se_t ON se_t.submovement_id=s.id AND se_t.name='t' "
        "JOIN series se_y ON se_y.submovement_id=s.id AND se_y.name='hip_angle' "
        "WHERE s.ordinal=1"
    ).fetchone()
    con.close()
    t = json.loads(row["t"])
    hip = json.loads(row["y"])
    # fase concentrica aproximada: do minimo de angulo ate o maximo subsequente
    lo = hip.index(min(hip))
    hi = lo + hip[lo:].index(max(hip[lo:]))
    res = A.logistic_fit(t[lo:hi + 1], hip[lo:hi + 1])
    assert res["fit_ok"], res
    assert res["peak_rate_analytic"] > 0
    assert res["r2"] is None or res["r2"] > 0.5


def test_robust_peak_close_to_raw():
    con = _con()
    row = con.execute(
        "SELECT samples FROM series WHERE name='force' AND submovement_id="
        "(SELECT id FROM submovement WHERE ordinal=1)"
    ).fetchone()
    con.close()
    force = json.loads(row["samples"])
    rp = A.robust_peak(force)
    assert rp["robust"] <= rp["raw"]  # mediana da janela <= pico bruto


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(fns) - failed}/{len(fns)} testes passaram")
    sys.exit(1 if failed else 0)
