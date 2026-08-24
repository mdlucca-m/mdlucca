# -*- coding: utf-8 -*-
"""GOLD · TRIANGULAÇÃO — estímulo (HIIT × jogo) × resposta (humor, sono, estresse).

Cruza vários métodos para a mesma pergunta: quais variáveis são mais sensíveis e
responsivas a cada estímulo, como se comportam na semana, e como os perfis se
ligam a sono/estresse por tipo de dia. Tudo reprodutível (Delta) e testado.

Tabelas (an_tri_*):
  an_tri_acute       efeito agudo pré→pós por variável × tipo de dia (dz, p)
  an_tri_contrast    contraste HIIT vs jogo por variável (dz, p, FDR)
  an_tri_cv          coeficiente de variação (total, intra-dia, semana) + ICC
  an_tri_prof_day    prevalência de cada perfil por dia (1..7)
  an_tri_wb_daytype  sono/estresse por tipo de dia + contraste HIIT×jogo
  an_tri_wb_profile  sono/estresse por grupo de perfil (favorável/neutro/risco) + Kruskal
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from scipy import stats
import lh

VARS = [("vigor", "Vigor", "Vigor"), ("fadiga", "Fadiga", "Fadiga"),
        ("fadfisica", "FadFisica", "Fadiga física"), ("tensao", "Tensao", "Tensão"),
        ("depressao", "Depressao", "Depressão"), ("raiva", "Raiva", "Raiva"),
        ("confusao", "Confusao", "Confusão"), ("pth", "PTH", "PTH")]
CAT = {"HIIT": "HIIT", "Jogo": "Jogo", "Baseline": "Outro", "Forca": "Outro"}
SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
NAMES = list(CENT); CM = np.array([CENT[k] for k in NAMES])
ACC = {"Iceberg": "Iceberg", "Superficie": "Superfície", "Submerso": "Submerso",
       "Everest invertido": "Everest invertido", "Barbatana de tubarao": "Barbatana de tubarão",
       "Iceberg invertido": "Iceberg invertido"}


def _mag(dz):
    a = abs(dz)
    return "grande" if a >= .8 else "médio" if a >= .5 else "pequeno" if a >= .2 else "trivial"


def _dz_p(a, b):
    j = pd.concat([a, b], axis=1).dropna(); j.columns = ["a", "b"]
    d = j["b"] - j["a"]
    if len(j) < 5 or d.std(ddof=1) == 0:
        return np.nan, np.nan
    return float(d.mean() / d.std(ddof=1)), float(stats.wilcoxon(j["a"], j["b"]).pvalue)


def _classify(df, cols=SUB, mu=None, sd=None):
    Z = (df[cols] - (mu if mu is not None else df[cols].mean())) / (sd if sd is not None else df[cols].std())
    return Z.apply(lambda r: NAMES[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)


def an_tri_acute(m):
    m = m.copy(); m["cat"] = m["day_type"].map(CAT)
    rows = []
    for key, col, lab in VARS:
        for c in ["HIIT", "Jogo", "Outro"]:
            sub = m[m.cat == c]
            pre = sub[sub.is_pre].groupby("ID")[col].mean(); pos = sub[sub.is_pos].groupby("ID")[col].mean()
            dz, p = _dz_p(pre, pos)
            rows.append(dict(var=key, lab=lab, tipo=c, pre=round(float(pre.mean()), 2),
                             pos=round(float(pos.mean()), 2),
                             dz=round(dz, 2) if not np.isnan(dz) else 0.0,
                             p=round(p, 3) if not np.isnan(p) else 1.0,
                             sig=bool((not np.isnan(p)) and p < .05)))
    return pd.DataFrame(rows)


def an_tri_contrast(m):
    """HIIT (D2,D4) vs jogo (D3,D5), pareado por atleta; dz, p e FDR (8 variáveis)."""
    rows = []
    for key, col, lab in VARS:
        hi = m[m.dia.isin([2, 4])].groupby("ID")[col].mean()
        jo = m[m.dia.isin([3, 5])].groupby("ID")[col].mean()
        dz, p = _dz_p(jo, hi)  # hi - jo
        rows.append(dict(var=key, lab=lab, media_hiit=round(float(hi.mean()), 2),
                         media_jogo=round(float(jo.mean()), 2), dz=round(dz, 2), p=round(p, 3),
                         magnitude=_mag(dz)))
    df = pd.DataFrame(rows)
    pv = df["p"].values; o = np.argsort(pv); rk = np.empty_like(o); rk[o] = np.arange(1, len(pv) + 1)
    fdr = np.minimum.accumulate((pv * len(pv) / rk)[o][::-1])[::-1]; adj = np.empty_like(fdr); adj[o] = np.clip(fdr, 0, 1)
    df["fdr"] = np.round(adj, 3); df["sig_fdr"] = df["fdr"] < .05
    return df


def an_tri_cv(m):
    """CV total, intra-dia (pré↔pós) e entre dias (semana), + ICC(2,1) por variável."""
    import pingouin as pg
    rows = []
    for key, col, lab in VARS:
        allv = m[col]; mean = float(allv.mean()); cv_tot = round(100 * float(allv.std()) / mean, 1) if mean else 0
        # intra-dia: DP entre respostas do mesmo atleta-dia / média do dia (média dos dias)
        gd = m.groupby(["ID", "dia"])[col]
        cv_intra = round(float((gd.std() / gd.mean().replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).mean()) * 100, 1)
        # entre dias: DP das médias diárias do grupo / média
        dg = m.groupby("dia")[col].mean(); cv_week = round(100 * float(dg.std()) / float(dg.mean()), 1) if dg.mean() else 0
        try:
            ad = m.groupby(["ID", "dia"])[col].mean().reset_index()
            w = ad.pivot_table(index="ID", columns="dia", values=col).dropna()
            lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
            icc = round(float(pg.intraclass_corr(data=lg, targets="ID", raters="dia", ratings="v")
                              .query("Type=='ICC(A,1)'").ICC.iloc[0]), 2)
        except Exception:
            icc = 0.0
        rows.append(dict(var=key, lab=lab, media=round(mean, 2), cv_total=cv_tot,
                         cv_intradia=cv_intra, cv_semana=cv_week, icc=icc))
    return pd.DataFrame(rows)


def an_tri_prof_day(m):
    mu, sd = m[SUB].mean(), m[SUB].std()
    m = m.copy(); m["perfil"] = _classify(m, mu=mu, sd=sd).values
    rows = []
    for d in range(1, 8):
        sub = m[m.dia == d]; vc = sub["perfil"].value_counts(normalize=True).mul(100)
        for nm in NAMES:
            rows.append(dict(dia=d, perfil=ACC[nm], pct=round(float(vc.get(nm, 0.0)), 1)))
    return pd.DataFrame(rows)


def an_tri_wb_daytype(wb, m):
    dtype = m.groupby("dia")["day_type"].first().map(CAT)
    w = wb.copy(); w["cat"] = w["dia"].map(dtype)
    rows = []
    for c in ["epworth", "pss"]:
        r = {k: round(float(w[w.cat == k][c].mean()), 1) for k in ["Outro", "HIIT", "Jogo"]}
        hi = w[w.dia.isin([2, 4, 7])].groupby("ID")[c].mean(); jo = w[w.dia.isin([3, 5])].groupby("ID")[c].mean()
        dz, p = _dz_p(jo, hi)
        rows.append(dict(medida="Epworth" if c == "epworth" else "PSS", outro=r["Outro"], hiit=r["HIIT"],
                         jogo=r["Jogo"], dz_hiit_jogo=round(dz, 2), p=round(p, 3), sig=bool(p < .05)))
    return pd.DataFrame(rows)


def an_tri_wb_profile(wb, m):
    mu, sd = m[SUB].mean(), m[SUB].std()
    ad = m.groupby(["ID", "dia"])[SUB].mean()
    prof = _classify(ad.reset_index(), mu=mu, sd=sd)
    pad = ad.reset_index()[["ID", "dia"]].copy(); pad["perfil"] = prof.values
    mg = wb.merge(pad, on=["ID", "dia"])
    mg["grp"] = np.where(mg.perfil.isin(["Iceberg invertido", "Everest invertido", "Barbatana de tubarao"]),
                         "risco/sobrecarga", np.where(mg.perfil.isin(["Iceberg", "Superficie"]), "favorável", "neutro"))
    rows = []
    for c in ["epworth", "pss"]:
        gs = [mg[mg.grp == k][c].dropna() for k in ["favorável", "neutro", "risco/sobrecarga"]]
        h, p = stats.kruskal(*gs)
        rows.append(dict(medida="Epworth" if c == "epworth" else "PSS",
                         favoravel=round(float(gs[0].mean()), 1), neutro=round(float(gs[1].mean()), 1),
                         risco=round(float(gs[2].mean()), 1), H=round(float(h), 2), p=round(float(p), 3),
                         sig=bool(p < .05)))
    return pd.DataFrame(rows)


def run():
    m = lh.read_delta("silver", "mood"); wb = lh.read_delta("silver", "wellbeing")
    lh.write_delta("gold", "an_tri_acute", an_tri_acute(m)); print("[gold] an_tri_acute")
    lh.write_delta("gold", "an_tri_contrast", an_tri_contrast(m)); print("[gold] an_tri_contrast")
    lh.write_delta("gold", "an_tri_cv", an_tri_cv(m)); print("[gold] an_tri_cv")
    lh.write_delta("gold", "an_tri_prof_day", an_tri_prof_day(m)); print("[gold] an_tri_prof_day")
    lh.write_delta("gold", "an_tri_wb_daytype", an_tri_wb_daytype(wb, m)); print("[gold] an_tri_wb_daytype")
    lh.write_delta("gold", "an_tri_wb_profile", an_tri_wb_profile(wb, m)); print("[gold] an_tri_wb_profile")


if __name__ == "__main__":
    run()
