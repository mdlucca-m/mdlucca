"""
Validacao do motor de cinematica (app.kinematics): recomputa angulos a
partir dos LANDMARKS e confere correlacao alta com as series armazenadas.
A defasagem residual e o aspect ratio faltante (calibracao) — recuperado
por fit_aspect e que desaparece sob coordenadas metricas na Etapa 2.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import kinematics as K  # noqa: E402

DB = Path(__file__).resolve().parents[1] / "data" / "db.sqlite"


def _skeleton_and_ref(ordinal=1):
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    sub = con.execute("SELECT id FROM submovement WHERE ordinal=?", (ordinal,)).fetchone()["id"]
    sk = json.loads(con.execute(
        "SELECT payload FROM dataset WHERE submovement_id=? AND kind='skeleton'", (sub,)).fetchone()["payload"])
    ref = {}
    for jntip in ("hip", "knee", "elbow"):
        r = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                        (sub, f"{jntip}_angle")).fetchone()
        ref[jntip] = json.loads(r["samples"])
    con.close()
    return sk, ref


def test_fit_aspect_recovers_plausible_ratio():
    sk, ref = _skeleton_and_ref()
    fit = K.fit_aspect(sk, ref)
    # aspect do video vertical fica entre ~1.7 e ~2.4 (bbox ~2.2)
    assert 1.5 < fit["aspect"] < 2.6, fit


def test_recomputed_angles_correlate_with_stored():
    sk, ref = _skeleton_and_ref()
    asp = K.fit_aspect(sk, ref)["aspect"]
    rep = K.validate_against(sk, ref, asp)
    for joint in ("hip", "knee", "elbow"):
        assert rep[joint]["corr"] > 0.95, (joint, rep[joint])


def test_center_of_mass_shape():
    sk, ref = _skeleton_and_ref()
    com = K.center_of_mass(sk, 2.31)
    assert com["n"] == len(sk["hip"])
    assert com["y_excursion"] > 0
    assert len(com["y"]) == com["n"]


def test_angles_from_landmarks_all_joints():
    sk, _ = _skeleton_and_ref()
    ang = K.angles_from_landmarks(sk, 2.31)
    assert {"elbow", "knee", "hip"} <= set(ang)
    assert all(0 <= v <= 180 for v in ang["knee"])


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
