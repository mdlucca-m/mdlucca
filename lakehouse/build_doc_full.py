# -*- coding: utf-8 -*-
"""Reúne TODAS as estatísticas e figuras do documento ABNT (versão completa).
Descritiva com média, DP, mediana, mínimo, máximo, CV, IC95%; confiabilidade
ICC(A,1)/ICC(A,k) com IC e ômega; humor, sono, estresse e T-CAR (todas as
métricas); efeitos com IC do dz; perfis com KPIs; e a triangulação.
Figuras: fundo branco, sem grade, pontos de inflexão, sem sobreposição de linhas.
Saída em scratchpad/doc2/."""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import lh

SEED = 7
OUT = "/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad/doc2"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.family": "DejaVu Sans", "font.size": 11, "axes.edgecolor": "#2b2b2b",
    "axes.linewidth": 1.1, "axes.grid": False})

C = {"Vigor": "#1b7a3d", "Fadiga": "#d95f02", "FadFisica": "#e6550d", "PTH": "#5e4fa2",
     "Tensao": "#2b7bba", "Depressao": "#b5179e", "Raiva": "#d1112b", "Confusao": "#b8860b",
     "Epworth": "#2b7bba", "PSS": "#5e4fa2", "azul": "#1f5c8a", "laranja": "#d95f02"}
LAB = {"Vigor": "Vigor", "Fadiga": "Fadiga", "FadFisica": "Fadiga física", "Tensao": "Tensão",
       "Depressao": "Depressão", "Raiva": "Raiva", "Confusao": "Confusão", "PTH": "PTH"}
ACC = {"Iceberg": "Iceberg", "Superficie": "Superfície", "Submerso": "Submerso",
       "Everest invertido": "Everest invertido", "Barbatana de tubarao": "Barbatana de tubarão",
       "Iceberg invertido": "Iceberg invertido"}
SUB = ["Tensao", "Depressao", "Raiva", "Vigor", "Fadiga", "Confusao"]
CENT = {"Iceberg": [-.5, -.5, -.5, 1., -.5, -.5], "Iceberg invertido": [.6, .6, .6, -1., .6, .6],
        "Everest invertido": [1.2, 1.4, 1.2, -.8, 1.2, 1.2], "Barbatana de tubarao": [.2, .2, .2, .3, 1.4, .2],
        "Superficie": [0, 0, 0, 0, 0, 0], "Submerso": [-.9, -.9, -.9, -.9, -.9, -.9]}
NAMES = list(CENT); CM = np.array([CENT[k] for k in NAMES])


def mag(dz):
    a = abs(float(dz))
    return "grande" if a >= .8 else "médio" if a >= .5 else "pequeno" if a >= .2 else "trivial"


def desc_row(s):
    s = pd.Series(s).dropna().astype(float); m = s.mean(); sd = s.std(ddof=1); n = len(s)
    ci = stats.t.ppf(0.975, n - 1) * sd / np.sqrt(n) if n > 1 else 0
    return dict(n=int(n), media=round(float(m), 2), dp=round(float(sd), 2),
                mediana=round(float(s.median()), 2), minimo=round(float(s.min()), 2),
                maximo=round(float(s.max()), 2), cv=round(100 * sd / m, 1) if m else 0.0,
                ic_lo=round(float(m - ci), 2), ic_hi=round(float(m + ci), 2))


def icc_ci(m, col):
    import pingouin as pg
    ad = m.groupby(["ID", "dia"])[col].mean().reset_index()
    w = ad.pivot_table(index="ID", columns="dia", values=col).dropna()
    lg = w.reset_index().melt(id_vars="ID", var_name="dia", value_name="v")
    t = pg.intraclass_corr(data=lg, targets="ID", raters="dia", ratings="v")
    def g(ty):
        r = t[t.Type == ty].iloc[0]; ci = r["CI95"]
        return round(float(r["ICC"]), 2), round(float(ci[0]), 2), round(float(ci[1]), 2), int(len(w))
    a1 = g("ICC(A,1)"); ak = g("ICC(A,k)")
    return dict(icc1=a1[0], icc1_lo=a1[1], icc1_hi=a1[2], icck=ak[0], icck_lo=ak[1], icck_hi=ak[2], n=a1[3])


def dz_ci(pre, pos, B=2000):
    j = pd.concat([pd.Series(pre).reset_index(drop=True), pd.Series(pos).reset_index(drop=True)], axis=1).dropna()
    j.columns = ["a", "b"]; d = (j["b"] - j["a"]).values
    if len(d) < 5 or d.std(ddof=1) == 0:
        return 0.0, 0.0, 0.0, 1.0
    dz = d.mean() / d.std(ddof=1)
    rng = np.random.default_rng(SEED); n = len(d)
    bs = []
    for _ in range(B):
        s = d[rng.integers(0, n, n)]
        sd = s.std(ddof=1)
        bs.append(s.mean() / sd if sd else 0.0)
    lo, hi = np.percentile(bs, [2.5, 97.5])
    p = stats.wilcoxon(j["a"], j["b"]).pvalue
    return round(float(dz), 2), round(float(lo), 2), round(float(hi), 2), float(p)


def classify(df, mu, sd):
    Z = (df[SUB] - mu) / sd
    return Z.apply(lambda r: NAMES[int(((CM - r.values) ** 2).sum(1).argmin())], axis=1)


def gather():
    m = lh.read_delta("silver", "mood"); wb = lh.read_delta("silver", "wellbeing")
    ph = lh.read_delta("silver", "physical")
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    omega = lh.read_delta("gold", "an_omega").set_index("dim")
    sp = lh.read_delta("gold", "an_spearman"); wc = lh.read_delta("gold", "an_wellbeing_corr")
    prof = lh.read_delta("gold", "an_profiles")
    tri = {t: lh.read_delta("gold", t) for t in
           ["an_tri_acute", "an_tri_contrast", "an_tri_cv", "an_tri_prof_day",
            "an_tri_wb_daytype", "an_tri_wb_profile"]}
    prepos = lh.read_delta("gold", "an_prepos_dim").set_index("var")

    DIMS = [("Vigor", "Vigor"), ("Fadiga", "Fadiga"), ("FadFisica", "Fadiga física"),
            ("Tensao", "Tensão"), ("Depressao", "Depressão"), ("Raiva", "Raiva"),
            ("Confusao", "Confusão"), ("PTH", "PTH")]
    omg = {"Vigor": "vigor", "Fadiga": "fadiga", "Tensao": "tensao", "Depressao": "depressao",
           "Raiva": "raiva", "Confusao": "confusao"}

    mood_desc = []
    for col, lab in DIMS:
        d = desc_row(m[col]); d["lab"] = lab; d["col"] = col
        ic = icc_ci(m, col)
        d.update(icc1=ic["icc1"], icc1_lo=ic["icc1_lo"], icc1_hi=ic["icc1_hi"],
                 icck=ic["icck"], icck_lo=ic["icck_lo"], icck_hi=ic["icck_hi"], icc_n=ic["n"])
        d["omega"] = round(float(omega.loc[omg[col], "omega"]), 2) if col in omg else None
        mood_desc.append(d)

    # sono/estresse
    wb_desc = []
    for col, lab in [("epworth", "Epworth (sonolência)"), ("pss", "PSS (estresse)")]:
        d = desc_row(wb[col]); d["lab"] = lab
        # ICC entre dias para sono/estresse
        try:
            ic = icc_ci(wb.rename(columns={col: "x"}).assign(**{col: wb[col]}), col)
            d.update(icc1=ic["icc1"], icc1_lo=ic["icc1_lo"], icc1_hi=ic["icc1_hi"], icc_n=ic["n"])
        except Exception:
            d.update(icc1=None, icc1_lo=None, icc1_hi=None, icc_n=None)
        wb_desc.append(d)

    # T-CAR completo + neuromuscular + antropometria
    def prepos_metric(pre, pos, lab, unit):
        dp = desc_row(pre); dq = desc_row(pos); dz, lo, hi, p = dz_ci(ph[pre.name] if hasattr(pre, 'name') else pre, pos)
        return dict(lab=lab, unit=unit, pre=dp, pos=dq, dz=dz, dz_lo=lo, dz_hi=hi, p=p, mag=mag(dz))
    tcar = [
        prepos_metric(ph.TCARpv_pre, ph.TCARpv_pos, "Pico de velocidade (PV)", "km/h"),
        prepos_metric(ph.TCARfc_pre, ph.TCARfc_pos, "FC máxima no teste", "bpm"),
        prepos_metric(ph.TCARrep_pre, ph.TCARrep_pos, "Repetições completadas", "n"),
    ]
    neuro = [
        prepos_metric(ph.CMJ_pre, ph.CMJ_pos, "Salto com contramovimento (CMJ)", "cm"),
        prepos_metric(ph.BkMel_pre, ph.BkMel_pos, "Baker melhor tempo", "s"),
        prepos_metric(ph.BkSoma_pre, ph.BkSoma_pos, "Baker tempo total", "s"),
        prepos_metric(ph.BkF_pre, ph.BkF_pos, "Baker índice de fadiga", "%"),
    ]
    anthro = [dict(lab=l, unit=u, **desc_row(ph[c])) for c, l, u in
              [("Idade", "Idade", "anos"), ("Estatura", "Estatura", "m"),
               ("Massa", "Massa corporal", "kg"), ("%G", "Gordura corporal", "%")]]
    carga = [dict(lab=l, unit=u, **desc_row(ph[c])) for c, l, u in
             [("Carga_PSE", "PSE da sessão", "u.a."), ("Carga_TRIMP", "TRIMP", "u.a."),
              ("Carga_%FC", "Carga (% FC)", "%")]]

    # perfis com KPIs (índice de iceberg = vigor - média das negativas)
    mu, sd = m[SUB].mean(), m[SUB].std()
    mm = m.copy(); mm["perfil"] = classify(mm, mu, sd).values
    prof_kpi = []
    NEG = ["Tensao", "Depressao", "Raiva", "Confusao", "Fadiga"]
    for nm in NAMES:
        sub = mm[mm.perfil == nm]
        prev = 100 * len(sub) / len(mm)
        idx = float(sub["Vigor"].mean() - sub[NEG].mean(axis=1).mean()) if len(sub) else 0.0
        n_at = int(sub.groupby("ID").size().pipe(lambda s: (s >= 1).sum())) if len(sub) else 0
        prof_kpi.append(dict(perfil=ACC[nm], prev=round(prev, 1), n=int(len(sub)),
                             n_atletas=n_at, indice=round(idx, 2),
                             vigor=round(float(sub["Vigor"].mean()), 1) if len(sub) else 0,
                             tmd=round(float(sub["PTH"].mean()), 1) if len(sub) else 0,
                             fad=round(float(sub["Fadiga"].mean()), 1) if len(sub) else 0))
    prof_kpi.sort(key=lambda r: -r["prev"])

    # índice de iceberg do grupo por dia (vigor - média negativas), com IC
    ice_day = []
    for d in range(1, 8):
        s = mm[mm.dia == d]
        vals = (s["Vigor"] - s[NEG].mean(axis=1))
        dd = desc_row(vals); dd["dia"] = d; ice_day.append(dd)

    def rows(df, keys):
        return [dict(zip(keys, [getattr(r, k) for k in keys])) for r in df.itertuples()]

    data = dict(
        meta=dict(n_atletas=int(m.ID.nunique()), n_resp=int(len(m)), n_dias=int(m.dia.nunique()),
                  n_fisico=int(len(ph)), n_ctrl=int((ph.Grupo == "Controle").sum()),
                  n_exp=int((ph.Grupo == "Experimental").sum())),
        daily={c: [round(float(v), 2) for v in dg[c]] for c in
               ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao", "pth"]},
        daytype=list(dg["day_type"]),
        mood_desc=mood_desc, wb_desc=wb_desc, tcar=tcar, neuro=neuro, anthro=anthro, carga=carga,
        prof_kpi=prof_kpi, ice_day=ice_day,
        prepos=[dict(lab=lab, pre=round(float(prepos.loc[k, "pre"]), 2), pos=round(float(prepos.loc[k, "pos"]), 2),
                     pct=int(prepos.loc[k, "pct"]), p=float(prepos.loc[k, "p"]), dz=round(float(prepos.loc[k, "dz"]), 2),
                     mag=mag(prepos.loc[k, "dz"])) for k, lab in
                [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
                 ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]],
        spearman=[dict(par=r.par, rho=round(float(r.rho), 2), p=float(r.p)) for r in sp.itertuples()],
        wcorr=[dict(par=r.par, rho=round(float(r.rho), 2), p=float(r.p)) for r in wc.itertuples()],
        acute=[dict(var=r.var, lab=r.lab, tipo=r.tipo, dz=float(r.dz), p=float(r.p), sig=bool(r.sig))
               for r in tri["an_tri_acute"].itertuples()],
        contrast=[dict(var=r.var, lab=r.lab, hiit=float(r.media_hiit), jogo=float(r.media_jogo),
                       dz=float(r.dz), p=float(r.p), mag=r.magnitude, fdr=float(r.fdr), sig_fdr=bool(r.sig_fdr))
                  for r in tri["an_tri_contrast"].itertuples()],
        prof_day={p_: [float(tri["an_tri_prof_day"][(tri["an_tri_prof_day"].dia == d) & (tri["an_tri_prof_day"].perfil == p_)]["pct"].iloc[0])
                       for d in range(1, 8)]
                  for p_ in ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão", "Everest invertido", "Iceberg invertido"]},
        wb_daytype=[dict(medida=r.medida, outro=float(r.outro), hiit=float(r.hiit), jogo=float(r.jogo),
                         dz=float(r.dz_hiit_jogo), p=float(r.p), sig=bool(r.sig)) for r in tri["an_tri_wb_daytype"].itertuples()],
        wb_profile=[dict(medida=r.medida, favoravel=float(r.favoravel), neutro=float(r.neutro),
                         risco=float(r.risco), H=float(r.H), p=float(r.p), sig=bool(r.sig)) for r in tri["an_tri_wb_profile"].itertuples()],
    )
    return data, m, wb, ph


# ---------------- FIGURAS ----------------
def clean(ax, ytitle=None, xtitle=None):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=4, width=1.0, colors="#2b2b2b", labelsize=9)
    if ytitle:
        ax.set_ylabel(ytitle, fontsize=10)
    if xtitle:
        ax.set_xlabel(xtitle, fontsize=10)


def inflex(y):
    d = np.diff(y); idx = []
    for i in range(1, len(y) - 1):
        if (d[i - 1] > 0 and d[i] <= 0) or (d[i - 1] < 0 and d[i] >= 0):
            idx.append(i)
    return idx


def daylabels(dt):
    return [f"D{d}\n{t if t != 'Baseline' else 'Base'}" for d, t in zip(range(1, 8), dt)]


def fig_traj_facets(data):
    """Small multiples: uma variável por painel, sem sobreposição de linhas."""
    order = [("vigor", "Vigor", C["Vigor"]), ("fadiga", "Fadiga", C["Fadiga"]),
             ("pth", "PTH", C["PTH"]), ("tensao", "Tensão", C["Tensao"]),
             ("depressao", "Depressão", C["Depressao"]), ("raiva", "Raiva", C["Raiva"]),
             ("confusao", "Confusão", C["Confusao"])]
    dias = list(range(1, 8)); dt = data["daytype"]
    fig, axes = plt.subplots(3, 3, figsize=(9.6, 8.0), sharex=True)
    axes = axes.ravel()
    for ax, (k, lab, col) in zip(axes, order):
        y = data["daily"][k]
        ax.plot(dias, y, "-", color=col, lw=3.2, solid_capstyle="round", zorder=3)
        ax.plot(dias, y, "o", color=col, ms=5, zorder=4)
        for i in inflex(y):
            ax.plot(dias[i], y[i], "o", ms=10, mfc="white", mec=col, mew=2.0, zorder=5)
            ax.annotate(f"{y[i]:.1f}".replace(".", ","), (dias[i], y[i]), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8, color=col, fontweight="bold")
        ax.set_title(lab, fontsize=11, color=col, fontweight="bold", pad=6)
        ax.set_ylim(0, max(y) + 1.2 if max(y) > 3 else 4)
        ax.set_xlim(0.7, 7.3); ax.set_xticks(dias)
        clean(ax)
    for ax in axes[len(order):]:
        ax.axis("off")
    for ax in axes[:len(order)]:
        ax.set_xticklabels([f"D{d}" for d in dias], fontsize=8)
    fig.text(0.5, 0.06, "Dia do microciclo (D2·D4·D7 = HIIT; D3·D5 = jogo; D6 = força)", ha="center", fontsize=9.5)
    fig.text(0.02, 0.5, "Escore BRUMS (0–16)", va="center", rotation=90, fontsize=9.5)
    fig.tight_layout(rect=[0.03, 0.07, 1, 1])
    fig.savefig(f"{OUT}/fig_traj_facets.png", dpi=150); plt.close(fig)


def fig_sono_traj(data, wb):
    dias = list(range(1, 8)); dt = data["daytype"]
    ep = [float(wb[wb.dia == d]["epworth"].mean()) for d in dias]
    ps = [float(wb[wb.dia == d]["pss"].mean()) for d in dias]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9.4, 3.9))
    for ax, y, lab, col in [(a1, ep, "Sonolência (Epworth)", C["Epworth"]), (a2, ps, "Estresse (PSS)", C["PSS"])]:
        ax.plot(dias, y, "-", color=col, lw=3.2, solid_capstyle="round", zorder=3)
        ax.plot(dias, y, "o", color=col, ms=5, zorder=4)
        for i in inflex(y):
            ax.plot(dias[i], y[i], "o", ms=10, mfc="white", mec=col, mew=2.0, zorder=5)
            ax.annotate(f"{y[i]:.1f}".replace(".", ","), (dias[i], y[i]), textcoords="offset points",
                        xytext=(0, 8), ha="center", fontsize=8, color=col, fontweight="bold")
        ax.set_title(lab, fontsize=11, color=col, fontweight="bold")
        ax.set_xticks(dias); ax.set_xticklabels([f"D{d}" for d in dias], fontsize=8)
        ax.set_ylim(min(y) - 2, max(y) + 2)
        clean(ax)
    a1.set_ylabel("Escore", fontsize=10)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_sono_traj.png", dpi=150); plt.close(fig)


def fig_tcar(data):
    """T-CAR pré→pós: dumbbell por métrica (sem sobreposição)."""
    items = data["tcar"]
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 3.6))
    for ax, it in zip(axes, items):
        pre, pos = it["pre"]["media"], it["pos"]["media"]
        ax.plot([0, 1], [pre, pos], "-", color="#9aa4b2", lw=2.4, zorder=1)
        ax.plot(0, pre, "o", color=C["azul"], ms=13, zorder=3)
        ax.plot(1, pos, "o", color=C["laranja"], ms=13, zorder=3)
        ax.annotate(f"{pre:.1f}".replace(".", ","), (0, pre), textcoords="offset points", xytext=(-4, 12), ha="right", fontsize=9, color=C["azul"], fontweight="bold")
        ax.annotate(f"{pos:.1f}".replace(".", ","), (1, pos), textcoords="offset points", xytext=(4, 12), ha="left", fontsize=9, color=C["laranja"], fontweight="bold")
        ax.set_title(f"{it['lab']}\n({it['unit']}) · dz {('+' if it['dz']>=0 else '')}{it['dz']:.2f}".replace(".", ","), fontsize=9.5, pad=8)
        ax.set_xlim(-0.5, 1.5); ax.set_xticks([0, 1]); ax.set_xticklabels(["Pré", "Pós"], fontsize=9)
        rng = max(pre, pos) - min(pre, pos)
        ax.set_ylim(min(pre, pos) - max(rng, 1) * 1.4, max(pre, pos) + max(rng, 1) * 1.4)
        clean(ax)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_tcar.png", dpi=150); plt.close(fig)


def fig_perfil_radar(data):
    """Assinatura dos 6 perfis em escores T (T=50+10z) — padrão do artigo.
    Linhas em painéis separados (sem sobreposição), faixa normal T 40–60."""
    dims = ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"]
    order = ["Iceberg", "Superficie", "Submerso", "Barbatana de tubarao", "Everest invertido", "Iceberg invertido"]
    disp = {"Superficie": "Superfície", "Barbatana de tubarao": "Barbatana de tubarão"}
    COL = {"Iceberg": "#2f9e44", "Superficie": "#1971c2", "Submerso": "#7048e8",
           "Barbatana de tubarao": "#e8590c", "Everest invertido": "#e0525b", "Iceberg invertido": "#f59f00"}
    x = np.arange(len(dims))
    fig, axes = plt.subplots(2, 3, figsize=(9.8, 6.2), sharey=True)
    axes = axes.ravel()
    for ax, nm in zip(axes, order):
        col = COL[nm]
        T = [50 + 10 * z for z in CENT[nm]]
        ax.axhspan(40, 60, color="#eef1f4", zorder=0)
        ax.axhline(50, color="#b8c0cc", lw=1.0, ls=(0, (4, 3)), zorder=1)
        ax.plot(x, T, "-", color=col, lw=3.0, solid_capstyle="round", zorder=3)
        ax.plot(x, T, "o", color=col, ms=6, zorder=4)
        ax.set_xticks(x); ax.set_xticklabels(dims, rotation=32, ha="right", fontsize=8)
        ax.set_ylim(30, 72)
        ax.set_title(disp.get(nm, nm), fontsize=11, color=col, fontweight="bold", pad=6)
        clean(ax)
        ax.set_yticks([40, 50, 60])
    axes[0].set_ylabel("Escore T", fontsize=10); axes[3].set_ylabel("Escore T", fontsize=10)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_perfil_radar.png", dpi=150); plt.close(fig)


def fig_prof_day(data):
    dias = list(range(1, 8)); dt = data["daytype"]
    sel = [("Barbatana de tubarão", C["Fadiga"], "Barbatana (sobrecarga)"),
           ("Submerso", C["Tensao"], "Submerso (recolhimento)"),
           ("Iceberg", C["Vigor"], "Iceberg (favorável)")]
    fig, ax = plt.subplots(figsize=(8.6, 4.3))
    for perfil, col, lab in sel:
        y = data["prof_day"][perfil]
        ax.plot(dias, y, "-", color=col, lw=3.2, solid_capstyle="round", label=lab, zorder=3)
        ax.plot(dias, y, "o", color=col, ms=5, zorder=4)
        for i in inflex(y):
            ax.plot(dias[i], y[i], "o", ms=10, mfc="white", mec=col, mew=2.0, zorder=5)
    ax.set_xlim(0.7, 7.3); ax.set_ylim(0, 46); ax.set_xticks(dias)
    ax.set_xticklabels(daylabels(dt), fontsize=9)
    clean(ax, "Prevalência do perfil (%)")
    ax.yaxis.set_major_locator(MultipleLocator(10))
    ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.12), fontsize=9.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_prof_day.png", dpi=150); plt.close(fig)


def fig_agudo(data):
    order = ["vigor", "fadiga", "fadfisica", "tensao", "depressao", "raiva", "confusao", "pth"]
    ac = {(r["var"], r["tipo"]): r for r in data["acute"]}
    labs = [LAB[k.capitalize()] if k.capitalize() in LAB else k for k in order]
    labs = ["Vigor", "Fadiga", "Fadiga física", "Tensão", "Depressão", "Raiva", "Confusão", "PTH"]
    hi = [ac[(k, "HIIT")]["dz"] for k in order]; jo = [ac[(k, "Jogo")]["dz"] for k in order]
    x = np.arange(len(order)); w = 0.38
    fig, ax = plt.subplots(figsize=(9.0, 4.2))
    ax.axhline(0, color="#2b2b2b", lw=1.0)
    ax.bar(x - w / 2, hi, w, color=C["Fadiga"], label="HIIT")
    ax.bar(x + w / 2, jo, w, color=C["Tensao"], label="Jogo (amistoso)")
    for xi, v in zip(x - w / 2, hi):
        ax.annotate(f"{v:+.2f}".replace(".", ","), (xi, v), textcoords="offset points", xytext=(0, 3 if v >= 0 else -10), ha="center", fontsize=7, color="#2b2b2b")
    for xi, v in zip(x + w / 2, jo):
        ax.annotate(f"{v:+.2f}".replace(".", ","), (xi, v), textcoords="offset points", xytext=(0, 3 if v >= 0 else -10), ha="center", fontsize=7, color="#2b2b2b")
    ax.set_xticks(x); ax.set_xticklabels(labs, rotation=22, ha="right", fontsize=9)
    ax.set_ylim(min(hi + jo) - 0.25, max(hi + jo) + 0.3)
    clean(ax, "Efeito agudo dz (pré→pós)")
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_agudo.png", dpi=150); plt.close(fig)


def fig_contrast(data):
    rows = sorted(data["contrast"], key=lambda r: r["dz"])
    labs = [r["lab"] for r in rows]; dz = [r["dz"] for r in rows]
    cols = [(C["Raiva"] if r["sig_fdr"] else (C["Fadiga"] if r["p"] < .05 else "#9aa4b2")) for r in rows]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(8.6, 4.1))
    ax.axvline(0, color="#2b2b2b", lw=1.0)
    for yi, v, c in zip(y, dz, cols):
        ax.plot([0, v], [yi, yi], "-", color=c, lw=3.2, solid_capstyle="round", zorder=2)
        ax.plot(v, yi, "o", color=c, ms=9, zorder=3)
        ax.annotate(f"{v:+.2f}".replace(".", ","), (v, yi), textcoords="offset points", xytext=(9 if v >= 0 else -9, 0), va="center", ha="left" if v >= 0 else "right", fontsize=9, fontweight="bold", color="#2b2b2b")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=10)
    ax.set_xlim(-0.2, 0.62); clean(ax, None, "dz (média HIIT − média jogo) · positivo = maior no HIIT")
    ax.xaxis.set_major_locator(MultipleLocator(0.1))
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_contrast.png", dpi=150); plt.close(fig)


def fig_sono_perfil(data):
    grp = ["favoravel", "neutro", "risco"]; glab = ["Favorável", "Neutro", "Risco"]
    ep = next(w for w in data["wb_profile"] if w["medida"] == "Epworth")
    ps = next(w for w in data["wb_profile"] if w["medida"] == "PSS")
    x = np.arange(3); w = 0.38
    fig, ax = plt.subplots(figsize=(7.4, 4.0))
    ax.bar(x - w / 2, [ep[g] for g in grp], w, color=C["Epworth"], label="Sonolência (Epworth)")
    ax.bar(x + w / 2, [ps[g] for g in grp], w, color=C["PSS"], label="Estresse (PSS)")
    for xi, g in zip(x - w / 2, grp):
        ax.annotate(f"{ep[g]:.1f}".replace(".", ","), (xi, ep[g]), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    for xi, g in zip(x + w / 2, grp):
        ax.annotate(f"{ps[g]:.1f}".replace(".", ","), (xi, ps[g]), textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9)
    ax.set_xticks(x); ax.set_xticklabels(glab, fontsize=11); ax.set_ylim(0, 26)
    clean(ax, "Média"); ax.yaxis.set_major_locator(MultipleLocator(5))
    ax.legend(frameon=False, fontsize=9.5, loc="upper left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_sono_perfil.png", dpi=150); plt.close(fig)


def fig_ice_index(data):
    """Índice de iceberg do grupo por dia, com IC95%."""
    dias = list(range(1, 8)); dt = data["daytype"]
    y = [r["media"] for r in data["ice_day"]]; lo = [r["ic_lo"] for r in data["ice_day"]]; hi = [r["ic_hi"] for r in data["ice_day"]]
    fig, ax = plt.subplots(figsize=(8.6, 4.0))
    ax.fill_between(dias, lo, hi, color=C["Vigor"], alpha=0.13, zorder=1)
    ax.plot(dias, y, "-", color=C["Vigor"], lw=3.2, solid_capstyle="round", zorder=3)
    ax.plot(dias, y, "o", color=C["Vigor"], ms=5, zorder=4)
    for i in inflex(y):
        ax.plot(dias[i], y[i], "o", ms=10, mfc="white", mec=C["Vigor"], mew=2.0, zorder=5)
        ax.annotate(f"{y[i]:.1f}".replace(".", ","), (dias[i], y[i]), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=8, color=C["Vigor"], fontweight="bold")
    ax.axhline(0, color="#9aa4b2", lw=1.0, ls=(0, (4, 3)))
    ax.set_xticks(dias); ax.set_xticklabels(daylabels(dt), fontsize=9); ax.set_xlim(0.7, 7.3)
    clean(ax, "Índice de iceberg (vigor − média das negativas)")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_ice_index.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    data, m, wb, ph = gather()
    with open(f"{OUT}/data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    fig_traj_facets(data); fig_sono_traj(data, wb); fig_tcar(data); fig_perfil_radar(data)
    fig_prof_day(data); fig_agudo(data); fig_contrast(data); fig_sono_perfil(data); fig_ice_index(data)
    print("OK ->", OUT)
    print("meta:", data["meta"])
