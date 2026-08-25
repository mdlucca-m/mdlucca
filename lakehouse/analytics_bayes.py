# -*- coding: utf-8 -*-
"""Reestimação bayesiana dos efeitos-chave (BEST) — incerteza honesta para n pequeno.

Com 27 atletas e sete dias, os valores de p dos efeitos afetivos pequenos são
frágeis. A estimação bayesiana (Kruschke, "Bayesian estimation supersedes the
t-test") modela as diferenças pareadas do primeiro contra o último dia com uma
verossimilhança t de Student (robusta a valores extremos) e retorna a
DISTRIBUIÇÃO POSTERIOR do efeito, com intervalo de credibilidade e probabilidade
de direção — uma leitura de incerteza mais informativa que o p isolado.

Roda FORA do pipeline determinístico (verify) por ser um reforço de robustez e
por depender do PyMC. Semente fixa (7) para reprodutibilidade.

Gera em gold: an_bayes, an_bayes_payload
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

DIMS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("pth", "PTH"), ("tensao", "Tensão")]
SEED = 7


def _pairs(adu, col):
    d = adu.pivot_table(index="ID", columns="dia", values=col)
    if 1 not in d.columns or 7 not in d.columns:
        return None
    sub = d[[1, 7]].dropna()
    return (sub[7] - sub[1]).values  # diferença D7 - D1 por atleta


def run():
    try:
        import pymc as pm
        import arviz as az
    except Exception as e:
        print("[bayes] PyMC indisponível — módulo ignorado:", e)
        return None
    adu = lh.read_delta("gold", "athlete_day_unified").copy()
    out, posts = [], {}
    for col, lab in DIMS:
        diffs = _pairs(adu, col)
        if diffs is None or len(diffs) < 8:
            continue
        with pm.Model():
            mu = pm.Normal("mu", 0.0, 5.0)
            sigma = pm.HalfNormal("sigma", 5.0)
            nu = pm.Exponential("nu", 1.0 / 29.0) + 1.0
            pm.Deterministic("dz", mu / sigma)
            pm.StudentT("y", nu=nu, mu=mu, sigma=sigma, observed=diffs)
            idata = pm.sample(2000, tune=1000, chains=2, cores=1, random_seed=SEED,
                              progressbar=False, target_accept=0.9)
        post = idata.posterior
        mu_s = post["mu"].values.flatten()
        dz_s = post["dz"].values.flatten()
        hdi = az.hdi(idata, var_names=["mu"], hdi_prob=0.94)["mu"].values
        hdi_dz = az.hdi(idata, var_names=["dz"], hdi_prob=0.94)["dz"].values
        pdir = float(np.mean(mu_s > 0)) if mu_s.mean() > 0 else float(np.mean(mu_s < 0))
        # histograma da posterior de dz para o painel
        hist, edges = np.histogram(dz_s, bins=40, density=True)
        centers = ((edges[:-1] + edges[1:]) / 2).round(3)
        out.append(dict(dim=col, dim_lab=lab, n=int(len(diffs)),
                        mu=round(float(mu_s.mean()), 3), mu_lo=round(float(hdi[0]), 3), mu_hi=round(float(hdi[1]), 3),
                        dz=round(float(dz_s.mean()), 3), dz_lo=round(float(hdi_dz[0]), 3), dz_hi=round(float(hdi_dz[1]), 3),
                        p_dir=round(pdir, 3), excl_zero=bool(hdi[0] > 0 or hdi[1] < 0)))
        posts[col] = {"x": centers.tolist(), "y": [round(float(v), 4) for v in hist]}
    bayes = pd.DataFrame(out)
    payload = {
        "bayes": out, "posts": posts,
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "notas": [
            "Estimação bayesiana (BEST, Kruschke): diferenças pareadas D7 - D1 por atleta, verossimilhança t de Student robusta.",
            "Prior fraca (mu ~ Normal(0,5)); posterior com intervalo de credibilidade de 94% e probabilidade de direção.",
            "dz = mu/sigma (efeito padronizado bayesiano); IC exclui zero indica direção crível.",
            "Amostra pequena (pares D1-D7 completos por atleta); leitura de incerteza, complementar ao p.",
        ],
    }
    lh.write_delta("gold", "an_bayes", bayes); print("[gold] an_bayes", bayes.shape)
    lh.write_delta("gold", "an_bayes_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_bayes_payload")
    return payload


if __name__ == "__main__":
    p = run()
    if p:
        print("\n=== reestimação bayesiana (BEST) ===")
        for r in p["bayes"]:
            print(f"  {r['dim_lab']:8} n={r['n']} | efeito μ={r['mu']:+.2f} [IC94 {r['mu_lo']:+.2f}, {r['mu_hi']:+.2f}] | "
                  f"dz={r['dz']:+.2f} | P(direção)={r['p_dir']:.3f} | IC exclui zero: {r['excl_zero']}")
