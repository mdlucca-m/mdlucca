"""Geração das tabelas de resultados a partir do corpus elegível.

Toda tabela devolve (titulo, cabecalho, linhas, nota) e declara explicitamente
a base sobre a qual foi contada — a ausência dessa declaração é o achado G4.
"""
from __future__ import annotations

import collections
import re
import sqlite3
from dataclasses import dataclass

from . import psicometria as P
from .elegibilidade import FAMILIA_DE_SUBVARIAVEL, JANELA, fluxo_prisma


@dataclass
class Tabela:
    numero: int
    titulo: str
    cabecalho: list[str]
    linhas: list[list[str]]
    nota: str = ""
    fonte: str = "Elaborada pelos autores."

    def markdown(self) -> str:
        al = ["---" if i == 0 else "---:" for i in range(len(self.cabecalho))]
        out = [f"**Tabela {self.numero} – {self.titulo}**", "",
               "| " + " | ".join(self.cabecalho) + " |",
               "| " + " | ".join(al) + " |"]
        out += ["| " + " | ".join(str(c) for c in l) + " |" for l in self.linhas]
        out += ["", f"Fonte: {self.fonte}"]
        if self.nota:
            out += [f"Nota: {self.nota}"]
        return "\n".join(out)


# A biblioteca guarda nomes de país sem diacríticos (achado A7); restaura-se a
# grafia correta na apresentação, sem alterar o dado de origem.
ACENTOS_PAIS = {
    "Polonia": "Polônia", "Tunisia": "Tunísia", "Franca": "França",
    "Suecia": "Suécia", "Japao": "Japão", "Ira": "Irã", "Croacia": "Croácia",
    "Hungria": "Hungria", "Turquia": "Turquia", "Servia": "Sérvia",
    "Eslovenia": "Eslovênia", "Grecia": "Grécia", "Belgica": "Bélgica",
    "Austria": "Áustria", "Suica": "Suíça", "Islandia": "Islândia",
    "Finlandia": "Finlândia", "Russia": "Rússia", "Ucrania": "Ucrânia",
    "Coreia do Sul": "Coreia do Sul", "Catar": "Catar", "Egito": "Egito",
    "Argelia": "Argélia", "Arabia Saudita": "Arábia Saudita",
    "Estados Unidos": "Estados Unidos", "Canada": "Canadá", "Mexico": "México",
    "Colombia": "Colômbia", "Australia": "Austrália", "Italia": "Itália",
    "Romenia": "Romênia", "Eslovaquia": "Eslováquia", "Tchequia": "Tchéquia",
    "Paises Baixos": "Países Baixos", "Lituania": "Lituânia",
    "Letonia": "Letônia", "Estonia": "Estônia", "Bulgaria": "Bulgária",
    "Bosnia": "Bósnia e Herzegovina", "India": "Índia",
    "Africa do Sul": "África do Sul", "Oma": "Omã", "Israel": "Israel",
    "Macedonia do Norte": "Macedônia do Norte", "Montenegro": "Montenegro",
    "Reino Unido": "Reino Unido", "Nigeria": "Nigéria", "Chile": "Chile",
}


def acentuar_pais(p: str) -> str:
    return ACENTOS_PAIS.get(p, p)


def _pct(n: int, base: int) -> str:
    return f"{100 * n / base:.1f}".replace(".", ",") if base else "—"


# ── Tabela 1 · fontes ───────────────────────────────────────────────────────
def fontes(con: sqlite3.Connection) -> Tabela:
    linhas = [[r[0], r[1]] for r in con.execute(
        "SELECT fonte, COUNT(*) n FROM artigo WHERE COALESCE(fonte,'')<>'' "
        "GROUP BY fonte ORDER BY n DESC")]
    total = sum(l[1] for l in linhas)
    linhas.append(["**Total**", f"**{total}**"])
    return Tabela(
        1, "Bases de origem dos registros da biblioteca",
        ["Base", "Registros"], linhas,
        nota=("Contagem sobre a biblioteca completa, pelo campo de procedência "
              "de cada registro. O rendimento por base da execução corrente da "
              "busca é gravado em `busca_rendimento` e deve substituir esta "
              "tabela assim que a busca por API for reexecutada."))


# ── Tabela 3 · fluxo PRISMA ─────────────────────────────────────────────────
def prisma(decisoes: list) -> Tabela:
    f = fluxo_prisma(decisoes)
    linhas = [["Registros na biblioteca curada", f["avaliados"]],
              ["Excluídos na triagem", f["excluidos"]]]
    linhas += [[f"  · {m}", n] for m, n in f["por_motivo"].items() if n]
    linhas.append(["**Registros elegíveis**", f"**{f['incluidos']}**"])
    return Tabela(
        3, "Triagem segundo os critérios dos Quadros 1 e 2",
        ["Etapa", "n"], linhas,
        nota=("Cada exclusão recebe um único motivo, o primeiro aplicável na "
              "ordem do Quadro 2, como o PRISMA exige. Dos elegíveis, "
              f"{f['por_evidencia']['instrumento nomeado']} nomeiam um instrumento "
              "psicométrico no título, resumo ou palavras-chave e "
              f"{f['por_evidencia']['construto no resumo']} declaram o construto "
              "sem nomear o instrumento; nestes a confirmação depende do texto "
              "completo."))


# ── Tabela 4 · famílias de construto ────────────────────────────────────────
def familias(decisoes: list) -> Tabela:
    inc = [d for d in decisoes if d.incluido]
    cnt = collections.Counter(f for d in inc for f in d.familias)
    base = len(inc)
    linhas = [[fam, n, _pct(n, base)] for fam, n in cnt.most_common()]
    return Tabela(
        4, "Famílias de construto psicológico nos registros elegíveis",
        ["Família de construto", "Registros", "%"], linhas,
        nota=(f"Base: {base} registros elegíveis. Um registro pode figurar em "
              "mais de uma família, de modo que a soma da coluna excede a base "
              "e os percentuais não somam 100%. A família é atribuída pelo "
              "construto efetivamente aferido — pelo instrumento, quando "
              "nomeado — e não pela marcação de área do artigo."))


# ── Tabela 5 · instrumentos psicométricos ───────────────────────────────────
def instrumentos(decisoes: list) -> Tabela:
    inc = [d for d in decisoes if d.incluido]
    cnt = collections.Counter(i.canonico for d in inc for i in d.instrumentos)
    fam = {i.canonico: i.familia for d in inc for i in d.instrumentos}
    com = sum(1 for d in inc if d.instrumentos)
    linhas = [[c, fam[c], n] for c, n in cnt.most_common(20)]
    return Tabela(
        5, "Instrumentos psicométricos nomeados nos registros elegíveis",
        ["Instrumento", "Família de construto", "Registros"], linhas,
        nota=(f"Base: {com} dos {len(inc)} registros elegíveis nomeiam ao menos "
              "um instrumento. A detecção corre sobre título, resumo e "
              "palavras-chave por dicionário controlado; estudos que nomeiam o "
              "instrumento apenas na seção de método não são alcançados, de modo "
              "que estes números são um piso. Escalas de percepção de esforço "
              "não constam: são medidas psicofísicas, não psicometria de "
              "construto."))


# ── Tabela 6 · distribuição geográfica ──────────────────────────────────────
def paises(con: sqlite3.Connection, decisoes: list) -> Tabela:
    ids = {d.id for d in decisoes if d.incluido}
    cnt = collections.Counter()
    sem = 0
    for i, pais in con.execute("SELECT id, pais FROM artigo"):
        if i in ids:
            cnt[pais] += 1 if pais else 0
            if not pais:
                sem += 1
    linhas = [[acentuar_pais(p), n, _pct(n, len(ids))]
              for p, n in cnt.most_common(15) if p]
    return Tabela(
        6, "Distribuição geográfica dos registros elegíveis",
        ["País", "Registros", "%"], linhas,
        nota=(f"Base: {len(ids)} registros elegíveis, dos quais {sem} sem país "
              "recuperável na afiliação. O país é o da afiliação do primeiro "
              "autor, não necessariamente o da amostra."))


# ── Tabela 7 · práticas de relato ───────────────────────────────────────────
PRATICAS = [
    ("Relato de tamanho de efeito",
     r"tamanho de efeito|effect size|cohen'?s d|partial eta|η2|hedges"),
    ("Correção para comparações múltiplas",
     r"bonferroni|holm|false discovery|fdr correction|sidak|tukey"),
    ("Intervalo de confiança relatado", r"confidence interval|intervalo de confian|95% ci"),
    ("Análise de potência ou cálculo amostral",
     r"power analysis|sample size calculation|g\*power|calculo amostral"),
    ("Confiabilidade do instrumento relatada",
     r"cronbach|omega de mcdonald|mcdonald'?s omega|test[- ]retest|icc\b"),
]


def relato(con: sqlite3.Connection, decisoes: list) -> Tabela:
    ids = {d.id for d in decisoes if d.incluido}
    textos = {}
    for i, est, res in con.execute("SELECT id, estatistica, resumo FROM artigo"):
        if i in ids:
            textos[i] = f"{est or ''} {res or ''}".lower()
    base = len(textos)
    linhas = []
    for rotulo, padrao in PRATICAS:
        rx = re.compile(padrao, re.I)
        n = sum(1 for t in textos.values() if rx.search(t))
        linhas.append([rotulo, n, _pct(n, base)])
    return Tabela(
        7, "Práticas de relato detectáveis nos registros elegíveis",
        ["Prática de relato", "n", "%"], linhas,
        nota=(f"Base: {base} registros elegíveis, sobre resumo e campo de análise "
              "estatística. A ausência de detecção indica que a prática não foi "
              "relatada de forma recuperável nesses campos, e não que esteja "
              "ausente do estudo; o resumo omite rotineiramente a estatística. "
              "A versão desta tabela sobre os textos completos exige nova "
              "mineração e substitui esta assim que disponível."))


# ── Tabela 8 · vocabulário da estratégia ────────────────────────────────────
def vocabulario() -> Tabela:
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from busca import estrategia as E
    linhas = [
        ["Conceito", "MeSH", len(E.CONCEITO_MESH), "; ".join(E.CONCEITO_MESH)],
        ["Conceito", "DeCS", len(E.CONCEITO_DECS), "; ".join(E.CONCEITO_DECS)],
        ["Conceito", "Termo livre", len(E.CONCEITO_LIVRE), "; ".join(E.CONCEITO_LIVRE)],
        ["Contexto", "MeSH", len(E.CONTEXTO_MESH), "; ".join(E.CONTEXTO_MESH)],
        ["Contexto", "Termo livre", len(E.CONTEXTO_LIVRE), "; ".join(E.CONTEXTO_LIVRE)],
        ["População", "Termo livre", len(E.POPULACAO_LIVRE), "; ".join(E.POPULACAO_LIVRE)],
    ]
    return Tabela(
        8, "Vocabulário controlado e termos livres, por bloco",
        ["Bloco", "Vocabulário", "n", "Termos"], linhas,
        nota=("Não há descritor MeSH para handebol, verificação feita no MeSH "
              "Browser da National Library of Medicine; o bloco de população é "
              "composto exclusivamente por termos livres. Os termos aqui "
              "listados são a fonte de que as consultas de cada base são "
              "geradas, de modo que apêndice e busca não podem divergir."))


def todas(con: sqlite3.Connection, decisoes: list) -> list[Tabela]:
    return [fontes(con), prisma(decisoes), familias(decisoes),
            instrumentos(decisoes), paises(con, decisoes), relato(con, decisoes),
            vocabulario()]
