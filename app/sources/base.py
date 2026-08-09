"""
app/sources/base.py

Interface de FONTE DE POSE — o ponto de extensão da Etapa 2.

O `ingest.py` é agnóstico à origem dos dados: ele consome um "bundle"
canônico (o mesmo formato de `data/dashboard_extracted.json`, com as chaves
`DATA`, `MOMENTS`, `LOGISTIC`, ...). Cada fonte de pose implementa
`PoseSource.bundle()` produzindo esse formato, e declara sua qualidade via
`is_calibrated` / `coordinate_system`, que vão para `session.pose_source` e
`session.pose_model` — permitindo comparar MediaPipe × fonte de alta
qualidade lado a lado no mesmo schema.

    Etapa 1 (hoje):  MediaPipeDashboardSource  (pose monocular, não calibrada)
    Etapa 2 (alvo):  HighQualityPoseSource     (3D métrico calibrado)
"""
from __future__ import annotations

import abc


class PoseSource(abc.ABC):
    #: identificador curto gravado em session.pose_source (ex.: 'mediapipe')
    name: str = "abstract"
    #: descrição do modelo gravada em session.pose_model
    model: str = "abstract"
    #: True quando há calibração de câmera / escala métrica real
    is_calibrated: bool = False
    #: 'image_normalized' (pixels/normalizado) ou 'metric_3d' (metros)
    coordinate_system: str = "image_normalized"

    @abc.abstractmethod
    def bundle(self) -> dict:
        """Retorna o bundle canônico consumido pelo ingest (mesmo formato de
        dashboard_extracted.json)."""
        raise NotImplementedError

    def session_overrides(self) -> dict:
        """Campos de `session` que descrevem a proveniência desta fonte."""
        return {
            "pose_source": self.name,
            "pose_model": self.model,
            "is_calibrated": self.is_calibrated,
            "coordinate_system": self.coordinate_system,
        }
