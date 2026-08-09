"""
Testes do modelo balistico de Samozino (perfil F-V-P de saltos + FVimb).
Verifica self-consistencia (perfil reproduz a altura medida), maximalidade do
perfil otimo e a direcao do desequilibrio (deficit de forca vs velocidade).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import samozino as S  # noqa: E402

G = 9.81


def test_jump_height_self_consistent():
    """Perfil ajustado deve reproduzir a altura sem carga usada de entrada."""
    res = S.profile_from_jumps([75, 95, 115, 135],
                               [0.40, 0.31, 0.24, 0.185], 0.40, bodyweight_kg=75)
    p = res["perfil"]
    h = S.jump_height(p["F0_N"], p["Sfv_N_por_m_s"], 75, 0.40)
    assert abs(h - 0.40) < 0.01
    assert p["r2"] > 0.99


def test_optimal_is_maximal():
    """Nenhum Sfv deve dar altura maior que o perfil otimo (para o mesmo Pmax)."""
    Pmax, m0, hPO = 2000.0, 75.0, 0.40
    opt = S.optimal_profile(Pmax, m0, hPO, G)
    import numpy as np
    for sfv in np.linspace(opt["Sfv_opt"] * 0.3, opt["Sfv_opt"] * 3, 40):
        F0 = float(np.sqrt(4 * Pmax * sfv))
        h = S.jump_height(F0, sfv, m0, hPO, G)
        if h is not None:
            assert h <= opt["altura_otima_m"] + 1e-6


def test_fvimb_direction_force_deficit():
    """Altura cai MUITO com a carga -> Sfv < Sfv_opt -> deficit de FORCA."""
    res = S.profile_from_jumps([70, 90, 110], [0.40, 0.29, 0.20], 0.40, bodyweight_kg=70)
    assert res["perfil_otimo"]["razao_Sfv_atual_sobre_otimo"] < 1.0
    assert "forca" in res["FVimb"]["tipo"]
    assert res["FVimb"]["ganho_potencial_m"] >= 0


def test_fvimb_direction_velocity_deficit():
    """Altura cai POUCO com a carga -> Sfv > Sfv_opt -> deficit de VELOCIDADE."""
    res = S.profile_from_jumps([70, 90, 110], [0.40, 0.375, 0.35], 0.40, bodyweight_kg=70)
    assert res["perfil_otimo"]["razao_Sfv_atual_sobre_otimo"] > 1.0
    assert "velocidade" in res["FVimb"]["tipo"]
    # otimo nunca e pior que o atual
    assert res["FVimb"]["ganho_potencial_m"] >= 0


def test_needs_pushoff_and_two_loads():
    for bad in (dict(masses_kg=[75], jump_heights_m=[0.4], push_off_m=0.4),
                dict(masses_kg=[75, 95], jump_heights_m=[0.4, 0.3], push_off_m=0.0)):
        try:
            S.profile_from_jumps(**bad)
            assert False, "deveria falhar"
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
