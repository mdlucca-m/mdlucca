"""Apresentação "Humor na Ginástica Rítmica e Esportes Estéticos" -- uma
aba PRIVADA no painel.

Pedido explícito do Mateus: "crie essa apresentação no painel do lape
somente para quem eu autorizar". Mesmo desenho de `ginastica_ritmica.py`
(mesma razão: uma tabela dedicada e pequena, em vez de dar privacidade por
linha numa tela grande e muito usada). O acesso é uma LISTA
(`apresentacao_humor_acesso`), não nomes fixos no código: quem concede e
quem revoga é a própria coordenação, escolhendo entre os integrantes já
cadastrados. `admin` sempre vê.

O conteúdo dos slides (`SLIDES`) é a mesma síntese entregue antes em
docx/apresentação (25 estudos verificados no PubMed, 1994-2026, sobre
humor em ginástica rítmica e esportes estéticos) -- fica em Python, e não
embutido no JS do painel, pelo mesmo motivo da lista de estudos da
ginástica rítmica: quem não tem acesso não deve conseguir ler o conteúdo
nem abrindo o código-fonte da página, só a rota (gated) devolve os dados.
"""
from __future__ import annotations

from typing import Any

from .db import Database


def tem_acesso(db: Database, member_id: int | None, user_role: str | None = None) -> bool:
    if user_role == "admin":
        return True
    if not member_id:
        return False
    return bool(db.scalar(
        "SELECT 1 FROM apresentacao_humor_acesso WHERE member_id = ?", (member_id,)))


def conceder(db: Database, member_id: int, concedido_por: int | None) -> None:
    db.execute(
        "INSERT INTO apresentacao_humor_acesso (member_id, concedido_por) VALUES (?, ?)"
        " ON CONFLICT (member_id) DO NOTHING", (member_id, concedido_por))
    db.conn.commit()


def revogar(db: Database, member_id: int) -> None:
    db.execute("DELETE FROM apresentacao_humor_acesso WHERE member_id = ?", (member_id,))
    db.conn.commit()


def quem_tem_acesso(db: Database) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT m.id, m.full_name, a.concedido_em"
        "  FROM apresentacao_humor_acesso a JOIN members m ON m.id = a.member_id"
        " ORDER BY m.full_name")


# ----------------------------------------------------------------------
# Conteúdo dos slides -- síntese de 25 estudos verificados no PubMed
# (1994-2026; busca e triagem documentadas na apresentação entregue ao
# Mateus). Cada item tem um "tipo" que diz ao painel como desenhar o
# slide; nenhuma citação aqui é inventada -- todas vieram de metadados
# reais (mcp__PubMed__get_article_metadata/search_articles).
# ----------------------------------------------------------------------
SLIDES: tuple[dict[str, Any], ...] = (
    {
        "tipo": "capa",
        "eyebrow": "Revisão da literatura",
        "titulo": "Humor em Ginástica Rítmica e Esportes Estéticos",
        "subtitulo": "O construto psicológico do humor nas modalidades estéticas de "
                      "competição — uma síntese de 25 estudos",
        "nota": "LAPE — Laboratório de Psicologia do Esporte e do Exercício · UDESC/CEFID",
    },
    {
        "tipo": "topicos", "eyebrow": "Sumário", "titulo": "Roteiro",
        "itens": [
            "Humor e esportes estéticos",
            "Método: mineração de dados",
            "Panorama temático",
            "Achados por tema",
            "Lacunas e fechamento",
        ],
    },
    {
        "tipo": "grade", "eyebrow": "Fundamentos", "titulo": "O que é \"humor\", aqui",
        "texto": "Humor (mood) é o estado afetivo transitório do atleta, medido sobretudo "
                 "pelo POMS (Profile of Mood States) e sua versão abreviada, o BRUMS "
                 "(Brunel Mood Scale) — seis dimensões que oscilam com o treino, a "
                 "competição e a pressão estética.",
        "cartoes": [
            {"titulo": "Tensão", "nota": "Tension–Anxiety"},
            {"titulo": "Depressão", "nota": "Depression–Dejection"},
            {"titulo": "Hostilidade", "nota": "Anger–Hostility"},
            {"titulo": "Vigor", "nota": "Vigor–Activity", "destaque": True},
            {"titulo": "Fadiga", "nota": "Fatigue–Inertia"},
            {"titulo": "Confusão", "nota": "Confusion–Bewilderment"},
        ],
    },
    {
        "tipo": "grade", "eyebrow": "Fundamentos",
        "titulo": "Esportes estéticos: a família em questão",
        "texto": "Modalidades julgadas por critérios de execução e expressão artística — "
                 "não apenas tempo, distância ou gols — o que as expõe de forma particular "
                 "à pressão estética sobre o corpo e o humor.",
        "cartoes": [
            {"titulo": "Ginástica Rítmica",
             "nota": "Foco desta revisão — a modalidade mais estudada no corpus", "destaque": True},
            {"titulo": "Ginástica Artística", "nota": "Aparelhos, acrobacia e precisão de execução"},
            {"titulo": "Patinação Artística",
             "nota": "Expressão sobre o gelo, julgamento de componentes do programa"},
            {"titulo": "Dança e afins",
             "nota": "Balé e modalidades de dança competitiva com critérios estéticos semelhantes"},
        ],
    },
    {
        "tipo": "funil", "eyebrow": "Método", "titulo": "Como os estudos foram encontrados",
        "texto": "Mineração de dados sobre o PubMed: quatro buscas combinatórias, "
                 "progressivamente ajustadas para afastar ruído (ex.: \"diving\" trazia "
                 "medicina de descompressão, não ginástica), seguidas de dois critérios "
                 "de elegibilidade.",
        "passos": [
            {"numero": "4", "legenda": "buscas combinatórias no PubMed"},
            {"numero": "57", "legenda": "registros brutos (5+7+13+32)"},
            {"numero": "2", "legenda": "critérios de elegibilidade aplicados"},
            {"numero": "25", "legenda": "estudos incluídos, 1994–2026", "destaque": True},
        ],
        "nota": "Critérios: (1) relação explícita entre humor/estado afetivo e um esporte "
                "estético competitivo; (2) peer review, idioma com resumo acessível e "
                "metadados verificáveis (PMID/DOI).",
    },
    {
        "tipo": "arvore", "eyebrow": "Panorama temático", "titulo": "Seis eixos nos 25 estudos",
        "raiz": "Humor nos Esportes Estéticos",
        "folhas": [
            {"n": 5, "rotulo": "Humor direto"},
            {"n": 2, "rotulo": "Carga e bem-estar"},
            {"n": 2, "rotulo": "Autofala e ansiedade"},
            {"n": 3, "rotulo": "Regulação emocional"},
            {"n": 7, "rotulo": "Pressão estética"},
            {"n": 6, "rotulo": "Saúde mental"},
        ],
    },
    {
        "tipo": "dendrograma", "eyebrow": "Panorama temático",
        "titulo": "Como os seis eixos se agrupam",
        "raiz": "25 estudos",
        "clusters": [
            {"n": 7, "rotulo": "Humor monitorado diretamente",
             "folhas": [{"n": 5, "rotulo": "Humor direto"}, {"n": 2, "rotulo": "Carga e bem-estar"}]},
            {"n": 18, "rotulo": "Bem-estar e saúde mental em sentido amplo",
             "folhas": [{"n": 2, "rotulo": "Autofala"}, {"n": 3, "rotulo": "Regulação emocional"},
                        {"n": 7, "rotulo": "Pressão estética"}, {"n": 6, "rotulo": "Saúde mental"}]},
        ],
    },
    {
        "tipo": "achado", "indice": "1 de 6", "n": 5,
        "titulo": "Humor medido diretamente",
        "texto": "Cinco estudos aplicaram POMS/BRUMS diretamente em ginastas e "
                 "patinadoras, ligando o perfil de humor a desempenho, lesão e etapa da "
                 "temporada.",
        "itens": [
            "Perfil de \"iceberg\" (vigor alto, demais fatores baixos) associado a melhor "
            "desempenho competitivo (Kolt & Kirkby, 1994)",
            "Humor pré-competitivo distingue atletas lesionadas de não lesionadas em "
            "ginástica (Harringe, Renström & Werner, 2007)",
            "Flutuações de humor acompanham a fase da temporada e a proximidade da "
            "competição (Filaire, Bonis & Lac, 2004; Boldizsár et al., 2016; Neves et al., 2016)",
        ],
    },
    {
        "tipo": "achado", "indice": "2 de 6", "n": 2,
        "titulo": "Carga de treinamento e humor",
        "texto": "Dois estudos usaram o humor como sensor da carga de treino, "
                 "acompanhando picos pré-competitivos.",
        "itens": [
            "Picos de carga de treino elevam fadiga e tensão e reduzem vigor em semanas "
            "pré-competitivas (Fernandes et al., 2022)",
            "Monitoramento do humor sinaliza acúmulo de carga antes de queda de "
            "desempenho ou lesão (Leupold et al., 2024)",
        ],
    },
    {
        "tipo": "achado", "indice": "3 de 6", "n": 2,
        "titulo": "Autofala e ansiedade",
        "texto": "Dois estudos mostram que a forma como a atleta fala consigo mesma "
                 "amortece a ansiedade e sustenta o humor positivo.",
        "itens": [
            "Autofala positiva associa-se a menor ansiedade competitiva em ginastas de "
            "rítmica (Gómez-Landero et al., 2025)",
            "Otimismo disposicional modera a relação entre estresse competitivo e estado "
            "de humor (van Bokhorst et al., 2016)",
        ],
    },
    {
        "tipo": "achado", "indice": "4 de 6", "n": 3,
        "titulo": "Regulação emocional e intervenção",
        "texto": "Três estudos testaram estratégias de regulação emocional como via de "
                 "melhora do humor e de redução de exaustão.",
        "itens": [
            "Intervenções de regulação emocional reduzem exaustão e melhoram estado de "
            "humor em ginastas jovens (Duan et al., 2022)",
            "Estratégias de reavaliação cognitiva amortecem o impacto do estresse "
            "competitivo sobre o humor (Zhang & Ma, 2025)",
            "Programas de recuperação psicológica (incl. balneoterapia) favorecem "
            "estados de humor mais positivos (Stepanenko et al., 2017)",
        ],
    },
    {
        "tipo": "achado", "indice": "5 de 6", "n": 7,
        "titulo": "Perfeccionismo e pressão estética",
        "texto": "O maior grupo temático (7 estudos): perfeccionismo, insatisfação "
                 "corporal e pressão por peso associados a humor mais negativo.",
        "itens": [
            "Perfeccionismo \"preocupado\" prediz maior exaustão e pior humor ao longo da "
            "temporada (St-Cyr et al., 2024)",
            "Pressão estética sobre o corpo associa-se a sintomas de transtorno "
            "alimentar e a estados de humor negativos (Kipp, Bolter & Phillips Reichter, "
            "2019; Casper, Michaels & Simon, 1997)",
            "Insatisfação corporal e cobrança por magreza elevam ansiedade e rebaixam o "
            "humor em ginastas (Krentz & Warschburger, 2011; Paixão, Oliveira & Ferreira, 2020)",
            "Clima motivacional voltado à performance estética amplifica a pressão "
            "percebida (Mayolas-Pi et al., 2020; Nordin-Bates & Jowett, 2021)",
        ],
    },
    {
        "tipo": "achado", "indice": "6 de 6", "n": 6,
        "titulo": "Saúde mental e epidemiologia",
        "texto": "Seis estudos recentes (2023–2026) tratam o humor negativo persistente "
                 "como porta de entrada para quadros clínicos mais amplos.",
        "itens": [
            "Prevalência elevada de sintomas depressivos e ansiosos em atletas de elite "
            "de esportes estéticos (Reardon & Hitchcock, 2024; Jederström et al., 2023)",
            "Sofrimento psicológico subnotificado nessas modalidades reforça a "
            "necessidade de triagem regular (Pomerleau-Fontaine et al., 2026; Saroha et al., 2026)",
            "Comportamentos alimentares de risco coocorrem com humor negativo e "
            "sintomas de ansiedade (Cordero et al., 2026; Ni et al., 2026)",
        ],
    },
    {
        "tipo": "topicos", "eyebrow": "Fechamento", "titulo": "Lacunas e direções futuras",
        "itens": [
            "Desenhos majoritariamente transversais — a direção causal entre pressão "
            "estética e humor permanece pouco testada",
            "Ginástica rítmica ainda minoritária — boa parte do corpus trata esportes "
            "estéticos em geral",
            "Instrumentos genéricos de humor — POMS/BRUMS não foram desenhados para o "
            "contexto estético competitivo",
            "Intervenções pouco testadas no contexto — raramente replicadas em "
            "ginástica rítmica, onde a pressão estética é mais marcada",
        ],
    },
    {
        "tipo": "fechamento", "eyebrow": "Perguntas e discussão", "titulo": "Obrigado.",
        "texto": "Síntese baseada em 25 estudos verificados no PubMed (1994–2026) sobre "
                 "humor em ginástica rítmica e esportes estéticos.",
        "nota": "LAPE — Laboratório de Psicologia do Esporte e do Exercício · UDESC/CEFID",
    },
)


def listar_slides() -> list[dict[str, Any]]:
    return [dict(slide) for slide in SLIDES]
