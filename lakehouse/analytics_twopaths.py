# -*- coding: utf-8 -*-
"""Dois caminhos analíticos lado a lado:
  Caminho A — n=19, casos completos, SEM imputação.
  Caminho B — n=27, COM imputação dos dias ausentes pela média do dia.
  (+ modelo misto n=27 como referência rigorosa, sem imputação.)
Omnibus (rm-ANOVA+Mauchly+GG, Friedman+W), Dunnett vs basal, tipo de dia.
Escreve gold an_two_* e um JSON (TWOPATH) para painel e documento.
Tudo determinístico (SEED=7)."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from scipy import stats
import pingouin as pg
import statsmodels.formula.api as smf
import lh

SEED = 7
m = lh.read_delta("silver", "mood"); wb = lh.read_delta("silver", "wellbeing")
VARS = [("Vigor", "m", "Vigor"), ("Fadiga", "m", "Fadiga"), ("FadFisica", "m", "Fadiga física"),
        ("FadMental", "m", "Fadiga mental"), ("Tensao", "m", "Tensão"), ("Depressao", "m", "Depressão"),
        ("Raiva", "m", "Raiva"), ("Confusao", "m", "Confusão"), ("PTH", "m", "PTH"),
        ("epworth", "wb", "Sonolência (Epworth)"), ("pss", "wb", "Estresse (PSS)")]
DAYTYPE = {1: "Basal", 2: "HIIT", 3: "Jogo", 4: "HIIT", 5: "Jogo", 6: "Técnico/força", 7: "HIIT"}


def _ad(col, src):
    df = m if src == "m" else wb
    return df.groupby(["ID", "dia"])[col].mean().reset_index() if src == "m" else df[["ID", "dia", col]].copy()


def wide(col, src, scen):
    ad = _ad(col, src)
    if scen == "c":                       # casos completos (n=19)
        return ad.pivot_table(index="ID", columns="dia", values=col).dropna()
    ids = ad["ID"].unique()               # imputado (n=27): todos os atletas do var
    full = pd.MultiIndex.from_product([ids, range(1, 8)], names=["ID", "dia"]).to_frame(index=False)
    j = full.merge(ad, on=["ID", "dia"], how="left")
    j[col] = j[col].fillna(j.groupby("dia")[col].transform("mean"))
    return j.pivot_table(index="ID", columns="dia", values=col)


def omnibus_one(col, src, scen):
    w = wide(col, src, scen); n = len(w)
    lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
    a = pg.rm_anova(data=lg, dv="v", within="dia", subject="ID", correction=True, detailed=True)
    ss, sse = a.loc[0, "SS"], a.loc[1, "SS"]
    F, pgg, eps = a.loc[0, "F"], a.loc[0, "p_GG_corr"], a.loc[0, "eps"]
    wsph, psph = a.loc[0, "W_spher"], a.loc[0, "p_spher"]
    fr = pg.friedman(data=lg, dv="v", within="dia", subject="ID")
    return dict(n=int(n), F=round(float(F), 2), np2=round(float(ss / (ss + sse)), 3),
                p_gg=round(float(pgg), 4), gg_eps=round(float(eps), 3),
                mauchly_p=round(float(psph), 4), esferica=bool(psph >= .05),
                kendall_W=round(float(fr["W"].iloc[0]), 3), friedman_p=round(float(fr["p_unc"].iloc[0]), 4),
                sig_anova=bool(pgg < .05), sig_friedman=bool(fr["p_unc"].iloc[0] < .05))


def mixed_one(col, src):
    """Modelo misto n=27 (dados disponíveis, SEM imputação): efeito conjunto de dia
    por teste de Wald sobre os coeficientes C(dia) (estável, não refita o nulo)."""
    ad = _ad(col, src).dropna(subset=[col]).copy()
    ad["dia"] = ad["dia"].astype("category")
    try:
        md = smf.mixedlm("%s ~ C(dia)" % col, ad, groups=ad["ID"])
        fit = md.fit(reml=False, method="lbfgs", maxiter=400)
        wt = fit.wald_test_terms(skip_single=False, scalar=True)
        tbl = wt.table
        # linha do termo C(dia)
        key = [k for k in tbl.index if "dia" in str(k)]
        row = tbl.loc[key[0]]
        chi2 = float(row.get("statistic", row.iloc[0])); p = float(row.get("pvalue", row.iloc[-2]))
        return dict(n=int(ad["ID"].nunique()), LRchi2=round(chi2, 2), p=round(p, 4), sig=bool(p < .05), metodo="misto")
    except Exception:
        # covariância aleatória singular (variância entre-atletas ~0): reduz a OLS
        try:
            ols = smf.ols("%s ~ C(dia)" % col, ad).fit()
            wt = ols.wald_test_terms(skip_single=False, scalar=True).table
            key = [k for k in wt.index if "dia" in str(k)][0]
            F = float(wt.loc[key].get("statistic", wt.loc[key].iloc[0]))
            p = float(wt.loc[key].get("pvalue", wt.loc[key].iloc[-2]))
            return dict(n=int(ad["ID"].nunique()), LRchi2=round(F, 2), p=round(p, 4), sig=bool(p < .05), metodo="ols")
        except Exception as e:
            return dict(n=int(ad["ID"].nunique()), LRchi2=None, p=None, sig=None, metodo="falhou")


def dunnett_one(col, src, scen, rho=0.5, B=200000):
    w = wide(col, src, scen); n = len(w); days = sorted(w.columns); base = w[days[0]].values
    contr = days[1:]; k = len(contr); ts = []
    for dcol in contr:
        diff = w[dcol].values - base; se = diff.std(ddof=1) / np.sqrt(n)
        ts.append(diff.mean() / se if se else 0.0)
    ts = np.array(ts); df = n - 1
    rng = np.random.default_rng(SEED)
    L = np.linalg.cholesky(rho * np.ones((k, k)) + (1 - rho) * np.eye(k))
    Z = rng.standard_normal((B, k)) @ L.T; chi = rng.chisquare(df, B) / df
    Tmax = np.abs(Z / np.sqrt(chi)[:, None]).max(1)
    padj = [float((Tmax >= abs(t)).mean()) for t in ts]
    return [dict(dia=int(dd), t=round(float(t), 2), p=round(p, 4), sig=bool(p < .05))
            for dd, t, p in zip(contr, ts, padj)]


def daytype_one(col, src, scen):
    w = wide(col, src, scen); lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
    lg["tipo"] = lg["dia"].map(DAYTYPE)
    piv = lg.groupby(["ID", "tipo"])["v"].mean().reset_index().pivot_table(index="ID", columns="tipo", values="v").dropna()
    tipos = list(piv.columns); res = []
    for i in range(len(tipos)):
        for j in range(i + 1, len(tipos)):
            a, b = tipos[i], tipos[j]
            try:
                p = float(stats.wilcoxon(piv[a], piv[b]).pvalue)
            except Exception:
                p = 1.0
            res.append(dict(par=f"{a} × {b}", p=round(p, 4), sig=bool(p < .05), tem_basal=("Basal" in (a, b))))
    return res


def build():
    omni, dun, dtp, mix = [], [], [], []
    for col, src, lab in VARS:
        row = dict(var=col, lab=lab)
        for scen, tag in [("c", "n19"), ("i", "n27")]:
            o = omnibus_one(col, src, scen)
            for kk, vv in o.items():
                row[f"{kk}_{tag}"] = vv
        omni.append(row)
        mx = mixed_one(col, src); mix.append(dict(var=col, lab=lab, **mx))
        for scen, tag in [("c", "n19"), ("i", "n27")]:
            for r in dunnett_one(col, src, scen):
                dun.append(dict(var=col, lab=lab, caminho=tag, **r))
            for r in daytype_one(col, src, scen):
                dtp.append(dict(var=col, lab=lab, caminho=tag, **r))
    omni = pd.DataFrame(omni); dun = pd.DataFrame(dun); dtp = pd.DataFrame(dtp); mix = pd.DataFrame(mix)
    return omni, dun, dtp, mix


def to_json(omni, dun, dtp, mix):
    def dcount(var, tag):
        s = dun[(dun.var == var) & (dun.caminho == tag)]
        return int(s.sig.sum()), [int(x) for x in s[s.sig]["dia"]]
    O = []
    for r in omni.itertuples():
        O.append(dict(var=r.var, lab=r.lab,
                      n19=dict(n=r.n_n19, F=r.F_n19, np2=r.np2_n19, pgg=r.p_gg_n19, eps=r.gg_eps_n19,
                               mauchly=r.mauchly_p_n19, kW=r.kendall_W_n19, frp=r.friedman_p_n19,
                               sigA=bool(r.sig_anova_n19), sigF=bool(r.sig_friedman_n19), dun=dcount(r.var, "n19")[0]),
                      n27=dict(n=r.n_n27, F=r.F_n27, np2=r.np2_n27, pgg=r.p_gg_n27, eps=r.gg_eps_n27,
                               mauchly=r.mauchly_p_n27, kW=r.kendall_W_n27, frp=r.friedman_p_n27,
                               sigA=bool(r.sig_anova_n27), sigF=bool(r.sig_friedman_n27), dun=dcount(r.var, "n27")[0])))
    M = [dict(var=r.var, lab=r.lab, n=r.n, LRchi2=r.LRchi2, p=r.p, sig=(bool(r.sig) if pd.notna(r.sig) else None)) for r in mix.itertuples()]
    DUN = {}
    for tag in ["n19", "n27"]:
        DUN[tag] = {}
        for var in omni["var"]:
            s = dun[(dun.var == var) & (dun.caminho == tag)].sort_values("dia")
            DUN[tag][var] = [dict(dia=int(x.dia), t=x.t, p=x.p, sig=bool(x.sig)) for x in s.itertuples()]
    return dict(omni=O, mixed=M, dunnett=DUN,
                sig_n19=int(omni.sig_anova_n19.sum()), sig_n27=int(omni.sig_anova_n27.sum()))


def run():
    omni, dun, dtp, mix = build()
    lh.write_delta("gold", "an_two_omnibus", omni); print("[gold] an_two_omnibus", len(omni))
    lh.write_delta("gold", "an_two_dunnett", dun); print("[gold] an_two_dunnett", len(dun))
    lh.write_delta("gold", "an_two_daytype", dtp); print("[gold] an_two_daytype", len(dtp))
    lh.write_delta("gold", "an_two_mixed", mix); print("[gold] an_two_mixed", len(mix))
    payload = to_json(omni, dun, dtp, mix)
    lh.write_delta("gold", "an_two_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_two_payload · sig n19=%d n27=%d" % (payload["sig_n19"], payload["sig_n27"]))
    return payload


if __name__ == "__main__":
    p = run()
    print(json.dumps(p["omni"][:3], ensure_ascii=False, indent=1))
