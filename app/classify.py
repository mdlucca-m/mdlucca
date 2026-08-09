"""
app/classify.py — classificacao automatica do padrao de movimento a partir do
angulo primario (quadril), inspirada na biblioteca de movimentos de plataformas
de avaliacao. Heuristica por features (amplitude, nº de ciclos, duracao) com um
grau de confianca honesto.

Padroes: agachamento_forca, agachamento, salto_cmj, pliometrico,
hopping_repetido, levantamento_terra, indefinido.
"""
from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks

from app import signals as S


def classify_movement(hip, t, load_kg: float | None = None,
                      body_mass_kg: float | None = None,
                      exercise_hint: str | None = None) -> dict:
    y = S.savgol(np.asarray(hip, float), window=13)
    tt = np.asarray(t, float)
    rom = float(np.ptp(y))
    # contagem de ciclos por proeminencia (robusto a qualquer amplitude:
    # agachamento grande ou hops pequenos)
    prom = max(3.0, 0.25 * rom)
    bottoms, _ = find_peaks(-y, prominence=prom, distance=4)
    tops, _ = find_peaks(y, prominence=prom, distance=4)
    n = int(max(len(bottoms), len(tops)))
    if len(bottoms) >= 2:
        dur = float(np.mean(np.diff(tt[bottoms])))
    elif tt.size:
        dur = float(tt[-1] - tt[0]) / max(1, n)
    else:
        dur = 0.0
    rel_load = (load_kg / body_mass_kg) if (load_kg and body_mass_kg) else None

    pattern, conf = "indefinido", 0.4
    desc = "Padrão não identificado com confiança suficiente."
    hint = (exercise_hint or "").lower()

    if any(k in hint for k in ("terra", "deadlift")):
        pattern, conf = "levantamento_terra", 0.8
        desc = "Levantamento terra: extensão de quadril dominante a partir do solo."
    elif n >= 3 and dur < 1.3 and rom < 45:
        pattern, conf = "hopping_repetido", 0.82
        desc = "Saltitos reativos repetidos: vários ciclos curtos, baixa amplitude (SSC rápido)."
    elif n >= 2 and dur < 1.6 and rom < 60:
        pattern, conf = "pliometrico", 0.66
        desc = "Padrão pliométrico: ciclos curtos com amortização breve."
    elif rom >= 80 and dur >= 2.2:
        pattern, conf = "agachamento_forca", 0.75
        desc = "Agachamento de força: grande amplitude de quadril, execução lenta."
    elif rom >= 80:
        pattern, conf = "agachamento", 0.7
        desc = "Agachamento: grande amplitude de quadril no ciclo desce-sobe."
    elif 45 <= rom < 80 and n <= 2:
        pattern, conf = "salto_cmj", 0.62
        desc = "Salto com contra-movimento (CMJ): descida rápida e extensão explosiva."

    if rel_load is not None and rel_load >= 0.8 and pattern in ("agachamento", "agachamento_forca"):
        pattern, conf = "agachamento_forca", max(conf, 0.78)
        desc = f"Agachamento de força (carga {rel_load:.0%} do peso corporal)."

    return {"pattern": pattern, "confidence": round(conf, 2), "description": desc,
            "n_ciclos": n, "rom_quadril_graus": round(rom, 1),
            "duracao_ciclo_s": round(dur, 2)}
