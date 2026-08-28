#!/usr/bin/env python3
"""Compara as versões do artigo primário sobre humor no handebol.

Seis arquivos circulam com títulos parecidos e resultados diferentes. Este
script estabelece a cronologia real (pelos metadados, não pelo nome do
arquivo), separa as linhagens e confronta os números que cada versão declara.

    python3 scripts/humor/comparar_versoes.py ARTIGO1.docx ARTIGO2.docx ...
"""
from __future__ import annotations

import argparse
import re
import sys
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"

# Números que devem ser os mesmos em todas as versões do mesmo estudo.
INVARIANTES = {
    "observações": r"(\d{3})\s*observaç[õo]es\s*(?:válidas|v[áa]lidas)?",
    "atletas": r"(?:em|com)\s*(\d{2})\s*atletas",
    "coorte completa": r"(?:Dezenove|Dezoito|(\d{1,2}))\s*atletas?\s*\(?\d*%?\)?\s*complet",
    "pares pré/pós": r"~?\s*(\d{2,3})\s*pares",
    "fatores retidos": r"reteve\s+(?:os\s+)?(cinco|seis|\d)\s*fatores",
    "α da tensão": r"tens[ãa]o\s*\(?α\s*=\s*(0,\d{2})",
    "R² marginal": r"R²\s*marginal\s*=\s*(0,\d{3})",
    "R² condicional": r"R²\s*condicional\s*=\s*(0,\d{3})",
}

# Tamanhos de efeito da resposta aguda: onde as linhagens divergem.
EFEITOS = ("Vigor", "Fadiga", "PTH", "Tensão", "Depressão", "Raiva", "Confusão")


@dataclass
class Versao:
    rotulo: str
    caminho: Path
    criado: str = ""
    modificado: str = ""
    autor: str = ""
    paginas: str = "?"
    paragrafos: list[str] = field(default_factory=list)
    tabelas: list = field(default_factory=list)
    figuras: int = 0

    @property
    def texto(self) -> str:
        return "\n".join(self.paragrafos)

    @property
    def palavras(self) -> int:
        return len(self.texto.split())

    @property
    def titulo(self) -> str:
        return next((p for p in self.paragrafos if p.strip()), "")[:88]


def ler(caminho: Path) -> Versao:
    v = Versao(caminho.stem[:24], caminho)
    z = zipfile.ZipFile(caminho)
    raiz = ET.fromstring(z.read("word/document.xml"))
    for el in raiz.find(f"{W}body"):
        if el.tag == f"{W}p":
            v.paragrafos.append(" ".join(
                "".join(t.text or "" for t in el.iter(f"{W}t")).split()))
        elif el.tag == f"{W}tbl":
            v.tabelas.append([
                [" ".join("".join(t.text or "" for t in tc.iter(f"{W}t")).split())
                 for tc in tr.findall(f"{W}tc")]
                for tr in el.findall(f"{W}tr")])
    v.figuras = sum(1 for n in z.namelist() if n.startswith("word/media/"))
    if "docProps/core.xml" in z.namelist():
        x = z.read("docProps/core.xml").decode("utf-8")
        pega = lambda t: (re.search(rf"<[^>]*{t}[^>]*>([^<]*)<", x) or [None, ""])[1]
        v.criado, v.modificado, v.autor = pega("created"), pega("modified"), pega("creator")
    if "docProps/app.xml" in z.namelist():
        a = z.read("docProps/app.xml").decode("utf-8")
        v.paginas = (re.search(r"<Pages>(\d+)</Pages>", a) or [None, "?"])[1]
    return v


def linhagem(v: Versao) -> str:
    """Duas linhagens: validação psicométrica vs descrição do perfil."""
    t = v.texto.lower()
    a = sum(t.count(k) for k in ("pseudorreplicaç", "permanova", "fator de bayes",
                                 "rmcorr", "rope", "hotelling"))
    b = sum(t.count(k) for k in ("escores t", "youden", "t-car", "friedman",
                                 "w de kendall"))
    return "psicométrica" if a > b else "perfil" if b > a else "—"


def invariantes(v: Versao) -> dict[str, str]:
    fora = {}
    for nome, padrao in INVARIANTES.items():
        vals = {m for g in re.findall(padrao, v.texto, re.I)
                for m in (g if isinstance(g, tuple) else (g,)) if m}
        fora[nome] = " / ".join(sorted(vals)) if vals else "—"
    return fora


def efeitos_agudos(v: Versao) -> dict[str, str]:
    """Extrai o tamanho de efeito pré→pós de cada dimensão, da primeira tabela
    que traga uma coluna de d ou dz."""
    for t in v.tabelas:
        if not t or len(t) < 4:
            continue
        cab = " ".join(t[0]).lower()
        if not re.search(r"\bd\b|\bdz\b|cohen", cab):
            continue
        if not any(re.search(r"pr[ée]|p[óo]s|Δ|delta", c, re.I) for c in t[0]):
            continue
        col = next((i for i, c in enumerate(t[0])
                    if re.search(r"\bdz\b|d de cohen|d cohen", c, re.I)), None)
        if col is None:
            continue
        saida = {}
        for linha in t[1:]:
            if len(linha) <= col:
                continue
            # "Fadiga física" não é a subescala "Fadiga" do BRUMS; casa-se a
            # dimensão mais longa primeiro para não confundir as duas.
            rotulo = linha[0].strip()
            dim = next((e for e in sorted(EFEITOS, key=len, reverse=True)
                        if rotulo == e or rotulo.startswith(e + " (")), None)
            if dim and dim not in saida:
                saida[dim] = linha[col].split("[")[0].strip()
        if len(saida) >= 3:
            return saida
    return {}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("arquivos", nargs="+", type=Path)
    a = p.parse_args()

    versoes = [ler(f) for f in a.arquivos]
    versoes.sort(key=lambda v: v.modificado or v.criado or "")

    print("── cronologia real (metadados, não o nome do arquivo) ──")
    print(f'{"arquivo":30s} {"modificado":21s} {"linhagem":13s} {"pág":>4s} '
          f'{"palavras":>9s} {"tab":>4s} {"fig":>4s}')
    for v in versoes:
        print(f"{v.caminho.name[:30]:30s} {(v.modificado or '—'):21s} "
              f"{linhagem(v):13s} {v.paginas:>4s} {v.palavras:>9d} "
              f"{len(v.tabelas):>4d} {v.figuras:>4d}")
    mais_nova = versoes[-1]
    maior = max(versoes, key=lambda v: v.palavras)
    if mais_nova is not maior:
        print(f"\n  ⚠ a versão mais recente ({mais_nova.caminho.name}) não é a mais "
              f"desenvolvida ({maior.caminho.name}), e as duas estão em linhagens "
              f"diferentes ({linhagem(mais_nova)} vs {linhagem(maior)}).")

    print("\n── invariantes do estudo: devem ser iguais em toda versão ──")
    tabela = {v.rotulo: invariantes(v) for v in versoes}
    for nome in INVARIANTES:
        vals = {r: d[nome] for r, d in tabela.items() if d[nome] != "—"}
        distintos = set(vals.values())
        marca = "  " if len(distintos) <= 1 else "✗ "
        print(f"{marca}{nome:18s} " + " | ".join(f"{r[:14]}={x}" for r, x in vals.items()))

    print("\n── tamanho de efeito da resposta aguda pré→pós ──")
    efs = {v.rotulo: efeitos_agudos(v) for v in versoes}
    efs = {k: d for k, d in efs.items() if d}
    if efs:
        dims = [d for d in EFEITOS if any(d in x for x in efs.values())]
        print(f'{"dimensão":12s} ' + " ".join(f"{r[:15]:>16s}" for r in efs))
        for d in dims:
            print(f"{d:12s} " + " ".join(f"{efs[r].get(d,'—'):>16s}" for r in efs))
        print("\n  Uma diferença sistemática entre colunas indica que uma das versões")
        print("  não corrigiu a pseudorreplicação: tratar cada par pré/pós como")
        print("  independente infla o tamanho de efeito.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
