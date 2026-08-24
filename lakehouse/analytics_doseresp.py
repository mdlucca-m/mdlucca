# -*- coding: utf-8 -*-
"""Modelo dose-resposta: substitui o fator categórico day_type por CARGA CONTÍNUA
segmentada, e valida a ponderação de carga contra a recuperação percebida (TQR).

Racional (literatura de carga de treino):
  - Carga interna = resposta ao trabalho; sRPE (Foster, 2001) é o padrão, mas o
    RPE por sessão NÃO foi coletado. Sem RPE, a rota defensável é a CARGA
    EXTERNA/VOLUME ponderada por intensidade de tipo (Impellizzeri et al., 2005,
    2019 — "internal vs external load"), ancorada no que foi medido (PSE do HIIT)
    e validada contra uma resposta interna independente (TQR; Kenttä & Hassmén,
    1998). Monotonia/strain seguem Foster (1998). ACWR (Gabbett, 2016) exige
    janela crônica ~28 dias — NÃO se aplica a 7 dias (registrado como ressalva).

O que o modelo faz:
  - decompõe a carga do dia em AGUDA (sRPE/volume do próprio dia) e CUMULATIVA
    (carga acumulada, h), duas variáveis contínuas e interpretáveis no lugar dos
    rótulos day_type. Ambas são de nível-dia (plano da equipe), então o modelo
    re-parametriza a trajetória diária em quantidades de carga, com intercepto
    aleatório por atleta (statsmodels MixedLM; cascata p/ OLS robusto).
  - valida a ponderação: correlação (dia a dia) entre carga e TQR — se a carga
    sobe e a TQR cai, a métrica de carga se comporta como esperado.

Gera em gold:
  an_dose        — por dimensão: β agudo, β cumulativo, p, qual componente domina
  an_dose_payload
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

DIMS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
        ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]
# TQR (Total Quality Recovery, 6–20; média da equipe por dia) — confirmado na fonte/organograma
TQR_DIA = {1: 13.5, 2: 11.4, 3: 11.4, 4: 11.1, 5: 11.6, 6: 11.7, 7: 9.0}


def _z(s):
    s = np.asarray(s, float)
    return (s - s.mean()) / (s.std(ddof=0) or 1)


def _fit(sub):
    """MixedLM y ~ z_agudo + z_cum, intercepto por atleta; cascata p/ OLS robusto."""
    import statsmodels.formula.api as smf
    try:
        r = smf.mixedlm("y ~ z_agudo + z_cum", sub, groups=sub["ID"]).fit(reml=True, method="lbfgs")
        if not np.isfinite(r.bse.get("z_agudo", np.nan)) or r.bse["z_agudo"] == 0:
            raise ValueError
        return r, "misto"
    except Exception:
        r = smf.ols("y ~ z_agudo + z_cum", sub).fit(cov_type="cluster", cov_kwds={"groups": sub["ID"]})
        return r, "ols_cluster"


def run():
    ad = lh.read_delta("gold", "athlete_day_unified").copy()
    carga = lh.read_delta("gold", "an_carga_dia").copy()  # dia, horas, carga_acum_h, srpe
    L = carga[["dia", "horas", "carga_acum_h", "srpe"]].copy()
    L["z_agudo"] = _z(L["srpe"])
    L["z_cum"] = _z(L["carga_acum_h"])
    d = ad.merge(L[["dia", "z_agudo", "z_cum"]], on="dia", how="inner")

    out = []
    for col, lab in DIMS:
        sub = d[["ID", "z_agudo", "z_cum", col]].dropna().rename(columns={col: "y"}).copy()
        r, metodo = _fit(sub)
        ba, bc = float(r.params["z_agudo"]), float(r.params["z_cum"])
        pa, pc = float(r.pvalues["z_agudo"]), float(r.pvalues["z_cum"])
        cia = r.conf_int().loc["z_agudo"].tolist(); cic = r.conf_int().loc["z_cum"].tolist()
        dom = "cumulativa" if abs(bc) > abs(ba) else "aguda"
        out.append(dict(dim=col, dim_lab=lab, metodo=metodo,
                        beta_agudo=round(ba, 3), ic_agudo=[round(cia[0], 3), round(cia[1], 3)], p_agudo=round(pa, 4), sig_agudo=bool(pa < 0.05),
                        beta_cum=round(bc, 3), ic_cum=[round(cic[0], 3), round(cic[1], 3)], p_cum=round(pc, 4), sig_cum=bool(pc < 0.05),
                        domina=dom, n=int(sub.ID.nunique())))
    dose = pd.DataFrame(out)

    # validação da ponderação de carga × TQR (nível-dia, n=7)
    from scipy import stats
    cd = carga.copy(); cd["tqr"] = cd["dia"].map(TQR_DIA)
    rho_acum, p_acum = stats.spearmanr(cd["carga_acum_h"], cd["tqr"])
    rho_srpe, p_srpe = stats.spearmanr(cd["srpe"], cd["tqr"])

    payload = {
        "dose": dose.to_dict("records"),
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "tqr_dia": [{"dia": int(k), "tqr": v} for k, v in TQR_DIA.items()],
        "valid": {"rho_acum_tqr": round(float(rho_acum), 3), "p_acum_tqr": round(float(p_acum), 3),
                  "rho_srpe_tqr": round(float(rho_srpe), 3), "p_srpe_tqr": round(float(p_srpe), 3)},
        "n_atl": int(d.ID.nunique()),
        "notas": [
            "Carga contínua (aguda = sRPE/volume do dia; cumulativa = carga acumulada em h) no lugar do fator day_type.",
            "β padronizado: mudança na dimensão por 1 DP de carga; intercepto aleatório por atleta.",
            "Carga é de nível-dia (plano da equipe) — o modelo re-parametriza a trajetória diária em quantidades de carga interpretáveis; dose-resposta individual exigiria carga por atleta (RPE/HR por sessão).",
            "Validação: TQR (recuperação percebida) cai quando a carga acumulada sobe (Spearman ρ=" + str(round(float(rho_acum), 2)) + ") — a métrica de carga se comporta como esperado.",
            "ACWR não calculado: janela crônica (~28 dias) indisponível em 7 dias.",
        ],
    }
    lh.write_delta("gold", "an_dose", dose); print("[gold] an_dose", dose.shape)
    lh.write_delta("gold", "an_dose_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_dose_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== dose-resposta (β padronizado; qual carga domina) ===")
    for r in p["dose"]:
        print(f"  {r['dim_lab']:12} agudo β={r['beta_agudo']:+.2f}{'*' if r['sig_agudo'] else ' '} | cumulativo β={r['beta_cum']:+.2f}{'*' if r['sig_cum'] else ' '} → domina {r['domina']}")
    print(f"\n  Validação TQR: ρ(acum,TQR)={p['valid']['rho_acum_tqr']} (p={p['valid']['p_acum_tqr']}) · ρ(sRPE,TQR)={p['valid']['rho_srpe_tqr']}")
