"""O que a TV mostra além do painel: temas, ritmo, mundo, acervos, rotina e notícias.

O mural (`/mural`, `/tv`) e o Ao vivo em modo TV (`/aovivo?tv=1`) ficam
ligados numa parede, sem ninguém operando. Este módulo junta, numa
chamada só, o que as duas telas acrescentam ao que já mostravam:

- os indicadores temáticos do ano (tempo até publicar, taxa de aceite,
  acesso aberto, colaboração internacional, revistas e países);
- o ritmo mensal com tendência, faixa de confiança e projeção;
- os países que assinam com o laboratório, por número de artigos;
- os acervos abertos, com tamanho, segmentos e a última rodada;
- a rotina automática: cada passo, quando rodou e quando volta;
- as notícias: últimos publicados, últimos aceites, últimas submissões
  e os próximos compromissos;
- as citações: dados de impacto sincronizados de OpenAlex, Scopus e WOS.

Tudo é calculado do banco a cada pedido. Nada aqui é texto de modelo de
linguagem: o que não pode ser refeito a partir dos dados não entra.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Any

from . import aovivo, sinais, cache
from .db import Database

logger = logging.getLogger(__name__)

NOTICIAS = 6          # itens por grupo nas notícias
PAISES_NA_TV = 10     # países no ranking da parede
LEITURAS_NA_TV = 4    # frases do cálculo que cabem num quadro
MESES_NA_TV = 24      # a curva mensal que cabe numa parede lida de longe


def _curto(texto: Any, n: int = 90) -> str:
    t = str(texto or "").strip()
    return t if len(t) <= n else t[: n - 1].rstrip() + "…"


def noticias(db: Database, hoje: date | None = None, n: int = NOTICIAS) -> dict[str, Any]:
    """Os últimos acontecimentos, para a faixa que corre embaixo da tela.

    Publicados pela data de publicação (quem só tem o ano vai depois, pelo
    ano); aceites pela data de aceite; submissões pela data da tentativa
    mais recente; compromissos de hoje em diante, na ordem em que acontecem.
    """
    hoje = hoje or date.today()
    publicados = [
        {"titulo": _curto(a["title"]), "revista": a["journal"],
         "data": a["published_on"], "ano": a["year_published"]}
        for a in db.dicts(
            "SELECT title, journal, published_on, year_published FROM articles"
            " WHERE status = 'publicado'"
            " ORDER BY COALESCE(substr(published_on, 1, 10), year_published || '-00-00') DESC, id DESC"
            " LIMIT ?", (n,))]
    aceitos = [
        {"titulo": _curto(a["title"]), "revista": a["journal"], "data": a["accepted_on"]}
        for a in db.dicts(
            "SELECT title, journal, accepted_on FROM articles WHERE status = 'aceito'"
            " ORDER BY COALESCE(accepted_on, '') DESC, id DESC LIMIT ?", (n,))]
    submetidos = [
        {"titulo": _curto(s["title"]), "revista": s["journal"] or s["revista_do_artigo"],
         "data": s["submitted_on"]}
        for s in db.dicts(
            "SELECT a.title, s.journal, a.journal AS revista_do_artigo, s.submitted_on"
            "  FROM submissions s JOIN articles a ON a.id = s.article_id"
            " WHERE a.status IN ('submetido', 'em_revisao') AND s.submitted_on IS NOT NULL"
            " ORDER BY s.submitted_on DESC, s.id DESC LIMIT ?", (n,))]
    eventos = [
        {"titulo": _curto(e["title"], 70), "tipo": e["kind"], "quando": e["start_at"],
         "local": e["location_name"] or e["city"], "dia_inteiro": bool(e["all_day"])}
        for e in db.dicts(
            "SELECT title, kind, start_at, location_name, city, all_day FROM events"
            " WHERE substr(start_at, 1, 10) >= ? AND COALESCE(status, '') <> 'cancelado'"
            " ORDER BY start_at LIMIT ?", (hoje.isoformat(), n))]
    return {"publicados": publicados, "aceitos": aceitos, "submetidos": submetidos,
            "eventos": eventos}


def _acervos(db: Database) -> list[dict[str, Any]]:
    """Os acervos abertos, com o que a parede diz de cada um.

    Sem `quem`, `biblioteca.todas` devolve só os abertos: a TV não tem
    login, e acervo restrito não vai para a parede.
    """
    from . import biblioteca

    saida = []
    for b in biblioteca.todas(db):
        bid = db.scalar("SELECT id FROM biblioteca WHERE code = ?", (b["code"],))
        if bid is None:
            continue
        bid = int(bid)
        total = int(b.get("n") or 0)
        segmentos = int(db.scalar(
            "SELECT COUNT(DISTINCT segmento) FROM biblioteca_busca"
            " WHERE biblioteca_id = ? AND segmento IS NOT NULL", (bid,)) or 0)
        rodadas = db.dicts(
            "SELECT base, MAX(rodada_em) AS rodada_em,"
            "       SUM(CASE WHEN erro IS NOT NULL AND erro <> '' THEN 1 ELSE 0 END) AS erros"
            "  FROM biblioteca_busca WHERE biblioteca_id = ? GROUP BY base", (bid,))
        bases_ok = sum(1 for r in rodadas if r["rodada_em"] and not int(r["erros"] or 0))
        ultima = max((r["rodada_em"] for r in rodadas if r["rodada_em"]), default=None)
        saida.append({
            "code": b["code"], "title": b["title"], "linha": b.get("linha"),
            "eixo": b.get("eixo"), "total": total, "segmentos": segmentos,
            "bases_ok": bases_ok, "bases": len(rodadas), "rodada_em": ultima,
        })
    saida.sort(key=lambda x: (-x["total"], x["title"]))
    return saida


def _sinais_para_a_tv(s: dict[str, Any]) -> dict[str, Any]:
    """A parte do cálculo que cabe numa parede: os últimos meses, a
    tendência com a faixa, a projeção, e as frases."""
    k = MESES_NA_TV
    reg = s.get("regressao") or {}
    ic = s.get("tendencia_ic") or {}
    ultima_inflexao = (s.get("inflexoes") or [None])[-1]
    limite = s.get("limite") or {}
    return {
        "labels": list(s["labels"])[-k:],
        "meses": list(s["meses"])[-k:],
        "valores": list(s["valores"])[-k:],
        "tendencia": list(s["tendencia"])[-k:],
        "tendencia_alto": list(ic.get("alto") or [])[-k:],
        "tendencia_baixo": list(ic.get("baixo") or [])[-k:],
        "projecao": s.get("projecao"),
        "ritmo": s.get("ritmo"), "ritmo_antes": s.get("ritmo_antes"),
        "deriva_ano": reg.get("deriva_ano"), "r2": reg.get("r2"),
        "sinal_ruido": s.get("sinal_ruido"),
        "soma": s.get("soma"), "acumulado": (s.get("acumulado") or [None])[-1],
        "integral": (s.get("integral") or {}).get("area"),
        "inflexao": ultima_inflexao,
        "limite_k": limite.get("K"),
        "leituras": list(s.get("leituras") or [])[:LEITURAS_NA_TV],
    }


def _comparacoes(db: Database, hoje: date) -> dict[str, Any]:
    """Compara métricas com período anterior (mês, trimestre, ano)."""
    mes_atual = int(hoje.strftime("%m"))
    ano_atual = hoje.year
    dia_mes = hoje.day

    mes_anterior = mes_atual - 1 if mes_atual > 1 else 12
    ano_anterior_mes = ano_atual if mes_atual > 1 else ano_atual - 1

    # Publicações este mês vs. mês anterior
    pub_agora = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado' "
        "AND strftime('%Y-%m', COALESCE(published_on, year_published || '-01-01')) = ?",
        (f"{ano_atual:04d}-{mes_atual:02d}",)) or 0)
    pub_antes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado' "
        "AND strftime('%Y-%m', COALESCE(published_on, year_published || '-01-01')) = ?",
        (f"{ano_anterior_mes:04d}-{mes_anterior:02d}",)) or 0)

    # Aceites este mês vs. mês anterior
    aceites_agora = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'aceito' "
        "AND strftime('%Y-%m', COALESCE(accepted_on, '0000-00-00')) = ?",
        (f"{ano_atual:04d}-{mes_atual:02d}",)) or 0)
    aceites_antes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'aceito' "
        "AND strftime('%Y-%m', COALESCE(accepted_on, '0000-00-00')) = ?",
        (f"{ano_anterior_mes:04d}-{mes_anterior:02d}",)) or 0)

    # Taxa de aceite anual (aceitos / submetidos totais)
    aceitos_ano = int(db.scalar(
        "SELECT COUNT(DISTINCT article_id) FROM submissions "
        "WHERE strftime('%Y', submitted_on) = ?",
        (f"{ano_atual:04d}",)) or 0)
    submetidos_ano = int(db.scalar(
        "SELECT COUNT(DISTINCT article_id) FROM submissions "
        "WHERE strftime('%Y', submitted_on) = ? AND article_id IN "
        "(SELECT id FROM articles WHERE status IN ('aceito', 'publicado'))",
        (f"{ano_atual:04d}",)) or 0)
    taxa_aceite = round(100 * submetidos_ano / max(aceitos_ano, 1), 1) if aceitos_ano > 0 else 0

    return {
        "mes_atual": mes_atual,
        "publicacoes": {"agora": pub_agora, "antes": pub_antes, "delta": pub_agora - pub_antes},
        "aceites": {"agora": aceites_agora, "antes": aceites_antes, "delta": aceites_agora - aceites_antes},
        "taxa_aceite_anual": taxa_aceite,
    }


def _sazonalidade(db: Database, hoje: date) -> dict[str, Any]:
    """Analisa padrões de produção por mês (sazonalidade)."""
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    publicacoes_por_mes: dict[int, int] = {}
    aceites_por_mes: dict[int, int] = {}

    for mes in range(1, 13):
        pub = int(db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'publicado' "
            "AND strftime('%m', COALESCE(published_on, year_published || '-01-01')) = ?",
            (f"{mes:02d}",)) or 0)
        aceite = int(db.scalar(
            "SELECT COUNT(*) FROM articles WHERE status = 'aceito' "
            "AND strftime('%m', COALESCE(accepted_on, '0000-00-00')) = ?",
            (f"{mes:02d}",)) or 0)
        publicacoes_por_mes[mes] = pub
        aceites_por_mes[mes] = aceite

    picos_pub = sorted(publicacoes_por_mes.items(), key=lambda x: -x[1])[:3]
    picos_aceites = sorted(aceites_por_mes.items(), key=lambda x: -x[1])[:3]

    return {
        "picos_publicacao": [{"mes": meses[m - 1], "n": n} for m, n in picos_pub],
        "picos_aceite": [{"mes": meses[m - 1], "n": n} for m, n in picos_aceites],
    }


def _alertas(db: Database, hoje: date) -> dict[str, Any]:
    """Identifica eventos urgentes: aceites recentes, publicações, revistas ativas."""
    # Aceites nos últimos 7 dias
    aceites_recentes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'aceito' "
        "AND accepted_on >= date(?, '-7 days')",
        (hoje.isoformat(),)) or 0)

    # Publicações nos últimos 7 dias
    pubs_recentes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado' "
        "AND (published_on IS NOT NULL OR year_published >= ?)",
        (hoje.year,)) or 0)

    # Revistas com mais de 1 artigo em processo
    revistas_ativas = [r["journal"] for r in db.query(
        "SELECT journal FROM articles WHERE status IN ('submetido', 'em_revisao') "
        "GROUP BY journal HAVING COUNT(*) > 1 LIMIT 5")]

    # Dias desde última submissão
    ultima_submissao = db.scalar(
        "SELECT MAX(submitted_on) FROM submissions")
    dias_sem_submissao = (hoje - date.fromisoformat(ultima_submissao.split("T")[0])).days if ultima_submissao else None

    return {
        "aceites_ultimos_7d": aceites_recentes,
        "pubs_recentes": pubs_recentes,
        "revistas_em_processo": revistas_ativas or [],
        "dias_sem_submissao": dias_sem_submissao,
    }


def _health_rotina(db: Database) -> dict[str, Any]:
    """Verifica saúde da rotina automática: último ciclo, próximo, erros."""
    try:
        from . import rotina
        sit = rotina.situacao(db)
        proximos = sit.get("proximos", [])
        tarefas = sit.get("tarefas", [])
        return {
            "tarefas_ok": sum(1 for t in tarefas if not t.get("erro")),
            "tarefas_total": len(tarefas),
            "ligada": sit.get("ligada", False),
            "proximos_em_horas": len(proximos),
        }
    except Exception:
        # Banco ainda não tem tabelas de rotina, retorna defaults
        return {
            "tarefas_ok": 0,
            "tarefas_total": 0,
            "ligada": False,
            "proximos_em_horas": 0,
        }


def _linhas_pesquisa(db: Database) -> list[dict[str, Any]]:
    """Linhas de pesquisa com número de artigos e taxa de publicação."""
    saida = []
    linhas = db.dicts(
        "SELECT id, name FROM research_lines WHERE active ORDER BY name"
    )
    for linha in linhas:
        lid = linha["id"]
        total_artigos = int(db.scalar(
            "SELECT COUNT(*) FROM articles a"
            " WHERE a.research_line_id = ?", (lid,)
        ) or 0)
        publicados = int(db.scalar(
            "SELECT COUNT(*) FROM articles a"
            " WHERE a.research_line_id = ? AND a.status = 'publicado'", (lid,)
        ) or 0)
        taxa = publicados / total_artigos if total_artigos > 0 else 0
        saida.append({
            "id": lid,
            "nome": linha["name"],
            "artigos": total_artigos,
            "taxa_publicacao": taxa,
        })
    return saida


def _pessoas_com_ponto(db: Database, agora: datetime | None = None) -> list[dict[str, Any]]:
    """Pessoas cadastradas com indicador de quem está presente agora.

    "Presente" é quem tem sessão de ponto aberta agora mesmo (ponto.agora),
    não um horário fixo nem um "visto há N horas" -- o mesmo dado que a
    tela de ponto do integrante usa para bater entrada e saída.
    """
    from . import ponto

    presentes = {p["member_id"]: p for p in ponto.agora(db)}

    saida = []
    pessoas = db.dicts(
        "SELECT id, full_name, role FROM members ORDER BY full_name"
    )
    for pessoa in pessoas:
        pid = pessoa["id"]
        n_artigos = int(db.scalar(
            "SELECT COUNT(DISTINCT a.id) FROM articles a"
            " JOIN article_authors aa ON aa.article_id = a.id"
            " WHERE aa.member_id = ?", (pid,)
        ) or 0)
        presenca = presentes.get(pid)

        saida.append({
            "id": pid,
            "nome": pessoa["full_name"],
            "vinculo": pessoa["role"],
            "n_artigos": n_artigos,
            "ativo_agora": presenca is not None,
            "ha_horas": presenca["ha_horas"] if presenca else None,
            "atividade": (presenca or {}).get("atividade"),
            "projeto": (presenca or {}).get("projeto"),
            "artigo": (presenca or {}).get("artigo"),
        })
    return saida


def _citacoes_bases_dados(db: Database) -> dict[str, Any]:
    """Sincroniza e retorna dados de citações de bases externas (OpenAlex, Scopus, WOS)."""
    try:
        from . import bases_dados
        sync = bases_dados.SincronizadorCitacoes(db)
        return cache.computar("dashboard_citacoes_tv", lambda: sync.dashboard_citacoes(), ttl=604800)
    except Exception as e:
        logger.exception(f"Erro ao sincronizar citações: {e}")
        return {"linhas": [], "resumo": {"total_artigos": 0, "total_citacoes": 0, "media_citacoes": 0}}


def para_a_tv(db: Database, hoje: date | None = None) -> dict[str, Any]:
    """Tudo o que as telas da parede acrescentam, numa chamada só, com cache."""
    from . import rotina

    hoje = hoje or date.today()

    def _agregar():
        per = aovivo.periodo(db, "ano", hoje)
        t = aovivo.temas(db, per, hoje)
        m = aovivo.mundo(db)
        paises = sorted(m["paises"], key=lambda p: (-int(p["n"]), p["pais"]))
        fora_do_brasil = [p for p in paises if (p.get("iso") or "").upper() != "BR"
                          and p["pais"].strip().lower() != "brasil"]
        return {
            "periodo": {"code": per["code"], "rotulo": per["rotulo"], "de": per["de"], "ate": per["ate"]},
            "temas": {"kpis": t["kpis"], "revistas": t["treemap"][:8]},
            "mundo": {
                "sede": m["sede"],
                "paises": paises[:PAISES_NA_TV],
                "n_paises": len(paises) + len(m.get("sem_coordenada") or []),
                "n_fora_do_brasil": len(fora_do_brasil) + len(m.get("sem_coordenada") or []),
                "artigos_com_pais": m["artigos_com_pais"],
                "instituicoes": len(m["instituicoes"]),
            },
            "sinais": _sinais_para_a_tv(sinais.analisar(db, hoje)),
            "acervos": cache.computar(f"acervos_{hoje.isoformat()}", lambda: _acervos(db), ttl=300),
            "rotina": rotina.situacao(db),
            "noticias": cache.computar(f"noticias_{hoje.isoformat()}", lambda: noticias(db, hoje), ttl=120),
            "comparacoes": cache.computar(f"comp_{hoje.isoformat()}", lambda: _comparacoes(db, hoje), ttl=3600),
            "sazonalidade": cache.computar("sazonalidade", lambda: _sazonalidade(db, hoje), ttl=86400),
            "alertas": cache.computar(f"alertas_{hoje.isoformat()}", lambda: _alertas(db, hoje), ttl=600),
            "health": _health_rotina(db),
            "linhas": cache.computar("linhas_pesquisa", lambda: _linhas_pesquisa(db), ttl=300),
            "pessoas": cache.computar("pessoas_com_ponto", lambda: _pessoas_com_ponto(db), ttl=120),
            "citacoes": _citacoes_bases_dados(db),
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
        }

    return cache.computar(f"tv_completo_{hoje.isoformat()}", _agregar, ttl=60)
