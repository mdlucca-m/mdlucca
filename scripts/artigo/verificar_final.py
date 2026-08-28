#!/usr/bin/env python3
"""Verifica que a versão corrigida do artigo resolveu o que devia resolver.

Roda como teste de regressão: as mesmas checagens falham no original e passam
na versão final.

    python3 scripts/artigo/verificar_final.py ORIGINAL.docx CORRIGIDO.docx
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def ler(caminho: Path):
    z = zipfile.ZipFile(caminho)
    raiz = ET.fromstring(z.read("word/document.xml"))
    corpo = raiz.find(f"{W}body")
    paras, tabelas, legenda = [], [], None
    for el in corpo:
        if el.tag == f"{W}p":
            t = " ".join("".join(x.text or "" for x in el.iter(f"{W}t")).split())
            paras.append(t)
            m = re.match(r"^(Tabela|Quadro)\s*(\d+)", t)
            if m:
                legenda = f"{m.group(1)} {m.group(2)}"
        elif el.tag == f"{W}tbl":
            tabelas.append((legenda, [
                [" ".join("".join(x.text or "" for x in tc.iter(f"{W}t")).split())
                 for tc in tr.findall(f"{W}tc")]
                for tr in el.findall(f"{W}tr")]))
    imgs = sum(1 for n in z.namelist() if n.startswith("word/media/"))
    return "\n".join(paras), tabelas, imgs


def celula(tabelas, legenda, rotulo, coluna_contem):
    for cap, t in tabelas:
        if cap != legenda or not t:
            continue
        col = next((i for i, c in enumerate(t[0])
                    if coluna_contem.lower() in c.lower()), None)
        if col is None:
            continue
        for linha in t[1:]:
            if linha and linha[0].strip() == rotulo and len(linha) > col:
                return linha[col].strip()
    return None


CHECAGENS = [
    ("Vigor sobrevive ao FDR na Tabela 35",
     lambda txt, tab: celula(tab, "Tabela 35", "Vigor", "sobrevive") == "Sim",
     "A Tabela 23 (p_FDR = 0,005), a Figura 42 e duas passagens do texto "
     "afirmam que o vigor sobrevive; a célula dizia 'Não'."),

    ("Resumo nomeia as três subescalas abaixo de α 0,70",
     lambda txt, tab: "confusão (0,65)" in txt and "vigor (0,68)" in txt,
     "A Tabela 3 registra α = 0,65 para a confusão e 0,68 para o vigor; o "
     "resumo citava apenas a tensão."),

    ("Tabela 3 declara que o erro de medida vem do α",
     lambda txt, tab: "derivam do α de Cronbach" in txt, ""),
    ("Tabela 43 declara que o erro de medida vem do ω",
     lambda txt, tab: "derivados do ômega de McDonald" in txt, ""),
    ("Tabela 56 declara o ICC e é designada referência",
     lambda txt, tab: "referência para decisão individual" in txt, ""),
    ("Tabelas 19 e 52 declaram o estimador de cada uma",
     lambda txt, tab: "estimativa em dois passos" in txt and "Nível médio bruto" in txt, ""),

    ("Nota de reconciliação presente",
     lambda txt, tab: "Nota de reconciliação" in txt, ""),
    ("A nota registra a divergência das 456 observações",
     lambda txt, tab: "456" in txt and "351 observações" in txt,
     "O Esquema 1 permite no máximo 13 coletas por atleta; 27 × 13 = 351."),
    ("A nota registra a divergência do MDC₉₅",
     lambda txt, tab: "1,83 a 3,69" in txt, ""),
    ("A nota registra a divergência das médias diárias",
     lambda txt, tab: "2,87" in txt and "4,5" in txt, ""),
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("original", type=Path)
    ap.add_argument("corrigido", type=Path)
    a = ap.parse_args()

    to, tabo, imo = ler(a.original)
    tc, tabc, imc = ler(a.corrigido)

    print(f'{"checagem":52s} {"original":>10s} {"final":>8s}')
    falhas = 0
    for nome, fn, motivo in CHECAGENS:
        antes, depois = fn(to, tabo), fn(tc, tabc)
        marca = "✓" if depois else "✗"
        if not depois:
            falhas += 1
        print(f'{marca} {nome:50s} {"passa" if antes else "falha":>10s} '
              f'{"passa" if depois else "FALHA":>8s}')
        if motivo and not antes:
            print(f'      {motivo}')

    print(f"\n── integridade ──")
    for rot, o, c in (("tabelas", len(tabo), len(tabc)), ("imagens", imo, imc)):
        ok = o == c
        print(f'  {"✓" if ok else "✗"} {rot}: {o} → {c}')
        falhas += 0 if ok else 1

    print(f"\n{'OK: tudo verificado' if not falhas else f'FALHOU: {falhas} checagem(ns)'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
