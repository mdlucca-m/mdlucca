"""
app/phases.py

Deteccao automatica e ROBUSTA das fases concentrica/excentrica ao longo de
TODO o movimento (nao so um ponto de fundo), com as transicoes, e as metricas
do componente elastico (ciclo alongamento-encurtamento) por transicao.

Convencao: no sinal "primario", subir = CONCENTRICA (encurtamento/producao),
descer = EXCENTRICA (alongamento/absorcao). Ex.: altura do CoG, extensao
articular. Robustez: suavizacao + limiar com histerese + fusao de trechos
curtos (< min_dur) para eliminar jitter.
"""
from __future__ import annotations

import numpy as np

from app import signals as S


def _labels(primary, t, smooth_window: int, vmin_frac: float):
    v = S.derivative(primary, t, smooth_window=smooth_window)
    vmax = float(np.nanmax(np.abs(v))) or 1e-9
    thr = vmin_frac * vmax
    lab = np.where(v > thr, "concentrica", np.where(v < -thr, "excentrica", "isometrica"))
    return lab, v


def _runs(lab):
    runs = []
    i0 = 0
    for i in range(1, len(lab) + 1):
        if i == len(lab) or lab[i] != lab[i0]:
            runs.append([lab[i0], i0, i - 1])   # [tipo, i_start, i_end]
            i0 = i
    return runs


def detect_phases(primary, t, smooth_window: int = 9, vmin_frac: float = 0.08,
                  min_dur: float = 0.10) -> dict:
    """Segmenta o movimento em fases e devolve as transicoes."""
    primary = S.interpolate_gaps(S.as_array(primary))
    t = S.as_array(t)
    lab, v = _labels(primary, t, smooth_window, vmin_frac)
    lab = np.array(lab, dtype=object)
    dt = float(np.median(np.diff(t))) if t.size > 1 else 0.033
    min_frames = max(1, int(round(min_dur / dt)))

    # funde trechos curtos no vizinho (elimina jitter) ate estabilizar
    changed = True
    while changed:
        changed = False
        runs = _runs(lab)
        for k, (typ, a, b) in enumerate(runs):
            if (b - a + 1) < min_frames and len(runs) > 1:
                repl = runs[k - 1][0] if k > 0 else runs[k + 1][0]
                lab[a:b + 1] = repl
                changed = True
                break

    runs = _runs(lab)
    phases = [{"type": typ, "i_start": a, "i_end": b,
               "t_start": round(float(t[a]), 3), "t_end": round(float(t[b]), 3),
               "duration_s": round(float(t[b] - t[a]), 3)} for typ, a, b in runs]
    # transicoes: entre fases consecutivas; marca excentrica->concentrica (SSC)
    trans = []
    for p, q in zip(phases[:-1], phases[1:]):
        trans.append({"from": p["type"], "to": q["type"], "t": q["t_start"],
                      "index": q["i_start"], "ssc": p["type"] == "excentrica" and q["type"] == "concentrica"})
    return {"n_frames": int(len(lab)), "dt": round(dt, 4),
            "counts": {k: int(sum(1 for p in phases if p["type"] == k))
                       for k in ("concentrica", "excentrica", "isometrica")},
            "phases": phases, "transitions": trans}


def elastic_metrics(primary, t, phases_result: dict, power=None) -> dict:
    """Componente elastico (SSC) por transicao excentrica->concentrica:
    tempo de acoplamento (amortizacao), trabalho excentrico (absorvido) e
    concentrico (gerado) e a razao de utilizacao elastica (EUR)."""
    t = S.as_array(t)
    phases = phases_result["phases"]
    p = S.interpolate_gaps(S.as_array(power)) if power is not None else None
    results = []
    for k in range(len(phases) - 1):
        ecc = phases[k]
        # encontra a proxima concentrica (pode haver isometrica no meio = amortizacao)
        j = k + 1
        coupling = 0.0
        while j < len(phases) and phases[j]["type"] == "isometrica":
            coupling += phases[j]["duration_s"]; j += 1
        if ecc["type"] != "excentrica" or j >= len(phases) or phases[j]["type"] != "concentrica":
            continue
        con = phases[j]
        rec = {"t_transicao": con["t_start"], "amortizacao_ms": round(coupling * 1000, 1),
               "dur_excentrica_s": ecc["duration_s"], "dur_concentrica_s": con["duration_s"]}
        if p is not None:
            we = S.integrate(p[ecc["i_start"]:ecc["i_end"] + 1], t[ecc["i_start"]:ecc["i_end"] + 1])
            wc = S.integrate(p[con["i_start"]:con["i_end"] + 1], t[con["i_start"]:con["i_end"] + 1])
            rec["trabalho_excentrico_J"] = round(we, 2)
            rec["trabalho_concentrico_J"] = round(wc, 2)
            rec["EUR"] = round(wc / abs(we), 3) if we != 0 else None   # razao de utilizacao elastica
        results.append(rec)
    return {"n_transicoes_ssc": len(results), "transicoes": results,
            "nota": "EUR = trabalho concentrico / |trabalho excentrico|; amortizacao curta + EUR alto = mais reuso elastico."}
