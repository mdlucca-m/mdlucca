"""Fichas repetidas da mesma pessoa, propostas para fusao.

A planilha que abastece o laboratorio lista os autores de cada artigo em
formato livre, e nem sempre no mesmo formato. Num artigo saiu
"Alexandro"; em dezoito, "Andrade". Sao a mesma pessoa e viraram duas
fichas, porque a chave de autor e montada sobre o sobrenome e "alexandro"
nao encontra "andrade_a" de maneira nenhuma.

O que este modulo NAO faz e decidir sozinho. "Henrique" e "Henrique
Fukumasa" tem a mesma forma de "Alexandro" e "Alexandro Andrade", e
podem ser duas pessoas -- um laboratorio com vinte integrantes tem dois
Henriques com facilidade. Fundir por conta propria juntaria a producao de
duas pessoas num nome so, e desfazer isso depois exige saber qual artigo
era de quem, que e exatamente a informacao que se perdeu na fusao.

Entao: aqui se PROPOE, com a evidencia ao lado, e quem conhece a equipe
confirma.
"""
from __future__ import annotations

from typing import Any

from .db import Database
from .util import norm_key


def _primeiro_nome(nome: str) -> str:
    partes = str(nome or "").strip().split()
    return norm_key(partes[0]) if partes else ""


def _tokens(nome: str) -> list[str]:
    return [p for p in str(nome or "").strip().split() if p]


def candidatos(db: Database) -> list[dict[str, Any]]:
    """Pares que parecem a mesma pessoa, do mais evidente ao menos.

    A forma procurada e sempre a mesma: uma ficha de UM nome so, que e o
    primeiro nome de outra ficha mais completa. E ha uma condicao de
    seguranca: as duas nunca podem assinar o mesmo artigo. Se assinam,
    ou sao pessoas diferentes, ou a lista de autores daquele artigo esta
    errada -- e nos dois casos fundir seria apagar a evidencia.
    """
    pessoas = db.dicts(
        "SELECT id, full_name, short_name, role, is_external FROM members"
        " WHERE is_external = 0 ORDER BY id")
    artigos = {}
    for linha in db.dicts("SELECT member_id, article_id FROM article_authors"
                          " WHERE member_id IS NOT NULL"):
        artigos.setdefault(linha["member_id"], set()).add(linha["article_id"])

    curtas = [p for p in pessoas if len(_tokens(p["full_name"])) == 1]
    achados = []
    for curta in curtas:
        alvo = norm_key(curta["full_name"])
        for cheia in pessoas:
            if cheia["id"] == curta["id"] or len(_tokens(cheia["full_name"])) < 2:
                continue
            if _primeiro_nome(cheia["full_name"]) != alvo:
                continue
            juntos = artigos.get(curta["id"], set()) & artigos.get(cheia["id"], set())
            if juntos:
                continue
            achados.append({
                "sumir": {"id": curta["id"], "nome": curta["full_name"],
                          "artigos": len(artigos.get(curta["id"], set()))},
                "manter": {"id": cheia["id"], "nome": cheia["full_name"],
                           "papel": cheia["role"],
                           "artigos": len(artigos.get(cheia["id"], set()))},
                "porque": (f"“{curta['full_name']}” e o primeiro nome de "
                           f"“{cheia['full_name']}”, e as duas fichas nunca "
                           f"assinam o mesmo artigo"),
            })
    # A ficha mais completa primeiro: e onde a decisao e mais facil e o
    # ganho, maior.
    achados.sort(key=lambda x: (-x["manter"]["artigos"], x["sumir"]["nome"]))
    return achados


# Fusoes que a coordenacao ja conferiu e confirmou. Ficam escritas aqui
# pelo mesmo motivo das linhas de pesquisa e das grafias dos professores:
# sao decisao do laboratorio, valem para toda instalacao e nao se
# redigitam. Cada par e (ficha que fica, ficha que sai) POR NOME.
#
# Entrar nesta lista nao dispensa a conferencia: a fusao so acontece se o
# encaixe de `e_fantasma_de` continuar valendo no banco em que ela roda --
# ficha de um nome so, primeiro nome igual, nenhum artigo em comum. Uma
# linha aqui diz "ja perguntamos a quem sabe"; nao diz "junte de qualquer
# maneira".
FUSOES_DECLARADAS: tuple[tuple[str, str], ...] = (
    # Um artigo trouxe "Henrique" e outro, "Henrique Fukumasa": a planilha
    # listou os autores so pelo primeiro nome num deles. Sao a mesma
    # pessoa, conferido com a coordenacao do LAPE.
    ("Henrique Fukumasa", "Henrique"),
)


def aplicar_declaradas(db: Database) -> list[dict[str, Any]]:
    """Junta as fichas da lista acima, se ainda houver o que juntar.

    Roda na subida do servico. E silenciosa quando nao ha nada a fazer, o
    que e o caso na segunda vez em diante: a ficha antiga deixou de
    existir e a grafia dela ja esta guardada como variacao do nome.
    """
    feitas = []
    for nome_fica, nome_sai in FUSOES_DECLARADAS:
        fica = db.member_id(nome_fica, create=False)
        sai = db.member_id(nome_sai, create=False)
        if not fica or not sai or fica == sai:
            continue
        if not e_fantasma_de(db, sai, fica):
            continue
        feitas.append(fundir(db, manter_id=fica, sumir_id=sai))
    return feitas


def e_fantasma_de(db: Database, ficha_id: int, pessoa_id: int) -> bool:
    """A ficha `ficha_id` e so um pedaco do nome de `pessoa_id`?

    As mesmas duas perguntas de `candidatos`, feitas sobre um par ja
    escolhido: a ficha suspeita tem UM nome so, e esse nome e o primeiro
    nome da outra? E as duas nunca assinam o mesmo artigo?

    Serve ao caso em que a coordenacao ja declarou a grafia -- ai nao ha o
    que propor a ninguem, porque a resposta ja foi dada por escrito.
    """
    fichas = {p["id"]: p for p in db.dicts(
        "SELECT id, full_name FROM members WHERE id IN (?, ?)", (ficha_id, pessoa_id))}
    if ficha_id not in fichas or pessoa_id not in fichas or ficha_id == pessoa_id:
        return False
    curto, cheio = fichas[ficha_id]["full_name"], fichas[pessoa_id]["full_name"]
    if len(_tokens(curto)) != 1 or len(_tokens(cheio)) < 2:
        return False
    if norm_key(curto) != _primeiro_nome(cheio):
        return False
    juntos = db.scalar(
        "SELECT COUNT(*) FROM article_authors a JOIN article_authors b"
        "    ON a.article_id = b.article_id"
        " WHERE a.member_id = ? AND b.member_id = ?", (ficha_id, pessoa_id))
    return not juntos


def fundir(db: Database, manter_id: int, sumir_id: int) -> dict[str, Any]:
    """Junta as duas fichas e guarda a grafia que sumiu como variacao.

    Guardar a grafia nao e detalhe: sem ela, a proxima importacao da mesma
    planilha reencontra "Alexandro", nao acha ninguem com essa chave e cria
    a ficha de novo. O trabalho seria refeito a cada mes, sem que nada na
    tela dissesse por que a duplicata voltou.
    """
    if manter_id == sumir_id:
        raise ValueError("uma ficha nao se funde com ela mesma")
    fichas = {p["id"]: p for p in db.dicts(
        "SELECT id, full_name FROM members WHERE id IN (?, ?)", (manter_id, sumir_id))}
    if manter_id not in fichas or sumir_id not in fichas:
        raise ValueError("ficha nao encontrada")

    grafia = fichas[sumir_id]["full_name"]
    antes = int(db.scalar("SELECT COUNT(*) FROM article_authors WHERE member_id = ?",
                          (sumir_id,)) or 0)
    db.merge_members(sumir_id, manter_id)
    # A grafia so entra DEPOIS da fusao: enquanto a ficha antiga existe, a
    # chave dela pertence a outro integrante e o cadastro recusa o apelido.
    try:
        db.register_alias(grafia, manter_id)
    except ValueError:
        pass
    db.conn.commit()
    return {"manter": fichas[manter_id]["full_name"], "sumiu": grafia,
            "artigos_movidos": antes,
            "artigos_agora": int(db.scalar(
                "SELECT COUNT(*) FROM article_authors WHERE member_id = ?",
                (manter_id,)) or 0)}
