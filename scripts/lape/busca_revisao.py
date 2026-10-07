"""Robo de busca das revisoes de handebol nas bases bibliograficas.

Le as estrategias (blocos de termos) de data/revisoes/handebol/estrategias.json,
traduz cada uma para a sintaxe de cada base, coleta os registros, funde as
duplicatas e grava tudo em data/revisoes/handebol/busca_<revisao>_<data>/.

Bases abertas: OpenAlex (chave gratuita OPENALEX_API_KEY recomendada), Crossref, Europe PMC, PubMed.
Bases com chave, que so respondem por inteiro de dentro da rede da universidade
ou com a assinatura dela: Scopus (SCOPUS_API_KEY, SCOPUS_INST_TOKEN) e Web of
Science (WOS_API_KEY). Sem a chave a base e pulada e o relatorio diz isso -- a
busca nunca finge ter consultado uma base que nao respondeu.

Uso:
    python3 -m scripts.lape.busca_revisao --revisao humor
    python3 -m scripts.lape.busca_revisao --revisao mapeamento --bases openalex pubmed scopus
    python3 -m scripts.lape.busca_revisao --revisao humor --max 300 --teste
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import time
import unicodedata
from datetime import date
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

import os

from . import config

RAIZ = Path(__file__).resolve().parents[2]
PASTA = RAIZ / "data" / "revisoes" / "handebol"
CAMPOS = ["base", "estrategia", "id_base", "doi", "pmid", "titulo", "ano", "periodico", "autores"]


def _ua() -> str:
    return f"LAPE-Lab ({config.CONTACT_EMAIL or 'sem-contato'})"


def http_json(url: str, headers: dict | None = None, tentativas: int = 3, espera: float = 1.0):
    h = {"User-Agent": _ua(), "Accept": "application/json"}
    h.update(headers or {})
    for i in range(tentativas):
        try:
            with urlopen(Request(url, headers=h), timeout=40) as r:
                return json.loads(r.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError, TimeoutError) as e:
            if i == tentativas - 1:
                raise RuntimeError(f"{url[:90]}... -> {e}") from e
            time.sleep(espera * (2 ** i))


# --------------------------------------------------------------- estrategias
def carregar() -> dict:
    return json.loads((PASTA / "estrategias.json").read_text(encoding="utf-8"))


def blocos_da(estr: dict, cfg: dict) -> list[list[str]]:
    """Cada elemento de `and` vira uma lista de termos (OR dentro do grupo)."""
    out = []
    for grupo in estr["and"]:
        termos: list[str] = []
        for nome in grupo:
            termos += cfg["blocos"][nome]
        out.append(list(dict.fromkeys(termos)))
    return out


def _aspas(t: str) -> str:
    return f'"{t}"' if " " in t or "-" in t else t


def sintaxe(base: str, grupos: list[list[str]]) -> str:
    def or_(ts, campo=None):
        partes = [_aspas(t) for t in ts]
        if base == "pubmed":
            partes = [f"{p}[tiab]" for p in partes]
        elif base == "europepmc":
            partes = [f"(TITLE_ABS:{p})" for p in partes]
        elif base == "scopus":
            return "(" + " OR ".join(partes) + ")"
        elif base == "wos":
            return "(" + " OR ".join(partes) + ")"
        return "(" + " OR ".join(partes) + ")"
    corpo = " AND ".join(or_(g) for g in grupos)
    if base == "scopus":
        return f"TITLE-ABS-KEY({corpo})"
    if base == "wos":
        return f"TS={corpo}"
    return corpo


# ------------------------------------------------------------------- bases
def _reg(base, estr, id_base="", doi="", pmid="", titulo="", ano="", periodico="", autores=""):
    doi = (doi or "").lower().replace("https://doi.org/", "").strip()
    return dict(base=base, estrategia=estr, id_base=id_base, doi=doi, pmid=pmid, titulo=(titulo or "").strip(),
                ano=ano, periodico=periodico or "", autores=autores or "")


def busca_openalex(estr_id, grupos, maximo):
    q = sintaxe("openalex", grupos)
    out, cursor = [], "*"
    while len(out) < maximo and cursor:
        par = {"search": q, "per-page": 100, "cursor": cursor, "select": "id,doi,title,publication_year,primary_location,authorships,ids"}
        if os.environ.get("OPENALEX_API_KEY"):  # sem chave, o limite diario e dividido por todo o IP
            par["api_key"] = os.environ["OPENALEX_API_KEY"]
        url = "https://api.openalex.org/works?" + urlencode(par)
        d = http_json(url)
        for w in d.get("results", []):
            loc = (w.get("primary_location") or {}).get("source") or {}
            au = "; ".join((a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])[:6])
            out.append(_reg("OpenAlex", estr_id, w.get("id", ""), w.get("doi") or "", (w.get("ids") or {}).get("pmid", "").rsplit("/", 1)[-1], w.get("title"), w.get("publication_year"), loc.get("display_name"), au))
        cursor = d.get("meta", {}).get("next_cursor")
        if not d.get("results"):
            break
    return out[:maximo], d.get("meta", {}).get("count") if out else 0


def busca_crossref(estr_id, grupos, maximo):
    # A Crossref nao aceita operadores booleanos: cruza-se o primeiro termo do
    # primeiro grupo com cada termo dos demais, e a fusao tira as repetidas.
    base_t = grupos[0][:3]
    outros = grupos[1][:6] if len(grupos) > 1 else [""]
    out, vistos = [], set()
    for t1 in base_t:
        for t2 in outros:
            url = "https://api.crossref.org/works?" + urlencode({"query.bibliographic": f"{t1} {t2}".strip(), "rows": 50, "select": "DOI,title,issued,container-title,author"})
            try:
                d = http_json(url)
            except RuntimeError:
                continue
            for w in d["message"]["items"]:
                if w["DOI"] in vistos:
                    continue
                vistos.add(w["DOI"])
                ano = (w.get("issued", {}).get("date-parts") or [[""]])[0][0]
                au = "; ".join(f"{a.get('family','')} {a.get('given','')[:1]}" for a in w.get("author", [])[:6])
                out.append(_reg("Crossref", estr_id, w["DOI"], w["DOI"], "", (w.get("title") or [""])[0], ano, (w.get("container-title") or [""])[0], au))
    return out[:maximo], len(out)


def busca_europepmc(estr_id, grupos, maximo):
    q = sintaxe("europepmc", grupos)
    out, cursor, total = [], "*", 0
    while len(out) < maximo:
        url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search?" + urlencode({"query": q, "format": "json", "pageSize": 100, "cursorMark": cursor, "resultType": "lite"})
        d = http_json(url)
        total = d.get("hitCount", 0)
        for r in d.get("resultList", {}).get("result", []):
            out.append(_reg("Europe PMC", estr_id, f"{r.get('source')}:{r.get('id')}", r.get("doi", ""), r.get("pmid", ""), r.get("title"), r.get("pubYear"), r.get("journalTitle"), r.get("authorString", "")))
        nxt = d.get("nextCursorMark")
        if not nxt or nxt == cursor or not d.get("resultList", {}).get("result"):
            break
        cursor = nxt
    return out[:maximo], total


def busca_pubmed(estr_id, grupos, maximo):
    q = sintaxe("pubmed", grupos)
    d = http_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?" + urlencode({"db": "pubmed", "term": q, "retmax": maximo, "retmode": "json"}))
    ids = d["esearchresult"].get("idlist", []); total = int(d["esearchresult"].get("count", 0))
    out = []
    for i in range(0, len(ids), 100):
        lote = ids[i:i + 100]
        s = http_json("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?" + urlencode({"db": "pubmed", "id": ",".join(lote), "retmode": "json"}))["result"]
        for pid in lote:
            r = s.get(pid, {})
            doi = next((x["value"] for x in r.get("articleids", []) if x.get("idtype") == "doi"), "")
            out.append(_reg("PubMed", estr_id, pid, doi, pid, r.get("title"), (r.get("pubdate") or "")[:4], r.get("fulljournalname"), "; ".join(a["name"] for a in r.get("authors", [])[:6])))
        time.sleep(0.4)
    return out, total


def busca_scopus(estr_id, grupos, maximo):
    if not (config.SCOPUS_API_KEY or config.SCOPUS_INST_TOKEN):
        raise RuntimeError("sem SCOPUS_API_KEY/SCOPUS_INST_TOKEN")
    h = {}
    if config.SCOPUS_API_KEY:
        h["X-ELS-APIKey"] = config.SCOPUS_API_KEY
    if config.SCOPUS_INST_TOKEN:
        h["X-ELS-Insttoken"] = config.SCOPUS_INST_TOKEN
    q = sintaxe("scopus", grupos); out, inicio, total = [], 0, 0
    while len(out) < maximo:
        d = http_json("https://api.elsevier.com/content/search/scopus?" + urlencode({"query": q, "count": 25, "start": inicio, "view": "STANDARD"}), h)["search-results"]
        total = int(d.get("opensearch:totalResults", 0)); ents = d.get("entry", [])
        if not ents or "error" in ents[0]:
            break
        for e in ents:
            out.append(_reg("Scopus", estr_id, e.get("eid", ""), e.get("prism:doi", ""), e.get("pubmed-id", ""), e.get("dc:title"), (e.get("prism:coverDate") or "")[:4], e.get("prism:publicationName"), e.get("dc:creator", "")))
        inicio += 25
        if inicio >= total:
            break
        time.sleep(0.3)
    return out[:maximo], total


def busca_wos(estr_id, grupos, maximo):
    if not config.WOS_API_KEY:
        raise RuntimeError("sem WOS_API_KEY")
    q = sintaxe("wos", grupos); out, pag, total = [], 1, 0
    while len(out) < maximo:
        d = http_json("https://api.clarivate.com/apis/wos-starter/v1/documents?" + urlencode({"q": q, "limit": 50, "page": pag}), {"X-ApiKey": config.WOS_API_KEY})
        total = d.get("metadata", {}).get("total", 0)
        hits = d.get("hits", [])
        if not hits:
            break
        for r in hits:
            ids = r.get("identifiers", {}); src = r.get("source", {})
            out.append(_reg("Web of Science", estr_id, r.get("uid", ""), ids.get("doi", ""), ids.get("pmid", ""), r.get("title"), src.get("publishYear"), src.get("sourceTitle"), "; ".join(a.get("displayName", "") for a in r.get("names", {}).get("authors", [])[:6])))
        pag += 1
        if len(out) >= total:
            break
        time.sleep(0.5)
    return out[:maximo], total


BASES = {"openalex": busca_openalex, "crossref": busca_crossref, "europepmc": busca_europepmc, "pubmed": busca_pubmed, "scopus": busca_scopus, "wos": busca_wos}
NOMES = {"openalex": "OpenAlex", "crossref": "Crossref", "europepmc": "Europe PMC", "pubmed": "PubMed", "scopus": "Scopus", "wos": "Web of Science"}


# ----------------------------------------------------------------- fusao
def _norm(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", t)


def fundir(regs: list[dict]) -> list[dict]:
    """Identificador digital, depois PubMed, depois titulo normalizado (como no metodo)."""
    por_doi, por_pmid, por_tit, saida = {}, {}, {}, []
    for r in regs:
        alvo = None
        if r["doi"] and r["doi"] in por_doi:
            alvo = por_doi[r["doi"]]
        elif r["pmid"] and r["pmid"] in por_pmid:
            alvo = por_pmid[r["pmid"]]
        elif _norm(r["titulo"]) and _norm(r["titulo"]) in por_tit:
            alvo = por_tit[_norm(r["titulo"])]
        if alvo is None:
            alvo = dict(r, bases={r["base"]}); alvo["estrategias"] = {r["estrategia"]}; saida.append(alvo)
        else:
            alvo["bases"].add(r["base"]); alvo["estrategias"].add(r["estrategia"])
            for k in ("doi", "pmid", "ano", "periodico", "autores"):
                alvo[k] = alvo[k] or r[k]
        if alvo["doi"]:
            por_doi[alvo["doi"]] = alvo
        if alvo["pmid"]:
            por_pmid[alvo["pmid"]] = alvo
        if _norm(alvo["titulo"]):
            por_tit[_norm(alvo["titulo"])] = alvo
    return saida


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--revisao", choices=["humor", "mapeamento"], required=True)
    ap.add_argument("--bases", nargs="*", default=list(BASES), choices=list(BASES))
    ap.add_argument("--max", type=int, default=1000, help="maximo de registros por consulta (estrategia x base)")
    ap.add_argument("--teste", action="store_true", help="so a estrategia mestra, 50 registros por base")
    a = ap.parse_args(argv)
    cfg = carregar(); rev = cfg["revisoes"][a.revisao]
    estrs = rev["estrategias"][:1] if a.teste else rev["estrategias"]
    maximo = 50 if a.teste else a.max
    saida = PASTA / f"busca_{a.revisao}_{date.today().isoformat()}"
    saida.mkdir(parents=True, exist_ok=True)
    todos, relatorio = [], []
    for e in estrs:
        grupos = blocos_da(e, cfg)
        for b in a.bases:
            t0 = time.time()
            try:
                regs, total = BASES[b](e["id"], grupos, maximo)
                st = "ok"
            except Exception as ex:  # base fora do ar, sem chave ou sem acesso
                regs, total, st = [], 0, f"SEM RETORNO: {ex}"
            todos += regs
            relatorio.append(dict(estrategia=e["id"], base=NOMES[b], status=st, total_na_base=total, coletados=len(regs), consulta=sintaxe(b, grupos), segundos=round(time.time() - t0, 1)))
            print(f"[{e['id']}] {NOMES[b]:15} {st[:60]:60} coletados={len(regs)} total_na_base={total}")
    with open(saida / "passagens.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CAMPOS); w.writeheader(); w.writerows(todos)
    distintos = fundir(todos)
    with open(saida / "distintos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(CAMPOS[3:] + ["bases", "estrategias"])
        for r in distintos:
            w.writerow([r["doi"], r["pmid"], r["titulo"], r["ano"], r["periodico"], r["autores"], "; ".join(sorted(r["bases"])), "; ".join(sorted(r["estrategias"]))])
    with open(saida / "relatorio.json", "w", encoding="utf-8") as f:
        json.dump(dict(revisao=a.revisao, data=date.today().isoformat(), passagens=len(todos), distintos=len(distintos), por_consulta=relatorio), f, ensure_ascii=False, indent=2)
    por_base = {}
    for r in todos:
        por_base[r["base"]] = por_base.get(r["base"], 0) + 1
    print("\nPassagens por base:", por_base, "| total", len(todos), "| distintos", len(distintos))
    print("Saida:", saida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
