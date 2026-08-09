"""
app/calibration.py

Calibracao metrica: converte pixels em metros. Duas fontes, da mais para a
menos confiavel:

  1. reference  — objeto de tamanho conhecido no quadro (regua, barra, marca):
     dois pontos em pixels + comprimento real -> escala exata (m/px).
  2. stature    — estatura real do atleta + extensao vertical da pose em pe:
     escala a partir de nariz->tornozelo em pixels.

Sem calibracao, o backend usa a estimativa pelo tronco (world landmarks), que
e aproximada. Este modulo permite trocar por uma escala confiavel, e todas as
grandezas em metros/cm passam a ter significado fisico real.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Calibration:
    m_per_px: float          # metros por pixel
    source: str              # 'reference' | 'stature' | 'trunk_estimate'
    ground_px: float | None = None   # y do solo em pixels (opcional)
    detail: dict | None = None

    def px_to_m(self, px: float) -> float:
        return float(px) * self.m_per_px

    def height_above_ground_cm(self, y_px: float) -> float | None:
        if self.ground_px is None:
            return None
        return (self.ground_px - float(y_px)) * self.m_per_px * 100.0


def from_reference(p1_px, p2_px, known_length_m: float, ground_px: float | None = None) -> Calibration:
    """Escala a partir de um objeto de comprimento conhecido no quadro."""
    d = float(np.hypot(p2_px[0] - p1_px[0], p2_px[1] - p1_px[1]))
    if d <= 0:
        raise ValueError("os dois pontos de referencia coincidem")
    return Calibration(m_per_px=known_length_m / d, source="reference", ground_px=ground_px,
                       detail={"pixels": round(d, 2), "known_length_m": known_length_m})


def from_stature(nose_px, ankle_px, stature_m: float, ground_px: float | None = None) -> Calibration:
    """Escala a partir da estatura real e da altura da pose (nariz->tornozelo)
    em pixels. stature_m e a altura real do atleta em metros. O fator 0.936
    aproxima a fracao nariz-tornozelo da estatura total (De Leva/antropometria)."""
    d = abs(float(ankle_px[1]) - float(nose_px[1]))
    if d <= 0:
        raise ValueError("extensao vertical nula")
    return Calibration(m_per_px=(stature_m * 0.936) / d, source="stature", ground_px=ground_px,
                       detail={"pixels": round(d, 2), "stature_m": stature_m})


def from_trunk_estimate(trunk_m: float, trunk_px: float, ground_px: float | None = None) -> Calibration:
    """Estimativa atual (fallback): comprimento do tronco em world x pixels."""
    return Calibration(m_per_px=trunk_m / (trunk_px or 1.0), source="trunk_estimate",
                       ground_px=ground_px, detail={"trunk_m": trunk_m, "trunk_px": trunk_px})
