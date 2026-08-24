# -*- coding: utf-8 -*-
"""Reúne dados do gold e gera as figuras do documento Word da triangulação.
Figuras: fundo branco, sem grade, linhas grossas, pontos de inflexão marcados,
escalas bem distribuídas. Saída em scratchpad/doc/."""
from __future__ import annotations
import json, os
import numpy as np, pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import lh

OUT = "/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad/doc"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.facecolor": "white",
    "font.family": "DejaVu Sans", "font.size": 12, "axes.edgecolor": "#333333",
    "axes.linewidth": 1.2, "axes.grid": False, "svg.fonttype": "none"})

CORES = {"Vigor": "#1b9e77", "Fadiga": "#d95f02", "FadFisica": "#e6550d", "PTH": "#7570b3",
         "Tensao": "#3690c0", "Depressao": "#c51b8a", "Raiva": "#e31a1c", "Confusao": "#d9a300"}
LAB = {"vigor": "Vigor", "fadiga": "Fadiga", "fadfisica": "Fadiga física", "tensao": "Tensão",
       "depressao": "Depressão", "raiva": "Raiva", "confusao": "Confusão", "pth": "PTH"}
ACC = {"Superficie": "Superfície", "Barbatana de tubarao": "Barbatana de tubarão"}


def _mag(dz):
    a = abs(float(dz))
    return "grande" if a >= .8 else "médio" if a >= .5 else "pequeno" if a >= .2 else "trivial"


def _cv(s):
    s = s.dropna(); mu = s.mean()
    return round(100 * s.std() / mu, 1) if mu else 0.0


def gather():
    m = lh.read_delta("silver", "mood")
    dg = lh.read_delta("gold", "daily_group").sort_values("dia")
    desc = lh.read_delta("gold", "an_desc").set_index("var")
    icc = lh.read_delta("gold", "an_icc").set_index("dim")
    pp = lh.read_delta("gold", "an_prepos_dim").set_index("var")
    sp = lh.read_delta("gold", "an_spearman")
    wc = lh.read_delta("gold", "an_wellbeing_corr")
    prof = lh.read_delta("gold", "an_profiles").sort_values("prevalencia", ascending=False)
    tri = {t: lh.read_delta("gold", t) for t in
           ["an_tri_acute", "an_tri_contrast", "an_tri_cv", "an_tri_prof_day",
            "an_tri_wb_daytype", "an_tri_wb_profile"]}

    # CV estendido: total, intradia, pré/pós do dia, pré/pós da semana (D1/D7), semana + ICC
    COLS = [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("fadfisica", "FadFisica"), ("tensao", "Tensao"),
            ("depressao", "Depressao"), ("raiva", "Raiva"), ("confusao", "Confusao"), ("pth", "PTH")]
    tcv = tri["an_tri_cv"].set_index("var")
    cv_rows = []
    for k, col in COLS:
        gd = m.groupby(["ID", "dia"])[col]
        cv_intra = round(float((gd.std() / gd.mean().replace(0, np.nan)).replace([np.inf, -np.inf], np.nan).mean()) * 100, 1)
        cv_rows.append(dict(
            var=k, lab=LAB[k], media=round(float(m[col].mean()), 2),
            cv_total=_cv(m[col]), cv_intradia=cv_intra,
            cv_pre_dia=_cv(m[m.is_pre][col]), cv_pos_dia=_cv(m[m.is_pos][col]),
            cv_pre_sem=_cv(m[m.dia == 1][col]), cv_pos_sem=_cv(m[m.dia == 7][col]),
            cv_semana=float(tcv.loc[k, "cv_semana"]), icc=float(tcv.loc[k, "icc"])))

    data = dict(
        n_resp=int(len(m)), n_atletas=int(m.ID.nunique()), n_dias=int(m.dia.nunique()),
        daily={c: [round(float(v), 2) for v in dg[c]] for c in
               ["vigor", "fadiga", "tensao", "depressao", "raiva", "confusao", "pth"]},
        daytype=list(dg["day_type"]),
        desc=[dict(var=k, lab=lab, media=round(float(desc.loc[cap, "media"]), 1),
                   dp=round(float(desc.loc[cap, "dp"]), 1),
                   minimo=int(desc.loc[cap, "minimo"]), maximo=int(desc.loc[cap, "maximo"]),
                   cv=round(100 * float(desc.loc[cap, "dp"]) / float(desc.loc[cap, "media"]), 0) if float(desc.loc[cap, "media"]) else 0)
              for k, lab, cap in [("vigor", "Vigor", "vigor"), ("fadiga", "Fadiga", "fadiga"),
                                  ("tensao", "Tensão", "tensao"), ("depressao", "Depressão", "depressao"),
                                  ("raiva", "Raiva", "raiva"), ("confusao", "Confusão", "confusao"),
                                  ("pth", "PTH", "pth")]],
        cv=cv_rows,
        icc=[dict(lab=lab, icc1=round(float(icc.loc[k, "icc1"]), 2), icck=round(float(icc.loc[k, "icck"]), 2),
                  label=icc.loc[k, "label"]) for k, lab in
             [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
              ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão")]],
        prepos=[dict(lab=lab, pre=round(float(pp.loc[k, "pre"]), 2), pos=round(float(pp.loc[k, "pos"]), 2),
                     pct=int(pp.loc[k, "pct"]), p=float(pp.loc[k, "p"]), dz=round(float(pp.loc[k, "dz"]), 2),
                     mag=_mag(pp.loc[k, "dz"])) for k, lab in
                [("vigor", "Vigor"), ("fadiga", "Fadiga"), ("tensao", "Tensão"),
                 ("depressao", "Depressão"), ("raiva", "Raiva"), ("confusao", "Confusão"), ("pth", "PTH")]],
        spearman=[dict(par=r.par, rho=round(float(r.rho), 2), p=float(r.p)) for r in sp.itertuples()],
        wcorr=[dict(par=r.par, rho=round(float(r.rho), 2), p=float(r.p)) for r in wc.itertuples()],
        prof_week=[dict(perfil=ACC.get(r.perfil, r.perfil), prev=round(float(r.prevalencia), 1), n=int(r.n)) for r in prof.itertuples()],
        acute=[dict(var=r.var, lab=r.lab, tipo=r.tipo, pre=float(r.pre), pos=float(r.pos),
                    dz=float(r.dz), p=float(r.p), sig=bool(r.sig)) for r in tri["an_tri_acute"].itertuples()],
        contrast=[dict(var=r.var, lab=r.lab, hiit=float(r.media_hiit), jogo=float(r.media_jogo),
                       dz=float(r.dz), p=float(r.p), mag=r.magnitude, fdr=float(r.fdr), sig_fdr=bool(r.sig_fdr))
                  for r in tri["an_tri_contrast"].itertuples()],
        prof_day={p_: [float(tri["an_tri_prof_day"][(tri["an_tri_prof_day"].dia == d) & (tri["an_tri_prof_day"].perfil == p_)]["pct"].iloc[0])
                       for d in range(1, 8)]
                  for p_ in ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão",
                             "Everest invertido", "Iceberg invertido"]},
        wb_daytype=[dict(medida=r.medida, outro=float(r.outro), hiit=float(r.hiit), jogo=float(r.jogo),
                         dz=float(r.dz_hiit_jogo), p=float(r.p), sig=bool(r.sig))
                    for r in tri["an_tri_wb_daytype"].itertuples()],
        wb_profile=[dict(medida=r.medida, favoravel=float(r.favoravel), neutro=float(r.neutro),
                         risco=float(r.risco), H=float(r.H), p=float(r.p), sig=bool(r.sig))
                    for r in tri["an_tri_wb_profile"].itertuples()],
    )
    return data


# ---------- figuras ----------
def _clean(ax):
    ax.grid(False)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.tick_params(length=4, width=1.1, colors="#333333")


def _inflex(y):
    """Índices de máximos/mínimos locais (inclui extremos)."""
    d = np.diff(y); idx = []
    for i in range(1, len(y) - 1):
        if (d[i - 1] > 0 and d[i] <= 0) or (d[i - 1] < 0 and d[i] >= 0):
            idx.append(i)
    return idx


def fig_traj(data):
    dias = list(range(1, 8)); dt = data["daytype"]
    series = [("vigor", "Vigor"), ("fadfisica", None), ("pth", "PTH"), ("fadiga", "Fadiga")]
    fig, ax = plt.subplots(figsize=(8.4, 4.6))
    # fadfisica não está em daily (é pré/pós agregado); usamos vigor/fadiga/pth/tensao do daily
    plot = [("vigor", "Vigor", CORES["Vigor"]), ("fadiga", "Fadiga", CORES["Fadiga"]),
            ("pth", "PTH", CORES["PTH"]), ("tensao", "Tensão", CORES["Tensao"])]
    for key, lab, col in plot:
        y = data["daily"][key]
        ax.plot(dias, y, "-", color=col, lw=3.4, solid_capstyle="round", label=lab, zorder=3)
        ax.plot(dias, y, "o", color=col, ms=6, zorder=4)
        for i in _inflex(y):
            ax.plot(dias[i], y[i], "o", ms=11, mfc="none", mec=col, mew=2.2, zorder=5)
            ax.annotate(f"{y[i]:.1f}".replace(".", ","), (dias[i], y[i]),
                        textcoords="offset points", xytext=(0, 11 if key in ("vigor",) else -15),
                        ha="center", fontsize=9, color=col, fontweight="bold")
    ax.set_xlim(0.7, 7.3); ax.set_ylim(0, 9)
    ax.xaxis.set_major_locator(MultipleLocator(1)); ax.yaxis.set_major_locator(MultipleLocator(1))
    ax.set_xticks(dias)
    ax.set_xticklabels([f"D{d}\n{t if t!='Baseline' else 'Base'}" for d, t in zip(dias, dt)], fontsize=9)
    ax.set_ylabel("Escore BRUMS (0–16)"); ax.set_xlabel("")
    _clean(ax)
    ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.10), fontsize=10)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_traj.png", dpi=150); plt.close(fig)


def fig_agudo(data):
    order = ["vigor", "fadiga", "fadfisica", "tensao", "depressao", "raiva", "confusao", "pth"]
    ac = {(r["var"], r["tipo"]): r for r in data["acute"]}
    labs = [LAB[k] for k in order]
    hi = [ac[(k, "HIIT")]["dz"] for k in order]; jo = [ac[(k, "Jogo")]["dz"] for k in order]
    x = np.arange(len(order)); w = 0.38
    fig, ax = plt.subplots(figsize=(8.4, 4.4))
    ax.axhline(0, color="#333333", lw=1.1)
    b1 = ax.bar(x - w / 2, hi, w, color=CORES["Fadiga"], label="HIIT")
    b2 = ax.bar(x + w / 2, jo, w, color=CORES["Tensao"], label="Jogo (amistoso)")
    for bars, vals in ((b1, hi), (b2, jo)):
        for rect, v in zip(bars, vals):
            ax.annotate(f"{v:+.2f}".replace(".", ","), (rect.get_x() + rect.get_width() / 2, v),
                        textcoords="offset points", xytext=(0, 3 if v >= 0 else -11),
                        ha="center", fontsize=7.5, color="#333333")
    ax.set_xticks(x); ax.set_xticklabels(labs, rotation=25, ha="right", fontsize=9)
    ax.set_ylabel("Tamanho de efeito agudo dz (pré→pós)")
    ax.set_ylim(min(min(hi), min(jo)) - 0.25, max(max(hi), max(jo)) + 0.3)
    ax.yaxis.set_major_locator(MultipleLocator(0.25))
    _clean(ax); ax.legend(frameon=False, fontsize=10, loc="upper left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_agudo.png", dpi=150); plt.close(fig)


def fig_contrast(data):
    rows = sorted(data["contrast"], key=lambda r: r["dz"])
    labs = [r["lab"] for r in rows]; dz = [r["dz"] for r in rows]
    cols = [(CORES["Raiva"] if r["sig_fdr"] else (CORES["Fadiga"] if r["p"] < .05 else "#9aa4b2")) for r in rows]
    y = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(8.4, 4.3))
    ax.axvline(0, color="#333333", lw=1.1)
    for yi, v, c in zip(y, dz, cols):
        ax.plot([0, v], [yi, yi], "-", color=c, lw=3.4, solid_capstyle="round", zorder=2)
        ax.plot(v, yi, "o", color=c, ms=9, zorder=3)
        ax.annotate(f"{v:+.2f}".replace(".", ","), (v, yi), textcoords="offset points",
                    xytext=(9 if v >= 0 else -9, 0), va="center", ha="left" if v >= 0 else "right",
                    fontsize=9, color="#333333", fontweight="bold")
    ax.set_yticks(y); ax.set_yticklabels(labs, fontsize=10)
    ax.set_xlabel("dz (média HIIT − média jogo) · positivo = maior no HIIT")
    ax.set_xlim(-0.2, 0.62); ax.xaxis.set_major_locator(MultipleLocator(0.1))
    _clean(ax)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_contrast.png", dpi=150); plt.close(fig)


def fig_perfis_dia(data):
    dias = list(range(1, 8)); dt = data["daytype"]
    sel = [("Barbatana de tubarão", CORES["Fadiga"], "Barbatana (sobrecarga)"),
           ("Submerso", CORES["Tensao"], "Submerso (recolhimento)"),
           ("Iceberg", CORES["Vigor"], "Iceberg (favorável)")]
    fig, ax = plt.subplots(figsize=(8.4, 4.5))
    for perfil, col, lab in sel:
        y = data["prof_day"][perfil]
        ax.plot(dias, y, "-", color=col, lw=3.4, solid_capstyle="round", label=lab, zorder=3)
        ax.plot(dias, y, "o", color=col, ms=6, zorder=4)
        for i in _inflex(y):
            ax.plot(dias[i], y[i], "o", ms=11, mfc="none", mec=col, mew=2.2, zorder=5)
    ax.set_xlim(0.7, 7.3); ax.set_ylim(0, max(max(data["prof_day"]["Iceberg"]), 42) + 2)
    ax.set_xticks(dias)
    ax.set_xticklabels([f"D{d}\n{t if t!='Baseline' else 'Base'}" for d, t in zip(dias, dt)], fontsize=9)
    ax.set_ylabel("Prevalência do perfil (%)")
    ax.yaxis.set_major_locator(MultipleLocator(10))
    _clean(ax); ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.10), fontsize=9.5)
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_perfis_dia.png", dpi=150); plt.close(fig)


def fig_sono_perfil(data):
    grp = ["favoravel", "neutro", "risco"]; glab = ["Favorável", "Neutro", "Risco"]
    ep = next(w for w in data["wb_profile"] if w["medida"] == "Epworth")
    ps = next(w for w in data["wb_profile"] if w["medida"] == "PSS")
    x = np.arange(3); w = 0.38
    fig, ax = plt.subplots(figsize=(7.4, 4.2))
    b1 = ax.bar(x - w / 2, [ep[g] for g in grp], w, color=CORES["Tensao"], label="Sonolência (Epworth)")
    b2 = ax.bar(x + w / 2, [ps[g] for g in grp], w, color=CORES["PTH"], label="Estresse (PSS)")
    for bars, m_ in ((b1, ep), (b2, ps)):
        for rect, g in zip(bars, grp):
            ax.annotate(f"{m_[g]:.1f}".replace(".", ","), (rect.get_x() + rect.get_width() / 2, m_[g]),
                        textcoords="offset points", xytext=(0, 3), ha="center", fontsize=9, color="#333333")
    ax.set_xticks(x); ax.set_xticklabels(glab, fontsize=11)
    ax.set_ylabel("Média"); ax.set_ylim(0, 26); ax.yaxis.set_major_locator(MultipleLocator(5))
    _clean(ax); ax.legend(frameon=False, fontsize=10, loc="upper left")
    fig.tight_layout(); fig.savefig(f"{OUT}/fig_sono_perfil.png", dpi=150); plt.close(fig)


if __name__ == "__main__":
    d = gather()
    with open(f"{OUT}/data.json", "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    fig_traj(d); fig_agudo(d); fig_contrast(d); fig_perfis_dia(d); fig_sono_perfil(d)
    print("OK ->", OUT)
    for k in ("n_resp", "n_atletas"):
        print(k, d[k])
