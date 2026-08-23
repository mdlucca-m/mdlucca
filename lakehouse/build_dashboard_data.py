# -*- coding: utf-8 -*-
"""Painel ← gold: gera as constantes de dados do painel A PARTIR do lakehouse.

O dashboard_humor.html é autossuficiente (para enviar ao orientador), então não
faz consultas ao vivo. Este gerador lê as tabelas gold (an_*) e regenera, no
próprio HTML, os blocos `const DIM/D17/FRIED/SNR/SPEAR = [...]`. Assim os números
do painel passam a VIR do gold (fonte única da verdade), sem quebrar o arquivo
único. Rode após o pipeline; depois `export_dashboard.py` confirma a paridade.
"""
from __future__ import annotations
import os, re, json
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

def gen_byday():
    t = lh.read_delta("gold", "an_profiles_byday_t").sort_values("dia")
    order = ["tensao", "depressao", "raiva", "vigor", "fadiga", "confusao"]
    rows = [f'{int(r.dia)}:[{",".join(_n(getattr(r,k),1) for k in order)}]' for r in t.itertuples()]
    return "byday:{" + ",".join(rows) + "}"

def gen_byday_dom():
    d = lh.read_delta("gold", "an_profiles_byday").sort_values("dia")
    rows = [f'{int(r.dia)}:["{ACC[r.dominante]}",{_n(r.pct,1)}]' for r in d.itertuples()]
    return "byday_dom:{" + ",".join(rows) + "}"

DIM_ORDER_PV = ["Vigor", "Fadiga", "FadFisica", "FadMental", "TMD",
                "Tensao", "Depressao", "Raiva", "Confusao"]

def _pv_wide():
    pm = lh.read_delta("silver", "pv_mood").sort_values("pair")
    PV = pm[pm.dim == "Vigor"].set_index("pair")["pv"].sort_index()
    mood = {d: pm[pm.dim == d].set_index("pair")["mood"].sort_index().tolist() for d in DIM_ORDER_PV}
    return PV.tolist(), mood

def gen_AERO():
    """AERO ← gold (an_tcar_adapt, an_pv_mood) + silver.pv_mood. Grupo único (sem by_group)."""
    ad = lh.read_delta("gold", "an_tcar_adapt").set_index("var")
    pmv = lh.read_delta("gold", "an_pv_mood")
    PV, mood = _pv_wide()
    assoc = [dict(dim=r.dim, lab=r.lab, r=r.r, lo=r.lo, hi=r.hi, p=r.p, fdr=r.fdr)
             for r in pmv.itertuples()]
    def adapt(key):
        r = ad.loc[key]
        return dict(lab=r["lab"], pre=f'{r["pre"]:.2f} ± {r["pre_sd"]:.2f}',
                    pos=f'{r["pos"]:.2f} ± {r["pos_sd"]:.2f}', dz=float(r["dz"]), p=float(r["p"]),
                    pre_n=float(r["pre"]), pos_n=float(r["pos"]))  # grupo único: médias agrupadas
    aero = dict(pv=PV, mood=mood, assoc=assoc,
                tcarpv=adapt("tcarpv"), cmj=adapt("cmj"), bksoma=adapt("bksoma"),
                n_pm=len(PV), n_ph=int(ad.loc["tcarpv", "n"]))
    return "const AERO=" + json.dumps(aero)

def gen_DESC():
    """DESC ← gold.an_desc: [lab, média, DP, "min–max"] por dimensão."""
    d = lh.read_delta("gold", "an_desc").set_index("var")
    def rng(k):
        mn = int(d.loc[k, "minimo"]); mx = int(d.loc[k, "maximo"])
        return (f"−{abs(mn)}" if mn < 0 else f"{mn}") + "–" + str(mx)
    rows = [f'["{lab}",{_n(d.loc[k,"media"],1)},{_n(d.loc[k,"dp"],1)},"{rng(k)}"]' for k, lab in ORDER]
    return "const DESC=[" + ",".join(rows) + "]"

PREPOS_ORDER = [("tensao", "Tensão"), ("depressao", "Depressão"), ("raiva", "Raiva"),
                ("vigor", "Vigor"), ("fadiga", "Fadiga"), ("confusao", "Confusão"), ("pth", "PTH")]

def gen_PREPOS():
    """PREPOS ← gold.an_prepos_dim: [lab, pré, pós, %, "p", dz] (pré=1ª do dia, pós=última)."""
    d = lh.read_delta("gold", "an_prepos_dim").set_index("var")
    rows = [f'["{lab}",{d.loc[k,"pre"]:.2f},{d.loc[k,"pos"]:.2f},{int(d.loc[k,"pct"])},'
            f'{_pstr(d.loc[k,"p"])},{_n(d.loc[k,"dz"],2)}]' for k, lab in PREPOS_ORDER]
    return "const PREPOS=[" + ",".join(rows) + "]"

PERFIS_ORDER = ["Iceberg", "Superficie", "Submerso", "Barbatana de tubarao",
                "Everest invertido", "Iceberg invertido"]

def gen_PERFIS():
    """PERFIS ← gold.an_perfis_byday_count: [perfil, n_D1, n_D7]."""
    d = lh.read_delta("gold", "an_perfis_byday_count").set_index("perfil")
    rows = [f'["{ACC[nm]}",{int(d.loc[nm,"d1"])},{int(d.loc[nm,"d7"])}]' for nm in PERFIS_ORDER]
    return "const PERFIS=[" + ",".join(rows) + "]"

def gen_SONO():
    """SONO ← gold: an_wellbeing(d17) · an_wellbeing_byday · an_wellbeing_corr(atleta-dia) · an_wellbeing_bytype."""
    d17 = lh.read_delta("gold", "an_wellbeing").set_index("var")
    byd = lh.read_delta("gold", "an_wellbeing_byday").sort_values("dia")
    cor = lh.read_delta("gold", "an_wellbeing_corr").set_index("par")
    byt = lh.read_delta("gold", "an_wellbeing_bytype").set_index("cat")
    ck = {"Epworth_Fadiga": "epworth × fadiga", "Epworth_Vigor": "epworth × vigor",
          "Epworth_TMD": "epworth × pth", "PSS_TMD": "pss × pth", "PSS_Vigor": "pss × vigor"}
    corr = {k: {"rho": float(cor.loc[v, "rho"]), "p": float(cor.loc[v, "p"])} for k, v in ck.items()}
    sono = {
        "byday": {"Epworth": [float(x) for x in byd["epworth"]], "PSS": [float(x) for x in byd["pss"]]},
        "d17": {"Epworth": {"d1": float(d17.loc["epworth", "d1"]), "d7": float(d17.loc["epworth", "d7"]),
                            "dz": float(d17.loc["epworth", "dz"]), "p": float(d17.loc["epworth", "p"])},
                "PSS": {"d1": float(d17.loc["pss", "d1"]), "d7": float(d17.loc["pss", "d7"]),
                        "dz": float(d17.loc["pss", "dz"]), "p": float(d17.loc["pss", "p"])}},
        "corr": corr,
        "bytype": {"Epworth": {c: float(byt.loc[c, "epworth"]) for c in ["Outro", "HIIT", "Amistoso"]},
                   "PSS": {c: float(byt.loc[c, "pss"]) for c in ["Outro", "HIIT", "Amistoso"]}}}
    return "const SONO=" + json.dumps(sono)

def gen_ATLETAV():
    """ATLETAV ← gold.athlete_day: trajetória individual por atleta-dia,
    ordem [Vigor,Fadiga,Tensão,Depressão,Raiva,Confusão,PTH], 1 casa.
    CORRIGE o bug de rótulo: a constante antiga usava uma permutação dos códigos
    (A01→A19…), plotando o atleta errado; agora usa o mesmo A01–A27 do silver/perfis."""
    ad = lh.read_delta("gold", "athlete_day")
    cols = ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao", "pth"]
    out = {}
    for r in ad.itertuples():
        out.setdefault(r.ID, {})[str(int(r.dia))] = [round(float(getattr(r, c)), 1) for c in cols]
    aid_sorted = {a: out[a] for a in sorted(out)}
    return "const ATLETAV=" + json.dumps(aid_sorted)

def gen_HDL(html):
    """HDL: preserva as peças do humor (velG, rowsA, hiit) e regenera do gold as
    peças FÍSICAS (bands, band_n, median, limr) — an_pv_bands + an_pv_threshold."""
    m = re.search(r'const HDL=(\{.*?\});', html)
    hdl = json.loads(m.group(1))
    bd = lh.read_delta("gold", "an_pv_bands")
    bands = {k: [float(bd[(bd.dim == k) & (bd.band == b)]["mean"].iloc[0]) for b in range(3)]
             for k in ["Vigor", "Fadiga", "FadFisica"]}
    band_n = [int(bd[(bd.dim == "Vigor") & (bd.band == b)]["n"].iloc[0]) for b in range(3)]
    th = lh.read_delta("gold", "an_pv_threshold")
    limr = [dict(dim=r.dim, lab=r.lab, hi=float(r.hi), lo=float(r.lo), dz=float(r.dz), p=float(r.p))
            for r in th.itertuples()]
    hdl.update(bands=bands, band_n=band_n, median=float(bd["median"].iloc[0]), limr=limr)
    return "const HDL=" + json.dumps(hdl)

def replace_nested(html, key, new_literal):
    i = html.find(key + ":{")
    assert i >= 0, f"chave {key} não encontrada"
    j = html.index("{", i); depth = 0
    for k in range(j, len(html)):
        if html[k] == "{": depth += 1
        elif html[k] == "}":
            depth -= 1
            if depth == 0:
                return html[:i] + new_literal + html[k + 1:]
    raise ValueError(key)

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
            "PROFATL": gen_PROFATL(), "PROFGRP": gen_PROFGRP(),
            "AERO": gen_AERO(), "HDL": gen_HDL(html), "ATLETAV": gen_ATLETAV(),
            "DESC": gen_DESC(), "PREPOS": gen_PREPOS(), "PERFIS": gen_PERFIS(), "SONO": gen_SONO()}
    for name, rhs in gens.items():
        html = replace_const(html, name, rhs)
        print(f"[painel←gold] const {name} regenerada do gold")
    for key, gen in [("byday", gen_byday()), ("byday_dom", gen_byday_dom())]:
        html = replace_nested(html, key, gen)
        print(f"[painel←gold] PROFDATA.{key} regenerado do gold")
    open(DASH, "w", encoding="utf-8").write(html)
    print("painel atualizado a partir do lakehouse:", os.path.relpath(DASH, lh.ROOT))

if __name__ == "__main__":
    run()
