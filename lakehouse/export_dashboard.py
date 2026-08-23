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

def _html():
    return open(DASH, encoding="utf-8").read()

def parse_scalar(const_kind: str) -> dict:
    """Extrai {var: valor} do painel para D17.dz e SNR.snr."""
    html = _html(); out = {}
    if const_kind == "dz":  # const D17=[ ["Vigor",d1,d7,pct,dz,"mag"], ... ]
        blk = html[html.find("const D17="):html.find("];", html.find("const D17="))]
        for m in re.finditer(r'\["(\w+)",[-0-9.]+,[-0-9.]+,[-0-9.]+,([-0-9.]+)', blk):
            out[m.group(1)] = float(m.group(2))
    elif const_kind == "snr":  # const SNR=[ {lab:"Vigor",...,snr:2.0,...}, ... ]
        blk = html[html.find("const SNR="):html.find("];", html.find("const SNR="))]
        for m in re.finditer(r'lab:"([^"]+)"[^}]*?snr:([-0-9.]+)', blk):
            out[m.group(1)] = float(m.group(2))
    return out

def _check(title, pairs, tol):
    ok = True
    print(f"\n  {title}")
    for name, a, b in pairs:
        m = b is not None and abs(a - b) <= tol
        ok = ok and m
        print(f"    {name:12s} lakehouse={a!s:>7}  painel={b!s:>7}  {'OK' if m else 'DIVERGE'}")
    return ok

def reconcile(daily: dict) -> bool:
    dim = parse_dim_from_html()
    ok = True
    print("  trajetória diária (DIM)")
    for v in VARS:
        g, d = daily[v], dim.get(v)
        match = d is not None and all(abs(a - b) <= 0.1 for a, b in zip(g, d))
        ok = ok and match
        print(f"    {LAB[v]:12s} {'OK' if match else 'DIVERGE'}")
    # dz (D1→D7) e SNR contra as análises do lakehouse
    an_d17 = lh.read_delta("gold", "an_d17").set_index("var")["dz"].to_dict()
    an_snr = lh.read_delta("gold", "an_snr").set_index("var")["snr"].to_dict()
    dz_h, snr_h = parse_scalar("dz"), parse_scalar("snr")
    labmap = {v: LAB[v] for v in VARS}
    ok &= _check("efeito D1→D7 (dz)", [(LAB[v], an_d17[v], dz_h.get(labmap[v])) for v in VARS], 0.02)
    ok &= _check("sinal/ruído (SNR)", [(LAB[v], an_snr[v], snr_h.get(labmap[v])) for v in VARS], 0.15)
    ok &= reconcile_aero()
    print("\n" + ("[OK] painel e lakehouse CONSISTENTES (DIM · dz · SNR · T-CAR)" if ok
                  else "[!!] há divergência — regenerar o painel a partir do lakehouse"))
    return ok

def reconcile_aero() -> bool:
    """Aptidão aeróbia (T-CAR) × humor: painel (AERO) × gold (an_tcar_adapt · an_pv_mood)."""
    m = re.search(r'const AERO=(\{.*?\});', _html())
    if not m:
        print("\n  aptidão T-CAR × humor\n    AERO não encontrada no painel  DIVERGE"); return False
    A = json.loads(m.group(1))
    ad = lh.read_delta("gold", "an_tcar_adapt").set_index("var")
    pm = lh.read_delta("gold", "an_pv_mood").set_index("dim")
    assoc = {a["dim"]: a for a in A["assoc"]}
    pairs = [("T-CAR PV dz", float(ad.loc["tcarpv", "dz"]), A["tcarpv"]["dz"]),
             ("Baker soma dz", float(ad.loc["bksoma", "dz"]), A["bksoma"]["dz"]),
             ("ρ fad.física", float(pm.loc["FadFisica", "r"]), round(assoc["FadFisica"]["r"], 4)),
             ("ρ vigor", float(pm.loc["Vigor", "r"]), round(assoc["Vigor"]["r"], 4)),
             ("n pares (PV×humor)", 25, A["n_pm"]), ("n coorte física", 24, A["n_ph"])]
    return _check("aptidão T-CAR × humor", pairs, 0.02)

def run():
    daily = gold_daily()
    p = export_json(daily)
    print(f"[export] gold → {os.path.relpath(p, lh.ROOT)}\n")
    return reconcile(daily)

if __name__ == "__main__":
    import sys
    sys.exit(0 if run() else 1)
