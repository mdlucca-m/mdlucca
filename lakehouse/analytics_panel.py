# -*- coding: utf-8 -*-
"""GOLD · ANÁLISES DO PAINEL — constantes descritivas/agregadas do painel, do gold.

Traz para o lakehouse (auditável, reprodutível) as tabelas que alimentam abas
antes servidas por constantes fixas: descritivas, resposta aguda pré→pós,
contagem de perfis por dia, e sono/estresse (Epworth/PSS) por dia e por tipo.

Regra pré/pós (do estudo): pré = PRIMEIRA resposta do dia (manhã, is_pre),
pós = ÚLTIMA do dia (is_pos). Unidade = atleta (média das respostas do atleta).
"""
from __future__ import annotations
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


def run():
    m = lh.read_delta("silver", "mood")
    wb = lh.read_delta("silver", "wellbeing")
    it = lh.read_delta("silver", "brums_items")
    icc, om = an_reliability(m, it)
    lh.write_delta("gold", "an_icc", icc); print("[gold] an_icc")
    lh.write_delta("gold", "an_omega", om); print("[gold] an_omega")
    nmeans, nmix = an_negatives_bydaytype(m)
    lh.write_delta("gold", "an_negatives_bydaytype", nmeans); print("[gold] an_negatives_bydaytype")
    lh.write_delta("gold", "an_negatives_mix", nmix); print("[gold] an_negatives_mix")
    lh.write_delta("gold", "an_desc", an_desc(m)); print("[gold] an_desc")
    lh.write_delta("gold", "an_prepos_dim", an_prepos_dim(m)); print("[gold] an_prepos_dim")
    lh.write_delta("gold", "an_perfis_byday_count", an_perfis_byday_count(m)); print("[gold] an_perfis_byday_count")
    lh.write_delta("gold", "an_wellbeing_byday", an_wellbeing_byday(wb)); print("[gold] an_wellbeing_byday")
    lh.write_delta("gold", "an_wellbeing_bytype", an_wellbeing_bytype(wb, m)); print("[gold] an_wellbeing_bytype")


if __name__ == "__main__":
    run()
