"""As linhas de pesquisa do LAPE, como o laboratorio as declarou.

Ficam escritas aqui pelo mesmo motivo do vocabulario de variaveis: sao a
espinha do laboratorio, mudam de ano em ano e nao de dia em dia, e ter de
redigita-las a cada instalacao e um convite a divergencia -- uma maquina
com "Psicologia do Esporte", outra com "Psicologia do esporte", e o painel
contando duas linhas onde ha uma.

Instalar de novo nao apaga o que foi mexido: o `code` e a chave, e uma
linha ja existente so tem preenchido o que estiver em branco. Quem
renomeou, descreveu melhor ou apontou a coordenacao continua com o que
escreveu.
"""
from __future__ import annotations

from typing import Any

from .db import Database

# (codigo, nome, descricao, palavras-chave)
# As palavras-chave nao sao enfeite: e por elas que a busca da tela
# encontra a linha, e sao a ponte com o vocabulario de variaveis.
LINHAS: tuple[tuple[str, str, str, str], ...] = (
    ("atividade_fisica_saude", "Atividade Física e Saúde",
     "Prática de atividade física e seus desfechos de saúde na população geral.",
     "atividade física; saúde; sedentarismo; aptidão física; qualidade de vida"),
    ("psicologia_exercicio", "Psicologia do Exercício",
     "Processos psicológicos associados à prática regular de exercício físico.",
     "exercício; motivação; aderência; humor; bem-estar; autoeficácia"),
    ("psicologia_do_esporte", "Psicologia do Esporte",
     "Aspectos psicológicos do desempenho, do treinamento e da competição.",
     "esporte; atletas; ansiedade competitiva; desempenho; coesão de equipe"),
    ("qualidade_do_ar", "Qualidade do ar e poluição no exercício e no esporte",
     "Efeitos da poluição atmosférica sobre quem treina e compete ao ar livre.",
     "poluição; qualidade do ar; material particulado; exercício ao ar livre; ozônio"),
    ("exercicio_fibromialgia", "Exercício na saúde física e mental na Fibromialgia",
     "Exercício como tratamento da fibromialgia: dor, impacto da doença e saúde mental.",
     "fibromialgia; dor crônica; treinamento resistido; impacto da doença; sono"),
    ("exercicio_cancer", "Exercício na saúde mental no tratamento do câncer",
     "Exercício durante e após o tratamento oncológico, com foco em saúde mental.",
     "câncer; oncologia; fadiga; depressão; ansiedade; qualidade de vida"),
    ("exercicio_envelhecimento", "Exercício na saúde mental no envelhecimento",
     "Exercício e saúde mental ao longo do envelhecimento.",
     "envelhecimento; idosos; cognição; depressão; autonomia funcional"),
)


def _achar(db: Database, codigo: str, nome: str):
    """A linha que ja existe, se existir -- por codigo ou por nome.

    So por codigo, uma linha antiga que por acaso ocupasse o mesmo codigo
    engoliria a nova em silencio: foi o que aconteceu com "Psicologia do
    Esporte", que ficou de fora porque o banco ja tinha "Psicologia do
    Esporte e do Exercicio" no codigo `psicologia_esporte`. So por nome,
    uma linha renomeada a mao viraria duas. As duas perguntas cobrem os
    dois casos, e a comparacao de nome ignora caixa e acento.
    """
    from .util import norm_key

    achado = db.dicts(
        "SELECT id, name FROM research_lines WHERE code = ? OR name = ?",
        (codigo, nome))
    if achado:
        return achado[0]
    alvo = norm_key(nome)
    for linha in db.dicts("SELECT id, name FROM research_lines"):
        if norm_key(linha["name"]) == alvo:
            return linha
    return None


def instalar(db: Database) -> dict[str, Any]:
    """Poe as linhas no banco. Rodar de novo nao desfaz o que foi mexido."""
    novas, ja_havia = [], []
    for codigo, nome, descricao, palavras in LINHAS:
        achado = _achar(db, codigo, nome)
        if achado:
            # Preenche buraco pelo ID -- nao pelo codigo. Gravar por codigo
            # criaria uma segunda linha quando a existente foi encontrada
            # pelo nome e tem outro codigo. E nao se toca em `name`: quem
            # reescreveu o nome na tela continua com o dele.
            db.execute(
                "UPDATE research_lines"
                "   SET description = COALESCE(NULLIF(TRIM(description), ''), ?),"
                "       keywords    = COALESCE(NULLIF(TRIM(keywords), ''), ?),"
                "       active      = 1"
                " WHERE id = ?",
                (descricao, palavras, achado["id"]))
            ja_havia.append(achado["name"])
            continue
        db.upsert("research_lines", {
            "code": codigo, "name": nome, "description": descricao,
            "keywords": palavras, "active": 1,
        }, conflict=("code",))
        novas.append(nome)
    db.conn.commit()
    return {"novas": novas, "ja_havia": ja_havia, "total": len(LINHAS)}
