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

# (codigo, nome, descricao, palavras-chave, icone)
# As palavras-chave nao sao enfeite: e por elas que a busca da tela
# encontra a linha, e sao a ponte com o vocabulario de variaveis.
LINHAS: tuple[tuple[str, str, str, str, str], ...] = (
    ("atividade_fisica_saude", "Atividade Física e Saúde",
     "Investiga a relação entre o movimento habitual e os desfechos de saúde na "
     "população geral. Interessa o quanto uma pessoa se move, com que constância, "
     "e o que disso se converte em aptidão física, autonomia e redução de risco.",
     "atividade física; saúde; sedentarismo; aptidão física; qualidade de vida",
     "corrida"),
    ("psicologia_exercicio", "Psicologia do Exercício",
     "Examina os processos psicológicos que sustentam a prática regular de "
     "exercício. A pergunta central não é o que o corpo faz, e sim o que leva "
     "alguém a começar, a permanecer e a voltar depois da interrupção.",
     "exercício; motivação; aderência; humor; bem-estar; autoeficácia",
     "halteres"),
    ("psicologia_do_esporte", "Psicologia do Esporte",
     "Estuda a mente sob competição. Ansiedade pré-competitiva, foco, coesão de "
     "equipe e regulação emocional respondem por parte do desempenho que o "
     "treinamento físico, sozinho, não explica.",
     "esporte; atletas; ansiedade competitiva; desempenho; coesão de equipe",
     "trofeu"),
    ("qualidade_do_ar", "Qualidade do ar e poluição no exercício e no esporte",
     "Mede o custo de treinar no ar que há. O exercício multiplica o volume "
     "respirado, e com ele a dose de material particulado que alcança o pulmão "
     "de quem corre, pedala ou compete a céu aberto.",
     "poluição; qualidade do ar; material particulado; exercício ao ar livre; ozônio",
     "pulmao"),
    ("exercicio_fibromialgia", "Exercício na saúde física e mental na Fibromialgia",
     "Trata o exercício como intervenção clínica na fibromialgia. Dor difusa, sono "
     "fragmentado, fadiga e sintomas depressivos respondem à carga, à intensidade "
     "e à progressão, e é essa dose que a linha procura estabelecer.",
     "fibromialgia; dor crônica; treinamento resistido; impacto da doença; sono",
     "dor"),
    ("exercicio_cancer", "Exercício na saúde mental no tratamento do câncer",
     "Acompanha o exercício ao longo do tratamento oncológico e depois dele. "
     "Fadiga, ansiedade, sintomas depressivos e qualidade de vida constituem os "
     "desfechos, em pacientes cuja tolerância ao esforço muda de semana para semana.",
     "câncer; oncologia; fadiga; depressão; ansiedade; qualidade de vida",
     "fita"),
    ("exercicio_envelhecimento", "Exercício na saúde mental no envelhecimento",
     "Observa o que o exercício preserva quando os anos avançam. Cognição, humor, "
     "autonomia funcional e vínculo social envelhecem em ritmos distintos, e a "
     "prática regular altera esse ritmo.",
     "envelhecimento; idosos; cognição; depressão; autonomia funcional",
     "envelhecimento"),
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
    for codigo, nome, descricao, palavras, _icone in LINHAS:
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


def icone_de(codigo: str | None, nome: str | None) -> str:
    """O icone da linha, pelo codigo ou pelo nome -- "linha" quando nao ha.

    Precisa das duas perguntas pelo mesmo motivo de `_achar`: uma linha
    instalada aqui pode ter sido encontrada pelo nome e guardada com outro
    codigo, e ai a busca so por codigo devolveria o icone generico para uma
    linha que tem o seu. Uma linha que o laboratorio criou a mao continua
    com o icone neutro, e isso e o certo: inventar "corrida" para uma linha
    que ninguem descreveu seria a tela afirmando o que nao sabe.
    """
    from .util import norm_key

    if codigo:
        for c, _n, _d, _p, icone in LINHAS:
            if c == codigo:
                return icone
    if nome:
        alvo = norm_key(nome)
        for _c, n, _d, _p, icone in LINHAS:
            if norm_key(n) == alvo:
                return icone
    return "linha"
