# -*- coding: utf-8 -*-
"""Estímulo do jogo amistoso — comportamento, responsividade e sensibilidade.

Os jogos amistosos ocorreram em D3 e D5 (alto volume, ~120 min). Este módulo
isola o estímulo do JOGO e mede, para cada variável do humor:

  1. NÍVEL (estado): média nos dias de jogo contra os demais dias, pareada por
     atleta (dz de Cohen; Wilcoxon). Mostra o que o jogo faz ao estado de humor.
  2. RESPONSIVIDADE: o tamanho de efeito |dz| do jogo — quais variáveis mais se
     movem com o estímulo (nível e resposta aguda pré→pós no próprio dia).
  3. SENSIBILIDADE (discriminação): a AUC de cada variável para separar um dia de
     jogo de um dia sem jogo (nível atleta-dia). AUC ~ 0,5 = não discrimina;
     afastar-se de 0,5 indica poder de sinalizar o jogo (para cima ou para baixo).

Leitura esperada (jogo protetor do humor): apesar do alto volume, as dimensões
negativas tendem a ser menores no jogo e o vigor preservado — contraste com o
HIIT (aversivo), já visto na triangulação.

Gera em gold: an_game, an_game_payload
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh
from scipy import stats

DIMS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
        ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]
GAME_DAYS = [3, 5]


def _dz_paired(a, b):
    d = np.asarray(a, float) - np.asarray(b, float)
    d = d[~np.isnan(d)]
    if len(d) < 3 or d.std(ddof=1) == 0:
        return float(d.mean()) if len(d) else np.nan, np.nan, len(d)
    dz = d.mean() / d.std(ddof=1)
    try:
        p = stats.wilcoxon(d)[1]
    except Exception:
        p = np.nan
    return float(dz), float(p), int(len(d))


def _auc(is_game, values):
    v = np.asarray(values, float); g = np.asarray(is_game, int)
    m = ~np.isnan(v)
    v, g = v[m], g[m]
    if g.sum() == 0 or g.sum() == len(g):
        return np.nan
    from sklearn.metrics import roc_auc_score
    return float(roc_auc_score(g, v))


def run():
    adu = lh.read_delta("gold", "athlete_day_unified").copy()
    adu["is_game"] = adu["dia"].isin(GAME_DAYS).astype(int)
    # nível pareado por atleta: média nos dias de jogo × média nos demais dias
    state = []
    for col, lab in DIMS:
        g = adu[adu.is_game == 1].groupby("ID")[col].mean()
        o = adu[adu.is_game == 0].groupby("ID")[col].mean()
        j = pd.concat([g.rename("game"), o.rename("other")], axis=1).dropna()
        dz, p, n = _dz_paired(j["game"].values, j["other"].values)
        auc = _auc(adu["is_game"], adu[col])
        state.append(dict(dim=col, dim_lab=lab, media_jogo=round(float(g.mean()), 2),
                          media_outro=round(float(o.mean()), 2), dz=round(dz, 3) if np.isfinite(dz) else None,
                          p=round(p, 4) if np.isfinite(p) else None, sig=bool(np.isfinite(p) and p < 0.05),
                          auc=round(auc, 3) if np.isfinite(auc) else None,
                          direcao="maior no jogo" if (np.isfinite(auc) and auc > 0.5) else "menor no jogo",
                          n=n))

    # resposta aguda pré→pós NO dia de jogo (silver.mood)
    mood = lh.read_delta("silver", "mood").copy()
    mood.columns = [c.lower() for c in mood.columns]
    mood["pth"] = mood[["tensao", "depressao", "raiva", "fadiga", "confusao"]].sum(axis=1) - mood["vigor"]
    gm = mood[(mood["dia"].isin(GAME_DAYS)) & (mood["momento"].isin(["pre", "pos"]))]
    acute = []
    for col, lab in DIMS:
        piv = gm.pivot_table(index=["id", "dia"], columns="momento", values=col, aggfunc="mean")
        if "pre" not in piv.columns or "pos" not in piv.columns:
            continue
        piv = piv.dropna(subset=["pre", "pos"])
        # média por atleta (colapsa D3/D5) para o contraste pareado
        pa = piv.groupby(level=0).mean()
        dz, p, n = _dz_paired(pa["pos"].values, pa["pre"].values)
        acute.append(dict(dim=col, dim_lab=lab, pre=round(float(pa["pre"].mean()), 2),
                          pos=round(float(pa["pos"].mean()), 2), dz=round(dz, 3) if np.isfinite(dz) else None,
                          p=round(p, 4) if np.isfinite(p) else None, sig=bool(np.isfinite(p) and p < 0.05), n=n))

    # ranking de responsividade (|dz| do nível) e de sensibilidade (|auc-0.5|)
    resp = sorted([s for s in state if s["dz"] is not None], key=lambda s: -abs(s["dz"]))
    sens = sorted([s for s in state if s["auc"] is not None], key=lambda s: -abs(s["auc"] - 0.5))

    payload = {
        "state": state, "acute": acute,
        "resp_rank": [{"dim_lab": s["dim_lab"], "dz": s["dz"]} for s in resp],
        "sens_rank": [{"dim_lab": s["dim_lab"], "auc": s["auc"], "direcao": s["direcao"]} for s in sens],
        "game_days": GAME_DAYS, "n_game_obs": int((adu.is_game == 1).sum()),
        "dims": [{"dim": c, "lab": l} for c, l in DIMS],
        "notas": [
            "Jogo amistoso em D3 e D5 (alto volume, ~120 min). Nível pareado por atleta: média nos dias de jogo contra os demais dias (dz de Cohen; Wilcoxon).",
            "Responsividade = tamanho de efeito |dz| do estímulo; sensibilidade = AUC para separar dia de jogo de dia sem jogo (0,5 = não discrimina).",
            "Resposta aguda = contraste pré→pós no próprio dia de jogo (nível momento; PTH derivado das seis dimensões).",
            "Estudo observacional de grupo único: o tipo de dia está confundido com o dia e a carga; leitura descritiva, não causal.",
        ],
    }
    g = pd.DataFrame(state)
    lh.write_delta("gold", "an_game", g); print("[gold] an_game", g.shape)
    lh.write_delta("gold", "an_game_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_game_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== estímulo do jogo · nível (jogo × demais dias) ===")
    for s in p["state"]:
        print(f"  {s['dim_lab']:10} jogo {s['media_jogo']:5} vs outro {s['media_outro']:5} | dz {s['dz']:+.2f}{'*' if s['sig'] else ' '} | AUC {s['auc']} ({s['direcao']})")
    print("\n=== resposta aguda pré→pós no jogo ===")
    for a in p["acute"]:
        print(f"  {a['dim_lab']:10} {a['pre']:5} -> {a['pos']:5} | dz {a['dz']:+.2f}{'*' if a['sig'] else ''}")
