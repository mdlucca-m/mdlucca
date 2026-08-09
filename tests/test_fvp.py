"""
Testes do perfil Forca-Velocidade-Potencia (teste de cargas).
Constroi um teste sintetico a partir de uma reta F-v conhecida e verifica que
o motor recupera F0, V0, Pmax, carga otima e as equacoes.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import fvp as FVP  # noqa: E402

G = 9.81


def _synthetic():
    """F-v exata: F = F0 - Sfv*v, com F = carga*g. F0=1000, Sfv=500 -> V0=2, Pmax=500."""
    F0, Sfv = 1000.0, 500.0
    loads = [20.0, 40.0, 60.0, 80.0]
    vels = [(F0 - L * G) / Sfv for L in loads]     # v = (F0 - m g)/Sfv
    return loads, vels, F0, Sfv


def test_fv_recovers_F0_V0_Pmax():
    loads, vels, F0, Sfv = _synthetic()
    r = FVP.full_profile(loads, vels, g=G)
    fv = r["perfil_forca_velocidade"]
    assert abs(fv["F0_N"] - F0) < 1.0
    assert abs(fv["V0_m_s"] - F0 / Sfv) < 0.02        # V0 = 2.0
    assert abs(fv["Pmax_W"] - F0 * (F0 / Sfv) / 4) < 1.0   # 500 W
    assert fv["r2"] > 0.999
    assert "F =" in fv["equation_fv"] and "P =" in fv["equation_pv"]


def test_optimal_load_and_velocity():
    loads, vels, F0, Sfv = _synthetic()
    fv = FVP.full_profile(loads, vels, g=G)["perfil_forca_velocidade"]
    assert abs(fv["v_otima_m_s"] - 1.0) < 0.02        # V0/2
    assert abs(fv["F_otima_N"] - 500.0) < 1.0         # F0/2
    assert abs(fv["carga_otima_kg"] - 500.0 / G) < 0.5


def test_load_velocity_1rm_estimate():
    loads, vels, F0, Sfv = _synthetic()
    lv = FVP.full_profile(loads, vels, g=G, v1rm=0.30)["perfil_carga_velocidade"]
    # 1RM pratico (v=0.30) deve ficar entre a maior carga testada e o 1RM teorico
    assert lv["carga_1RM_estimada_kg"] > 80
    assert lv["carga_1RM_teorica_v0_kg"] >= lv["carga_1RM_estimada_kg"]
    assert lv["r2"] > 0.999


def test_gravitational_component_and_bodyweight():
    loads, vels, _, _ = _synthetic()
    r = FVP.full_profile(loads, vels, g=G, bodyweight_kg=80.0)
    # forca do 1o ponto inclui a massa corporal: (carga+80)*g
    p0 = r["pontos"][0]
    assert abs(p0["forca_grav_N"] - (p0["carga_kg"] + 80.0) * G) < 0.1
    assert r["ajustes_alometricos"]["disponivel"] is True
    assert r["ajustes_alometricos"]["Pmax_por_kg_W"] is not None


def test_adjustments_present():
    loads, vels, _, _ = _synthetic()
    r = FVP.full_profile(loads, vels, g=G)
    assert r["ajuste_quadratico_fv"]["disponivel"] is True
    assert "orientacao" in r["interpretacao"]
    assert len(r["equacoes_regressao"]) == 3


def test_needs_two_loads():
    try:
        FVP.full_profile([50.0], [0.8])
        assert False, "deveria exigir >= 2 cargas"
    except ValueError:
        pass


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
