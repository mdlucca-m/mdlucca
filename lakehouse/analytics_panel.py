# -*- coding: utf-8 -*-
"""GOLD · ANÁLISES DO PAINEL — constantes descritivas/agregadas do painel, do gold.

Traz para o lakehouse (auditável, reprodutível) as tabelas que alimentam abas
antes servidas por constantes fixas: descritivas, resposta aguda pré→pós,
contagem de perfis por dia, e sono/estresse (Epworth/PSS) por dia e por tipo.

Regra pré/pós (do estudo): pré = PRIMEIRA resposta do dia (manhã, is_pre),
pós = ÚLTIMA do dia (is_pos). Unidade = atleta (média das respostas do atleta).
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from scipy import stats
import lh

BR = ["Vigor", "Fadiga", "Tensao", "Depressao", "Raiva", "Confusao", "PTH"]
KEY = {"Vigor": "vigor", "Fadiga": "fadiga", "Tensao": "tensao", "Depressao": "depressao",
       "Raiva": "raiva", "Confusao": "confusao", "PTH": "pth"}
SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
# tipo de dia → categoria do painel
DAYCAT = {"HIIT": "HIIT", "Jogo": "Amistoso", "Baseline": "Outro", "Forca": "Outro"}


def an_desc(m):
    """Descritiva por dimensão: média, DP e faixa observada (todas as respostas)."""
    rows = []
    for c in BR:
        rows.append(dict(var=KEY[c], media=round(float(m[c].mean()), 1), dp=round(float(m[c].std()), 1),
                         minimo=int(m[c].min()), maximo=int(m[c].max())))
    return pd.DataFrame(rows)


def an_prepos_dim(m):
    """Resposta aguda pré→pós por dimensão (pré=primeira do dia, pós=última; Wilcoxon)."""
    pre = m[m.is_pre].groupby("ID")[BR].mean()
    pos = m[m.is_pos].groupby("ID")[BR].mean()
    rows = []
    for c in BR:
        j = pd.concat([pre[c], pos[c]], axis=1).dropna(); j.columns = ["pre", "pos"]
        d = j["pos"] - j["pre"]; dz = d.mean() / d.std(ddof=1)
        p = stats.wilcoxon(j["pre"], j["pos"]).pvalue
        pct = round(100 * (j["pos"].mean() - j["pre"].mean()) / j["pre"].mean()) if j["pre"].mean() else 0
        rows.append(dict(var=KEY[c], pre=round(float(j["pre"].mean()), 2), pos=round(float(j["pos"].mean()), 2),
                         pct=int(pct), p=round(float(p), 3), dz=round(float(dz), 2)))
    return pd.DataFrame(rows)


def _classify_day(m, d):
    mu, sd = m[SUB].mean(), m[SUB].std()
    ad = m[m.dia == d].groupby("ID")[SUB].mean()
    Z = (ad - mu) / sd
    names = list(CENT); CM = np.array([CENT[k] for k in names])
    return Z.apply(lambda r: names[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)


def an_perfis_byday_count(m):
    """Nº de atletas por perfil no D1 e no D7 (perfil do atleta-dia médio)."""
    d1 = _classify_day(m, 1).value_counts()
    d7 = _classify_day(m, 7).value_counts()
    names = list(CENT)
    rows = [dict(perfil=nm, d1=int(d1.get(nm, 0)), d7=int(d7.get(nm, 0))) for nm in names]
    return pd.DataFrame(rows)


def an_wellbeing_byday(wb):
    """Epworth/PSS média por dia (trajetória)."""
    rows = []
    for d in range(1, 8):
        s = wb[wb.dia == d]
        rows.append(dict(dia=d, epworth=round(float(s["epworth"].mean()), 1), pss=round(float(s["pss"].mean()), 1)))
    return pd.DataFrame(rows)


def an_wellbeing_bytype(wb, m):
    """Epworth/PSS média por tipo de dia (Outro/HIIT/Amistoso)."""
    dtype = m.groupby("dia")["day_type"].first().map(DAYCAT)
    w = wb.copy(); w["cat"] = w["dia"].map(dtype)
    rows = []
    for cat in ["Outro", "HIIT", "Amistoso"]:
        s = w[w.cat == cat]
        rows.append(dict(cat=cat, epworth=round(float(s["epworth"].mean()), 1), pss=round(float(s["pss"].mean()), 1)))
    return pd.DataFrame(rows)


NEG = ["Tensao", "Depressao", "Raiva", "Confusao"]

def an_negatives_bydaytype(m):
    """Média das negativas + vigor/fadiga por tipo de dia (Outro/HIIT/Amistoso),
    Δ agudo pré→pós por tipo, e efeito de tipo por MODELO MISTO (intercepto aleatório
    por atleta; contraste Amistoso − Outro). Métodos padrão, documentados."""
    import statsmodels.formula.api as smf
    mm = m.copy(); mm["cat"] = mm["day_type"].map(DAYCAT)
    rows = []
    for k in NEG + ["Vigor", "Fadiga"]:
        for c in ["Outro", "HIIT", "Amistoso"]:
            sub = mm[mm.cat == c]
            # Δ agudo pré→pós por atleta-dia (só p/ as negativas)
            if k in NEG:
                pre = sub[sub.is_pre].groupby(["ID", "dia"])[k].mean()
                pos = sub[sub.is_pos].groupby(["ID", "dia"])[k].mean()
                acute = round(float((pos - pre).mean()), 2)
            else:
                acute = None
            rows.append(dict(dim=k, cat=c, media=round(float(sub[k].mean()), 2), acute=acute))
    means = pd.DataFrame(rows)
    # modelo misto: HIIT (D2,D4) vs Jogo (D3,D5) CONTROLANDO a posição na semana (dia),
    # intercepto aleatório por atleta. b>0 = HIIT mais aversivo que o jogo.
    mw = mm[mm.dia.isin([2, 3, 4, 5])].copy()
    mw["tipo"] = np.where(mw.dia.isin([2, 4]), "HIIT", "Jogo")
    adw = mw.groupby(["ID", "dia", "tipo"])[NEG].mean().reset_index()
    mix = []
    for k in NEG:
        md = smf.mixedlm(f"{k} ~ C(tipo, Treatment('Jogo')) + dia", adw, groups=adw["ID"]).fit(reml=False)
        c = [i for i in md.params.index if "HIIT" in i][0]
        mix.append(dict(dim=k, b=round(float(md.params[c]), 2), p=round(float(md.pvalues[c]), 3)))
    return means, pd.DataFrame(mix)


BR6 = ["Vigor", "Fadiga", "Tensao", "Depressao", "Raiva", "Confusao"]
ITEM_PREF = {"Vigor": "vig", "Fadiga": "fad", "Tensao": "ten", "Depressao": "dep",
             "Raiva": "rai", "Confusao": "con"}

def _icc_label(single):
    return "boa" if single >= .6 else "moderada" if single >= .5 else "pobre"

def an_reliability(m, it):
    """Confiabilidade: ICC(2,1)/(2,k) (dois fatores, acordo absoluto, casos completos)
    por dimensão; e ômega de McDonald (fator único sobre os 4 itens de cada dimensão)."""
    import pingouin as pg
    from statsmodels.multivariate.factor import Factor
    ad = m.groupby(["ID", "dia"])[BR6].mean().reset_index()
    icc = []
    for c in BR6:
        w = ad.pivot_table(index="ID", columns="dia", values=c).dropna()
        long = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
        long["dia"] = long["dia"].astype(str)
        r = pg.intraclass_corr(data=long, targets="ID", raters="dia", ratings="v")
        s = float(r[r.Type == "ICC(A,1)"].ICC.iloc[0]); k = float(r[r.Type == "ICC(A,k)"].ICC.iloc[0])
        icc.append(dict(dim=KEY[c], icc1=round(s, 2), icck=round(k, 2), label=_icc_label(s), n=int(len(w)))
                   )
    om = []
    for c in BR6:
        cols = [f"{ITEM_PREF[c]}{i}" for i in range(1, 5)]
        X = it[cols].dropna().astype(float)
        # ômega de McDonald sobre as cargas do fator único (eixo principal, PAF)
        fa = Factor(X.values, n_factor=1, method="pa").fit()
        l = fa.loadings[:, 0]; l = l * np.sign(l.sum())
        omega = (l.sum() ** 2) / ((l.sum() ** 2) + np.sum(1 - l ** 2))
        om.append(dict(dim=KEY[c], omega=round(float(omega), 2)))
    return pd.DataFrame(icc), pd.DataFrame(om)


PROF_SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
PROF_CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
             "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
             "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
VM_DIMS = [("Vigor", "Vigor", "Vigor"), ("Fadiga", "Fadiga", "Fadiga"),
           ("PTH", "TMD", "PTH"), ("FadFisica", "FadFisica", "Fadiga física")]


def an_thresholds(icc, desc):
    """LIM: SEM, MDC90, MDC95 e SWC (mudança mínima detectável e menor mudança
    relevante) por dimensão, derivados do ICC(2,1) e do DP (métodos padrão)."""
    rows = []
    for k in BR6:
        kk = KEY[k]
        sd = float(desc.loc[kk, "dp"]); r = float(icc.loc[kk, "icc1"])
        sem = sd * np.sqrt(max(1 - r, 0))
        rows.append(dict(dim=kk, sem=round(sem, 1), mdc90=round(1.645 * np.sqrt(2) * sem, 1),
                         mdc95=round(1.96 * np.sqrt(2) * sem, 1), swc=round(0.2 * sd, 1)))
    return pd.DataFrame(rows)


def an_variance(m):
    """VM: decomposição de variância em 3 níveis (entre atletas / entre dias /
    intra-dia) por modelo aninhado; e trajetória pré/pós por dia. ICC = fração atleta."""
    import statsmodels.formula.api as smf
    mm = m.copy(); mm["dia"] = mm["dia"].astype(int)
    vc, curves = [], []
    for col, key, lab in VM_DIMS:
        md = smf.mixedlm(f"{col} ~ 1", mm, groups=mm["ID"], re_formula="1",
                         vc_formula={"dia": "0+C(dia)"}).fit(reml=True)
        va = float(np.asarray(md.cov_re)[0, 0]); vd = float(md.vcomp[0]); vr = float(md.scale)
        tot = va + vd + vr
        vc.append(dict(dim=key, lab=lab, atleta=round(100 * va / tot, 1), dia=round(100 * vd / tot, 1),
                       momento=round(100 * vr / tot, 1), icc=round(va / tot, 3)))
        for d in range(1, 8):
            pre = mm[(mm.dia == d) & (mm.is_pre)][col].mean()
            pos = mm[(mm.dia == d) & (mm.is_pos)][col].mean()
            curves.append(dict(dim=key, dia=d, x_pre=round(d - 0.2, 1), x_pos=round(d + 0.2, 1),
                               y_pre=round(float(pre), 2), y_pos=round(float(pos), 2)))
    return pd.DataFrame(vc), pd.DataFrame(curves)


def an_transitions(m):
    """TRANS: transições sequenciais — recuperação (pós Dk → pré Dk+1) e aguda
    (pré Dk → pós Dk), tamanho de efeito dz para vigor/fadiga/PTH + significância."""
    from scipy import stats
    pre = m[m.is_pre].groupby(["ID", "dia"])[["Vigor", "Fadiga", "PTH"]].mean()
    pos = m[m.is_pos].groupby(["ID", "dia"])[["Vigor", "Fadiga", "PTH"]].mean()
    def eff(a, b, c):
        j = pd.concat([a[c], b[c]], axis=1).dropna(); j.columns = ["a", "b"]
        d = j["b"] - j["a"]
        if len(j) < 5 or d.std(ddof=1) == 0:
            return 0.0, False
        p = stats.wilcoxon(j["a"], j["b"]).pvalue
        return round(float(d.mean() / d.std(ddof=1)), 2), bool(p < 0.05)
    rows = []
    for d in range(1, 7):
        a = pos.xs(d, level="dia"); b = pre.xs(d + 1, level="dia")
        vals = {c: eff(a, b, c) for c in ["Vigor", "Fadiga", "PTH"]}
        rows.append(dict(lab=f"D{d}→D{d+1} pré", tipo="Recuperação", vigor=vals["Vigor"][0],
                         fadiga=vals["Fadiga"][0], pth=vals["PTH"][0], sig=vals["PTH"][1]))
        a2 = pre.xs(d + 1, level="dia"); b2 = pos.xs(d + 1, level="dia")
        v2 = {c: eff(a2, b2, c) for c in ["Vigor", "Fadiga", "PTH"]}
        rows.append(dict(lab=f"D{d+1} pré→pós", tipo="Agudo", vigor=v2["Vigor"][0],
                         fadiga=v2["Fadiga"][0], pth=v2["PTH"][0], sig=v2["PTH"][1]))
    return pd.DataFrame(rows)


def an_risk_profiles(m):
    """PRISCO: exposição a perfis de risco por atleta-dia — prevalência de perfil
    negativo (Everest/Iceberg invertido) e de sobrecarga (barbatana), por dia e por atleta."""
    mu, sd = m[PROF_SUB].mean(), m[PROF_SUB].std()
    names = list(PROF_CENT); CM = np.array([PROF_CENT[k] for k in names])
    ad = m.groupby(["ID", "dia"])[PROF_SUB].mean()
    Z = (ad - mu) / sd
    prof = Z.apply(lambda r: names[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)
    a = ad.reset_index(); a["perfil"] = prof.values
    a["neg"] = a.perfil.isin(["Everest invertido", "Iceberg invertido"])
    a["fad"] = a.perfil.isin(["Barbatana de tubarao"])
    byday = [[int(round(100 * a[a.dia == d].neg.mean())), int(round(100 * a[a.dia == d].fad.mean()))]
             for d in range(1, 8)]
    en = a.groupby("ID").neg.sum(); ef = a.groupby("ID").fad.sum()
    return pd.DataFrame([dict(
        neg_prev=round(100 * a.neg.mean(), 1), fad_prev=round(100 * a.fad.mean(), 1),
        exp_neg1=int((en >= 1).sum()), exp_neg2=int((en >= 2).sum()),
        exp_fad1=int((ef >= 1).sum()), never=int(((en == 0) & (ef == 0)).sum()),
        byday=json.dumps(byday))])


ABBR = {"Iceberg": "IC", "Superficie": "SU", "Submerso": "SB",
        "Barbatana de tubarao": "BT", "Iceberg invertido": "II", "Everest invertido": "EI"}
RISK = {"EI": 2, "II": 2, "BT": 1, "SB": 1, "SU": 0, "IC": 0}

def an_athlete_profiles(m):
    """Perfil classificado por atleta-dia (mesmo A01–A27 do silver): sigla, nível de
    risco (0 bom/1 atenção/2 risco) e PTH/Vigor/Fadiga do dia. Alimenta os ícones da
    visão individual, consistente com PROFATL/ATLETAV."""
    mu, sd = m[PROF_SUB].mean(), m[PROF_SUB].std()
    names = list(PROF_CENT); CM = np.array([PROF_CENT[k] for k in names])
    ad = m.groupby(["ID", "dia"])[PROF_SUB + ["PTH"]].mean()
    Z = (ad[PROF_SUB] - mu) / sd
    prof = Z.apply(lambda r: names[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)
    a = ad.reset_index(); a["abbr"] = [ABBR[p] for p in prof.values]
    a["risco"] = [RISK[x] for x in a["abbr"]]
    return a[["ID", "dia", "abbr", "risco", "PTH", "Vigor", "Fadiga"]].rename(
        columns={"PTH": "pth", "Vigor": "vigor", "Fadiga": "fadiga"})


def run():
    m = lh.read_delta("silver", "mood")
    wb = lh.read_delta("silver", "wellbeing")
    it = lh.read_delta("silver", "brums_items")
    lh.write_delta("gold", "an_athlete_profiles", an_athlete_profiles(m)); print("[gold] an_athlete_profiles")
    vc, vcurve = an_variance(m)
    lh.write_delta("gold", "an_variance", vc); lh.write_delta("gold", "an_variance_curves", vcurve); print("[gold] an_variance (+curves)")
    lh.write_delta("gold", "an_transitions", an_transitions(m)); print("[gold] an_transitions")
    lh.write_delta("gold", "an_risk_profiles", an_risk_profiles(m)); print("[gold] an_risk_profiles")
    icc, om = an_reliability(m, it)
    lh.write_delta("gold", "an_icc", icc); print("[gold] an_icc")
    lh.write_delta("gold", "an_omega", om); print("[gold] an_omega")
    nmeans, nmix = an_negatives_bydaytype(m)
    lh.write_delta("gold", "an_negatives_bydaytype", nmeans); print("[gold] an_negatives_bydaytype")
    lh.write_delta("gold", "an_negatives_mix", nmix); print("[gold] an_negatives_mix")
    desc = an_desc(m)
    lh.write_delta("gold", "an_desc", desc); print("[gold] an_desc")
    lh.write_delta("gold", "an_thresholds", an_thresholds(icc.set_index("dim"), desc.set_index("var"))); print("[gold] an_thresholds")
    lh.write_delta("gold", "an_prepos_dim", an_prepos_dim(m)); print("[gold] an_prepos_dim")
    lh.write_delta("gold", "an_perfis_byday_count", an_perfis_byday_count(m)); print("[gold] an_perfis_byday_count")
    lh.write_delta("gold", "an_wellbeing_byday", an_wellbeing_byday(wb)); print("[gold] an_wellbeing_byday")
    lh.write_delta("gold", "an_wellbeing_bytype", an_wellbeing_bytype(wb, m)); print("[gold] an_wellbeing_bytype")


if __name__ == "__main__":
    run()
