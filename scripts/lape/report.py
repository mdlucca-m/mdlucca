"""Geracao do painel HTML autocontido do LAPE.

O arquivo final nao depende de rede: CSS, JavaScript e dados vao embutidos,
o que permite abrir o painel offline, enviar por e-mail ou publicar no
GitHub Pages sem nenhuma configuracao adicional.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import config

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
HTML_TEMPLATE = TEMPLATE_DIR / "dashboard.html"
JS_TEMPLATE = TEMPLATE_DIR / "dashboard.js"


def load_basemap(geo_dir: Path = config.GEO_DIR) -> list[list[list[float]]]:
    """Carrega contornos opcionais para o mapa (data/geo/*.geojson).

    Espera GeoJSON com Polygon/MultiPolygon em coordenadas [lon, lat].
    Sem arquivo, o mapa e desenhado apenas com a grade de coordenadas.
    """
    rings: list[list[list[float]]] = []
    if not geo_dir.exists():
        return rings
    for path in sorted(geo_dir.glob("*.geojson")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        features = data.get("features", [data])
        for feature in features:
            geometry = feature.get("geometry", feature) or {}
            kind, coords = geometry.get("type"), geometry.get("coordinates")
            if kind == "Polygon":
                rings.extend(coords)
            elif kind == "MultiPolygon":
                for polygon in coords:
                    rings.extend(polygon)
    return [[[float(x), float(y)] for x, y in ring] for ring in rings if len(ring) > 2]


def to_json(payload: dict[str, Any]) -> str:
    """Serializa o payload de forma segura para embutir em <script>."""
    text = json.dumps(payload, ensure_ascii=False, default=str, separators=(",", ":"))
    # impede que qualquer texto vindo dos dados feche a tag <script>
    return text.replace("</", "<\\/")


def render(payload: dict[str, Any], output: Path = config.REPORT_PATH,
           geo_dir: Path = config.GEO_DIR) -> Path:
    payload = dict(payload)
    payload["geo"] = load_basemap(geo_dir)

    html = HTML_TEMPLATE.read_text(encoding="utf-8")
    script = JS_TEMPLATE.read_text(encoding="utf-8")
    title = f"{payload['overview']['lab_name']} — Painel de indicadores"

    html = html.replace("__TITLE__", title)
    html = html.replace("__SCRIPT__", script)
    html = html.replace("__DATA__", to_json(payload))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return output


def export_json(payload: dict[str, Any], output: Path) -> Path:
    """Exporta o payload cru, usado pela API e por integracoes externas."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                      encoding="utf-8")
    return output
