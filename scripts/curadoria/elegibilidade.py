"""Aplicação dos critérios dos Quadros 1 e 2 à biblioteca, com registro do
motivo de cada exclusão — o que o diagrama PRISMA exige e o manuscrito não
tinha (achados B2 e B3).

Cada registro recebe uma decisão e, quando excluído, o primeiro critério que o
excluiu, na ordem declarada no Quadro 2. A ordem importa: o PRISMA pede um
motivo por estudo, não todos os motivos aplicáveis.
"""
from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass, field

from . import psicometria as P

JANELA = (2006, 2026)

TERMOS_HANDEBOL = ("handball", "handebol", "balonmano", "andebol", "handboll",
                   "handbal", "hand ball", "teamhandball")

# Quadro 2, critério 4: delineamento inelegível.
TIPOS_INELEGIVEIS = {
    "Revisao": "revisão narrativa",
    "Revisao sistematica": "revisão sistemática",
    "Meta-analise": "meta-análise",
    "Capitulo de livro": "capítulo de livro",
    "Trabalho em anais": "resumo de congresso",
}
DESENHOS_INELEGIVEIS = {"Revisao de literatura": "revisão narrativa"}

# Quadro 2, critério 3: "contexto clínico, escolar ou laboratorial SEM vínculo
# com a prática esportiva". Exclui-se por evidência positiva de contexto
# inelegível, nunca por campo pouco informativo — o mesmo princípio que a §3.6
# aplica aos registros sem resumo: ausência de evidência não é evidência de
# inelegibilidade.
CONTEXTO_ESPORTIVO = re.compile(
    r"competicao|competi|treino|temporada|jogo|partida|match|training|season|"
    r"elite|profissional|semiprofissional|amador|recreacional|clube|equipe|"
    r"atleta|jogador|player", re.I)
CONTEXTO_NAO_ESPORTIVO = re.compile(r"laboratorio|clinico|reabilitacao|escola/ef", re.I)

MOTIVOS = [
    "fora da janela temporal",
    "população não é de handebol",
    "não mede variável psicológica",
    "fora de treinamento ou competição",
    "delineamento inelegível",
]


def _plano(t: str) -> str:
    return unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()


@dataclass
class Decisao:
    id: int
    incluido: bool
    motivo: str = ""
    detalhe: str = ""
    instrumentos: list = field(default_factory=list)
    familias: set = field(default_factory=set)
    evidencia: str = ""   # "instrumento nomeado" | "construto no resumo"


def avaliar(reg: sqlite3.Row, subvariaveis: set[str]) -> Decisao:
    texto = " ".join(str(reg[c] or "") for c in
                     ("titulo", "resumo", "palavras_chave"))
    plano = _plano(texto)
    ident = reg["id"]

    # 1 · Janela temporal (Quadro 1)
    ano = reg["ano"]
    if not (ano or "").isdigit() or not (JANELA[0] <= int(ano) <= JANELA[1]):
        return Decisao(ident, False, MOTIVOS[0], f"ano = {ano or 'ausente'}")

    # 2 · População de handebol (Quadro 2, critério 1)
    if not any(t in plano for t in TERMOS_HANDEBOL):
        return Decisao(ident, False, MOTIVOS[1],
                       "sem menção a handebol em título, resumo ou palavras-chave")

    # 3 · Delineamento (Quadro 2, critério 4) — antes do conceito, porque uma
    #     revisão sobre ansiedade no handebol é inelegível ainda que meça o
    #     construto.
    tipo = (reg["tipo_estudo"] or "").strip()
    desenho = (reg["desenho_estudo"] or "").strip()
    if tipo in TIPOS_INELEGIVEIS:
        return Decisao(ident, False, MOTIVOS[4], TIPOS_INELEGIVEIS[tipo])
    if desenho in DESENHOS_INELEGIVEIS:
        return Decisao(ident, False, MOTIVOS[4], DESENHOS_INELEGIVEIS[desenho])

    # 4 · Aferição de variável psicológica (Quadro 1, eixo Conceito)
    instrumentos = P.detectar(reg["titulo"], reg["resumo"], reg["palavras_chave"])
    familias = P.familias_de(instrumentos)
    psico_sub = subvariaveis & SUBVARIAVEIS_PSICOLOGICAS
    if instrumentos:
        evidencia = "instrumento nomeado"
    elif psico_sub - {"Percepcao de esforco"}:
        evidencia = "construto no resumo"
        familias = {FAMILIA_DE_SUBVARIAVEL[s] for s in psico_sub
                    if s in FAMILIA_DE_SUBVARIAVEL}
    else:
        detalhe = ("apenas percepção de esforço, que é medida psicofísica"
                   if psico_sub else "nenhum construto psicológico aferido")
        return Decisao(ident, False, MOTIVOS[2], detalhe)

    # 5 · Contexto (Quadro 2, critério 3)
    contexto = _plano((reg["pcc_contexto"] or "") + " " + (reg["populacao"] or ""))
    if CONTEXTO_NAO_ESPORTIVO.search(contexto) and not CONTEXTO_ESPORTIVO.search(contexto):
        return Decisao(ident, False, MOTIVOS[3],
                       f"contexto exclusivamente {(reg['pcc_contexto'] or '').strip()[:50]}")

    return Decisao(ident, True, instrumentos=instrumentos, familias=familias,
                   evidencia=evidencia)


# Sub-variáveis da biblioteca que constituem construto psicológico, e a
# família da Tabela 4 a que cada uma pertence.
FAMILIA_DE_SUBVARIAVEL = {
    "Ansiedade": "ansiedade e estresse",
    "Estresse": "ansiedade e estresse",
    "Motivacao": "motivação",
    "Engajamento / satisfacao": "motivação",
    "Cognicao / Tomada de decisao": "cognição e atenção",
    "Burnout": "burnout e saúde mental",
    "Saude mental": "burnout e saúde mental",
    "Depressao": "burnout e saúde mental",
    "Imagem corporal / alimentar": "burnout e saúde mental",
    "Enfrentamento (coping)": "coping e resiliência",
    "Resiliencia / Mental toughness": "coping e resiliência",
    "Habilidades mentais": "coping e resiliência",
    "Medo de re-lesao / prontidao": "coping e resiliência",
    "Sono / Sonolencia": "sono e recuperação",
    "Bem-estar": "sono e recuperação",
    "Autoconfianca / Autoeficacia": "autoeficácia e confiança",
    "Humor / Afeto": "humor e afeto",
    "Personalidade": "personalidade",
    "Coesao / Lideranca": "coesão e grupo",
}
SUBVARIAVEIS_PSICOLOGICAS = set(FAMILIA_DE_SUBVARIAVEL) | {"Percepcao de esforco"}


def triar(con: sqlite3.Connection) -> list[Decisao]:
    con.row_factory = sqlite3.Row
    subs: dict[int, set[str]] = {}
    for aid, s in con.execute("SELECT artigo_id, subvariavel FROM artigo_subvariavel"):
        subs.setdefault(aid, set()).add(s)
    return [avaliar(r, subs.get(r["id"], set()))
            for r in con.execute("SELECT * FROM artigo ORDER BY id")]


def fluxo_prisma(decisoes: list[Decisao]) -> dict:
    """Contagens do diagrama PRISMA, com um motivo por estudo excluído."""
    excluidos: dict[str, int] = {}
    for d in decisoes:
        if not d.incluido:
            excluidos[d.motivo] = excluidos.get(d.motivo, 0) + 1
    incluidos = [d for d in decisoes if d.incluido]
    return {
        "avaliados": len(decisoes),
        "incluidos": len(incluidos),
        "excluidos": len(decisoes) - len(incluidos),
        "por_motivo": {m: excluidos.get(m, 0) for m in MOTIVOS},
        "por_evidencia": {
            "instrumento nomeado": sum(1 for d in incluidos
                                       if d.evidencia == "instrumento nomeado"),
            "construto no resumo": sum(1 for d in incluidos
                                       if d.evidencia == "construto no resumo"),
        },
    }
