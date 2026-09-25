"""O painel ao vivo: uma tela, os numeros de agora, e o que mudou.

O painel de indicadores responde a tudo, em sete secoes e quarenta telas.
Esta pagina responde a UMA pergunta -- "como o laboratorio esta, e para
onde vai?" -- e cabe num projetor. Cada numero vem com o mesmo numero do
periodo anterior ao lado, porque um numero sozinho nao diz nada: 9
publicados e bom ou ruim conforme o ano passado teve 12 ou 4.

Tres regras, e as tres sao contra mentir com grafico:

1. O periodo e ALINHADO AO ANO. O laboratorio preenche `year_published`
   e nem sempre `published_on`; um recorte de "ultimos 12 meses" teria de
   decidir em que mes cai um artigo que so tem o ano, e qualquer decisao
   seria invencao. Por ano, a conta e exata.

2. Comparacao so quando ha com o que comparar. Sem periodo anterior, ou
   com zero nele, a seta nao aparece -- "+infinito%" nao e leitura, e
   comparar com zero e o jeito mais facil de fabricar um crescimento.

3. As "leituras" no fim sao CALCULADAS, e cada frase carrega o numero e a
   regra de onde saiu. Nao ha modelo de linguagem aqui, e a tela diz isso.
   Uma frase que nao possa ser refeita a partir do banco nao entra.
"""
from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from typing import Any

from . import biblioteca, metas, padrao, revisao, sinais
from . import linhas as linhas_vocab
from .db import Database

PERIODOS: tuple[dict[str, Any], ...] = (
    {"code": "ano", "rotulo": "Este ano", "anos": 1},
    {"code": "3a", "rotulo": "Últimos 3 anos", "anos": 3},
    {"code": "5a", "rotulo": "Últimos 5 anos", "anos": 5},
    {"code": "tudo", "rotulo": "Desde o início", "anos": None},
)
PADRAO = "ano"

SITUACOES: tuple[tuple[str, str], ...] = (
    ("em_producao", "Em produção"), ("submetido", "Submetido"),
    ("em_revisao", "Em revisão"), ("aceito", "Aceito"),
    ("publicado", "Publicado"), ("rejeitado", "Rejeitado"),
    ("arquivado", "Arquivado"),
)
ROTULO_DA_SITUACAO = dict(SITUACOES)

MESES = ("jan", "fev", "mar", "abr", "mai", "jun",
         "jul", "ago", "set", "out", "nov", "dez")
MESES_POR_EXTENSO = ("janeiro", "fevereiro", "março", "abril", "maio", "junho",
                     "julho", "agosto", "setembro", "outubro", "novembro",
                     "dezembro")

# Faixas de citacao do histograma. Fechadas em cima, abertas na ultima.
FAIXAS_DE_CITACAO: tuple[tuple[str, int, int | None], ...] = (
    ("0", 0, 0), ("1–5", 1, 5), ("6–20", 6, 20), ("21–50", 21, 50),
    ("51–100", 51, 100), ("> 100", 101, None),
)

# Quantas linhas de pesquisa aparecem com nome proprio nos graficos que
# empilham; o resto vira "Outras". Oito series e o teto da paleta, e
# seis ja e o que um olho separa numa area empilhada.
LINHAS_COM_NOME = 6

ANO_SQL = "CAST(strftime('%Y', {c}) AS INTEGER)"
MES_SQL = "CAST(strftime('%m', {c}) AS INTEGER)"

# A melhor base por artigo: o painel inteiro conta citacao assim, e este
# painel nao pode contar de outro jeito, senao os dois discordam na tela.
MELHOR_BASE = ("MAX(COALESCE(wos_citations, 0), COALESCE(scopus_citations, 0),"
               " COALESCE(openalex_citations, 0))")


# ----------------------------------------------------------------------
# Periodo
# ----------------------------------------------------------------------
def periodo(db: Database, code: str | None, hoje: date | None = None) -> dict[str, Any]:
    """O recorte pedido, sempre em anos inteiros, com o anterior do mesmo tamanho."""
    hoje = hoje or date.today()
    escolhido = next((p for p in PERIODOS if p["code"] == (code or PADRAO)), PERIODOS[0])
    ate = hoje.year
    if escolhido["anos"] is None:
        primeiro = db.scalar(
            "SELECT MIN(ano) FROM ("
            "  SELECT MIN(year_published) AS ano FROM articles"
            f"  UNION ALL SELECT MIN({ANO_SQL.format(c='started_on')}) FROM articles"
            f"  UNION ALL SELECT MIN({ANO_SQL.format(c='submitted_on')}) FROM submissions)")
        de = int(primeiro) if primeiro else ate
        anterior = None
    else:
        de = ate - escolhido["anos"] + 1
        anterior = (de - escolhido["anos"], de - 1)
    return {
        "code": escolhido["code"], "rotulo": escolhido["rotulo"],
        "de": de, "ate": ate, "anterior": anterior,
        "mensal": escolhido["anos"] == 1,
        # O ano em curso nao acabou. A seta compara com o anterior INTEIRO,
        # e a tela precisa dizer isso ao lado dela.
        "meses_restantes": 12 - hoje.month,
        "hoje": hoje.isoformat(),
    }


# ----------------------------------------------------------------------
# As contagens que os indicadores usam
# ----------------------------------------------------------------------
def _publicados(db: Database, de: int, ate: int) -> int:
    return int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
        "   AND year_published BETWEEN ? AND ?", (de, ate)) or 0)


def _submetidos(db: Database, de: int, ate: int) -> int:
    return int(db.scalar(
        "SELECT COUNT(*) FROM submissions WHERE submitted_on IS NOT NULL"
        f"   AND {ANO_SQL.format(c='submitted_on')} BETWEEN ? AND ?", (de, ate)) or 0)


def _aceitos(db: Database, de: int, ate: int) -> int:
    return int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE accepted_on IS NOT NULL"
        f"   AND {ANO_SQL.format(c='accepted_on')} BETWEEN ? AND ?", (de, ate)) or 0)


def _citacoes_agora(db: Database) -> int:
    return int(db.scalar(f"SELECT COALESCE(SUM({MELHOR_BASE}), 0) FROM articles") or 0)


def _citacoes_em(db: Database, dia: str) -> int | None:
    """A soma das citacoes no ultimo instantaneo ate `dia`, ou None sem historico.

    A melhor base por artigo, como em `_citacoes_agora`: o mesmo criterio
    nas duas pontas, senao a diferenca mede a troca de criterio e nao as
    citacoes que chegaram.
    """
    ha = db.scalar("SELECT COUNT(*) FROM citation_snapshots WHERE snapshot_on <= ?", (dia,))
    if not ha:
        return None
    return int(db.scalar(
        "SELECT COALESCE(SUM(melhor), 0) FROM ("
        "  SELECT article_id, MAX(citations) AS melhor FROM citation_snapshots s"
        "   WHERE snapshot_on = (SELECT MAX(snapshot_on) FROM citation_snapshots s2"
        "                         WHERE s2.article_id = s.article_id"
        "                           AND s2.source = s.source AND s2.snapshot_on <= ?)"
        "   GROUP BY article_id)", (dia,)) or 0)


def _por_ano(db: Database, sql: str, de: int, ate: int) -> list[int]:
    """Uma contagem por ano de `de` a `ate`, com zero onde nao houve nada."""
    linhas = db.dicts(sql, (de, ate))
    conta = {int(l["ano"]): int(l["n"]) for l in linhas if l["ano"] is not None}
    return [conta.get(ano, 0) for ano in range(de, ate + 1)]


def _variacao(agora: int, antes: int | None) -> dict[str, Any]:
    """A seta. So existe com anterior maior que zero."""
    if antes is None:
        return {"anterior": None, "delta": None, "pct": None}
    delta = agora - antes
    pct = round(100.0 * delta / antes, 1) if antes else None
    return {"anterior": antes, "delta": delta, "pct": pct}


def indicadores(db: Database, per: dict[str, Any]) -> list[dict[str, Any]]:
    de, ate = per["de"], per["ate"]
    ant = per["anterior"]

    saida = []
    for code, rotulo, conta, sql_por_ano in (
        ("publicacoes", "Publicados", _publicados,
         "SELECT year_published AS ano, COUNT(*) AS n FROM articles"
         " WHERE status = 'publicado' AND year_published BETWEEN ? AND ? GROUP BY 1"),
        ("submissoes", "Submissões", _submetidos,
         f"SELECT {ANO_SQL.format(c='submitted_on')} AS ano, COUNT(*) AS n FROM submissions"
         f" WHERE submitted_on IS NOT NULL AND {ANO_SQL.format(c='submitted_on')}"
         " BETWEEN ? AND ? GROUP BY 1"),
        ("aceites", "Aceites", _aceitos,
         f"SELECT {ANO_SQL.format(c='accepted_on')} AS ano, COUNT(*) AS n FROM articles"
         f" WHERE accepted_on IS NOT NULL AND {ANO_SQL.format(c='accepted_on')}"
         " BETWEEN ? AND ? GROUP BY 1"),
    ):
        agora = conta(db, de, ate)
        antes = conta(db, ant[0], ant[1]) if ant else None
        saida.append({
            "code": code, "rotulo": rotulo, "valor": agora,
            **_variacao(agora, antes),
            "faisca": _por_ano(db, sql_por_ano, ate - 5, ate),
            "faisca_de": ate - 5,
            "fonte": metas.CONTAGEM[code].split(" WHERE")[0].replace("SELECT COUNT(*) FROM ", ""),
        })

    # Citacoes: o estoque de agora, e quanto entrou desde o comeco do
    # periodo. Nao ha "periodo anterior" de citacao -- ha o que o
    # laboratorio tinha no primeiro dia e o que tem hoje.
    agora = _citacoes_agora(db)
    no_comeco = _citacoes_em(db, f"{de}-01-01")
    historico = db.dicts(
        "SELECT snapshot_on AS dia, SUM(melhor) AS n FROM ("
        "  SELECT snapshot_on, article_id, MAX(citations) AS melhor"
        "    FROM citation_snapshots GROUP BY snapshot_on, article_id)"
        " GROUP BY snapshot_on ORDER BY snapshot_on")
    saida.append({
        "code": "citacoes", "rotulo": "Citações", "valor": agora,
        **_variacao(agora, no_comeco),
        "faisca": [int(h["n"]) for h in historico[-12:]],
        "faisca_de": historico[-12:][0]["dia"][:7] if historico else None,
        "fonte": "articles (melhor base) e citation_snapshots",
        "nota": f"recebidas desde 1º/jan/{de}" if no_comeco is not None
                else "sem instantâneo anterior para comparar",
    })
    return saida


# ----------------------------------------------------------------------
# Evolucao no tempo
# ----------------------------------------------------------------------
def evolucao(db: Database, per: dict[str, Any]) -> dict[str, Any]:
    """Mes a mes num periodo de um ano; ano a ano nos maiores.

    Mes a mes so entra quem tem a data completa. Quem so tem o ano e
    CONTADO a parte e dito na legenda -- espalhar esses artigos por um mes
    qualquer daria uma curva bonita e falsa.
    """
    de, ate = per["de"], per["ate"]
    if per["mensal"]:
        rotulos = [f"{MESES[m]}/{str(ate)[2:]}" for m in range(12)]
        series = []
        for rotulo, sql in (
            ("Publicados", f"SELECT {MES_SQL.format(c='published_on')} AS m, COUNT(*) AS n"
                           " FROM articles WHERE status = 'publicado'"
                           f" AND {ANO_SQL.format(c='published_on')} = ? GROUP BY 1"),
            ("Submetidos", f"SELECT {MES_SQL.format(c='submitted_on')} AS m, COUNT(*) AS n"
                           f" FROM submissions WHERE {ANO_SQL.format(c='submitted_on')} = ?"
                           " GROUP BY 1"),
            ("Aceitos", f"SELECT {MES_SQL.format(c='accepted_on')} AS m, COUNT(*) AS n"
                        f" FROM articles WHERE {ANO_SQL.format(c='accepted_on')} = ? GROUP BY 1"),
        ):
            conta = {int(l["m"]): int(l["n"]) for l in db.dicts(sql, (ate,)) if l["m"]}
            series.append({"label": rotulo, "values": [conta.get(m, 0) for m in range(1, 13)]})
        sem_mes = int(db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
            "   AND year_published = ? AND published_on IS NULL", (ate,)) or 0)
        return {"grao": "mes", "labels": rotulos, "series": series, "sem_mes": sem_mes}

    rotulos = [str(a) for a in range(de, ate + 1)]
    series = [
        {"label": "Publicados", "values": _por_ano(
            db, "SELECT year_published AS ano, COUNT(*) AS n FROM articles"
                " WHERE status = 'publicado' AND year_published BETWEEN ? AND ? GROUP BY 1",
            de, ate)},
        {"label": "Submetidos", "values": _por_ano(
            db, f"SELECT {ANO_SQL.format(c='submitted_on')} AS ano, COUNT(*) AS n"
                " FROM submissions WHERE submitted_on IS NOT NULL"
                f" AND {ANO_SQL.format(c='submitted_on')} BETWEEN ? AND ? GROUP BY 1",
            de, ate)},
        {"label": "Aceitos", "values": _por_ano(
            db, f"SELECT {ANO_SQL.format(c='accepted_on')} AS ano, COUNT(*) AS n"
                " FROM articles WHERE accepted_on IS NOT NULL"
                f" AND {ANO_SQL.format(c='accepted_on')} BETWEEN ? AND ? GROUP BY 1",
            de, ate)},
    ]
    return {"grao": "ano", "labels": rotulos, "series": series, "sem_mes": 0}


# ----------------------------------------------------------------------
# Recortes: linha e situacao
# ----------------------------------------------------------------------
def _publicados_por_linha(db: Database, de: int, ate: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT COALESCE(rl.name, 'Sem linha') AS linha, rl.code AS code, COUNT(*) AS n"
        "  FROM articles a LEFT JOIN research_lines rl ON rl.id = a.research_line_id"
        " WHERE a.status = 'publicado' AND a.year_published BETWEEN ? AND ?"
        " GROUP BY 1, 2 ORDER BY n DESC, linha", (de, ate))


def por_linha(db: Database, per: dict[str, Any]) -> dict[str, Any]:
    agora = _publicados_por_linha(db, per["de"], per["ate"])
    antes = (_publicados_por_linha(db, *per["anterior"]) if per["anterior"] else [])
    total = sum(int(l["n"]) for l in agora)
    return {
        # O icone vem do vocabulario das linhas: e o mesmo desenho que o
        # mural e o painel usam, e nao um palpite desta tela.
        "items": [{"label": l["linha"], "value": int(l["n"]),
                   "pct": round(100.0 * int(l["n"]) / total, 1) if total else 0.0,
                   "icone": linhas_vocab.icone_de(l["code"], l["linha"])}
                  for l in agora],
        "anterior": {l["linha"]: int(l["n"]) for l in antes},
        "total": total,
    }


def por_situacao(db: Database) -> list[dict[str, Any]]:
    """Onde cada artigo esta AGORA -- e um retrato, nao um periodo."""
    conta = {l["status"]: int(l["n"]) for l in db.dicts(
        "SELECT status, COUNT(*) AS n FROM articles GROUP BY status")}
    return [{"code": code, "label": rotulo, "value": conta.get(code, 0)}
            for code, rotulo in SITUACOES if conta.get(code, 0)]


# ----------------------------------------------------------------------
# O caminho do artigo
# ----------------------------------------------------------------------
def caminho(db: Database) -> list[dict[str, Any]]:
    """As seis etapas, com o que ha em cada uma AGORA e a tela que a faz.

    Nao e um funil: cada etapa conta uma coisa diferente (referencia,
    registro triado, artigo), e por isso nao ha porcentagem entre elas.
    Uma porcentagem aqui compararia laranja com tijolo.
    """
    def n(sql: str) -> int:
        return int(db.scalar(sql) or 0)

    situacoes = {l["status"]: int(l["n"]) for l in db.dicts(
        "SELECT status, COUNT(*) AS n FROM articles GROUP BY status")}
    return [
        {"code": "biblioteca", "rotulo": "Pesquisa bibliográfica",
         "valor": n("SELECT COUNT(*) FROM biblioteca_item"), "unidade": "referências no acervo",
         "faz": "as buscas rodam sozinhas nas bases, com a estratégia guardada",
         "ferramenta": "Biblioteca", "href": "/app#biblioteca"},
        {"code": "triagem", "rotulo": "Seleção dos estudos",
         "valor": n("SELECT COUNT(*) FROM refs"), "unidade": "registros em triagem",
         "detalhe": n("SELECT COUNT(*) FROM refs WHERE stage = 'incluido'"),
         "detalhe_rotulo": "incluídos",
         "faz": "dois avaliadores às cegas, PRISMA e risco de viés saindo sozinhos",
         "ferramenta": "Triagem", "href": "/triagem"},
        {"code": "producao", "rotulo": "Escrita",
         "valor": situacoes.get("em_producao", 0), "unidade": "artigos em produção",
         "faz": "cada manuscrito com responsável, linha e variáveis declaradas",
         "ferramenta": "Artigos", "href": "/app#artigos"},
        {"code": "submissao", "rotulo": "Submissão e revisão",
         "valor": situacoes.get("submetido", 0) + situacoes.get("em_revisao", 0),
         "unidade": "esperando resposta de revista",
         "faz": "cada tentativa registrada, com o tempo de espera contado",
         "ferramenta": "Submissões", "href": "/app#submissoes"},
        {"code": "aceite", "rotulo": "Aceite",
         "valor": situacoes.get("aceito", 0), "unidade": "aceitos, ainda não publicados",
         "faz": "o aceite conta no ano em que aconteceu, mesmo publicando depois",
         "ferramenta": "Metas", "href": "/#metas"},
        {"code": "publicacao", "rotulo": "Publicação",
         "valor": situacoes.get("publicado", 0), "unidade": "publicados",
         "faz": "DOI, acesso aberto e citações conferidos nas bases",
         "ferramenta": "Painel", "href": "/#publicacoes"},
    ]


# ----------------------------------------------------------------------
# Os doze olhares
# ----------------------------------------------------------------------
def _calor(db: Database, ate: int) -> dict[str, Any]:
    anos = list(range(ate - 4, ate + 1))
    linhas = db.dicts(
        f"SELECT {ANO_SQL.format(c='published_on')} AS ano,"
        f"       {MES_SQL.format(c='published_on')} AS mes, COUNT(*) AS n"
        "  FROM articles WHERE status = 'publicado' AND published_on IS NOT NULL"
        f"   AND {ANO_SQL.format(c='published_on')} BETWEEN ? AND ? GROUP BY 1, 2",
        (anos[0], anos[-1]))
    conta = {(int(l["ano"]), int(l["mes"])): int(l["n"]) for l in linhas}
    return {"years": anos,
            "values": [conta.get((a, m), 0) for a in anos for m in range(1, 13)]}


def _cascata(db: Database, per: dict[str, Any], linhas: dict[str, Any]) -> dict[str, Any] | None:
    if not per["anterior"]:
        return None
    antes = linhas["anterior"]
    agora = {i["label"]: i["value"] for i in linhas["items"]}
    nomes = sorted(set(antes) | set(agora), key=lambda n: -(agora.get(n, 0) - antes.get(n, 0)))
    items: list[dict[str, Any]] = [
        {"label": f"{per['anterior'][0]}–{per['anterior'][1]}" if per["anterior"][0] != per["anterior"][1]
                  else str(per["anterior"][0]),
         "value": sum(antes.values()), "total": True}]
    for nome in nomes:
        diferenca = agora.get(nome, 0) - antes.get(nome, 0)
        if diferenca:
            items.append({"label": nome, "value": diferenca})
    items.append({"label": f"{per['de']}–{per['ate']}" if per["de"] != per["ate"] else str(per["de"]),
                  "value": sum(agora.values()), "total": True})
    return {"items": items}


def _empilhadas(db: Database, ate: int) -> dict[str, Any]:
    """Artigos por ano e situacao. O ano e o de publicacao para quem publicou
    e o de inicio para o resto -- e o unico ano que todo artigo tem."""
    anos = list(range(ate - 5, ate + 1))
    linhas = db.dicts(
        "SELECT CASE WHEN status = 'publicado' THEN year_published"
        f"            ELSE {ANO_SQL.format(c='started_on')} END AS ano, status, COUNT(*) AS n"
        "  FROM articles GROUP BY 1, 2")
    conta = {(int(l["ano"]), l["status"]): int(l["n"]) for l in linhas if l["ano"] is not None}
    series = []
    for code, rotulo in SITUACOES:
        valores = [conta.get((a, code), 0) for a in anos]
        if any(valores):
            series.append({"label": rotulo, "code": code, "values": valores})
    return {"labels": [str(a) for a in anos], "series": series}


def _dispersao(db: Database, hoje: date) -> dict[str, Any]:
    pontos = db.dicts(
        f"SELECT title, year_published AS ano, {MELHOR_BASE} AS citacoes FROM articles"
        " WHERE status = 'publicado' AND year_published IS NOT NULL")
    return {"points": [{"x": hoje.year - int(p["ano"]), "y": int(p["citacoes"]),
                        "label": str(p["title"] or "")[:80]} for p in pontos]}


def _histograma(db: Database) -> dict[str, Any]:
    valores = [int(l["c"]) for l in db.dicts(
        f"SELECT {MELHOR_BASE} AS c FROM articles WHERE status = 'publicado'")]
    conta = []
    for rotulo, baixo, alto in FAIXAS_DE_CITACAO:
        conta.append(sum(1 for v in valores if v >= baixo and (alto is None or v <= alto)))
    return {"labels": [f[0] for f in FAIXAS_DE_CITACAO], "values": conta, "n": len(valores)}


def _caixa(db: Database) -> dict[str, Any]:
    """Dias ate a decisao, por decisao. Quartis, e nao media: uma revista
    que demora dois anos puxa a media inteira e some na mediana."""
    linhas = db.dicts(
        "SELECT decision, CAST(julianday(decision_on) - julianday(submitted_on) AS INTEGER) AS dias"
        "  FROM submissions WHERE submitted_on IS NOT NULL AND decision_on IS NOT NULL"
        "   AND decision IN ('aceito', 'rejeitado', 'desk_reject', 'revisao_solicitada')")
    grupos: dict[str, list[int]] = {}
    for l in linhas:
        if l["dias"] is not None and int(l["dias"]) >= 0:
            grupos.setdefault(l["decision"], []).append(int(l["dias"]))
    rotulo = {"aceito": "Aceito", "rejeitado": "Rejeitado após revisão",
              "desk_reject": "Recusa sem revisão", "revisao_solicitada": "Revisão solicitada"}
    return {"groups": [{"label": rotulo[d], "code": d, "values": sorted(v)}
                       for d, v in grupos.items() if len(v) >= 1]}


def _area(db: Database, ate: int) -> dict[str, Any]:
    """Publicacoes acumuladas por linha, ano a ano."""
    anos = list(range(ate - 7, ate + 1))
    linhas = db.dicts(
        "SELECT COALESCE(rl.name, 'Sem linha') AS linha, a.year_published AS ano, COUNT(*) AS n"
        "  FROM articles a LEFT JOIN research_lines rl ON rl.id = a.research_line_id"
        " WHERE a.status = 'publicado' AND a.year_published IS NOT NULL GROUP BY 1, 2")
    por_linha_: dict[str, Counter] = {}
    for l in linhas:
        por_linha_.setdefault(l["linha"], Counter())[int(l["ano"])] += int(l["n"])
    ordem = sorted(por_linha_, key=lambda n: -sum(por_linha_[n].values()))
    com_nome, outras = ordem[:LINHAS_COM_NOME], ordem[LINHAS_COM_NOME:]
    series = []
    for nome in com_nome:
        acumulado, valores = sum(v for a, v in por_linha_[nome].items() if a < anos[0]), []
        for a in anos:
            acumulado += por_linha_[nome].get(a, 0)
            valores.append(acumulado)
        series.append({"label": nome, "values": valores})
    if outras:
        junto: Counter = Counter()
        for nome in outras:
            junto.update(por_linha_[nome])
        acumulado, valores = sum(v for a, v in junto.items() if a < anos[0]), []
        for a in anos:
            acumulado += junto.get(a, 0)
            valores.append(acumulado)
        series.append({"label": f"Outras ({len(outras)})", "values": valores})
    return {"labels": [str(a) for a in anos], "series": series}


def _bullet(db: Database, ano: int) -> dict[str, Any]:
    """Realizado contra a meta do ano. Sem meta declarada, contra a media
    dos tres anos anteriores -- e o item diz qual dos dois e."""
    declaradas = metas.metas_declaradas(db, ano)
    items = []
    for code, rotulo, _ in metas.INDICADORES[:3]:
        feito = metas.realizado(db, code, ano)
        meta = declaradas.get(code)
        if meta is None:
            anteriores = [metas.realizado(db, code, a) for a in range(ano - 3, ano)]
            referencia = round(sum(anteriores) / 3.0, 1) if any(anteriores) else None
            items.append({"label": rotulo, "value": feito, "target": referencia,
                          "referencia": "média 3 anos" if referencia is not None else None,
                          "max": max(feito, referencia or 0, 1)})
        else:
            items.append({"label": rotulo, "value": feito, "target": meta,
                          "referencia": "meta declarada", "max": max(feito, meta, 1)})
    return {"ano": ano, "items": items}


def _tendencia(db: Database, hoje: date) -> dict[str, Any]:
    """Submissoes por mes nos ultimos 24 meses, com a media movel de tres.

    A media movel e CALCULADA daqui, e nao lida: e a serie bruta suavizada,
    e a legenda diz de quantos meses. Sem isso, "tendencia" e so uma
    segunda linha bonita.
    """
    meses = []
    ano, mes = hoje.year, hoje.month
    for _ in range(24):
        meses.append((ano, mes))
        mes -= 1
        if mes == 0:
            ano, mes = ano - 1, 12
    meses.reverse()
    linhas = db.dicts(
        f"SELECT {ANO_SQL.format(c='submitted_on')} AS ano, {MES_SQL.format(c='submitted_on')} AS mes,"
        "       COUNT(*) AS n FROM submissions WHERE submitted_on IS NOT NULL GROUP BY 1, 2")
    conta = {(int(l["ano"]), int(l["mes"])): int(l["n"]) for l in linhas if l["ano"]}
    bruto = [conta.get(m, 0) for m in meses]
    movel = [round(sum(bruto[max(0, i - 2):i + 1]) / min(3, i + 1), 2) for i in range(len(bruto))]
    return {"labels": [f"{MESES[m - 1]}/{str(a)[2:]}" for a, m in meses],
            "series": [{"label": "Submissões no mês", "values": bruto},
                       {"label": "Média móvel de 3 meses", "values": movel}]}


def _funil(db: Database) -> dict[str, Any]:
    """Do acervo inteiro: quantos foram submetidos, aceitos e publicados.

    E uma COORTE, e nao um retrato: quem esta publicado tambem foi
    submetido e aceito, e por isso cada degrau contem o de baixo. Uma
    porcentagem entre degraus so faz sentido assim.
    """
    total = int(db.scalar("SELECT COUNT(*) FROM articles WHERE status <> 'arquivado'") or 0)
    submetidos = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status <> 'arquivado' AND ("
        "  first_submission_on IS NOT NULL"
        "  OR status IN ('submetido', 'em_revisao', 'aceito', 'publicado', 'rejeitado')"
        "  OR id IN (SELECT article_id FROM submissions))") or 0)
    aceitos = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status <> 'arquivado' AND ("
        "  accepted_on IS NOT NULL OR status IN ('aceito', 'publicado'))") or 0)
    publicados = int(db.scalar("SELECT COUNT(*) FROM articles WHERE status = 'publicado'") or 0)
    return {"steps": [{"label": "Iniciados", "value": total},
                      {"label": "Submetidos", "value": submetidos},
                      {"label": "Aceitos", "value": aceitos},
                      {"label": "Publicados", "value": publicados}]}


def doze_olhares(db: Database, per: dict[str, Any], hoje: date,
                 linhas: dict[str, Any], evolucao_: dict[str, Any]) -> list[dict[str, Any]]:
    """Cada olhar responde uma pergunta escrita ao lado dele."""
    return [
        {"code": "calor", "tipo": "heatmap", "titulo": "Mapa de calor",
         "pergunta": "Em que meses o laboratório publica?",
         "nota": "só artigos com a data completa de publicação",
         "dados": _calor(db, per["ate"])},
        {"code": "cascata", "tipo": "waterfall", "titulo": "Cascata",
         "pergunta": "Que linhas explicam a diferença para o período anterior?",
         "dados": _cascata(db, per, linhas),
         "vazio": "sem período anterior para comparar" if not per["anterior"] else None},
        {"code": "linhas", "tipo": "lines", "titulo": "Série temporal",
         "pergunta": "Como a produção evoluiu no período?",
         "dados": evolucao_},
        {"code": "empilhadas", "tipo": "columns", "titulo": "Barras empilhadas",
         "pergunta": "De que é feito cada ano: publicado, em produção, recusado?",
         "dados": _empilhadas(db, per["ate"])},
        {"code": "rosca", "tipo": "donut", "titulo": "Rosca",
         "pergunta": "Que fatia de cada linha há no que foi publicado?",
         "dados": {"items": linhas["items"]}},
        {"code": "dispersao", "tipo": "scatter", "titulo": "Dispersão",
         "pergunta": "Artigo mais antigo é mais citado?",
         "dados": _dispersao(db, hoje)},
        {"code": "histograma", "tipo": "columns", "titulo": "Histograma",
         "pergunta": "Quantos artigos há em cada faixa de citação?",
         "dados": _histograma(db)},
        {"code": "caixa", "tipo": "distribution", "titulo": "Caixa (box plot)",
         "pergunta": "Quanto tempo a revista leva para decidir — e quanto isso varia?",
         "dados": _caixa(db)},
        {"code": "area", "tipo": "area", "titulo": "Área empilhada",
         "pergunta": "Como o acumulado de cada linha cresceu?",
         "dados": _area(db, per["ate"])},
        {"code": "bullet", "tipo": "bullet", "titulo": "Bullet",
         "pergunta": f"O ano de {per['ate']} está no ritmo da meta?",
         "dados": _bullet(db, per["ate"])},
        {"code": "tendencia", "tipo": "lines", "titulo": "Tendência",
         "pergunta": "Tirando o sobe-e-desce do mês, as submissões sobem ou descem?",
         "dados": _tendencia(db, hoje)},
        {"code": "funil", "tipo": "funnel", "titulo": "Funil",
         "pergunta": "De tudo o que foi começado, quanto chegou à publicação?",
         "dados": _funil(db)},
    ]


# ----------------------------------------------------------------------
# As leituras
# ----------------------------------------------------------------------
def _pct(v: float | None) -> str:
    if v is None:
        return ""
    sinal = "+" if v > 0 else ""
    return f"{sinal}{str(round(v, 1)).replace('.', ',')}%"


def leituras(db: Database, per: dict[str, Any], kpis: list[dict[str, Any]],
             linhas: dict[str, Any], evolucao_: dict[str, Any]) -> list[dict[str, Any]]:
    """Frases calculadas. Cada uma traz o numero e a regra de onde saiu.

    Nao ha modelo de linguagem aqui. Uma frase que nao possa ser refeita
    a partir do banco por quem ler a regra nao entra.
    """
    saida: list[dict[str, Any]] = []
    rotulo_do_periodo = (str(per["de"]) if per["de"] == per["ate"]
                         else f"{per['de']}–{per['ate']}")

    # 1. O indicador que mais mudou contra o periodo anterior.
    com_seta = [k for k in kpis if k["code"] != "citacoes" and k.get("pct") is not None]
    if com_seta:
        maior = max(com_seta, key=lambda k: abs(k["pct"]))
        ant = per["anterior"]
        rotulo_ant = str(ant[0]) if ant[0] == ant[1] else f"{ant[0]}–{ant[1]}"
        saida.append({
            "code": "maior_variacao", "valor": maior["pct"],
            "texto": (f"{maior['rotulo']}: {maior['valor']} em {rotulo_do_periodo} contra "
                      f"{maior['anterior']} em {rotulo_ant} ({_pct(maior['pct'])})"
                      + (f" — e {per['ate']} ainda tem {per['meses_restantes']} mês(es)."
                         if per["meses_restantes"] and per["ate"] >= int(per["hoje"][:4]) else ".")),
            "regra": "o indicador com a maior variação percentual entre os que têm anterior maior que zero",
        })

    # 2. A linha que mais cresceu em publicados.
    if per["anterior"] and linhas["items"]:
        antes = linhas["anterior"]
        agora = {i["label"]: i["value"] for i in linhas["items"]}
        nomes = set(antes) | set(agora)
        nome = max(nomes, key=lambda n: (agora.get(n, 0) - antes.get(n, 0), agora.get(n, 0)))
        diferenca = agora.get(nome, 0) - antes.get(nome, 0)
        if diferenca > 0:
            saida.append({
                "code": "linha_que_cresceu", "valor": diferenca,
                "texto": (f"A linha que mais cresceu foi {nome}: {agora.get(nome, 0)} "
                          f"publicado(s) contra {antes.get(nome, 0)} no período anterior "
                          f"(+{diferenca})."),
                "regra": "maior diferença de publicados por linha entre os dois períodos",
            })

    # 3. O mes mais forte, quando o periodo e de um ano e ha data completa.
    if evolucao_["grao"] == "mes":
        publicados = next(s for s in evolucao_["series"] if s["label"] == "Publicados")["values"]
        pico = max(publicados)
        if pico > 0:
            mes = publicados.index(pico)
            empatados = sum(1 for v in publicados if v == pico)
            saida.append({
                "code": "mes_mais_forte", "valor": pico,
                "texto": (f"{MESES_POR_EXTENSO[mes].capitalize()} foi o mês com mais "
                          f"publicações em {per['ate']}: {pico}"
                          + (f" (empatado com outros {empatados - 1})" if empatados > 1 else "")
                          + (f"; {evolucao_['sem_mes']} publicado(s) só têm o ano e ficaram fora "
                             "da conta por mês." if evolucao_["sem_mes"] else ".")),
                "regra": "o mês com mais `published_on` no ano; empate é dito",
            })

    # 4. A submissao mais antiga sem resposta.
    espera = db.dicts(
        "SELECT s.journal, a.title, CAST(julianday(?) - julianday(s.submitted_on) AS INTEGER) AS dias"
        "  FROM submissions s JOIN articles a ON a.id = s.article_id"
        " WHERE s.decision = 'em_avaliacao' AND s.submitted_on IS NOT NULL"
        " ORDER BY s.submitted_on LIMIT 1", (per["hoje"],))
    if espera and espera[0]["dias"] is not None and int(espera[0]["dias"]) > 0:
        e = espera[0]
        saida.append({
            "code": "espera_mais_longa", "valor": int(e["dias"]),
            "texto": (f"A submissão mais antiga sem resposta espera há {int(e['dias'])} dias"
                      f"{' na ' + e['journal'] if e['journal'] else ''}: "
                      f"“{str(e['title'])[:70]}”."),
            "regra": "a submissão em avaliação com o `submitted_on` mais antigo",
        })

    # 5. Citacoes que chegaram no periodo.
    cit = next(k for k in kpis if k["code"] == "citacoes")
    if cit.get("delta") is not None:
        saida.append({
            "code": "citacoes_no_periodo", "valor": cit["delta"],
            "texto": (f"Os artigos receberam {cit['delta']} citação(ões) desde 1º de janeiro de "
                      f"{per['de']}, de {cit['anterior']} para {cit['valor']}"
                      f"{' (' + _pct(cit['pct']) + ')' if cit['pct'] is not None else ''}."),
            "regra": "melhor base por artigo hoje, menos a melhor base no último instantâneo "
                     "antes do período",
        })

    # 6. Qualis A entre os publicados do periodo.
    total = _publicados(db, per["de"], per["ate"])
    if total:
        alto = int(db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
            "   AND year_published BETWEEN ? AND ?"
            "   AND UPPER(TRIM(COALESCE(qualis, ''))) IN ('A1','A2','A3','A4')",
            (per["de"], per["ate"])) or 0)
        saida.append({
            "code": "qualis_a", "valor": alto,
            "texto": (f"{alto} de {total} publicado(s) em {rotulo_do_periodo} estão em "
                      f"Qualis A ({round(100.0 * alto / total)}%)."),
            "regra": "publicados no período com Qualis A1 a A4",
        })
    return saida



# ----------------------------------------------------------------------
# Os acervos, as triagens e as bases: o Observatorio dentro do LAPE
# ----------------------------------------------------------------------
# Quantos segmentos aparecem com nome proprio no mapa de calor. O acervo
# de fibromialgia tem vinte e tantos; num mapa, doze linhas ja e o que se
# le sem rolar, e o resto continua na lista da biblioteca.
SEGMENTOS_NO_MAPA = 12

# Quantos anos a curva do acervo mostra. Antes disso ha registro esparso
# que so serve para achatar a escala.
ANOS_DO_ACERVO = 15


def _estado_da_base(buscas: int, rodadas: int, erros: int, manual: bool) -> str:
    """ok, erro, pronta (para colar) ou nunca rodada -- nesta ordem de gravidade.

    "Pronta" e o estado de uma base que o sistema nao alcanca sozinho: a
    estrategia esta guardada e espera alguem com o acesso. Nao e falha, e
    dizer "erro" mandaria consertar o que nao esta quebrado.
    """
    if erros:
        return "erro"
    if rodadas:
        return "ok"
    return "pronta" if manual else "nunca rodou"


def acervos(db: Database, quem: int | None = None,
            perfil: str = "leitura") -> list[dict[str, Any]]:
    """Cada acervo que esta pessoa pode ver, com o retrato que o Observatorio pede.

    Respeita o acervo restrito pela mesma regra da biblioteca: chamada sem
    `quem`, so os abertos. Uma tela nova que esquecesse o usuario mostraria
    acervo restrito a todo mundo, e esse descuido nao da erro nenhum.
    """
    saida = []
    for b in biblioteca.todas(db, quem, perfil):
        retrato = biblioteca.panorama(db, b["code"])
        bid = retrato["biblioteca"]["id"]
        por_base = db.dicts(
            "SELECT base, COUNT(*) AS buscas, SUM(COALESCE(achados, 0)) AS achados,"
            "       SUM(COALESCE(novos, 0)) AS novos, MAX(rodada_em) AS rodada_em,"
            "       SUM(CASE WHEN erro IS NOT NULL AND erro <> '' THEN 1 ELSE 0 END) AS erros,"
            "       SUM(CASE WHEN rodada_em IS NOT NULL THEN 1 ELSE 0 END) AS rodadas"
            "  FROM biblioteca_busca WHERE biblioteca_id = ? GROUP BY base ORDER BY base", (bid,))
        itens_por_base = {l["base"]: int(l["n"]) for l in db.dicts(
            "SELECT base, COUNT(*) AS n FROM biblioteca_item WHERE biblioteca_id = ?"
            " GROUP BY base", (bid,))}
        bases = []
        for l in por_base:
            manual = l["base"] in biblioteca.BASES_MANUAIS
            bases.append({
                "base": l["base"], "rotulo": biblioteca.ROTULO_BASE.get(l["base"], l["base"]),
                "itens": itens_por_base.get(l["base"], 0), "achados": int(l["achados"] or 0),
                "novos": int(l["novos"] or 0), "rodada_em": l["rodada_em"],
                "erros": int(l["erros"] or 0), "manual": manual,
                "estado": _estado_da_base(int(l["buscas"]), int(l["rodadas"] or 0),
                                          int(l["erros"] or 0), manual),
            })

        # O mapa segmento x base. Tres coisas diferentes numa celula, e as
        # tres precisam sair diferentes: um numero (achou), "erro" (a base
        # respondeu erro nesse segmento) e "lacuna" (a busca nunca rodou ali).
        segmentos = retrato["segmentos"][:SEGMENTOS_NO_MAPA]
        colunas = [x["base"] for x in bases if not x["manual"] or x["itens"]]
        celulas = {(l["segmento"], l["base"]): (l["rodada_em"], l["erro"]) for l in db.dicts(
            "SELECT segmento, base, rodada_em, erro FROM biblioteca_busca"
            " WHERE biblioteca_id = ? AND segmento IS NOT NULL", (bid,))}
        valores = []
        for seg in segmentos:
            linha = []
            for base in colunas:
                rodada, erro = celulas.get((seg["segmento"], base), (None, None))
                if erro:
                    linha.append("erro")
                elif not rodada:
                    linha.append(None)
                else:
                    linha.append(int(db.scalar(
                        "SELECT COUNT(*) FROM biblioteca_item WHERE biblioteca_id = ?"
                        "   AND base = ? AND ('; ' || segmento || '; ') LIKE ?",
                        (bid, base, f"%; {seg['segmento']}; %")) or 0))
            valores.append(linha)

        anos = [int(a["ano"]) for a in retrato["anos"]]
        ate = max(anos) if anos else date.today().year
        eixo = list(range(ate - ANOS_DO_ACERVO + 1, ate + 1))
        conta = {int(a["ano"]): int(a["n"]) for a in retrato["anos"]}
        saida.append({
            "code": b["code"], "title": b["title"], "descricao": b["descricao"],
            "linha": b["linha"], "eixo": b["eixo"], "restrita": bool(b["restrita"]),
            "dono": b["dono"], "atualizada_em": b["atualizada_em"],
            "total": retrato["total"], "sem_ano": retrato["sem_ano"],
            "livres": retrato["livres"], "com_doi": retrato["com_doi"],
            "segmentos": [{"segmento": x["segmento"], "n": x["n"], "erro": x["erro"],
                           "rodada_em": x["rodada_em"]} for x in retrato["segmentos"]],
            "bases": bases,
            "calor": {"rows": [x["segmento"] for x in segmentos],
                      "cols": [biblioteca.ROTULO_BASE.get(c, c) for c in colunas],
                      "values": valores},
            "anos": {"labels": [str(a) for a in eixo], "values": [conta.get(a, 0) for a in eixo],
                     "antes": sum(n for a, n in conta.items() if a < eixo[0])},
            "paises": retrato["paises"][:8],
        })
    return saida


def triagens(db: Database) -> list[dict[str, Any]]:
    """Cada revisao aberta, com o fluxograma contado do banco e a concordancia.

    O kappa e entre as DUAS pessoas que mais triaram: e o par que a revista
    vai perguntar. Com uma pessoa so nao ha kappa, e a tela diz isso em vez
    de mostrar 1,000.
    """
    saida = []
    for rev in db.dicts("SELECT id, code, title, tipo, reviewers_needed, blind, status"
                        "  FROM reviews ORDER BY id"):
        fluxo = revisao.prisma(db, rev["id"]) or {}
        decisoes = {l["decisao"]: int(l["n"]) for l in db.dicts(
            "SELECT COALESCE(decision, 'pendente') AS decisao, COUNT(*) AS n FROM refs"
            " WHERE review_id = ? AND duplicate_of IS NULL AND stage = 'titulo_resumo'"
            " GROUP BY 1", (rev["id"],))}
        equipe = [a for a in revisao.andamento(db, rev["id"]) if a["stage"] == "titulo_resumo"]
        kappa = None
        if len(equipe) >= 2:
            kappa = revisao.concordancia(db, rev["id"], equipe[0]["member_id"],
                                         equipe[1]["member_id"])
            kappa["entre"] = [equipe[0]["quem"], equipe[1]["quem"]]
        conferencia = padrao.conferir(db, rev["id"])
        tipo = padrao.tipo(rev["tipo"])
        saida.append({
            "code": rev["code"], "title": rev["title"], "tipo": tipo["rotulo"],
            "padrao": tipo["padrao"], "status": rev["status"],
            "avaliadores": int(rev["reviewers_needed"] or 1), "as_cegas": bool(rev["blind"]),
            "fluxo": {k: int(fluxo.get(k) or 0) for k in (
                "identificados", "registros", "duplicados", "triados", "pendentes",
                "excluidos_triagem", "texto_completo", "excluidos_texto", "incluidos")},
            "motivos": [{"motivo": m["motivo"], "n": int(m["n"])} for m in fluxo.get("motivos", [])],
            "por_base": [{"base": x["base"], "n": int(x["n"]), "duplicados": int(x["duplicados"] or 0)}
                         for x in fluxo.get("por_base", [])],
            "decisoes": {"incluir": decisoes.get("incluir", 0), "excluir": decisoes.get("excluir", 0),
                         "talvez": decisoes.get("talvez", 0), "pendente": decisoes.get("pendente", 0)},
            "equipe": [{"quem": a["quem"], "triadas": int(a["triadas"]),
                        "incluiu": int(a["incluiu"]), "excluiu": int(a["excluiu"])} for a in equipe],
            "kappa": kappa,
            "conferencia": conferencia["conta"],
        })
    return saida


def bases(db: Database, quem: int | None = None,
          perfil: str = "leitura") -> list[dict[str, Any]]:
    """Cada base, somada pelos acervos que esta pessoa ve: estado, ultima rodada, o que trouxe."""
    codes = [b["code"] for b in biblioteca.todas(db, quem, perfil)]
    if not codes:
        return []
    marcas = ",".join("?" for _ in codes)
    linhas = db.dicts(
        "SELECT s.base, COUNT(DISTINCT s.biblioteca_id) AS acervos, COUNT(*) AS buscas,"
        "       SUM(CASE WHEN s.rodada_em IS NOT NULL THEN 1 ELSE 0 END) AS rodadas,"
        "       SUM(CASE WHEN s.erro IS NOT NULL AND s.erro <> '' THEN 1 ELSE 0 END) AS erros,"
        "       SUM(COALESCE(s.achados, 0)) AS achados, MAX(s.rodada_em) AS ultima,"
        "       (SELECT COUNT(*) FROM biblioteca_item i JOIN biblioteca b2 ON b2.id = i.biblioteca_id"
        f"         WHERE i.base = s.base AND b2.code IN ({marcas})) AS itens,"
        "       (SELECT erro FROM biblioteca_busca e WHERE e.base = s.base AND e.erro IS NOT NULL"
        "         AND e.erro <> '' ORDER BY e.rodada_em DESC LIMIT 1) AS ultimo_erro"
        "  FROM biblioteca_busca s JOIN biblioteca b ON b.id = s.biblioteca_id"
        f" WHERE b.code IN ({marcas}) GROUP BY s.base ORDER BY itens DESC, s.base",
        (*codes, *codes))
    saida = []
    for l in linhas:
        manual = l["base"] in biblioteca.BASES_MANUAIS
        saida.append({
            "base": l["base"], "rotulo": biblioteca.ROTULO_BASE.get(l["base"], l["base"]),
            "acervos": int(l["acervos"]), "buscas": int(l["buscas"]), "rodadas": int(l["rodadas"] or 0),
            "erros": int(l["erros"] or 0), "achados": int(l["achados"] or 0), "itens": int(l["itens"] or 0),
            "ultima": l["ultima"], "ultimo_erro": l["ultimo_erro"], "manual": manual,
            "estado": _estado_da_base(int(l["buscas"]), int(l["rodadas"] or 0),
                                      int(l["erros"] or 0), manual),
            "nota": biblioteca.PORQUE_MANUAL.get(l["base"]) if manual else None,
        })
    return saida


# ----------------------------------------------------------------------
# Tudo junto
# ----------------------------------------------------------------------
# ----------------------------------------------------------------------
# Temas: os indicadores tematicos e os graficos que faltavam
# ----------------------------------------------------------------------
# Cada KPI aqui e uma pergunta que o laboratorio faz de si e que os
# quatro numeros do painel nao respondem: quanto tempo leva, quanto e
# aceito, quanto e aberto, com quem se publica, o que se publica.
EIXOS_DO_RADAR = ("Publicado", "Acesso aberto", "Com DOI", "Citado", "Internacional")
ANOS_DO_BUMP = 5
REVISTAS_NO_TREEMAP = 12
TIPOS_NO_SANKEY = 6


def _mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    v = sorted(valores)
    n = len(v)
    return float(v[n // 2]) if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2.0


def _paises_por_artigo(db: Database) -> dict[int, set[str]]:
    """O pais de quem assina, por artigo -- cadastro e afiliacao juntos."""
    saida: dict[int, set[str]] = {}
    for l in db.dicts(
            "SELECT DISTINCT aa.article_id, i.country FROM article_authors aa"
            "  JOIN members m ON m.id = aa.member_id"
            "  JOIN institutions i ON i.id = m.institution_id WHERE i.country IS NOT NULL"):
        saida.setdefault(int(l["article_id"]), set()).add(l["country"])
    for l in db.dicts("SELECT article_id, country FROM article_countries"):
        saida.setdefault(int(l["article_id"]), set()).add(l["country"])
    return saida


def _e_internacional(paises: set[str]) -> bool:
    from .util import norm_key
    return any(norm_key(p) not in ("brasil", "brazil") for p in paises)


def temas(db: Database, per: dict[str, Any], hoje: date) -> dict[str, Any]:
    de, ate = per["de"], per["ate"]
    publicados = db.dicts(
        "SELECT id, journal, study_type, open_access, doi, days_start_to_publication,"
        "       COALESCE(wos_citations, 0) AS wos, COALESCE(scopus_citations, 0) AS scopus,"
        "       COALESCE(openalex_citations, 0) AS openalex"
        "  FROM v_articles_full WHERE status = 'publicado' AND year_published BETWEEN ? AND ?",
        (de, ate))
    n_pub = len(publicados)
    paises = _paises_por_artigo(db)

    def pct(parte: int, todo: int) -> float | None:
        return None if not todo else round(100.0 * parte / todo, 1)

    dias = [float(a["days_start_to_publication"]) for a in publicados
            if a["days_start_to_publication"] is not None and float(a["days_start_to_publication"]) >= 0]
    decididas = db.dicts(
        f"SELECT decision, COUNT(*) AS n FROM submissions WHERE decision IN ('aceito', 'rejeitado', 'desk_reject')"
        f"   AND decision_on IS NOT NULL AND {ANO_SQL.format(c='decision_on')} BETWEEN ? AND ? GROUP BY 1", (de, ate))
    aceites = sum(int(d["n"]) for d in decididas if d["decision"] == "aceito")
    n_decididas = sum(int(d["n"]) for d in decididas)
    abertos = sum(1 for a in publicados if a["open_access"])
    internacionais = sum(1 for a in publicados if _e_internacional(paises.get(int(a["id"]), set())))
    tipos = Counter(a["study_type"] for a in publicados if a["study_type"])
    tipo, n_tipo = (tipos.most_common(1)[0] if tipos else (None, 0))
    revistas = {a["journal"] for a in publicados if a["journal"]}
    paises_do_periodo = set()
    for a in publicados:
        paises_do_periodo |= paises.get(int(a["id"]), set())
    orientandos = metas.realizado(db, "orientandos_publicando", ate)

    kpis = [
        {"code": "tempo", "rotulo": "Do início à publicação", "icon": "relogio", "tom": "cyan",
         "valor": None if not dias else round(_mediana(dias)), "unidade": "dias (mediana)",
         "pe": f"{len(dias)} artigo(s) com as duas datas" if dias else "nenhum artigo com data de início e de publicação"},
        {"code": "aceite", "rotulo": "Taxa de aceite", "icon": "aceite", "tom": "green",
         "valor": pct(aceites, n_decididas), "unidade": "%", "n_decididas": n_decididas,
         "pe": f"{aceites} aceite(s) em {n_decididas} decisão(ões)" if n_decididas else "nenhuma decisão de revista no período"},
        {"code": "acesso_aberto", "rotulo": "Acesso aberto", "icon": "livro", "tom": "yellow",
         "valor": pct(abertos, n_pub), "unidade": "%",
         "pe": f"{abertos} de {n_pub} publicado(s)" if n_pub else "nenhum publicado no período"},
        {"code": "internacional", "rotulo": "Colaboração internacional", "icon": "mapa", "tom": "purple",
         "valor": pct(internacionais, n_pub), "unidade": "%",
         "pe": f"{internacionais} artigo(s) com autor fora do Brasil" if n_pub else "nenhum publicado no período"},
        {"code": "tipo", "rotulo": "Desenho mais frequente", "icon": "experimento", "tom": "orange",
         "valor": tipo or "—", "unidade": "",
         "pe": f"{n_tipo} de {n_pub} publicado(s)" if tipo else "nenhum publicado com tipo de estudo"},
        {"code": "orientandos", "rotulo": "Orientandos publicando", "icon": "orientacao", "tom": "magenta",
         "valor": int(orientandos or 0), "unidade": "pessoas em " + str(ate),
         "pe": "orientandos com ao menos um artigo publicado no ano"},
        {"code": "revistas", "rotulo": "Revistas distintas", "icon": "citacao", "tom": "blue",
         "valor": len(revistas), "unidade": "revistas", "pe": f"{n_pub} publicado(s) no período"},
        {"code": "paises", "rotulo": "Países que assinam", "icon": "espaco", "tom": "cyan",
         "valor": len(paises_do_periodo), "unidade": "países",
         "pe": ", ".join(sorted(paises_do_periodo)[:4]) + (" …" if len(paises_do_periodo) > 4 else "") if paises_do_periodo else "sem país cadastrado nos autores"},
    ]

    # radar: as linhas mais produtivas, cada eixo em % dos artigos da linha
    linhas = db.dicts(
        "SELECT rl.id, rl.name, rl.code, COUNT(a.id) AS n FROM research_lines rl"
        "  JOIN articles a ON a.research_line_id = rl.id"
        " WHERE COALESCE(rl.active, 1) = 1 GROUP BY rl.id ORDER BY n DESC, rl.name LIMIT 4")
    series_radar = []
    for l in linhas:
        arts = db.dicts(
            "SELECT id, status, open_access, doi, COALESCE(wos_citations,0) AS wos,"
            "       COALESCE(scopus_citations,0) AS scopus, COALESCE(openalex_citations,0) AS openalex"
            "  FROM articles WHERE research_line_id = ?", (l["id"],))
        n = len(arts) or 1
        series_radar.append({"label": l["name"], "icone": linhas_vocab.icone_de(l["code"], l["name"]), "values": [
            round(100.0 * sum(1 for a in arts if a["status"] == "publicado") / n, 1),
            round(100.0 * sum(1 for a in arts if a["open_access"]) / n, 1),
            round(100.0 * sum(1 for a in arts if a["doi"]) / n, 1),
            round(100.0 * sum(1 for a in arts if max(a["wos"], a["scopus"], a["openalex"]) > 0) / n, 1),
            round(100.0 * sum(1 for a in arts if _e_internacional(paises.get(int(a["id"]), set()))) / n, 1),
        ]})

    # dumbbell: cada linha, do periodo anterior para este
    anterior = per.get("anterior")
    haltere = []
    if anterior:
        agora = {l["name"]: int(l["n"]) for l in db.dicts(
            "SELECT rl.name, COUNT(*) AS n FROM articles a JOIN research_lines rl ON rl.id = a.research_line_id"
            " WHERE a.status = 'publicado' AND a.year_published BETWEEN ? AND ? GROUP BY rl.id", (de, ate))}
        antes = {l["name"]: int(l["n"]) for l in db.dicts(
            "SELECT rl.name, COUNT(*) AS n FROM articles a JOIN research_lines rl ON rl.id = a.research_line_id"
            " WHERE a.status = 'publicado' AND a.year_published BETWEEN ? AND ? GROUP BY rl.id",
            (anterior[0], anterior[1]))}
        for nome in sorted(set(agora) | set(antes), key=lambda k: -(agora.get(k, 0) + antes.get(k, 0))):
            haltere.append({"label": nome, "from": antes.get(nome, 0), "to": agora.get(nome, 0)})

    # bump: a posicao de cada linha, ano a ano
    anos = list(range(ate - ANOS_DO_BUMP + 1, ate + 1))
    por_ano = db.dicts(
        "SELECT rl.name, a.year_published AS ano, COUNT(*) AS n FROM articles a"
        "  JOIN research_lines rl ON rl.id = a.research_line_id"
        " WHERE a.status = 'publicado' AND a.year_published BETWEEN ? AND ? GROUP BY rl.id, ano",
        (anos[0], anos[-1]))
    tabela: dict[str, dict[int, int]] = {}
    for l in por_ano:
        tabela.setdefault(l["name"], {})[int(l["ano"])] = int(l["n"])
    bump_series = []
    for nome in tabela:
        bump_series.append({"label": nome, "values": []})
    for ano in anos:
        ordem = sorted(tabela, key=lambda k: (-tabela[k].get(ano, 0), k))
        posicao = {nome: i + 1 for i, nome in enumerate(ordem) if tabela[nome].get(ano, 0)}
        for s in bump_series:
            s["values"].append(posicao.get(s["label"]))
    bump_series.sort(key=lambda s: -sum(tabela[s["label"]].values()))

    # sankey: desenho do estudo -> situacao de hoje
    fluxo = db.dicts(
        "SELECT COALESCE(NULLIF(TRIM(study_type), ''), 'sem tipo') AS tipo, status, COUNT(*) AS n"
        "  FROM articles WHERE status IS NOT NULL GROUP BY 1, 2")
    por_tipo = Counter()
    for l in fluxo:
        por_tipo[l["tipo"]] += int(l["n"])
    principais = [t for t, _ in por_tipo.most_common(TIPOS_NO_SANKEY)]
    nos, ligacoes = [], []
    rotulo_status = ROTULO_DA_SITUACAO
    situacoes = []
    for l in fluxo:
        tipo = l["tipo"] if l["tipo"] in principais else "outros"
        if l["status"] not in situacoes:
            situacoes.append(l["status"])
        ligacoes.append({"source": "t:" + tipo, "target": "s:" + l["status"], "value": int(l["n"])})
    junta: dict[tuple[str, str], int] = {}
    for lig in ligacoes:
        junta[(lig["source"], lig["target"])] = junta.get((lig["source"], lig["target"]), 0) + lig["value"]
    ligacoes = [{"source": a, "target": b, "value": v} for (a, b), v in junta.items()]
    for t in principais + (["outros"] if any(k[0] == "t:outros" for k in junta) else []):
        nos.append({"id": "t:" + t, "label": t, "depth": 0})
    for st in situacoes:
        nos.append({"id": "s:" + st, "label": rotulo_status.get(st, st.replace("_", " ")), "depth": 1})

    # treemap: onde se publica
    revistas_n = db.dicts(
        "SELECT journal, COUNT(*) AS n FROM articles WHERE status = 'publicado'"
        "   AND journal IS NOT NULL AND TRIM(journal) <> '' GROUP BY journal ORDER BY n DESC")
    treemap = [{"label": r["journal"], "value": int(r["n"])} for r in revistas_n[:REVISTAS_NO_TREEMAP]]
    resto = sum(int(r["n"]) for r in revistas_n[REVISTAS_NO_TREEMAP:])
    if resto:
        treemap.append({"label": f"outras {len(revistas_n) - REVISTAS_NO_TREEMAP} revistas", "value": resto})

    # calendario: cada dia em que algo aconteceu no ano
    dias_do_ano: Counter = Counter()
    for sql in (
        "SELECT substr(published_on, 1, 10) AS d FROM articles WHERE status = 'publicado' AND length(published_on) >= 10",
        "SELECT substr(submitted_on, 1, 10) AS d FROM submissions WHERE length(submitted_on) >= 10",
        "SELECT substr(accepted_on, 1, 10) AS d FROM articles WHERE length(accepted_on) >= 10",
        "SELECT substr(decided_at, 1, 10) AS d FROM screenings WHERE length(decided_at) >= 10",
        "SELECT substr(start_at, 1, 10) AS d FROM events WHERE length(start_at) >= 10",
    ):
        for l in db.dicts(sql):
            if l["d"] and l["d"].startswith(str(ate)):
                dias_do_ano[l["d"]] += 1

    return {
        "kpis": kpis,
        "radar": {"axes": list(EIXOS_DO_RADAR), "series": series_radar},
        "haltere": haltere,
        "bump": {"labels": [str(a) for a in anos], "series": bump_series},
        "sankey": {"nodes": nos, "links": ligacoes},
        "treemap": treemap,
        "calendario": {"year": ate, "days": dict(dias_do_ano), "total": sum(dias_do_ano.values())},
    }


# ----------------------------------------------------------------------
# Mundo: de onde vem a producao, para o globo que gira
# ----------------------------------------------------------------------
SEDE = {"nome": "UDESC / CEFID", "cidade": "Florianópolis", "pais": "Brasil",
        "latitude": -27.5949, "longitude": -48.5482}


def mundo(db: Database) -> dict[str, Any]:
    from . import analise

    p = analise.paises(db)
    paises = []
    sem_coordenada = []
    for item in p.get("todos", []):
        if item["latitude"] is None or item["longitude"] is None:
            sem_coordenada.append(item["pais"])
            continue
        paises.append({"pais": item["pais"], "iso": item.get("iso"), "n": int(item["n"]),
                       "latitude": float(item["latitude"]), "longitude": float(item["longitude"]),
                       "instituicoes": list(item.get("instituicoes") or [])[:5]})
    instituicoes = db.dicts(
        "SELECT i.name, i.acronym, i.city, i.country, i.latitude, i.longitude,"
        "       (SELECT COUNT(*) FROM members m WHERE m.institution_id = i.id) AS pessoas"
        "  FROM institutions i WHERE i.latitude IS NOT NULL AND i.longitude IS NOT NULL"
        " ORDER BY pessoas DESC, i.name")
    sede = dict(SEDE)
    for i in instituicoes:
        if (i["acronym"] or "").upper().startswith("UDESC") or "estado de santa catarina" in (i["name"] or "").lower():
            sede.update({"nome": i["acronym"] or i["name"], "cidade": i["city"] or sede["cidade"],
                         "latitude": float(i["latitude"]), "longitude": float(i["longitude"])})
            break
    artigos_com_pais = len(_paises_por_artigo(db))
    return {"sede": sede, "paises": paises, "sem_coordenada": sem_coordenada,
            "instituicoes": [{"nome": i["name"], "sigla": i["acronym"], "cidade": i["city"], "pais": i["country"],
                              "latitude": float(i["latitude"]), "longitude": float(i["longitude"]),
                              "pessoas": int(i["pessoas"] or 0)} for i in instituicoes],
            "artigos_com_pais": artigos_com_pais}


# ----------------------------------------------------------------------
# Buscar: um campo, tudo o que o laboratorio tem com aquele nome
# ----------------------------------------------------------------------
POR_GRUPO = 8


def buscar(db: Database, q: str, quem: int | None = None, perfil: str = "leitura") -> dict[str, Any]:
    """Artigos, pessoas, projetos, linhas, acervos e temas com o termo.

    A comparacao ignora caixa e acento dos dois lados: "motivacao" acha
    "Motivação". O LIKE do SQLite so ignora caixa em ASCII, entao a
    filtragem e feita aqui, em Python, sobre as tabelas -- que sao
    pequenas: o maior e o de artigos, na casa das centenas.
    """
    from .util import norm_key

    termo = norm_key(q or "")
    saida: dict[str, Any] = {"q": q or "", "artigos": [], "pessoas": [], "projetos": [],
                             "linhas": [], "acervos": [], "temas": [], "total": 0}
    if len(termo) < 2:
        return saida

    def bate(*campos: Any) -> bool:
        return any(termo in norm_key(c) for c in campos if c)

    for a in db.dicts(
            "SELECT id, title, year_published, status, journal, research_line, study_type, authors"
            "  FROM v_articles_full ORDER BY COALESCE(year_published, 0) DESC, title"):
        if bate(a["title"], a["journal"], a["authors"], a["study_type"]):
            saida["artigos"].append({"id": a["id"], "titulo": a["title"], "ano": a["year_published"],
                                     "situacao": a["status"], "revista": a["journal"], "linha": a["research_line"]})
    for m in db.dicts("SELECT id, full_name, short_name, role FROM members WHERE COALESCE(active, 1) = 1"
                      " ORDER BY full_name"):
        if bate(m["full_name"], m["short_name"]):
            saida["pessoas"].append({"id": m["id"], "nome": m["full_name"], "papel": m["role"]})
    for pr in db.dicts("SELECT id, name, status FROM projects ORDER BY name"):
        if bate(pr["name"]):
            saida["projetos"].append({"id": pr["id"], "nome": pr["name"], "situacao": pr["status"]})
    for l in db.dicts(
            "SELECT rl.id, rl.name, rl.code, rl.keywords,"
            "       (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id) AS n"
            "  FROM research_lines rl WHERE COALESCE(rl.active, 1) = 1 ORDER BY rl.name"):
        if bate(l["name"], l["keywords"]):
            saida["linhas"].append({"id": l["id"], "nome": l["name"], "code": l["code"], "n": int(l["n"] or 0),
                                    "icone": linhas_vocab.icone_de(l["code"], l["name"])})
    visiveis = biblioteca.todas(db, quem, perfil)
    for b in visiveis:
        if bate(b["title"], b["descricao"], b["linha"]):
            saida["acervos"].append({"code": b["code"], "titulo": b["title"], "n": int(b["n"] or 0), "linha": b["linha"]})
    # temas: os segmentos dos acervos visiveis e os tipos de estudo
    codigos = {b["code"] for b in visiveis}
    vistos = set()
    for seg in db.dicts(
            "SELECT DISTINCT b.code, b.title, bb.segmento FROM biblioteca_busca bb"
            "  JOIN biblioteca b ON b.id = bb.biblioteca_id WHERE bb.segmento IS NOT NULL ORDER BY bb.segmento"):
        if seg["code"] in codigos and bate(seg["segmento"]) and (seg["code"], seg["segmento"]) not in vistos:
            vistos.add((seg["code"], seg["segmento"]))
            saida["temas"].append({"tema": seg["segmento"], "acervo": seg["code"], "acervo_titulo": seg["title"], "tipo": "segmento"})
    for t in db.dicts("SELECT study_type AS t, COUNT(*) AS n FROM articles WHERE study_type IS NOT NULL"
                      " GROUP BY 1 ORDER BY n DESC"):
        if bate(t["t"]):
            saida["temas"].append({"tema": t["t"], "n": int(t["n"]), "tipo": "tipo de estudo"})
    for grupo in ("artigos", "pessoas", "projetos", "linhas", "acervos", "temas"):
        saida["total"] += len(saida[grupo])
        saida[grupo] = saida[grupo][:POR_GRUPO]
    return saida


def _noticias(db: Database, hoje: date) -> dict[str, Any]:
    """As últimas notícias, para a faixa que corre no modo TV."""
    from . import tv

    return tv.noticias(db, hoje)


def montar(db: Database, periodo_code: str | None = None,
           hoje: date | None = None, quem: int | None = None,
           perfil: str = "leitura") -> dict[str, Any]:
    hoje = hoje or date.today()
    per = periodo(db, periodo_code, hoje)
    kpis = indicadores(db, per)
    linhas = por_linha(db, per)
    evolucao_ = evolucao(db, per)
    return {
        "periodo": per,
        "periodos": [{"code": p["code"], "rotulo": p["rotulo"]} for p in PERIODOS],
        "kpis": kpis,
        "evolucao": evolucao_,
        "por_linha": linhas,
        "por_situacao": por_situacao(db),
        "caminho": caminho(db),
        "doze": doze_olhares(db, per, hoje, linhas, evolucao_),
        "leituras": leituras(db, per, kpis, linhas, evolucao_),
        "acervos": acervos(db, quem, perfil),
        "triagens": triagens(db),
        "bases": bases(db, quem, perfil),
        "temas": temas(db, per, hoje),
        "mundo": mundo(db),
        "sinais": sinais.analisar(db, hoje),
        "noticias": _noticias(db, hoje),
        "aviso": ("As leituras são calculadas a partir do banco, e cada uma diz a regra "
                  "de onde saiu. Não há modelo de linguagem aqui: o que não pode ser "
                  "refeito a partir dos dados não entra."),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
