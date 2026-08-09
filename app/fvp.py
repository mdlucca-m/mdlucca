"""
app/fvp.py — Perfil Forca-Velocidade-Potencia (FVP) a partir de TESTE DE CARGAS.

Dado um conjunto de pares (carga, velocidade) medidos em cargas crescentes
(teste incremental), traca:
  * Perfil Carga-Velocidade (LV) — regressao linear v = a + b*carga; estima 1RM
    por extrapolacao (velocidade-alvo, ex. 0.30 m/s — Gonzalez-Badillo).
  * Perfil Forca-Velocidade (FV) — F = F0 - Sfv*v (regressao linear), com a
    FORCA obtida do COMPONENTE GRAVITACIONAL do sistema: F = m*g
    (m = carga + massa corporal em movimento, quando aplicavel).
  * Perfil Potencia-Velocidade (PV) — P(v) = F(v)*v (parabola); Pmax = F0*V0/4
    em v_opt = V0/2, F_opt = F0/2 (Samozino/Jimenez-Reyes; Cross et al. 2017).

Todas as regressoes devolvem a equacao (string), R^2 e os coeficientes.
Referencias:
  Jimenez-Reyes et al. (2017) Front Physiol 7:677.
  Cross, Brughelli, Samozino, Morin (2017) Sports Med 47:1255-1269.
  Gonzalez-Badillo & Sanchez-Medina (2010) Int J Sports Med 31:347-352.
"""
from __future__ import annotations

import numpy as np

G_DEFAULT = 9.81


def _linreg(x, y) -> dict:
    """Regressao linear y = slope*x + intercept + R^2 (minimos quadrados)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.size < 2:
        raise ValueError("regressao exige >= 2 pontos")
    slope, intercept = np.polyfit(x, y, 1)
    yhat = slope * x + intercept
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"slope": float(slope), "intercept": float(intercept), "r2": float(r2)}


def load_velocity_profile(loads_kg, velocities, v1rm: float = 0.30) -> dict:
    """Perfil Carga-Velocidade: v = a + b*carga. Estima 1RM a v=v1rm e v=0."""
    r = _linreg(loads_kg, velocities)      # v = b*carga + a
    b, a = r["slope"], r["intercept"]
    load_at_v1rm = (v1rm - a) / b if b != 0 else None      # 1RM pratico (VBT)
    load_at_v0 = (0.0 - a) / b if b != 0 else None          # 1RM teorico (v=0)
    return {
        "slope_b": round(b, 5), "intercept_a": round(a, 4), "r2": round(r["r2"], 4),
        "equation": f"v = {a:.3f} {b:+.4f}·carga",
        "v1rm_alvo_m_s": v1rm,
        "carga_1RM_estimada_kg": round(load_at_v1rm, 1) if load_at_v1rm else None,
        "carga_1RM_teorica_v0_kg": round(load_at_v0, 1) if load_at_v0 else None,
    }


def force_velocity_profile(loads_kg, velocities, g: float = G_DEFAULT,
                           bodyweight_kg: float = 0.0) -> dict:
    """Perfil Forca-Velocidade a partir do componente gravitacional (F=m*g)."""
    loads = np.asarray(loads_kg, float)
    vel = np.asarray(velocities, float)
    moving_mass = loads + float(bodyweight_kg or 0.0)
    force = moving_mass * g                 # componente gravitacional (N)

    r = _linreg(vel, force)                 # F = slope*v + intercept
    slope, intercept = r["slope"], r["intercept"]
    F0 = intercept                          # forca teorica a v=0 (N)
    Sfv = -slope                            # inclinacao do perfil F-v (N/(m/s))
    V0 = F0 / Sfv if Sfv > 0 else float("nan")   # velocidade teorica a F=0 (m/s)
    Pmax = F0 * V0 / 4.0 if np.isfinite(V0) else float("nan")
    v_opt = V0 / 2.0 if np.isfinite(V0) else float("nan")
    F_opt = F0 / 2.0
    load_opt = F_opt / g - float(bodyweight_kg or 0.0)   # carga otima (kg)

    return {
        "forca": {"unidade": "N", "eixo": "componente gravitacional m*g"},
        "F0_N": round(F0, 1), "V0_m_s": round(V0, 3) if np.isfinite(V0) else None,
        "Sfv_N_por_m_s": round(Sfv, 1), "r2": round(r["r2"], 4),
        "equation_fv": f"F = {F0:.1f} - {Sfv:.1f}·v",
        "Pmax_W": round(Pmax, 1) if np.isfinite(Pmax) else None,
        "v_otima_m_s": round(v_opt, 3) if np.isfinite(v_opt) else None,
        "F_otima_N": round(F_opt, 1),
        "carga_otima_kg": round(load_opt, 1),
        "equation_pv": f"P = {F0:.1f}·v - {Sfv:.1f}·v²",
    }


def _poly2_r2(x, y) -> dict:
    """Ajuste quadratico y = c2*x^2 + c1*x + c0 + R^2 (comparacao de modelos)."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if x.size < 3:
        return {"disponivel": False, "nota": "precisa de >= 3 pontos"}
    c2, c1, c0 = np.polyfit(x, y, 2)
    yhat = c2 * x ** 2 + c1 * x + c0
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - np.mean(y)) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return {"disponivel": True, "c2": round(float(c2), 4), "c1": round(float(c1), 4),
            "c0": round(float(c0), 2), "r2": round(float(r2), 4),
            "equation": f"F = {c2:.2f}·v² {c1:+.1f}·v {c0:+.1f}"}


def allometric_adjustments(F0: float, Pmax: float, bodyweight_kg: float) -> dict:
    """Ajustes alometricos/relativos (Jaric 2002): normaliza F0 e Pmax pela massa."""
    if not bodyweight_kg or bodyweight_kg <= 0:
        return {"disponivel": False,
                "nota": "informe massa_corporal_kg para valores relativos/alometricos"}
    bw = float(bodyweight_kg)
    return {
        "disponivel": True, "massa_kg": bw,
        "F0_por_kg_N": round(F0 / bw, 2),                    # N/kg
        "Pmax_por_kg_W": round(Pmax / bw, 2) if Pmax else None,   # W/kg (ratio std)
        "Pmax_alometrico_W_kg067": round(Pmax / bw ** 0.667, 2) if Pmax else None,
        "nota": "Expoente alometrico 0.667 (~massa^2/3) remove o vies do tamanho "
                "corporal na potencia (Jaric 2002).",
    }


def interpret(fv: dict, lv: dict) -> dict:
    """Leitura pratica do perfil (orientacao forca vs velocidade, ajuste)."""
    sfv = fv.get("Sfv_N_por_m_s") or 0.0
    r2 = fv.get("r2") or 0.0
    qualidade = ("otimo" if r2 >= 0.95 else "bom" if r2 >= 0.90
                 else "fraco (adicione mais cargas)")
    # orientacao qualitativa pela inclinacao relativa F0/V0
    v0 = fv.get("V0_m_s") or 1.0
    f0 = fv.get("F0_N") or 1.0
    ratio = (f0 / v0) if v0 else 0.0
    orient = ("perfil orientado a FORCA" if ratio > 900
              else "perfil orientado a VELOCIDADE" if ratio < 500
              else "perfil equilibrado")
    return {
        "qualidade_ajuste": qualidade,
        "orientacao": orient,
        "inclinacao_Sfv": round(sfv, 1),
        "nota": "Orientacao qualitativa (F0/V0). Para desequilibrio F-v absoluto "
                "(FVimb% vs perfil otimo), e preciso o modelo balistico do gesto "
                "(Samozino) com distancia de push-off.",
        "carga_1RM_estimada_kg": lv.get("carga_1RM_estimada_kg"),
    }


def energy_equivalents(points, fv: dict, g: float, com_displacement_m: float,
                       bodyweight_kg: float = 0.0) -> dict:
    """Equivalentes de energia/trabalho a partir do deslocamento do centro de massa.

    Trabalho gravitacional por carga:  W = F·d = m·g·d  (J).
    Energia potencial ganha:           Ep = m·g·Δh  (= W quando d = Δh vertical).
    Altura equivalente de salto:        h = v²/(2g)  (balistica).
    """
    d = float(com_displacement_m)
    if d <= 0:
        return {"disponivel": False,
                "nota": "informe com_displacement_m (deslocamento vertical do "
                        "centro de massa, em metros) para os equivalentes"}
    works = [round(p["forca_grav_N"] * d, 1) for p in points]      # J por carga
    V0 = fv.get("V0_m_s") or 0.0
    v_opt = fv.get("v_otima_m_s") or 0.0
    F_opt = fv.get("F_otima_N") or 0.0
    out = {
        "disponivel": True,
        "deslocamento_com_m": round(d, 3),
        "trabalho_por_carga_J": works,
        "trabalho_medio_J": round(sum(works) / len(works), 1) if works else None,
        "trabalho_carga_otima_J": round(F_opt * d, 1),
        "potencia_media_carga_otima_W": round(F_opt * v_opt, 1),
        "altura_equivalente_V0_m": round(V0 ** 2 / (2 * g), 3),
        "altura_equivalente_vopt_m": round(v_opt ** 2 / (2 * g), 3),
        "nota": "W=m·g·d (trabalho gravitacional); h=v²/2g (altura equivalente de salto).",
    }
    if bodyweight_kg and bodyweight_kg > 0:
        out["F0_em_pesos_corporais"] = round((fv.get("F0_N") or 0.0)
                                             / (bodyweight_kg * g), 2)
    return out


def full_profile(loads_kg, velocities, g: float = G_DEFAULT,
                 bodyweight_kg: float = 0.0, v1rm: float = 0.30,
                 com_displacement_m: float = 0.0) -> dict:
    """Perfil completo LV + FV + PV + ajustes a partir de um teste de cargas."""
    loads = [float(x) for x in loads_kg]
    vel = [float(x) for x in velocities]
    if len(loads) != len(vel):
        raise ValueError("loads_kg e velocities precisam ter o mesmo tamanho")
    if len(loads) < 2:
        raise ValueError("teste de cargas exige >= 2 cargas diferentes")

    bw = float(bodyweight_kg or 0.0)
    lv = load_velocity_profile(loads, vel, v1rm=v1rm)
    fv = force_velocity_profile(loads, vel, g=g, bodyweight_kg=bw)
    d = float(com_displacement_m or 0.0)
    points = [{"carga_kg": round(l, 1), "velocidade_m_s": round(v, 3),
               "forca_grav_N": round((l + bw) * g, 1),
               **({"trabalho_J": round((l + bw) * g * d, 1)} if d > 0 else {})}
              for l, v in sorted(zip(loads, vel))]
    forces = [(l + bw) * g for l, v in sorted(zip(loads, vel))]
    vsorted = [v for l, v in sorted(zip(loads, vel))]
    return {
        "n_pontos": len(loads),
        "g": g, "massa_corporal_kg": bw,
        "componente_gravitacional": {
            "formula": "F = m·g  (m = carga + massa corporal em movimento)",
            "g_m_s2": g,
            "nota": "A forca do eixo F-v e o peso do sistema (m·g). Para gestos "
                    "que movem o corpo (salto/agacho) informe massa_corporal_kg.",
        },
        "pontos": points,
        "perfil_carga_velocidade": lv,
        "perfil_forca_velocidade": fv,
        "ajuste_quadratico_fv": _poly2_r2(vsorted, forces),
        "ajustes_alometricos": allometric_adjustments(
            fv["F0_N"], fv["Pmax_W"] or 0.0, bw),
        "equivalentes": energy_equivalents(points, fv, g, d, bodyweight_kg=bw),
        "interpretacao": interpret(fv, lv),
        "equacoes_regressao": [lv["equation"], fv["equation_fv"], fv["equation_pv"]],
    }
