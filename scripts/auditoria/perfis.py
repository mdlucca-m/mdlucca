#!/usr/bin/env python3
"""Auditoria de toda menção a perfil de humor com percentual, em todo
documento do projeto.

Percorre os .docx e os .html disponíveis, extrai parágrafos e células de
tabela, e recorta cada trecho que cite um perfil junto de um número. O objetivo
é localizar a origem de cada valor que circula e apontar as divergências.

    python3 scripts/auditoria/perfis.py
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

PERFIS = ("iceberg", "superfície", "superficie", "submerso", "tubarão",
          "tubarao", "everest", "perturbado", "morgan", "parsons")
NUMERO = re.compile(r"\d{1,3}[,.]\d|\d{1,3}\s*%")


def blocos_docx(caminho: Path):
    """Cada parágrafo e cada linha de tabela, na ordem do documento."""
    raiz = ET.fromstring(zipfile.ZipFile(caminho).read("word/document.xml"))
    corpo = raiz.find(f"{W}body")
    for el in corpo:
        if el.tag == f"{W}p":
            texto = " ".join("".join(t.text or "" for t in el.iter(f"{W}t")).split())
            if texto:
                yield "parágrafo", texto
        elif el.tag == f"{W}tbl":
            for linha in el.iter(f"{W}tr"):
                celulas = [" ".join("".join(t.text or "" for t in c.iter(f"{W}t")).split())
                           for c in linha.iter(f"{W}tc")]
                texto = " | ".join(c for c in celulas if c)
                if texto:
                    yield "tabela", texto


def blocos_html(caminho: Path):
    bruto = caminho.read_text(errors="ignore")
    bruto = re.sub(r"<script.*?</script>", " ", bruto, flags=re.S | re.I)
    bruto = re.sub(r"<style.*?</style>", " ", bruto, flags=re.S | re.I)
    for pedaco in re.split(r"<[^>]+>", bruto):
        texto = " ".join(pedaco.split())
        if texto:
            yield "html", texto


def interessa(texto: str) -> bool:
    plano = texto.lower()
    return any(p in plano for p in PERFIS) and bool(NUMERO.search(texto))


def varrer(caminhos: list[Path]) -> None:
    for caminho in caminhos:
        leitor = blocos_html if caminho.suffix == ".html" else blocos_docx
        try:
            achados = [(t, x) for t, x in leitor(caminho) if interessa(x)]
        except Exception as erro:  # documento ilegível não interrompe a varredura
            print(f"\n### {caminho.name}: não foi possível ler ({erro})")
            continue
        if not achados:
            continue
        print(f"\n{'=' * 78}\n### {caminho.name}  ({len(achados)} trechos)\n{'=' * 78}")
        for tipo, texto in achados:
            print(f"  [{tipo}] {texto[:300]}")


def main() -> int:
    raiz = Path(__file__).resolve().parents[2]
    envios = Path("/root/.claude/uploads/1185cafb-8b56-53ba-b7f5-bdafb0f0a09d")
    caminhos = sorted(raiz.glob("data/*.docx"))
    if envios.is_dir():
        caminhos += sorted(envios.glob("*.docx")) + sorted(envios.glob("*.html"))
    varrer(caminhos)
    return 0


if __name__ == "__main__":
    sys.exit(main())
