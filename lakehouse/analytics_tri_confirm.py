# -*- coding: utf-8 -*-
"""Confirmação da triangulação por métodos convergentes + recálculo sob referência
externa. Para cada valor-chave da triangulação computa vias independentes e verifica
se concordam:
  - efeito agudo e contraste HIIT×jogo: Wilcoxon (já feito) + permutação pareada
    (sign-flip) + IC95% do dz por bootstrap → concordância.
  - sono/estresse por tipo de dia: idem.
  - sono × perfil (favorável→risco): Kruskal (já feito) + tendência de Kendall
    (grupos ordenados) + Spearman(Epworth, índice-iceberg contínuo), nos dois modos
    de padronização (interno × externo).
  - partes dependentes de perfil recomputadas sob padronização EXTERNA.
Escreve gold an_tric_* e um payload (TRICONF). Determinístico (SEED=7).
Nota: efeitos padronizados (dz) e ICC são INVARIANTES à padronização linear por
variável, então acute/contrast/ICC não mudam com referência externa (demonstrado)."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from scipy import stats
import lh

SEED = 7
VARS = [("vigor", "Vigor", "Vigor"), ("fadiga", "Fadiga", "Fadiga"),
        ("fadfisica", "FadFisica", "Fadiga física"), ("tensao", "Tensao", "Tensão"),
        ("depressao", "Depressao", "Depressão"), ("raiva", "Raiva", "Raiva"),
        ("confusao", "Confusao", "Confusão"), ("pth", "PTH", "PTH")]
CAT = {"HIIT": "HIIT", "Jogo": "Jogo", "Baseline": "Outro", "Forca": "Outro"}
SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
NEG = ["Tensao", "Depressao", "Raiva", "Fadiga", "Confusao"]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
NAMES = list(CENT); CM = np.array([CENT[k] for k in NAMES])
NORM_M = {"Tensao": 4.0, "Depressao": 2.0, "Raiva": 2.8, "Vigor": 8.0, "Fadiga": 5.0, "Confusao": 2.6}
NORM_SD = {"Tensao": 3.0, "Depressao": 2.6, "Raiva": 3.0, "Vigor": 3.5, "Fadiga": 3.6, "Confusao": 2.7}
RISCO = ["Iceberg invertido", "Everest invertido", "Barbatana de tubarao"]
FAVOR = ["Iceberg", "Superficie"]


def _paired(a, b):
    j = pd.concat([a, b], axis=1).dropna(); j.columns = ["a", "b"]
    return (j["b"] - j["a"]).values


def dz_of(d):
    sd = d.std(ddof=1)
    return float(d.mean() / sd) if (len(d) >= 5 and sd > 0) else 0.0


def boot_ci(d, B=4000):
    rng = np.random.default_rng(SEED); n = len(d); out = []
    for _ in range(B):
        s = d[rng.integers(0, n, n)]; sd = s.std(ddof=1)
        out.append(s.mean() / sd if sd > 0 else 0.0)
    return np.percentile(out, [2.5, 97.5])


def perm_p(d, B=20000):
    """Permutação pareada (sign-flip): H0 = mediana das diferenças = 0."""
    rng = np.random.default_rng(SEED); n = len(d); obs = abs(d.mean())
    signs = rng.integers(0, 2, (B, n)) * 2 - 1
    perm = np.abs((signs * d).mean(1))
    return float((perm >= obs).mean())


def confirm_pair(a, b):
    d = _paired(a, b)
    if len(d) < 5:
        return None
    dz = dz_of(d); lo, hi = boot_ci(d)
    try:
        pw = float(stats.wilcoxon(d).pvalue)
    except Exception:
        pw = 1.0
    pp = perm_p(d)
    ci_excl = bool(lo * hi > 0)  # IC não cruza zero
    concord = (pw < .05) == (pp < .05) == ci_excl
    return dict(dz=round(dz, 2), ic=[round(float(lo), 2), round(float(hi), 2)],
                p_wilcoxon=round(pw, 3), p_perm=round(pp, 3), ic_exclui_zero=ci_excl,
                concordam=bool(concord))


def classify(m, modo):
    if modo == "interno":
        mu, sd = m[SUB].mean(), m[SUB].std()
    else:
        mu, sd = pd.Series(NORM_M)[SUB], pd.Series(NORM_SD)[SUB]
    Z = (m[SUB] - mu) / sd
    return Z.apply(lambda r: NAMES[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)


def ice_index(m, modo):
    if modo == "interno":
        mu, sd = m[SUB].mean(), m[SUB].std()
    else:
        mu, sd = pd.Series(NORM_M)[SUB], pd.Series(NORM_SD)[SUB]
    Z = (m[SUB] - mu) / sd
    return Z["Vigor"] - Z[NEG].mean(axis=1)


def kendall_trend(groups_vals):
    """Tendência: grupos ordenados 0<1<2 vs valor (Kendall tau-b)."""
    g, v = [], []
    for i, arr in enumerate(groups_vals):
        g += [i] * len(arr); v += list(arr)
    if len(set(g)) < 2:
        return np.nan, np.nan
    tau, p = stats.kendalltau(g, v)
    return float(tau), float(p)


def confirm_profile(wb, m, modo):
    mu, sd = m[SUB].mean(), m[SUB].std()
    ad = m.groupby(["ID", "dia"])[SUB].mean()
    prof = classify(ad.reset_index(), modo)
    pad = ad.reset_index()[["ID", "dia"]].copy(); pad["perfil"] = prof.values
    mg = wb.merge(pad, on=["ID", "dia"])
    mg["grp"] = np.where(mg.perfil.isin(RISCO), 2, np.where(mg.perfil.isin(FAVOR), 0, 1))
    # índice-iceberg contínuo por atleta-dia
    idx = ice_index(ad.reset_index(), modo)
    icd = ad.reset_index()[["ID", "dia"]].copy(); icd["idx"] = idx.values
    mgi = wb.merge(icd, on=["ID", "dia"])
    out = {}
    for c, lab in [("epworth", "Epworth"), ("pss", "PSS")]:
        gs = [mg[mg.grp == k][c].dropna().values for k in [0, 1, 2]]
        H, pk = stats.kruskal(*gs)
        tau, pt = kendall_trend(gs)
        # Spearman (nível atleta) valor × índice-iceberg
        at = mgi.groupby("ID").apply(lambda d: pd.Series({"m": d[c].mean(), "i": d["idx"].mean()}))
        rho, ps = stats.spearmanr(at["m"], at["i"])
        out[c] = dict(medida=lab, fav=round(float(np.mean(gs[0])), 1), neu=round(float(np.mean(gs[1])), 1),
                      risco=round(float(np.mean(gs[2])), 1),
                      kruskal_p=round(float(pk), 3), kendall_tau=round(tau, 2), kendall_p=round(float(pt), 3),
                      spearman_rho=round(float(rho), 2), spearman_p=round(float(ps), 3),
                      concordam=bool((pk < .05) == (pt < .05)))
    return out


def prof_day(m, modo):
    ad = m.copy(); ad["perfil"] = classify(ad, modo).values
    disp = {"Iceberg": "Iceberg", "Superficie": "Superfície", "Submerso": "Submerso",
            "Everest invertido": "Everest invertido", "Barbatana de tubarao": "Barbatana de tubarão",
            "Iceberg invertido": "Iceberg invertido"}
    out = {}
    for d in range(1, 8):
        vc = ad[ad.dia == d]["perfil"].value_counts(normalize=True).mul(100)
        out[str(d)] = {disp[nm]: round(float(vc.get(nm, 0.0)), 1) for nm in NAMES}
    return out


def run():
    m = lh.read_delta("silver", "mood"); wb = lh.read_delta("silver", "wellbeing")
    m = m.copy(); m["cat"] = m["day_type"].map(CAT)

    # 1) efeito agudo por tipo de dia — confirmação
    acute = []
    for key, col, lab in VARS:
        for c in ["HIIT", "Jogo", "Outro"]:
            sub = m[m.cat == c]
            pre = sub[sub.is_pre].groupby("ID")[col].mean(); pos = sub[sub.is_pos].groupby("ID")[col].mean()
            r = confirm_pair(pre, pos)
            if r:
                acute.append(dict(var=key, lab=lab, tipo=c, **r))
    # 2) contraste HIIT×jogo — confirmação + FDR sobre p_perm
    contrast = []
    for key, col, lab in VARS:
        hi = m[m.dia.isin([2, 4])].groupby("ID")[col].mean()
        jo = m[m.dia.isin([3, 5])].groupby("ID")[col].mean()
        r = confirm_pair(jo, hi)  # hi - jo
        if r:
            contrast.append(dict(var=key, lab=lab, **r))
    cp = np.array([c["p_perm"] for c in contrast]); o = np.argsort(cp); rk = np.empty_like(o); rk[o] = np.arange(1, len(cp) + 1)
    fdr = np.minimum.accumulate((cp * len(cp) / rk)[o][::-1])[::-1]; adj = np.empty_like(fdr); adj[o] = np.clip(fdr, 0, 1)
    for c, q in zip(contrast, adj):
        c["fdr_perm"] = round(float(q), 3); c["sig_fdr_perm"] = bool(q < .05)
    # 3) sono/estresse por tipo de dia — confirmação
    dtype = m.groupby("dia")["day_type"].first().map(CAT); w = wb.copy(); w["cat"] = w["dia"].map(dtype)
    wbday = []
    for c, lab in [("epworth", "Epworth"), ("pss", "PSS")]:
        hi = w[w.dia.isin([2, 4, 7])].groupby("ID")[c].mean(); jo = w[w.dia.isin([3, 5])].groupby("ID")[c].mean()
        r = confirm_pair(jo, hi)
        if r:
            wbday.append(dict(medida=lab, **r))
    # 4) perfil × sono/estresse — interno e externo
    prof_int = confirm_profile(wb, m, "interno"); prof_ext = confirm_profile(wb, m, "externo")
    # 5) prof_day interno × externo (o que muda)
    pd_int = prof_day(m, "interno"); pd_ext = prof_day(m, "externo")

    payload = dict(acute=acute, contrast=contrast, wbday=wbday,
                   prof_int=prof_int, prof_ext=prof_ext, pd_int=pd_int, pd_ext=pd_ext,
                   n_acute_concord=sum(a["concordam"] for a in acute), n_acute=len(acute),
                   n_contrast_concord=sum(c["concordam"] for c in contrast), n_contrast=len(contrast))
    lh.write_delta("gold", "an_tric_acute", pd.DataFrame(acute)); print("[gold] an_tric_acute", len(acute))
    lh.write_delta("gold", "an_tric_contrast", pd.DataFrame(contrast)); print("[gold] an_tric_contrast", len(contrast))
    lh.write_delta("gold", "an_tric_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_tric_payload · acute concord %d/%d · contrast concord %d/%d"
          % (payload["n_acute_concord"], payload["n_acute"], payload["n_contrast_concord"], payload["n_contrast"]))
    return payload


if __name__ == "__main__":
    p = run()
    print("\nCONTRASTE HIIT×jogo (confirmação):")
    for c in sorted(p["contrast"], key=lambda z: -z["dz"]):
        print(f"  {c['lab']:14s} dz={c['dz']:+.2f} IC{c['ic']} pW={c['p_wilcoxon']:.3f} pPerm={c['p_perm']:.3f} "
              f"FDR={c['fdr_perm']:.3f} concord={c['concordam']}")
    print("\nSONO×PERFIL (Epworth) interno vs externo:")
    for modo, pr in [("interno", p["prof_int"]), ("externo", p["prof_ext"])]:
        e = pr["epworth"]
        print(f"  {modo}: fav {e['fav']} → risco {e['risco']} · Kruskal p={e['kruskal_p']} · "
              f"Kendall tau={e['kendall_tau']} p={e['kendall_p']} · Spearman rho={e['spearman_rho']} p={e['spearman_p']}")
