# -*- coding: utf-8 -*-
"""Rede psicométrica (GGM) + painel cruzado defasado (CLPM) — estrutura e dinâmica.

Duas leituras modernas que complementam a PCA e o AR(1):

1) REDE GAUSSIANA (GGM): estima a rede de CORRELAÇÕES PARCIAIS entre as
   dimensões do humor, a sonolência e o estresse. Cada aresta é a associação
   entre duas variáveis CONTROLANDO todas as demais (precisão = inversa da
   covariância; regularização por Graphical Lasso com validação cruzada). É a
   visão de "componentes conectados" — quais medidas se ligam diretamente.

2) PAINEL CRUZADO DEFASADO (CLPM): testa PRECEDÊNCIA TEMPORAL entre dimensões.
   Para cada par (X, Y): Y no dia seguinte ~ Y do dia (autorregressão) + X do
   dia (defasagem cruzada), com intercepto aleatório por atleta. O coeficiente
   cruzado indica se X ajuda a prever a mudança de Y além da inércia de Y.

Ressalvas (no payload): n pequeno (27 atletas, 133 pares dia→dia+1); a carga é
de nível-dia (sem variação por atleta), então o CLPM foca as relações
humor→humor; associações descritivas, não causais.

Gera em gold:
  an_net_nodes, an_net_edges  — rede GGM
  an_clpm                     — coeficientes cruzados defasados
  an_net_payload
"""
from __future__ import annotations
import json, warnings
import numpy as np, pandas as pd
warnings.filterwarnings("ignore")
import lh

MOOD = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
        ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão")]
NET_VARS = MOOD + [("epworth", "Sonolência"), ("pss", "Estresse")]
LAG_VARS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("pth", "PTH"), ("epworth", "Sonolência")]


def _z(df, cols):
    z = df[cols].astype(float).copy()
    return (z - z.mean()) / z.std(ddof=0).replace(0, 1)


def _ggm(adu):
    cols = [c for c, _ in NET_VARS]
    X = adu[cols].dropna()
    Xz = (X - X.mean()) / X.std(ddof=0).replace(0, 1)
    prec = None
    try:
        from sklearn.covariance import GraphicalLassoCV
        m = GraphicalLassoCV(cv=5, max_iter=200).fit(Xz.values)
        prec = m.precision_
    except Exception:
        prec = np.linalg.pinv(np.corrcoef(Xz.values, rowvar=False))
    p = prec.shape[0]
    pcorr = np.zeros((p, p))
    for i in range(p):
        for j in range(p):
            if i != j and prec[i, i] > 0 and prec[j, j] > 0:
                pcorr[i, j] = -prec[i, j] / np.sqrt(prec[i, i] * prec[j, j])
    labs = [l for _, l in NET_VARS]
    nodes = [{"id": cols[i], "lab": labs[i],
              "strength": round(float(np.sum(np.abs(pcorr[i]))), 3)} for i in range(p)]
    edges = []
    for i in range(p):
        for j in range(i + 1, p):
            w = pcorr[i, j]
            if abs(w) >= 0.05:
                edges.append({"a": cols[i], "b": cols[j], "a_lab": labs[i], "b_lab": labs[j],
                              "w": round(float(w), 3), "sign": "pos" if w > 0 else "neg"})
    edges.sort(key=lambda e: -abs(e["w"]))
    return nodes, edges, int(len(X))


def _clpm(adu):
    import statsmodels.formula.api as smf
    df = adu.copy().sort_values(["ID", "dia"])
    cols = [c for c, _ in LAG_VARS]
    zc = _z(df, cols)
    for c in cols:
        df["z_" + c] = zc[c]
    # constrói pares (dia d -> d+1) por atleta
    rows = []
    for a, g in df.groupby("ID"):
        gi = g.set_index("dia")
        for d in gi.index:
            if d + 1 in gi.index:
                cur = {("cur_" + c): gi.loc[d, "z_" + c] for c in cols}
                nxt = {("nxt_" + c): gi.loc[d + 1, "z_" + c] for c in cols}
                cur.update(nxt); cur["ID"] = a; rows.append(cur)
    P = pd.DataFrame(rows).dropna()
    out = []
    for xc, xl in LAG_VARS:
        for yc, yl in LAG_VARS:
            if xc == yc:
                continue
            sub = P[["ID", "cur_" + yc, "cur_" + xc, "nxt_" + yc]].rename(
                columns={"cur_" + yc: "y_cur", "cur_" + xc: "x_cur", "nxt_" + yc: "y_nxt"}).dropna()
            if len(sub) < 20:
                continue
            try:
                r = smf.mixedlm("y_nxt ~ y_cur + x_cur", sub, groups=sub["ID"]).fit(reml=False, method="lbfgs")
                b, p = float(r.params["x_cur"]), float(r.pvalues["x_cur"])
                ar = float(r.params["y_cur"]); met = "misto"
            except Exception:
                r = smf.ols("y_nxt ~ y_cur + x_cur", sub).fit(cov_type="cluster", cov_kwds={"groups": sub["ID"]})
                b, p = float(r.params["x_cur"]), float(r.pvalues["x_cur"])
                ar = float(r.params["y_cur"]); met = "ols_cluster"
            out.append(dict(x=xc, y=yc, x_lab=xl, y_lab=yl, beta=round(b, 3), p=round(p, 4),
                            sig=bool(p < 0.05), ar=round(ar, 3), n=int(len(sub)), metodo=met))
    return out, int(len(P))


def run():
    adu = lh.read_delta("gold", "athlete_day_unified").copy()
    nodes, edges, n_ggm = _ggm(adu)
    clpm, n_pairs = _clpm(adu)
    lh.write_delta("gold", "an_net_nodes", pd.DataFrame(nodes)); print("[gold] an_net_nodes", len(nodes))
    lh.write_delta("gold", "an_net_edges", pd.DataFrame(edges)); print("[gold] an_net_edges", len(edges))
    lh.write_delta("gold", "an_clpm", pd.DataFrame(clpm)); print("[gold] an_clpm", len(clpm))
    payload = {
        "nodes": nodes, "edges": edges,
        "clpm": clpm, "lag_vars": [{"id": c, "lab": l} for c, l in LAG_VARS],
        "n_ggm": n_ggm, "n_pairs": n_pairs,
        "top_edges": edges[:6],
        "notas": [
            "Rede GGM: arestas = correlação parcial (associação entre duas medidas controlando todas as demais); regularização por Graphical Lasso com validação cruzada.",
            "CLPM: Y(dia+1) ~ Y(dia) + X(dia), intercepto aleatório por atleta; o coeficiente cruzado (X→Y) indica precedência temporal além da inércia de Y.",
            "n pequeno (27 atletas; " + str(n_pairs) + " pares dia→dia+1); a carga é de nível-dia, então o CLPM foca relações humor→humor.",
            "Associações descritivas (grupo único, T curto), não causais.",
        ],
    }
    lh.write_delta("gold", "an_net_payload", pd.DataFrame([{"payload": json.dumps(payload, ensure_ascii=False)}]))
    print("[gold] an_net_payload")
    return payload


if __name__ == "__main__":
    p = run()
    print("\n=== Rede GGM (arestas mais fortes) ===")
    for e in p["top_edges"]:
        print(f"  {e['a_lab']:10} — {e['b_lab']:10} parcial {e['w']:+.2f} ({e['sign']})")
    print("\n=== CLPM (defasagens cruzadas significativas) ===")
    for c in p["clpm"]:
        if c["sig"]:
            print(f"  {c['x_lab']:10} (dia) -> {c['y_lab']:10} (dia+1)  β={c['beta']:+.2f} p={c['p']}")
