"""Fonte única da estratégia de busca.

Os blocos conceituais abaixo são a definição normativa da busca. As consultas
de cada base são *geradas* a partir deles, de modo que atualizar a estratégia
seja a edição de um único arquivo, e não a reescrita de seis strings de sintaxe
divergente.

Blocos (PCC):
    POPULACAO  - handebol; sem descritor controlado disponível (ver nota)
    CONCEITO   - variáveis psicológicas; vocabulário controlado + termo livre
    CONTEXTO   - treinamento e competição

Nota metodológica: não existe descritor MeSH para handebol (verificado no MeSH
Browser da NLM). O bloco de população depende integralmente de termo livre em
todas as bases.
"""
from __future__ import annotations

JANELA = (2006, 2026)

# ── População ───────────────────────────────────────────────────────────────
POPULACAO_LIVRE = [
    "handball", "team handball", "beach handball", "handball player",
    "handball players", "handball athlete", "handball athletes",
    "handball practitioner", "handball practitioners", "handball training",
    "amateur handball", "recreational handball", "youth handball",
    "female handball", "male handball", "handball team",
]

# ── Conceito ────────────────────────────────────────────────────────────────
CONCEITO_MESH = [
    "Affect", "Emotions", "Anxiety", "Stress, Psychological", "Motivation",
    "Self Efficacy", "Burnout, Psychological", "Sleep", "Mental Health",
    "Adaptation, Psychological", "Depression", "Cognition",
    "Resilience, Psychological", "Personality", "Mood Disorders", "Fatigue",
]

CONCEITO_DECS = [
    "Afeto", "Emoções", "Ansiedade", "Estresse Psicológico", "Motivação",
    "Autoeficácia", "Esgotamento Psicológico", "Sono", "Saúde Mental",
    "Adaptação Psicológica", "Depressão", "Cognição", "Resiliência Psicológica",
    "Personalidade", "Fadiga",
]

# Termos de assunto para bases que indexam por palavra-chave de autor / termo
# de índice (Scopus, WoS). Descritor MeSH em forma invertida — "Stress,
# Psychological" — praticamente nunca casa nesses índices; usa-se aqui a forma
# corrente do termo.
CONCEITO_ASSUNTO = [
    "affect", "emotion", "emotions", "anxiety", "psychological stress",
    "motivation", "self-efficacy", "burnout", "sleep", "mental health",
    "coping", "depression", "cognition", "resilience", "personality",
    "mood", "fatigue",
]

CONCEITO_LIVRE = [
    "BRUMS", "CSAI", "Hooper index", "PANAS", "POMS", "RESTQ", "STAI",
    "affective state", "anxiety", "athlete burnout", "burnout",
    "cognitive anxiety", "competitive anxiety", "coping", "coping strategies",
    "depression", "depressive symptoms", "dropout", "ego orientation",
    "emotion regulation", "emotional exhaustion", "feeling scale",
    "goal orientation", "goal setting", "imagery", "insomnia",
    "intrinsic motivation", "mental health", "mental toughness",
    "mental training", "mindfulness", "mood", "mood state", "motivation",
    "negative affect", "perceived competence", "perceived recovery",
    "perceived stress", "positive affect", "psychological distress",
    "psychological skills", "psychological stress", "quality of life",
    "resilience", "self-confidence", "self-determination", "self-efficacy",
    "self-talk", "sleep", "sleep quality", "sleepiness", "somatic anxiety",
    "state anxiety", "stress", "task orientation", "total mood disturbance",
    "trait anxiety", "vigor", "vigour", "well-being", "wellbeing", "wellness",
]

# ── Contexto ────────────────────────────────────────────────────────────────
CONTEXTO_MESH = [
    "Athletic Performance", "Physical Conditioning, Human",
    "Competitive Behavior", "Athletes", "Team Sports", "Sports",
]

CONTEXTO_LIVRE = [
    "championship", "competition", "competitive", "competitive season",
    "elite athlete", "elite athletes", "game", "in-season", "league",
    "match", "match play", "matches", "official match", "practice",
    "pre-season", "preparation period", "professional athlete",
    "professional athletes", "season", "sport training", "team sport",
    "tournament", "training", "training camp", "training load",
    "training session", "youth athlete",
]


# ── Geradores de sintaxe ────────────────────────────────────────────────────
def _ou(termos: list[str], molde: str) -> str:
    return " OR ".join(molde.format(t) for t in termos)


def pubmed() -> str:
    """Sintaxe PubMed/MEDLINE: [tiab] para termo livre, [Mesh] para descritor."""
    pop = _ou(POPULACAO_LIVRE, '"{}"[tiab]')
    mesh = _ou(CONCEITO_MESH, '"{}"[Mesh]')
    livre = _ou(CONCEITO_LIVRE, '"{}"[tiab]')
    ctx_mesh = _ou(CONTEXTO_MESH, '"{}"[Mesh]')
    ctx_livre = _ou(CONTEXTO_LIVRE, '"{}"[tiab]')
    return (f"({pop}) AND (({mesh}) OR ({livre})) "
            f"AND (({ctx_mesh}) OR ({ctx_livre}))")


def scopus() -> str:
    """Sintaxe Scopus: TITLE-ABS-KEY para termo livre, KEY para termo de índice."""
    pop = _ou(POPULACAO_LIVRE, 'TITLE-ABS-KEY("{}")')
    chave = _ou(CONCEITO_ASSUNTO, 'KEY("{}")')
    livre = _ou(CONCEITO_LIVRE, 'TITLE-ABS-KEY("{}")')
    ctx = _ou(CONTEXTO_LIVRE, 'TITLE-ABS-KEY("{}")')
    return (f"({pop}) AND (({chave}) OR ({livre})) AND ({ctx}) "
            f"AND PUBYEAR > {JANELA[0] - 1} AND PUBYEAR < {JANELA[1] + 1}")


def wos() -> str:
    """Sintaxe Web of Science: TS=() sobre título, resumo, autor-keywords e KeyWords Plus."""
    aspas = lambda t: f'"{t}"' if " " in t or "-" in t else t
    pop = " OR ".join(aspas(t) for t in POPULACAO_LIVRE)
    conc = " OR ".join(aspas(t) for t in CONCEITO_LIVRE)
    ctx = " OR ".join(aspas(t) for t in CONTEXTO_LIVRE)
    return f"TS=(({pop}) AND ({conc}) AND ({ctx}))"


def lilacs() -> str:
    """Sintaxe LILACS/BVS: tw: para palavra do texto, mh: para descritor DeCS."""
    aspas = lambda t: f'"{t}"' if " " in t else t
    pop = " OR ".join(aspas(t) for t in POPULACAO_LIVRE)
    decs = " OR ".join(f'mh:("{t}")' for t in CONCEITO_DECS)
    livre = " OR ".join(aspas(t) for t in CONCEITO_LIVRE)
    ctx = " OR ".join(aspas(t) for t in CONTEXTO_LIVRE)
    return f"tw:(({pop}) AND (({decs}) OR ({livre})) AND ({ctx}))"


CONSULTAS = {
    "pubmed": pubmed,
    "scopus": scopus,
    "wos": wos,
    "lilacs": lilacs,
}


def resumo() -> dict[str, int]:
    """Contagem de termos por bloco, para a nota de método e a Tabela 8."""
    return {
        "populacao_livre": len(POPULACAO_LIVRE),
        "conceito_mesh": len(CONCEITO_MESH),
        "conceito_decs": len(CONCEITO_DECS),
        "conceito_assunto": len(CONCEITO_ASSUNTO),
        "conceito_livre": len(CONCEITO_LIVRE),
        "contexto_mesh": len(CONTEXTO_MESH),
        "contexto_livre": len(CONTEXTO_LIVRE),
    }


if __name__ == "__main__":
    for nome, fn in CONSULTAS.items():
        q = fn()
        print(f"=== {nome.upper()} ({len(q)} caracteres) ===")
        print(q)
        print()
    print("termos por bloco:", resumo())
