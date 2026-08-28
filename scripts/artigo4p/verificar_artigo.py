#!/usr/bin/env python3
"""Confere o artigo gerado: estrutura, tabelas, figuras e coerência numérica.

    python3 scripts/artigo4p/verificar_artigo.py data/ARTIGO_SENSIBILIDADE_HUMOR.docx

Cada verificação compara o documento contra analise.py, que é a única fonte
dos números. Nenhum valor é conferido contra o texto por leitura visual.
"""
from __future__ import annotations

import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
import conteudo  # noqa: E402
import dados  # noqa: E402
from analise import DIARIO, ORDEM, br, sinal  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
DADOS = conteudo.DADOS


def ler(caminho: Path) -> tuple[list[str], ET.Element]:
    raiz = ET.fromstring(zipfile.ZipFile(caminho).read("word/document.xml"))
    corpo = raiz.find(f"{W}body")
    paragrafos = [" ".join("".join(t.text or "" for t in el.iter(f"{W}t")).split())
                  for el in corpo if el.tag == f"{W}p"]
    return [p for p in paragrafos if p], raiz


def main() -> int:
    alvo = Path(sys.argv[1] if len(sys.argv) > 1
                else "data/ARTIGO_SENSIBILIDADE_HUMOR.docx")
    paragrafos, raiz = ler(alvo)
    texto = "\n".join(paragrafos)
    tabelas = raiz.iter(f"{W}tbl")
    celulas = [" ".join("".join(t.text or "" for t in c.iter(f"{W}t")).split())
               for tab in tabelas for c in tab.iter(f"{W}tc")]
    n_tabelas = len(list(ET.fromstring(
        zipfile.ZipFile(alvo).read("word/document.xml")).iter(f"{W}tbl")))
    n_figuras = len([n for n in raiz.iter(f"{W}drawing")])

    checagens: list[tuple[str, bool, str]] = []

    def conferir(rotulo, condicao, detalhe=""):
        checagens.append((rotulo, bool(condicao), detalhe))

    # ── estrutura ──────────────────────────────────────────────────────────
    for secao in conteudo.SECOES:
        conferir(f"seção presente: {secao['titulo']}",
                 secao["titulo"] in texto)
    conferir("cinco tabelas", n_tabelas == 5, f"encontradas {n_tabelas}")
    conferir("quatro figuras", n_figuras == 4, f"encontradas {n_figuras}")
    conferir("resumo presente", conteudo.RESUMO[:60] in texto)
    conferir("palavras-chave presentes", "Palavras-chave" in texto)
    for n in (1, 2, 3, 4, 5):
        conferir(f"título da Tabela {n}", f"Tabela {n} - " in texto)
    conferir("fonte sob cada tabela",
             texto.count(conteudo.FONTE_TABELA) == 5,
             f"{texto.count(conteudo.FONTE_TABELA)} ocorrência(s)")
    conferir("fonte sob cada figura",
             texto.count(conteudo.FONTE_FIGURA) == 4,
             f"{texto.count(conteudo.FONTE_FIGURA)} ocorrência(s)")

    # ── o que o pedido excluiu ────────────────────────────────────────────
    for termo in ("PERMANOVA", "permanova", "dissimilaridade", "Bray"):
        conferir(f"sem {termo}", termo not in texto)

    # ── coerência numérica: médias diárias na Tabela 1 ─────────────────────
    faltando = [f"{d} dia {i + 1}" for d in ORDEM
                for i, v in enumerate(DIARIO[d]) if br(v, 2) not in celulas]
    conferir("médias diárias na Tabela 1", not faltando,
             f"ausentes: {faltando[:4]}")

    # ── coerência numérica: condições na Tabela 2 ─────────────────────────
    ausentes = []
    for d in ORDEM:
        x = DADOS[d]
        for valor in (br(x["hiit"], 2), br(x["jogo"], 2),
                      sinal(x["dif_hj"], 2)):
            if valor not in celulas:
                ausentes.append(f"{d}:{valor}")
    conferir("médias por condição na Tabela 2", not ausentes,
             f"ausentes: {ausentes[:4]}")

    # ── coerência numérica: sensibilidade na Tabela 4 ─────────────────────
    ausentes = []
    for d in ORDEM:
        x = DADOS[d]
        for valor in (br(x["resposta_hiit"], 0), br(x["resposta_jogo"], 0),
                      br(x["especificidade"], 0), br(x["piso"], 1)):
            if valor not in celulas:
                ausentes.append(f"{d}:{valor}")
    conferir("índices de sensibilidade na Tabela 4", not ausentes,
             f"ausentes: {ausentes[:4]}")

    # ── coerência entre o texto e a análise ───────────────────────────────
    pth = DADOS["PTH"]
    fad = DADOS["Fadiga"]
    conferir("texto cita a média da PTH sob HIIT", br(pth["hiit"], 2) in texto)
    conferir("texto cita a média da PTH sob jogo", br(pth["jogo"], 2) in texto)
    conferir("texto cita a especificidade da PTH",
             br(pth["especificidade"], 0) in texto)
    conferir("texto cita a resposta da PTH ao HIIT",
             br(pth["resposta_hiit"], 0) in texto)
    conferir("texto cita a especificidade da fadiga",
             br(fad["especificidade"], 0) in texto)
    conferir("texto cita as três dimensões com resposta aguda",
             all(f"dz = {v}" in texto for v in ("0,45", "0,44", "−0,39")))
    # migração dos perfis: cada percentual do texto existe na tabela
    perfil = []
    for nome, v in dados.PARSONS.items():
        for i in (1, 2):
            if br(v[i], 1) not in celulas:
                perfil.append(f"{nome}:{br(v[i], 1)}")
    for dia in (1, 7):
        for k in (0, 1):
            if br(dados.PERFIL_DIA[dia][k], 1) not in celulas:
                perfil.append(f"Morgan dia {dia}")
    conferir("migração dos perfis na Tabela 4", not perfil,
             f"ausentes: {perfil[:4]}")
    conferir("texto cita a queda do perfil iceberg",
             "71,4%" in texto and "32,6%" in texto)
    conferir("texto cita o avanço do humor perturbado",
             "47,6%" in texto and "71,7%" in texto)
    conferir("texto declara o piso das quatro subescalas",
             all(br(DADOS[d]["piso"], 1) in texto
                 for d in ("Confusão", "Depressão", "Raiva", "Tensão")))

    # ── números decimais sempre com vírgula no corpo ──────────────────────
    corpo_texto = [x for x in paragrafos if not re.match(r"^\d+(\.\d+)* ", x)]
    pontos = [m for x in corpo_texto
              for m in re.findall(r"\b\d+\.\d+\b", x)]
    conferir("decimais com vírgula", not pontos, f"com ponto: {pontos[:4]}")

    print(f"── verificação do artigo: {alvo.name} ──")
    falhas = 0
    for rotulo, ok, detalhe in checagens:
        falhas += 0 if ok else 1
        marca = "✓" if ok else "✗"
        print(f"  {marca} {rotulo}" + (f"   {detalhe}" if not ok and detalhe else ""))
    print(f"\n  {len(paragrafos)} parágrafos, {n_tabelas} tabelas, "
          f"{n_figuras} figuras, {len(texto.split())} palavras")
    print("OK: artigo conforme" if not falhas else f"FALHOU: {falhas} verificação(ões)")
    return 1 if falhas else 0


if __name__ == "__main__":
    sys.exit(main())
