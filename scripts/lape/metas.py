"""As metas do ano, o ritmo e a projecao de fim de ano.

O painel sabia contar o que ja aconteceu e nao sabia dizer se o
laboratorio vai chegar aonde quer. E um numero sozinho nao se interpreta:
13 publicacoes e muito ou pouco dependendo de quanto se pretendia, e de
como costumam ser os meses que faltam.

Tres coisas separadas, e a separacao e o ponto:

  o REALIZADO  e dado -- esta no banco, foi contado.
  a META       e decisao -- a coordenacao declara, o sistema nao sugere.
  a PROJECAO   e palpite -- e tem de ser apresentada como tal.

Projetar o fim do ano dividindo o que saiu pela fracao do ano que passou
supoe que o ano e uniforme, e ele nao e: aceite e publicacao andam em
lote, e dezembro nao se parece com fevereiro. Quando o laboratorio tem
historico com mes, da para perguntar ao proprio historico que fatia do
ano costuma estar pronta ate este mes, e projetar por ai -- com a faixa
que os anos anteriores desenharam. Quando nao tem, sobra a regra linear,
e a tela e obrigada a dizer que e ela.

A projecao nunca vira um numero unico na tela. Um numero unico convida a
ser lido como previsao, e o que existe aqui e uma faixa.
"""
from __future__ import annotations

from datetime import date
from typing import Any

from .db import Database

# Quantos anos completos e quantos trabalhos por ano o historico precisa
# ter para valer como base de sazonalidade. Abaixo disso a "fatia tipica
# do ano" seria desenhada por dois ou tres acasos.
ANOS_MINIMOS = 3
POR_ANO_MINIMO = 4

# (codigo, rotulo, o que conta, ajuda)
INDICADORES: tuple[tuple[str, str, str], ...] = (
    ("publicacoes", "Publicações",
     "artigos publicados no ano"),
    ("submissoes", "Submissões",
     "tentativas de submissão registradas no ano"),
    ("aceites", "Aceites",
     "artigos aceitos no ano, ainda que publiquem no ano seguinte"),
    ("qualis_alto", "Publicações em Qualis A",
     "publicados no ano com Qualis A1, A2, A3 ou A4"),
    ("orientandos_publicando", "Orientandos com publicação",
     "orientandos que assinaram ao menos um artigo publicado no ano"),
)
ROTULOS = {codigo: rotulo for codigo, rotulo, _ in INDICADORES}


def _ano_de(coluna: str) -> str:
    return f"CAST(strftime('%Y', {coluna}) AS INTEGER)"


CONTAGEM: dict[str, str] = {
    # Publicado usa `year_published`, que e o campo que o laboratorio
    # preenche; `published_on` nem sempre existe.
    "publicacoes":
        "SELECT COUNT(*) FROM articles"
        " WHERE status = 'publicado' AND year_published = ?",
    "submissoes":
        "SELECT COUNT(*) FROM submissions"
        f" WHERE submitted_on IS NOT NULL AND {_ano_de('submitted_on')} = ?",
    "aceites":
        "SELECT COUNT(*) FROM articles"
        f" WHERE accepted_on IS NOT NULL AND {_ano_de('accepted_on')} = ?",
    "qualis_alto":
        "SELECT COUNT(*) FROM articles"
        " WHERE status = 'publicado' AND year_published = ?"
        "   AND UPPER(TRIM(COALESCE(qualis, ''))) IN ('A1','A2','A3','A4')",
    "orientandos_publicando":
        "SELECT COUNT(DISTINCT m.id) FROM members m"
        "  JOIN article_authors aa ON aa.member_id = m.id"
        "  JOIN articles a ON a.id = aa.article_id"
        " WHERE m.advisor_id IS NOT NULL AND COALESCE(m.is_external, 0) = 0"
        "   AND a.status = 'publicado' AND a.year_published = ?",
}

# A data que diz QUANDO cada coisa aconteceu, para medir sazonalidade.
# Sem ela so se sabe o ano, e o ano inteiro nao tem meses.
DATA_DO_FATO: dict[str, tuple[str, str, str]] = {
    # codigo -> (tabela, coluna de data, filtro extra)
    "publicacoes": ("articles", "published_on", "status = 'publicado'"),
    "submissoes": ("submissions", "submitted_on", "1 = 1"),
    "aceites": ("articles", "accepted_on", "1 = 1"),
    "qualis_alto": ("articles", "published_on",
                    "status = 'publicado'"
                    " AND UPPER(TRIM(COALESCE(qualis, ''))) IN ('A1','A2','A3','A4')"),
}


def realizado(db: Database, codigo: str, ano: int) -> int:
    sql = CONTAGEM.get(codigo)
    if not sql:
        return 0
    return int(db.scalar(sql, (ano,)) or 0)


def _mediana(valores: list[float]) -> float | None:
    dados = sorted(v for v in valores if v is not None)
    if not dados:
        return None
    meio = len(dados) // 2
    return dados[meio] if len(dados) % 2 else (dados[meio - 1] + dados[meio]) / 2


def fatia_tipica(db: Database, codigo: str, mes: int, ano_corrente: int
                 ) -> dict[str, Any] | None:
    """Que fatia do ano costuma estar pronta ate o fim deste mes.

    Sai do historico do proprio laboratorio, e nao de uma suposicao sobre
    como um ano deveria se distribuir. Devolve a mediana e a faixa entre o
    ano mais lento e o mais adiantado -- e e essa faixa que vira o
    intervalo da projecao, em vez de um numero unico.

    Devolve None quando nao ha base: poucos anos completos, poucos
    trabalhos por ano, ou datas sem mes. Nesse caso quem chama cai na
    regra linear, e a tela diz qual das duas usou.
    """
    fonte = DATA_DO_FATO.get(codigo)
    if not fonte:
        return None
    tabela, coluna, filtro = fonte
    linhas = db.dicts(
        f"SELECT CAST(strftime('%Y', {coluna}) AS INTEGER) AS ano,"
        f"       CAST(strftime('%m', {coluna}) AS INTEGER) AS mes"
        f"  FROM {tabela}"
        f" WHERE {coluna} IS NOT NULL AND LENGTH({coluna}) >= 7 AND ({filtro})")
    por_ano: dict[int, list[int]] = {}
    for linha in linhas:
        if linha["ano"] is None or linha["mes"] is None:
            continue
        if linha["ano"] >= ano_corrente:      # o ano corrente ainda esta acontecendo
            continue
        por_ano.setdefault(int(linha["ano"]), []).append(int(linha["mes"]))

    fatias = []
    for _ano, meses in sorted(por_ano.items()):
        if len(meses) < POR_ANO_MINIMO:
            continue
        ate = sum(1 for m in meses if m <= mes)
        fatias.append(ate / len(meses))
    fatias = [f for f in fatias if f > 0]
    if len(fatias) < ANOS_MINIMOS:
        return None
    return {"mediana": _mediana(fatias), "minima": min(fatias), "maxima": max(fatias),
            "anos": len(fatias)}


def _fracao_do_ano_decorrida(hoje: date) -> float:
    primeiro = date(hoje.year, 1, 1)
    ultimo = date(hoje.year, 12, 31)
    return ((hoje - primeiro).days + 1) / ((ultimo - primeiro).days + 1)


def projetar(db: Database, codigo: str, ano: int, feito: int,
             hoje: date | None = None) -> dict[str, Any]:
    """O fim do ano como faixa, dizendo de onde a faixa veio."""
    hoje = hoje or date.today()
    if ano != hoje.year:
        # ano fechado (ou futuro): nao se projeta o que ja aconteceu
        return {"metodo": "fechado", "de": feito, "ate": feito, "central": feito}

    tipica = fatia_tipica(db, codigo, hoje.month, ano)
    if tipica and tipica["mediana"]:
        central = feito / tipica["mediana"]
        # o ano mais adiantado do historico projeta o total mais baixo,
        # porque nele esta fatia ja representava quase tudo
        de = feito / tipica["maxima"]
        ate = feito / tipica["minima"]
        # E a faixa nunca fecha em zero. Um historico regular faz a fatia
        # minima e a maxima coincidirem, e a projecao sairia como um numero
        # unico -- que se le como certeza sobre um ano que ainda nao
        # terminou. O que falta acontecer tem a incerteza de uma contagem,
        # e ela entra aqui mesmo quando o historico e uniforme.
        de, ate = _com_folga_de_contagem(feito, central, de, ate)
        return {
            "metodo": "sazonal",
            "anos_de_base": tipica["anos"],
            "central": round(central),
            "de": de, "ate": ate,
            "fatia": round(tipica["mediana"], 3),
        }

    decorrido = _fracao_do_ano_decorrida(hoje)
    if decorrido <= 0:
        return {"metodo": "linear", "central": feito, "de": feito, "ate": feito,
                "fatia": round(decorrido, 3)}
    if feito == 0:
        # De zero eventos nao se estima taxa: dividir zero pelo tempo
        # decorrido devolve zero, e a tela passava a afirmar que o ano
        # termina em zero -- em setembro, com tres meses pela frente. O
        # teto aqui e a regra de tres: nenhum evento em T diz que a taxa
        # esta abaixo de 3/T com 95% de confianca, e e isso que ainda cabe
        # no que resta do ano.
        resta = 1 - decorrido
        return {"metodo": "linear", "central": 0, "de": 0,
                "ate": max(0, round(3 * resta / decorrido)),
                "fatia": round(decorrido, 3)}
    central = feito / decorrido
    de, ate = _com_folga_de_contagem(feito, central, central, central)
    return {
        "metodo": "linear",
        "central": round(central),
        "de": de, "ate": ate,
        "fatia": round(decorrido, 3),
    }


def _com_folga_de_contagem(feito: int, central: float, de: float, ate: float
                           ) -> tuple[int, int]:
    """Alarga a faixa pela incerteza do que ainda falta acontecer.

    Publicacao e contagem de eventos: a incerteza do que falta cresce com
    a raiz do que falta, e nao proporcionalmente. Sem esta folga um
    historico regular devolveria faixa de largura zero -- e faixa de
    largura zero e uma afirmacao de certeza sobre um ano que ainda nao
    acabou. O piso e sempre o que ja saiu: o ano nao anda para tras.
    """
    restante = max(0.0, central - feito)
    folga = 1.96 * (restante ** 0.5)
    return (max(feito, round(min(de, central - folga))),
            max(feito, round(max(ate, central + folga))))


def _veredito(meta: int | None, feito: int, projecao: dict[str, Any]) -> str:
    """O que dizer, sem dizer mais do que se sabe."""
    if not meta:
        return "sem meta declarada"
    if feito >= meta:
        return "alcançada"
    if projecao["metodo"] == "fechado" or projecao["ate"] <= feito:
        # nao ha mais ano para acontecer: "no ritmo atual" nao cabe
        return "não alcançada"
    if meta <= projecao["de"]:
        return "no ritmo atual, alcança"
    if meta > projecao["ate"]:
        return "no ritmo atual, não alcança"
    return "depende do fim do ano"


def metas_declaradas(db: Database, ano: int) -> dict[str, int]:
    return {r["code"]: int(r["target"])
            for r in db.dicts("SELECT code, target FROM goals WHERE year = ?", (ano,))}


def declarar(db: Database, ano: int, codigo: str, alvo: int | None,
             por: str | None = None) -> dict[str, Any]:
    """Grava (ou apaga) a meta de um indicador no ano."""
    if codigo not in ROTULOS:
        raise ValueError(f"indicador desconhecido: {codigo}")
    if alvo is None:
        db.execute("DELETE FROM goals WHERE year = ? AND code = ?", (ano, codigo))
        db.conn.commit()
        return {"ano": ano, "codigo": codigo, "meta": None}
    alvo = int(alvo)
    if alvo < 0:
        raise ValueError("a meta não pode ser negativa")
    if alvo > 1000:
        raise ValueError("meta acima de 1000: confira o número digitado")
    db.execute(
        "INSERT INTO goals (year, code, target, set_by) VALUES (?, ?, ?, ?)"
        " ON CONFLICT(year, code) DO UPDATE SET target = excluded.target,"
        "   set_on = datetime('now'), set_by = excluded.set_by",
        (ano, codigo, alvo, por))
    db.conn.commit()
    return {"ano": ano, "codigo": codigo, "meta": alvo}


def progresso(db: Database, ano: int | None = None,
              hoje: date | None = None) -> dict[str, Any]:
    """Quanto falta, em que ritmo, e onde o ano provavelmente termina."""
    hoje = hoje or date.today()
    ano = ano or hoje.year
    declaradas = metas_declaradas(db, ano)
    corrente = ano == hoje.year
    meses_corridos = hoje.month if corrente else 12
    meses_restantes = (12 - hoje.month) if corrente else 0

    itens = []
    for codigo, rotulo, ajuda in INDICADORES:
        feito = realizado(db, codigo, ano)
        meta = declaradas.get(codigo)
        projecao = projetar(db, codigo, ano, feito, hoje)
        faltam = max(0, (meta or 0) - feito) if meta else None
        itens.append({
            "codigo": codigo, "rotulo": rotulo, "ajuda": ajuda,
            "realizado": feito, "meta": meta,
            "pct": round(100 * feito / meta) if meta else None,
            "faltam": faltam,
            "ritmo_mes": round(feito / meses_corridos, 2) if meses_corridos else None,
            # o que o ritmo precisa virar daqui para a frente, que e a
            # unica parte acionavel: "faltam 2" nao diz o que fazer,
            # "1 por mes ate dezembro" diz
            "precisa_por_mes": (round(faltam / meses_restantes, 2)
                                if faltam and meses_restantes else None),
            "projecao": projecao,
            "veredito": _veredito(meta, feito, projecao),
        })
    return {
        "ano": ano, "corrente": corrente, "hoje": hoje.isoformat(),
        "meses_corridos": meses_corridos, "meses_restantes": meses_restantes,
        "indicadores": itens,
        "sem_meta": [i["rotulo"] for i in itens if not i["meta"]],
    }
