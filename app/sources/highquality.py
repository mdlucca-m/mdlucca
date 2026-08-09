"""
app/sources/highquality.py

STUB da Etapa 2 — fonte de pose de alta qualidade.

Objetivo: substituir a pose monocular do MediaPipe por captura markerless
CALIBRADA (multi-câmera / research-grade) com coordenadas 3D em METROS,
mantendo schema e API intactos. Como o schema já carrega `pose_source`,
basta esta fonte produzir o mesmo bundle canônico a partir dos landmarks
de qualidade superior.

Contrato de entrada esperado (a preencher na Etapa 2):
  * landmarks 3D métricos por frame e por articulação (m), já calibrados;
  * parâmetros de câmera (intrínsecos + extrínsecos) para escala real;
  * opcional: força de reação do solo (força-plataforma) — habilita
    dinâmica inversa completa e o torque de joelho pelo método adequado
    (hoje frágil por falta desse dado);
  * taxa de amostragem real (dispensa a heurística de câmera-lenta).

Como produzir o bundle:
  1. Segmentar a sessão em submovimentos (mesma convenção: ordinal/label).
  2. Para cada submovimento, montar `DATA.efforts[i]` com as SÉRIES
     (t, *_angle, *_angvel, force, power, tau_*, ...). A partir daí, TODAS
     as análises padrão-ouro já são recomputadas pela própria API
     (app.biomech / app.analyses) — não é preciso recalcular escalares aqui.
  3. Preencher `LOADCTX` e devolver o dict.

Enquanto a integração não existe, `bundle()` levanta NotImplementedError
com orientação — de propósito, para não fabricar dados.
"""
from __future__ import annotations

from app.sources.base import PoseSource


class HighQualityPoseSource(PoseSource):
    name = "highquality"
    model = "Markerless calibrado 3D (a definir na Etapa 2)"
    is_calibrated = True
    coordinate_system = "metric_3d"

    def __init__(self, capture_path: str | None = None, camera_calib: dict | None = None):
        self.capture_path = capture_path
        self.camera_calib = camera_calib

    def bundle(self) -> dict:
        raise NotImplementedError(
            "HighQualityPoseSource ainda nao implementada (Etapa 2). Forneca "
            "landmarks 3D metricos calibrados + calibracao de camera e monte o "
            "bundle canonico conforme o docstring deste modulo. Ver README "
            "(secao Roadmap - Etapa 2)."
        )


SOURCES = {
    "mediapipe": "app.sources.mediapipe:MediaPipeDashboardSource",
    "highquality": "app.sources.highquality:HighQualityPoseSource",
}
