# -*- coding: utf-8 -*-
"""Mapa de multiplicidade — correção de comparações múltiplas unificada.

Ao longo do estudo muitos testes foram conduzidos. Este módulo reúne a FAMÍLIA
CONFIRMATÓRIA PRIMÁRIA (a variação semanal do humor) num único quadro e aplica,
de forma explícita e uniforme, duas correções:
  - Benjamini-Hochberg (FDR): controla a proporção esperada de falsos positivos;
  - Bonferroni: controla a probabilidade de qualquer falso positivo (conservador).

Família primária:
  - Wilcoxon do primeiro contra o último dia (D1 vs D7), por dimensão (7 testes);
  - Friedman dos sete dias, por dimensão (7 testes).

A correção é feita dentro de cada família e no conjunto (14 testes), o que
torna transparente quais achados sobrevivem à multiplicidade. Efeitos afetivos
pequenos tendem a não sobreviver, o que reforça a leitura por tendência.

Gera em gold: an_multiplicity, an_mult_payload
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

LAB = {"vigor": "Vigor", "fadiga": "Fadiga", "tensao": "Tensão", "depressao": "Depressão",
       "raiva": "Raiva", "confusao": "Confusão", "pth": "PTH"}


def _adj(pvals):
    from statsmodels.stats.multitest import multipletests
    p = np.asarray(pvals, float)
    fdr = multipletests(p, alpha=0.05, method="fdr_bh")[1]
    bon = multipletests(p, alpha=0.05, method="bonferroni")[1]
    return fdr, bon


def run():
    d17 = lh.read_delta("gold", "an_d17").set_index("var")
    fri = lh.read_delta("gold", "an_friedman").set_index("var")
    rows = []
    for k in ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao", "pth"]:
        if k in d17.index:
            rows.append(dict(familia="Wilcoxon D1 vs D7", dim=k, dim_lab=LAB[k], teste="Wilcoxon",
                             p=float(d17.loc[k, "p_wilcoxon"]), efeito=float(d17.loc[k, "dz"])))
        if k in fri.index:
            rows.append(dict(familia="Friedman (7 dias)", dim=k, dim_lab=LAB[k], teste="Friedman",
                             p=float(fri.loc[k, "p"]), efeito=float(fri.loc[k, "W"])))
    df = pd.DataFrame(rows)

    # correção dentro de cada família
    df["p_fdr"] = np.nan; df["p_bonf"] = np.nan
    for fam, g in df.groupby("familia"):
        fdr, bon = _adj(g["p"].values)
        df.loc[g.index, "p_fdr"] = fdr
        df.loc[g.index, "p_bonf"] = bon
    # correção conjunta (todas as 14)
    fdr_all, bon_all = _adj(df["p"].values)
    df["p_fdr_geral"] = fdr_all; df["p_bonf_geral"] = bon_all

    df["sig_bruto"] = df["p"] < 0.05
    df["sig_fdr"] = df["p_fdr"] < 0.05
    df["sig_bonf"] = df["p_bonf"] < 0.05
    df = df.round(4)

    recs = []
    for r in df.itertuples():
        recs.append(dict(familia=r.familia, dim=r.dim, dim_lab=r.dim_lab, teste=r.teste,
                         p=r.p, p_fdr=r.p_fdr, p_bonf=r.p_bonf,
                         efeito=r.efeito, sig_bruto=bool(r.sig_bruto),
                         sig_fdr=bool(r.sig_fdr), sig_bonf=bool(r.sig_bonf)))
    n_bruto = int(df["sig_bruto"].sum()); n_fdr = int(df["sig_fdr"].sum()); n_bonf = int(df["sig_bonf"].sum())
    payload = {
        "tests": recs, "n_total": int(len(df)),
        "n_bruto": n_bruto, "n_fdr": n_fdr, "n_bonf": n_bonf,
        "familias": sorted(df["familia"].unique().tolist()),
        "sobrevivem_fdr": sorted(set(df[df["sig_fdr"]]["dim_lab"].tolist())),
        "notas": [
            "Família confirmatória primária: Wilcoxon D1 vs D7 (7) e Friedman dos 7 dias (7); correção dentro de cada família (Benjamini-Hochberg e Bonferroni).",
            "FDR controla a proporção esperada de falsos positivos; Bonferroni controla a chance de qualquer falso positivo (mais conservador).",
            "Do total de " + str(len(df)) + " testes, " + str(n_bruto) + " são significativos sem correção, " + str(n_fdr) + " sobrevivem ao FDR e " + str(n_bonf) + " ao Bonferroni.",
            "Os efeitos que sobrevivem concentram-se no eixo energético (vigor e fadiga) e em algumas dimensões com padrão semanal forte; os afetivos pequenos não sobrevivem, o que reforça a leitura por tendência convergente.",
        ],
    }
    lh.write_delta("gold", "an_multiplicity", df); print("[gold] an_multiplicity", df.shape)
    lh.write_delta("gold", "an_mult_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_mult_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print(f"\n=== mapa de multiplicidade ({p['n_total']} testes) ===")
    print(f"  significativos: bruto {p['n_bruto']} · FDR {p['n_fdr']} · Bonferroni {p['n_bonf']}")
    for t in p["tests"]:
        if t["sig_bruto"]:
            fl = ("FDR" if t["sig_fdr"] else "   ") + ("+Bonf" if t["sig_bonf"] else "     ")
            print(f"  {t['teste']:9} {t['dim_lab']:10} p={t['p']:.3f} -> pFDR={t['p_fdr']:.3f} [{fl}]")
