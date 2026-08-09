"""
Testes de filtragem/ruido, interpolacao de frames e calibracao metrica.
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import calibration as Cal  # noqa: E402
from app import signals as S  # noqa: E402


def test_butter_reduces_noise():
    """Sinal senoidal + ruido branco: o filtrado fica mais perto do verdadeiro."""
    rng = np.random.default_rng(0)
    fs = 100.0
    t = np.arange(0, 3, 1 / fs)
    true = np.sin(2 * np.pi * 1.5 * t)          # 1.5 Hz
    noisy = true + 0.3 * rng.standard_normal(t.size)
    filt = S.butter_lowpass(noisy, fs, cutoff=6)
    err_noisy = np.sqrt(np.mean((noisy - true) ** 2))
    err_filt = np.sqrt(np.mean((filt - true) ** 2))
    assert err_filt < err_noisy * 0.5, (err_filt, err_noisy)


def test_noise_metrics_snr_positive():
    fs = 100.0
    t = np.arange(0, 3, 1 / fs)
    y = np.sin(2 * np.pi * 1.0 * t) + 0.05 * np.random.default_rng(1).standard_normal(t.size)
    m = S.noise_metrics(y, fs, 6)
    assert m["snr_db"] > 10  # sinal bem acima do ruido


def test_interpolate_gaps_1d():
    a = np.array([0.0, np.nan, np.nan, 3.0, np.nan, 5.0])
    f = S.interpolate_gaps(a)
    assert np.allclose(f, [0, 1, 2, 3, 4, 5])


def test_stack_frames_none():
    """Frames faltantes (None) sao interpolados, nao repetem o 1o quadro."""
    frames = [np.zeros((2, 2)), None, np.full((2, 2), 2.0)]
    out = S.stack_frames(frames, (2, 2))
    assert np.allclose(out[1], 1.0)          # interpolado entre 0 e 2
    assert out.shape == (3, 2, 2)


def test_residual_analysis_monotonic():
    fs = 100.0
    t = np.arange(0, 2, 1 / fs)
    y = np.sin(2 * np.pi * 2 * t) + 0.1 * np.random.default_rng(2).standard_normal(t.size)
    r = S.residual_analysis(y, fs)["residuals"]
    # residuo cai conforme o corte sobe (menos coisa e removida)
    assert r[0]["rms_residual"] >= r[-1]["rms_residual"]


def test_calibration_reference():
    # 200 px na horizontal = 1.0 m  -> 0.005 m/px
    c = Cal.from_reference([100, 100], [300, 100], 1.0)
    assert abs(c.m_per_px - 0.005) < 1e-9
    assert abs(c.px_to_m(300) - 1.5) < 1e-9


def test_calibration_stature_and_ground():
    # nariz y=100, tornozelo y=900 -> 800 px = 0.936*1.6 m
    c = Cal.from_stature([500, 100], [500, 900], 1.6, ground_px=900)
    assert c.m_per_px > 0
    # altura do quadril (y=500) acima do solo (900) = 400 px * escala
    h = c.height_above_ground_cm(500)
    assert h is not None and h > 0


def test_reference_target_and_range():
    from app import reference_values as Ref
    # joelho quase reto -> otimo; longe do 180 -> abaixo
    assert Ref.evaluate("knee_extension_deg", 176)["status"] == "otimo"
    assert Ref.evaluate("knee_extension_deg", 140)["status"] == "abaixo"
    # CV baixo otimo, alto fora
    assert Ref.evaluate("cv_pct", 4)["status"] == "otimo"
    assert Ref.evaluate("cv_pct", 30)["status"] == "fora"
    # metrica desconhecida
    assert Ref.evaluate("xyz", 1)["status"] == "sem_referencia"
    # todo padrao tem citacao
    assert all(s.get("citation") for s in Ref.STANDARDS)


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
