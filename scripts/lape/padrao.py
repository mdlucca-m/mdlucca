"""Que tipo de revisao e esta, e o que o padrao dela cobra.

Sistematica, de escopo e mapping review nao sao a mesma coisa com nomes
diferentes. Elas respondem perguntas diferentes, seguem padroes de relato
diferentes e, principalmente, COBRAM COISAS DIFERENTES -- e o sistema
tratava as tres como uma so. Uma revisao de escopo saia com a conferencia
da sistematica, pedindo risco de vies que ela nao faz por definicao; e uma
sistematica podia chegar ao fim sem ninguem ter cobrado a avaliacao de
qualidade, que nela e obrigatoria.

O que este modulo NAO e: a checklist oficial. O PRISMA 2020 tem 27 itens e
o PRISMA-ScR tem 20, sao instrumentos publicados e e neles que a revista
manda conferir -- os links estao em cada tipo aqui embaixo. O que ha aqui
e um RESUMO em portugues do que o padrao cobra, e vale por uma coisa que
a checklist em PDF nao faz: ela nao sabe o que voce ja fez, e esta sabe.

Cada item diz em que situacao esta:

    feito    o sistema CONFERIU no banco e esta la
    falta    o sistema conferiu e nao esta
    manual   so uma pessoa pode dizer -- o sistema nao ve
    na       nao se aplica a este tipo de revisao

A diferenca entre "falta" e "manual" e a razao de este modulo existir. Uma
checklist que marca tudo como pendente e um PDF; uma que marca tudo como
feito e mentira. Esta marca so o que ela pode ver, e diz onde viu.
"""
from __future__ import annotations

from typing import Any, Callable

from .db import Database

FEITO, FALTA, MANUAL, NAO_SE_APLICA = "feito", "falta", "manual", "na"

TIPOS: tuple[dict[str, Any], ...] = (
    {
        "code": "sistematica",
        "rotulo": "Revisão sistemática",
        "padrao": "PRISMA 2020",
        "url": "https://www.prisma-statement.org/prisma-2020",
        "resumo": "Responde uma pergunta fechada sobre efeito ou associação, com "
                  "busca exaustiva, seleção e extração em duplicata e avaliação "
                  "da qualidade de cada estudo incluído.",
        # A avaliacao de qualidade e o que separa uma sistematica de uma
        # revisao narrativa com busca organizada.
        "risco_de_vies": True,
        "extracao": "extração de dados",
    },
    {
        "code": "escopo",
        "rotulo": "Revisão de escopo",
        "padrao": "PRISMA-ScR",
        "url": "https://www.prisma-statement.org/scoping",
        "resumo": "Mapeia o que existe sobre um tema amplo — que estudos há, com "
                  "que desenhos, em que populações e onde estão as lacunas. A "
                  "pergunta é aberta, e a avaliação de qualidade é opcional: o "
                  "objetivo é descrever o campo, não decidir o que funciona.",
        "risco_de_vies": False,
        # O JBI chama de "charting": nao se extrai efeito, mapeia-se
        # caracteristica. O nome muda porque o trabalho muda.
        "extracao": "charting (mapeamento dos dados)",
    },
    {
        "code": "mapping",
        "rotulo": "Mapping review",
        "padrao": "PRISMA-ScR (adaptado)",
        "url": "https://www.prisma-statement.org/scoping",
        "resumo": "Mapeia a COBERTURA da literatura: quanto existe de cada "
                  "recorte, e o que não foi estudado. Fica no nível do título e "
                  "resumo — o texto completo só entra quando o mapa exige — e "
                  "por isso descreve volume e distribuição, não achados.",
        "risco_de_vies": False,
        "extracao": "mapeamento da cobertura",
    },
)

PADRAO = "sistematica"


def tipo(code: str | None) -> dict[str, Any]:
    """O tipo pedido, ou o padrao -- nunca um erro por tipo desconhecido.

    Um banco antigo tem revisoes sem tipo, e uma revisao aberta antes
    deste campo existir nao pode deixar de abrir por causa dele.
    """
    for t in TIPOS:
        if t["code"] == (code or PADRAO):
            return t
    return TIPOS[0]


def _tem(valor: Any) -> bool:
    return bool(str(valor or "").strip())


# ----------------------------------------------------------------------
# As conferencias. Cada uma olha o banco e devolve (situacao, detalhe).
# ----------------------------------------------------------------------
def _protocolo(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    if _tem(rev.get("protocol_url")):
        return FEITO, str(rev["protocol_url"])
    return FALTA, ("registre o protocolo (PROSPERO, OSF ou Open Science "
                   "Framework) e guarde o link aqui")


def _pergunta(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    partes = [c for c in ("question", "population", "intervention", "outcome")
              if _tem(rev.get(c))]
    if _tem(rev.get("question")) and len(partes) >= 3:
        return FEITO, f"{len(partes)} de 4 campos preenchidos"
    if partes:
        return FALTA, (f"só {len(partes)} de 4 campos (pergunta, população, "
                       "intervenção, desfecho)")
    return FALTA, "nenhum campo da pergunta preenchido"


def _criterios(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    if _tem(rev.get("study_designs")):
        return FEITO, str(rev["study_designs"])[:120]
    return FALTA, "declare os delineamentos elegíveis"


def _fontes(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    bases = db.dicts(
        "SELECT base, COUNT(*) AS n, SUM(CASE WHEN query IS NULL OR query = ''"
        "   THEN 1 ELSE 0 END) AS sem_query,"
        "   SUM(CASE WHEN searched_on IS NULL OR searched_on = ''"
        "   THEN 1 ELSE 0 END) AS sem_data"
        "  FROM review_searches WHERE review_id = ? GROUP BY base ORDER BY base",
        (rev["id"],))
    if not bases:
        return FALTA, "nenhuma busca importada ainda"
    nomes = ", ".join(str(b["base"] or "sem nome") for b in bases)
    return FEITO, f"{len(bases)} base(s): {nomes}"


def _estrategia(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    """A estrategia de CADA base, com a data. E o que torna refazivel."""
    faltando = db.dicts(
        "SELECT base FROM review_searches"
        " WHERE review_id = ? AND (query IS NULL OR query = '')", (rev["id"],))
    total = db.scalar("SELECT COUNT(*) FROM review_searches WHERE review_id = ?",
                      (rev["id"],)) or 0
    if not total:
        return FALTA, "nenhuma busca importada ainda"
    if faltando:
        nomes = ", ".join(str(f["base"] or "sem nome") for f in faltando)
        return FALTA, f"{len(faltando)} de {total} sem a estratégia gravada: {nomes}"
    return FEITO, f"as {total} buscas têm a estratégia gravada"


def _data_da_busca(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    sem = db.scalar(
        "SELECT COUNT(*) FROM review_searches WHERE review_id = ?"
        "   AND (searched_on IS NULL OR searched_on = '')", (rev["id"],)) or 0
    total = db.scalar("SELECT COUNT(*) FROM review_searches WHERE review_id = ?",
                      (rev["id"],)) or 0
    if not total:
        return FALTA, "nenhuma busca importada ainda"
    if sem:
        return FALTA, f"{sem} de {total} buscas sem a data"
    ultima = db.scalar("SELECT MAX(searched_on) FROM review_searches"
                       " WHERE review_id = ?", (rev["id"],))
    return FEITO, f"última busca em {ultima}"


def _duplicata_na_selecao(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    precisa = int(rev.get("reviewers_needed") or 1)
    gente = db.scalar(
        "SELECT COUNT(DISTINCT s.member_id) FROM screenings s"
        "  JOIN refs r ON r.id = s.ref_id WHERE r.review_id = ?", (rev["id"],)) or 0
    if precisa < 2:
        return FALTA, ("a revisão está configurada para um avaliador só; o padrão "
                       "pede dois, em separado")
    if gente >= 2:
        return FEITO, f"{gente} pessoa(s) triando, com {precisa} decisões por registro"
    return FALTA, (f"configurada para {precisa} avaliadores, mas só {gente} "
                   "triou até agora")


def _as_cegas(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    if int(rev.get("blind") or 0):
        return FEITO, "cada avaliador decide sem ver a decisão do outro"
    return FALTA, ("a triagem está aberta: quem entra depois vê a decisão de quem "
                   "entrou antes, e isso arrasta a segunda opinião")


def _duplicados(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    n = db.scalar("SELECT COUNT(*) FROM refs WHERE review_id = ?"
                  "   AND duplicate_of IS NOT NULL", (rev["id"],)) or 0
    total = db.scalar("SELECT COUNT(*) FROM refs WHERE review_id = ?",
                      (rev["id"],)) or 0
    if not total:
        return FALTA, "nenhuma referência importada ainda"
    return FEITO, (f"{n} repetição(ões) marcada(s) e contada(s) em {total} "
                   "registro(s) importados")


def _motivos(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    """Excluido tem de ter motivo. E o que o fluxograma cobra.

    A conferencia e sobre quem chegou ao TEXTO COMPLETO -- e quem foi
    excluido no titulo e resumo nao precisa de motivo individual, e o
    PRISMA nao pede. Aqui isso aparece como `screenings` na etapa
    `texto_completo`: e nela que a decisao carrega o motivo.
    """
    sem = db.scalar(
        "SELECT COUNT(DISTINCT s.ref_id) FROM screenings s"
        "  JOIN refs r ON r.id = s.ref_id"
        " WHERE r.review_id = ? AND s.stage = 'texto_completo'"
        "   AND s.decision = 'excluir' AND s.reason_id IS NULL", (rev["id"],)) or 0
    total = db.scalar(
        "SELECT COUNT(DISTINCT s.ref_id) FROM screenings s"
        "  JOIN refs r ON r.id = s.ref_id"
        " WHERE r.review_id = ? AND s.stage = 'texto_completo'"
        "   AND s.decision = 'excluir'", (rev["id"],)) or 0
    if not total:
        return MANUAL, "ninguém foi excluído no texto completo ainda"
    if sem:
        return FALTA, f"{sem} de {total} excluído(s) no texto completo sem motivo"
    return FEITO, f"os {total} excluídos no texto completo têm motivo"


def _extracao_em_duplicata(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    linhas = db.dicts(
        "SELECT e.ref_id, COUNT(DISTINCT e.member_id) AS gente FROM extractions e"
        "  JOIN refs r ON r.id = e.ref_id WHERE r.review_id = ?"
        " GROUP BY e.ref_id", (rev["id"],))
    if not linhas:
        return FALTA, "nenhuma extração começou ainda"
    em_dupla = sum(1 for linha in linhas if linha["gente"] >= 2)
    if em_dupla == len(linhas):
        return FEITO, f"os {len(linhas)} estudos extraídos foram por duas pessoas"
    return FALTA, (f"{em_dupla} de {len(linhas)} estudos extraídos por duas "
                   "pessoas — conferir o que a outra digitou não é duplicata")


def _risco_de_vies(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    dominios = db.scalar("SELECT COUNT(*) FROM rob_domains WHERE review_id = ?",
                         (rev["id"],)) or 0
    if not dominios:
        return FALTA, ("nenhum instrumento escolhido — ROB 2, ROBINS-I ou JBI, "
                       "conforme o delineamento dos incluídos")
    julgados = db.scalar(
        "SELECT COUNT(DISTINCT f.ref_id) FROM rob_final f"
        "  JOIN refs r ON r.id = f.ref_id WHERE r.review_id = ?", (rev["id"],)) or 0
    incluidos = db.scalar(
        "SELECT COUNT(*) FROM refs WHERE review_id = ? AND stage = 'incluido'",
        (rev["id"],)) or 0
    if incluidos and julgados >= incluidos:
        return FEITO, f"{julgados} estudo(s) com julgamento fechado"
    return FALTA, f"{julgados} de {incluidos} incluído(s) com julgamento fechado"


def _concordancia(db: Database, rev: dict[str, Any]) -> tuple[str, str]:
    gente = db.scalar(
        "SELECT COUNT(DISTINCT s.member_id) FROM screenings s"
        "  JOIN refs r ON r.id = s.ref_id WHERE r.review_id = ?", (rev["id"],)) or 0
    if gente >= 2:
        return FEITO, "há decisões de duas pessoas: a tela de conflitos calcula o kappa"
    return FALTA, "são precisas duas pessoas triando para haver concordância"


ITENS: tuple[dict[str, Any], ...] = (
    {"code": "protocolo", "rotulo": "Protocolo registrado antes da busca",
     "porque": "Registrar depois não protege de nada: o protocolo existe para "
               "fixar a pergunta e os critérios antes de ver os resultados.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _protocolo},
    {"code": "pergunta", "rotulo": "Pergunta e critérios de elegibilidade",
     "porque": "É o que separa a revisão de uma leitura organizada.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _pergunta},
    {"code": "criterios", "rotulo": "Delineamentos elegíveis declarados",
     "porque": "Sem isso, incluir ou excluir um estudo vira decisão do dia.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _criterios},
    {"code": "fontes", "rotulo": "Fontes de informação (todas as bases)",
     "porque": "O padrão pede a lista completa, e não só as que responderam.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _fontes},
    {"code": "estrategia", "rotulo": "Estratégia de busca completa, base por base",
     "porque": "É o item que torna a revisão refazível — e o que o revisor "
               "da banca pede para conferir.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _estrategia},
    {"code": "data", "rotulo": "Data da última busca em cada base",
     "porque": "Uma busca sem data não pode ser atualizada nem repetida.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _data_da_busca},
    {"code": "duplicata", "rotulo": "Seleção por dois avaliadores, em separado",
     "porque": "Uma pessoa sozinha erra, e erra sempre para o mesmo lado.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _duplicata_na_selecao},
    {"code": "cegas", "rotulo": "Triagem às cegas",
     "porque": "Ver a decisão do outro antes de decidir não é segunda opinião.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _as_cegas},
    {"code": "duplicados", "rotulo": "Repetições entre bases removidas e contadas",
     "porque": "O fluxograma cobra quantos foram removidos por repetição.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _duplicados},
    {"code": "motivos", "rotulo": "Excluídos no texto completo, com motivo",
     "porque": "É exigência do fluxograma, e é o que permite discordar da revisão.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": _motivos},
    {"code": "extracao", "rotulo": "Extração por duas pessoas, em separado",
     "porque": "Conferir o que a outra digitou não é extração em duplicata.",
     "tipos": ("sistematica", "escopo"), "confere": _extracao_em_duplicata},
    {"code": "rob", "rotulo": "Risco de viés de cada estudo incluído",
     "porque": "É o que separa uma sistemática de uma revisão narrativa com "
               "busca organizada. Numa revisão de escopo é opcional por "
               "definição: ali o objetivo é descrever o campo, não decidir o "
               "que funciona.",
     "tipos": ("sistematica",), "confere": _risco_de_vies},
    {"code": "concordancia", "rotulo": "Concordância entre avaliadores relatada",
     "porque": "Diz se os critérios estavam claros o bastante para duas "
               "pessoas lerem igual.",
     "tipos": ("sistematica", "escopo"), "confere": _concordancia},
    {"code": "sintese", "rotulo": "Síntese descrita (como os achados foram juntados)",
     "porque": "Meta-análise, síntese narrativa ou mapa: o método tem de estar "
               "escrito, e o sistema não tem como saber qual você usou.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": None},
    {"code": "limitacoes", "rotulo": "Limitações e conflitos de interesse",
     "porque": "Vai no artigo, e nenhum sistema declara isso por você.",
     "tipos": ("sistematica", "escopo", "mapping"), "confere": None},
)


def conferir(db: Database, review_id: int) -> dict[str, Any]:
    """A conferencia do padrao desta revisao, item a item."""
    linhas = db.dicts("SELECT * FROM reviews WHERE id = ?", (review_id,))
    if not linhas:
        raise ValueError(f"revisão {review_id} não existe")
    rev = linhas[0]
    esta = tipo(rev.get("tipo"))

    itens = []
    for item in ITENS:
        if esta["code"] not in item["tipos"]:
            situacao, detalhe = NAO_SE_APLICA, _porque_nao_se_aplica(item, esta)
        elif item["confere"] is None:
            situacao, detalhe = MANUAL, "o sistema não vê isto — confira no texto"
        else:
            situacao, detalhe = item["confere"](db, rev)
        itens.append({"code": item["code"], "rotulo": item["rotulo"],
                      "porque": item["porque"], "situacao": situacao,
                      "detalhe": detalhe})

    conta = {s: sum(1 for i in itens if i["situacao"] == s)
             for s in (FEITO, FALTA, MANUAL, NAO_SE_APLICA)}
    return {"review_id": review_id, "tipo": esta, "itens": itens, "conta": conta,
            "aviso": ("Este é um resumo em português do que o padrão cobra, e não "
                      "a checklist oficial — ela está em " + esta["url"] + ". O que "
                      "o sistema marca como feito, ele conferiu no banco; o resto "
                      "continua sendo trabalho seu.")}


def _porque_nao_se_aplica(item: dict[str, Any], esta: dict[str, Any]) -> str:
    if item["code"] == "rob":
        return (f"{esta['rotulo']}: a avaliação de qualidade é opcional — o "
                "objetivo é descrever o campo, não decidir o que funciona")
    if item["code"] == "extracao":
        return f"{esta['rotulo']}: fica no nível do título e resumo"
    return f"não se aplica a {esta['rotulo'].lower()}"
