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
  e os próximos compromissos.

Tudo é calculado do banco a cada pedido. Nada aqui é texto de modelo de
linguagem: o que não pode ser refeito a partir dos dados não entra.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

from . import aovivo, sinais
from .db import Database

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


def para_a_tv(db: Database, hoje: date | None = None) -> dict[str, Any]:
    """Tudo o que as telas da parede acrescentam, numa chamada só."""
    from . import rotina

    hoje = hoje or date.today()
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
        "acervos": _acervos(db),
        "rotina": rotina.situacao(db),
        "noticias": noticias(db, hoje),
        "gerado_em": datetime.now().isoformat(timespec="seconds"),
    }
