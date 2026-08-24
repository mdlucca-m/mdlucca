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
import numpy as np
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

def gen_PROFPREV():
    """PROFPREV ← gold.an_profiles: prevalência por perfil (nível resposta), p/ o donut de composição."""
    p = lh.read_delta("gold", "an_profiles").sort_values("prevalencia", ascending=False)
    rows = [f'["{ACC[r.perfil]}",{_n(r.prevalencia,1)}]' for r in p.itertuples()]
    return "const PROFPREV=[" + ",".join(rows) + "]"

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

MODEL_COL = {"Random Forest": "C.vigor", "XGBoost": "C.fadiga", "LightGBM": "C.tensao"}

BR6_ORDER = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
             ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão")]

def gen_ICC():
    """ICC ← gold.an_icc: [lab, ICC(2,1), ICC(2,k), rótulo] por dimensão."""
    d = lh.read_delta("gold", "an_icc").set_index("dim")
    rows = [f'["{lab}",{_n(d.loc[k,"icc1"],2)},{_n(d.loc[k,"icck"],2)},"{d.loc[k,"label"]}"]'
            for k, lab in BR6_ORDER]
    return "const ICC=[" + ",".join(rows) + "]"

def gen_OMEGA():
    """OMEGA ← gold.an_omega: [lab, ômega] por dimensão."""
    d = lh.read_delta("gold", "an_omega").set_index("dim")
    rows = [f'["{lab}",{_n(d.loc[k,"omega"],2)}]' for k, lab in BR6_ORDER]
    return "const OMEGA=[" + ",".join(rows) + "]"

def gen_LIM():
    """LIM ← gold.an_thresholds: [lab, SEM, MDC90, MDC95, SWC] por dimensão."""
    d = lh.read_delta("gold", "an_thresholds").set_index("dim")
    rows = [f'["{lab}",{_n(d.loc[k,"sem"],1)},{_n(d.loc[k,"mdc90"],1)},{_n(d.loc[k,"mdc95"],1)},{_n(d.loc[k,"swc"],1)}]'
            for k, lab in BR6_ORDER]
    return "const LIM=[" + ",".join(rows) + "]"

def gen_VM():
    """VM ← gold.an_variance (+curves): componentes de variância + trajetória pré/pós."""
    vc = lh.read_delta("gold", "an_variance")
    cu = lh.read_delta("gold", "an_variance_curves").sort_values(["dim", "dia"])
    labmap = {"Vigor": "Vigor", "Fadiga": "Fadiga", "TMD": "PTH", "FadFisica": "Fadiga física"}
    vcl = [dict(lab=labmap[r.dim], dim=r.dim, atleta=float(r.atleta), dia=float(r.dia),
               momento=float(r.momento), icc=float(r.icc)) for r in vc.itertuples()]
    curves = {}
    for dim in ["Vigor", "Fadiga", "TMD", "FadFisica"]:
        sub = cu[cu.dim == dim]
        x, y = [], []
        for r in sub.itertuples():
            x += [float(r.x_pre), float(r.x_pos)]; y += [float(r.y_pre), float(r.y_pos)]
        curves[dim] = {"x": x, "y": y}
    ef = lh.read_delta("gold", "an_variance_eff").set_index("dim")
    eff = {d: {"ag": float(ef.loc[d, "ag"]), "agdz": float(ef.loc[d, "agdz"]),
               "rec": float(ef.loc[d, "rec"]), "recdz": float(ef.loc[d, "recdz"])}
           for d in ["Vigor", "Fadiga", "TMD", "FadFisica"]}
    return "const VM=" + json.dumps({"vc": vcl, "eff": eff, "curves": curves})

def gen_TRANS():
    """TRANS ← gold.an_transitions: [lab, tipo, vigor, fadiga, pth, sig]."""
    d = lh.read_delta("gold", "an_transitions")
    rows = [f'["{r.lab}","{r.tipo}",{_n(r.vigor,2)},{_n(r.fadiga,2)},{_n(r.pth,2)},{str(bool(r.sig)).lower()}]'
            for r in d.itertuples()]
    return "const TRANS=[" + ",".join(rows) + "]"

def gen_PRISCO():
    """PRISCO ← gold.an_risk_profiles: exposição a perfis de risco."""
    r = lh.read_delta("gold", "an_risk_profiles").iloc[0]
    return (f'const PRISCO={{neg_prev:{_n(r["neg_prev"],1)},fad_prev:{_n(r["fad_prev"],1)},'
            f'byday:{r["byday"]},exp_neg1:{int(r["exp_neg1"])},exp_neg2:{int(r["exp_neg2"])},'
            f'exp_fad1:{int(r["exp_fad1"])},never:{int(r["never"])}}}')

ABBR_NAME = {"IC": "Iceberg", "SU": "Superfície", "SB": "Submerso",
             "BT": "Barbatana", "II": "Iceberg inv.", "EI": "Everest inv."}

CURVE_ORDER = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
               ("confusao", "Confusão"), ("raiva", "Raiva"), ("depressao", "Depressão")]

def _curve_label(dz, pw, pf, piso):
    both = pw < 0.05 and pf < 0.05; anys = pw < 0.05 or pf < 0.05
    d = "queda" if dz < 0 else "subida"
    if both and abs(dz) >= 0.7: return f"{d} robusta"
    if both: return f"{d} moderada"
    if anys: return f"{d} consistente"
    if piso >= 65: return "piso · sem tendência"
    return "sem tendência clara"

def _payload(table):
    return lh.read_delta("gold", table).iloc[0]["payload"]

def gen_DERIV():
    return "const DERIV=" + _payload("an_deriv")

def gen_TRICONF():
    """TRICONF ← gold.an_tric_payload: confirmação da triangulação (métodos convergentes) + interno×externo."""
    return "const TRICONF=" + _payload("an_tric_payload")

def gen_FAC():
    """FAC ← gold.an_fac_payload: análise fatorial Momento × Tipo de dia (rm-ANOVA + misto)."""
    return "const FAC=" + _payload("an_fac_payload")

def gen_DYN():
    """DYN ← gold.an_dyn_payload: AR(1) multinível + GLM Poisson-GEE."""
    return "const DYN=" + _payload("an_dyn_payload")

def gen_LOAD():
    """LOAD ← gold.an_load_payload: sessões segmentadas + normalização de carga."""
    return "const LOAD=" + _payload("an_load_payload")

def gen_NORM():
    """NORMSTD ← gold.an_norm_payload: perfis sob padronização interna × externa (ilustrativa)."""
    return "const NORMSTD=" + _payload("an_norm_payload")

def gen_TWO():
    """TWO ← gold.an_two_payload: comparação dos dois caminhos (n=19 sem imputação
    × n=27 com imputação) + modelo misto n=27, para a aba de dois caminhos."""
    return "const TWO=" + _payload("an_two_payload")

def gen_SENSV():
    return "const SENSV=" + _payload("an_sensitivity")

def gen_HVS():
    return "const HVS=" + _payload("an_recovery")

def gen_SENSA():
    return "const SENSA=" + _payload("an_sensitivity_robust")

def gen_IOTPRED():
    return "const IOTPRED=" + _payload("an_iot")

def gen_MV():
    """MV ← gold.an_pca: dispersão PCA + clusters + cargas + variância (estrutura multivariada)."""
    return "const MV=" + lh.read_delta("gold", "an_pca").iloc[0]["payload"]

def gen_LC():
    """LC_X/LC_TR/LC_CV ← gold.an_learning: curva de aprendizado (treino × validação)."""
    d = lh.read_delta("gold", "an_learning").sort_values("n")
    xs = ",".join(str(int(v)) for v in d["n"])
    tr = ",".join(_n(v, 3) for v in d["train_auc"])
    cv = ",".join(_n(v, 3) for v in d["cv_auc"])
    return f"const LC_X=[{xs}],LC_TR=[{tr}],LC_CV=[{cv}]"

def _crossings(a, b):
    """Dias (interpolação linear) onde a curva a cruza a curva b (1..7)."""
    xs = []
    for i in range(6):
        da, db = a[i] - b[i], a[i + 1] - b[i + 1]
        if da == 0:
            xs.append(float(i + 1))
        elif da * db < 0:
            xs.append(round(i + 1 + da / (da - db), 1))
    return xs

def gen_CROSS():
    """CROSS/CURVE_CROSS ← gold.daily_group: dias de cruzamento vigor × fadiga."""
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    xs = _crossings(list(dg["vigor"]), list(dg["fadiga"]))
    lit = "[" + ",".join(_n(x, 1) for x in xs) + "]"
    return lit  # usado por replace_const para CROSS e CURVE_CROSS

def gen_CURVE():
    """CURVE ← gold (daily_group · an_d17 · an_friedman · an_snr): resumo por dimensão."""
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    d17 = lh.read_delta("gold", "an_d17").set_index("var")
    fr = lh.read_delta("gold", "an_friedman").set_index("var")
    sn = lh.read_delta("gold", "an_snr").set_index("var")
    rows = []
    for k, lab in CURVE_ORDER:
        d1 = float(dg.iloc[0][k]); d7 = float(dg.iloc[6][k]); dz = float(d17.loc[k, "dz"])
        pw = float(d17.loc[k, "p_wilcoxon"]); pf = float(fr.loc[k, "p"]); piso = float(sn.loc[k, "piso"])
        lbl = _curve_label(dz, pw, pf, piso)
        rows.append(f'["{lab}",{_n(d1,1)},{_n(d7,1)},{_n(d7-d1,1)},{_n(dz,2)},'
                    f'{_pstr(pw)},{_pstr(pf)},{_n(sn.loc[k,"snr"],1)},"{lbl}"]')
    return "const CURVE=[" + ",".join(rows) + "]"

def gen_ATLETA():
    """ATLETA ← gold.an_athlete_profiles: ícones de perfil dia a dia por atleta
    (mesmo A01–A27 do silver), consistente com ATLETAV/PROFATL."""
    ap = lh.read_delta("gold", "an_athlete_profiles")
    g = {}
    for r in ap.itertuples():
        g.setdefault(r.ID, {})[str(int(r.dia))] = [int(r.risco), r.abbr,
                                                    round(float(r.pth), 1), round(float(r.vigor), 1), round(float(r.fadiga), 1)]
    ids = sorted(g)
    return "const ATLETA=" + json.dumps({"g": {a: g[a] for a in ids}, "ids": ids, "names": ABBR_NAME})

def gen_ALO():
    """ALO ← gold.an_allometry + silver.pv_mood: expoentes de escala + curva ajustada
    (fit de Fadiga física) e nuvem observada (pvobs/obs) para o gráfico alométrico."""
    d = lh.read_delta("gold", "an_allometry")
    pm = lh.read_delta("silver", "pv_mood")
    ff = pm[pm.dim == "FadFisica"].sort_values("pair")
    pvobs = [round(float(x), 2) for x in ff["pv"]]; obs = [round(float(x), 2) for x in ff["mood"]]
    xs = list(np.linspace(float(pm["pv"].min()), float(pm["pv"].max()), 60))
    rows = [dict(dim=r.dim, lab=r.lab, b=float(r.b), lo=float(r.lo), hi=float(r.hi),
                 r2=float(r.r2), p=float(r.p), a=float(r.a)) for r in d.itertuples()]
    fr = d[d.dim == "FadFisica"].iloc[0]  # curva plotada = Fadiga física
    fit = [float(np.exp(fr["a"] + fr["b"] * np.log(x))) for x in xs]
    curve = {"pv": [round(x, 4) for x in xs], "fit": fit, "pvobs": pvobs, "obs": obs}
    return "const ALO=" + json.dumps({"rows": rows, "curve": curve})

def gen_PVMODEL():
    """PVMODEL ← gold.an_pvmodel: comparação de modelos PV→humor por RMSE (LOO)."""
    payload = lh.read_delta("gold", "an_pvmodel").iloc[0]["payload"]
    return "const PVMODEL=" + payload

def gen_NEGDT():
    """NEGDT ← gold: an_negatives_bydaytype (means+acute) · an_negatives_daytype (mid) · an_negatives_mix."""
    bd = lh.read_delta("gold", "an_negatives_bydaytype")
    mid = lh.read_delta("gold", "an_negatives_daytype").set_index("var")
    mx = lh.read_delta("gold", "an_negatives_mix").set_index("dim")
    NEG = ["Tensao", "Depressao", "Raiva", "Confusao"]
    means = {k: {c: float(bd[(bd.dim == k) & (bd.cat == c)]["media"].iloc[0]) for c in ["Outro", "HIIT", "Amistoso"]}
             for k in NEG + ["Vigor", "Fadiga"]}
    kn = {"Tensao": "tensao", "Depressao": "depressao", "Raiva": "raiva", "Confusao": "confusao"}
    mid_d = {k: {"amist": float(mid.loc[kn[k], "media_jogo"]), "hiit": float(mid.loc[kn[k], "media_hiit"]),
                 "dz": float(mid.loc[kn[k], "dz_jogo_menos_hiit"]), "p": float(mid.loc[kn[k], "p"])} for k in NEG}
    acute = {k: {"HIIT": float(bd[(bd.dim == k) & (bd.cat == "HIIT")]["acute"].iloc[0]),
                 "Amistoso": float(bd[(bd.dim == k) & (bd.cat == "Amistoso")]["acute"].iloc[0])} for k in NEG}
    mix = {k: {"b": float(mx.loc[k, "b"]), "p": float(mx.loc[k, "p"])} for k in NEG}
    return "const NEGDT=" + json.dumps({"means": means, "mid": mid_d, "acute": acute, "mix": mix})

def gen_TRI():
    """TRI ← gold.an_tri_*: triangulação estímulo (HIIT × jogo) × resposta.
    Empacota os 6 recortes num único JSON: efeito agudo por tipo de dia, contraste
    HIIT×jogo (FDR), coeficiente de variação (+ICC), prevalência de perfil por dia,
    sono/estresse por tipo de dia e por grupo de perfil."""
    ac = lh.read_delta("gold", "an_tri_acute")
    ct = lh.read_delta("gold", "an_tri_contrast")
    cv = lh.read_delta("gold", "an_tri_cv")
    pd_ = lh.read_delta("gold", "an_tri_prof_day").sort_values(["dia"])
    wd = lh.read_delta("gold", "an_tri_wb_daytype")
    wp = lh.read_delta("gold", "an_tri_wb_profile")
    order = ["vigor", "fadiga", "fadfisica", "tensao", "depressao", "raiva", "confusao", "pth"]
    idx = {k: i for i, k in enumerate(order)}
    acute = {}
    for r in ac.itertuples():
        acute.setdefault(r.var, {"lab": r.lab})[r.tipo] = dict(
            pre=float(r.pre), pos=float(r.pos), dz=float(r.dz), p=float(r.p), sig=bool(r.sig))
    acute_l = [dict(var=k, **acute[k]) for k in sorted(acute, key=lambda x: idx.get(x, 99))]
    contrast = [dict(var=r.var, lab=r.lab, hiit=float(r.media_hiit), jogo=float(r.media_jogo),
                     dz=float(r.dz), p=float(r.p), mag=r.magnitude, fdr=float(r.fdr), sig_fdr=bool(r.sig_fdr))
                for r in sorted(ct.itertuples(), key=lambda r: idx.get(r.var, 99))]
    cvl = [dict(var=r.var, lab=r.lab, media=float(r.media), total=float(r.cv_total),
               intradia=float(r.cv_intradia), semana=float(r.cv_semana), icc=float(r.icc))
           for r in sorted(cv.itertuples(), key=lambda r: idx.get(r.var, 99))]
    PROF6 = ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão",
             "Everest invertido", "Iceberg invertido"]
    prof_day = {p: [float(pd_[(pd_.dia == d) & (pd_.perfil == p)]["pct"].iloc[0]) for d in range(1, 8)]
                for p in PROF6}
    wb_daytype = [dict(medida=r.medida, outro=float(r.outro), hiit=float(r.hiit), jogo=float(r.jogo),
                       dz=float(r.dz_hiit_jogo), p=float(r.p), sig=bool(r.sig)) for r in wd.itertuples()]
    wb_profile = [dict(medida=r.medida, favoravel=float(r.favoravel), neutro=float(r.neutro),
                       risco=float(r.risco), H=float(r.H), p=float(r.p), sig=bool(r.sig)) for r in wp.itertuples()]
    return "const TRI=" + json.dumps(dict(acute=acute_l, contrast=contrast, cv=cvl,
                                          prof_day=prof_day, wb_daytype=wb_daytype, wb_profile=wb_profile))

def gen_MODELS():
    """MODELS ← gold.an_models: comparação de AUC (Random Forest, XGBoost, LightGBM)."""
    d = lh.read_delta("gold", "an_models")
    rows = [f'{{lab:"{r.modelo}",auc:{_n(r.auc,2)},col:{MODEL_COL.get(r.modelo,"C.muted")}}}'
            for r in d.itertuples()]
    return "const MODELS=[" + ",".join(rows) + "]"

def gen_ROC():
    """ROC_PTS ← gold.an_roc: curva ROC do melhor modelo."""
    d = lh.read_delta("gold", "an_roc")
    pts = [f'[{_n(r.fpr,3)},{_n(r.tpr,3)}]' for r in d.itertuples()]
    return "const ROC_PTS=[" + ",".join(pts) + "]"

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
            "PROFATL": gen_PROFATL(), "PROFGRP": gen_PROFGRP(), "PROFPREV": gen_PROFPREV(),
            "AERO": gen_AERO(), "HDL": gen_HDL(html), "ATLETAV": gen_ATLETAV(),
            "DESC": gen_DESC(), "PREPOS": gen_PREPOS(), "PERFIS": gen_PERFIS(), "SONO": gen_SONO(),
            "MODELS": gen_MODELS(), "ROC_PTS": gen_ROC(), "NEGDT": gen_NEGDT(), "ICC": gen_ICC(), "OMEGA": gen_OMEGA(),
            "LIM": gen_LIM(), "VM": gen_VM(), "TRANS": gen_TRANS(), "PRISCO": gen_PRISCO(),
            "ALO": gen_ALO(), "PVMODEL": gen_PVMODEL(), "ATLETA": gen_ATLETA(),
            "CURVE": gen_CURVE(), "LC_X": gen_LC(),
            "CROSS": f"const CROSS={gen_CROSS()}", "CURVE_CROSS": f"const CURVE_CROSS={gen_CROSS()}", "MV": gen_MV(), "SENSV": gen_SENSV(), "HVS": gen_HVS(), "SENSA": gen_SENSA(), "IOTPRED": gen_IOTPRED(), "DERIV": gen_DERIV(), "TRI": gen_TRI(), "TWO": gen_TWO(), "NORMSTD": gen_NORM(), "TRICONF": gen_TRICONF(), "FAC": gen_FAC(), "DYN": gen_DYN(), "LOAD": gen_LOAD()}
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
