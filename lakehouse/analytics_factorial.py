# -*- coding: utf-8 -*-
"""Análise fatorial (fatores observados) — Momento (pré/pós) × Tipo de dia (HIIT/Jogo/Força).

IMPORTANTE — natureza dos dados:
  O estudo é observacional, longitudinal e de grupo único. Não há delineamento
  fatorial experimental (os níveis não foram randomizados nem cruzados por
  desenho): o tipo de dia está confundido com o dia e com a carga acumulada da
  semana. Isto NÃO é um DOE fatorial completo/fracionado — é uma ANÁLISE
  fatorial da variância sobre fatores OBSERVADOS, com as ressalvas registradas
  no payload (confundimento com o tempo, desbalanceamento, potência limitada
  para a interação, esfericidade tratada por GG).

Estrutura 2×3 intra-sujeito (Baseline é só pré → excluído do fator momento):
  - Momento: pré / pós  (intra-sujeito)
  - Tipo de dia: HIIT / Jogo / Força  (intra-sujeito)
  - Resposta: cada dimensão do humor (6 subescalas + PTH + Fadiga física)

Rotas (como no restante do projeto — completo × robusto):
  1. rm-ANOVA de dois fatores intra-sujeito (pingouin), casos completos.
     Reporta F, p, p-GG (Greenhouse-Geisser), e η²p = F·df1/(F·df1+df2).
  2. Modelo misto (statsmodels), todos os atletas, intercepto aleatório por
     atleta — robustez à ausência de células. Teste de Wald conjunto da
     interação (LRT como reserva).

Gera em gold:
  an_fac_cells   — médias por dimensão × tipo de dia × momento (+ EPM) p/ gráfico
  an_fac_rm      — rm-ANOVA (efeitos: momento, tipo de dia, interação) por dimensão
  an_fac_mixed   — modelo misto (p da interação) por dimensão
  an_fac_payload — JSON único para o painel (cells + rm + mixed + ressalvas)
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

SEED = 7
DIMS = [("Vigor", "Vigor"), ("Fadiga", "Fadiga"), ("Tensao", "Tensão"),
        ("Depressao", "Depressão"), ("Raiva", "Raiva"), ("Confusao", "Confusão"),
        ("PTH", "PTH"), ("FadFisica", "Fadiga física")]
DAYS = ["HIIT", "Jogo", "Forca"]
DAYLAB = {"HIIT": "HIIT", "Jogo": "Jogo", "Forca": "Força"}
MOM = ["pre", "pos"]


def _cells(agg):
    """médias e EPM por dimensão × tipo de dia × momento (para o gráfico de interação)."""
    rows = []
    for col, lab in DIMS:
        for dt in DAYS:
            for mo in MOM:
                s = agg[(agg.day_type == dt) & (agg.momento == mo)][col].dropna()
                if len(s) == 0:
                    continue
                rows.append(dict(dim=col, dim_lab=lab, day_type=dt, day_lab=DAYLAB[dt],
                                 momento=mo, media=round(float(s.mean()), 3),
                                 epm=round(float(s.std(ddof=1) / np.sqrt(len(s))), 3),
                                 n=int(len(s))))
    return pd.DataFrame(rows)


def _rm(agg):
    """rm-ANOVA 2×3 intra-sujeito por dimensão (casos completos)."""
    import pingouin as pg
    out = []
    for col, lab in DIMS:
        sub = agg[["ID", "day_type", "momento", col]].dropna().rename(columns={col: "y"})
        # mantém apenas atletas com as 6 células (rm-ANOVA exige balanceamento intra)
        cnt = sub.groupby("ID").size()
        keep = cnt[cnt == len(DAYS) * len(MOM)].index
        sub = sub[sub.ID.isin(keep)]
        n = sub.ID.nunique()
        if n < 5:
            continue
        try:
            aov = pg.rm_anova(data=sub, dv="y", within=["momento", "day_type"],
                              subject="ID", detailed=True)
        except Exception as e:
            print("  rm falhou", col, e); continue
        pcol = "p-unc" if "p-unc" in aov.columns else "p_unc"
        ggcol = "p-GG-corr" if "p-GG-corr" in aov.columns else ("p_GG_corr" if "p_GG_corr" in aov.columns else None)
        for _, r in aov.iterrows():
            src = str(r["Source"])
            F = float(r["F"]); d1 = float(r["ddof1"]); d2 = float(r["ddof2"])
            eta_p = F * d1 / (F * d1 + d2) if (F * d1 + d2) else np.nan
            p = float(r[pcol]); pgg = float(r[ggcol]) if ggcol and pd.notna(r.get(ggcol, np.nan)) else p
            fator = {"momento": "Momento (pré/pós)", "day_type": "Tipo de dia",
                     "momento * day_type": "Momento × Tipo de dia"}.get(src, src)
            out.append(dict(dim=col, dim_lab=lab, fator=fator, n=n,
                            F=round(F, 3), df1=round(d1, 2), df2=round(d2, 2),
                            p=round(p, 4), p_gg=round(pgg, 4),
                            eta2p=round(float(eta_p), 3),
                            mag=("grande" if eta_p >= .14 else "médio" if eta_p >= .06 else "pequeno" if eta_p >= .01 else "trivial"),
                            sig=bool(pgg < 0.05)))
    return pd.DataFrame(out)


def _mixed(agg):
    """modelo misto y ~ momento*tipo de dia, intercepto aleatório por atleta (robustez, todos os atletas)."""
    import statsmodels.formula.api as smf
    out = []
    for col, lab in DIMS:
        sub = agg[["ID", "day_type", "momento", col]].dropna().rename(columns={col: "y"}).copy()
        sub["momento"] = pd.Categorical(sub["momento"], categories=MOM)
        sub["day_type"] = pd.Categorical(sub["day_type"], categories=DAYS)
        n = sub.ID.nunique()
        try:
            m = smf.mixedlm("y ~ C(momento)*C(day_type)", sub, groups=sub["ID"])
            r = m.fit(reml=False, method="lbfgs")
            inter = [t for t in r.params.index if (":" in t)]
            metodo = "misto"
            if inter:
                wt = r.wald_test(_contrast(r.params.index, inter), scalar=True)
                pint = float(wt.pvalue)
            else:
                pint = np.nan
        except Exception as e:
            # reserva: OLS com efeito fixo de atleta
            try:
                import statsmodels.formula.api as smf2
                r = smf2.ols("y ~ C(momento)*C(day_type)+C(ID)", sub).fit()
                inter = [t for t in r.params.index if (":" in t and "ID" not in t)]
                pint = float(r.f_test(_contrast(r.params.index, inter)).pvalue) if inter else np.nan
                metodo = "ols"
            except Exception as e2:
                print("  misto falhou", col, e2); continue
        out.append(dict(dim=col, dim_lab=lab, n=int(n), metodo=metodo,
                        p_interacao=round(float(pint), 4) if pint == pint else None,
                        sig_interacao=bool(pint < 0.05) if pint == pint else False))
    return pd.DataFrame(out)


def _contrast(names, terms):
    """matriz de contraste (linhas 0/1) para testar conjuntamente `terms` = 0."""
    names = list(names)
    R = np.zeros((len(terms), len(names)))
    for i, t in enumerate(terms):
        R[i, names.index(t)] = 1.0
    return R


def run():
    m = lh.read_delta("silver", "mood")
    d = m[m.momento.isin(MOM) & m.day_type.isin(DAYS)].copy()
    agg = d.groupby(["ID", "day_type", "momento"])[[c for c, _ in DIMS]].mean().reset_index()

    cells = _cells(agg)
    rm = _rm(agg)
    mixed = _mixed(agg)

    n_complete = int((agg.groupby("ID").size() == len(DAYS) * len(MOM)).sum())
    payload = {
        "cells": cells.to_dict("records"),
        "rm": rm.to_dict("records"),
        "mixed": mixed.to_dict("records"),
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "days": [{"key": k, "lab": DAYLAB[k]} for k in DAYS],
        "n_total": int(agg.ID.nunique()), "n_complete": n_complete,
        "ressalvas": [
            "Estudo observacional de grupo único: análise fatorial de fatores OBSERVADOS, não delineamento experimental.",
            "Tipo de dia está confundido com o dia e com a carga acumulada (HIIT em D2/D4/D7; jogo em D3/D5; força em D6).",
            "Baseline (D1) é apenas pré e não entra no fator momento.",
            "rm-ANOVA em casos completos (n=" + str(n_complete) + " com as 6 células); modelo misto usa todos (n=" + str(int(agg.ID.nunique())) + ").",
            "Interação de ordem alta com potência limitada; p por Greenhouse-Geisser (esfericidade).",
            "Aptidão aeróbia (PV do T-CAR) não pôde ser cruzada no nível da observação: os códigos do humor (A) e do coorte físico (P) são anonimizados separadamente; a relação PV×humor é reportada à parte (ρ=−0,54).",
        ],
    }
    lh.write_delta("gold", "an_fac_cells", cells); print("[gold] an_fac_cells", cells.shape)
    lh.write_delta("gold", "an_fac_rm", rm); print("[gold] an_fac_rm", rm.shape)
    lh.write_delta("gold", "an_fac_mixed", mixed); print("[gold] an_fac_mixed", mixed.shape)
    lh.write_delta("gold", "an_fac_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_fac_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== rm-ANOVA (efeitos significativos por GG) ===")
    for r in p["rm"]:
        if r["sig"]:
            print(f"  {r['dim_lab']:14} {r['fator']:22} F={r['F']:.2f} p_GG={r['p_gg']:.3f} η²p={r['eta2p']:.3f} ({r['mag']})")
