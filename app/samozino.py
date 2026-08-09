"""
app/samozino.py — Modelo balistico de Samozino (perfil F-V-P de saltos) e
desequilibrio forca-velocidade (FVimb).

Metodo simples de campo (Samozino et al. 2008, J Biomech 41:2940; 2012, MSSE
44:313), a partir de 3 entradas por condicao: massa do sistema, altura do salto
e distancia de push-off (deslocamento vertical do centro de massa na extensao):

    F_media = m·g·(h/hPO + 1)        [N]
    v_media = sqrt(g·h / 2)          [m/s]   (aprox. aceleracao constante)
    P_media = F_media · v_media      [W]

Varias cargas -> regressao linear F-v -> F0, v0, Sfv, Pmax.

Perfil OTIMO e FVimb (Samozino 2012; Jimenez-Reyes et al. 2017, Front Physiol
7:677): no mesmo enquadramento (valores medios / aceleracao constante), a altura
do salto sai da igualdade entre a forca media exigida e a reta F-v:
    m0·g·(h/hPO + 1) = F0 - Sfv·sqrt(g·h/2)
que se resolve para h (quadratica em sqrt(h)) — reproduz exatamente a altura
medida. O perfil otimo e a inclinacao Sfv_opt que MAXIMIZA h para o Pmax e o hPO
do individuo, obtida maximizando essa expressao fechada (nao uma constante de
memoria).

    FVimb (%) = 100 · |1 - Sfv/Sfv_opt|
    Sfv < Sfv_opt -> deficit de FORCA (perfil orientado a velocidade)
    Sfv > Sfv_opt -> deficit de VELOCIDADE (perfil orientado a forca)
"""
from __future__ import annotations

import numpy as np

G_DEFAULT = 9.81


def _linreg(x, y) -> dict:
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2)}


def jump_height(F0: float, Sfv: float, m: float, hPO: float,
                g: float = G_DEFAULT) -> float | None:
    """Altura do salto no modelo de Samozino (media/aceleracao constante).

    Resolve, para h, a igualdade entre a forca media exigida e a reta F-v:
        m·g·(h/hPO + 1) = F0 - Sfv·sqrt(g·h/2)
    Substituindo s = sqrt(h):  (m·g/hPO)·s^2 + Sfv·sqrt(g/2)·s + (m·g - F0) = 0.
    Devolve None se F0 nao vence o peso (F0 <= m·g).
    """
    if F0 <= m * g:
        return None
    A = m * g / hPO
    B = Sfv * float(np.sqrt(g / 2.0))
    C = m * g - F0
    disc = B * B - 4.0 * A * C
    if disc < 0:
        return None
    s = (-B + float(np.sqrt(disc))) / (2.0 * A)
    return s * s if s > 0 else None


def optimal_profile(Pmax: float, m: float, hPO: float,
                    g: float = G_DEFAULT) -> dict:
    """Acha Sfv_opt que maximiza a altura do salto p/ Pmax e hPO dados (numerico).

    Para cada Sfv: F0 = sqrt(4·Pmax·Sfv) (pois Pmax=F0·v0/4 e v0=F0/Sfv),
    exige F0 > m·g. Faz varredura + refino.
    """
    sfv_min = (m * g) ** 2 / (4.0 * Pmax)          # F0 = m g exatamente
    lo, hi = sfv_min * 1.02, sfv_min * 60.0
    best = None
    for _ in range(4):                              # refino sucessivo
        grid = np.linspace(lo, hi, 200)
        vals = []
        for sfv in grid:
            F0 = float(np.sqrt(4.0 * Pmax * sfv))
            h = jump_height(F0, sfv, m, hPO, g)
            vals.append(h if h is not None else -1.0)
        vals = np.asarray(vals)
        k = int(np.argmax(vals))
        best = (float(grid[k]), float(vals[k]))
        lo = grid[max(0, k - 1)]
        hi = grid[min(len(grid) - 1, k + 1)]
    sfv_opt, h_opt = best
    F0_opt = float(np.sqrt(4.0 * Pmax * sfv_opt))
    v0_opt = F0_opt / sfv_opt
    return {"Sfv_opt": sfv_opt, "F0_opt_N": F0_opt, "v0_opt_m_s": v0_opt,
            "altura_otima_m": h_opt}


def profile_from_jumps(masses_kg, jump_heights_m, push_off_m: float,
                       g: float = G_DEFAULT, bodyweight_kg: float | None = None) -> dict:
    """Perfil F-V-P de Samozino a partir de saltos com cargas + FVimb."""
    m = np.asarray(masses_kg, float)
    h = np.asarray(jump_heights_m, float)
    if m.size != h.size:
        raise ValueError("masses_kg e jump_heights_m precisam ter o mesmo tamanho")
    if m.size < 2:
        raise ValueError("precisa de >= 2 condicoes de carga")
    hPO = float(push_off_m)
    if hPO <= 0:
        raise ValueError("push_off_m (distancia de push-off) deve ser > 0")

    F = m * g * (h / hPO + 1.0)         # forca media por condicao (N)
    v = np.sqrt(g * h / 2.0)            # velocidade media (m/s)
    P = F * v                           # potencia media (W)

    reg = _linreg(v, F)                 # F = slope*v + intercept
    F0, Sfv = reg["intercept"], -reg["slope"]
    v0 = F0 / Sfv if Sfv > 0 else float("nan")
    Pmax = F0 * v0 / 4.0 if np.isfinite(v0) else float("nan")

    m0 = float(bodyweight_kg) if bodyweight_kg else float(np.min(m))
    opt = optimal_profile(Pmax, m0, hPO, g) if np.isfinite(Pmax) else None

    out = {
        "metodo": "Samozino (saltos com cargas)",
        "push_off_m": round(hPO, 3), "g": g, "massa_corporal_kg": round(m0, 1),
        "pontos": [{"massa_kg": round(float(mm), 1), "altura_m": round(float(hh), 3),
                    "F_media_N": round(float(ff), 1), "v_media_m_s": round(float(vv), 3),
                    "P_media_W": round(float(pp), 1)}
                   for mm, hh, ff, vv, pp in sorted(zip(m, h, F, v, P))],
        "perfil": {
            "F0_N": round(F0, 1), "v0_m_s": round(v0, 3) if np.isfinite(v0) else None,
            "Sfv_N_por_m_s": round(Sfv, 1), "Pmax_W": round(Pmax, 1) if np.isfinite(Pmax) else None,
            "F0_rel_N_kg": round(F0 / m0, 2), "Pmax_rel_W_kg": round(Pmax / m0, 2),
            "r2": round(reg["r2"], 4),
            "equation_fv": f"F = {F0:.1f} - {Sfv:.1f}·v",
        },
    }
    if opt:
        sfv_opt = opt["Sfv_opt"]
        fvimb = 100.0 * abs(1.0 - Sfv / sfv_opt) if sfv_opt else None
        deficit = ("deficit de forca (perfil orientado a velocidade)" if Sfv < sfv_opt
                   else "deficit de velocidade (perfil orientado a forca)"
                   if Sfv > sfv_opt else "equilibrado")
        h_actual = jump_height(F0, Sfv, m0, hPO, g)
        out["perfil_otimo"] = {
            "Sfv_opt_N_por_m_s": round(sfv_opt, 1),
            "F0_opt_N": round(opt["F0_opt_N"], 1),
            "v0_opt_m_s": round(opt["v0_opt_m_s"], 3),
            "razao_Sfv_atual_sobre_otimo": round(Sfv / sfv_opt, 3) if sfv_opt else None,
        }
        out["FVimb"] = {
            "FVimb_pct": round(fvimb, 1) if fvimb is not None else None,
            "tipo": deficit,
            "altura_atual_m": round(h_actual, 3) if h_actual else None,
            "altura_otima_m": round(opt["altura_otima_m"], 3),
            "ganho_potencial_m": round(opt["altura_otima_m"] - h_actual, 3)
            if (h_actual and opt["altura_otima_m"]) else None,
            "nota": "FVimb = 100·|1 - Sfv/Sfv_opt|. Perfil otimo maximiza a altura "
                    "para o Pmax e a distancia de push-off do individuo (Samozino 2012; "
                    "Jimenez-Reyes 2017).",
        }
    return out
