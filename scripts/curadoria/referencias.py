"""Formatação de referências pela NBR 6023 e verificação de integridade de DOI.

Corrige três achados:
  A2 — ponto duplo em 58 de 58 referências, de concatenar "A." com ".";
  A3 — nenhuma referência destacava o título do periódico, que a norma exige;
  G5 — 82 DOIs marcados como suspeitos na base e 39 com ano incoerente, nunca
       reportados, embora 2.366 referências sejam geradas desses campos.

A referência é devolvida em partes, com o trecho a destacar identificado, para
que o gerador do .docx aplique itálico de verdade em vez de marcação textual.
"""
from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass

# Ano embutido no DOI de editoras que o usam (Frontiers, MDPI, Elsevier...).
ANO_NO_DOI = re.compile(r"\.((?:19|20)\d{2})\.")
DOI_VALIDO = re.compile(r"^10\.\d{4,9}/[-._;()/:a-z0-9<>\[\]+]+$", re.I)


@dataclass
class Referencia:
    """Referência ABNT em três partes: o que vem antes do periódico, o nome do
    periódico (a destacar) e o que vem depois."""
    antes: str
    periodico: str
    depois: str
    doi: str = ""
    alerta: str = ""

    def texto(self) -> str:
        return f"{self.antes}{self.periodico}{self.depois}"


def _sobrenome_e_iniciais(nome: str) -> str:
    """'Walter Staiano' -> 'STAIANO, W.'  ·  'Krol-Zielinska, M.' -> 'KRÓL-ZIELIŃSKA, M.'"""
    nome = " ".join(nome.split())
    if "," in nome:
        sobre, resto = nome.split(",", 1)
        iniciais = " ".join(f"{p[0].upper()}." for p in resto.split() if p)
        return f"{sobre.strip().upper()}, {iniciais}".strip().rstrip(",")
    partes = nome.split()
    if len(partes) == 1:
        return partes[0].upper()
    sobre = partes[-1].upper()
    iniciais = " ".join(f"{p[0].upper()}." for p in partes[:-1])
    return f"{sobre}, {iniciais}"


def autores_abnt(bruto: str | None) -> str:
    """NBR 6023: até três autores, todos; mais de três, o primeiro e 'et al.'."""
    if not bruto or not bruto.strip():
        return "[s. n.]"
    nomes = [n.strip() for n in re.split(r";|,(?=\s*[A-ZÀ-Ý][a-zà-ÿ])", bruto) if n.strip()]
    if len(nomes) == 1:
        nomes = [n.strip() for n in bruto.split(",") if n.strip()]
        if len(nomes) > 1 and all(len(n.split()) <= 3 for n in nomes):
            pass
        else:
            nomes = [bruto.strip()]
    formatados = [_sobrenome_e_iniciais(n) for n in nomes if n]
    if not formatados:
        return "[s. n.]"
    if len(formatados) <= 3:
        return "; ".join(formatados)
    return f"{formatados[0]} et al."


def _limpar(s: str | None) -> str:
    return " ".join((s or "").split())


def formatar(reg: sqlite3.Row | dict) -> Referencia:
    g = (lambda k: _limpar(reg[k] if isinstance(reg, dict) else reg[k]))

    autores = autores_abnt(g("autores"))
    titulo = g("titulo").rstrip(".")
    periodico = g("revista") or "[s. l.]"
    ano = g("ano") or "[s. d.]"
    doi = g("doi").lower().rstrip(".")

    # "SILVA, A." já termina em ponto; não se acrescenta outro (achado A2).
    antes = autores if autores.endswith(".") else autores + "."
    antes = f"{antes} {titulo}. "

    depois_partes = []
    if g("volume"):
        depois_partes.append(f"v. {g('volume')}")
    if g("numero"):
        depois_partes.append(f"n. {g('numero')}")
    if g("paginas"):
        pag = g("paginas")
        depois_partes.append(f"p. {pag}" if not pag.lower().startswith("e") else pag)
    depois_partes.append(ano)
    depois = ", " + ", ".join(depois_partes) + "."
    if doi:
        depois += f" DOI: {doi}."

    return Referencia(antes, periodico, depois, doi,
                      alerta=_alerta_referencia(reg, doi, ano))


def _alerta_referencia(reg, doi: str, ano: str) -> str:
    """Primeira pendência aplicável, em ordem de gravidade."""
    if doi and not DOI_VALIDO.match(doi):
        return f"DOI malformado: {doi}"
    m = ANO_NO_DOI.search(doi) if doi else None
    if m and ano.isdigit() and abs(int(m.group(1)) - int(ano)) >= 2:
        return (f"ano do registro ({ano}) diverge do ano embutido no DOI "
                f"({m.group(1)}) em {abs(int(m.group(1)) - int(ano))} anos")
    try:
        if reg["doi_suspeito"]:
            return "marcado como doi_suspeito pela rotina de curadoria"
    except (KeyError, IndexError, TypeError):
        pass
    if not doi:
        return "sem DOI"
    if not _limpar(reg["volume"]) and not _limpar(reg["paginas"]):
        return "sem volume nem paginação, referência incompleta pela NBR 6023"
    if not _limpar(reg["volume"]):
        return "sem volume"
    return ""


def _alerta_doi_legado(reg, doi: str, ano: str) -> str:
    if not doi:
        return "sem DOI"
    if not DOI_VALIDO.match(doi):
        return f"DOI malformado: {doi}"
    m = ANO_NO_DOI.search(doi)
    if m and ano.isdigit() and abs(int(m.group(1)) - int(ano)) >= 2:
        return (f"ano do registro ({ano}) diverge do ano embutido no DOI "
                f"({m.group(1)}) em {abs(int(m.group(1)) - int(ano))} anos")
    try:
        suspeito = reg["doi_suspeito"]
    except (KeyError, IndexError, TypeError):
        suspeito = 0
    if suspeito:
        return "marcado como doi_suspeito pela rotina de curadoria"
    return ""


CATEGORIAS = (
    ("ano do registro", "ano do DOI divergente do ano do registro"),
    ("malformado", "DOI malformado"),
    ("doi_suspeito", "DOI marcado como suspeito pela curadoria"),
    ("sem DOI", "sem DOI"),
    ("sem volume nem", "sem volume nem paginação"),
    ("sem volume", "sem volume"),
)


def _categoria(alerta: str) -> str:
    for chave, rotulo in CATEGORIAS:
        if chave in alerta:
            return rotulo
    return alerta


# ── Verificação em lote ─────────────────────────────────────────────────────
def auditar(con: sqlite3.Connection, ids: set[int] | None = None) -> dict:
    con.row_factory = sqlite3.Row
    linhas = con.execute("SELECT * FROM artigo").fetchall()
    if ids is not None:
        linhas = [l for l in linhas if l["id"] in ids]
    problemas: dict[str, list] = {}
    for l in linhas:
        r = formatar(l)
        if r.alerta:
            problemas.setdefault(_categoria(r.alerta), []).append(
                (l["id"], r.doi, l["titulo"][:50]))
    return {
        "avaliados": len(linhas),
        "com_problema": sum(len(v) for v in problemas.values()),
        "por_tipo": {k: len(v) for k, v in sorted(
            problemas.items(), key=lambda x: -len(x[1]))},
        "exemplos": {k: v[:3] for k, v in problemas.items()},
    }


def verificar_crossref(dois: list[str], sessao=None) -> dict[str, dict]:
    """Confere autor, ano e título de cada DOI no Crossref.

    Requer que `api.crossref.org` esteja liberado na política de rede do
    ambiente; hoje ele responde 403 ao CONNECT. A função existe pronta e é
    exercitada pelo teste com resposta gravada.
    """
    import json
    import sys
    import urllib.parse
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from busca.http import ErroHTTP, Sessao

    sessao = sessao or Sessao(req_por_segundo=5.0)
    fora: dict[str, dict] = {}
    for doi in dois:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="")
        try:
            msg = json.loads(sessao.pedir(url, rotulo="crossref"))["message"]
        except (ErroHTTP, KeyError, json.JSONDecodeError) as e:
            fora[doi] = {"estado": "não resolve", "detalhe": str(e)[:120]}
            continue
        partes = (msg.get("issued", {}).get("date-parts") or [[None]])[0]
        fora[doi] = {
            "estado": "resolve",
            "ano": partes[0] if partes else None,
            "titulo": (msg.get("title") or [""])[0],
            "primeiro_autor": (msg.get("author") or [{}])[0].get("family", ""),
            "periodico": (msg.get("container-title") or [""])[0],
        }
    return fora
