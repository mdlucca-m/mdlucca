# -*- coding: utf-8 -*-
"""Análise estratificada: dias de HIIT (D2/D4/D7) × dias SEM HIIT (D1/D3/D5/D6).

Refaz, DENTRO de cada estrato, a bateria que já usamos (descritiva, omnibus,
tamanho de efeito, triangulação por métodos convergentes) e relaciona com o
perfil de humor, a sonolência (Epworth) e o estresse (PSS). Acrescenta o ajuste
LOGARÍTMICO pelo pico de velocidade (PV do T-CAR) e regressões (linear e
logística bicaudal), depois compara tudo.

Ressalvas honestas:
  - Grupo único, observacional; dias confundidos com o tempo/carga acumulada.
  - Estrato HIIT tem 3 dias; sem-HIIT tem 4 — potência baixa para tendência.
  - O PV (códigos P) só se liga ao humor pelos pares casados agregados por atleta
    (silver.pv_mood, n=25), SEM granularidade de dia — por isso o ajuste log/PV é
    de nível semanal (não estratificável por dia), e a logística de risco usa
    variáveis de nível-atleta que existem (humor, Epworth, PSS), não o PV.

Gera em gold:
  an_str_desc    — descritiva+efeito por dimensão × estrato (média, dz 1º→último, Friedman/W)
  an_str_tri     — triangulação (1º→último) por dimensão × estrato (dz, IC boot, Wilcoxon, perm)
  an_str_wb      — Epworth/PSS por estrato + correlações mood×sono/estresse por estrato
  an_str_prof    — prevalência de perfil dominante por estrato
  an_pv_log      — ajuste linear × logarítmico mood~PV (n=25) por dimensão
  an_logit       — logística bicaudal risco ~ (Epworth, PSS, fadiga)
  an_str_payload — JSON do painel
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
from scipy import stats
import lh

SEED = 7
DIMS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
        ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]
HIIT_D = [2, 4, 7]
NOHIIT_D = [1, 3, 5, 6]
STRATA = [("HIIT", HIIT_D), ("SemHIIT", NOHIIT_D)]


def _dz(diff):
    diff = np.asarray(diff, float)
    sd = diff.std(ddof=1)
    return float(diff.mean() / sd) if sd else 0.0


def _boot_ci(diff, n=4000):
    rng = np.random.default_rng(SEED)
    diff = np.asarray(diff, float)
    bs = [_dz(rng.choice(diff, len(diff), replace=True)) for _ in range(n)]
    return [round(float(np.percentile(bs, 2.5)), 3), round(float(np.percentile(bs, 97.5)), 3)]


def _perm(a, b, n=20000):
    rng = np.random.default_rng(SEED)
    d = np.asarray(a, float) - np.asarray(b, float)
    obs = abs(d.mean())
    cnt = 0
    for _ in range(n):
        sgn = rng.choice([-1, 1], len(d))
        if abs((d * sgn).mean()) >= obs:
            cnt += 1
    return (cnt + 1) / (n + 1)


def _pivot(ad, col, days):
    w = ad[ad.dia.isin(days)].pivot_table(index="ID", columns="dia", values=col)
    return w.dropna()


def desc_tri():
    ad = lh.read_delta("gold", "athlete_day_unified")
    rows_d, rows_t = [], []
    for col, lab in DIMS:
        for sname, days in STRATA:
            w = _pivot(ad, col, days)
            if len(w) < 5:
                continue
            first, last = w[days[0]], w[days[-1]]
            diff = (last - first).values
            dz = _dz(diff)
            # Friedman entre os dias do estrato (casos completos)
            try:
                fr = stats.friedmanchisquare(*[w[d].values for d in days])
                chi, pf = float(fr.statistic), float(fr.pvalue)
                k = len(days); Wk = chi / (len(w) * (k - 1))
            except Exception:
                chi, pf, Wk = np.nan, np.nan, np.nan
            rows_d.append(dict(dim=col, dim_lab=lab, estrato=sname, n=int(len(w)),
                               media=round(float(w.values.mean()), 2),
                               primeiro=round(float(first.mean()), 2), ultimo=round(float(last.mean()), 2),
                               dz=round(dz, 3), chi=round(chi, 2) if chi == chi else None,
                               p_fried=round(pf, 4) if pf == pf else None,
                               W=round(float(Wk), 3) if Wk == Wk else None,
                               mag=("grande" if abs(dz) >= .8 else "médio" if abs(dz) >= .5 else "pequeno" if abs(dz) >= .2 else "trivial")))
            # triangulação do contraste 1º→último
            try:
                pw = float(stats.wilcoxon(last, first).pvalue)
            except Exception:
                pw = np.nan
            ci = _boot_ci(diff); pp = _perm(last.values, first.values)
            exclui = ci[0] > 0 or ci[1] < 0
            concord = (exclui == (pw < 0.05)) and (exclui == (pp < 0.05))
            rows_t.append(dict(dim=col, dim_lab=lab, estrato=sname, dz=round(dz, 3),
                               ic=ci, p_wilcoxon=round(pw, 4) if pw == pw else None,
                               p_perm=round(float(pp), 4), ic_exclui_zero=bool(exclui),
                               concordam=bool(concord)))
    return pd.DataFrame(rows_d), pd.DataFrame(rows_t)


def wellbeing_strata():
    ad = lh.read_delta("gold", "athlete_day_unified")
    rows, corr = [], []
    for sname, days in STRATA:
        sub = ad[ad.dia.isin(days)]
        for wcol, wlab in [("epworth", "Epworth"), ("pss", "PSS")]:
            s = sub[wcol].dropna()
            w = _pivot(ad, wcol, days)
            first = w[days[0]] if len(w) else pd.Series(dtype=float)
            last = w[days[-1]] if len(w) else pd.Series(dtype=float)
            dz = _dz((last - last.index.map(lambda i: first.get(i, np.nan))).dropna().values) if len(w) else 0.0
            try:
                dz = _dz((w[days[-1]] - w[days[0]]).values)
            except Exception:
                dz = 0.0
            rows.append(dict(estrato=sname, medida=wlab, media=round(float(s.mean()), 2),
                             dz=round(dz, 3), n=int(w.shape[0]) if len(w) else 0))
        # correlações mood × sono/estresse dentro do estrato (nível atleta-dia)
        for wcol, wlab in [("epworth", "Epworth"), ("pss", "PSS")]:
            for col, lab in [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("pth", "PTH")]:
                d = sub[[wcol, col]].dropna()
                if len(d) > 6:
                    rho, p = stats.spearmanr(d[wcol], d[col])
                    corr.append(dict(estrato=sname, par=f"{wlab} × {lab}",
                                     rho=round(float(rho), 3), p=round(float(p), 4), sig=bool(p < 0.05)))
    return pd.DataFrame(rows), pd.DataFrame(corr)


def prof_strata():
    """prevalência do perfil dominante por estrato (a partir do dominante por dia)."""
    pbd = lh.read_delta("gold", "an_profiles_byday")
    rows = []
    for sname, days in STRATA:
        sub = pbd[pbd.dia.isin(days)]
        vc = sub.dominante.value_counts(normalize=True) * 100
        for perf, pct in vc.items():
            rows.append(dict(estrato=sname, perfil=str(perf), pct=round(float(pct), 1)))
    return pd.DataFrame(rows)


def pv_log():
    """ajuste linear × logarítmico mood ~ PV (pares casados, n=25) por dimensão."""
    import statsmodels.api as sm
    pm = lh.read_delta("silver", "pv_mood")
    order = [("Vigor", "Vigor"), ("Fadiga", "Fadiga"), ("FadFisica", "Fadiga física"),
             ("TMD", "TMD"), ("Tensao", "Tensão"), ("Depressao", "Depressão"),
             ("Raiva", "Raiva"), ("Confusao", "Confusão")]
    rows = []
    for key, lab in order:
        d = pm[pm.dim == key].dropna(subset=["pv", "mood"]).sort_values("pair")
        if len(d) < 8:
            continue
        x = d["pv"].values.astype(float); y = d["mood"].values.astype(float)
        # linear
        Xl = sm.add_constant(x); rl = sm.OLS(y, Xl).fit()
        # log: y ~ ln(x)
        Xg = sm.add_constant(np.log(x)); rg = sm.OLS(y, Xg).fit()
        rho, prho = stats.spearmanr(x, y)
        pts = [[round(float(a), 2), round(float(b), 2)] for a, b in zip(x, y)]
        rows.append(dict(dim=key, dim_lab=lab, n=int(len(d)),
                         b_lin=round(float(rl.params[1]), 3), r2_lin=round(float(rl.rsquared), 3),
                         aic_lin=round(float(rl.aic), 1), p_lin=round(float(rl.pvalues[1]), 4),
                         a_lin=round(float(rl.params[0]), 3),
                         b_log=round(float(rg.params[1]), 3), r2_log=round(float(rg.rsquared), 3),
                         aic_log=round(float(rg.aic), 1), p_log=round(float(rg.pvalues[1]), 4),
                         a_log=round(float(rg.params[0]), 3),
                         melhor=("log" if rg.aic < rl.aic else "linear"),
                         spearman=round(float(rho), 3), p_spearman=round(float(prho), 4),
                         xmin=round(float(x.min()), 2), xmax=round(float(x.max()), 2), pts=pts))
    return pd.DataFrame(rows)


def logit():
    """logística bicaudal: risco (perfil) ~ Epworth + PSS + fadiga (nível atleta)."""
    import statsmodels.api as sm
    pa = lh.read_delta("gold", "an_profile_athlete")[["ID", "risco", "fadiga", "vigor"]].copy()
    ad = lh.read_delta("gold", "athlete_day_unified")
    wb = ad.groupby("ID")[["epworth", "pss"]].mean().reset_index()
    d = pa.merge(wb, on="ID", how="left").dropna()
    d["risco"] = d["risco"].astype(int)
    out = []
    preds = [("epworth", "Epworth"), ("pss", "PSS"), ("fadiga", "Fadiga")]
    # modelo multivariado (z-padronizado) + univariados p/ robustez
    Z = d.copy()
    for k, _ in preds:
        Z[k] = (Z[k] - Z[k].mean()) / (Z[k].std(ddof=0) or 1)
    try:
        X = sm.add_constant(Z[[k for k, _ in preds]])
        r = sm.Logit(Z["risco"], X).fit(disp=0)
        ci = r.conf_int()
        for k, lab in preds:
            b = float(r.params[k]); p = float(r.pvalues[k])  # p bicaudal (default)
            out.append(dict(preditor=lab, tipo="multivariado", OR=round(float(np.exp(b)), 3),
                            ic_lo=round(float(np.exp(ci.loc[k, 0])), 3), ic_hi=round(float(np.exp(ci.loc[k, 1])), 3),
                            p=round(p, 4), sig=bool(p < 0.05), n=int(len(d))))
    except Exception as e:
        print("  logit multivariado falhou", e)
    return pd.DataFrame(out)


def mood_matrix():
    """médias por atleta das sete dimensões (nível do atleta, evita pseudorreplicação)."""
    ad = lh.read_delta("gold", "athlete_day_unified")
    cols = [c for c, _ in DIMS]
    g = ad.groupby("ID")[cols].mean().reset_index().sort_values("ID")
    atl = [{"ID": r.ID, "vals": [round(float(getattr(r, c)), 2) for c in cols]} for r in g.itertuples()]
    return {"dims": [{"dim": c, "lab": l} for c, l in DIMS], "atl": atl}


def run():
    desc, tri = desc_tri()
    wb, corr = wellbeing_strata()
    prof = prof_strata()
    pvl = pv_log()
    lg = logit()

    payload = {
        "desc": desc.to_dict("records"), "tri": tri.to_dict("records"),
        "wb": wb.to_dict("records"), "corr": corr.to_dict("records"),
        "prof": prof.to_dict("records"), "pv_log": pvl.to_dict("records"),
        "logit": lg.to_dict("records"), "mood_mat": mood_matrix(),
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "notas": [
            "Estratos: HIIT (D2/D4/D7, 3 dias) × sem-HIIT (D1/D3/D5/D6, 4 dias); contraste 1º→último dia de cada estrato.",
            "Triangulação: dz + IC bootstrap (SEED=7) + Wilcoxon + permutação sign-flip; concordam = as três vias apontam o mesmo.",
            "Ajuste log/PV é de nível semanal (pares casados n=25), sem estratificação por dia (fronteira de anonimização A×P).",
            "Logística bicaudal (p bilateral): risco de perfil ~ Epworth, PSS e fadiga padronizados; OR por 1 DP.",
            "Grupo único, T pequeno: leitura descritiva/de rastreio, não causal.",
        ],
    }
    lh.write_delta("gold", "an_str_desc", desc); print("[gold] an_str_desc", desc.shape)
    lh.write_delta("gold", "an_str_tri", tri); print("[gold] an_str_tri", tri.shape)
    lh.write_delta("gold", "an_str_wb", wb); print("[gold] an_str_wb", wb.shape)
    lh.write_delta("gold", "an_str_prof", prof); print("[gold] an_str_prof", prof.shape)
    lh.write_delta("gold", "an_pv_log", pvl); print("[gold] an_pv_log", pvl.shape)
    lh.write_delta("gold", "an_logit", lg); print("[gold] an_logit", lg.shape)
    lh.write_delta("gold", "an_str_corr", corr)
    lh.write_delta("gold", "an_str_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_str_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== contraste 1º→último por estrato (dz · triangulação) ===")
    for r in p["tri"]:
        print(f"  {r['dim_lab']:12} {r['estrato']:8} dz={r['dz']:+.2f} IC[{r['ic'][0]:.2f},{r['ic'][1]:.2f}] pW={r['p_wilcoxon']} pPerm={r['p_perm']} {'✓' if r['concordam'] else '·'}")
    print("\n=== ajuste PV: linear × log ===")
    for r in p["pv_log"]:
        print(f"  {r['dim_lab']:14} lin R²={r['r2_lin']:.2f}(AIC{r['aic_lin']:.0f}) log R²={r['r2_log']:.2f}(AIC{r['aic_log']:.0f}) → {r['melhor']} · ρ={r['spearman']:+.2f}")
    print("\n=== logística bicaudal (risco ~ ...) ===")
    for r in p["logit"]:
        print(f"  {r['preditor']:10} OR={r['OR']:.2f} IC[{r['ic_lo']:.2f},{r['ic_hi']:.2f}] p={r['p']:.3f}{' *' if r['sig'] else ''}")
