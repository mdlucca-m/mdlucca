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
SEED = 7
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
    # efeito agudo (pré→pós intradia) e de recuperação (pós Dk → pré Dk+1) por dimensão
    eff = []
    prg = mm[mm.is_pre].groupby(["ID", "dia"]); pog = mm[mm.is_pos].groupby(["ID", "dia"])
    for col, key, lab in VM_DIMS:
        pre = prg[col].mean(); pos = pog[col].mean()
        j = pd.concat([pre, pos], axis=1).dropna(); j.columns = ["pre", "pos"]
        ac = j["pos"] - j["pre"]
        ov = []
        for d in range(1, 7):
            a = pos.xs(d, level="dia") if d in pos.index.get_level_values("dia") else None
            b = pre.xs(d + 1, level="dia") if (d + 1) in pre.index.get_level_values("dia") else None
            if a is None or b is None: continue
            jj = pd.concat([a, b], axis=1).dropna(); jj.columns = ["a", "b"]
            ov.extend((jj["b"] - jj["a"]).tolist())
        ov = pd.Series(ov)
        eff.append(dict(dim=key, ag=round(float(ac.mean()), 2), agdz=round(float(ac.mean() / ac.std(ddof=1)), 2),
                        rec=round(float(ov.mean()), 2), recdz=round(float(ov.mean() / ov.std(ddof=1)), 2)))
    return pd.DataFrame(vc), pd.DataFrame(curves), pd.DataFrame(eff)


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


def an_pca(m):
    """Estrutura multivariada: PCA (2 componentes) das 6 dimensões padronizadas por
    resposta + agrupamento k-médias. Sinal fixo (vigor>0 no PC1) p/ reprodutibilidade.
    Devolve dispersão, centroides diários, clusters, cargas (correlação) e variância."""
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    m = m.sort_values(["ID", "dia", "seq"]).reset_index(drop=True)  # ordem estável (determinismo)
    Xz = ((m[PROF_SUB] - m[PROF_SUB].mean()) / m[PROF_SUB].std())
    X = Xz.values
    p = PCA(n_components=2, random_state=SEED).fit(X); Z = p.transform(X)
    load = p.components_.copy()
    for i in range(2):  # sinal determinístico: PC1 vigor>0, PC2 fadiga>0
        ref = "Vigor" if i == 0 else "Fadiga"
        if load[i][PROF_SUB.index(ref)] < 0:
            load[i] *= -1; Z[:, i] *= -1
    corr_load = [list(np.round(load[i] * np.sqrt(p.explained_variance_[i]), 2)) for i in range(2)]
    km = KMeans(n_clusters=2, random_state=SEED, n_init=10).fit(Z)
    lab = km.labels_.copy()
    # rótulo canônico: cluster 0 = o maior (evita troca de índice entre execuções)
    if (lab == 0).sum() < (lab == 1).sum():
        lab = 1 - lab
    sil = {k: round(float(silhouette_score(Z, KMeans(n_clusters=k, random_state=SEED, n_init=10).fit_predict(Z))), 3)
           for k in range(2, 7)}
    days = m["dia"].values
    pts = ";".join(f"{Z[i,0]:.3f},{Z[i,1]:.3f},{int(lab[i])},{int(days[i])}" for i in range(len(Z)))
    daycent = [[round(float(Z[days == d, 0].mean()), 3), round(float(Z[days == d, 1].mean()), 3)] for d in range(1, 8)]
    prof_z = [[round(float(Xz.iloc[lab == c][col].mean()), 2) for col in PROF_SUB] for c in range(2)]
    cent_pc = [[round(float(Z[lab == c, 0].mean()), 3), round(float(Z[lab == c, 1].mean()), 3)] for c in range(2)]
    payload = {"pts": pts, "day": daycent,
               "cl": {"k": 2, "sil": sil[2], "centroids_pc": cent_pc, "n": [int((lab == 0).sum()), int((lab == 1).sum())],
                      "profile_z": prof_z},
               "var": [round(float(v), 3) for v in p.explained_variance_ratio_],
               "load": {"PCo1": corr_load[0], "PCo2": corr_load[1]}, "sil": sil}
    return payload


SENS_DIMS = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
HIITD = [2, 4, 7]

def _snr_one(series7):
    """Decomposição de variância (tendência+HIIT+ruído) de uma série diária (7 pts)."""
    x = np.arange(1, 8); y = series7 - series7.mean()
    Xt = np.column_stack([x - 4, (x - 4) ** 2]); bt, *_ = np.linalg.lstsq(Xt, y, rcond=None); tr = Xt @ bt
    det = y - tr; isH = np.isin(x, HIITD).astype(float)
    hc = (isH - isH.mean()) * (det[isH == 1].mean() - det[isH == 0].mean()); no = det - hc
    ss = lambda a: float((a ** 2).sum()); tot = ss(y) or 1
    snr = (ss(tr) + ss(hc)) / ss(no) if ss(no) else 999
    return round(ss(tr) / tot * 100, 1), round(ss(hc) / tot * 100, 1), round(ss(no) / tot * 100, 1), round(float(snr), 1)


def an_sensitivity(m):
    """SENSV: robustez do achado por dimensão — dz(D1→D7), SNR, F/p da ANOVA de
    medidas repetidas (dia) e importância de permutação (RF fase tardia×inicial)."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.inspection import permutation_importance
    ad = m.groupby(["ID", "dia"])[SENS_DIMS].mean().reset_index()
    rows = []
    for c in SENS_DIMS:
        w = ad.pivot_table(index="ID", columns="dia", values=c).dropna()
        # ANOVA de medidas repetidas (efeito dia), cálculo manual sobre casos completos
        M = w.values; n, k = M.shape; grand = M.mean()
        ss_day = n * ((M.mean(0) - grand) ** 2).sum()
        ss_subj = k * ((M.mean(1) - grand) ** 2).sum()
        ss_err = ((M - M.mean(0) - M.mean(1)[:, None] + grand) ** 2).sum()
        df_day, df_err = k - 1, (n - 1) * (k - 1)
        F = round(float((ss_day / df_day) / (ss_err / df_err)), 2)
        p = round(float(stats.f.sf(F, df_day, df_err)), 4)
        j = pd.concat([w[1], w[7]], axis=1).dropna(); d = j.iloc[:, 1] - j.iloc[:, 0]
        dz = round(float(d.mean() / d.std(ddof=1)), 2)
        _, _, _, snr = _snr_one(m.groupby("dia")[c].mean().reindex(range(1, 8)).values)
        rows.append(dict(dim=c, dz17=dz, snr=snr, F_uni=F, p_uni=p))
    dfp = pd.DataFrame(rows).set_index("dim")
    # importância de permutação (RF, tarefa fase tardia×inicial)
    adg = lh.read_delta("gold", "athlete_day").sort_values(["ID", "dia"])  # ordem estável (RF determinístico)
    sub = adg[adg.dia.isin([1, 2, 3, 5, 6, 7])]
    y = (sub["dia"] >= 5).astype(int).values
    FE = ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao"]
    rf = RandomForestClassifier(n_estimators=300, max_depth=4, random_state=SEED, n_jobs=1,
                                class_weight="balanced").fit(sub[FE].values, y)
    imp = permutation_importance(rf, sub[FE].values, y, n_repeats=20, random_state=SEED, n_jobs=1)
    impd = dict(zip([f.capitalize() for f in FE], np.round(imp.importances_mean, 3)))
    keymap = {"Tensao": "Tensao", "Depressao": "Depressao", "Raiva": "Raiva", "Vigor": "Vigor",
              "Fadiga": "Fadiga", "Confusao": "Confusao"}
    perm = [float(impd[keymap[c]]) for c in SENS_DIMS]
    return {"lab": ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"], "dims": SENS_DIMS,
            "F_uni": [float(dfp.loc[c, "F_uni"]) for c in SENS_DIMS],
            "perm_imp": perm, "dz17": [float(dfp.loc[c, "dz17"]) for c in SENS_DIMS],
            "snr": [float(dfp.loc[c, "snr"]) for c in SENS_DIMS],
            "p_uni": [float(dfp.loc[c, "p_uni"]) for c in SENS_DIMS]}


REC_DIMS = [("Vigor", "Vigor", "Vigor"), ("Fadiga", "Fadiga", "Fadiga"),
            ("PTH", "TMD", "PTH"), ("FadFisica", "FadFisica", "Fadiga física")]

def an_recovery(m):
    """HVS: recuperação noturna (pós Dk → pré Dk+1) entrando em noite de HIIT (ph) vs
    fora (pn) + Wilcoxon; variação intra-dia por HIIT/fora; e SNR (inclui fadiga física)."""
    pre = m[m.is_pre].groupby(["ID", "dia"]); pos = m[m.is_pos].groupby(["ID", "dia"])
    rec, intra, snr = [], {}, []
    for col, key, lab in REC_DIMS:
        prem = pre[col].mean(); posm = pos[col].mean()
        # recuperação: pós(d) → pré(d+1); noite "HIIT" se d+1 é dia de HIIT
        ov = []
        for d in range(1, 7):
            a = posm.xs(d, level="dia") if d in posm.index.get_level_values("dia") else None
            b = prem.xs(d + 1, level="dia") if (d + 1) in prem.index.get_level_values("dia") else None
            if a is None or b is None: continue
            j = pd.concat([a, b], axis=1).dropna(); j.columns = ["a", "b"]
            for ath, r in j.iterrows():
                ov.append((ath, d + 1, r["b"] - r["a"]))
        ovd = pd.DataFrame(ov, columns=["ID", "dia", "delta"])
        hh = ovd[ovd.dia.isin(HIITD)].groupby("ID")["delta"].mean()
        nn = ovd[~ovd.dia.isin(HIITD)].groupby("ID")["delta"].mean()
        jj = pd.concat([hh, nn], axis=1).dropna(); jj.columns = ["h", "n"]
        p = float(stats.wilcoxon(jj["h"], jj["n"]).pvalue) if len(jj) >= 5 else 1.0
        rec.append(dict(dim=key, lab=lab, ph=round(float(hh.mean()), 2), pn=round(float(nn.mean()), 2), p=round(p, 3)))
        # intra-dia: |pós-pré| médio por atleta-dia, HIIT vs fora, como % do escore médio
        dd = (posm - prem).dropna().reset_index(); dd.columns = ["ID", "dia", "delta"]
        dh = dd[dd.dia.isin(HIITD)]["delta"].abs().mean(); dn = dd[~dd.dia.isin(HIITD)]["delta"].abs().mean()
        base = m[col].mean()
        intra[key] = {"h": round(100 * dh / base, 1), "n": round(100 * dn / base, 1)}
        t, hi, no, sr = _snr_one(m.groupby("dia")[col].mean().reindex(range(1, 8)).values)
        snr.append(dict(dim=key, lab=lab, trend=t, hiit=hi, noise=no, snr=sr))
    return {"rec": rec, "intra": intra, "snr": snr}


def an_sensitivity_robust(m):
    """SENSA: robustez do dz(D1→D7) — deixa-um-atleta-de-fora (min/max/amplitude) e
    janela (D1→D7 vs D2→D7), para Vigor/Fadiga/PTH. n de atletas."""
    ad = m.groupby(["ID", "dia"])[["Vigor", "Fadiga", "PTH"]].mean().reset_index()
    loao, window = {}, {}
    labmap = {"Vigor": "Vigor", "Fadiga": "Fadiga", "PTH": "TMD"}
    for col in ["Vigor", "Fadiga", "PTH"]:
        w = ad.pivot_table(index="ID", columns="dia", values=col)
        j = w[[1, 7]].dropna(); d = j[7] - j[1]; full = d.mean() / d.std(ddof=1)
        loos = []
        for ath in j.index:
            dd = d.drop(ath); loos.append(dd.mean() / dd.std(ddof=1))
        j2 = w[[2, 7]].dropna(); d2 = j2[7] - j2[2]; dz2 = d2.mean() / d2.std(ddof=1)
        loao[labmap[col]] = {"full": round(float(full), 2), "min": round(float(min(loos)), 2),
                             "max": round(float(max(loos)), 2), "range": round(float(max(loos) - min(loos)), 3)}
        window[labmap[col]] = {"D1_D7": round(float(full), 2), "D2_D7": round(float(dz2), 2)}
    return {"loao": loao, "window": window, "n_ath": int(ad["ID"].nunique())}


DERIV9 = [("vigor", "Vigor", "Vigor", "#33c2ad"), ("fadiga", "Fadiga", "Fadiga", "#ff7a45"),
          ("tensao", "Tensao", "Tensão", "#4d9de0"), ("depressao", "Depressao", "Depressão", "#c56bd6"),
          ("raiva", "Raiva", "Raiva", "#e0525b"), ("confusao", "Confusao", "Confusão", "#f0a848"),
          ("pth", "PTH", "PTH", "#8b7bf0"), ("fadfisica", "FadFisica", "Fadiga física", "#2fb37a"),
          ("fadmental", "FadMental", "Fadiga mental", "#d6537e")]

def an_deriv(m):
    """DERIV: curvas suavizadas por dia + derivadas (spline cúbica pelos pontos pré/pós),
    estatísticas por dimensão, acoplamento agudo/crônico, pré→pós por dia, transições,
    distribuições diárias e PCA. Método documentado e reprodutível (substitui a
    suavização original irrecuperável)."""
    import pingouin as pg
    from scipy.interpolate import PchipInterpolator
    xgrid = list(np.round(np.linspace(1, 7.2, 110), 3))
    xg = np.array(xgrid)
    pre = m[m.is_pre].groupby(["ID", "dia"]); pos = m[m.is_pos].groupby(["ID", "dia"])
    prem = m[m.is_pre].groupby("dia"); posm = m[m.is_pos].groupby("dia")
    ad = m.groupby(["ID", "dia"])
    vars_, stats_, ac_ = {}, {}, {}
    for key, col, lab, color in DERIV9:
        pm = prem[col].mean(); po = posm[col].mean()
        raw = [[1.0, round(float(pm[1]), 3)]]
        for d in range(2, 8):
            raw.append([round(d - 0.2, 1), round(float(pm[d]), 3)])
            raw.append([round(d + 0.2, 1), round(float(po[d]), 3)])
        rx = np.array([p[0] for p in raw]); ry = np.array([p[1] for p in raw])
        from scipy.ndimage import uniform_filter1d
        sp = PchipInterpolator(rx, ry); sig = sp(xg)  # preserva a forma (sem overshoot)
        # derivadas numéricas com suavização leve (reduz o dente do gradiente numérico)
        d1 = uniform_filter1d(np.gradient(sig, xg), size=7, mode="nearest")
        d2 = uniform_filter1d(np.gradient(d1, xg), size=9, mode="nearest")
        infl = [round(float(xg[i]), 1) for i in range(1, len(xg)) if d2[i - 1] * d2[i] < 0]
        vpk_i = int(np.argmin(d1)) if abs(d1.min()) > abs(d1.max()) else int(np.argmax(d1))
        vars_[key] = dict(lab=lab, c=color, raw=raw, sig=[round(float(v), 3) for v in sig],
                          d1=[round(float(v), 3) for v in d1], d2=[round(float(v), 3) for v in d2],
                          ymin=round(float(sig.min()), 2), ymax=round(float(sig.max()), 2),
                          min_x=round(float(xg[int(np.argmin(sig))]), 1), max_x=round(float(xg[int(np.argmax(sig))]), 1),
                          infl=infl, vpk=round(float(d1[vpk_i]), 2), vpk_x=round(float(xg[vpk_i]), 1))
        # estatísticas
        allv = m[col]; mean = float(allv.mean()); sd = float(allv.std())
        dgm = m.groupby("dia")[col].mean()
        d1v, d7v = float(dgm[1]), float(dgm[7])
        w = ad[col].mean().reset_index().pivot_table(index="ID", columns="dia", values=col).dropna()
        chi, fp = stats.friedmanchisquare(*[w[c] for c in range(1, 8)])
        W = chi / (len(w) * 6)
        j = w[[1, 7]].dropna(); dd = j[7] - j[1]; dz = float(dd.mean() / dd.std(ddof=1))
        p17 = float(stats.wilcoxon(j[1], j[7]).pvalue)
        prp = pre[col].mean().groupby("ID").mean() if False else m[m.is_pre].groupby("ID")[col].mean()
        pop = m[m.is_pos].groupby("ID")[col].mean()
        jj = pd.concat([prp, pop], axis=1).dropna(); jj.columns = ["pre", "pos"]
        dpp = jj["pos"] - jj["pre"]; dzpp = float(dpp.mean() / dpp.std(ddof=1))
        ppp = float(stats.wilcoxon(jj["pre"], jj["pos"]).pvalue)
        try:
            lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
            icc = float(pg.intraclass_corr(data=lg, targets="ID", raters="dia", ratings="v")
                        .query("Type=='ICC(A,1)'").ICC.iloc[0])
        except Exception:
            icc = 0.0
        sem = sd * np.sqrt(max(1 - icc, 0)); mdc95 = 1.96 * np.sqrt(2) * sem
        tr_, hi_, no_, snr = _snr_one(dgm.reindex(range(1, 8)).values)
        floor = round(100 * float((allv == 0).mean()))
        stats_[key] = dict(m=round(mean, 2), sd=round(sd, 2), cv=round(100 * sd / mean) if mean else 0,
                           floor=floor, icc=round(icc, 2), mdc95=round(float(mdc95), 1),
                           chi=round(float(chi), 1), fp=round(float(fp), 3), W=round(float(W), 2),
                           d1=round(d1v, 1), d7=round(d7v, 1), delta=round(d7v - d1v, 1), dz=round(dz, 2),
                           p17=float(p17), sig17=bool(p17 < .05), pre=round(float(jj["pre"].mean()), 2),
                           pos=round(float(jj["pos"].mean()), 2), dzpp=round(dzpp, 2), ppp=float(ppp),
                           sigpp=bool(ppp < .05), ag=round(dzpp, 2), cr=round(d7v - d1v, 1), crdz=round(dz, 2),
                           crsig=bool(p17 < .05), infl=infl[0] if infl else None,
                           vpk=round(float(d1[vpk_i]), 1), vpkx=round(float(xg[vpk_i]), 1),
                           snr=snr, noise=round(no_ / 100, 2), amp=round(float(sig.max() - sig.min()), 1))
        ac_[key] = dict(ag=round(dzpp, 2), cr=round(d7v - d1v, 1), dz=round(dz, 2), sig=bool(p17 < .05))
    # pré→pós por dia
    prepos_dia = {}
    for d in range(2, 8):
        prepos_dia[str(d)] = {}
        for key, col, _, _ in DERIV9:
            a = pre[col].mean().xs(d, level="dia") if (d) in pre[col].mean().index.get_level_values("dia") else None
            b = pos[col].mean().xs(d, level="dia") if (d) in pos[col].mean().index.get_level_values("dia") else None
            if a is None or b is None:
                prepos_dia[str(d)][key] = {"dz": 0.0, "sig": False}; continue
            jj = pd.concat([a, b], axis=1).dropna(); jj.columns = ["a", "b"]; e = jj["b"] - jj["a"]
            dz = float(e.mean() / e.std(ddof=1)) if e.std(ddof=1) else 0.0
            p = float(stats.wilcoxon(jj["a"], jj["b"]).pvalue) if len(jj) >= 5 and e.std(ddof=1) else 1.0
            prepos_dia[str(d)][key] = {"dz": round(dz, 3), "sig": bool(p < .05)}
    # transições (12) × 9 dims
    prd = pre; pod = pos
    trans = []
    for d in range(1, 7):
        for lab, tipo, a_src, b_src, da, db in [(f"D{d} base→D{d+1} pré" if d == 1 else f"D{d}→D{d+1} pré", "Recuperação", pod, prd, d, d + 1),
                                                (f"D{d+1} pré→pós", "Agudo", prd, pod, d + 1, d + 1)]:
            v = {}
            for key, col, _, _ in DERIV9:
                am = a_src[col].mean(); bm = b_src[col].mean()
                A = am.xs(da, level="dia") if da in am.index.get_level_values("dia") else None
                B = bm.xs(db, level="dia") if db in bm.index.get_level_values("dia") else None
                if A is None or B is None:
                    v[key] = {"dz": 0.0, "sig": False}; continue
                jj = pd.concat([A, B], axis=1).dropna(); jj.columns = ["a", "b"]; e = jj["b"] - jj["a"]
                dz = float(e.mean() / e.std(ddof=1)) if e.std(ddof=1) else 0.0
                p = float(stats.wilcoxon(jj["a"], jj["b"]).pvalue) if len(jj) >= 5 and e.std(ddof=1) else 1.0
                v[key] = {"dz": round(dz, 3), "sig": bool(p < .05)}
            trans.append({"lab": lab, "tipo": tipo, "v": v})
    # distribuições diárias (média atleta-dia por dia)
    dist = {}
    for key, col, _, _ in DERIV9:
        dm = ad[col].mean().reset_index()
        dist[key] = {str(d): [round(float(x), 1) for x in dm[dm.dia == d][col]] for d in range(1, 8)}
    # PCA (variância + cargas)
    pca_p = an_pca(m)
    # load = lista de 6 pares [carga_PC1, carga_PC2] (uma por dimensão)
    load2d = [[pca_p["load"]["PCo1"][i], pca_p["load"]["PCo2"][i]] for i in range(6)]
    pca = {"dims": ["Vigor", "Fadiga", "Tensão", "Depressão", "Raiva", "Confusão"],
           "keys": ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao"],
           "load": load2d, "ve": pca_p["var"]}
    return {"x": xgrid, "vars": vars_, "ac": ac_, "trans": trans, "prepos_dia": prepos_dia,
            "order": [k for k, _, _, _ in DERIV9], "stats": stats_, "dist": dist, "pca": pca}


def run():
    m = lh.read_delta("silver", "mood")
    wb = lh.read_delta("silver", "wellbeing")
    it = lh.read_delta("silver", "brums_items")
    lh.write_delta("gold", "an_athlete_profiles", an_athlete_profiles(m)); print("[gold] an_athlete_profiles")
    lh.write_delta("gold", "an_deriv", pd.DataFrame([dict(payload=json.dumps(an_deriv(m)))])); print("[gold] an_deriv")
    lh.write_delta("gold", "an_pca", pd.DataFrame([dict(payload=json.dumps(an_pca(m)))])); print("[gold] an_pca")
    lh.write_delta("gold", "an_sensitivity", pd.DataFrame([dict(payload=json.dumps(an_sensitivity(m)))])); print("[gold] an_sensitivity")
    lh.write_delta("gold", "an_recovery", pd.DataFrame([dict(payload=json.dumps(an_recovery(m)))])); print("[gold] an_recovery")
    lh.write_delta("gold", "an_sensitivity_robust", pd.DataFrame([dict(payload=json.dumps(an_sensitivity_robust(m)))])); print("[gold] an_sensitivity_robust")
    vc, vcurve, veff = an_variance(m)
    lh.write_delta("gold", "an_variance", vc); lh.write_delta("gold", "an_variance_curves", vcurve)
    lh.write_delta("gold", "an_variance_eff", veff); print("[gold] an_variance (+curves +eff)")
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
