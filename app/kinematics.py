"""
app/kinematics.py

Motor de cinemática: computa ângulos articulares e centro de gravidade a
partir dos LANDMARKS de pose (não das séries derivadas). É a ponte
"landmarks -> biomecânica" que a Etapa 2 usará: a fonte de pose de alta
qualidade fornece landmarks melhores (3D métricos, calibrados) e este
módulo produz as séries; toda a análise padrão-ouro (app.biomech) segue
por cima, sem mudar.

Nota sobre a Etapa 1: os landmarks do MediaPipe vêm normalizados em [0,1],
com x e y divididos por largura e altura da imagem SEPARADAMENTE — o que
distorce ângulos pelo aspect ratio (não gravado nos dados). `fit_aspect`
recupera esse fator ajustando-o a ângulos de referência. Sob a Etapa 2
(coordenadas métricas reais), esse ajuste desaparece (aspect = 1).
"""
from __future__ import annotations

from typing import Sequence

import numpy as np

from app.analyses import DE_LEVA_SEGMENTS

# Articulacao -> (proximal, vertice, distal) em nomes de landmark.
JOINT_TRIPLETS = {
    "elbow": ("sh", "el", "wr"),
    "knee": ("hip", "kn", "an"),
    "hip": ("sh", "hip", "kn"),
    "shoulder": ("el", "sh", "hip"),
    "wrist": ("el", "wr", "idx_finger"),
}

# Segmentos para CoG (De Leva 1996) a partir dos landmarks disponiveis.
# (proximal, distal, chave em DE_LEVA_SEGMENTS)  — aproximacao 2D unilateral.
COG_SEGMENTS = [
    ("ear", "sh", "head_neck"),
    ("sh", "hip", "trunk"),
    ("sh", "el", "upper_arm"),
    ("el", "wr", "forearm_hand"),
    ("hip", "kn", "thigh"),
    ("kn", "an", "shank_foot"),
]


def _pts(skeleton: dict, key: str, aspect: float) -> np.ndarray:
    """Landmarks (n,2) com y escalado pelo aspect ratio."""
    a = np.asarray(skeleton[key], dtype=float).copy()
    a[:, 1] *= aspect
    return a


def joint_angle(proximal, vertex, distal) -> np.ndarray:
    """Ângulo (graus) no vértice entre os segmentos vértice->proximal e
    vértice->distal, quadro a quadro."""
    p = np.asarray(proximal, float)
    b = np.asarray(vertex, float)
    d = np.asarray(distal, float)
    v1, v2 = p - b, d - b
    cos = (v1 * v2).sum(-1) / (np.linalg.norm(v1, axis=-1) * np.linalg.norm(v2, axis=-1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


def angles_from_landmarks(skeleton: dict, aspect: float = 1.0,
                          joints: Sequence[str] | None = None) -> dict[str, list]:
    """Recomputa as séries angulares de todas as articulações com triplet
    válido no esqueleto."""
    joints = joints or list(JOINT_TRIPLETS)
    out: dict[str, list] = {}
    for j in joints:
        a, b, c = JOINT_TRIPLETS[j]
        if all(k in skeleton for k in (a, b, c)):
            ang = joint_angle(_pts(skeleton, a, aspect), _pts(skeleton, b, aspect),
                              _pts(skeleton, c, aspect))
            out[j] = [round(float(x), 2) for x in ang]
    return out


def fit_aspect(skeleton: dict, reference: dict[str, Sequence[float]],
               lo: float = 1.0, hi: float = 3.0, steps: int = 201) -> dict:
    """Recupera o aspect ratio que melhor reproduz os ângulos de referência
    (RMSE mínimo somado sobre as articulações fornecidas)."""
    grid = np.linspace(lo, hi, steps)
    best_r, best_err = 1.0, np.inf
    for r in grid:
        err = 0.0
        for j, ref in reference.items():
            if j not in JOINT_TRIPLETS:
                continue
            a, b, c = JOINT_TRIPLETS[j]
            if not all(k in skeleton for k in (a, b, c)):
                continue
            ang = joint_angle(_pts(skeleton, a, r), _pts(skeleton, b, r), _pts(skeleton, c, r))
            err += float(np.sqrt(np.mean((ang - np.asarray(ref, float)) ** 2)))
        if err < best_err:
            best_r, best_err = float(r), err
    return {"aspect": round(best_r, 4), "rmse_sum_deg": round(best_err, 3)}


def validate_against(skeleton: dict, reference: dict[str, Sequence[float]],
                     aspect: float) -> dict:
    """Correlação e RMSE das séries recomputadas vs referência, por articulação."""
    rec = angles_from_landmarks(skeleton, aspect, joints=list(reference))
    report = {}
    for j, ref in reference.items():
        if j not in rec:
            continue
        a = np.asarray(rec[j], float)
        b = np.asarray(ref, float)
        corr = float(np.corrcoef(a, b)[0, 1]) if a.std() and b.std() else None
        report[j] = {
            "corr": round(corr, 4) if corr is not None else None,
            "rmse_deg": round(float(np.sqrt(np.mean((a - b) ** 2))), 2),
        }
    return report


def center_of_mass(skeleton: dict, aspect: float = 1.0) -> dict:
    """Trajetória do centro de gravidade (De Leva 1996) a partir dos
    segmentos. Aproximação 2D unilateral — sob a Etapa 2 (3D bilateral)
    torna-se um CoM completo. Retorna séries x,y (normalizadas) e excursões."""
    seg_cogs = []
    weights = []
    for prox, dist, key in COG_SEGMENTS:
        if prox not in skeleton or dist not in skeleton:
            continue
        p = _pts(skeleton, prox, aspect)
        d = _pts(skeleton, dist, aspect)
        frac = DE_LEVA_SEGMENTS[key]["cog_frac"]
        seg_cogs.append(p + frac * (d - p))
        weights.append(DE_LEVA_SEGMENTS[key]["mass_frac"])
    if not seg_cogs:
        return {"error": "landmarks insuficientes"}
    w = np.asarray(weights)
    w = w / w.sum()
    com = np.tensordot(w, np.stack(seg_cogs), axes=(0, 0))  # (n,2)
    x, y = com[:, 0], com[:, 1]
    return {
        "n": int(com.shape[0]),
        "aspect": aspect,
        "x": [round(float(v), 4) for v in x],
        "y": [round(float(v), 4) for v in y],
        "x_excursion": round(float(x.max() - x.min()), 4),
        "y_excursion": round(float(y.max() - y.min()), 4),
        "note": "Aproximacao 2D unilateral (De Leva 1996). Etapa 2 (3D) -> CoM completo.",
    }
