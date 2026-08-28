#!/usr/bin/env python3
"""Auditoria dos documentos de análise do humor no handebol.

Confere ANALISE_HUMOR_HANDEBOL.docx, DESCRITIVA_HUMOR_HANDEBOL.docx e
ORGANOGRAMA_HUMOR.html contra a biblioteca curada, e verifica se o material
sustenta uma análise do *perfil de humor* dos atletas — que é coisa distinta
de uma análise da *produção científica sobre* humor.

    python3 scripts/humor/auditar_humor.py \
        --painel ORGANOGRAMA_HUMOR.html \
        --db data/BIBLIOTECA_HANDEBOL.sqlite
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import sqlite3
import sys
from pathlib import Path

# Fatores do POMS/BRUMS: é deles que se faz um perfil de humor.
FATORES_HUMOR = {
    "tensão/ansiedade": r"\btension\b|tensao|tensão",
    "depressão": r"\bdepression\b|depressao|depressão",
    "raiva/hostilidade": r"\banger\b|hostilit|raiva",
    "vigor": r"\bvigou?r\b",
    "fadiga": r"\bfatigue\b|fadiga",
    "confusão": r"\bconfusion\b|confusao|confusão",
    "distúrbio total de humor": r"total mood disturbance|\bTMD\b",
    "perfil iceberg": r"iceberg",
}

# Um escore de humor recuperável tem a forma "vigor 18.4 ± 3.2" ou "(18.4;".
ESCORE = re.compile(
    r"(vigou?r|fatigue|tension|depression|anger|confusion|TMD|mood)"
    r"\D{0,25}(\d+[.,]\d+)\s*[±(]", re.I)

ESTATISTICA = {
    "tamanho de efeito": r"effect size|cohen'?s d|eta.?squared|η2|hedges",
    "valor de p": r"\bp\s*[<=>]\s*0?[.,]\d",
    "intervalo de confiança": r"95%\s*(CI|confidence)|IC\s*95",
    "coeficiente de correlação": r"\br\s*=\s*[-−]?0?[.,]\d",
}

achados: list[tuple[str, str]] = []


def anotar(nivel: str, msg: str) -> None:
    achados.append((nivel, msg))


def estudos_do_painel(caminho: Path) -> list[dict]:
    """Extrai a lista de estudos embutida no organograma HTML."""
    h = caminho.read_text(encoding="utf-8")
    m = re.search(r"(?:const|let|var)\s+D\s*=\s*", h)
    if not m:
        raise SystemExit("não encontrei a estrutura de dados D no painel")
    i = m.end()
    profundidade, j = 0, i
    while j < len(h):
        if h[j] in "[{":
            profundidade += 1
        elif h[j] in "]}":
            profundidade -= 1
        if profundidade == 0:
            break
        j += 1
    return json.loads(h[i:j + 1]).get("arts", [])


def casar(con: sqlite3.Connection, estudos: list[dict]) -> tuple[list[int], list[dict]]:
    ids, orfaos = [], []
    for e in estudos:
        r = None
        if e.get("doi"):
            r = con.execute("SELECT id FROM artigo WHERE lower(doi)=?",
                            (e["doi"].lower(),)).fetchone()
        if r is None and e.get("pmid"):
            r = con.execute("SELECT id FROM artigo WHERE pmid=?",
                            (str(e["pmid"]),)).fetchone()
        if r is None:
            r = con.execute("SELECT id FROM artigo WHERE titulo=?", (e["t"],)).fetchone()
        (ids.append(r[0]) if r else orfaos.append(e))
    return ids, orfaos


def auditar(painel: Path, db: Path) -> int:
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    estudos = estudos_do_painel(painel)
    ids, orfaos = casar(con, estudos)
    marcas = ",".join("?" * len(ids))
    print(f"painel: {len(estudos)} estudos; {len(ids)} casados na biblioteca")
    if orfaos:
        anotar("GRAVE", f"{len(orfaos)} estudos do painel não existem na biblioteca: "
                        + "; ".join(o["t"][:50] for o in orfaos[:3]))

    # ── 1 · o corpus é mesmo de humor? ──
    com_marca = {r[0] for r in con.execute(
        f"SELECT artigo_id FROM artigo_subvariavel WHERE subvariavel='Humor / Afeto' "
        f"AND artigo_id IN ({marcas})", ids)}
    sem_marca = set(ids) - com_marca
    if sem_marca:
        for i in sem_marca:
            r = con.execute("SELECT ano, titulo, resumo FROM artigo WHERE id=?", (i,)).fetchone()
            texto = f"{r['titulo']} {r['resumo'] or ''}".lower()
            mencao = any(k in texto for k in ("mood", "humor", "poms", "brums", "affect"))
            anotar("BLOQUEADOR",
                   f"Estudo sem marcação de Humor/Afeto no corpus de {len(ids)}: "
                   f"[{r['ano']}] {r['titulo'][:64]} — "
                   f"{'menciona' if mencao else 'não menciona'} humor no resumo.")

    # ── 2 · delineamentos inelegíveis (Quadro 2 do protocolo) ──
    inel = con.execute(
        f"SELECT ano, tipo_estudo, titulo FROM artigo WHERE id IN ({marcas}) "
        "AND (tipo_estudo LIKE '%evis%' OR tipo_estudo LIKE '%apitulo%' "
        "OR tipo_estudo LIKE '%anais%')", ids).fetchall()
    for r in inel:
        anotar("GRAVE", f"Delineamento excluído pelo Quadro 2 dentro do corpus: "
                        f"[{r['ano']}] {r['tipo_estudo']} — {r['titulo'][:60]}")

    # ── 3 · existe perfil de humor a analisar? ──
    print("\n── fatores de humor nos resumos ──")
    cont = collections.Counter()
    com_fator: set[int] = set()
    for i in ids:
        r = con.execute("SELECT titulo, resumo, sintese FROM artigo WHERE id=?", (i,)).fetchone()
        texto = " ".join(x or "" for x in r)
        for nome, padrao in FATORES_HUMOR.items():
            if re.search(padrao, texto, re.I):
                cont[nome] += 1
                com_fator.add(i)
    for k, v in cont.most_common():
        print(f"   {v:3d}  {k}")
    print(f"   → {len(com_fator)} de {len(ids)} mencionam ao menos um fator")
    if len(com_fator) < len(ids) / 2:
        anotar("BLOQUEADOR",
               f"Apenas {len(com_fator)} dos {len(ids)} estudos mencionam algum fator do "
               "POMS/BRUMS (vigor, fadiga, tensão, depressão, raiva, confusão). Sem esses "
               "fatores não há perfil de humor a descrever — só bibliometria sobre humor.")

    com_escore = sum(1 for i in ids if ESCORE.search(
        con.execute("SELECT coalesce(resumo,'') FROM artigo WHERE id=?", (i,)).fetchone()[0]))
    print(f"   escores de humor com valor recuperável no resumo: {com_escore} de {len(ids)}")
    if com_escore == 0:
        anotar("BLOQUEADOR",
               "Nenhum estudo traz escore de humor com valor no resumo. Qualquer "
               "perfil (média por fator, perfil iceberg, metanálise) depende de "
               "extrair os fatores dos textos completos.")

    print("\n── relato estatístico nos resumos ──")
    for rot, padrao in ESTATISTICA.items():
        n = sum(1 for i in ids if re.search(padrao, con.execute(
            "SELECT coalesce(resumo,'')||' '||coalesce(sintese,'') FROM artigo WHERE id=?",
            (i,)).fetchone()[0], re.I))
        print(f"   {n:3d}/{len(ids)}  {rot}")

    # ── 4 · números que os documentos afirmam ──
    print("\n── contagens reproduzidas da biblioteca ──")
    areas = collections.Counter()
    for aid, v in con.execute(
            f"SELECT artigo_id, variavel FROM artigo_variavel WHERE artigo_id IN ({marcas})", ids):
        if v != "psicologicas":
            areas[v] += 1
    isolados = sum(1 for i in ids if not areas or all(
        v == "psicologicas" for (v,) in con.execute(
            "SELECT variavel FROM artigo_variavel WHERE artigo_id=?", (i,))))
    print(f"   isolado {isolados} · combinado {len(ids) - isolados}")
    for k, v in areas.most_common():
        print(f"   co-ocorrência com {k}: {v}")
    if areas.get("fisicas", 0) > areas.get("fisiologicas", 0):
        anotar("GRAVE",
               f"A co-ocorrência mais frequente é com capacidades físicas "
               f"({areas['fisicas']}), não com variáveis fisiológicas "
               f"({areas['fisiologicas']}). A síntese de ANALISE inverte as duas.")

    subs = collections.Counter()
    for aid, s in con.execute(
            f"SELECT artigo_id, subvariavel FROM artigo_subvariavel WHERE artigo_id IN ({marcas})", ids):
        if s != "Humor / Afeto":
            subs[s] += 1
    top3 = [k for k, _ in subs.most_common(3)]
    print(f"   construtos mais associados: {top3}")
    hab = subs.get("Habilidades mentais", 0)
    if hab and "Habilidades mentais" not in top3:
        anotar("GRAVE",
               f"'Habilidades mentais' aparece em {hab} de {len(ids)} estudos, mas ANALISE "
               f"a nomeia entre as três principais associações. As três reais são: "
               + ", ".join(top3) + ".")

    # ── 5 · amostra ──
    ns = sorted(int(m.group(1)) for i in ids
                if (m := re.search(r"(\d+)", con.execute(
                    "SELECT coalesce(amostra,'') FROM artigo WHERE id=?", (i,)).fetchone()[0])))
    if ns:
        print(f"\n   amostra reportada em {len(ns)} estudos: "
              f"mediana {ns[len(ns) // 2]}, mín {ns[0]}, máx {ns[-1]}, total {sum(ns)}")
        if ns[-1] / sum(ns) > 0.4:
            anotar("GRAVE",
                   f"Um único estudo (n={ns[-1]}) responde por "
                   f"{100 * ns[-1] / sum(ns):.0f}% do total agregado de participantes; "
                   "o total soma populações de desenhos incompatíveis e não deve ser "
                   "reportado como 'participantes da evidência'.")
        if ns[0] <= 2:
            anotar("GRAVE", f"Amostra mínima registrada é n={ns[0]}, valor implausível "
                            "para um estudo de grupo; conferir no texto completo.")

    print("\n== ACHADOS ==")
    ordem = {"BLOQUEADOR": 0, "GRAVE": 1, "NOTA": 2}
    for nivel, msg in sorted(achados, key=lambda a: ordem.get(a[0], 9)):
        print(f"[{nivel:11s}] {msg}")
    n_bloq = sum(1 for n, _ in achados if n == "BLOQUEADOR")
    print(f"\n{len(achados)} achados ({n_bloq} bloqueadores).")
    con.close()
    return 1 if n_bloq else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--painel", type=Path, required=True)
    p.add_argument("--db", type=Path, default=Path("data/BIBLIOTECA_HANDEBOL.sqlite"))
    a = p.parse_args()
    return auditar(a.painel, a.db)


if __name__ == "__main__":
    sys.exit(main())
