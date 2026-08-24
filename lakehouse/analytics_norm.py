# -*- coding: utf-8 -*-
"""Perfis de humor sob DUAS padronizações, para comparação ILUSTRATIVA:
  Interno  — z contra a média/DP da própria amostra (o que o estudo usa).
  Externo  — z contra uma referência externa (normas adultas do BRUMS).
IMPORTANTE: os valores de referência externa são ILUSTRATIVOS (representativos das
normas adultas do BRUMS), rotulados como tal e substituíveis pelas tabelas oficiais
(Terry, Lane & Fogarty, 2003; Rohlfs et al., 2008). Serve só para comparar o efeito
da escolha de padronização sobre a classificação e a migração dos perfis.
Escreve gold an_norm_* e um payload (NORMSTD) para painel e documento. Determinístico."""
from __future__ import annotations
import json
import numpy as np, pandas as pd
import lh

SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
NAMES = list(CENT); CM = np.array([CENT[k] for k in NAMES])
ACC = {"Iceberg": "Iceberg", "Superficie": "Superfície", "Submerso": "Submerso",
       "Everest invertido": "Everest invertido", "Barbatana de tubarao": "Barbatana de tubarão",
       "Iceberg invertido": "Iceberg invertido"}
# referência externa ILUSTRATIVA (0-16), representativa de normas adultas do BRUMS.
NORM_M = {"Tensao": 4.0, "Depressao": 2.0, "Raiva": 2.8, "Vigor": 8.0, "Fadiga": 5.0, "Confusao": 2.6}
NORM_SD = {"Tensao": 3.0, "Depressao": 2.6, "Raiva": 3.0, "Vigor": 3.5, "Fadiga": 3.6, "Confusao": 2.7}


def _classify(Z):
    return Z.apply(lambda r: NAMES[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)


def _run(m, modo):
    if modo == "interno":
        mu = m[SUB].mean(); sd = m[SUB].std()
        Z = (m[SUB] - mu) / sd
    else:
        mu = pd.Series(NORM_M); sd = pd.Series(NORM_SD)
        Z = (m[SUB] - mu) / sd
    perfil = _classify(Z)
    dd = m[["ID", "dia"]].copy(); dd["perfil"] = perfil.values
    # prevalência na semana (nível resposta)
    vc = dd["perfil"].value_counts(normalize=True).mul(100)
    week = [dict(perfil=ACC[nm], prev=round(float(vc.get(nm, 0.0)), 1)) for nm in NAMES]
    # prevalência por dia + dominante
    byday = {}
    for d in range(1, 8):
        sub = dd[dd.dia == d]; v = sub["perfil"].value_counts(normalize=True).mul(100)
        prev = {ACC[nm]: round(float(v.get(nm, 0.0)), 1) for nm in NAMES}
        dom = max(prev, key=prev.get)
        byday[str(d)] = dict(dom=dom, pct=prev[dom], prev=prev)
    return dict(week=week, byday=byday,
                iceberg_d1=byday["1"]["prev"]["Iceberg"], iceberg_d7=byday["7"]["prev"]["Iceberg"])


def build(m):
    interno = _run(m, "interno"); externo = _run(m, "externo")
    norm = [dict(dim=ACC.get(s, s), lab={"Tensao": "Tensão", "Depressao": "Depressão", "Raiva": "Raiva",
                                         "Vigor": "Vigor", "Fadiga": "Fadiga", "Confusao": "Confusão"}[s],
                 M=NORM_M[s], SD=NORM_SD[s],
                 amostra_M=round(float(m[s].mean()), 2), amostra_SD=round(float(m[s].std()), 2)) for s in SUB]
    payload = dict(interno=interno, externo=externo, norm=norm, ilustrativo=True)
    return payload


def run():
    m = lh.read_delta("silver", "mood")
    payload = build(m)
    # tabelas gold (long) para auditoria
    rows = []
    for modo, d in [("interno", payload["interno"]), ("externo", payload["externo"])]:
        for w in d["week"]:
            rows.append(dict(modo=modo, nivel="semana", dia=0, perfil=w["perfil"], prev=w["prev"]))
        for dia, b in d["byday"].items():
            for perfil, pct in b["prev"].items():
                rows.append(dict(modo=modo, nivel="dia", dia=int(dia), perfil=perfil, prev=pct))
    lh.write_delta("gold", "an_norm_prev", pd.DataFrame(rows)); print("[gold] an_norm_prev", len(rows))
    lh.write_delta("gold", "an_norm_ref", pd.DataFrame(payload["norm"])); print("[gold] an_norm_ref")
    lh.write_delta("gold", "an_norm_payload",
                   pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_norm_payload · iceberg interno D1=%.1f→D7=%.1f · externo D1=%.1f→D7=%.1f"
          % (payload["interno"]["iceberg_d1"], payload["interno"]["iceberg_d7"],
             payload["externo"]["iceberg_d1"], payload["externo"]["iceberg_d7"]))
    return payload


if __name__ == "__main__":
    p = run()
    print("INTERNO semana:", [(w["perfil"], w["prev"]) for w in p["interno"]["week"]])
    print("EXTERNO semana:", [(w["perfil"], w["prev"]) for w in p["externo"]["week"]])
