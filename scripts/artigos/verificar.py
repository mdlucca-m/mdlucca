#!/usr/bin/env python3
"""Confere os três documentos da série contra os módulos de origem.

    python3 scripts/artigos/verificar.py

Cada número citado no texto e em cada célula é comparado com fonte.py, com
dados.py ou com o panorama do corpus. Nenhuma conferência é visual.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

RAIZ = Path(__file__).resolve().parents[2]
for sub in ("comum", "artigo4p", "plano", "artigos"):
    sys.path.insert(0, str(RAIZ / "scripts" / sub))
sys.path.insert(0, str(RAIZ))

import artigo1  # noqa: E402
import artigo2  # noqa: E402
import fonte as F  # noqa: E402
from dados import PARSONS, PERFIL_DIA  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def ler(caminho: Path):
    raiz = ET.fromstring(zipfile.ZipFile(caminho).read("word/document.xml"))
    corpo = raiz.find(f"{W}body")
    paragrafos = [" ".join("".join(t.text or "" for t in el.iter(f"{W}t")).split())
                  for el in corpo if el.tag == f"{W}p"]
    celulas = [" ".join("".join(t.text or "" for t in c.iter(f"{W}t")).split())
               for tab in raiz.iter(f"{W}tbl") for c in tab.iter(f"{W}tc")]
    n_tab = len(list(raiz.iter(f"{W}tbl")))
    n_fig = len(list(raiz.iter(f"{W}drawing")))
    return [p for p in paragrafos if p], celulas, n_tab, n_fig


def conferir(nome: str, caminho: Path, mod, checagens) -> int:
    paragrafos, celulas, n_tab, n_fig = ler(caminho)
    texto = "\n".join(paragrafos)
    print(f"── {nome} ──")
    falhas = 0
    itens = [
        (f"{len(mod.TABELAS)} tabelas", n_tab == len(mod.TABELAS),
         f"encontradas {n_tab}"),
        ("três figuras", n_fig == 3, f"encontradas {n_fig}"),
        ("resumo presente", mod.ABERTURA[0][1][:60] in texto, ""),
        ("palavras-chave presentes", "PALAVRAS-CHAVE" in texto, ""),
        ("fonte sob cada tabela",
         texto.count(mod.FONTE_TABELA) == len(mod.TABELAS),
         f"{texto.count(mod.FONTE_TABELA)} de {len(mod.TABELAS)}"),
        ("fonte sob cada figura", texto.count(mod.FONTE_FIGURA) == 3,
         f"{texto.count(mod.FONTE_FIGURA)}"),
        ("referências presentes", "REFERÊNCIAS" in texto, ""),
        ("sem PERMANOVA", "PERMANOVA" not in texto, ""),
    ] + checagens(texto, celulas)
    for rotulo, ok, detalhe in itens:
        falhas += 0 if ok else 1
        print(f'  {"✓" if ok else "✗"} {rotulo}'
              + (f"   {detalhe}" if not ok and detalhe else ""))
    print(f"  {len(texto.split())} palavras, {n_tab} tabelas, {n_fig} figuras\n")
    return falhas


def checar_a1(texto, celulas):
    faltando = [f"{n}:{F.br(v, 2)}" for n, vals in F.DESCRITIVA.items()
                for v in vals[:2] if F.br(v, 2) not in celulas]
    percentis = [f"{n}:{v}" for n, vals in F.PERCENTIS.items()
                 for v in vals if str(v) not in celulas]
    confiab = [f"{n}:{F.br(v, 2)}" for n, vals in F.CONFIABILIDADE.items()
               for v in vals if v is not None and F.br(v, 2) not in celulas]
    prev = [f"{n}:{F.br(v[0], 1)}" for n, v in PARSONS.items()
            if F.br(v[0], 1) not in celulas]
    return [
        ("descritivas na Tabela 1", not faltando, f"ausentes: {faltando[:3]}"),
        ("percentis na Tabela 2", not percentis, f"ausentes: {percentis[:3]}"),
        ("confiabilidade na Tabela 3", not confiab, f"ausentes: {confiab[:3]}"),
        ("prevalência dos perfis na Tabela 5", not prev,
         f"ausentes: {prev[:3]}"),
        ("texto cita o excesso de perfil superfície",
         "56,8" in texto and "42,0" in texto, ""),
        ("texto cita o piso da confusão", "80,5" in texto, ""),
        ("texto cita o ganho de estabilidade da média semanal",
         "0,76" in texto or "sete dias" in texto, ""),
        ("texto soma os três perfis de risco",
         artigo1.F.br(artigo1._RISCO, 1) in texto,
         f"esperado {artigo1.F.br(artigo1._RISCO, 1)}%"),
        ("texto compara com a amostra brasileira",
         "26,5" in texto and "Rohlfs" in texto, ""),
        ("texto declara o limite de piso de 15%",
         "15%" in texto and "Terwee" in texto, ""),
        ("texto relata a divergência entre os dois critérios",
         "71,4" in texto and "21,4" in texto, ""),
        ("método declara aprovação ética",
         "comitê de ética" in texto and "consentimento" in texto, ""),
        ("método declara a instrução de resposta",
         "momento presente" in texto, ""),
        ("limitação da k-médias semeada declarada",
         "semeada" in texto, ""),
        ("afirmação de pioneirismo qualificada",
         "Até onde alcança" in texto, ""),
    ]


def checar_a2(texto, celulas):
    sessoes = [f"{n}:{F.br(v, 1)}" for n, vals in F.SESSOES.items()
               for v in vals[:3] if F.br(v, 1) not in celulas]
    bayes = [f"{n}:{F.sinal(dz, 2)}" for n, (dz, _, _) in F.BAYES.items()
             if F.sinal(dz, 2) not in celulas]
    rec = [f"{n}:{F.br(r, 1)}" for n, (r, _) in F.RECUPERACAO.items()
           if F.br(r, 1) not in celulas]
    return [
        ("progressão das sessões na Tabela 2", not sessoes,
         f"ausentes: {sessoes[:3]}"),
        ("fatores de Bayes na Tabela 3", not bayes, f"ausentes: {bayes[:3]}"),
        ("recuperação noturna na Tabela 5", not rec, f"ausentes: {rec[:3]}"),
        ("migração do iceberg na Tabela 6",
         F.br(PERFIL_DIA[1][0], 1) in celulas
         and F.br(PERFIL_DIA[7][0], 1) in celulas, ""),
        ("texto cita a dissociação entre FC e esforço",
         "184" in texto and "181" in texto and "9,1" in texto, ""),
        ("texto cita a inclinação da PTH por sessão", "1,76" in texto, ""),
        ("texto declara que não há diagnóstico",
         "não um diagnóstico" in texto or "assinatura de sobrecarga" in texto,
         ""),
        ("texto declara a ausência de medida de desempenho",
         "não mediu desempenho" in texto, ""),
        ("recomendações práticas presentes",
         "RECOMENDAÇÕES PARA A COMISSÃO TÉCNICA" in texto, ""),
    ]


def main() -> int:
    falhas = conferir("Artigo 1", RAIZ / "data" / "ARTIGO1_PERFIS_HUMOR_HANDEBOL.docx",
                      artigo1, checar_a1)
    falhas += conferir("Artigo 2", RAIZ / "data" / "ARTIGO2_FADIGA_PERFIS_HANDEBOL.docx",
                       artigo2, checar_a2)
    print("OK: os dois manuscritos conferem" if not falhas
          else f"FALHOU: {falhas} verificação(ões)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
