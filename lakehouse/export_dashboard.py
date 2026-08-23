# -*- coding: utf-8 -*-
"""Ponte lakehouse → painel: mantém os dois consistentes.

(1) Exporta a camada GOLD para um JSON que o painel pode consumir (fonte única
    da verdade dos números da trajetória diária).
(2) RECONCILIA o gold contra a constante DIM embutida no dashboard_humor.html e
    reporta qualquer divergência (guarda de deriva). É o que "mantém os dois":
    rode o pipeline e este verificador; se algo destoar, o painel precisa ser
    atualizado a partir do lakehouse.
"""
from __future__ import annotations
import os, re, json
import lh

DASH = os.path.abspath(os.path.join(lh.ROOT, "..", "Artigos", "dashboard_humor.html"))
OUT = os.path.join(lh.ROOT, "exports")
VARS = ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao", "pth"]
LAB = {"vigor": "Vigor", "fadiga": "Fadiga", "tensao": "Tensão", "depressao": "Depressão",
       "raiva": "Raiva", "confusao": "Confusão", "pth": "PTH"}

def gold_daily() -> dict:
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    return {v: [round(float(x), 1) for x in dg[v].tolist()] for v in VARS}

def export_json(daily: dict) -> str:
    os.makedirs(OUT, exist_ok=True)
    payload = {"source": "lakehouse:gold.daily_group",
               "dims": [{"k": v, "lab": LAB[v], "daily": daily[v]} for v in VARS]}
    path = os.path.join(OUT, "dashboard_daily.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=1)
    return path

def parse_dim_from_html() -> dict:
    html = open(DASH, encoding="utf-8").read()
    i = html.find("const DIM=")
    block = html[i:html.find("];", i)]
    out = {}
    for m in re.finditer(r'\{k:"(\w+)".*?daily:\[([-0-9.,\s]+)\]\}', block):
        out[m.group(1)] = [float(x) for x in m.group(2).split(",")]
    return out

def reconcile(daily: dict) -> bool:
    dim = parse_dim_from_html()
    ok = True
    print(f"{'variável':10s} {'lakehouse (gold)':<34s} {'painel (DIM)':<34s} status")
    for v in VARS:
        g = daily[v]
        d = dim.get(v)
        match = d is not None and all(abs(a - b) <= 0.1 for a, b in zip(g, d))
        ok = ok and match
        print(f"{LAB[v]:10s} {str(g):<34s} {str(d):<34s} {'OK' if match else 'DIVERGE'}")
    print("\n" + ("[OK] painel e lakehouse CONSISTENTES (tolerância 0,1)" if ok
                  else "[!!] há divergência — regenerar o painel a partir do lakehouse"))
    return ok

def run():
    daily = gold_daily()
    p = export_json(daily)
    print(f"[export] gold → {os.path.relpath(p, lh.ROOT)}\n")
    return reconcile(daily)

if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
