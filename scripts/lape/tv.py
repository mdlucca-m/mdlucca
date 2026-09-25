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
    """Linhas de pesquisa com número de artigos, taxa de publicação e
    citações -- citações lidas de `articles.openalex_citations`, a mesma
    coluna que a rotina automática mantém sincronizada e que
    `_citacoes_bases_dados` usa (ver o comentário lá sobre por que não
    busca na OpenAlex de novo aqui)."""
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
        citacoes = int(db.scalar(
            "SELECT COALESCE(SUM(a.openalex_citations), 0) FROM articles a"
            " WHERE a.research_line_id = ?", (lid,)
        ) or 0)
        taxa = publicados / total_artigos if total_artigos > 0 else 0
        saida.append({
            "id": lid,
            "nome": linha["name"],
            "artigos": total_artigos,
            "publicados": publicados,
            "citacoes": citacoes,
            "taxa_publicacao": taxa,
        })
    return saida


def _organograma_para_tv(db: Database) -> dict[str, Any]:
    """O organograma de verdade (metrics.organograma_publico), mais o ponto.

    Só quem está no cadastro do LAPE com `is_external = 0` -- nunca coautor
    externo, nunca rede de colaboração montada por artigo em comum. A
    hierarquia (quem orienta quem, e as raízes) vem de `advisor_id`/
    `co_advisor_id`, exatamente como o organograma que a coordenação já usa
    -- o mural não inventa outra árvore. `organograma_publico` já tira o
    que é só da coordenação (bolsa, prazo de defesa); aqui só falta somar
    quem está com o ponto aberto agora.
    """
    from . import metrics, ponto

    org = metrics.organograma_publico(db)
    presentes = {p["member_id"]: p for p in ponto.agora(db)}
    for pessoa in org["people"]:
        presenca = presentes.get(pessoa["id"])
        pessoa["ativo_agora"] = presenca is not None
        pessoa["ha_horas"] = presenca["ha_horas"] if presenca else None
        pessoa["atividade"] = (presenca or {}).get("atividade")
    return org


def _citacoes_bases_dados(db: Database) -> dict[str, Any]:
    """Citações por linha de pesquisa, direto de `articles.openalex_citations`
    -- a coluna que a rotina automática já mantém sincronizada com a
    OpenAlex (ver rotina.py). Antes esta função chamava a OpenAlex de
    novo, artigo por artigo, TODA VEZ que a tela era montada (via
    `bases_dados.SincronizadorCitacoes`) -- centenas de chamadas de rede
    síncronas dentro de um pedido de página, e um erro de digitação
    (`db.dict` em vez de `db.dicts`) que fazia toda chamada falhar
    silenciosamente, deixando a tela sempre em zero. Ler a coluna já
    sincronizada é mais rápido, mais confiável, e é exatamente o mesmo
    dado -- só sem buscar de novo o que a rotina já trouxe.
    """
    linhas_db = db.dicts(
        "SELECT rl.id, rl.name AS nome,"
        "       COUNT(a.id) AS total_artigos,"
        "       COALESCE(SUM(a.openalex_citations), 0) AS total_citacoes,"
        "       SUM(CASE WHEN COALESCE(a.openalex_citations, 0) > 0 THEN 1 ELSE 0 END) AS artigos_com_dados"
        "  FROM research_lines rl"
        "  LEFT JOIN articles a ON a.research_line_id = rl.id"
        " WHERE rl.active"
        " GROUP BY rl.id, rl.name"
        " ORDER BY rl.name")

    # Os mais citados de cada linha, para a lista "Mais citados" da tela --
    # antes vinha do mesmo lugar que nunca funcionava (ver acima); aqui é
    # só ler o que a rotina já sincronizou, maior citação primeiro.
    artigos_db = db.dicts(
        "SELECT a.research_line_id, a.title AS titulo, a.journal AS revista,"
        "       a.year_published AS ano_publicacao, a.openalex_citations AS citacoes"
        "  FROM articles a"
        " WHERE COALESCE(a.openalex_citations, 0) > 0"
        " ORDER BY a.openalex_citations DESC"
        " LIMIT 40")
    artigos_por_linha: dict[int, list[dict[str, Any]]] = {}
    for artigo in artigos_db:
        artigos_por_linha.setdefault(artigo["research_line_id"], []).append({
            "titulo": artigo["titulo"], "revista": artigo["revista"],
            "ano_publicacao": artigo["ano_publicacao"], "citacoes": artigo["citacoes"],
        })

    linhas = []
    total_citacoes_lab = 0
    total_artigos_lab = 0
    artigos_com_dados_lab = 0
    for linha in linhas_db:
        total_citacoes = linha["total_citacoes"] or 0
        total_artigos = linha["total_artigos"] or 0
        artigos_com_dados = linha["artigos_com_dados"] or 0
        media = round(total_citacoes / artigos_com_dados, 2) if artigos_com_dados else 0
        linhas.append({
            "id": linha["id"], "nome": linha["nome"],
            "total_artigos": total_artigos, "total_citacoes": total_citacoes,
            "media_citacoes": media, "artigos_com_dados": artigos_com_dados,
            "artigos": artigos_por_linha.get(linha["id"], [])[:5],
        })
        total_citacoes_lab += total_citacoes
        total_artigos_lab += total_artigos
        artigos_com_dados_lab += artigos_com_dados

    return {
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
        "linhas": linhas,
        "resumo": {
            "total_artigos": total_artigos_lab,
            "total_citacoes": total_citacoes_lab,
            "media_citacoes": round(total_citacoes_lab / artigos_com_dados_lab, 2) if artigos_com_dados_lab else 0,
            "linhas_ativas": len(linhas),
        },
    }


def para_a_tv(db: Database, hoje: date | None = None) -> dict[str, Any]:
    """Tudo o que as telas da parede acrescentam, numa chamada só, com cache."""
    from . import metas, rotina

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
                # Todo país com artigo, não só o top 10 do ranking -- o
                # mapa-múndi colore pelo nome, e um país de fora do
                # ranking apareceria "sem dado" mesmo tendo produção.
                "mapa_paises": {p["pais"]: p["n"] for p in paises},
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
            "organograma": cache.computar("organograma_tv", lambda: _organograma_para_tv(db), ttl=120),
            "citacoes": _citacoes_bases_dados(db),
            "meta_publicacoes": _meta_publicacoes(db, metas, hoje),
            "gerado_em": datetime.now().isoformat(timespec="seconds"),
        }

    return cache.computar(f"tv_completo_{hoje.isoformat()}", _agregar, ttl=60)


def _meta_publicacoes(db: Database, metas_mod: Any, hoje: date) -> dict[str, Any] | None:
    """Só o indicador "publicacoes" de `metas.progresso` -- o que a lâmina
    de indicadores precisa para uma frase honesta sobre o ano, nunca um
    "vai bater a meta" inventado. Sem meta declarada, `meta` vem None e
    `veredito` já diz "sem meta declarada" -- a tela mostra isso, e não
    finge que existe uma meta."""
    progresso = metas_mod.progresso(db, hoje.year, hoje)
    for item in progresso["indicadores"]:
        if item["codigo"] == "publicacoes":
            return item
    return None
