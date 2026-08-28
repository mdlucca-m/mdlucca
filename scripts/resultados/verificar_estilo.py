#!/usr/bin/env python3
"""Verifica as restrições de redação pedidas: nenhum travessão e nenhum
gerúndio no texto descritivo.

    python3 scripts/resultados/verificar_estilo.py            # confere o módulo
    python3 scripts/resultados/verificar_estilo.py doc.docx   # confere o .docx
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

TRAVESSOES = {"—": "travessão (—)", "–": "traço de meia risca (–)"}

# Palavras terminadas em -ndo que não são gerúndio.
NAO_GERUNDIO = {
    "quando", "mundo", "segundo", "fundo", "profundo", "redondo", "estupendo",
    "tremendo", "horrendo", "reverendo", "comando", "bando", "grando",
    "orlando", "fernando", "armando", "rotundo", "oriundo", "moribundo",
    "furibundo", "nefando", "educando", "doutorando", "mestrando",
    "graduando", "somando",
}
GERUNDIO = re.compile(r"\b\w*?[aeiouáéíóúâêôãõ]ndo\b", re.IGNORECASE)


def achar_gerundios(texto: str) -> list[str]:
    achados = []
    for m in GERUNDIO.finditer(texto):
        p = m.group(0).lower()
        if p in NAO_GERUNDIO:
            continue
        # gerúndio verbal termina em -ando, -endo ou -indo
        if p.endswith(("ando", "endo", "indo")):
            achados.append(m.group(0))
    return achados


def texto_do_docx(caminho: Path) -> str:
    import zipfile
    from xml.etree import ElementTree as ET
    W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    z = zipfile.ZipFile(caminho)
    raiz = ET.fromstring(z.read("word/document.xml"))
    return "\n".join(
        " ".join("".join(t.text or "" for t in el.iter(f"{W}t")).split())
        for el in raiz.find(f"{W}body") if el.tag == f"{W}p")


def texto_do_modulo() -> str:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import conteudo
    partes = [conteudo.TITULO, conteudo.SUBTITULO]
    for s in conteudo.SECOES:
        partes.append(s["titulo"])
        partes += s.get("paragrafos", []) + s.get("pos_tabela", [])
        if "legenda_figura" in s:
            partes.append(s["legenda_figura"])
    for t in conteudo.TABELAS.values():
        partes += [t["titulo"], t["nota"]]
        partes += [c for linha in t["linhas"] for c in linha]
        partes += t["cabecalho"]
    return "\n".join(partes)


def main() -> int:
    if len(sys.argv) > 1:
        alvo = Path(sys.argv[1])
        texto = texto_do_docx(alvo)
        rotulo = alvo.name
    else:
        texto = texto_do_modulo()
        rotulo = "conteudo.py"

    print(f"── verificação de estilo: {rotulo} ──")
    falhas = 0

    for simbolo, nome in TRAVESSOES.items():
        ocorrencias = texto.count(simbolo)
        # O sinal de menos unicode (−) é permitido em números negativos.
        if simbolo == "–":
            ocorrencias = len(re.findall(r"(?<!\d)–(?!\d)", texto))
        ok = ocorrencias == 0
        falhas += 0 if ok else 1
        print(f'  {"✓" if ok else "✗"} sem {nome}: {ocorrencias} ocorrência(s)')
        if not ok:
            for m in list(re.finditer(rf"[^\n]{{0,55}}{simbolo}[^\n]{{0,55}}", texto))[:4]:
                print(f"        …{m.group(0).strip()}…")

    gerundios = achar_gerundios(texto)
    ok = not gerundios
    falhas += 0 if ok else 1
    print(f'  {"✓" if ok else "✗"} sem gerúndio: {len(gerundios)} ocorrência(s)')
    for g in dict.fromkeys(gerundios[:12]):
        m = re.search(rf"[^\n]{{0,60}}\b{re.escape(g)}\b[^\n]{{0,60}}", texto)
        print(f'        "{g}"  em: …{m.group(0).strip() if m else ""}…')

    palavras = len(texto.split())
    print(f"\n  {palavras} palavras verificadas")
    print(f"\n{'OK: estilo conforme' if not falhas else f'FALHOU: {falhas} restrição(ões)'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
