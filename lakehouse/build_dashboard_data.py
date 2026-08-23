# -*- coding: utf-8 -*-
"""Painel ← gold: gera as constantes de dados do painel A PARTIR do lakehouse.

O dashboard_humor.html é autossuficiente (para enviar ao orientador), então não
faz consultas ao vivo. Este gerador lê as tabelas gold (an_*) e regenera, no
próprio HTML, os blocos `const DIM/D17/FRIED/SNR/SPEAR = [...]`. Assim os números
do painel passam a VIR do gold (fonte única da verdade), sem quebrar o arquivo
único. Rode após o pipeline; depois `export_dashboard.py` confirma a paridade.
"""
from __future__ import annotations
import os, re
import lh

DASH = os.path.abspath(os.path.join(lh.ROOT, "..", "Artigos", "dashboard_humor.html"))
ORDER = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
         ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]

def _n(x, d=1):
    s = f"{float(x):.{d}f}"
    return s.rstrip("0").rstrip(".") if "." in s and d > 1 else s

def _pstr(p):
    return '"<0,001"' if float(p) < 0.001 else '"' + f"{float(p):.3f}".replace(".", ",") + '"'

def _magdz(dz):
    a = abs(float(dz))
    return "grande" if a >= .8 else "médio" if a >= .5 else "pequeno" if a >= .2 else "trivial"

def _magW(w):
    w = float(w)
    return "grande" if w >= .5 else "médio" if w >= .3 else "pequeno" if w >= .1 else "trivial"

def gen_DIM():
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    rows = [f' {{k:"{k}",lab:"{lab}",c:C.{k},daily:[{",".join(_n(v,1) for v in dg[k])}]}}'
            for k, lab in ORDER]
    return "const DIM=[\n" + ",\n".join(rows) + "\n]"

def gen_D17():
    d = lh.read_delta("gold", "an_d17").set_index("var")
    rows = [f'["{lab}",{_n(d.loc[k,"d1"],2)},{_n(d.loc[k,"d7"],2)},{int(d.loc[k,"pct"])},'
            f'{_n(d.loc[k,"dz"],2)},"{_magdz(d.loc[k,"dz"])}"]' for k, lab in ORDER]
    return "const D17=[" + ",".join(rows) + "]"

def gen_FRIED():
    f = lh.read_delta("gold", "an_friedman").set_index("var")
    rows = [f'["{lab}",{_n(f.loc[k,"chi2"],1)},{_pstr(f.loc[k,"p"])},{_n(f.loc[k,"W"],2)},'
            f'"{_magW(f.loc[k,"W"])}"]' for k, lab in ORDER]
    return "const FRIED=[" + ",".join(rows) + "]"

def gen_SNR(html):
    s = lh.read_delta("gold", "an_snr").set_index("var")
    # preserva o 'piso' já exibido (evita mexer no narrativo de piso)
    cur = dict(re.findall(r'lab:"([^"]+)"[^}]*?piso:([-0-9.]+)',
               html[html.find("const SNR="):html.find("];", html.find("const SNR="))]))
    rows = []
    for k, lab in ORDER:
        piso = cur.get(lab, str(int(s.loc[k, "piso"])) if "piso" in s.columns else "0")
        rows.append(f' {{lab:"{lab}",trend:{_n(s.loc[k,"tendencia"],1)},hiit:{_n(s.loc[k,"hiit"],1)},'
                    f'noise:{_n(s.loc[k,"ruido"],1)},snr:{_n(s.loc[k,"snr"],1)},piso:{piso}}}')
    return "const SNR=[\n" + ",\n".join(rows) + "\n]"

ACC = {"Iceberg": "Iceberg", "Superficie": "Superfície", "Submerso": "Submerso",
       "Everest invertido": "Everest invertido", "Barbatana de tubarao": "Barbatana de tubarão",
       "Iceberg invertido": "Iceberg invertido"}

def gen_PROFATL():
    a = lh.read_delta("gold", "an_profile_athlete")
    parts = []
    for r in a.itertuples():
        t = [_n(r.tensao, 1), _n(r.depressao, 1), _n(r.raiva, 1), _n(r.vigor, 1), _n(r.fadiga, 1), _n(r.confusao, 1)]
        parts.append(f'"{r.ID}":{{"med":"{ACC[r.perfil_medio]}","mod":"{ACC[r.perfil_modal]}",'
                     f'"risco":{str(bool(r.risco)).lower()},"t":[{",".join(t)}]}}')
    return "const PROFATL={" + ",".join(parts) + "}"

def gen_PROFGRP():
    g = lh.read_delta("gold", "an_profile_group").iloc[0]
    return f'const PROFGRP={{prev:"{ACC[g["perfil_mais_prevalente"]]}",pct:{_n(g["prevalencia_pct"],1)}}}'

def gen_SPEAR():
    sp = lh.read_delta("gold", "an_spearman")
    cap = {k: lab for k, lab in ORDER}
    def lab(par):
        a, b = par.split(" × ")
        return f"{cap.get(a,a.title())} × {cap.get(b,b.title())}"
    rows = [f'["{lab(r.par)}",{_n(r.rho,2)},{_pstr(r.p)}]' for r in sp.itertuples()]
    return "const SPEAR=[" + ",".join(rows) + "]"

def replace_const(html, name, new_rhs):
    i = html.find(f"const {name}=")
    assert i >= 0, f"const {name} não encontrada"
    j = html.index("=", i) + 1
    depth, k = 0, j
    while k < len(html):
        c = html[k]
        if c in "[{(": depth += 1
        elif c in "]})": depth -= 1
        elif c == ";" and depth == 0: break
        k += 1
    return html[:i] + new_rhs + html[k:]  # new_rhs sem ';' final; mantém o ';' original

def run():
    html = open(DASH, encoding="utf-8").read()
    gens = {"DIM": gen_DIM(), "D17": gen_D17(), "FRIED": gen_FRIED(),
            "SNR": gen_SNR(html), "SPEAR": gen_SPEAR(),
            "PROFATL": gen_PROFATL(), "PROFGRP": gen_PROFGRP()}
    for name, rhs in gens.items():
        html = replace_const(html, name, rhs)
        print(f"[painel←gold] const {name} regenerada do gold")
    open(DASH, "w", encoding="utf-8").write(html)
    print("painel atualizado a partir do lakehouse:", os.path.relpath(DASH, lh.ROOT))

if __name__ == "__main__":
    run()
