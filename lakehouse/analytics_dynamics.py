# -*- coding: utf-8 -*-
"""Dois modelos para a dinâmica do humor, honestos ao desenho (grupo único, T=7):

1) Autorregressivo de painel lag-1 multinível (MixedLM, Gaussian)
   y_{i,dia} ~ y_{i,dia-1} + tipo de dia, com intercepto aleatório por atleta.
   O coeficiente do lag (β1) mede a PERSISTÊNCIA/arrasto do estado de um dia
   para o seguinte. Ressalva registrada: em painéis dinâmicos com T pequeno há
   viés de Nickell (β1 tende a ser subestimado com efeitos por unidade); aqui é
   leitura EXPLORATÓRIA da persistência, não estimativa causal.

2) Modelo linear generalizado (GLM) — Poisson via GEE (equações de estimação
   generalizadas) com correlação de trabalho permutável e erros-padrão robustos
   (sanduíche), agrupado por atleta. As subescalas do BRUMS são CONTAGENS 0–16
   com piso (muitos zeros); o link log e os EP robustos respeitam melhor essa
   natureza do que a ANOVA gaussiana. Reporta IRR (razão de taxas) por tipo de
   dia (ref. Jogo) e por momento (ref. pré). Ressalva: há sobredispersão/zeros
   em excesso nas negativas — os EP robustos permanecem válidos; um NegBin/zero
   -inflado seria o próximo passo confirmatório.

Gera em gold:
  an_ar1         — persistência lag-1 por dimensão (β1, IC, p, ICC)
  an_glm         — IRR do GLM Poisson-GEE por subescala × preditor
  an_dyn_payload — JSON para o painel
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

DIMS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
        ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"),
        ("pth", "PTH")]
SUBS = [("Vigor", "Vigor"), ("Fadiga", "Fadiga"), ("Tensao", "Tensão"),
        ("Depressao", "Depressão"), ("Raiva", "Raiva"), ("Confusao", "Confusão")]
DAYLAB = {"HIIT": "HIIT", "Jogo": "Jogo", "Forca": "Força", "Baseline": "Baseline"}


def _fit_ar1(sub):
    """cascata: MixedLM (com/sem tipo de dia) → OLS com EP robusto agrupado por atleta."""
    import statsmodels.formula.api as smf
    for formula in ("y ~ lag + C(day_type)", "y ~ lag"):
        try:
            r = smf.mixedlm(formula, sub, groups=sub["ID"]).fit(reml=True, method="lbfgs")
            se = float(r.bse["lag"])
            if not np.isfinite(se) or se == 0:
                raise ValueError("bse inválido")
            gv = float(r.cov_re.iloc[0, 0]); rv = float(r.scale)
            icc = gv / (gv + rv) if (gv + rv) else np.nan
            ci = r.conf_int().loc["lag"].tolist()
            return dict(beta1=float(r.params["lag"]), ci=ci, p=float(r.pvalues["lag"]),
                        icc=float(icc), metodo="misto")
        except Exception:
            continue
    r = smf.ols("y ~ lag + C(day_type)", sub).fit(cov_type="cluster", cov_kwds={"groups": sub["ID"]})
    ci = r.conf_int().loc["lag"].tolist()
    return dict(beta1=float(r.params["lag"]), ci=ci, p=float(r.pvalues["lag"]),
                icc=None, metodo="ols_cluster")


def ar1():
    """AR(1) multinível por dimensão sobre médias diárias por atleta."""
    ad = lh.read_delta("gold", "athlete_day_unified").sort_values(["ID", "dia"]).copy()
    out = []
    for col, lab in DIMS:
        ad["lag"] = ad.groupby("ID")[col].shift(1)
        sub = ad.dropna(subset=["lag", col, "day_type"]).rename(columns={col: "y"}).copy()
        f = _fit_ar1(sub)
        b = f["beta1"]
        out.append(dict(dim=col, dim_lab=lab, beta1=round(b, 3),
                        ic_lo=round(float(f["ci"][0]), 3), ic_hi=round(float(f["ci"][1]), 3),
                        p=round(f["p"], 4),
                        icc=round(float(f["icc"]), 3) if f["icc"] is not None else None,
                        metodo=f["metodo"], n_pairs=int(len(sub)), n_atl=int(sub.ID.nunique()),
                        sig=bool(f["p"] < 0.05),
                        forca=("alta" if b >= 0.5 else "moderada" if b >= 0.3 else "fraca" if b >= 0.1 else "desprezível")))
    return pd.DataFrame(out)


def glm():
    """GLM Poisson-GEE (log link, EP robustos, permutável) por subescala."""
    import statsmodels.api as sm, statsmodels.formula.api as smf
    m = lh.read_delta("silver", "mood")
    d = m[m.day_type.isin(["HIIT", "Jogo", "Forca", "Baseline"]) & m.momento.isin(["pre", "mid", "pos"])].copy()
    d["day_type"] = d["day_type"].astype(str)
    d["momento"] = d["momento"].astype(str)
    out = []
    for col, lab in SUBS:
        try:
            mod = smf.gee(f"{col} ~ C(day_type, Treatment('Jogo')) + C(momento, Treatment('pre'))",
                          "ID", data=d, family=sm.families.Poisson(), cov_struct=sm.cov_struct.Exchangeable())
            r = mod.fit()
            ci = r.conf_int()
            for term in r.params.index:
                if term == "Intercept":
                    continue
                # rótulo amigável do preditor
                lab_p = (term.replace("C(day_type, Treatment('Jogo'))[T.", "dia ")
                              .replace("C(momento, Treatment('pre'))[T.", "momento ")
                              .replace("]", ""))
                lab_p = lab_p.replace("dia HIIT", "HIIT vs Jogo").replace("dia Forca", "Força vs Jogo") \
                             .replace("dia Baseline", "Baseline vs Jogo").replace("momento pos", "pós vs pré") \
                             .replace("momento mid", "meio vs pré")
                b = float(r.params[term]); p = float(r.pvalues[term])
                out.append(dict(dim=col, dim_lab=lab, preditor=lab_p,
                                irr=round(float(np.exp(b)), 3),
                                ic_lo=round(float(np.exp(ci.loc[term, 0])), 3),
                                ic_hi=round(float(np.exp(ci.loc[term, 1])), 3),
                                p=round(p, 4), sig=bool(p < 0.05)))
        except Exception as e:
            print("  glm falhou", col, e); continue
    return pd.DataFrame(out)


def run():
    ar = ar1()
    gl = glm()
    payload = {
        "ar1": ar.to_dict("records"),
        "glm": gl.to_dict("records"),
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "subs": [{"dim": c, "lab": l} for c, l in SUBS],
        "ressalvas": [
            "AR(1): persistência do estado de um dia para o seguinte (β1); intercepto aleatório por atleta.",
            "Viés de Nickell em painel dinâmico com T pequeno (7 dias): β1 tende a ser subestimado — leitura exploratória.",
            "GLM: Poisson via GEE (link log), correlação permutável e EP robustos agrupados por atleta; subescalas são contagens 0–16 com piso.",
            "IRR>1 = a taxa esperada da dimensão aumenta vs a referência (dia Jogo, momento pré); IRR<1 = diminui.",
            "Sobredispersão/excesso de zeros nas negativas: EP robustos válidos; NegBin/zero-inflado seria o passo confirmatório.",
        ],
    }
    lh.write_delta("gold", "an_ar1", ar); print("[gold] an_ar1", ar.shape)
    lh.write_delta("gold", "an_glm", gl); print("[gold] an_glm", gl.shape)
    lh.write_delta("gold", "an_dyn_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_dyn_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== AR(1) persistência (β1) ===")
    for r in p["ar1"]:
        print(f"  {r['dim_lab']:12} β1={r['beta1']:+.2f} IC[{r['ic_lo']:.2f},{r['ic_hi']:.2f}] p={r['p']:.3f} ICC={r['icc']:.2f} ({r['forca']})")
    print("\n=== GLM Poisson-GEE · IRR significativos ===")
    for r in p["glm"]:
        if r["sig"]:
            print(f"  {r['dim_lab']:12} {r['preditor']:18} IRR={r['irr']:.2f} IC[{r['ic_lo']:.2f},{r['ic_hi']:.2f}] p={r['p']:.3f}")
