"""
app/biomech.py

Analises biomecanicas profundas recomputadas a partir das SERIES BRUTAS
(nao dos escalares pre-calculados). Cada funcao usa metodos numericos
explicitos (app.signals): integracao trapezoidal, diferenciacao suavizada,
deteccao de onset. Entram arrays + constantes da sessao, saem dicts.

Convencao de unidades: forca [N], velocidade [m/s], potencia [W],
angulo [graus], velocidade angular [graus/s], torque [N.m], tempo [s].
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from app import signals as S

DEG2RAD = S.DEG2RAD


# --------------------------------------------------------------------------
# Impulso e trabalho mecanico
# --------------------------------------------------------------------------
def impulse_work(force, speed, power, t, mass_kg: float, g: float = 9.81) -> dict:
    """Impulso (bruto e liquido) e trabalho mecanico por integracao."""
    f = S.as_array(force)
    tt = S.as_array(t)
    weight = mass_kg * g
    impulse_total = S.integrate(f, tt)
    impulse_net = S.integrate(f - weight, tt)
    work_power = S.integrate(power, tt)
    work_fv = S.integrate(f * S.as_array(speed), tt)
    w_pos, w_neg = S.positive_negative_work(power, tt)
    return {
        "impulse_total_Ns": round(impulse_total, 2),
        "impulse_net_Ns": round(impulse_net, 2),
        "work_from_power_J": round(work_power, 2),
        "work_from_Fv_J": round(work_fv, 2),
        "work_positive_J": round(w_pos, 2),
        "work_negative_J": round(w_neg, 2),
        "duration_s": round(float(tt[-1] - tt[0]), 3),
    }


def efficiency(power, height, t, mass_kg: float, g: float = 9.81) -> dict:
    """Eficiencia energetica = energia potencial minima (m*g*dh) / trabalho
    positivo real. dh = excursao vertical da barra na janela."""
    h = S.as_array(height)
    dh = float(np.max(h) - np.min(h))
    pe = mass_kg * g * dh
    w_pos, _ = S.positive_negative_work(power, t)
    eff = 100.0 * pe / w_pos if w_pos > 0 else None
    return {
        "delta_h_m": round(dh, 3),
        "PE_theoretical_J": round(pe, 2),
        "W_positive_J": round(w_pos, 2),
        "efficiency_pct": round(eff, 1) if eff is not None else None,
    }


# --------------------------------------------------------------------------
# RFD de pico + TDF em janelas fixas (padrao-ouro em forca explosiva)
# --------------------------------------------------------------------------
def rfd_tdf(force, t, windows_ms=(50, 100, 150, 200), smooth_window: int = 11,
           onset_index: int | None = None) -> dict:
    """RFD de pico + TDF em janelas fixas a partir do onset. Se onset_index
    for dado (ex.: fundo do movimento / inicio da fase concentrica), usa-o;
    senao detecta pelo limiar de forca (baseline + k*sd)."""
    f = S.as_array(force)
    tt = S.as_array(t)
    dfdt = S.derivative(f, tt, smooth_window=smooth_window)
    onset = onset_index if onset_index is not None else S.find_onset(f, tt)
    t0, f0 = float(tt[onset]), float(f[onset])
    out = {
        "onset_index": onset,
        "t_onset_s": round(t0, 3),
        "F_onset_N": round(f0, 1),
        "RFD_peak_Ns": round(float(np.max(dfdt)), 1),
        "t_RFD_peak_s": round(float(tt[int(np.argmax(dfdt))]), 3),
        "windows": {},
    }
    for w in windows_ms:
        tw = t0 + w / 1000.0
        if tw > tt[-1]:
            out["windows"][f"{w}ms"] = None
            continue
        j = int(np.searchsorted(tt, tw))
        j = min(j, f.size - 1)
        dt = float(tt[j] - t0) or 1e-9
        tdf = (float(f[j]) - f0) / dt
        impulse = S.integrate(f[onset:j + 1] - f0, tt[onset:j + 1])
        out["windows"][f"{w}ms"] = {"TDF_Ns": round(tdf, 1), "impulse_Ns": round(impulse, 2)}
    return out


# --------------------------------------------------------------------------
# Velocidade propulsiva (MPV/PPV/MCV) — Sanchez-Medina & Gonzalez-Badillo
# --------------------------------------------------------------------------
def velocity_metrics(velocity, tangential_accel, t, g: float = 9.81) -> dict:
    """MPV = velocidade media enquanto a aceleracao tangencial e >= -g (fase
    propulsiva). MCV = media na fase concentrica (v>0). PPV = pico."""
    v = S.as_array(velocity)
    a = S.as_array(tangential_accel)
    conc = v > 0
    prop = conc & (a >= -g)
    ppv = float(np.max(v)) if v.size else None
    mcv = float(np.mean(v[conc])) if conc.any() else None
    mpv = float(np.mean(v[prop])) if prop.any() else None
    pct_prop = 100.0 * prop.sum() / conc.sum() if conc.any() else None
    return {
        "MPV_ms": round(mpv, 3) if mpv is not None else None,
        "MCV_ms": round(mcv, 3) if mcv is not None else None,
        "PPV_ms": round(ppv, 3) if ppv is not None else None,
        "pct_propulsive": round(float(pct_prop), 1) if pct_prop is not None else None,
    }


def ballistic(tangential_accel, force, t) -> dict:
    """Decompoe a fase em aceleracao (a>0, propulsiva) vs frenagem (a<0)."""
    a = S.as_array(tangential_accel)
    f = S.as_array(force)
    tt = S.as_array(t)
    acc = a > 0
    brk = a < 0
    n = a.size or 1
    imp_prop = S.integrate(np.where(acc, f, 0.0), tt)
    imp_brake = S.integrate(np.where(brk, f, 0.0), tt)
    return {
        "pct_time_accelerating": round(float(100.0 * acc.sum() / n), 1),
        "pct_time_braking": round(float(100.0 * brk.sum() / n), 1),
        "impulse_propulsive_Ns": round(imp_prop, 1),
        "impulse_braking_Ns": round(imp_brake, 1),
        "ratio_prop_brake": round(imp_prop / imp_brake, 2) if imp_brake else None,
    }


# --------------------------------------------------------------------------
# Jerk (3a derivada) com suavizacao reforcada
# --------------------------------------------------------------------------
def jerk(accel, t, smooth_window: int = 21) -> dict:
    """Jerk = d(aceleracao)/dt. A 3a derivada herda ruido das anteriores;
    por isso usa-se janela de suavizacao maior."""
    a = S.as_array(accel)
    tt = S.as_array(t)
    j = S.derivative(a, tt, smooth_window=smooth_window)
    return {
        "jerk_peak": round(float(np.max(np.abs(j))), 2),
        "jerk_rms": round(float(np.sqrt(np.mean(j ** 2))), 2),
        "a_peak": round(float(np.max(np.abs(a))), 2),
        "smooth_window": smooth_window,
    }


# --------------------------------------------------------------------------
# Potencia articular = torque x velocidade angular (fluxo de energia)
# --------------------------------------------------------------------------
def joint_power(torque, angvel_deg, t) -> dict:
    """P_joint [W] = torque [N.m] x velocidade angular [rad/s]. Positivo =
    concentrico (gera energia), negativo = excentrico (absorve)."""
    tau = S.as_array(torque)
    w = S.as_array(angvel_deg) * DEG2RAD
    p = tau * w
    tt = S.as_array(t)
    w_pos, w_neg = S.positive_negative_work(p, tt)
    pos = p > 0
    return {
        "peak_pos_W": round(float(np.max(p)), 1),
        "peak_neg_W": round(float(np.min(p)), 1),
        "work_pos_J": round(w_pos, 1),
        "work_neg_J": round(w_neg, 1),
        "pct_concentric": round(float(100.0 * pos.sum() / (p.size or 1)), 1),
    }


# --------------------------------------------------------------------------
# Ciclo alongamento-encurtamento (SSC) + RSI modificado
# --------------------------------------------------------------------------
def ssc(angle, angvel_deg, velocity, t, thr_frac: float = 0.2) -> dict:
    """Tempo de amortizacao = do fundo (min angulo) ate atingir thr_frac do
    pico de velocidade angular concentrica. RSI-mod = v_linear_pico / t_amort."""
    ang = S.as_array(angle)
    w = S.as_array(angvel_deg)
    v = S.as_array(velocity)
    tt = S.as_array(t)
    bottom = int(np.argmin(ang))
    w_conc = w[bottom:]
    if w_conc.size < 2:
        return {"error": "janela concentrica curta"}
    peak_ang = float(np.max(w_conc))
    peak_idx = bottom + int(np.argmax(w_conc))
    thr = thr_frac * peak_ang
    rel = np.argmax(w[bottom:] >= thr)
    t_amort = float(tt[bottom + int(rel)] - tt[bottom])
    v_peak_conc = float(np.max(v[bottom:])) if v[bottom:].size else 0.0
    rsi = v_peak_conc / t_amort if t_amort > 0 else None
    return {
        "t_bottom_s": round(float(tt[bottom]), 3),
        "t_amortization_ms": round(t_amort * 1000, 1),
        "peak_concentric_angvel": round(peak_ang, 1),
        "t_peak_angvel_s": round(float(tt[peak_idx]), 3),
        "v_peak_concentric": round(v_peak_conc, 3),
        "rsi_modified": round(rsi, 2) if rsi is not None else None,
    }


# --------------------------------------------------------------------------
# Sequenciamento cinetico: ordem dos picos de velocidade angular
# --------------------------------------------------------------------------
def sequencing(angvel_by_joint: dict, t, window: tuple[int, int] | None = None) -> dict:
    """Recebe {joint: serie_angvel}. Retorna a ordem temporal dos picos na
    janela (default: janela toda). Padrao esperado na subida: proximal->distal."""
    tt = S.as_array(t)
    lo, hi = window or (0, tt.size - 1)
    events = []
    for joint, series in angvel_by_joint.items():
        w = S.as_array(series)[lo:hi + 1]
        if w.size == 0:
            continue
        i = int(np.argmax(w))
        events.append({"joint": joint, "t_peak_s": round(float(tt[lo + i]), 3),
                       "peak_angvel": round(float(w[i]), 1)})
    events.sort(key=lambda e: e["t_peak_s"])
    return {"order": [e["joint"] for e in events], "events": events}


def normalized_cycle(series, n: int = 101) -> list[float]:
    return [round(float(x), 4) for x in S.resample_cycle(series, n)]
