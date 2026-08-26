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
CHARTS_TEMPLATE = TEMPLATE_DIR / "charts.js"
THEME_TEMPLATE = TEMPLATE_DIR / "theme.css"


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


def render_html(payload: dict[str, Any], geo_dir: Path = config.GEO_DIR) -> str:
    """Monta o painel completo como string HTML.

    Usado tanto pela exportacao estatica quanto pela rota '/' da API, que
    remonta a pagina a cada acesso com os dados atuais do banco.
    """
    payload = dict(payload)
    payload.setdefault("geo", load_basemap(geo_dir))
    payload.setdefault("session", {"live": False, "user": None})

    html = HTML_TEMPLATE.read_text(encoding="utf-8")
    title = f"{payload['overview']['lab_name']} — Painel de indicadores"

    # A ordem importa: o CSS e a biblioteca de graficos entram antes do
    # dado, e o dado por ultimo, para que nenhum texto vindo do banco
    # possa ser confundido com um marcador do modelo.
    html = html.replace("__TITLE__", title)
    html = html.replace("__THEME_CSS__", THEME_TEMPLATE.read_text(encoding="utf-8"))
    html = html.replace("__CHARTS_JS__", CHARTS_TEMPLATE.read_text(encoding="utf-8"))
    html = html.replace("__SCRIPT__", JS_TEMPLATE.read_text(encoding="utf-8"))
    return html.replace("__DATA__", to_json(payload))


def render(payload: dict[str, Any], output: Path = config.REPORT_PATH,
           geo_dir: Path = config.GEO_DIR) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_html(payload, geo_dir), encoding="utf-8")
    return output


def export_json(payload: dict[str, Any], output: Path) -> Path:
    """Exporta o payload cru, usado pela API e por integracoes externas."""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str),
                      encoding="utf-8")
    return output
