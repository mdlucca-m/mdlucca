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


def contagem(db: Database) -> dict[str, int]:
    """Quantos de cada lado -- e quantos esperam confirmacao."""
    return {
        "pesquisadores": int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE COALESCE(is_external, 0) = 0"
            "   AND COALESCE(active, 1) = 1") or 0),
        "coautores": int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE is_external = 1") or 0),
        "a_confirmar": len(candidatos(db)),
    }
