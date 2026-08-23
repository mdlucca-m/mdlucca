# -*- coding: utf-8 -*-
"""ML — treina o classificador de risco a partir da camada GOLD.

Lê gold.risk_features (uma via, reprodutível) e treina uma regressão logística
para prever o risco do dia seguinte a partir dos marcadores de hoje, validando
com GroupKFold POR ATLETA (não vaza atleta entre treino e teste). Salva o modelo
e as métricas em ml/. Espelha o sistema de alerta precoce do painel (IoT).
"""
from __future__ import annotations
import os, json
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score
import lh

FEATS = ["pth", "fadiga", "vigor", "hiit_flag"]
OUT = os.path.join(lh.ROOT, "ml")

def run():
    df = lh.read_delta("gold", "risk_features").dropna(subset=["risco_amanha"]).copy()
    X, y, g = df[FEATS].values, df["risco_amanha"].astype(int).values, df["ID"].values
    os.makedirs(OUT, exist_ok=True)
    if len(np.unique(y)) < 2:
        print("[ml] rótulos insuficientes para treinar"); return
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    n_groups = len(np.unique(g))
    cv = GroupKFold(n_splits=min(5, n_groups))
    proba = cross_val_predict(clf, X, y, cv=cv, groups=g, method="predict_proba")[:, 1]
    auc = roc_auc_score(y, proba)
    clf.fit(X, y)  # modelo final em todos os dados
    import pickle
    with open(os.path.join(OUT, "risk_model.pkl"), "wb") as f:
        pickle.dump({"model": clf, "features": FEATS}, f)
    metrics = {"auc_groupkfold": round(float(auc), 3), "n": int(len(y)),
               "positivos": int(y.sum()), "features": FEATS,
               "coef": dict(zip(FEATS, np.round(clf.coef_[0], 3).tolist()))}
    with open(os.path.join(OUT, "metrics.json"), "w") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)
    print(f"[ml] AUC (GroupKFold por atleta) = {auc:.3f} · n={len(y)} · modelo salvo em ml/risk_model.pkl")
    return metrics

if __name__ == "__main__":
    run()
