# -*- coding: utf-8 -*-
"""Auditoria da bateria estatística (omnibus / post hoc / Dunnett / tipo de dia).
Computa tudo do dado real (silver) e confere contra as afirmações do usuário."""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy import stats
import pingouin as pg
import scikit_posthocs as sph
import lh

SEED = 7
m = lh.read_delta("silver", "mood"); wb = lh.read_delta("silver", "wellbeing")
VARS = [("Vigor", "m"), ("Fadiga", "m"), ("FadFisica", "m"), ("FadMental", "m"),
        ("Tensao", "m"), ("Depressao", "m"), ("Raiva", "m"), ("Confusao", "m"),
        ("PTH", "m"), ("epworth", "wb"), ("pss", "wb")]
DAYTYPE = {1: "Basal", 2: "HIIT", 3: "Jogo", 4: "HIIT", 5: "Jogo", 6: "Técnico/força", 7: "HIIT"}


def wide(col, src):
    df = m if src == "m" else wb
    ad = df.groupby(["ID", "dia"])[col].mean().reset_index() if src == "m" else df[["ID", "dia", col]].copy()
    return ad.pivot_table(index="ID", columns="dia", values=col).dropna()


# ---------- 1. DESCRITIVAS 11 × 7 ----------
def bootstrap_ci(x, B=5000):
    rng = np.random.default_rng(SEED); x = np.asarray(x); n = len(x)
    bs = x[rng.integers(0, n, (B, n))].mean(1)
    return np.percentile(bs, [2.5, 97.5])


def descritivas():
    rows = []
    for col, src in VARS:
        df = m if src == "m" else wb
        ad = df.groupby(["ID", "dia"])[col].mean().reset_index() if src == "m" else df[["ID", "dia", col]].copy()
        for d in range(1, 8):
            x = ad[ad.dia == d][col].dropna().values
            if len(x) < 3:
                continue
            lo, hi = bootstrap_ci(x)
            rows.append(dict(var=col, dia=d, n=len(x), media=round(float(x.mean()), 2),
                             dp=round(float(x.std(ddof=1)), 2), epm=round(float(x.std(ddof=1) / np.sqrt(len(x))), 2),
                             ic_lo=round(float(lo), 2), ic_hi=round(float(hi), 2),
                             mediana=round(float(np.median(x)), 2), q1=round(float(np.percentile(x, 25)), 2),
                             q3=round(float(np.percentile(x, 75)), 2), minimo=round(float(x.min()), 2),
                             maximo=round(float(x.max()), 2), piso=round(100 * float((x == 0).mean()), 1),
                             assimetria=round(float(stats.skew(x)), 2), curtose=round(float(stats.kurtosis(x)), 2)))
    return pd.DataFrame(rows)


# ---------- 2. OMNIBUS ----------
def omnibus():
    rows = []
    for col, src in VARS:
        w = wide(col, src); n = len(w)
        lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
        a = pg.rm_anova(data=lg, dv="v", within="dia", subject="ID", correction=True, detailed=True)
        ss, sse = a.loc[0, "SS"], a.loc[1, "SS"]
        F, pun, pgg, eps = a.loc[0, "F"], a.loc[0, "p_unc"], a.loc[0, "p_GG_corr"], a.loc[0, "eps"]
        wsph, psph = a.loc[0, "W_spher"], a.loc[0, "p_spher"]
        np2 = ss / (ss + sse)
        fr = pg.friedman(data=lg, dv="v", within="dia", subject="ID")
        rows.append(dict(var=col, n=n, F=round(float(F), 2), np2=round(float(np2), 3),
                         p_unc=round(float(pun), 4), p_gg=round(float(pgg), 4), gg_eps=round(float(eps), 3),
                         mauchly_W=round(float(wsph), 3), mauchly_p=round(float(psph), 4),
                         esferica=bool(psph >= .05),
                         friedman_Q=round(float(fr["Q"].iloc[0]), 2), kendall_W=round(float(fr["W"].iloc[0]), 3),
                         friedman_p=round(float(fr["p_unc"].iloc[0]), 4),
                         sig_anova=bool(pgg < .05), sig_friedman=bool(fr["p_unc"].iloc[0] < .05)))
    return pd.DataFrame(rows).sort_values("F", ascending=False)


# ---------- 3. POST HOC (21 pares × 7 métodos) ----------
def posthoc(col, src):
    w = wide(col, src); lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
    # bruto (Wilcoxon pareado) + Holm/Bonf/Sidak/BH via pingouin
    def padj(method):
        pt = pg.pairwise_tests(data=lg, dv="v", within="dia", subject="ID", parametric=False,
                               padjust=method, return_desc=False)
        return pt
    base = padj("none")
    pairs = [(int(a), int(b)) for a, b in zip(base["A"], base["B"])]
    out = pd.DataFrame({"par": [f"D{a}-D{b}" for a, b in pairs], "p_bruto": base["p_unc"].round(4).values})
    for meth, coln in [("bonf", "p_bonferroni"), ("holm", "p_holm"), ("sidak", "p_sidak"), ("fdr_bh", "p_bh")]:
        out[coln] = padj(meth)["p_corr"].round(4).values
    # Tukey (paramétrico)
    tuk = pg.pairwise_tukey(data=lg, dv="v", between=None, effsize="hedges") if False else None
    # Tukey em desenho intra: aproxima via pairwise_tests paramétrico + Tukey p — usa statsmodels
    try:
        tk = pg.pairwise_tukey(dv="v", between="dia", data=lg)
        tkcol = "p-tukey" if "p-tukey" in tk.columns else "p_tukey"
        tkmap = {f"D{int(min(a,b))}-D{int(max(a,b))}": p for a, b, p in zip(tk["A"], tk["B"], tk[tkcol])}
        out["p_tukey"] = [round(float(tkmap.get(f"D{min(a,b)}-D{max(a,b)}", np.nan)), 4) for a, b in pairs]
    except Exception:
        out["p_tukey"] = np.nan
    # Conover-Iman (pós Friedman) com Holm
    ci = sph.posthoc_conover_friedman(w.values, p_adjust="holm")
    days = list(w.columns)
    out["p_conover_holm"] = [round(float(ci.iloc[days.index(a), days.index(b)]), 4) for a, b in pairs]
    return out


# ---------- 4. DUNNETT vs basal (RM, max|T| sob t-multivariada ρ=0.5) ----------
def dunnett_rm(col, src, rho=0.5, B=200000):
    w = wide(col, src); n = len(w); days = sorted(w.columns)
    base = w[days[0]].values
    contr = days[1:]; k = len(contr)
    ts = []
    for d in contr:
        diff = w[d].values - base
        se = diff.std(ddof=1) / np.sqrt(n)
        ts.append(diff.mean() / se if se else 0.0)
    ts = np.array(ts); df = n - 1
    # simulação: Z ~ N(0, Σ) equicorr ρ; T = Z / sqrt(chi2_df/df); estat = max|T|
    rng = np.random.default_rng(SEED)
    L = np.linalg.cholesky(rho * np.ones((k, k)) + (1 - rho) * np.eye(k))
    Z = rng.standard_normal((B, k)) @ L.T
    chi = rng.chisquare(df, B) / df
    Tmax = np.abs(Z / np.sqrt(chi)[:, None]).max(1)
    padj = [float((Tmax >= abs(t)).mean()) for t in ts]
    return pd.DataFrame(dict(var=col, contraste=[f"D{d} vs D1" for d in contr],
                             t=[round(float(x), 2) for x in ts], p_dunnett=[round(p, 4) for p in padj],
                             sig=[bool(p < .05) for p in padj]))


# ---------- 5. TIPO DE DIA ----------
def por_tipo(col, src):
    w = wide(col, src); lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
    lg["tipo"] = lg["dia"].map(DAYTYPE)
    ag = lg.groupby(["ID", "tipo"])["v"].mean().reset_index()
    piv = ag.pivot_table(index="ID", columns="tipo", values="v").dropna()
    tipos = list(piv.columns); res = []
    for i in range(len(tipos)):
        for j in range(i + 1, len(tipos)):
            a, b = tipos[i], tipos[j]
            try:
                st = stats.wilcoxon(piv[a], piv[b]); p = st.pvalue
            except Exception:
                p = np.nan
            res.append(dict(var=col, par=f"{a} × {b}", p=round(float(p), 4), sig=bool(p < .05),
                            tem_basal=bool("Basal" in (a, b))))
    return pd.DataFrame(res)


def run():
    """Materializa a bateria (correta e reproduzível) como tabelas gold an_bat_*."""
    dd = descritivas(); lh.write_delta("gold", "an_bat_desc", dd); print("[gold] an_bat_desc", len(dd))
    om = omnibus(); lh.write_delta("gold", "an_bat_omnibus", om); print("[gold] an_bat_omnibus", len(om))
    dun = pd.concat([dunnett_rm(c, s) for c, s in VARS], ignore_index=True)
    lh.write_delta("gold", "an_bat_dunnett", dun); print("[gold] an_bat_dunnett", len(dun))
    dtp = pd.concat([por_tipo(c, s) for c, s in VARS], ignore_index=True)
    lh.write_delta("gold", "an_bat_daytype", dtp); print("[gold] an_bat_daytype", len(dtp))
    sig = list(om[om.sig_anova]["var"])
    src = {c: s for c, s in VARS}
    ph = pd.concat([posthoc(c, src[c]).assign(var=c) for c in sig], ignore_index=True)
    lh.write_delta("gold", "an_bat_posthoc", ph); print("[gold] an_bat_posthoc", len(ph))
    return om


if __name__ == "__main__":
    print("=" * 70)
    om = omnibus()
    print("OMNIBUS (11 variáveis):")
    print(om[["var", "n", "F", "np2", "p_gg", "mauchly_p", "kendall_W", "friedman_p", "sig_anova", "sig_friedman"]].to_string(index=False))
    print(f"\nsig ANOVA-GG: {om.sig_anova.sum()}/11 · sig Friedman: {om.sig_friedman.sum()}/11 · "
          f"concordam: {(om.sig_anova==om.sig_friedman).sum()}/11")
    top = om.iloc[0]; sec = om.iloc[1]
    print(f"LÍDER: {top['var']} F={top.F} np2={top.np2} | 2º: {sec['var']} F={sec.F} np2={sec.np2}")
