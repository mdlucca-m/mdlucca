"""
app/multicam.py  —  Reconstrucao 3D por MULTIPLAS CAMERAS (scaffold Etapa 3)

Hoje o sistema usa UMA camera (vista sagital) + world landmarks do MediaPipe:
os angulos e velocidades sao medidas diretas, mas a profundidade (eixo Z) e
estimada. Com 2-3 cameras sincronizadas e calibradas, cada ponto do corpo passa
a ser triangulado em 3D metrico verdadeiro (sem assumir plano sagital), o que
melhora forcas/potencias fora do plano e movimentos com rotacao.

Este modulo entrega o nucleo matematico REUTILIZAVEL:
  - Camera: matriz de projecao P (3x4) a partir de intrinsecos K, rotacao R e
    translacao t (P = K [R | t]).
  - triangulate_point: triangulacao linear (DLT) por minimos quadrados a partir
    de N vistas 2D do MESMO ponto.
  - triangulate_landmarks: aplica a triangulacao a um conjunto de landmarks
    (ex.: as 33 juntas do BlazePose) ponderando pela visibilidade.
  - reprojection_error: erro de reprojecao (px) para validar a calibracao.

Referencias:
  Hartley & Zisserman (2004), Multiple View Geometry, cap. 12 (triangulacao).
  Zhang (2000), IEEE TPAMI 22(11):1330-1334 (calibracao por tabuleiro).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Sequence

import numpy as np


# --------------------------------------------------------------------------
# Protocolo de captura recomendado (3 cameras)
# --------------------------------------------------------------------------
CAPTURE_PROTOCOL = {
    "cameras": 3,
    "arranjo": "≈120° entre si ao redor do atleta (frontal, oblíqua, lateral); "
               "todas enquadrando o corpo inteiro na fase de maior amplitude.",
    "sincronizacao": "clap/flash comum no início OU timecode; alinhar por evento "
                     "compartilhado no pós (pico de áudio ou frame do flash).",
    "calibracao": "tabuleiro de xadrez (ex.: 9x6, quadrado 25mm) visível em pares "
                  "de câmeras para intrínsecos (Zhang 2000) + extrínsecos por "
                  "pose relativa; escala por objeto de dimensão conhecida.",
    "fps": "≥ 60 fps para explosivos (idealmente 120-240); mesma taxa nas 3.",
    "saida": "por câmera, os landmarks 2D (pixel) por frame + a matriz P; este "
             "módulo tri­angula para 3D métrico e alimenta o mesmo pipeline "
             "(kinematics/biomech) já existente.",
}


@dataclass
class Camera:
    """Camera pinhole com matriz de projecao P (3x4), mapeando X (mundo, 3D
    homogeneo) -> x (imagem, 2D homogeneo): x ~ P X."""
    P: np.ndarray  # (3,4)
    name: str = ""

    @classmethod
    def from_krt(cls, K: np.ndarray, R: np.ndarray, t: np.ndarray,
                 name: str = "") -> "Camera":
        """Constroi P = K [R | t] a partir dos intrinsecos K (3x3), rotacao R
        (3x3) e translacao t (3,)."""
        K = np.asarray(K, float).reshape(3, 3)
        R = np.asarray(R, float).reshape(3, 3)
        t = np.asarray(t, float).reshape(3, 1)
        return cls(P=K @ np.hstack([R, t]), name=name)

    def project(self, X: Sequence[float]) -> np.ndarray:
        """Projeta um ponto 3D X=(x,y,z) para pixel (u,v)."""
        Xh = np.array([X[0], X[1], X[2], 1.0])
        x = self.P @ Xh
        return x[:2] / x[2]


def triangulate_point(cameras: Sequence[Camera],
                      points2d: Sequence[Optional[Sequence[float]]],
                      weights: Optional[Sequence[float]] = None) -> Optional[np.ndarray]:
    """Triangulacao linear (DLT) de um ponto 3D a partir de N vistas 2D.

    Cada vista contribui 2 equacoes do sistema A X = 0 (X homogeneo, 4D):
        u (P3·X) - (P1·X) = 0
        v (P3·X) - (P2·X) = 0
    Resolve por SVD (menor valor singular). `points2d[i]` = (u,v) em pixels ou
    None quando a camera i nao viu o ponto. `weights` (ex.: visibilidade 0..1)
    pondera as linhas. Precisa de >= 2 vistas validas; devolve None caso contrario.
    """
    rows = []
    for i, (cam, pt) in enumerate(zip(cameras, points2d)):
        if pt is None:
            continue
        w = 1.0 if weights is None else float(weights[i])
        if w <= 0:
            continue
        u, v = float(pt[0]), float(pt[1])
        P1, P2, P3 = cam.P[0], cam.P[1], cam.P[2]
        rows.append(w * (u * P3 - P1))
        rows.append(w * (v * P3 - P2))
    if len(rows) < 4:  # < 2 vistas validas
        return None
    A = np.asarray(rows, float)
    _, _, Vt = np.linalg.svd(A)
    X = Vt[-1]
    if abs(X[3]) < 1e-12:
        return None
    return X[:3] / X[3]


def reprojection_error(cameras: Sequence[Camera], X: Sequence[float],
                       points2d: Sequence[Optional[Sequence[float]]]) -> float:
    """Erro medio de reprojecao (em pixels) do ponto 3D X nas vistas observadas."""
    errs = []
    for cam, pt in zip(cameras, points2d):
        if pt is None:
            continue
        uv = cam.project(X)
        errs.append(float(np.hypot(uv[0] - pt[0], uv[1] - pt[1])))
    return float(np.mean(errs)) if errs else float("nan")


def triangulate_landmarks(cameras: Sequence[Camera],
                          views: Sequence[Sequence[Optional[Sequence[float]]]],
                          vis: Optional[Sequence[Sequence[float]]] = None) -> list:
    """Triangula um conjunto de landmarks a partir de varias cameras.

    `views[i]` = lista de pontos 2D (u,v) ou None do landmark, por camera i
    (todas as cameras com a MESMA ordem de landmarks). `vis[i]` = visibilidade
    por landmark da camera i (opcional). Devolve lista de pontos 3D (ou None).
    """
    n_cams = len(cameras)
    if n_cams < 2:
        raise ValueError("triangulacao 3D exige >= 2 cameras")
    n_lms = len(views[0])
    out = []
    for k in range(n_lms):
        pts = [views[i][k] if k < len(views[i]) else None for i in range(n_cams)]
        w = None if vis is None else [vis[i][k] if k < len(vis[i]) else 0.0
                                      for i in range(n_cams)]
        out.append(triangulate_point(cameras, pts, w))
    return out
