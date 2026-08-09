"""
app/analyses.py

Analises biomecanicas "padrao-ouro" reimplementadas com rigor estatistico
(numpy/scipy). O dashboard HTML original computava estas metricas com
aproximacoes feitas a mao em JavaScript (ex.: valor critico de Grubbs
hardcoded, sem intervalo de confianca real). Aqui cada uma e recalculada
de forma independente e correta, servida sob demanda pela API.

Todas as funcoes sao puras (entram listas/arrays, saem dicts) e nao
dependem do banco — o que as torna testaveis isoladamente.
"""
from __future__ import annotations

from typing import Sequence

import numpy as np
from scipy import optimize, stats

Number = float


# --------------------------------------------------------------------------
# Descritivas e picos robustos
# --------------------------------------------------------------------------
def describe(values: Sequence[Number]) -> dict:
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    if a.size == 0:
        return {"n": 0}
    return {
        "n": int(a.size),
        "mean": float(np.mean(a)),
        "sd": float(np.std(a, ddof=1)) if a.size > 1 else 0.0,
        "min": float(np.min(a)),
        "max": float(np.max(a)),
        "median": float(np.median(a)),
    }


def robust_peak(series: Sequence[Number], half_window: int = 2) -> dict:
    """Pico robusto: mediana de uma janela centrada no maximo (reduz ruido
    de 1 frame isolado). Retorna valor bruto, valor robusto e indice."""
    a = np.asarray(series, dtype=float)
    if a.size == 0:
        return {}
    idx = int(np.nanargmax(a))
    lo, hi = max(0, idx - half_window), min(a.size, idx + half_window + 1)
    return {
        "index": idx,
        "raw": float(a[idx]),
        "robust": float(np.nanmedian(a[lo:hi])),
        "window": [lo, hi - 1],
    }


# --------------------------------------------------------------------------
# Coeficiente de Variacao (com IC bootstrap)
# --------------------------------------------------------------------------
def classify_cv(cv_pct: float) -> str:
    if cv_pct < 5:
        return "muito consistente"
    if cv_pct < 10:
        return "consistente"
    if cv_pct < 15:
        return "moderado"
    return "variavel"


def coefficient_of_variation(
    values: Sequence[Number], n_boot: int = 5000, alpha: float = 0.05, seed: int = 42
) -> dict:
    """CV% = 100 * sd_amostral / media. Inclui IC bootstrap percentil — o
    HTML reportava apenas a estimativa pontual, sem incerteza."""
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    n = a.size
    if n < 2 or np.mean(a) == 0:
        return {"n": int(n), "cv_pct": None, "error": "amostra insuficiente ou media zero"}
    mean = float(np.mean(a))
    sd = float(np.std(a, ddof=1))
    cv = 100.0 * sd / mean

    rng = np.random.default_rng(seed)
    boots = []
    for _ in range(n_boot):
        s = rng.choice(a, size=n, replace=True)
        m = np.mean(s)
        if m != 0 and np.std(s, ddof=1) > 0:
            boots.append(100.0 * np.std(s, ddof=1) / m)
    ci = (
        [float(np.percentile(boots, 100 * alpha / 2)),
         float(np.percentile(boots, 100 * (1 - alpha / 2)))]
        if boots else None
    )
    return {
        "n": int(n),
        "mean": mean,
        "sd": sd,
        "cv_pct": round(cv, 4),
        "classification": classify_cv(cv),
        "ci95": ci,
        "n_bootstrap_valid": len(boots),
        "note": "IC bootstrap com n pequeno e amplo; interpretar com cautela." if n < 8 else None,
    }


# --------------------------------------------------------------------------
# Teste de outlier de Grubbs (bilateral) — valor critico exato via t
# --------------------------------------------------------------------------
def grubbs_test(values: Sequence[Number], alpha: float = 0.05) -> dict:
    """Grubbs bilateral. Diferente do HTML (G_critico=1.672 hardcoded), aqui
    o valor critico vem da distribuicao t para o (n, alpha) reais."""
    a = np.asarray(values, dtype=float)
    a = a[np.isfinite(a)]
    n = a.size
    if n < 3:
        return {"n": int(n), "error": "Grubbs exige n >= 3"}
    mean = float(np.mean(a))
    sd = float(np.std(a, ddof=1))
    if sd == 0:
        return {"n": int(n), "G": 0.0, "is_outlier": False, "note": "desvio-padrao zero"}
    abs_dev = np.abs(a - mean)
    i = int(np.argmax(abs_dev))
    G = float(abs_dev[i] / sd)

    # valor critico bilateral
    t_crit = stats.t.ppf(1 - alpha / (2 * n), n - 2)
    G_crit = (n - 1) / np.sqrt(n) * np.sqrt(t_crit**2 / (n - 2 + t_crit**2))

    # p-valor bilateral (Bonferroni) a partir de G
    t_stat = np.sqrt((n * (n - 2) * G**2) / ((n - 1) ** 2 - n * G**2)) if (n - 1) ** 2 - n * G**2 > 0 else np.inf
    p = float(min(1.0, 2 * n * stats.t.sf(t_stat, n - 2)))
    return {
        "n": int(n),
        "outlier_index": i,
        "outlier_value": float(a[i]),
        "mean": mean,
        "sd": sd,
        "G": round(G, 4),
        "G_critical": round(float(G_crit), 4),
        "alpha": alpha,
        "p_value": round(p, 4),
        "is_outlier": bool(G > G_crit),
    }


# --------------------------------------------------------------------------
# Regressao linear e lei de potencia (log-log) com IC bootstrap do slope
# --------------------------------------------------------------------------
def linear_regression(x: Sequence[Number], y: Sequence[Number]) -> dict:
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    x, y = x[m], y[m]
    if x.size < 2:
        return {"n": int(x.size), "error": "amostra insuficiente"}
    r = stats.linregress(x, y)
    return {
        "n": int(x.size),
        "slope": float(r.slope),
        "intercept": float(r.intercept),
        "r2": float(r.rvalue**2),
        "p_value": float(r.pvalue),
        "stderr": float(r.stderr),
    }


def powerlaw_fit(x: Sequence[Number], y: Sequence[Number]) -> dict:
    """y = a * x^b  ->  regressao linear em log(y) ~ log(x).
    Retorna a, b, r2 (na escala log) e p do expoente."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
    x, y = x[m], y[m]
    if x.size < 2:
        return {"n": int(x.size), "error": "amostra insuficiente (exige x>0, y>0)"}
    lr = stats.linregress(np.log(x), np.log(y))
    a = float(np.exp(lr.intercept))
    b = float(lr.slope)
    return {
        "n": int(x.size),
        "a": a,
        "b": b,
        "r2": float(lr.rvalue**2),
        "p_value": float(lr.pvalue),
        "eq": "y = a * x^b",
    }


def bootstrap_slope_ci(
    x: Sequence[Number],
    y: Sequence[Number],
    space: str = "loglog",
    n_boot: int = 5000,
    alpha: float = 0.05,
    seed: int = 42,
) -> dict:
    """IC bootstrap (percentil) do coeficiente angular. space='loglog' para
    lei de potencia (slope = expoente b), 'linear' para regressao direta."""
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    m = np.isfinite(x) & np.isfinite(y)
    if space == "loglog":
        m &= (x > 0) & (y > 0)
    x, y = x[m], y[m]
    n = x.size
    if n < 3:
        return {"n": int(n), "error": "amostra insuficiente"}
    tx = np.log(x) if space == "loglog" else x
    ty = np.log(y) if space == "loglog" else y

    rng = np.random.default_rng(seed)
    slopes = []
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        xb, yb = tx[idx], ty[idx]
        if np.ptp(xb) == 0:
            continue
        slopes.append(np.polyfit(xb, yb, 1)[0])
    slopes = np.asarray(slopes)
    lo = float(np.percentile(slopes, 100 * alpha / 2))
    hi = float(np.percentile(slopes, 100 * (1 - alpha / 2)))
    return {
        "n": int(n),
        "space": space,
        "slope_point": float(np.polyfit(tx, ty, 1)[0]),
        "slope_median": float(np.median(slopes)),
        "ci95_low": round(lo, 4),
        "ci95_high": round(hi, 4),
        "includes_zero": bool(lo <= 0 <= hi),
        "n_bootstrap_valid": int(slopes.size),
    }


# --------------------------------------------------------------------------
# Ajuste logistico (nls) da fase concentrica
# --------------------------------------------------------------------------
def _logistic(t, b, L, k, t0):
    return b + L / (1 + np.exp(-k * (t - t0)))


def logistic_fit(t: Sequence[Number], theta: Sequence[Number]) -> dict:
    """Ajusta theta(t) = b + L / (1 + e^(-k(t-t0))) por minimos quadrados
    nao-lineares. A derivada tem maximo exato em t0 (= L*k/4), estimando o
    pico de velocidade angular sem diferenciacao numerica ruidosa."""
    t = np.asarray(t, dtype=float)
    y = np.asarray(theta, dtype=float)
    m = np.isfinite(t) & np.isfinite(y)
    t, y = t[m], y[m]
    if t.size < 4:
        return {"n": int(t.size), "fit_ok": False, "error": "amostra insuficiente"}
    span = float(np.ptp(y)) or 1.0
    tspan = float(np.ptp(t)) or 1.0
    b0 = float(np.min(y))
    L0 = span
    t00 = float(t[np.argmax(np.gradient(y, t))]) if t.size > 2 else float(np.median(t))
    k0 = 5.0 / tspan
    # Limites fisicos: evitam a solucao degenerada (L e b divergindo para
    # aproximar uma reta). L>0 e limitado a alguns spans, b perto da faixa
    # observada, k>0 finito, t0 dentro da janela temporal.
    lower = [float(np.min(y)) - span, 1e-6, 1e-6, float(np.min(t))]
    upper = [float(np.max(y)), 3.0 * span, 1e3, float(np.max(t))]
    t00 = min(max(t00, lower[3]), upper[3])
    try:
        popt, _ = optimize.curve_fit(
            _logistic, t, y, p0=[b0, L0, k0, t00],
            bounds=(lower, upper), maxfev=20000,
        )
    except Exception as exc:  # noqa: BLE001
        return {"n": int(t.size), "fit_ok": False, "error": str(exc)}
    b, L, k, t0 = (float(v) for v in popt)
    resid = y - _logistic(t, *popt)
    ss_res = float(np.sum(resid**2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else None
    return {
        "n": int(t.size),
        "fit_ok": True,
        "b": b,
        "L": L,
        "k": k,
        "t0": t0,
        "limite_inferior": b,
        "limite_superior": b + L,
        "peak_rate_analytic": abs(L * k / 4),  # unidade de theta por unidade de t
        "r2": r2,
    }


# --------------------------------------------------------------------------
# Normalizacao alometrica (Jaric, 2002)
# --------------------------------------------------------------------------
def allometric_scale(value: float, body_mass_kg: float, b: float) -> float:
    """Escala uma variavel pela massa corporal elevada ao expoente alometrico
    (b=0.67 para forca ~ area de secao; b=1.0 para torque)."""
    return float(value) / (float(body_mass_kg) ** float(b))


# --------------------------------------------------------------------------
# Parametros antropometricos de De Leva (1996) — referencia para CoG
# --------------------------------------------------------------------------
# fracao de massa do segmento e posicao do CoG (fracao do comprimento a partir
# do terminal proximal), media de homens. Fonte: De Leva P. (1996), J Biomech.
DE_LEVA_SEGMENTS = {
    "head_neck": {"mass_frac": 0.0694, "cog_frac": 0.5002},
    "trunk":     {"mass_frac": 0.4346, "cog_frac": 0.4486},
    "upper_arm": {"mass_frac": 0.0271, "cog_frac": 0.5772},
    "forearm_hand": {"mass_frac": 0.0227, "cog_frac": 0.4574},
    "thigh":     {"mass_frac": 0.1416, "cog_frac": 0.4095},
    "shank_foot": {"mass_frac": 0.0616, "cog_frac": 0.4459},
}
