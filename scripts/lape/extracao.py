"""Extracao de dados e risco de vies dos estudos incluidos.

Depois da triagem vem a parte que ninguem gosta: ler cada estudo e tirar
dele, campo a campo, o que a revisao precisa. Hoje isso e feito em
planilha compartilhada -- e a planilha nao sabe que duas pessoas deviam
extrair em separado, nem onde as duas discordaram. O Rayyan nao faz nem
isso: a triagem acaba e a ferramenta acaba junto.

O desenho e o mesmo da triagem, e pela mesma razao: cada pessoa preenche
a sua, e a versao final e uma terceira coisa, construida a partir das
duas. Sem isso, "extracao em duplicata" vira uma pessoa conferindo o que
a outra digitou -- que nao e a mesma coisa e nao vale como duplicata.

Duas saidas, que sao o que a revista pede:

  a tabela de caracteristicas dos estudos incluidos
  o semaforo de risco de vies, com o julgamento de cada dominio
"""
from __future__ import annotations

import json
from typing import Any

from .db import Database
from .util import clean_text

TIPOS = ("texto", "texto_longo", "numero", "data", "escolha", "multipla", "sim_nao")

# ----------------------------------------------------------------------
# O formulario de extracao
# ----------------------------------------------------------------------
# Ponto de partida, nao camisa de forca: cobre o que quase toda revisao de
# intervencao precisa, e cada revisao acrescenta ou tira o que quiser. Uma
# revisao que comeca com a folha em branco costuma terminar com campos
# inventados no meio do caminho, e ai metade dos estudos ja foi extraida
# sem eles.
FORMULARIO_PADRAO: tuple[dict[str, Any], ...] = (
    {"code": "pais", "label": "País", "kind": "texto", "grupo": "Identificação"},
    {"code": "delineamento", "label": "Delineamento", "kind": "escolha",
     "grupo": "Identificação",
     "options": "Ensaio randomizado;Ensaio não randomizado;Coorte;Caso-controle;"
                "Transversal;Série de casos;Qualitativo;Revisão"},
    {"code": "financiamento", "label": "Financiamento", "kind": "texto",
     "grupo": "Identificação", "help": "Agência, ou 'não declarado'"},
    {"code": "n_total", "label": "N total", "kind": "numero", "grupo": "Participantes",
     "required": 1},
    {"code": "n_intervencao", "label": "N no grupo intervenção", "kind": "numero",
     "grupo": "Participantes"},
    {"code": "n_controle", "label": "N no grupo controle", "kind": "numero",
     "grupo": "Participantes"},
    {"code": "idade", "label": "Idade (média ± DP)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "sexo", "label": "Sexo (% mulheres)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "populacao", "label": "População", "kind": "texto_longo",
     "grupo": "Participantes", "help": "Quem eram, e como foram recrutados"},
    {"code": "intervencao", "label": "Intervenção", "kind": "texto_longo",
     "grupo": "Intervenção", "required": 1},
    {"code": "duracao", "label": "Duração", "kind": "texto", "grupo": "Intervenção"},
    {"code": "frequencia", "label": "Frequência", "kind": "texto", "grupo": "Intervenção"},
    {"code": "comparador", "label": "Comparador", "kind": "texto_longo",
     "grupo": "Intervenção"},
    {"code": "desfecho_primario", "label": "Desfecho primário", "kind": "texto_longo",
     "grupo": "Desfechos", "required": 1},
    {"code": "instrumentos", "label": "Instrumentos", "kind": "texto_longo",
     "grupo": "Desfechos", "help": "Escalas e questionários usados"},
    {"code": "momentos", "label": "Momentos de avaliação", "kind": "texto",
     "grupo": "Desfechos"},
    {"code": "resultado", "label": "Resultado principal", "kind": "texto_longo",
     "grupo": "Resultados", "required": 1},
    {"code": "tamanho_efeito", "label": "Tamanho de efeito", "kind": "texto",
     "grupo": "Resultados", "help": "d de Cohen, diferença média, RR — com IC quando houver"},
    {"code": "perdas", "label": "Perdas de seguimento", "kind": "texto",
     "grupo": "Resultados"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Resultados"},
)


# Os MODELOS de formulario. O de intervencao acima e o padrao porque e o
# que este laboratorio mais usa; os outros existem porque extrair um
# estudo transversal com campos de ensaio clinico produz tres quartos de
# campo vazio e nenhum dos campos que importam -- e a tabela de
# caracteristicas sai com "não se aplica" em coluna atras de coluna.
#
# Cada um segue o que a literatura de metodo cobra para aquele desenho: o
# formulario de coleta da Cochrane para intervencao, o STROBE para
# observacional, o JBI-QARI para qualitativo, o COSMIN para psicometria e
# o "charting" do JBI para revisao de escopo. Sao ponto de partida, e nao
# camisa de forca: cada revisao acrescenta e tira o que quiser -- mas
# comecar da folha em branco e como metade dos estudos ja extraida quando
# alguem descobre que faltava um campo.
MODELO_OBSERVACIONAL: tuple[dict[str, Any], ...] = (
    {"code": "pais", "label": "País", "kind": "texto", "grupo": "Identificação"},
    {"code": "delineamento", "label": "Delineamento", "kind": "escolha",
     "grupo": "Identificação",
     "options": "Coorte prospectiva;Coorte retrospectiva;Caso-controle;"
                "Transversal;Ecológico"},
    {"code": "fonte", "label": "Fonte dos participantes", "kind": "texto_longo",
     "grupo": "Identificação", "help": "De onde saiu a amostra, e como foi recrutada"},
    {"code": "financiamento", "label": "Financiamento", "kind": "texto",
     "grupo": "Identificação"},
    {"code": "n_total", "label": "N analisado", "kind": "numero",
     "grupo": "Participantes", "required": 1},
    {"code": "idade", "label": "Idade (média ± DP)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "sexo", "label": "Sexo (% mulheres)", "kind": "texto",
     "grupo": "Participantes"},
    {"code": "elegibilidade", "label": "Critérios de elegibilidade",
     "kind": "texto_longo", "grupo": "Participantes"},
    {"code": "exposicao", "label": "Exposição / variável independente",
     "kind": "texto_longo", "grupo": "Medidas", "required": 1},
    {"code": "desfecho", "label": "Desfecho / variável dependente",
     "kind": "texto_longo", "grupo": "Medidas", "required": 1},
    {"code": "instrumentos", "label": "Instrumentos", "kind": "texto_longo",
     "grupo": "Medidas"},
    {"code": "seguimento", "label": "Tempo de seguimento", "kind": "texto",
     "grupo": "Medidas", "help": "só para coorte"},
    {"code": "confundidores", "label": "Confundidores considerados",
     "kind": "texto_longo", "grupo": "Análise",
     "help": "O STROBE cobra quais foram, e não só que houve ajuste"},
    {"code": "ajuste", "label": "Modelo e ajuste", "kind": "texto_longo",
     "grupo": "Análise"},
    {"code": "medida", "label": "Medida de associação", "kind": "texto",
     "grupo": "Resultados", "required": 1,
     "help": "OR, RR, HR, beta ou r — com intervalo de confiança"},
    {"code": "perdas", "label": "Perdas e dados faltantes", "kind": "texto",
     "grupo": "Resultados"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Resultados"},
)

MODELO_QUALITATIVO: tuple[dict[str, Any], ...] = (
    {"code": "pais", "label": "País", "kind": "texto", "grupo": "Identificação"},
    {"code": "metodologia", "label": "Metodologia", "kind": "escolha",
     "grupo": "Identificação",
     "options": "Fenomenologia;Teoria fundamentada;Etnografia;Estudo de caso;"
                "Análise de conteúdo;Análise temática;Pesquisa-ação;Outra"},
    {"code": "posicionamento", "label": "Posicionamento do pesquisador",
     "kind": "texto_longo", "grupo": "Identificação",
     "help": "O JBI cobra: quem pesquisou, e de que lugar"},
    {"code": "participantes", "label": "Participantes e contexto",
     "kind": "texto_longo", "grupo": "Participantes", "required": 1},
    {"code": "amostragem", "label": "Amostragem", "kind": "texto",
     "grupo": "Participantes", "help": "Intencional, bola de neve, por conveniência…"},
    {"code": "coleta", "label": "Coleta de dados", "kind": "texto_longo",
     "grupo": "Método", "required": 1,
     "help": "Entrevista, grupo focal, observação — e por quanto tempo"},
    {"code": "analise", "label": "Análise dos dados", "kind": "texto_longo",
     "grupo": "Método", "required": 1},
    {"code": "rigor", "label": "Critérios de rigor", "kind": "texto_longo",
     "grupo": "Método", "help": "Triangulação, validação pelos participantes, saturação"},
    {"code": "temas", "label": "Temas e categorias", "kind": "texto_longo",
     "grupo": "Achados", "required": 1},
    {"code": "citacoes", "label": "Falas ilustrativas", "kind": "texto_longo",
     "grupo": "Achados", "help": "As citações que sustentam cada tema"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Achados"},
)

MODELO_PSICOMETRIA: tuple[dict[str, Any], ...] = (
    {"code": "instrumento", "label": "Instrumento", "kind": "texto",
     "grupo": "Identificação", "required": 1},
    {"code": "versao", "label": "Versão / idioma", "kind": "texto",
     "grupo": "Identificação"},
    {"code": "construto", "label": "Construto medido", "kind": "texto_longo",
     "grupo": "Identificação", "required": 1},
    {"code": "itens", "label": "Itens e fatores", "kind": "texto",
     "grupo": "Estrutura", "help": "Quantos itens, em quantos fatores"},
    {"code": "n_total", "label": "N da amostra", "kind": "numero",
     "grupo": "Estrutura", "required": 1},
    {"code": "estrutura", "label": "Estrutura fatorial", "kind": "texto_longo",
     "grupo": "Estrutura", "help": "AFE/AFC, e os índices de ajuste"},
    {"code": "consistencia", "label": "Consistência interna", "kind": "texto",
     "grupo": "Confiabilidade", "help": "Alfa, ômega — por fator"},
    {"code": "teste_reteste", "label": "Teste-reteste", "kind": "texto",
     "grupo": "Confiabilidade", "help": "CCI, e o intervalo entre as medidas"},
    {"code": "validade", "label": "Validade de construto", "kind": "texto_longo",
     "grupo": "Validade", "help": "Convergente, discriminante, de critério"},
    {"code": "invariancia", "label": "Invariância de medida", "kind": "texto",
     "grupo": "Validade",
     "help": "Entre sexos, idades ou modalidades — é o que permite comparar grupos"},
    {"code": "erro", "label": "Erro de medida", "kind": "texto",
     "grupo": "Validade", "help": "EPM, mínima mudança detectável"},
    {"code": "conclusao", "label": "Conclusão dos autores", "kind": "texto_longo",
     "grupo": "Validade"},
)

MODELO_ESCOPO: tuple[dict[str, Any], ...] = (
    {"code": "pais", "label": "País", "kind": "texto", "grupo": "Identificação"},
    {"code": "delineamento", "label": "Delineamento", "kind": "escolha",
     "grupo": "Identificação",
     "options": "Ensaio randomizado;Ensaio não randomizado;Coorte;Caso-controle;"
                "Transversal;Qualitativo;Métodos mistos;Revisão;Ensaio teórico"},
    {"code": "objetivo", "label": "Objetivo do estudo", "kind": "texto_longo",
     "grupo": "Identificação", "required": 1},
    {"code": "populacao", "label": "População", "kind": "texto_longo",
     "grupo": "PCC", "required": 1},
    {"code": "conceito", "label": "Conceito", "kind": "texto_longo",
     "grupo": "PCC", "required": 1,
     "help": "O que se estuda — na revisão de escopo é o C do PCC"},
    {"code": "contexto", "label": "Contexto", "kind": "texto_longo",
     "grupo": "PCC", "required": 1,
     "help": "Onde: país, nível competitivo, ambiente"},
    {"code": "n_total", "label": "N", "kind": "numero", "grupo": "Achados"},
    {"code": "instrumentos", "label": "Instrumentos e medidas", "kind": "texto_longo",
     "grupo": "Achados"},
    {"code": "principais", "label": "Principais achados", "kind": "texto_longo",
     "grupo": "Achados", "required": 1},
    {"code": "lacuna", "label": "Lacuna apontada pelos autores",
     "kind": "texto_longo", "grupo": "Achados",
     "help": "Numa revisão de escopo, a lacuna é o produto"},
)

MODELOS: dict[str, dict[str, Any]] = {
    "intervencao": {
        "nome": "Intervenção (ensaios) — formulário de coleta da Cochrane",
        "campos": FORMULARIO_PADRAO,
        "para": "Ensaios randomizados e não randomizados.",
    },
    "observacional": {
        "nome": "Observacional (STROBE) — coorte, caso-controle, transversal",
        "campos": MODELO_OBSERVACIONAL,
        "para": "Estudos sem intervenção, em que o que importa é a exposição, "
                "os confundidores e a medida de associação.",
    },
    "qualitativo": {
        "nome": "Qualitativo (JBI-QARI)",
        "campos": MODELO_QUALITATIVO,
        "para": "Entrevista, grupo focal, etnografia — método, rigor e temas.",
    },
    "psicometria": {
        "nome": "Psicometria (COSMIN)",
        "campos": MODELO_PSICOMETRIA,
        "para": "Validação de instrumento: estrutura, confiabilidade, validade "
                "e invariância.",
    },
    "escopo": {
        "nome": "Revisão de escopo (charting JBI, população–conceito–contexto)",
        "campos": MODELO_ESCOPO,
        "para": "Charting de revisão de escopo e mapping review: descreve o "
                "campo, e não o efeito.",
    },
}


# ----------------------------------------------------------------------
# Risco de vies
# ----------------------------------------------------------------------
# Os instrumentos vivem aqui, e nao no banco, porque sao padrao publicado:
# a RoB 2 tem os dominios que tem, e nao cabe a cada revisao inventar os
# seus. O que vai para o banco e a copia que a revisao usa -- assim uma
# revisao antiga nao muda de instrumento quando o codigo e atualizado.
FERRAMENTAS_ROB: dict[str, dict[str, Any]] = {
    "rob2": {
        "nome": "RoB 2 (Cochrane, ensaios randomizados)",
        "julgamentos": (
            ("baixo", "Baixo risco", "good"),
            ("duvidas", "Algumas dúvidas", "warning"),
            ("alto", "Alto risco", "critical"),
        ),
        "dominios": (
            ("d1", "Processo de randomização"),
            ("d2", "Desvios das intervenções pretendidas"),
            ("d3", "Dados de desfecho faltantes"),
            ("d4", "Mensuração do desfecho"),
            ("d5", "Seleção do resultado relatado"),
        ),
    },
    "robins": {
        "nome": "ROBINS-I (estudos não randomizados de intervenção)",
        "julgamentos": (
            ("baixo", "Baixo risco", "good"),
            ("moderado", "Risco moderado", "warning"),
            ("serio", "Risco sério", "serious"),
            ("critico", "Risco crítico", "critical"),
            ("sem_info", "Sem informação", "neutro"),
        ),
        "dominios": (
            ("d1", "Confundimento"),
            ("d2", "Seleção dos participantes"),
            ("d3", "Classificação das intervenções"),
            ("d4", "Desvios das intervenções pretendidas"),
            ("d5", "Dados faltantes"),
            ("d6", "Mensuração dos desfechos"),
            ("d7", "Seleção do resultado relatado"),
        ),
    },
    "jbi_transversal": {
        "nome": "JBI — estudos transversais analíticos",
        "julgamentos": (
            ("sim", "Sim", "good"),
            ("nao", "Não", "critical"),
            ("incerto", "Incerto", "warning"),
            ("na", "Não se aplica", "neutro"),
        ),
        "dominios": (
            ("d1", "Critérios de inclusão definidos"),
            ("d2", "Participantes e contexto descritos"),
            ("d3", "Exposição medida de forma válida"),
            ("d4", "Critérios objetivos de medida"),
            ("d5", "Confundidores identificados"),
            ("d6", "Estratégias para lidar com confundidores"),
            ("d7", "Desfechos medidos de forma válida"),
            ("d8", "Análise estatística apropriada"),
        ),
    },
}
GERAL = ("geral", "Risco de viés geral")


def preparar(db: Database, review_id: int, ferramenta: str = "rob2",
             campos: tuple[dict[str, Any], ...] | None = None,
             modelo: str | None = None) -> dict[str, int]:
    """Instala o formulario e os dominios da ferramenta escolhida.

    Nao apaga o que ja existe: rodar de novo acrescenta o que faltava e
    deixa em paz o que a revisao ja mexeu. Trocar de instrumento no meio
    de uma revisao e decisao seria, e nao pode acontecer por engano.
    """
    if ferramenta not in FERRAMENTAS_ROB:
        raise ValueError(f"instrumento desconhecido: {ferramenta}. "
                         f"Use {', '.join(FERRAMENTAS_ROB)}")
    if modelo is not None and modelo not in MODELOS:
        raise ValueError(f"modelo de extração desconhecido: {modelo}. "
                         f"Use {', '.join(MODELOS)}")
    if campos is None and modelo:
        campos = MODELOS[modelo]["campos"]
    for seq, campo in enumerate(campos or FORMULARIO_PADRAO, start=1):
        db.upsert("extraction_fields", {
            "review_id": review_id, "code": campo["code"], "label": campo["label"],
            "kind": campo.get("kind", "texto"), "options": campo.get("options"),
            "help": campo.get("help"), "grupo": campo.get("grupo"),
            "seq": seq, "required": int(campo.get("required", 0)),
        }, conflict=("review_id", "code"), preserve=("label", "kind", "options", "help"))
    dominios = list(FERRAMENTAS_ROB[ferramenta]["dominios"]) + [GERAL]
    for seq, (code, label) in enumerate(dominios, start=1):
        db.upsert("rob_domains", {
            "review_id": review_id, "code": code, "label": label, "seq": seq,
        }, conflict=("review_id", "code"), preserve=("label",))
    db.execute("UPDATE reviews SET study_designs = COALESCE(study_designs, ?)"
               " WHERE id = ?", (ferramenta, review_id))
    db.conn.commit()
    return {"campos": len(campos or FORMULARIO_PADRAO), "dominios": len(dominios),
            "modelo": modelo}


def ferramenta_da(db: Database, review_id: int) -> dict[str, Any]:
    codigo = db.scalar("SELECT study_designs FROM reviews WHERE id = ?", (review_id,))
    escolhida = FERRAMENTAS_ROB.get(str(codigo or ""), FERRAMENTAS_ROB["rob2"])
    return {"codigo": codigo if codigo in FERRAMENTAS_ROB else "rob2", **escolhida}


# ----------------------------------------------------------------------
# Preencher
# ----------------------------------------------------------------------
def campos(db: Database, review_id: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT id, code, label, kind, options, help, grupo, seq, required"
        "  FROM extraction_fields WHERE review_id = ? ORDER BY seq", (review_id,))


def dominios(db: Database, review_id: int) -> list[dict[str, Any]]:
    return db.dicts("SELECT id, code, label, help, seq FROM rob_domains"
                    " WHERE review_id = ? ORDER BY seq", (review_id,))


def gravar(db: Database, ref_id: int, member_id: int,
           valores: dict[str, Any], risco: dict[str, Any] | None = None) -> dict[str, int]:
    """Grava a extracao de UMA pessoa sobre UM estudo.

    Chave e o codigo do campo, e nao o id: assim o formulario da revisao
    pode ganhar campo novo sem quebrar quem ja tinha a tela aberta.
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    if review_id is None:
        raise ValueError(f"referência {ref_id} não existe")
    por_codigo = {c["code"]: c for c in campos(db, review_id)}
    gravados = 0
    for codigo, valor in (valores or {}).items():
        campo = por_codigo.get(codigo)
        if campo is None:
            continue
        db.upsert("extractions", {
            "ref_id": ref_id, "member_id": member_id, "field_id": campo["id"],
            "value": _texto(valor), "updated_at": db.scalar("SELECT datetime('now')"),
        }, conflict=("ref_id", "member_id", "field_id"))
        gravados += 1

    dominios_por_codigo = {d["code"]: d for d in dominios(db, review_id)}
    julgamentos = {j[0] for j in ferramenta_da(db, review_id)["julgamentos"]}
    riscos = 0
    for codigo, resposta in (risco or {}).items():
        dominio = dominios_por_codigo.get(codigo)
        if dominio is None:
            continue
        item = resposta if isinstance(resposta, dict) else {"julgamento": resposta}
        julgamento = clean_text(item.get("julgamento"))
        if julgamento not in julgamentos:
            raise ValueError(
                f"julgamento desconhecido: {julgamento}. Use {', '.join(sorted(julgamentos))}")
        db.upsert("rob_answers", {
            "ref_id": ref_id, "member_id": member_id, "domain_id": dominio["id"],
            "judgement": julgamento, "support": clean_text(item.get("justificativa")),
            "updated_at": db.scalar("SELECT datetime('now')"),
        }, conflict=("ref_id", "member_id", "domain_id"))
        riscos += 1
    db.conn.commit()
    return {"campos": gravados, "dominios": riscos}


def minha_extracao(db: Database, ref_id: int, member_id: int) -> dict[str, Any]:
    valores = {linha["code"]: linha["value"] for linha in db.dicts(
        "SELECT f.code, e.value FROM extractions e"
        "  JOIN extraction_fields f ON f.id = e.field_id"
        " WHERE e.ref_id = ? AND e.member_id = ?", (ref_id, member_id))}
    risco = {linha["code"]: {"julgamento": linha["judgement"],
                             "justificativa": linha["support"]}
             for linha in db.dicts(
        "SELECT d.code, a.judgement, a.support FROM rob_answers a"
        "  JOIN rob_domains d ON d.id = a.domain_id"
        " WHERE a.ref_id = ? AND a.member_id = ?", (ref_id, member_id))}
    return {"valores": valores, "risco": risco}


# ----------------------------------------------------------------------
# Comparar e acordar
# ----------------------------------------------------------------------
def divergencias(db: Database, ref_id: int) -> dict[str, Any]:
    """Onde as extracoes discordam -- campo a campo, dominio a dominio.

    So faz sentido depois de duas pessoas terem preenchido. Antes disso a
    comparacao seria entre uma extracao e o vazio, e apontaria diferenca
    em tudo.
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    quem = db.dicts(
        "SELECT DISTINCT m.id, m.full_name FROM extractions e"
        "  JOIN members m ON m.id = e.member_id WHERE e.ref_id = ?"
        " UNION SELECT DISTINCT m.id, m.full_name FROM rob_answers a"
        "  JOIN members m ON m.id = a.member_id WHERE a.ref_id = ?"
        " ORDER BY 2", (ref_id, ref_id))
    por_pessoa = {p["id"]: minha_extracao(db, ref_id, p["id"]) for p in quem}
    final = versao_final(db, ref_id)

    campos_diff, iguais = [], []
    for campo in campos(db, review_id):
        respostas = {p["full_name"]: (por_pessoa[p["id"]]["valores"].get(campo["code"]) or "")
                     for p in quem}
        valores = {v.strip() for v in respostas.values()}
        acordado = final["valores"].get(campo["code"])
        item = {**campo, "respostas": respostas, "final": acordado,
                "resolvida": acordado not in (None, ""),
                "sugestao": next((v for v in respostas.values() if v.strip()), "")}
        (iguais if len(valores) <= 1 else campos_diff).append(item)

    risco_diff, risco_iguais = [], []
    for dominio in dominios(db, review_id):
        respostas = {p["full_name"]: por_pessoa[p["id"]]["risco"].get(dominio["code"])
                     for p in quem}
        julgamentos = {(r or {}).get("julgamento") for r in respostas.values()}
        acordado = final["risco"].get(dominio["code"])
        item = {**dominio, "respostas": respostas, "final": acordado,
                "resolvida": bool(acordado)}
        (risco_iguais if len(julgamentos) <= 1 else risco_diff).append(item)

    return {"pessoas": quem, "divergencias": campos_diff, "acordo": iguais,
            "risco_divergente": risco_diff, "risco_acordo": risco_iguais,
            "pronto": len(quem) >= 2}


def acordar(db: Database, ref_id: int, member_id: int,
            valores: dict[str, Any] | None = None,
            risco: dict[str, Any] | None = None) -> dict[str, int]:
    """Grava a versao final -- a que vai para a tabela do artigo."""
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    if review_id is None:
        raise ValueError(f"referência {ref_id} não existe")
    por_codigo = {c["code"]: c for c in campos(db, review_id)}
    agora = db.scalar("SELECT datetime('now')")
    n = 0
    for codigo, valor in (valores or {}).items():
        campo = por_codigo.get(codigo)
        if campo is None:
            continue
        db.execute(
            "INSERT INTO extraction_final (ref_id, field_id, value, decided_by, decided_at)"
            " VALUES (?, ?, ?, ?, ?)"
            " ON CONFLICT (ref_id, field_id) DO UPDATE SET value = excluded.value,"
            "   decided_by = excluded.decided_by, decided_at = excluded.decided_at",
            (ref_id, campo["id"], _texto(valor), member_id, agora))
        n += 1
    dominios_por_codigo = {d["code"]: d for d in dominios(db, review_id)}
    julgamentos = {j[0] for j in ferramenta_da(db, review_id)["julgamentos"]}
    r = 0
    for codigo, resposta in (risco or {}).items():
        dominio = dominios_por_codigo.get(codigo)
        if dominio is None:
            continue
        item = resposta if isinstance(resposta, dict) else {"julgamento": resposta}
        julgamento = clean_text(item.get("julgamento"))
        if julgamento not in julgamentos:
            raise ValueError(f"julgamento desconhecido: {julgamento}")
        db.execute(
            "INSERT INTO rob_final (ref_id, domain_id, judgement, support, decided_by, decided_at)"
            " VALUES (?, ?, ?, ?, ?, ?)"
            " ON CONFLICT (ref_id, domain_id) DO UPDATE SET judgement = excluded.judgement,"
            "   support = excluded.support, decided_by = excluded.decided_by,"
            "   decided_at = excluded.decided_at",
            (ref_id, dominio["id"], julgamento, clean_text(item.get("justificativa")),
             member_id, agora))
        r += 1
    db.conn.commit()
    return {"campos": n, "dominios": r}


def versao_final(db: Database, ref_id: int) -> dict[str, Any]:
    valores = {linha["code"]: linha["value"] for linha in db.dicts(
        "SELECT f.code, x.value FROM extraction_final x"
        "  JOIN extraction_fields f ON f.id = x.field_id WHERE x.ref_id = ?", (ref_id,))}
    risco = {linha["code"]: {"julgamento": linha["judgement"],
                             "justificativa": linha["support"]}
             for linha in db.dicts(
        "SELECT d.code, x.judgement, x.support FROM rob_final x"
        "  JOIN rob_domains d ON d.id = x.domain_id WHERE x.ref_id = ?", (ref_id,))}
    return {"valores": valores, "risco": risco}


# ----------------------------------------------------------------------
# As saidas
# ----------------------------------------------------------------------
def consenso(db: Database, ref_id: int) -> dict[str, dict[str, Any]]:
    """O valor que vale para cada campo, e de onde ele veio.

    Tres origens, nesta ordem:

      `acordado`   alguem conciliou as duas extracoes e gravou a final
      `unanime`    as duas pessoas escreveram a mesma coisa -- e isso JA e
                   consenso; exigir um clique para confirmar o que ninguem
                   contesta e trabalho inutil, e trabalho inutil e pulado
      `provisorio` so uma pessoa extraiu, ou as duas discordam e ninguem
                   conciliou ainda

    A origem viaja junto com o valor porque a tabela precisa mostrar a
    diferenca: celula vazia parece "nao se aplica", e nao "ainda nao
    conferimos".
    """
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    final = versao_final(db, ref_id)["valores"]
    por_campo: dict[str, list[str]] = {}
    for linha in db.dicts(
            "SELECT f.code, e.value FROM extractions e"
            "  JOIN extraction_fields f ON f.id = e.field_id"
            " WHERE e.ref_id = ? ORDER BY e.updated_at", (ref_id,)):
        por_campo.setdefault(linha["code"], []).append((linha["value"] or "").strip())

    saida: dict[str, dict[str, Any]] = {}
    for campo in campos(db, review_id):
        codigo = campo["code"]
        acordado = final.get(codigo)
        if acordado not in (None, ""):
            saida[codigo] = {"valor": acordado, "origem": "acordado"}
            continue
        dadas = [v for v in por_campo.get(codigo, []) if v]
        if dadas and len(set(dadas)) == 1 and len(dadas) >= 2:
            saida[codigo] = {"valor": dadas[0], "origem": "unanime"}
        elif dadas:
            saida[codigo] = {"valor": dadas[0], "origem": "provisorio"}
        else:
            saida[codigo] = {"valor": "", "origem": "vazio"}
    return saida


def consenso_risco(db: Database, ref_id: int) -> dict[str, dict[str, Any]]:
    """O mesmo, para os dominios de risco de vies."""
    review_id = db.scalar("SELECT review_id FROM refs WHERE id = ?", (ref_id,))
    final = versao_final(db, ref_id)["risco"]
    por_dominio: dict[str, list[dict[str, Any]]] = {}
    for linha in db.dicts(
            "SELECT d.code, a.judgement, a.support FROM rob_answers a"
            "  JOIN rob_domains d ON d.id = a.domain_id"
            " WHERE a.ref_id = ? ORDER BY a.updated_at", (ref_id,)):
        por_dominio.setdefault(linha["code"], []).append(linha)

    saida: dict[str, dict[str, Any]] = {}
    for dominio in dominios(db, review_id):
        codigo = dominio["code"]
        acordado = final.get(codigo)
        if acordado:
            saida[codigo] = {**acordado, "origem": "acordado"}
            continue
        dadas = por_dominio.get(codigo, [])
        julgamentos = {d["judgement"] for d in dadas}
        if len(julgamentos) == 1 and len(dadas) >= 2:
            saida[codigo] = {"julgamento": dadas[0]["judgement"],
                             "justificativa": dadas[0]["support"], "origem": "unanime"}
        elif dadas:
            saida[codigo] = {"julgamento": dadas[0]["judgement"],
                             "justificativa": dadas[0]["support"], "origem": "provisorio"}
        else:
            saida[codigo] = {"julgamento": None, "origem": "vazio"}
    return saida


def tabela(db: Database, review_id: int) -> dict[str, Any]:
    """A tabela de caracteristicas dos estudos incluidos.

    Cada linha e um estudo, cada coluna um campo do formulario. O valor
    e o acordado; onde ainda nao houve acordo, mostra-se o que uma pessoa
    escreveu, marcado como provisorio -- em branco pareceria "nao se
    aplica", e nao "ainda nao conferimos".
    """
    incluidos = db.dicts(
        "SELECT id, title, authors, journal, year, doi FROM refs"
        " WHERE review_id = ? AND stage = 'incluido' AND duplicate_of IS NULL"
        " ORDER BY COALESCE(year, 0), title", (review_id,))
    lista_campos = campos(db, review_id)
    linhas = []
    for estudo in incluidos:
        celulas = consenso(db, estudo["id"])
        linhas.append({**estudo, "estudo": _citacao(estudo), "celulas": celulas})
    return {"campos": lista_campos, "estudos": linhas}


def _citacao(estudo: dict[str, Any]) -> str:
    """'Vilarino et al., 2023' -- como o estudo aparece na tabela."""
    autores = [p.strip() for p in str(estudo.get("authors") or "").split(";") if p.strip()]
    if not autores:
        return str(estudo.get("title") or "sem autoria")[:60]
    primeiro = autores[0].split(",")[0].strip() or autores[0]
    sufixo = " et al." if len(autores) > 2 else (f" & {autores[1].split(',')[0].strip()}"
                                                 if len(autores) == 2 else "")
    return f"{primeiro}{sufixo}, {estudo.get('year') or 's.d.'}"


def semaforo(db: Database, review_id: int) -> dict[str, Any]:
    """Os dados do semaforo de risco de vies: estudos x dominios."""
    ferramenta = ferramenta_da(db, review_id)
    tons = {codigo: tom for codigo, _, tom in ferramenta["julgamentos"]}
    rotulos = {codigo: rotulo for codigo, rotulo, _ in ferramenta["julgamentos"]}
    lista_dominios = dominios(db, review_id)
    estudos = db.dicts(
        "SELECT id, title, authors, year FROM refs"
        " WHERE review_id = ? AND stage = 'incluido' AND duplicate_of IS NULL"
        " ORDER BY COALESCE(year, 0), title", (review_id,))
    linhas, resumo = [], {d["code"]: {} for d in lista_dominios}
    for estudo in estudos:
        acordado = consenso_risco(db, estudo["id"])
        celulas = []
        for dominio in lista_dominios:
            item = acordado.get(dominio["code"]) or {}
            julgamento = item.get("julgamento")
            celulas.append({
                "dominio": dominio["code"], "julgamento": julgamento,
                "rotulo": rotulos.get(julgamento, "Sem julgamento"),
                "tom": tons.get(julgamento, "neutro"),
                "origem": item.get("origem", "vazio"),
                "justificativa": item.get("justificativa"),
            })
            chave = julgamento or "sem_julgamento"
            resumo[dominio["code"]][chave] = resumo[dominio["code"]].get(chave, 0) + 1
        linhas.append({"estudo": _citacao(estudo), "ref_id": estudo["id"],
                       "title": estudo["title"], "celulas": celulas})
    legenda = [{"codigo": c, "rotulo": r, "tom": t}
               for c, r, t in ferramenta["julgamentos"]]
    # Circulo cinza aparece na grade sempre que um dominio ainda nao foi
    # julgado. Se ele nao estiver na legenda, o desenho tem um simbolo sem
    # significado -- e quem le nao sabe se e "sem risco" ou "sem resposta".
    if any(c["julgamento"] is None for linha in linhas for c in linha["celulas"]):
        legenda.append({"codigo": None, "rotulo": "Sem julgamento", "tom": "neutro"})
    return {"ferramenta": ferramenta["nome"], "codigo": ferramenta["codigo"],
            "julgamentos": legenda,
            "dominios": lista_dominios, "estudos": linhas, "resumo": resumo}


def progresso(db: Database, review_id: int) -> dict[str, Any]:
    """Quanto da extracao ja foi feita, e por quem."""
    incluidos = int(db.scalar(
        "SELECT COUNT(*) FROM refs WHERE review_id = ? AND stage = 'incluido'"
        "   AND duplicate_of IS NULL", (review_id,)) or 0)
    com_duas = int(db.scalar(
        "SELECT COUNT(*) FROM (SELECT e.ref_id FROM extractions e"
        "   JOIN refs r ON r.id = e.ref_id WHERE r.review_id = ?"
        "   GROUP BY e.ref_id HAVING COUNT(DISTINCT e.member_id) >= 2)", (review_id,)) or 0)
    acordados = int(db.scalar(
        "SELECT COUNT(DISTINCT x.ref_id) FROM extraction_final x"
        "  JOIN refs r ON r.id = x.ref_id WHERE r.review_id = ?", (review_id,)) or 0)
    return {
        "incluidos": incluidos, "com_duas_extracoes": com_duas, "acordados": acordados,
        "por_pessoa": db.dicts(
            "SELECT m.full_name AS quem, COUNT(DISTINCT e.ref_id) AS estudos,"
            "       COUNT(*) AS campos, MAX(e.updated_at) AS ultima"
            "  FROM extractions e JOIN members m ON m.id = e.member_id"
            "  JOIN refs r ON r.id = e.ref_id WHERE r.review_id = ?"
            " GROUP BY m.id ORDER BY estudos DESC", (review_id,)),
    }


def _texto(valor: Any) -> str | None:
    if isinstance(valor, (list, tuple)):
        return "; ".join(str(v) for v in valor if str(v).strip()) or None
    if isinstance(valor, dict):
        return json.dumps(valor, ensure_ascii=False)
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    return clean_text(valor)
