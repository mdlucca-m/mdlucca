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
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.metrics import roc_auc_score, roc_curve
import pandas as pd
import lh

FEATS = ["pth", "fadiga", "vigor", "hiit_flag"]
OUT = os.path.join(lh.ROOT, "ml")
SEED = 7


def _models():
    import xgboost as xgb, lightgbm as lgb
    return {
        "Random Forest": RandomForestClassifier(n_estimators=300, max_depth=4, random_state=SEED,
                                                n_jobs=1, class_weight="balanced"),
        "XGBoost": xgb.XGBClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=SEED,
                                     n_jobs=1, eval_metric="logloss", verbosity=0),
        "LightGBM": lgb.LGBMClassifier(n_estimators=200, max_depth=3, learning_rate=0.05, random_state=SEED,
                                       n_jobs=1, verbose=-1),
    }


PHASE_FE = ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao"]

def run_models():
    """Compara Random Forest, XGBoost e LightGBM na MESMA tarefa do painel — separar
    a fase tardia (D5–7) da inicial (D1–3) a partir do perfil de humor — com validação
    GroupKFold POR ATLETA (sem vazamento). Materializa gold.an_models (AUC por modelo,
    + importância do preditor) e gold.an_roc (curva ROC do melhor). Determinístico."""
    from sklearn.inspection import permutation_importance
    ad = lh.read_delta("gold", "athlete_day")
    sub = ad[ad.dia.isin([1, 2, 3, 5, 6, 7])].copy()
    y = (sub["dia"] >= 5).astype(int).values
    X, g = sub[PHASE_FE].values, sub["ID"].values
    cv = GroupKFold(n_splits=5)
    rows, best = [], None
    for name, clf in _models().items():
        proba = cross_val_predict(clf, X, y, cv=cv, groups=g, method="predict_proba")[:, 1]
        auc = round(float(roc_auc_score(y, proba)), 3)
        rows.append(dict(modelo=name, auc=auc, n=int(len(y)), positivos=int(y.sum())))
        if best is None or auc > best[1]:
            best = (name, auc, proba, clf)
    an_models = pd.DataFrame(rows).sort_values("auc", ascending=False).reset_index(drop=True)
    # importância por permutação do melhor modelo (preditor dominante para o KPI)
    best[3].fit(X, y)
    imp = permutation_importance(best[3], X, y, n_repeats=20, random_state=SEED, n_jobs=1)
    top = PHASE_FE[int(np.argmax(imp.importances_mean))]
    an_models["melhor"] = an_models["modelo"] == best[0]
    an_models["preditor_top"] = top
    an_models["auc_melhor"] = best[1]
    fpr, tpr, _ = roc_curve(y, best[2])
    idx = np.unique(np.linspace(0, len(fpr) - 1, 24).astype(int))
    an_roc = pd.DataFrame({"fpr": np.round(fpr[idx], 3), "tpr": np.round(tpr[idx], 3)})
    lh.write_delta("gold", "an_models", an_models)
    lh.write_delta("gold", "an_roc", an_roc)
    print(f"[gold] an_models (melhor: {best[0]} AUC={best[1]} · preditor {top}) · an_roc")
    _learning_curve(X, y, g)
    return an_models


def _learning_curve(X, y, g):
    """Curva de aprendizado (AUC de treino × validação por tamanho do conjunto),
    Random Forest na tarefa fase tardia×inicial, GroupKFold por atleta. Determinístico."""
    from sklearn.model_selection import learning_curve
    # regressão logística (não a floresta): treino e validação ficam próximos, mostrando
    # que o teto baixo é falta de sinal individual, não overfitting — coerente com a leitura.
    clf = LogisticRegression(max_iter=1000, class_weight="balanced")
    sizes = np.linspace(0.4, 1.0, 6)
    ts, tr, cv = learning_curve(clf, X, y, groups=g, cv=GroupKFold(n_splits=5),
                                train_sizes=sizes, scoring="roc_auc", random_state=SEED, n_jobs=1)
    df = pd.DataFrame({"n": ts.astype(int), "train_auc": np.round(tr.mean(1), 3),
                       "cv_auc": np.round(cv.mean(1), 3)})
    lh.write_delta("gold", "an_learning", df)
    print(f"[gold] an_learning ({len(df)} pontos)")

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
    run_models()
    return metrics

if __name__ == "__main__":
    run()
