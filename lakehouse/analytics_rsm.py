# -*- coding: utf-8 -*-
"""Delineamento de superfície de respostas (RSM) — versão observacional/defensável.

O que é: a RSM ajusta um modelo polinomial de 2ª ordem da resposta em função de
fatores contínuos, para MAPEAR a superfície e localizar um ponto estacionário
(máximo, mínimo ou sela) via análise canônica (autovalores da matriz de curvatura).

Aplicabilidade aos nossos dados (ressalvas honestas, registradas no payload):
  - RSM clássica é um DELINEAMENTO EXPERIMENTAL (central composite, Box-Behnken):
    os níveis dos fatores são fixados pelo pesquisador. Aqui os fatores são
    OBSERVADOS (carga aguda e cumulativa do plano da equipe), não manipulados.
  - Os dois fatores variam apenas no NÍVEL-DIA -> apenas 7 pontos de delineamento.
    Um polinômio de 2ª ordem tem 6 coeficientes; com 7 pontos, a curvatura é
    estimada com df mínimo (exploratória, não confirmatória).
  - Os fatores são correlacionados entre os dias (delineamento não ortogonal),
    então os coeficientes quadráticos/interação devem ser lidos com cautela.
  Portanto: mapeamento DESCRITIVO da resposta ao espaço de carga — não otimização
  causal. É a extensão de 2ª ordem do modelo dose-resposta (que era linear).

Fatores (padronizados, z):  x1 = carga aguda do dia (sRPE) ; x2 = carga cumulativa (h).
Respostas: eixo energético-afetivo (vigor, fadiga, PTH) + sonolência (Epworth).
Modelo:  y ~ x1 + x2 + x1^2 + x2^2 + x1:x2  (intercepto aleatório por atleta; cascata p/ OLS robusto).

Gera em gold:
  an_rsm          — por resposta: coeficientes, R2, ponto estacionário, autovalores, natureza
  an_rsm_payload  — inclui a grade da superfície ajustada para o painel
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

RESP = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("pth", "PTH"), ("epworth", "Sonolência (Epworth)")]


def _z(s):
    s = np.asarray(s, float)
    m, sd = s.mean(), (s.std(ddof=0) or 1.0)
    return (s - m) / sd, m, sd


def _fit(sub):
    """MixedLM de 2ª ordem, intercepto por atleta; cascata p/ OLS cluster-robusto."""
    import statsmodels.formula.api as smf
    f = "y ~ x1 + x2 + I(x1**2) + I(x2**2) + x1:x2"
    try:
        r = smf.mixedlm(f, sub, groups=sub["ID"]).fit(reml=False, method="lbfgs")
        if not np.all(np.isfinite(list(r.bse.values))):
            raise ValueError
        return r, "misto"
    except Exception:
        r = smf.ols(f, sub).fit(cov_type="cluster", cov_kwds={"groups": sub["ID"]})
        return r, "ols_cluster"


def _term(r, name):
    # statsmodels nomeia os quadráticos como "I(x1 ** 2)"; tolera variações de espaço
    for k in r.params.index:
        kk = k.replace(" ", "")
        if kk == name.replace(" ", ""):
            return float(r.params[k]), float(r.pvalues[k])
    return 0.0, np.nan


def run():
    ad = lh.read_delta("gold", "athlete_day_unified").copy()
    carga = lh.read_delta("gold", "an_carga_dia").copy()
    L = carga[["dia", "srpe", "carga_acum_h"]].copy()
    x1z, x1m, x1s = _z(L["srpe"]); x2z, x2m, x2s = _z(L["carga_acum_h"])
    L["x1"], L["x2"] = x1z, x2z
    dias = L.sort_values("dia")
    # colinearidade do delineamento (Pearson entre os fatores, nível-dia)
    rho_fac = float(np.corrcoef(L["x1"], L["x2"])[0, 1])
    d = ad.merge(L[["dia", "x1", "x2"]], on="dia", how="inner")

    out, grids = [], {}
    # grade padronizada p/ predição da superfície
    gx = np.linspace(-1.6, 1.6, 17)
    GX1, GX2 = np.meshgrid(gx, gx)
    for col, lab in RESP:
        sub = d[["ID", "x1", "x2", col]].dropna().rename(columns={col: "y"}).copy()
        if sub["y"].nunique() < 3:
            continue
        r, metodo = _fit(sub)
        b0 = float(r.params.get("Intercept", 0.0))
        b1, p1 = _term(r, "x1"); b2, p2 = _term(r, "x2")
        b11, p11 = _term(r, "I(x1**2)"); b22, p22 = _term(r, "I(x2**2)")
        b12, p12 = _term(r, "x1:x2")
        # matriz de curvatura B e gradiente b -> ponto estacionário xs = -0.5 B^-1 b
        B = np.array([[b11, b12 / 2.0], [b12 / 2.0, b22]])
        bb = np.array([b1, b2])
        try:
            xs = -0.5 * np.linalg.solve(B, bb)
            eig = np.linalg.eigvalsh(B)
            if np.all(eig < 0):
                nat = "máximo"
            elif np.all(eig > 0):
                nat = "mínimo"
            else:
                nat = "ponto de sela"
            in_region = bool(np.all(np.abs(xs) <= 1.6))
        except Exception:
            xs = np.array([np.nan, np.nan]); eig = np.array([np.nan, np.nan]); nat = "indefinido"; in_region = False
        # R2 (marginal: fitted efeitos fixos vs observado)
        try:
            yhat = r.predict(sub)
            R2 = float(np.corrcoef(yhat, sub["y"])[0, 1] ** 2)
        except Exception:
            R2 = np.nan
        # curvatura: menor p entre os termos de 2ª ordem
        p_curv = float(np.nanmin([p11, p22, p12]))
        # superfície predita na grade (usa os efeitos fixos)
        Z = b0 + b1 * GX1 + b2 * GX2 + b11 * GX1**2 + b22 * GX2**2 + b12 * GX1 * GX2
        # amostra da grade p/ painel (17x17)
        grid = [{"x1": round(float(GX1[i, j]), 3), "x2": round(float(GX2[i, j]), 3), "y": round(float(Z[i, j]), 3)}
                for i in range(GX1.shape[0]) for j in range(GX1.shape[1])]
        # converte ponto estacionário p/ unidades brutas
        xs_raw = [round(float(x1m + xs[0] * x1s), 0) if np.isfinite(xs[0]) else None,
                  round(float(x2m + xs[1] * x2s), 1) if np.isfinite(xs[1]) else None]
        out.append(dict(resp=col, resp_lab=lab, metodo=metodo, n=int(sub.ID.nunique()),
                        b0=round(b0, 3), b1=round(b1, 3), b2=round(b2, 3),
                        b11=round(b11, 3), b22=round(b22, 3), b12=round(b12, 3),
                        p1=round(p1, 4), p2=round(p2, 4), p11=round(p11, 4), p22=round(p22, 4), p12=round(p12, 4),
                        r2=round(R2, 3) if np.isfinite(R2) else None, p_curv=round(p_curv, 4) if np.isfinite(p_curv) else None,
                        sig_curv=bool(np.isfinite(p_curv) and p_curv < 0.05),
                        est_x1=round(float(xs[0]), 2) if np.isfinite(xs[0]) else None,
                        est_x2=round(float(xs[1]), 2) if np.isfinite(xs[1]) else None,
                        est_srpe=xs_raw[0], est_acum_h=xs_raw[1],
                        eig1=round(float(eig[0]), 3) if np.isfinite(eig[0]) else None,
                        eig2=round(float(eig[1]), 3) if np.isfinite(eig[1]) else None,
                        natureza=nat, dentro_regiao=in_region))
        grids[col] = grid
    rsm = pd.DataFrame(out)

    # rótulos dos fatores em unidades brutas p/ os eixos do painel
    fac = {
        "x1": {"nome": "Carga aguda (sRPE do dia)", "media": round(float(x1m), 0), "dp": round(float(x1s), 0),
               "min": round(float(L["srpe"].min()), 0), "max": round(float(L["srpe"].max()), 0), "unidade": "UA"},
        "x2": {"nome": "Carga cumulativa (h)", "media": round(float(x2m), 1), "dp": round(float(x2s), 1),
               "min": round(float(carga["carga_acum_h"].min()), 1), "max": round(float(carga["carga_acum_h"].max()), 1), "unidade": "h"},
    }
    dias_rec = dias.assign(srpe=carga.sort_values("dia")["srpe"].values,
                           acum=carga.sort_values("dia")["carga_acum_h"].values)[["dia", "x1", "x2"]]
    payload = {
        "rsm": rsm.to_dict("records"),
        "resp": [{"resp": c, "lab": l} for c, l in RESP],
        "grids": grids,
        "grid_axis": [round(float(v), 3) for v in gx],
        "fatores": fac,
        "rho_fatores": round(rho_fac, 3),
        "dias": [{"dia": int(row.dia), "x1": round(float(row.x1), 3), "x2": round(float(row.x2), 3)} for row in dias.itertuples()],
        "n_pontos_delineamento": 7,
        "notas": [
            "Modelo de 2ª ordem: y ~ x1 + x2 + x1² + x2² + x1·x2, com x1 = carga aguda (sRPE) e x2 = carga cumulativa (h), padronizados; intercepto aleatório por atleta.",
            "Fatores OBSERVADOS (não manipulados) e de nível-dia: apenas 7 pontos de delineamento — a curvatura é exploratória, não confirmatória.",
            "Delineamento não ortogonal: correlação entre os fatores ρ=" + str(round(rho_fac, 2)) + " — coeficientes quadráticos/interação a interpretar com cautela.",
            "Ponto estacionário obtido por xs = −½·B⁻¹·b; natureza pela análise canônica (autovalores de B). 'Dentro da região' indica se o ótimo cai no espaço observado.",
            "Não é otimização causal: mapeia como a resposta varia com a carga, não prescreve a carga ótima.",
        ],
    }
    lh.write_delta("gold", "an_rsm", rsm); print("[gold] an_rsm", rsm.shape)
    lh.write_delta("gold", "an_rsm_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_rsm_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== RSM · superfície de resposta (2ª ordem) ===")
    print(f"  correlação dos fatores (delineamento): ρ={p['rho_fatores']} · {p['n_pontos_delineamento']} pontos de nível-dia")
    for r in p["rsm"]:
        print(f"  {r['resp_lab']:20} R²={r['r2']} | curvatura p={r['p_curv']}{'*' if r['sig_curv'] else ''} | "
              f"estacionário={r['natureza']} (sRPE≈{r['est_srpe']}, acum≈{r['est_acum_h']}h, {'dentro' if r['dentro_regiao'] else 'fora'} da região)")
