"""
app/segments.py

Vocabulario de SEGMENTOS corporais e ARTICULACOES (indices BlazePose), com um
seletor. Permite escolher o que incluir na analise/desenho — com ou sem bracos,
quais pontos anatomicos — de forma consistente entre a API e os renders.
"""
from __future__ import annotations

# indice -> nome do ponto anatomico (BlazePose 33)
LANDMARKS = {
    0: "nariz", 7: "orelha_E", 8: "orelha_D", 11: "ombro_E", 12: "ombro_D",
    13: "cotovelo_E", 14: "cotovelo_D", 15: "punho_E", 16: "punho_D",
    19: "indicador_E", 20: "indicador_D", 23: "quadril_E", 24: "quadril_D",
    25: "joelho_E", 26: "joelho_D", 27: "tornozelo_E", 28: "tornozelo_D",
    31: "pe_E", 32: "pe_D",
}

# segmento -> ossos (pares de indices), pontos e rotulo
SEGMENTS = {
    "cabeca": {"bones": [(0, 7), (0, 8)], "points": [0, 7, 8], "label": "cabeca/pescoco"},
    "tronco": {"bones": [(11, 12), (11, 23), (12, 24), (23, 24)],
               "points": [11, 12, 23, 24], "label": "tronco"},
    "braco_E": {"bones": [(11, 13), (13, 15), (15, 19)], "points": [13, 15, 19], "label": "braco esquerdo"},
    "braco_D": {"bones": [(12, 14), (14, 16), (16, 20)], "points": [14, 16, 20], "label": "braco direito"},
    "perna_E": {"bones": [(23, 25), (25, 27), (27, 31)], "points": [25, 27, 31], "label": "perna esquerda"},
    "perna_D": {"bones": [(24, 26), (26, 28), (28, 32)], "points": [26, 28, 32], "label": "perna direita"},
}

# grupos convenientes
GROUPS = {
    "all": list(SEGMENTS),
    "sem_bracos": ["cabeca", "tronco", "perna_E", "perna_D"],
    "pernas": ["tronco", "perna_E", "perna_D"],
    "bracos": ["braco_E", "braco_D", "tronco"],
    "membros_inferiores": ["perna_E", "perna_D"],
    "membros_superiores": ["braco_E", "braco_D"],
}

# articulacao -> (proximal, vertice, distal) para angulo, e segmento dono
JOINTS = {
    "joelho_E": {"triplet": (23, 25, 27), "segment": "perna_E"},
    "joelho_D": {"triplet": (24, 26, 28), "segment": "perna_D"},
    "quadril_E": {"triplet": (11, 23, 25), "segment": "perna_E"},
    "quadril_D": {"triplet": (12, 24, 26), "segment": "perna_D"},
    "tornozelo_E": {"triplet": (25, 27, 31), "segment": "perna_E"},
    "tornozelo_D": {"triplet": (26, 28, 32), "segment": "perna_D"},
    "cotovelo_E": {"triplet": (11, 13, 15), "segment": "braco_E"},
    "cotovelo_D": {"triplet": (12, 14, 16), "segment": "braco_D"},
    "ombro_E": {"triplet": (13, 11, 23), "segment": "braco_E"},
    "ombro_D": {"triplet": (14, 12, 24), "segment": "braco_D"},
}


def resolve(spec) -> dict:
    """spec: nome de grupo ('sem_bracos'), lista de segmentos, ou 'all'.
    Devolve {segments, bones, points, joints} selecionados."""
    if spec is None:
        names = GROUPS["all"]
    elif isinstance(spec, str):
        if spec in GROUPS:
            names = GROUPS[spec]
        else:  # lista separada por virgula, ou nome unico de segmento
            names = [s.strip() for s in spec.split(",") if s.strip()]
    else:
        names = list(spec)
    names = [n for n in names if n in SEGMENTS]
    if not names:
        names = GROUPS["all"]
    bones, points = [], []
    for n in names:
        bones += SEGMENTS[n]["bones"]
        points += SEGMENTS[n]["points"]
    joints = [j for j, d in JOINTS.items() if d["segment"] in names]
    return {"segments": names, "bones": bones, "points": sorted(set(points)), "joints": joints}


def catalog() -> dict:
    return {
        "landmarks": LANDMARKS,
        "segments": {k: {"label": v["label"], "points": v["points"]} for k, v in SEGMENTS.items()},
        "groups": GROUPS,
        "joints": {k: v["segment"] for k, v in JOINTS.items()},
    }
