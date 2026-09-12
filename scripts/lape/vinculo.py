"""Quem e do laboratorio e quem assinou um artigo com o laboratorio.

Sao duas coisas diferentes, e o sistema as tratava como uma so. Qualquer
nome que aparecesse na lista de autores de um artigo virava ficha de
integrante: `db.member_id(create=True)` gravava `is_external = 0`, que e
o padrao da coluna. O orientador de fora, o colega de outra universidade,
o estatistico convidado e o coautor internacional entravam todos como
"pesquisador do LAPE" -- e iam parar na contagem da equipe, no
organograma e no indice de pesquisadores do painel.

A partir daqui quem so assina nasce coautor. Este modulo cuida do que ja
estava gravado antes disso.

O que ele NAO faz e decidir sozinho. Nao existe no banco nenhum sinal que
prove que alguem e do laboratorio: existem indicios (funcao declarada,
e-mail, Lattes, data de entrada, login, orientacao, projeto, presenca em
atividade). A ausencia de todos eles e um forte indicio de que a ficha
nasceu de uma autoria e nunca foi cadastrada por ninguem -- mas e indicio,
nao prova. A professora que ninguem terminou de cadastrar tem a mesma
ficha vazia do coautor de Toronto.

Entao: aqui se PROPOE, com a evidencia ao lado, e quem conhece a equipe
confirma. E a promocao de volta e um clique, porque errar para o lado do
coautor e reversivel e errar para o outro lado infla a equipe em silencio.
"""
from __future__ import annotations

from typing import Any

from .db import Database

# Os sinais de que alguem foi cadastrado como integrante, e nao apenas
# encontrado numa lista de autores. Qualquer um deles basta.
SINAIS = (
    ("role IS NOT NULL AND TRIM(role) <> ''", "vínculo declarado"),
    ("email IS NOT NULL AND TRIM(email) <> ''", "e-mail"),
    ("lattes_id IS NOT NULL AND TRIM(lattes_id) <> ''", "Lattes"),
    ("orcid IS NOT NULL AND TRIM(orcid) <> ''", "ORCID"),
    ("joined_on IS NOT NULL AND TRIM(joined_on) <> ''", "data de entrada"),
    ("login IS NOT NULL AND TRIM(login) <> ''", "conta no sistema"),
    ("advisor_id IS NOT NULL", "orientador apontado"),
    ("thesis_title IS NOT NULL AND TRIM(thesis_title) <> ''", "trabalho de conclusão"),
    ("degree IS NOT NULL AND TRIM(degree) <> ''", "formação"),
    ("scholarship IS NOT NULL AND TRIM(scholarship) <> ''", "bolsa"),
    ("research_line_id IS NOT NULL", "linha de pesquisa"),
    ("(SELECT COUNT(*) FROM project_members pm WHERE pm.member_id = m.id) > 0",
     "projeto"),
    ("(SELECT COUNT(*) FROM projects p WHERE p.coordinator_id = m.id) > 0",
     "coordenação de projeto"),
    ("(SELECT COUNT(*) FROM event_participants ep WHERE ep.member_id = m.id) > 0",
     "presença em atividade"),
    ("(SELECT COUNT(*) FROM members o WHERE o.advisor_id = m.id"
     "    OR o.co_advisor_id = m.id) > 0", "orienta alguém"),
)


def sinais_de(db: Database, member_id: int) -> list[str]:
    """Os indicios de vinculo que a ficha apresenta, em portugues."""
    achados = []
    for condicao, rotulo in SINAIS:
        if db.scalar(f"SELECT COUNT(*) FROM members m WHERE m.id = ? AND ({condicao})",
                     (member_id,)):
            achados.append(rotulo)
    return achados


def candidatos(db: Database) -> list[dict[str, Any]]:
    """Fichas marcadas como do LAPE que nao trazem sinal nenhum de vinculo.

    Ordenadas por numero de artigos, decrescente: a ficha com dezoito
    artigos e a que mais pesa no painel se estiver do lado errado, e e
    tambem a que a coordenacao reconhece mais depressa.
    """
    condicao = " OR ".join(f"({c})" for c, _ in SINAIS)
    linhas = db.dicts(
        f"""
        SELECT m.id, m.full_name, m.short_name,
               (SELECT COUNT(DISTINCT aa.article_id) FROM article_authors aa
                 WHERE aa.member_id = m.id) AS n_artigos,
               (SELECT GROUP_CONCAT(t.title, ' | ') FROM (
                    SELECT a.title FROM article_authors aa
                      JOIN articles a ON a.id = aa.article_id
                     WHERE aa.member_id = m.id
                     ORDER BY COALESCE(a.year_published, 0) DESC LIMIT 3) t
               ) AS exemplos
          FROM members m
         WHERE COALESCE(m.is_external, 0) = 0
           AND COALESCE(m.active, 1) = 1
           AND NOT ({condicao})
         ORDER BY n_artigos DESC, m.full_name
        """)
    # Uma ficha sem sinal de vinculo E sem artigo nenhum nao e coautor de
    # coisa nenhuma -- e um registro solto, que virou nada. Propor que ela
    # vire "coautor" seria inventar uma autoria que nao existe.
    return [linha for linha in linhas if (linha["n_artigos"] or 0) > 0]


def marcar(db: Database, member_id: int, coautor: bool) -> dict[str, Any]:
    """Move uma ficha entre as duas categorias.

    Vale nos dois sentidos: a coordenacao marca como coautor quem entrou
    por engano, e promove a integrante quem o sistema classificou mal. Os
    vinculos de autoria dos artigos acompanham, senao a tela de um artigo
    diria "externo" e a ficha da pessoa diria "do LAPE".
    """
    pessoa = db.dicts("SELECT id, full_name, is_external FROM members WHERE id = ?",
                      (member_id,))
    if not pessoa:
        raise ValueError(f"ficha {member_id} nao encontrada")
    novo = 1 if coautor else 0
    db.execute("UPDATE members SET is_external = ? WHERE id = ?", (novo, member_id))
    db.execute("UPDATE article_authors SET is_external = ? WHERE member_id = ?",
               (novo, member_id))
    db.conn.commit()
    return {"id": member_id, "quem": pessoa[0]["full_name"],
            "categoria": "coautor" if novo else "pesquisador do LAPE",
            "sinais": sinais_de(db, member_id)}


def soltas(db: Database) -> list[dict[str, Any]]:
    """Fichas sem sinal de vinculo E sem artigo nenhum.

    `candidatos` nao as inclui de proposito: quem nao assinou nada nao e
    coautor de coisa alguma, e propor que vire "coautor" seria inventar
    uma autoria que nao existe.

    So que elas tambem nao sao integrantes. Sao registros que viraram
    nada -- restos de importacao, nome digitado duas vezes, cadastro
    comecado e abandonado -- e enquanto ficam ativos contam na equipe e
    aparecem como "sem vinculo declarado" no painel, que foi exatamente a
    queixa que trouxe isto aqui.

    O lugar certo delas nao e o lixo: e `active = 0`. A ficha continua no
    banco, para o caso de alguem reconhecer o nome depois, e some de toda
    contagem de equipe -- que e o que se queria.
    """
    condicao = " OR ".join(f"({c})" for c, _ in SINAIS)
    return db.dicts(
        f"""
        SELECT m.id, m.full_name, m.short_name, m.created_at
          FROM members m
         WHERE COALESCE(m.is_external, 0) = 0
           AND COALESCE(m.active, 1) = 1
           AND NOT ({condicao})
           AND NOT EXISTS (SELECT 1 FROM article_authors aa WHERE aa.member_id = m.id)
         ORDER BY m.full_name
        """)


def arquivar_em_lote(db: Database, ids: list[int], ativo: bool = False) -> dict[str, Any]:
    """Tira da equipe sem apagar. `ativo=True` traz de volta.

    So aceita ids que estao na lista de soltas AGORA -- entre a tela abrir
    e o botao ser clicado, uma delas pode ter ganhado artigo ou vinculo, e
    arquivar essa seria esconder gente de verdade.
    """
    elegiveis = {f["id"] for f in soltas(db)} if not ativo else None
    movidas, recusadas = [], []
    for bruto in ids or []:
        try:
            member_id = int(bruto)
        except (TypeError, ValueError):
            continue
        if elegiveis is not None and member_id not in elegiveis:
            recusadas.append({"id": member_id,
                              "motivo": "deixou de ser ficha solta desde que a "
                                        "lista foi montada"})
            continue
        pessoa = db.dicts("SELECT full_name FROM members WHERE id = ?", (member_id,))
        if not pessoa:
            recusadas.append({"id": member_id, "motivo": "ficha não encontrada"})
            continue
        db.execute("UPDATE members SET active = ?, updated_at = datetime('now')"
                   " WHERE id = ?", (1 if ativo else 0, member_id))
        movidas.append({"id": member_id, "quem": pessoa[0]["full_name"]})
    if movidas:
        db.conn.commit()
    return {"movidas": len(movidas), "quais": movidas, "recusadas": recusadas,
            "desfazer": [m["id"] for m in movidas],
            "para": "ativa" if ativo else "arquivada"}


def marcar_em_lote(db: Database, ids: list[int], coautor: bool = True) -> dict[str, Any]:
    """Move varias fichas de uma vez, e devolve o que mover de volta.

    A tela nasceu de uma em uma de proposito: a ficha vazia da professora
    que ninguem terminou de cadastrar e identica a do coautor de outra
    universidade, e so quem conhece a equipe sabe qual e qual.

    So que "de uma em uma" com cinquenta e quatro fichas nao e cuidado --
    e a garantia de que ninguem vai fazer, e de que o organograma fica
    para sempre com cinquenta e quatro pessoas sem vinculo no meio. Entao
    o lote existe, com tres amarras:

      1. So aceita ids que estao na proposta AGORA. Um id que ganhou sinal
         de vinculo entre a tela abrir e o botao ser clicado -- porque a
         pessoa acabou de se cadastrar -- e recusado, e nao movido.
      2. Devolve `desfazer`, a lista do que mudou de fato, para que a volta
         seja um pedido so e nao cinquenta e quatro.
      3. Nao apaga nada. `is_external` e uma coluna; a ficha, os artigos e
         a autoria continuam todos la.
    """
    elegiveis = {c["id"] for c in candidatos(db)}
    movidos, recusados = [], []
    for bruto in ids or []:
        try:
            member_id = int(bruto)
        except (TypeError, ValueError):
            continue
        if coautor and member_id not in elegiveis:
            pessoa = db.dicts("SELECT full_name FROM members WHERE id = ?", (member_id,))
            recusados.append({
                "id": member_id,
                "quem": pessoa[0]["full_name"] if pessoa else None,
                "motivo": "ganhou sinal de vínculo desde que a lista foi montada"
                          if pessoa else "ficha não encontrada"})
            continue
        try:
            movidos.append(marcar(db, member_id, coautor))
        except ValueError as erro:
            recusados.append({"id": member_id, "quem": None, "motivo": str(erro)})
    return {
        "movidos": len(movidos), "quais": movidos, "recusados": recusados,
        "desfazer": [m["id"] for m in movidos],
        "para": "coautor" if coautor else "pesquisador do LAPE",
    }


def contagem(db: Database) -> dict[str, int]:
    """Quantos de cada lado -- e quantos esperam confirmacao."""
    return {
        "pesquisadores": int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE COALESCE(is_external, 0) = 0"
            "   AND COALESCE(active, 1) = 1") or 0),
        "coautores": int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE is_external = 1") or 0),
        "a_confirmar": len(candidatos(db)),
        "soltas": len(soltas(db)),
    }
