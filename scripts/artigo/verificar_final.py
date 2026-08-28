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

    # ── orientações do orientador ──
    ("Tabela de caracterização da carga por dia presente",
     lambda txt, tab: any(t and t[0] and t[0][0] == "Dia" and "Volume rel." in " ".join(t[0])
                          for _, t in tab),
     "Pedido central: uma tabela que caracterize tipo de treino e carga por dia."),
    ("A tabela de carga cobre os sete dias",
     lambda txt, tab: any(t and t[0] and t[0][0] == "Dia" and len(t) == 8
                          for _, t in tab), ""),
    ("Momento do monitoramento declarado",
     lambda txt, tab: "última semana de treinamento da fase pré-competitiva" in txt,
     "'a gente tem que colocar em que momento que foi feito esse monitoramento'."),
    ("Estudo reposicionado como acompanhamento",
     lambda txt, tab: "Trata-se de um estudo de acompanhamento" in txt,
     "'seria um estudo experimental...? Mas é um estudo de acompanhamento'."),
    ("Variação diária explicada pela carga",
     lambda txt, tab: "4.17 Caracterização da carga" in txt
                      and "governada mais pela intensidade" in txt,
     "'quais são os fatores que geram essa variação que potencialmente explicam isso'."),
    ("Recomendações para comissão técnica presentes",
     lambda txt, tab: "4.18 Recomendações" in txt
                      and "Quatro recomendações decorrem dos dados" in txt,
     "'os dados vão indicar recomendações para o treinamento, para o técnico'."),
    ("Alerta do Dia 7 para jogo no dia seguinte",
     lambda txt, tab: "pior estado psicológico de toda a semana" in txt,
     "'o que se obteve no sétimo dia não é favorável pra esse jogo'."),
    ("Seções na ordem 4.16 → 4.17 → 4.18",
     lambda txt, tab: (txt.index("4.16 Nota") < txt.index("4.17 Caracterização")
                       < txt.index("4.18 Recomendações"))
                      if all(k in txt for k in ("4.16 Nota", "4.17 Caracterização",
                                                "4.18 Recomendações")) else False, ""),
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
    # A correção acrescenta uma tabela (a de caracterização da carga) e não
    # remove nenhuma; imagens têm de ser preservadas integralmente.
    ok_tab = len(tabc) == len(tabo) + 1
    print(f'  {"✓" if ok_tab else "✗"} tabelas: {len(tabo)} → {len(tabc)} '
          f'(+1 esperada: a de carga)')
    falhas += 0 if ok_tab else 1
    ok_img = imo == imc
    print(f'  {"✓" if ok_img else "✗"} imagens preservadas: {imo} → {imc}')
    falhas += 0 if ok_img else 1

    print(f"\n{'OK: tudo verificado' if not falhas else f'FALHOU: {falhas} checagem(ns)'}")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
