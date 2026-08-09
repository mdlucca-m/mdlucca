"""
app/branding.py — identidade visual configuravel (white-label).

Cada licenciado roda o produto com a MARCA dele. A marca vem de (nesta ordem,
o ultimo vence): defaults -> config/brand.json -> variavel MDLUCCA_BRAND (JSON)
-> campo 'brand' da licenca (se presente, trava o nome no que foi licenciado).

Campos: name, tagline, primary, accent, logo_url, site, contact.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from app import licensing as Lic

_ROOT = Path(__file__).resolve().parents[1]

DEFAULT = {
    "name": "De Lucca Esporte",
    "tagline": "análise biomecânica",
    "primary": "#2a9d8f",
    "accent": "#e63946",
    "logo_url": None,
    "site": "",
    "contact": "",
}


def _load_file() -> dict:
    p = _ROOT / "config" / "brand.json"
    if p.is_file():
        try:
            return json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _load_env() -> dict:
    raw = os.environ.get("MDLUCCA_BRAND")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return {}


def brand() -> dict:
    b = dict(DEFAULT)
    b.update({k: v for k, v in _load_file().items() if v is not None})
    b.update({k: v for k, v in _load_env().items() if v is not None})
    lic = Lic.status()
    if lic.get("valid") and lic.get("brand"):
        b["name"] = lic["brand"]           # a licenca trava a marca licenciada
    return b


def name() -> str:
    return brand()["name"]
