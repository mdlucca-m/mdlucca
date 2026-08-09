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
