"""
app/sources/mediapipe.py

Fonte de pose da Etapa 1: formaliza o caminho atual — dados derivados do
MediaPipe (BlazePose GHUM 3D, monocular) já extraídos do dashboard para
`data/dashboard_extracted.json`. É a implementação de referência da
interface `PoseSource`.
"""
from __future__ import annotations

import json
from pathlib import Path

from app.sources.base import PoseSource

DEFAULT_JSON = Path(__file__).resolve().parents[2] / "data" / "dashboard_extracted.json"


class MediaPipeDashboardSource(PoseSource):
    name = "mediapipe"
    model = "MediaPipe Pose (BlazePose GHUM 3D, monocular)"
    is_calibrated = False
    coordinate_system = "image_normalized"

    def __init__(self, json_path: str | Path = DEFAULT_JSON):
        self.json_path = Path(json_path)

    def bundle(self) -> dict:
        if not self.json_path.exists():
            raise FileNotFoundError(
                f"{self.json_path} nao encontrado. Rode: "
                f"python3 scripts/extract_dashboard.py <HTML> -o {self.json_path}"
            )
        return json.loads(self.json_path.read_text(encoding="utf-8"))
