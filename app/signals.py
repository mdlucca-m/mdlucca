"""
app/signals.py

Processamento de sinal de nivel-pesquisa usado para recomputar as analises
biomecanicas diretamente das series brutas (fonte de verdade), em vez de
confiar nos escalares pre-calculados. Tudo aqui e numericamente explicito:
filtro Savitzky-Golay, integracao trapezoidal, diferenciacao e reamostragem
por ciclo (0-100%).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import integrate as _integ
from scipy import signal as _sig

DEG2RAD = np.pi / 180.0


# --------------------------------------------------------------------------
# Frames: interpolacao de quadros faltantes/ruins
# --------------------------------------------------------------------------
def interpolate_gaps(a: "np.ndarray") -> "np.ndarray":
    """Interpola linearmente NaNs ao longo do eixo do tempo (eixo 0), por
    coluna. Aceita 1D (serie) ou Nd (ex.: landmarks n x 33 x 3). Bordas sem
    dado sao preenchidas com o vizinho valido mais proximo."""
    a = np.asarray(a, dtype=float)
    orig = a.shape
    A = a.reshape(orig[0], -1).copy()
    idx = np.arange(orig[0])
    for c in range(A.shape[1]):
        col = A[:, c]
        m = ~np.isfinite(col)
        if m.any() and (~m).sum() >= 2:
            col[m] = np.interp(idx[m], idx[~m], col[~m])
        elif m.any() and (~m).sum() == 1:
            col[m] = col[~m][0]
        A[:, c] = col
    return A.reshape(orig)


def stack_frames(frames: list, elem_shape: tuple) -> "np.ndarray":
    """Empilha uma lista de quadros (cada um array ou None) preenchendo os
    None com NaN e interpolando. Corrige o antigo bug de repetir o 1o quadro."""
    filled = [np.asarray(f, float) if f is not None else np.full(elem_shape, np.nan)
              for f in frames]
    return interpolate_gaps(np.array(filled, dtype=float))


# --------------------------------------------------------------------------
# Filtro Butterworth passa-baixa de fase zero (padrao em biomecanica)
# --------------------------------------------------------------------------
def butter_lowpass(y, fs: float, cutoff: float = 6.0, order: int = 4) -> "np.ndarray":
    """Butterworth passa-baixa aplicado com filtfilt (fase zero, sem atraso).
    Cai para Savitzky-Golay quando a serie e curta demais para o filtfilt."""
    a = as_array(y)
    n = a.size
    a = interpolate_gaps(a)
    if fs <= 0 or cutoff <= 0 or cutoff >= fs / 2:
        return a
    padlen = 3 * (2 * order + 1)
    if n <= padlen:
        return savgol(a, min(n if n % 2 else n - 1, 11), 3)
    b, aa = _sig.butter(order, cutoff / (fs / 2.0), btype="low")
    return _sig.filtfilt(b, aa, a)


def residual_analysis(y, fs: float, cutoffs=None) -> dict:
    """Analise de residuo (Winter): RMS de (bruto - filtrado) por frequencia
    de corte. Ajuda a escolher o corte que remove ruido sem destruir sinal."""
    a = interpolate_gaps(as_array(y))
    if cutoffs is None:
        cutoffs = [c for c in (2, 3, 4, 5, 6, 8, 10, 12, 15) if c < fs / 2]
    res = []
    for c in cutoffs:
        f = butter_lowpass(a, fs, c)
        res.append({"cutoff_hz": c, "rms_residual": round(float(np.sqrt(np.mean((a - f) ** 2))), 4)})
    return {"fs": fs, "n": int(a.size), "residuals": res}


def noise_metrics(y, fs: float, cutoff: float = 6.0) -> dict:
    """Estimativa de ruido: RMS do que o passa-baixa remove e SNR aproximada."""
    a = interpolate_gaps(as_array(y))
    f = butter_lowpass(a, fs, cutoff)
    noise = a - f
    sig_rms = float(np.sqrt(np.mean(f ** 2))) or 1e-9
    noise_rms = float(np.sqrt(np.mean(noise ** 2)))
    return {"cutoff_hz": cutoff, "signal_rms": round(sig_rms, 4),
            "noise_rms": round(noise_rms, 4),
            "snr_db": round(20 * np.log10(sig_rms / (noise_rms or 1e-9)), 1)}


def as_array(x: Sequence[float]) -> np.ndarray:
    return np.asarray(x, dtype=float)


def savgol(y: Sequence[float], window: int = 11, poly: int = 3) -> np.ndarray:
    """Filtro Savitzky-Golay com janela saneada (impar, <= n, > poly)."""
    a = as_array(y)
    n = a.size
    if n < poly + 2:
        return a
    w = min(window, n if n % 2 == 1 else n - 1)
    if w % 2 == 0:
        w -= 1
    w = max(w, poly + 1 + (1 - (poly + 1) % 2))  # garante impar > poly
    if w <= poly:
        return a
    return _sig.savgol_filter(a, w, poly)


def derivative(y: Sequence[float], t: Sequence[float], smooth_window: int = 0) -> np.ndarray:
    """d y / d t via diferencas centradas (np.gradient), com suavizacao opcional."""
    a = as_array(y)
    tt = as_array(t)
    if smooth_window and smooth_window >= 3:
        a = savgol(a, smooth_window, 3)
    return np.gradient(a, tt)


def integrate(y: Sequence[float], t: Sequence[float]) -> float:
    """Integral definida (regra do trapezio)."""
    return float(_integ.trapezoid(as_array(y), as_array(t)))


def cumulative_integral(y: Sequence[float], t: Sequence[float]) -> np.ndarray:
    return _integ.cumulative_trapezoid(as_array(y), as_array(t), initial=0.0)


def resample_cycle(y: Sequence[float], n: int = 101) -> np.ndarray:
    """Reamostra uma serie para n pontos igualmente espacados em 0-100% do
    ciclo (padrao-ouro para comparar forma de curvas de duracoes diferentes)."""
    a = as_array(y)
    if a.size == 0:
        return np.array([])
    xp = np.linspace(0.0, 1.0, a.size)
    xq = np.linspace(0.0, 1.0, n)
    return np.interp(xq, xp, a)


def find_onset(force: Sequence[float], t: Sequence[float], baseline_frac: float = 0.1,
               k_sd: float = 5.0) -> int:
    """Onset da fase de forca: primeiro indice em que a forca ultrapassa
    baseline + k*sd, estimado sobre os primeiros baseline_frac da janela.
    Metodo classico em diagnostico de forca explosiva."""
    a = as_array(force)
    n = a.size
    if n < 5:
        return 0
    b = max(3, int(n * baseline_frac))
    mu = float(np.mean(a[:b]))
    sd = float(np.std(a[:b])) or 1.0
    thr = mu + k_sd * sd
    idx = np.argmax(a > thr)
    return int(idx) if a[idx] > thr else int(np.argmax(a))


def concentric_window(angle: Sequence[float]) -> tuple[int, int]:
    """Janela concentrica de uma serie angular: do minimo global ate o maximo
    subsequente (fundo do movimento -> extensao maxima)."""
    a = as_array(angle)
    if a.size < 2:
        return (0, a.size - 1)
    lo = int(np.argmin(a))
    hi = lo + int(np.argmax(a[lo:]))
    if hi <= lo:
        hi = a.size - 1
    return (lo, hi)


def positive_negative_work(power: Sequence[float], t: Sequence[float]) -> tuple[float, float]:
    """Trabalho positivo (concentrico) e negativo (excentrico) = integral da
    potencia nas regioes de sinal positivo/negativo."""
    p = as_array(power)
    tt = as_array(t)
    pos = np.where(p > 0, p, 0.0)
    neg = np.where(p < 0, p, 0.0)
    return integrate(pos, tt), integrate(neg, tt)
