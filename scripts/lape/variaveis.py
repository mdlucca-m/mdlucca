"""As variaveis que o LAPE estuda, e como elas se cruzam.

A producao de um laboratorio nao e uma lista de artigos: e um punhado de
variaveis estudadas ao longo do tempo, que se encontram. O artigo que
mediu ansiedade E dor E treinamento resistido e justamente o que liga as
tres -- e e dele que sai a historia da linha de pesquisa.

Por isso a ligacao e muitos-para-muitos, e nao uma coluna "tema" no
artigo. Uma coluna obrigaria a escolher uma variavel, e a escolha
apagaria a relacao, que e o que se quer ver.

O modulo faz tres coisas:

  1. guarda o vocabulario do laboratorio, com sinonimos em portugues e
     ingles e os instrumentos que medem cada coisa (POMS, FIQ, PSQI...),
     porque e pelo instrumento que metade dos titulos menciona a variavel;
  2. marca cada artigo com as variaveis que aparecem nele, guardando o
     TRECHO em que apareceu -- achado sem evidencia nao se confere;
  3. descobre o pais do estudo pela afiliacao, que e o que permite o mapa.

Nada aqui decide sozinho. A marcacao automatica nasce como `auto` e
existe para poupar leitura, nao para substitui-la.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from .db import Database
from .util import clean_text

ORIGENS = ("auto", "confirmada", "manual")

# ----------------------------------------------------------------------
# O vocabulario
# ----------------------------------------------------------------------
# (codigo, rotulo, grupo, icone, sinonimos)
#
# Os sinonimos incluem os INSTRUMENTOS de propósito. Metade dos resumos de
# psicologia do esporte nunca escreve "mood": escreve "POMS". Procurar so
# pelo nome da variavel perde esses -- e sao justamente os artigos mais
# metodologicos.
VOCABULARIO: tuple[tuple[str, str, str, str, tuple[str, ...]], ...] = (
    # --- condicao clinica: o que o laboratorio investiga ---
    ("fibromialgia", "Fibromialgia", "Condição clínica", "experimento", (
        "fibromialgia", "fibromyalgia", "fm", "fiq", "fiqr",
        "sindrome fibromialgica", "acr 1990", "acr 2016")),
    ("dor", "Dor crônica", "Condição clínica", "raio", (
        "dor", "dor cronica", "pain", "chronic pain", "algia", "limiar de dor",
        "pain threshold", "hiperalgesia", "eva", "escala visual analogica",
        "vas", "dor musculoesqueletica", "musculoskeletal pain", "lombalgia")),
    ("reumatica", "Doenças reumáticas", "Condição clínica", "experimento", (
        "reumatica", "reumaticas", "rheumatic", "artrite", "arthritis",
        "artrose", "osteoarthritis", "lupus", "espondilite")),
    ("assoalho_pelvico", "Assoalho pélvico", "Condição clínica", "experimento", (
        "assoalho pelvico", "pelvic floor", "incontinencia urinaria",
        "urinary incontinence", "disfuncao pelvica")),
    # --- intervencao: o que o laboratorio testa ---
    ("treinamento_resistido", "Treinamento resistido", "Intervenção", "subida", (
        "treinamento resistido", "resistance training", "treinamento de forca",
        "strength training", "musculacao", "exercicio resistido",
        "resistance exercise", "tr", "1rm", "carga de treino")),
    ("exercicio", "Exercício e atividade física", "Intervenção", "foguete", (
        "exercicio", "exercise", "atividade fisica", "physical activity",
        "treinamento", "training", "exercicio aerobio", "aerobic",
        "caminhada", "walking", "corrida", "running", "hidroterapia",
        "exercicio fisico", "physical exercise", "ipaq")),
    ("aventura", "Atividades de aventura", "Intervenção", "espaco", (
        "aventura", "adventure", "esportes de aventura", "adventure sports",
        "natureza", "outdoor", "surf", "escalada", "trilha")),
    ("exergames", "Exergames e tecnologia", "Intervenção", "automacao", (
        "exergame", "exergames", "exergaming", "realidade virtual",
        "virtual reality", "jogos digitais", "serious games", "gamificacao",
        "tecnologia educacional", "aplicativo", "mhealth")),
    ("reabilitacao", "Reabilitação", "Intervenção", "processo", (
        "reabilitacao", "rehabilitation", "fisioterapia", "physiotherapy",
        "physical therapy", "modalidades fisioterapeuticas", "eletroterapia",
        "cinesioterapia")),
    # --- desfecho psicologico ---
    ("ansiedade", "Ansiedade", "Desfecho psicológico", "raio", (
        "ansiedade", "anxiety", "ansiedade traco", "ansiedade estado",
        "state anxiety", "trait anxiety", "stai", "idate", "hads", "gad-7",
        "ansiedade competitiva", "competitive anxiety", "csai")),
    ("depressao", "Depressão", "Desfecho psicológico", "pausa", (
        "depressao", "depression", "depressive", "sintomas depressivos",
        "depressive symptoms", "bdi", "beck depression", "ces-d", "phq-9")),
    ("humor", "Estados de humor", "Desfecho psicológico", "apresentacao", (
        "humor", "estados de humor", "perfil de humor", "perfis de humor",
        "mood", "mood states", "profile of mood states", "poms", "brums",
        "vigor", "tensao", "fadiga", "confusao", "iceberg")),
    ("estresse", "Estresse", "Desfecho psicológico", "fogo", (
        "estresse", "stress", "estresse percebido", "perceived stress",
        "pss", "restq", "distress", "cortisol salivar")),
    ("saude_mental", "Saúde mental", "Desfecho psicológico", "pessoa", (
        "saude mental", "mental health", "sofrimento psiquico",
        "psychological distress", "transtorno mental", "srq-20", "ghq")),
    ("qualidade_vida", "Qualidade de vida", "Desfecho psicológico", "trofeu", (
        "qualidade de vida", "quality of life", "sf-36", "sf-12", "whoqol",
        "eq-5d", "bem-estar", "bem estar", "well-being", "wellbeing")),
    ("sono", "Sono", "Desfecho psicológico", "relogio", (
        "sono", "sleep", "qualidade do sono", "sleep quality", "insonia",
        "insomnia", "psqi", "sonolencia", "actigrafia")),
    ("autoeficacia", "Autoeficácia", "Desfecho psicológico", "subida", (
        "autoeficacia", "auto-eficacia", "self-efficacy", "self efficacy",
        "percepcao de competencia", "locus de controle")),
    ("catastrofizacao", "Catastrofização e medo", "Desfecho psicológico", "aviso", (
        "catastrofizacao", "catastrophizing", "pcs", "cinesiofobia",
        "kinesiophobia", "tampa", "medo do movimento", "fear avoidance")),
    # --- comportamento diante do tratamento ---
    ("aderencia", "Aderência e dropout", "Comportamento", "prazo", (
        "aderencia", "adesao", "adherence", "compliance", "dropout",
        "drop-out", "abandono", "desistencia", "attrition", "evasao",
        "permanencia", "retencao", "retention", "assiduidade")),
    ("motivacao", "Motivação", "Comportamento", "foguete", (
        "motivacao", "motivation", "motivational", "autodeterminacao",
        "self-determination", "motivacao intrinseca", "barreiras",
        "facilitadores", "expectativa")),
    ("percepcao_esforco", "Percepção de esforço", "Carga", "barras", (
        "percepcao de esforco", "percepcao subjetiva de esforco",
        "perceived exertion", "rpe", "srpe", "borg", "carga interna")),
    ("recuperacao", "Recuperação e fadiga", "Carga", "atualizar", (
        "recuperacao", "recovery", "fadiga", "fatigue", "overtraining",
        "tqr", "percepcao de recuperacao", "recovery-stress")),
    # --- ensino e formacao ---
    ("educacao_fisica", "Educação física escolar", "Ensino", "instituicao", (
        "educacao fisica", "physical education", "escolar", "school",
        "professores", "teachers", "curriculo", "aula")),
)

GRUPOS = ("Condição clínica", "Intervenção", "Desfecho psicológico",
          "Comportamento", "Carga", "Ensino")


def instalar(db: Database, review_id: int | None = None) -> int:
    """Poe o vocabulario no banco. Rodar de novo nao apaga o que foi mexido."""
    for seq, (codigo, rotulo, grupo, icone, _) in enumerate(VOCABULARIO, start=1):
        db.upsert("variables", {
            "review_id": review_id, "code": codigo, "label": rotulo,
            "grupo": grupo, "icone": icone, "seq": seq,
        }, conflict=("review_id", "code"), preserve=("label", "grupo", "icone", "cor"))
    db.conn.commit()
    return len(VOCABULARIO)


def lista(db: Database, review_id: int | None = None) -> list[dict[str, Any]]:
    if review_id is None:
        return db.dicts("SELECT * FROM variables WHERE review_id IS NULL ORDER BY seq")
    return db.dicts("SELECT * FROM variables WHERE review_id IS NULL OR review_id = ?"
                    " ORDER BY seq", (review_id,))


# ----------------------------------------------------------------------
# Reconhecer a variavel no texto
# ----------------------------------------------------------------------
def _dobra(texto: Any) -> str:
    """Sem acento e em minuscula: 'Ansiedade Pré-Competitiva' vira comparavel."""
    limpo = str(texto or "")
    sem = "".join(c for c in unicodedata.normalize("NFKD", limpo)
                  if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sem.lower()).strip()


# Cada sinonimo vira um padrao com fronteira de palavra. Sem a fronteira,
# "rpe" casaria dentro de "properties" e "act" dentro de "activity" -- e a
# marcacao automatica encheria a revisao de falso positivo silencioso.
PADROES: dict[str, tuple[tuple[str, Any], ...]] = {
    codigo: tuple((sin, re.compile(r"(?<![a-z0-9])" + re.escape(_dobra(sin)) + r"(?![a-z0-9])"))
                  for sin in sinonimos)
    for codigo, _, _, _, sinonimos in VOCABULARIO
}


def reconhecer(titulo: Any = None, resumo: Any = None,
               palavras: Any = None) -> list[dict[str, Any]]:
    """As variaveis que aparecem neste texto, com o trecho que as denunciou.

    O trecho e a evidencia. Uma marcacao sem ele obriga a reler o artigo
    inteiro para conferir, e o que obriga a reler nao e conferido.
    """
    campos = (("título", titulo), ("resumo", resumo), ("palavras-chave", palavras))
    achados: dict[str, dict[str, Any]] = {}
    for onde, bruto in campos:
        alvo = _dobra(bruto)
        if not alvo:
            continue
        for codigo, padroes in PADROES.items():
            if codigo in achados and achados[codigo]["onde"] == "título":
                continue          # achado no titulo manda: e o mais forte
            for sinonimo, padrao in padroes:
                casa = padrao.search(alvo)
                if casa:
                    achados[codigo] = {
                        "code": codigo, "termo": sinonimo, "onde": onde,
                        "trecho": _janela(alvo, casa.start(), casa.end()),
                    }
                    break
    return sorted(achados.values(), key=lambda x: x["code"])


def _janela(texto: str, inicio: int, fim: int, folga: int = 44) -> str:
    esquerda = max(0, inicio - folga)
    direita = min(len(texto), fim + folga)
    trecho = texto[esquerda:direita].strip()
    return ("…" if esquerda else "") + trecho + ("…" if direita < len(texto) else "")


def marcar(db: Database, review_id: int, apenas_novas: bool = True) -> dict[str, Any]:
    """Passa o vocabulario sobre as referencias e marca o que reconhecer.

    Nao mexe no que uma pessoa ja confirmou ou marcou a mao: a leitura
    humana vale mais do que a busca por palavra, e refazer a busca nao
    pode apagar o trabalho de quem leu.
    """
    por_codigo = {v["code"]: v["id"] for v in lista(db, review_id)}
    if not por_codigo:
        instalar(db)
        por_codigo = {v["code"]: v["id"] for v in lista(db, review_id)}

    ja_humano = {(linha["ref_id"], linha["variable_id"]) for linha in db.dicts(
        "SELECT ref_id, variable_id FROM ref_variables WHERE origem <> 'auto'")}

    filtro = ""
    if apenas_novas:
        filtro = (" AND NOT EXISTS (SELECT 1 FROM ref_variables rv"
                  " WHERE rv.ref_id = r.id)")
    referencias = db.dicts(
        "SELECT id, title, abstract, keywords FROM refs r"
        f" WHERE review_id = ? AND duplicate_of IS NULL{filtro}", (review_id,))

    marcadas, ligacoes = 0, 0
    for ref in referencias:
        achados = reconhecer(ref["title"], ref["abstract"], ref["keywords"])
        if not achados:
            continue
        marcadas += 1
        for achado in achados:
            variable_id = por_codigo.get(achado["code"])
            if variable_id is None or (ref["id"], variable_id) in ja_humano:
                continue
            db.execute(
                "INSERT INTO ref_variables (ref_id, variable_id, origem, trecho)"
                " VALUES (?, ?, 'auto', ?)"
                " ON CONFLICT (ref_id, variable_id) DO UPDATE SET trecho = excluded.trecho"
                " WHERE ref_variables.origem = 'auto'",
                (ref["id"], variable_id, f"{achado['onde']}: {achado['trecho']}"))
            ligacoes += 1
    db.conn.commit()
    return {"referencias_lidas": len(referencias), "com_variavel": marcadas,
            "ligacoes": ligacoes}


def marcar_artigos(db: Database, apenas_novos: bool = True) -> dict[str, Any]:
    """Passa o vocabulario sobre a producao do proprio laboratorio.

    O artigo do LAPE nao tem resumo no banco -- o titulo e o que ha, e
    titulo de artigo cientifico e descritivo o bastante. Onde houver
    observacoes, elas entram tambem.
    """
    por_codigo = {v["code"]: v["id"] for v in lista(db)}
    if not por_codigo:
        instalar(db)
        por_codigo = {v["code"]: v["id"] for v in lista(db)}

    ja_humano = {(l["article_id"], l["variable_id"]) for l in db.dicts(
        "SELECT article_id, variable_id FROM article_variables WHERE origem <> 'auto'")}
    filtro = (" AND NOT EXISTS (SELECT 1 FROM article_variables av"
              " WHERE av.article_id = a.id)") if apenas_novos else ""
    artigos = db.dicts(f"SELECT id, title, notes FROM articles a WHERE 1 = 1{filtro}")

    marcados, ligacoes = 0, 0
    for artigo in artigos:
        achados = reconhecer(artigo["title"], artigo["notes"])
        if not achados:
            continue
        marcados += 1
        for achado in achados:
            variable_id = por_codigo.get(achado["code"])
            if variable_id is None or (artigo["id"], variable_id) in ja_humano:
                continue
            db.execute(
                "INSERT INTO article_variables (article_id, variable_id, origem, trecho)"
                " VALUES (?, ?, 'auto', ?)"
                " ON CONFLICT (article_id, variable_id) DO UPDATE SET trecho = excluded.trecho"
                " WHERE article_variables.origem = 'auto'",
                (artigo["id"], variable_id, f"{achado['onde']}: {achado['trecho']}"))
            ligacoes += 1
    db.conn.commit()
    return {"artigos_lidos": len(artigos), "com_variavel": marcados, "ligacoes": ligacoes}


def do_artigo(db: Database, article_id: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT v.id, v.code, v.label, v.grupo, v.icone, av.origem, av.trecho"
        "  FROM article_variables av JOIN variables v ON v.id = av.variable_id"
        " WHERE av.article_id = ? ORDER BY v.seq", (article_id,))


def marcar_artigo_a_mao(db: Database, article_id: int,
                        codigos: Iterable[str]) -> dict[str, int]:
    """A palavra de quem escreveu o artigo, por cima da busca automatica."""
    por_codigo = {v["code"]: v["id"] for v in lista(db)}
    escolhidos = {por_codigo[c] for c in codigos if c in por_codigo}
    atuais = {l["variable_id"] for l in db.dicts(
        "SELECT variable_id FROM article_variables WHERE article_id = ?", (article_id,))}
    for variable_id in escolhidos - atuais:
        db.execute("INSERT INTO article_variables (article_id, variable_id, origem, trecho)"
                   " VALUES (?, ?, 'manual', 'marcada por quem leu')",
                   (article_id, variable_id))
    for variable_id in escolhidos & atuais:
        db.execute("UPDATE article_variables SET origem = 'confirmada'"
                   " WHERE article_id = ? AND variable_id = ? AND origem = 'auto'",
                   (article_id, variable_id))
    for variable_id in atuais - escolhidos:
        db.execute("DELETE FROM article_variables WHERE article_id = ? AND variable_id = ?",
                   (article_id, variable_id))
    db.conn.commit()
    return {"marcadas": len(escolhidos), "removidas": len(atuais - escolhidos)}


def marcar_a_mao(db: Database, ref_id: int, codigos: Iterable[str],
                 review_id: int | None = None) -> dict[str, int]:
    """A palavra de quem leu, por cima da busca automatica."""
    por_codigo = {v["code"]: v["id"] for v in lista(db, review_id)}
    escolhidos = {por_codigo[c] for c in codigos if c in por_codigo}
    atuais = {linha["variable_id"] for linha in db.dicts(
        "SELECT variable_id FROM ref_variables WHERE ref_id = ?", (ref_id,))}
    for variable_id in escolhidos - atuais:
        db.execute("INSERT INTO ref_variables (ref_id, variable_id, origem, trecho)"
                   " VALUES (?, ?, 'manual', 'marcada por quem leu')",
                   (ref_id, variable_id))
    for variable_id in escolhidos & atuais:
        db.execute("UPDATE ref_variables SET origem = 'confirmada'"
                   " WHERE ref_id = ? AND variable_id = ? AND origem = 'auto'",
                   (ref_id, variable_id))
    for variable_id in atuais - escolhidos:
        db.execute("DELETE FROM ref_variables WHERE ref_id = ? AND variable_id = ?",
                   (ref_id, variable_id))
    db.conn.commit()
    return {"marcadas": len(escolhidos), "removidas": len(atuais - escolhidos)}


def de(db: Database, ref_id: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT v.id, v.code, v.label, v.grupo, v.icone, rv.origem, rv.trecho"
        "  FROM ref_variables rv JOIN variables v ON v.id = rv.variable_id"
        " WHERE rv.ref_id = ? ORDER BY v.seq", (ref_id,))


# ----------------------------------------------------------------------
# De onde veio o estudo
# ----------------------------------------------------------------------
# Coordenadas aproximadas do centro de cada pais, para o mapa. So os que
# aparecem em ciencia do esporte -- uma lista com os 195 nao ajudaria e
# encheria o arquivo.
PAISES: dict[str, tuple[str, float, float]] = {
    "brazil": ("Brasil", -14.2, -51.9), "portugal": ("Portugal", 39.4, -8.2),
    "spain": ("Espanha", 40.4, -3.7), "france": ("França", 46.6, 2.4),
    "germany": ("Alemanha", 51.2, 10.5), "italy": ("Itália", 41.9, 12.6),
    "norway": ("Noruega", 60.5, 8.5), "denmark": ("Dinamarca", 56.3, 9.5),
    "sweden": ("Suécia", 60.1, 18.6), "iceland": ("Islândia", 65.0, -19.0),
    "croatia": ("Croácia", 45.1, 15.2), "serbia": ("Sérvia", 44.0, 21.0),
    "slovenia": ("Eslovênia", 46.2, 14.8), "hungary": ("Hungria", 47.2, 19.5),
    "poland": ("Polônia", 51.9, 19.1), "romania": ("Romênia", 45.9, 25.0),
    "russia": ("Rússia", 61.5, 105.3), "ukraine": ("Ucrânia", 48.4, 31.2),
    "netherlands": ("Países Baixos", 52.1, 5.3), "belgium": ("Bélgica", 50.5, 4.5),
    "switzerland": ("Suíça", 46.8, 8.2), "austria": ("Áustria", 47.5, 14.6),
    "greece": ("Grécia", 39.1, 21.8), "turkey": ("Turquia", 38.9, 35.2),
    "united kingdom": ("Reino Unido", 55.4, -3.4), "england": ("Reino Unido", 52.4, -1.5),
    "scotland": ("Reino Unido", 56.5, -4.2), "ireland": ("Irlanda", 53.1, -8.2),
    "united states": ("Estados Unidos", 39.8, -98.6), "usa": ("Estados Unidos", 39.8, -98.6),
    "canada": ("Canadá", 56.1, -106.3), "mexico": ("México", 23.6, -102.6),
    "argentina": ("Argentina", -38.4, -63.6), "chile": ("Chile", -35.7, -71.5),
    "colombia": ("Colômbia", 4.6, -74.3), "uruguay": ("Uruguai", -32.5, -55.8),
    "australia": ("Austrália", -25.3, 133.8), "new zealand": ("Nova Zelândia", -40.9, 174.9),
    "japan": ("Japão", 36.2, 138.3), "china": ("China", 35.9, 104.2),
    "south korea": ("Coreia do Sul", 35.9, 127.8), "korea": ("Coreia do Sul", 35.9, 127.8),
    "india": ("Índia", 20.6, 79.0), "iran": ("Irã", 32.4, 53.7),
    "israel": ("Israel", 31.0, 34.9), "qatar": ("Catar", 25.4, 51.2),
    "saudi arabia": ("Arábia Saudita", 23.9, 45.1), "egypt": ("Egito", 26.8, 30.8),
    "tunisia": ("Tunísia", 33.9, 9.5), "algeria": ("Argélia", 28.0, 1.7),
    "morocco": ("Marrocos", 31.8, -7.1), "south africa": ("África do Sul", -30.6, 22.9),
    "nigeria": ("Nigéria", 9.1, 8.7), "czech republic": ("Tchéquia", 49.8, 15.5),
    "czechia": ("Tchéquia", 49.8, 15.5), "slovakia": ("Eslováquia", 48.7, 19.7),
    "finland": ("Finlândia", 61.9, 25.7), "lithuania": ("Lituânia", 55.2, 23.9),
    "bosnia and herzegovina": ("Bósnia e Herzegovina", 43.9, 17.7),
    "north macedonia": ("Macedônia do Norte", 41.6, 21.7),
    "montenegro": ("Montenegro", 42.7, 19.4), "bulgaria": ("Bulgária", 42.7, 25.5),
}
# A afiliacao da Scopus termina no pais: "..., University of X, Oslo, Norway".
# Ler o ultimo pedaco e o que funciona; ler o texto inteiro traria "New York"
# como pais toda vez que alguem publicasse numa revista de Nova York.
_PAIS_POR_DOBRA = {_dobra(chave): valor for chave, valor in PAISES.items()}


def pais_da_afiliacao(afiliacao: Any) -> tuple[str, float, float] | None:
    texto = clean_text(afiliacao)
    if not texto:
        return None
    for pedaco in reversed(re.split(r"[;,]", texto)):
        achado = _PAIS_POR_DOBRA.get(_dobra(pedaco))
        if achado:
            return achado
    # a afiliacao pode vir sem virgula ("Univ Oslo Norway")
    dobrado = _dobra(texto)
    for chave, valor in _PAIS_POR_DOBRA.items():
        if re.search(r"(?<![a-z])" + re.escape(chave) + r"(?![a-z])", dobrado):
            return valor
    return None


def marcar_paises(db: Database, review_id: int) -> dict[str, int]:
    """Preenche o pais das referencias que trouxeram afiliacao."""
    achados = 0
    for ref in db.dicts(
            "SELECT id, affiliation FROM refs WHERE review_id = ?"
            "   AND country IS NULL AND affiliation IS NOT NULL", (review_id,)):
        achado = pais_da_afiliacao(ref["affiliation"])
        if achado:
            db.execute("UPDATE refs SET country = ? WHERE id = ?", (achado[0], ref["id"]))
            achados += 1
    db.conn.commit()
    return {"com_pais": achados}


def coordenadas(nome: Any) -> tuple[float, float] | None:
    alvo = _dobra(nome)
    for chave, (rotulo, lat, lon) in _PAIS_POR_DOBRA.items():
        if alvo in (chave, _dobra(rotulo)):
            return (lat, lon)
    return None
