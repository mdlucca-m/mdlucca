#!/usr/bin/env python3
"""Testes da camada de curadoria: elegibilidade, psicometria, tabelas,
extração e referências.

    python3 scripts/testar_curadoria.py [--db data/BIBLIOTECA_HANDEBOL.sqlite]
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from curadoria import extracao, psicometria, referencias, tabelas
from curadoria.elegibilidade import (JANELA, MOTIVOS, Decisao, avaliar,
                                     fluxo_prisma, triar)

falhas: list[str] = []
aprovados = 0


def conferir(cond: bool, desc: str, detalhe: str = "") -> None:
    global aprovados
    if cond:
        aprovados += 1
        print(f"  ✓ {desc}")
    else:
        print(f"  ✗ {desc}" + (f" → {detalhe}" if detalhe else ""))
        falhas.append(desc)


CAMPOS = ("id", "titulo", "resumo", "palavras_chave", "ano", "tipo_estudo",
          "desenho_estudo", "pcc_contexto", "populacao", "autores", "revista",
          "volume", "numero", "paginas", "doi", "doi_suspeito", "amostra")


def registro(**kw) -> dict:
    base = {c: "" for c in CAMPOS}
    base |= {"id": 1, "ano": "2020", "tipo_estudo": "Estudo original (empirico)",
             "doi_suspeito": 0}
    base |= kw
    return base


def main(db: Path) -> int:
    print("── dicionário psicométrico ──")
    conferir(len(psicometria.INSTRUMENTOS) >= 60,
             f"{len(psicometria.INSTRUMENTOS)} instrumentos no dicionário")
    conferir(all(i.familia in psicometria.FAMILIAS for i in psicometria.INSTRUMENTOS),
             "toda entrada aponta para uma família válida")
    achados = psicometria.detectar("Anxiety in handball", "The CSAI-2R was applied", "")
    conferir([i.canonico for i in achados] == ["CSAI-2 / CSAI-2R"],
             "detecta CSAI-2R pelo acrônimo", str([i.canonico for i in achados]))
    conferir(psicometria.detectar("", "instrumento de avaliacao em diferentes esportes, "
                                      "tais como o futebol e o handebol", "") == [],
             "não confunde o português 'tais como' com o TAIS")
    conferir(psicometria.detectar("", "Escala de motivacao (SMS/TEOSQ)", "") == [],
             "rótulo agregado da biblioteca não nomeia instrumento")
    conferir(psicometria.detectar_psicofisicos("", "Borg RPE scale was used", "") != [],
             "PSE/Borg reconhecida como psicofísica")
    conferir(not any(i.canonico.startswith("PSE") for i in psicometria.INSTRUMENTOS),
             "PSE/Borg não consta como instrumento psicométrico")

    print("\n── elegibilidade ──")
    caso = lambda **kw: avaliar(registro(**kw), set())
    d = caso(ano="1998", titulo="handball anxiety", resumo="STAI")
    conferir(d.motivo == MOTIVOS[0], "exclui fora da janela temporal", d.motivo)
    d = caso(titulo="Anxiety in volleyball players", resumo="STAI applied")
    conferir(d.motivo == MOTIVOS[1], "exclui população que não é de handebol", d.motivo)
    d = caso(titulo="Anxiety in handball", resumo="STAI", tipo_estudo="Revisao sistematica")
    conferir(d.motivo == MOTIVOS[4], "exclui delineamento inelegível", d.motivo)
    conferir("revisão sistemática" in d.detalhe, "detalha qual delineamento")
    d = caso(titulo="Jump height in handball players", resumo="CMJ and sprint times")
    conferir(d.motivo == MOTIVOS[2], "exclui quem não afere variável psicológica", d.motivo)
    d = avaliar(registro(titulo="Handball load monitoring", resumo="session RPE"),
                {"Percepcao de esforco"})
    conferir(d.motivo == MOTIVOS[2] and "psicofísica" in d.detalhe,
             "percepção de esforço sozinha não sustenta elegibilidade", d.detalhe)
    d = caso(titulo="Anxiety in handball players", resumo="The CSAI-2R was applied")
    conferir(d.incluido and d.evidencia == "instrumento nomeado",
             "inclui com instrumento nomeado")
    conferir(d.familias == {"ansiedade e estresse"}, "família vem do instrumento",
             str(d.familias))
    d = avaliar(registro(titulo="Motivation in handball", resumo="motivation was assessed"),
                {"Motivacao"})
    conferir(d.incluido and d.evidencia == "construto no resumo",
             "inclui por construto, marcando a evidência mais fraca")
    d = avaliar(registro(titulo="Handball players anxiety", resumo="STAI",
                         pcc_contexto="Laboratorio", populacao=""), set())
    conferir(d.motivo == MOTIVOS[3], "exclui contexto exclusivamente laboratorial", d.motivo)
    d = avaliar(registro(titulo="Handball anxiety", resumo="STAI",
                         pcc_contexto="Laboratorio; Competicao/jogo"), set())
    conferir(d.incluido, "laboratório com vínculo competitivo permanece elegível")
    d = avaliar(registro(titulo="Handball anxiety", resumo="STAI", pcc_contexto=""), set())
    conferir(d.incluido, "campo de contexto vazio não exclui (evidência ausente)")

    print("\n── referências (NBR 6023) ──")
    ref = referencias.formatar(registro(
        autores="Walter Staiano, Line Maj Sorensen", titulo="Overcoming mental fatigue",
        revista="Journal of Science and Medicine in Sport", ano="2026",
        volume="29", numero="1", paginas="91-99", doi="10.1016/j.jsams.2025.08.004"))
    conferir(".." not in ref.texto(), "sem ponto duplo", ref.texto()[:60])
    conferir(ref.periodico == "Journal of Science and Medicine in Sport",
             "periódico isolado para o itálico", ref.periodico)
    conferir(ref.antes.startswith("STAIANO, W.; SORENSEN, L. M."),
             "autores em versalete com iniciais", ref.antes[:40])
    conferir(ref.alerta == "", "referência completa não gera alerta", ref.alerta)
    quatro = referencias.autores_abnt("A Silva, B Souza, C Lima, D Costa")
    conferir(quatro.endswith("et al.") and quatro.startswith("SILVA"),
             "mais de três autores viram 'et al.'", quatro)
    r2 = referencias.formatar(registro(autores="X Y", titulo="T", revista="R",
                                       ano="2026", doi="10.1016/j.jsams.2006.03.027"))
    conferir("diverge" in r2.alerta, "alerta de ano do DOI divergente", r2.alerta)
    r3 = referencias.formatar(registro(autores="X Y", titulo="T", revista="R",
                                       ano="2020", doi="nao-e-um-doi"))
    conferir("malformado" in r3.alerta, "alerta de DOI malformado", r3.alerta)
    r4 = referencias.formatar(registro(autores="X Y", titulo="T", revista="R",
                                       ano="2020", doi="10.1234/ok", volume=""))
    conferir("sem volume" in r4.alerta, "alerta de referência incompleta", r4.alerta)

    print("\n── extração (Apêndice B) ──")
    alertas: list[str] = []
    conferir(extracao._amostra("n = 2022", alertas) == "a conferir" and alertas,
             "tamanho amostral igual a ano-calendário vira 'a conferir'")
    conferir(extracao._amostra("n = 56", []) == "56", "amostra normal é preservada")
    a2: list[str] = []
    conferir(extracao._idade("feminino; Jovem/Base; ~82 anos", a2) == "a conferir" and a2,
             "idade implausível vira 'a conferir'")
    conferir(extracao._idade("masculino; ~15.3 anos", []) == "15.3 anos",
             "idade plausível é preservada")
    conferir(extracao._sexo_e_nivel("feminino; Elite/Internacional")
             == ("feminino", "elite/internacional"), "sexo e nível separados")
    curto = extracao._encurtar("Um título curto")
    longo = extracao._encurtar("A" * 30 + " palavra " + "B" * 60, 40)
    conferir(curto == "Um título curto", "título curto intacto")
    conferir(longo.endswith("[…]") and not longo.endswith("B[…]"),
             "corte em fronteira de palavra, nunca no meio", longo)

    print("\n── integração com a biblioteca ──")
    if not db.exists():
        print(f"  (biblioteca ausente em {db}; testes de integração pulados)")
    else:
        con = sqlite3.connect(db)
        decisoes = triar(con)
        f = fluxo_prisma(decisoes)
        conferir(f["avaliados"] == sum(
            [f["incluidos"]] + list(f["por_motivo"].values())),
            "incluídos + excluídos por motivo = total avaliado",
            f"{f['avaliados']} vs {f['incluidos']} + {sum(f['por_motivo'].values())}")
        conferir(sum(f["por_evidencia"].values()) == f["incluidos"],
                 "todo incluído tem exatamente uma evidência declarada")
        inc = [d for d in decisoes if d.incluido]
        anos = dict(con.execute("SELECT id, ano FROM artigo"))
        conferir(all(JANELA[0] <= int(anos[d.id]) <= JANELA[1] for d in inc),
                 "nenhum incluído fora da janela declarada")
        conferir(all(d.familias for d in inc),
                 "todo incluído tem ao menos uma família de construto")

        t = {x.numero: x for x in tabelas.todas(con, decisoes)}
        base_t4 = round(int(t[4].linhas[0][1]) /
                        (float(t[4].linhas[0][2].replace(",", ".")) / 100))
        conferir(base_t4 == len(inc),
                 "base implícita nos percentuais da Tabela 4 = corpus elegível",
                 f"{base_t4} vs {len(inc)}")
        conferir(str(len(inc)) in t[4].nota, "Tabela 4 declara sua base na nota")
        nao_psico = ("agilidade", "jump", "sprint", "salivar", "lactato", "DXA", "GPS")
        conferir(not any(p in l[0].lower() for l in t[5].linhas for p in nao_psico),
                 "Tabela 5 não contém instrumento físico ou fisiológico")
        conferir(all(l[1] in psicometria.FAMILIAS for l in t[5].linhas),
                 "todo instrumento da Tabela 5 declara a família do construto")
        conferir("Polônia" in [l[0] for l in t[6].linhas]
                 or "Tunísia" in [l[0] for l in t[6].linhas],
                 "Tabela 6 traz países acentuados")

        linhas = extracao.montar(con, decisoes)
        conferir(len(linhas) == len(inc), "Apêndice B cobre todo o corpus elegível")

        # Achado B6: 49 das 80 linhas da versão anterior divergiam da base
        # quanto ao n. Aqui a conferência é feita linha a linha.
        import re
        amostras = dict(con.execute("SELECT id, amostra FROM artigo"))
        por_titulo = {tit[:60]: i for i, tit in
                      con.execute("SELECT id, titulo FROM artigo")}
        divergentes = 0
        for l in linhas:
            if l.n in ("n.d.", "a conferir"):
                continue
            chave = next((k for k in por_titulo if k.startswith(l.estudo[:40])), None)
            if chave is None:
                continue
            bruto = amostras.get(por_titulo[chave]) or ""
            m = re.search(r"(\d+)", bruto)
            if m and m.group(1) != l.n:
                divergentes += 1
        conferir(divergentes == 0,
                 "nenhuma linha do Apêndice B diverge da base quanto ao n",
                 f"{divergentes} divergentes")
        conferir(all(l.instrumentos != "" and l.construtos != "" for l in linhas),
                 "nenhuma célula de instrumento ou construto sai vazia")
        con.close()

    if falhas:
        print(f"\nFALHOU: {len(falhas)} de {len(falhas) + aprovados} verificações")
        for f_ in falhas:
            print(f"   · {f_}")
        return 1
    print(f"\nOK: {aprovados} verificações passaram")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", type=Path, default=Path("data/BIBLIOTECA_HANDEBOL.sqlite"))
    sys.exit(main(ap.parse_args().db))
