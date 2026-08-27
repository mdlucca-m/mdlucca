#!/usr/bin/env python3
"""Teste ponta a ponta da camada de busca, sem rede.

Alimenta os normalizadores com respostas gravadas das três APIs e verifica
parsing, deduplicação cruzada entre bases e gravação incremental no SQLite.

    python3 scripts/testar_busca.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))

from busca import deposito, estrategia
from busca.normalizar import chave_titulo, deduplicar, normalizar, normalizar_doi

FIX = Path(__file__).resolve().parent / "busca" / "fixtures"
falhas: list[str] = []
aprovados = 0


def conferir(condicao: bool, descricao: str, detalhe: str = "") -> None:
    global aprovados
    if condicao:
        aprovados += 1
        print(f"  ✓ {descricao}")
    else:
        print(f"  ✗ {descricao}" + (f" → {detalhe}" if detalhe else ""))
        falhas.append(descricao)


def carregar() -> list[dict]:
    """Reproduz o que cada cliente entrega ao normalizador."""
    brutos = []
    raiz = ET.fromstring((FIX / "pubmed_efetch.xml").read_bytes())
    for art in raiz.findall(".//PubmedArticle"):
        brutos.append({"_fonte": "PubMed", "_xml": art})

    sc = json.loads((FIX / "scopus_search.json").read_text())
    for e in sc["search-results"]["entry"]:
        brutos.append({"_fonte": "Scopus", "_view": "COMPLETE", **e})

    st = json.loads((FIX / "wos_starter.json").read_text())
    for h in st["hits"]:
        brutos.append({"_fonte": "Web of Science", "_api": "starter", **h})

    ex = json.loads((FIX / "wos_expanded.json").read_text())
    for r in ex["QueryResult"] and ex["Data"]["Records"]["records"]["REC"]:
        brutos.append({"_fonte": "Web of Science", "_api": "expanded", **r})
    return brutos


def main() -> int:
    print("── estratégia ──")
    r = estrategia.resumo()
    conferir(r["conceito_mesh"] == 16 and r["conceito_livre"] == 62,
             "bloco de conceito: 16 descritores MeSH + 62 termos livres", str(r))
    conferir(r["contexto_mesh"] == 6 and r["contexto_livre"] == 27,
             "bloco de contexto: 6 descritores + 27 termos livres", str(r))
    conferir(r["populacao_livre"] == 16 and r["conceito_decs"] == 15,
             "população: 16 termos livres; DeCS: 15 descritores", str(r))
    for nome, fn in estrategia.CONSULTAS.items():
        q = fn()
        conferir(q.count("(") == q.count(")"), f"{nome}: parênteses balanceados")
        conferir(" AND " in q and " OR " in q, f"{nome}: operadores presentes")
    conferir("PUBYEAR" in estrategia.scopus(), "scopus: janela temporal na consulta")
    conferir('"Stress, Psychological"' not in estrategia.scopus(),
             "scopus: não usa MeSH invertido em KEY() (achado da revisão)")

    print("\n── esquema ──")
    import gerar_schema
    arquivo = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    conferir(arquivo.exists() and arquivo.read_text() == gerar_schema.conteudo(),
             "sql/schema.sql em dia com o DDL de deposito.py "
             "(regenere com scripts/gerar_schema.py)")
    with tempfile.TemporaryDirectory() as t:
        c = sqlite3.connect(Path(t) / "s.sqlite")
        c.executescript(arquivo.read_text())
        objetos = {r[0] for r in c.execute(
            "SELECT name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        conferir("artigo" in objetos, "schema.sql cria a tabela artigo")
        conferir({"busca_execucao", "busca_rendimento", "busca_duplicata"} <= objetos,
                 "schema.sql cria as tabelas de proveniência")
        c.close()

    print("\n── normalização ──")
    registros = [normalizar(b) for b in carregar()]
    conferir(len(registros) == 7, "7 registros normalizados das 3 bases", str(len(registros)))

    swidwa = next(r for r in registros if "Temperament" in r["titulo"] and r["fonte"] == "PubMed")
    conferir(swidwa["pmid"] == "42461857", "pubmed: PMID")
    conferir(swidwa["doi"] == "10.1371/journal.pone.0353879", "pubmed: DOI normalizado")
    conferir(swidwa["pmcid"] == "PMC13375019", "pubmed: PMCID")
    conferir(swidwa["ano"] == "2026" and swidwa["volume"] == "21" and swidwa["numero"] == "7",
             "pubmed: ano, volume e número")
    conferir(swidwa["paginas"] == "e0353879", "pubmed: paginação de e-locator")
    conferir(swidwa["autores"].startswith("Jacek Świdwa"), "pubmed: autores com diacríticos")
    conferir(swidwa["pais"] == "Polônia", "pubmed: país deduzido da afiliação", swidwa["pais"])
    conferir("BACKGROUND:" in swidwa["resumo"] and "RESULTS:" in swidwa["resumo"],
             "pubmed: resumo estruturado com rótulos preservados")
    conferir("decision-making" in swidwa["palavras_chave"], "pubmed: palavras-chave")

    skarb = next(r for r in registros if "Integrated monitoring" in r["titulo"] and r["fonte"] == "PubMed")
    conferir(skarb["pais"] == "Lituânia", "pubmed: país (autor único)", skarb["pais"])

    sc_swidwa = next(r for r in registros if r["fonte"] == "Scopus" and "Temperament" in r["titulo"])
    conferir(sc_swidwa["citacoes"] == 4, "scopus: contagem de citações como inteiro")
    conferir(sc_swidwa["pais"] == "Polônia", "scopus: país da afiliação", sc_swidwa["pais"])
    conferir(sc_swidwa["palavras_chave"] == "decision-making, handball referees, temperament",
             "scopus: authkeywords separadas por barra vertical")
    conferir(sc_swidwa["link"].startswith("https://www.scopus.com"), "scopus: link preferencial")

    wos_st = next(r for r in registros if r["fonte"] == "Web of Science" and "Integrated" in r["titulo"])
    conferir(wos_st["pmid"] == "42421841", "wos starter: prefixo MEDLINE: removido do PMID")
    conferir(wos_st["citacoes"] == 2, "wos starter: citações")
    conferir(wos_st["paginas"] == "1869707-1869707", "wos starter: intervalo de páginas")

    wos_ex = next(r for r in registros if "Endocrine" in r["titulo"])
    conferir(wos_ex["revista"] == "SPORTS", "wos expanded: título da fonte vs título do item")
    conferir(wos_ex["titulo"].startswith("Associations Between Endocrine"),
             "wos expanded: título do item")
    conferir(wos_ex["doi"] == "10.3390/sports14070289", "wos expanded: DOI")
    conferir(wos_ex["pmid"] == "42506832", "wos expanded: PMID")
    conferir(wos_ex["pais"] == "Hungria", "wos expanded: país do endereço", wos_ex["pais"])
    conferir("endocrine status" in wos_ex["resumo"], "wos expanded: resumo")

    conferir(normalizar_doi("https://doi.org/10.1234/ABC.") == "10.1234/abc",
             "doi: prefixo de URL, caixa e ponto final")
    conferir(chave_titulo("Ação: um Estudo!") == "acaoumestudo", "título: chave normalizada")

    print("\n── deduplicação ──")
    # Os 7 registros carregam 5 DOIs distintos: Świdwa aparece em PubMed e Scopus,
    # e Skarbalius em PubMed e WoS Starter.
    unicos, dups = deduplicar(registros)
    conferir(len(unicos) == 5, "7 identificados → 5 únicos", f"{len(unicos)} únicos")
    conferir(len(dups) == 2, "2 duplicatas detectadas", f"{len(dups)}")
    conferir(sorted(d["_criterio"] for d in dups) == ["doi", "doi"],
             "ambas casadas por DOI, o critério mais confiável")

    # Os outros dois critérios do protocolo (§3.11), exercitados isoladamente.
    base = {"doi": "", "pmid": "", "titulo": "", "ano": "2026", "fonte": "PubMed",
            "resumo": "", "citacoes": None}
    so_pmid, _ = deduplicar([
        {**base, "pmid": "42461857", "titulo": "Registro sem DOI", "fonte": "PubMed"},
        {**base, "pmid": "42461857", "titulo": "Registro sem DOI", "fonte": "Scopus",
         "resumo": "veio do Scopus"}])
    conferir(len(so_pmid) == 1 and so_pmid[0]["resumo"] == "veio do Scopus",
             "dedup por PMID quando falta o DOI, com fusão de campos")

    so_titulo, dt = deduplicar([
        {**base, "titulo": "Anxiety and mood in elite handball goalkeepers", "fonte": "LILACS"},
        {**base, "titulo": "ANXIETY AND MOOD IN ELITE HANDBALL GOALKEEPERS!", "fonte": "Scopus"}])
    conferir(len(so_titulo) == 1 and dt[0]["_criterio"] == "titulo",
             "dedup por título normalizado quando faltam ambos os identificadores")

    curto, _ = deduplicar([{**base, "titulo": "Handebol"}, {**base, "titulo": "Handebol"}])
    conferir(len(curto) == 2,
             "título curto demais não dispara fusão (evita falso positivo)")

    fundido = next(r for r in unicos if "Integrated monitoring" in r["titulo"])
    conferir(fundido["fonte"] == "PubMed; Web of Science",
             "fusão registra as duas bases de origem", fundido["fonte"])
    conferir(fundido["resumo"] != "" and fundido["citacoes"] == 2,
             "fusão herda resumo do PubMed e citações do WoS")

    swid_u = next(r for r in unicos if "Temperament" in r["titulo"])
    conferir(swid_u["citacoes"] == 4 and swid_u["pmcid"] == "PMC13375019",
             "fusão PubMed+Scopus completa citações e PMCID")

    print("\n── gravação incremental ──")
    with tempfile.TemporaryDirectory() as tmp:
        db = Path(tmp) / "lib.sqlite"
        con = deposito.conectar(db)
        novos, atualizados = deposito.gravar(con, unicos)
        conferir((novos, atualizados) == (5, 0), "primeira carga: 5 novos", f"{novos}/{atualizados}")

        novos2, atual2 = deposito.gravar(con, unicos)
        conferir((novos2, atual2) == (0, 0), "recarga idempotente: nada muda", f"{novos2}/{atual2}")
        total = con.execute("SELECT COUNT(*) FROM artigo").fetchone()[0]
        conferir(total == 5, "sem duplicação na recarga", str(total))

        parcial = dict(unicos[0])
        parcial["citacoes"] = 99
        parcial["resumo"] = ""
        parcial["fonte"] = "LILACS"
        n3, a3 = deposito.gravar(con, [parcial])
        linha = con.execute("SELECT * FROM artigo WHERE doi=?", (parcial["doi"],)).fetchone()
        conferir((n3, a3) == (0, 1), "registro conhecido é atualizado, não duplicado")
        conferir(linha["citacoes"] == 99, "citações maiores substituem as menores")
        conferir("LILACS" in linha["fonte"] and "PubMed" in linha["fonte"],
                 "nova base é acrescentada ao campo fonte", linha["fonte"])
        conferir(linha["resumo"] != "", "campo preenchido não é apagado por valor vazio")

        con.execute("UPDATE artigo SET sintese='curadoria manual' WHERE doi=?", (parcial["doi"],))
        con.commit()
        deposito.gravar(con, [parcial])
        conferir(con.execute("SELECT sintese FROM artigo WHERE doi=?",
                             (parcial["doi"],)).fetchone()[0] == "curadoria manual",
                 "campos de curadoria não são tocados pela busca")

        eid = deposito.registrar_execucao(
            con, janela=(2006, 2026),
            rendimento={"PubMed": {"declarados": 300, "recuperados": 2, "erro": None},
                        "Scopus": {"declarados": 700, "recuperados": 2, "erro": None},
                        "Web of Science": {"declarados": None, "recuperados": None,
                                           "erro": "WOS_API_KEY não definida"}},
            duplicatas=dups, unicos=len(unicos), novos=novos, atualizados=atualizados,
            duracao_s=42, consultas={k: v() for k, v in estrategia.CONSULTAS.items()})
        conferir(eid == 1, "execução registrada com proveniência")
        nd = con.execute("SELECT COUNT(*) FROM busca_duplicata WHERE execucao_id=?",
                         (eid,)).fetchone()[0]
        conferir(nd == 2, "duplicatas gravadas com o critério que as identificou", str(nd))

        tabela = deposito.tabela_rendimento(con, eid)
        conferir("| **Total** | **4** |" in tabela, "Tabela 1 gerada dos dados", tabela)
        conferir("WOS_API_KEY" in tabela, "base sem chave aparece com a observação")
        print("\n" + tabela)
        con.close()

    if falhas:
        print(f"\nFALHOU: {len(falhas)} de {len(falhas) + aprovados} verificações")
        for f in falhas:
            print(f"   · {f}")
        return 1
    print(f"\nOK: {aprovados} verificações passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
