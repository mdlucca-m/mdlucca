# -*- coding: utf-8 -*-
"""GOLD · ANÁLISES FÍSICAS — aptidão aeróbia (T-CAR) × humor, a partir do lakehouse.

Fecha a lacuna: a relação aptidão×humor deixa de ser constante fixa no painel e
passa a VIR do gold, auditável e reprodutível (mesmos métodos do estudo).

Fontes (lakehouse):
  silver.physical  — bateria física (P-code), desenho de GRUPO ÚNICO (sem controle)
  silver.pv_mood   — pares pico de velocidade × humor, casados na fonte e anonimizados

Tabelas geradas (an_):
  an_tcar_adapt   adaptação pré→pós (T-CAR PV, CMJ, Baker soma) · grupo único · dz + ttest
  an_pv_mood      ρ de Spearman PV×humor (9 dims) + IC95% bootstrap (semente fixa) + BH-FDR
  an_pv_threshold acima vs abaixo da mediana do PV (Cohen d + Mann-Whitney)
  an_pv_bands     perfil por tercil de PV (baixo/médio/alto) + n por faixa + mediana

Determinismo: o bootstrap usa np.random.default_rng(7) — semente fixa ⇒ IC reprodutível.
"""
from __future__ import annotations
import json
import numpy as np, pandas as pd
from scipy import stats
import lh

SEED = 7
# dimensões e rótulos exatamente como o painel apresenta
DIM_ORDER = ["Vigor", "Fadiga", "FadFisica", "FadMental", "TMD",
             "Tensao", "Depressao", "Raiva", "Confusao"]
LAB = {"Vigor": "Vigor", "Fadiga": "Fadiga", "FadFisica": "Fadiga física",
       "FadMental": "Fadiga mental", "TMD": "PTH (TMD)", "Tensao": "Tensão",
       "Depressao": "Depressão", "Raiva": "Raiva", "Confusao": "Confusão"}
# rótulos curtos usados no bloco de limiar (HDL): PTH sem "(TMD)"
LAB_THR = {"Vigor": "Vigor", "Fadiga": "Fadiga", "FadFisica": "Fadiga física", "TMD": "PTH"}
ADAPT = [("TCARpv", "T-CAR pico de velocidade (km/h)", "tcarpv"),
         ("CMJ", "CMJ (cm)", "cmj"), ("BkSoma", "Baker soma (s)", "bksoma")]


def _dz_paired(a, b):
    x = b - a
    return float(x.mean() / x.std(ddof=1))


def an_tcar_adapt(ph):
    """Adaptação pré→pós de cada teste físico, agrupamento único (todos os atletas)."""
    rows = []
    for v, lab, key in ADAPT:
        a = ph[f"{v}_pre"].astype(float); b = ph[f"{v}_pos"].astype(float)
        m = a.notna() & b.notna(); a, b = a[m].values, b[m].values
        _, p = stats.ttest_rel(a, b)
        rows.append(dict(var=key, lab=lab,
                         pre=round(float(a.mean()), 2), pre_sd=round(float(a.std(ddof=1)), 2),
                         pos=round(float(b.mean()), 2), pos_sd=round(float(b.std(ddof=1)), 2),
                         dz=round(_dz_paired(a, b), 2), p=round(float(p), 4), n=int(m.sum())))
    return pd.DataFrame(rows)


def _wide(pm):
    """pv_mood tidy → PV (vetor) + mood por dimensão (ordena por par p/ reprodutibilidade)."""
    pm = pm.sort_values("pair")
    PV = pm[pm.dim == "Vigor"].set_index("pair")["pv"].sort_index().values
    mood = {d: pm[pm.dim == d].set_index("pair")["mood"].sort_index().values for d in DIM_ORDER}
    return PV, mood


def an_pv_mood(pm):
    """ρ de Spearman PV×humor + IC95% bootstrap (semente fixa) + BH-FDR (9 dimensões)."""
    PV, mood = _wide(pm)
    rng = np.random.default_rng(SEED)
    rows = []
    for k in DIM_ORDER:
        y = mood[k]; r, p = stats.spearmanr(PV, y); bs = []
        for _ in range(5000):
            idx = rng.integers(0, len(PV), len(PV))
            if len(np.unique(PV[idx])) > 2:
                bs.append(stats.spearmanr(PV[idx], y[idx]).correlation)
        lo, hi = np.nanpercentile(bs, [2.5, 97.5])
        rows.append(dict(dim=k, lab=LAB[k], r=round(float(r), 4), p=round(float(p), 4),
                         lo=round(float(lo), 4), hi=round(float(hi), 4)))
    pv = np.array([r["p"] for r in rows])
    o = np.argsort(pv); ranks = np.empty_like(o); ranks[o] = np.arange(1, len(pv) + 1)
    fdr = np.minimum.accumulate((pv * len(pv) / ranks)[o][::-1])[::-1]
    adj = np.empty_like(fdr); adj[o] = np.clip(fdr, 0, 1)
    for i, r in enumerate(rows):
        r["fdr"] = round(float(adj[i]), 4)
    return pd.DataFrame(rows)


def an_pv_threshold(pm):
    """Acima vs abaixo da mediana do PV (Cohen d de amostras independentes + Mann-Whitney)."""
    PV, mood = _wide(pm)
    med = float(np.median(PV)); hi = PV >= med; lo = PV < med
    rows = []
    for k in ["Vigor", "Fadiga", "FadFisica", "TMD"]:
        y = mood[k]; a, b = y[hi], y[lo]
        dz = (a.mean() - b.mean()) / np.sqrt(((a.std(ddof=1) ** 2) + (b.std(ddof=1) ** 2)) / 2)
        _, p = stats.mannwhitneyu(a, b)
        rows.append(dict(dim=k, lab=LAB_THR[k], median=round(med, 1),
                         hi=round(float(a.mean()), 2), lo=round(float(b.mean()), 2),
                         dz=round(float(dz), 2), p=round(float(p), 3)))
    return pd.DataFrame(rows)


def an_pv_bands(pm):
    """Perfil médio do humor por tercil de PV (baixo/médio/alto) + n por faixa."""
    PV, mood = _wide(pm)
    t1, t2 = np.quantile(PV, [1 / 3, 2 / 3])
    band = np.where(PV < t1, 0, np.where(PV < t2, 1, 2))
    med = float(np.median(PV))
    rows = []
    for k in ["Vigor", "Fadiga", "FadFisica"]:
        for b in range(3):
            sel = band == b
            rows.append(dict(dim=k, lab=LAB_THR[k], band=b,
                             mean=round(float(mood[k][sel].mean()), 2),
                             n=int(sel.sum()), median=round(med, 1)))
    return pd.DataFrame(rows)


ALO_DIMS = [("FadFisica", "Fadiga física"), ("Fadiga", "Fadiga"), ("Vigor", "Vigor"), ("TMD", "PTH")]

def an_allometry(pm):
    """Ajuste alométrico (lei de potência) humor = a·PV^b por regressão log-log
    (só valores positivos do humor). Devolve b, IC95%, R², p e o intercepto log (a=ln)."""
    rows = []
    for d, lab in ALO_DIMS:
        sub = pm[pm.dim == d].sort_values("pair")
        y, x = sub["mood"].values, sub["pv"].values
        mk = y > 0; y, x = y[mk], x[mk]
        lx, ly = np.log(x), np.log(y)
        b, a = np.polyfit(lx, ly, 1); n = len(x)
        yhat = a + b * lx; ss_res = float(((ly - yhat) ** 2).sum())
        sxx = float(((lx - lx.mean()) ** 2).sum()); r2 = float(np.corrcoef(lx, ly)[0, 1] ** 2)
        se = np.sqrt(ss_res / (n - 2) / sxx); tcrit = stats.t.ppf(0.975, n - 2)
        t = b / se; p = float(2 * (1 - stats.t.cdf(abs(t), n - 2)))
        rows.append(dict(dim=d, lab=lab, b=round(float(b), 2), lo=round(float(b - tcrit * se), 2),
                         hi=round(float(b + tcrit * se), 2), r2=round(r2, 2), p=round(p, 3),
                         a=round(float(a), 4), n=int(n)))
    return pd.DataFrame(rows)


def an_pvmodel(pm):
    """Compara modelos PV→humor por RMSE de validação leave-one-out: Linear,
    Logarítmico, Alométrico, XGBoost, LightGBM; base = prever a média. FadFísica e Vigor."""
    import xgboost as xgb, lightgbm as lgb
    from sklearn.model_selection import LeaveOneOut
    names = ["Linear", "Logarítmico", "Alométrico", "XGBoost", "LightGBM"]
    out = {"names": names}
    for d in ["FadFisica", "Vigor"]:
        sub = pm[pm.dim == d].sort_values("pair")
        y = sub["mood"].values.astype(float); x = sub["pv"].values.astype(float)
        loo = LeaveOneOut(); preds = {k: [] for k in names}; truth = []
        base_pred = []
        for tr, te in loo.split(x):
            xtr, ytr, xte = x[tr], y[tr], x[te]
            truth.append(y[te][0]); base_pred.append(ytr.mean())
            b1, b0 = np.polyfit(xtr, ytr, 1); preds["Linear"].append(b0 + b1 * xte[0])
            bl1, bl0 = np.polyfit(np.log(xtr), ytr, 1); preds["Logarítmico"].append(bl0 + bl1 * np.log(xte[0]))
            mk = ytr > 0
            if mk.sum() > 2:
                ab, aa = np.polyfit(np.log(xtr[mk]), np.log(ytr[mk]), 1)
                preds["Alométrico"].append(np.exp(aa + ab * np.log(xte[0])))
            else:
                preds["Alométrico"].append(ytr.mean())
            xg = xgb.XGBRegressor(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=SEED, verbosity=0)
            xg.fit(xtr.reshape(-1, 1), ytr); preds["XGBoost"].append(float(xg.predict(xte.reshape(-1, 1))[0]))
            lg = lgb.LGBMRegressor(n_estimators=80, max_depth=2, learning_rate=0.05, random_state=SEED, verbose=-1)
            lg.fit(xtr.reshape(-1, 1), ytr); preds["LightGBM"].append(float(lg.predict(xte.reshape(-1, 1))[0]))
        truth = np.array(truth)
        rmse = lambda pr: float(np.sqrt(np.mean((truth - np.array(pr)) ** 2)))
        vals = [round(rmse(preds[k]), 2) for k in names]
        out[d] = {"vals": vals, "base": round(rmse(base_pred), 2), "best": names[int(np.argmin(vals))]}
    return out


def run():
    ph = lh.read_delta("silver", "physical")
    pm = lh.read_delta("silver", "pv_mood")
    lh.write_delta("gold", "an_tcar_adapt", an_tcar_adapt(ph)); print("[gold] an_tcar_adapt")
    lh.write_delta("gold", "an_pv_mood", an_pv_mood(pm)); print("[gold] an_pv_mood")
    lh.write_delta("gold", "an_pv_threshold", an_pv_threshold(pm)); print("[gold] an_pv_threshold")
    lh.write_delta("gold", "an_pv_bands", an_pv_bands(pm)); print("[gold] an_pv_bands")
    lh.write_delta("gold", "an_allometry", an_allometry(pm)); print("[gold] an_allometry")
    pvm = an_pvmodel(pm)
    lh.write_delta("gold", "an_pvmodel", pd.DataFrame([dict(payload=json.dumps(pvm))])); print("[gold] an_pvmodel")


if __name__ == "__main__":
    run()
