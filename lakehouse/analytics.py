# -*- coding: utf-8 -*-
"""GOLD · ANÁLISES — todas as análises do estudo computadas a partir do lakehouse.

Lê silver.mood / silver.wellbeing e materializa as tabelas analíticas que o painel
apresenta, de forma reprodutível e versionada (Delta). Métodos idênticos aos
validados no estudo (não-paramétrico; unidade = atleta; casos completos p/ Friedman).

Tabelas geradas (prefixo an_):
  an_d17            D1→D7 (Wilcoxon dz) por dimensão
  an_friedman       Friedman χ²/p/W (7 dias, casos completos) por dimensão
  an_spearman       correlações de Spearman entre dimensões (atleta-dia)
  an_profiles       perfis Terry/Parsons-Smith: centroide-T, prevalência, dominante/dia
  an_snr            decomposição de variância (tendência+HIIT+ruído) e SNR
  an_negatives_daytype  negativas em dias de HIIT × jogo (meio de semana)
  an_wellbeing      Epworth/PSS D1→D7 + correlações com o humor
"""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy import stats
import lh

BR = ["Vigor", "Fadiga", "Tensao", "Depressao", "Raiva", "Confusao", "PTH"]
KEY = {"Vigor": "vigor", "Fadiga": "fadiga", "Tensao": "tensao", "Depressao": "depressao",
       "Raiva": "raiva", "Confusao": "confusao", "PTH": "pth"}
NEG = ["Tensao", "Depressao", "Raiva", "Confusao"]
SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]  # 6 dims p/ perfil
HIIT = [2, 4, 7]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}

def _athlete_day(m):
    return m.groupby(["ID", "dia"])[BR].mean().reset_index()

def an_d17(ad):
    rows = []
    for c in BR:
        w = ad.pivot_table(index="ID", columns="dia", values=c)
        j = pd.concat([w[1], w[7]], axis=1).dropna()
        diff = j[7] - j[1]; dz = diff.mean() / diff.std(ddof=1)
        p = stats.wilcoxon(j[1], j[7]).pvalue
        d1 = ad[ad.dia == 1][c].mean(); d7 = ad[ad.dia == 7][c].mean()  # DIM (todos por dia)
        rows.append(dict(var=KEY[c], d1=round(d1, 2), d7=round(d7, 2), delta=round(d7 - d1, 2),
                         pct=round(100 * (d7 - d1) / d1, 0), dz=round(dz, 2),
                         p_wilcoxon=round(float(p), 3), sig=bool(p < .05)))
    return pd.DataFrame(rows)

def an_friedman(ad):
    rows = []
    for c in BR:
        w = ad.pivot_table(index="ID", columns="dia", values=c).dropna()
        chi, p = stats.friedmanchisquare(*[w[d] for d in range(1, 8)])
        W = chi / (len(w) * (7 - 1))
        rows.append(dict(var=KEY[c], n=len(w), chi2=round(float(chi), 1),
                         p=round(float(p), 3), W=round(float(W), 2), sig=bool(p < .05)))
    return pd.DataFrame(rows)

def an_spearman(ad):
    # unidade = ATLETA (média por atleta corrige a pseudorreplicação das medidas
    # repetidas) e entre as 6 dimensões — PTH é excluída por ser o composto delas.
    dims = ["Vigor", "Fadiga", "Tensao", "Depressao", "Raiva", "Confusao"]
    am = ad.groupby("ID")[dims].mean()
    rows = []
    for i in range(len(dims)):
        for j in range(i + 1, len(dims)):
            a, b = dims[i], dims[j]
            r, p = stats.spearmanr(am[a], am[b])
            if p < .05:
                rows.append(dict(par=f"{KEY[a]} × {KEY[b]}", rho=round(float(r), 2), p=round(float(p), 3)))
    return pd.DataFrame(rows).sort_values("rho", key=abs, ascending=False).reset_index(drop=True)

def _classify(m):
    """Classifica cada atleta-dia no perfil mais próximo (z na amostra) e devolve T-scores."""
    mu, sd = m[SUB].mean(), m[SUB].std()
    Z = (m[SUB] - mu) / sd
    names = list(CENT); CM = np.array([CENT[k] for k in names])
    perfil = Z.apply(lambda r: names[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)
    return perfil, 50 + 10 * Z, mu, sd, names, CM

def _nearest(zvec, names, CM):
    return names[int(((CM - np.asarray(zvec)) ** 2).sum(1).argmin())]

def an_profiles(m):
    perfil, T, mu, sd, names, CM = _classify(m)
    m = m.copy(); m["perfil"] = perfil
    prof = []
    for nm in names:
        mk = m["perfil"] == nm
        prof.append(dict(perfil=nm, prevalencia=round(100 * mk.mean(), 1), n=int(mk.sum()),
                         **{KEY.get(c, c.lower()): round(float(T[mk][c].mean()), 1) for c in SUB}))
    dom = []
    for d in range(1, 8):
        vc = (m[m.dia == d]["perfil"].value_counts(normalize=True).mul(100)
              .rename_axis("perfil").reset_index(name="pct"))
        # desempate DETERMINÍSTICO por nome (evita flip em empates, ex.: D7)
        vc = vc.sort_values(["pct", "perfil"], ascending=[False, True]).reset_index(drop=True)
        empate = bool((vc["pct"] == vc.loc[0, "pct"]).sum() > 1)
        dom.append(dict(dia=d, dominante=vc.loc[0, "perfil"], pct=round(float(vc.loc[0, "pct"]), 1),
                        empate=empate))
    return pd.DataFrame(prof), pd.DataFrame(dom)

def an_profiles_byday_t(m):
    """Trajetória do GRUPO em escore-T por dia (6 dims, ordem do painel: Ten,Dep,Rai,Vig,Fad,Con)."""
    _, T, _, _, _, _ = _classify(m)
    adT = T.copy(); adT["ID"] = m["ID"].values; adT["dia"] = m["dia"].values
    ad = adT.groupby(["ID", "dia"])[SUB].mean().reset_index()
    dg = ad.groupby("dia")[SUB].mean().round(1).reset_index()
    return dg.rename(columns={c: KEY[c] for c in SUB})

def an_profile_group(m, prof):
    """Perfil do GRUPO: o mais prevalente e o do 'atleta-dia médio'."""
    top = prof.sort_values("prevalencia", ascending=False).iloc[0]
    _, _, mu, sd, names, CM = _classify(m)
    grupo = _nearest(np.zeros(len(SUB)), names, CM)  # média da amostra: z=0 (Superfície) por construção
    return pd.DataFrame([dict(
        perfil_mais_prevalente=top["perfil"], prevalencia_pct=float(top["prevalencia"]),
        perfil_medio_grupo=grupo,
        nota="Em escore-T dentro da amostra, a média do grupo é ~50 em todas as dimensões "
             "(Superfície) por construção; o perfil CARACTERÍSTICO do grupo é o mais prevalente, "
             "e a trajetória dia a dia (an_profiles_byday) mostra a erosão do iceberg.")])

def an_profile_athlete(m):
    """Perfil INDIVIDUAL por atleta: perfil médio (centroide) e modal (mais frequente) + T-scores."""
    perfil, T, mu, sd, names, CM = _classify(m)
    g = m.copy(); g["perfil"] = perfil
    for c in SUB:
        g[c + "_T"] = T[c].values
    rows = []
    for aid, sub in g.groupby("ID"):
        zmean = [(sub[c].mean() - mu[c]) / sd[c] for c in SUB]
        vc = sub["perfil"].value_counts()
        rows.append(dict(ID=aid, n_obs=int(len(sub)),
                         perfil_medio=_nearest(zmean, names, CM),
                         perfil_modal=vc.index[0], modal_freq=int(vc.iloc[0]),
                         **{KEY[c]: round(float(sub[c + "_T"].mean()), 1) for c in SUB},
                         risco=bool(sub["perfil"].isin(["Everest invertido", "Iceberg invertido"]).any())))
    return pd.DataFrame(rows).sort_values("ID").reset_index(drop=True)

def an_snr(m):
    # decomposição sobre a média diária de TODAS as respostas (mesmo método do painel)
    x = np.arange(1, 8); ss = lambda a: float((a ** 2).sum()); rows = []
    for c in BR:
        y = m.groupby("dia")[c].mean().reindex(range(1, 8)).values; yc = y - y.mean()
        Xt = np.column_stack([x - 4, (x - 4) ** 2]); bt, *_ = np.linalg.lstsq(Xt, yc, rcond=None); tr = Xt @ bt
        det = yc - tr; isH = np.isin(x, HIIT).astype(float)
        hc = (isH - isH.mean()) * (det[isH == 1].mean() - det[isH == 0].mean()); no = det - hc
        tot = ss(yc) or 1; snr = (ss(tr) + ss(hc)) / ss(no) if ss(no) else 999
        piso = round(100 * float((m[c] == 0).mean()), 0)  # % de escores nulos (efeito de piso)
        rows.append(dict(var=KEY[c], tendencia=round(ss(tr) / tot * 100, 1), hiit=round(ss(hc) / tot * 100, 1),
                         ruido=round(ss(no) / tot * 100, 1), snr=round(float(snr), 1), piso=piso))
    return pd.DataFrame(rows)

def an_negatives_daytype(ad):
    # meio de semana pareado: HIIT (D2,D4) vs jogo (D3,D5)
    rows = []
    for c in NEG:
        hi = ad[ad.dia.isin([2, 4])].groupby("ID")[c].mean()
        jo = ad[ad.dia.isin([3, 5])].groupby("ID")[c].mean()
        j = pd.concat([hi, jo], axis=1).dropna(); j.columns = ["hiit", "jogo"]
        if len(j) < 5: continue
        diff = j["jogo"] - j["hiit"]; dz = diff.mean() / diff.std(ddof=1)
        p = stats.wilcoxon(j["hiit"], j["jogo"]).pvalue
        rows.append(dict(var=KEY[c], media_hiit=round(j["hiit"].mean(), 2), media_jogo=round(j["jogo"].mean(), 2),
                         dz_jogo_menos_hiit=round(float(dz), 2), p=round(float(p), 3), sig=bool(p < .05)))
    return pd.DataFrame(rows)

def an_wellbeing(wb, adm):
    rows = []
    for c in ["epworth", "pss"]:
        w = wb.pivot_table(index="ID", columns="dia", values=c)
        j = pd.concat([w[1], w[7]], axis=1).dropna()
        diff = j[7] - j[1]; dz = diff.mean() / diff.std(ddof=1); p = stats.wilcoxon(j[1], j[7]).pvalue
        rows.append(dict(var=c, d1=round(w[1].mean(), 1), d7=round(w[7].mean(), 1),
                         dz=round(float(dz), 2), p=round(float(p), 3)))
    d17 = pd.DataFrame(rows)
    # correlações Epworth/PSS × humor (atleta-dia)
    mg = wb.merge(adm, on=["ID", "dia"])
    cor = []
    for a in ["epworth", "pss"]:
        for b in ["Fadiga", "Vigor", "PTH"]:
            r, p = stats.spearmanr(mg[a], mg[b])
            cor.append(dict(par=f"{a} × {KEY[b]}", rho=round(float(r), 2), p=round(float(p), 3)))
    return d17, pd.DataFrame(cor)

def run():
    m = lh.read_delta("silver", "mood")
    ad = _athlete_day(m)
    lh.write_delta("gold", "an_d17", an_d17(ad)); print("[gold] an_d17")
    lh.write_delta("gold", "an_friedman", an_friedman(ad)); print("[gold] an_friedman")
    lh.write_delta("gold", "an_spearman", an_spearman(ad)); print("[gold] an_spearman")
    prof, dom = an_profiles(m)
    lh.write_delta("gold", "an_profiles", prof); lh.write_delta("gold", "an_profiles_byday", dom); print("[gold] an_profiles (+byday)")
    lh.write_delta("gold", "an_profiles_byday_t", an_profiles_byday_t(m)); print("[gold] an_profiles_byday_t")
    lh.write_delta("gold", "an_profile_group", an_profile_group(m, prof)); print("[gold] an_profile_group")
    lh.write_delta("gold", "an_profile_athlete", an_profile_athlete(m)); print("[gold] an_profile_athlete")
    lh.write_delta("gold", "an_snr", an_snr(m)); print("[gold] an_snr")
    lh.write_delta("gold", "an_negatives_daytype", an_negatives_daytype(ad)); print("[gold] an_negatives_daytype")
    wb = lh.read_delta("silver", "wellbeing")
    wd17, wcor = an_wellbeing(wb, ad[["ID", "dia"] + BR])
    lh.write_delta("gold", "an_wellbeing", wd17); lh.write_delta("gold", "an_wellbeing_corr", wcor); print("[gold] an_wellbeing (+corr)")

if __name__ == "__main__":
    run()
