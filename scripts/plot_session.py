#!/usr/bin/env python3
"""
plot_session.py — gera TODAS as figuras analiticas de uma sessao de video e um
metrics.json com picos e indice de fadiga. Reproduz o que foi feito na analise
do deadlift para qualquer sessao.

Figuras (PNG, tema De Lucca Esporte):
  1. forca_potencia  — series temporais: forca (total/dinamica/gravitacional),
     potencia (fase +/-), velocidade, angulos, RFD; com RAW vs FILTRADO.
  2. analitica       — F-v, potencia x angulo do quadril, picos e trabalho/rep.
  3. momentos        — torque articular (quadril/joelho/tornozelo) por dinamica
     inversa quase-estatica (De Leva) + diagrama de aplicacao de forcas.
  4. fadiga          — comparacao entre reps: pico de potencia/velocidade,
     concentrico vs excentrico (pico de queda), curvas normalizadas e
     indice de fadiga (velocity loss, power drop, FI).

Filtros: Butterworth 6 Hz zero-fase (Winter 2009) + Savitzky-Golay.

Uso:
    python3 scripts/plot_session.py --session 16 \
        --pose data/out/pose_9e62186f-202.json --mass 87 --load 90 \
        --out data/out/analise_16
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.signal import savgol_filter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
from app import signals as Sig  # noqa: E402

TEAL, RED, YEL, BLU, PUR, GRY = "#2a9d8f", "#e63946", "#e9c46a", "#4aa8ff", "#c77dff", "#8b98a6"
_STYLE = {"figure.facecolor": "#0e1116", "axes.facecolor": "#0e1116",
          "axes.edgecolor": "#39424d", "axes.labelcolor": "#e6edf3", "text.color": "#e6edf3",
          "xtick.color": GRY, "ytick.color": GRY, "axes.grid": True,
          "grid.color": "#20262e", "font.size": 10}
DE_LEVA = [  # (nome, m_frac[*2 bilaterais], prox, dist, com_ratio)
    ("head", 0.0694, "ear_l", "ear_l", 0.0), ("trunk", 0.4346, "sh_l", "hip_l", 0.44),
    ("uarm", 0.0542, "sh_l", "el_l", 0.5772), ("farm", 0.0324, "el_l", "wr_l", 0.4574),
    ("hand", 0.0122, "wr_l", "wr_l", 0.0), ("thigh", 0.2832, "hip_l", "kn_l", 0.4095),
    ("shank", 0.0866, "kn_l", "an_l", 0.4459), ("foot", 0.0274, "an_l", "foot_l", 0.4415)]
ABOVE = {"hip": ["head", "trunk", "uarm", "farm", "hand", "load"],
         "knee": ["head", "trunk", "uarm", "farm", "hand", "load", "thigh"],
         "ankle": ["head", "trunk", "uarm", "farm", "hand", "load", "thigh", "shank"]}
JOINT = {"hip": "hip_l", "knee": "kn_l", "ankle": "an_l"}


def _con():
    return sqlite3.connect(str(ROOT / "data" / "db.sqlite"))


def _series(con, sub, name):
    r = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                    (sub, name)).fetchone()
    return np.array(json.loads(r[0]), float) if r else None


def _smooth(y, win=None):
    n = len(y)
    w = win or min(31, n if n % 2 else n - 1)
    w = max(7, w - (1 - w % 2))
    return savgol_filter(y, min(w, n - (1 - n % 2)), 3) if n > 7 else y


def _reps_and_full(con, session):
    subs = con.execute("SELECT id,ordinal,label,frame_start,frame_end,n_frames "
                        "FROM submovement WHERE session_id=? ORDER BY ordinal",
                        (session,)).fetchall()
    full = max(subs, key=lambda r: r[5])            # o de maior n_frames = sessao completa
    reps = [s for s in subs if s[0] != full[0]]
    return reps, full


def fatigue_metrics(con, reps):
    """Picos por rep + indices de fadiga (velocity loss, power drop, FI)."""
    rows = []
    for sid, ordv, lab, fs, fe, nfr in reps:
        P = _series(con, sid, "power"); v = _series(con, sid, "speed")
        t = _series(con, sid, "t")
        if P is None or v is None:
            continue
        P, v = _smooth(P), _smooth(v)
        dt = np.gradient(t) if t is not None else np.full_like(P, 1 / 30)
        rows.append({
            "rep": lab, "P_peak_W": float(np.max(P)),
            "P_peak_ecc_W": float(np.min(P)),          # pico de queda (descida)
            "v_peak_ms": float(np.max(v)),
            "work_pos_J": float(np.sum(np.clip(P, 0, None) * dt))})
    if not rows:
        return {"reps": [], "fadiga": {}}
    Pp = [r["P_peak_W"] for r in rows]; Vp = [r["v_peak_ms"] for r in rows]
    fi = lambda a: 100.0 * (max(a) - min(a)) / max(a) if max(a) else 0.0
    fad = {
        "velocity_loss_pct": round(100.0 * (Vp[0] - Vp[-1]) / Vp[0], 1) if Vp[0] else None,
        "power_drop_pct": round(100.0 * (Pp[0] - Pp[-1]) / Pp[0], 1) if Pp[0] else None,
        "fatigue_index_power_pct": round(fi(Pp), 1),
        "fatigue_index_velocity_pct": round(fi(Vp), 1),
        "nota": "VL/queda = 1a vs ultima rep; FI = (max-min)/max. Rep 1 pode "
                "incluir setup (VL superestimado).",
    }
    return {"reps": rows, "fadiga": fad}


# ---------- Figuras ----------
def fig_forca_potencia(con, full, reps, fs, out, title):
    t = _series(con, full[0], "t")
    F = _series(con, full[0], "force")
    Fg = _series(con, full[0], "force_gravity"); P = _series(con, full[0], "power")
    v = _series(con, full[0], "speed"); hip = _series(con, full[0], "hip_angle")
    knee = _series(con, full[0], "knee_angle"); ank = _series(con, full[0], "ankle_angle")
    rfd = _series(con, full[0], "rfd")
    tr = [(t[r[3]], t[min(r[4], len(t) - 1)], r[2]) for r in reps]
    plt.rcParams.update(_STYLE)
    fig, ax = plt.subplots(5, 1, figsize=(11, 13), sharex=True)
    fig.suptitle(title + "  ·  força-potência (raw vs filtrado)", color=TEAL,
                 fontweight="bold", fontsize=13, y=0.997)

    def shade(a):
        for s, e, lab in tr:
            a.axvspan(s, e, color="#fff", alpha=0.03)
    Ff = Sig.butter_lowpass(F, fs, cutoff=6.0)
    ax[0].plot(t, F, color=GRY, lw=0.6, alpha=.5, label="força bruta")
    ax[0].plot(t, Ff, color=TEAL, lw=1.6, label="força filtrada (Butterworth 6 Hz)")
    if Fg is not None:
        ax[0].plot(t, Fg, color=GRY, lw=1.0, ls="--", alpha=.7, label="componente m·g")
    k = int(np.argmax(Ff)); ax[0].plot(t[k], Ff[k], "o", color=RED)
    ax[0].annotate(f"pico {Ff[k]:.0f} N", (t[k], Ff[k]), color=RED, fontsize=9,
                   xytext=(6, 6), textcoords="offset points")
    ax[0].set_ylabel("Força (N)"); ax[0].legend(loc="upper right", fontsize=8,
                                                 facecolor="#171b22", edgecolor="#39424d")
    ax[1].axhline(0, color="#39424d", lw=.8)
    ax[1].fill_between(t, P, 0, where=(P >= 0), color=TEAL, alpha=.35)
    ax[1].fill_between(t, P, 0, where=(P < 0), color=RED, alpha=.30)
    ax[1].plot(t, P, color=TEAL, lw=1.2)
    k = int(np.argmax(P)); ax[1].annotate(f"pico {P[k]:.0f} W", (t[k], P[k]), color=RED,
                                          fontsize=9, xytext=(6, 6), textcoords="offset points")
    ax[1].plot(t[k], P[k], "o", color=RED); ax[1].set_ylabel("Potência (W)")
    ax[2].plot(t, v, color=BLU, lw=1.3); k = int(np.argmax(v))
    ax[2].plot(t[k], v[k], "o", color=RED)
    ax[2].annotate(f"PPV {v[k]:.2f} m/s", (t[k], v[k]), color=RED, fontsize=9,
                   xytext=(6, 6), textcoords="offset points"); ax[2].set_ylabel("Vel. (m/s)")
    ax[3].plot(t, hip, color=TEAL, lw=1.2, label="quadril")
    ax[3].plot(t, knee, color=YEL, lw=1.2, label="joelho")
    if ank is not None:
        ax[3].plot(t, ank, color=BLU, lw=1.0, alpha=.8, label="tornozelo")
    ax[3].axhline(180, color=RED, lw=.8, ls=":", alpha=.7)
    ax[3].set_ylabel("Ângulo (°)"); ax[3].legend(loc="lower right", fontsize=8,
                                                  facecolor="#171b22", edgecolor="#39424d")
    if rfd is not None:
        ax[4].plot(t, rfd, color=PUR, lw=1.0); ax[4].axhline(0, color="#39424d", lw=.8)
    ax[4].set_ylabel("RFD (N/s)"); ax[4].set_xlabel("tempo (s)")
    for a in ax:
        shade(a)
    fig.tight_layout(rect=[0, 0, 1, 0.987])
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor()); plt.close(fig)


def fig_fadiga(con, reps, out, title):
    data = fatigue_metrics(con, reps)
    rows, fad = data["reps"], data["fadiga"]
    labels = [r["rep"] for r in rows]
    Pp = [r["P_peak_W"] for r in rows]; Pe = [-r["P_peak_ecc_W"] for r in rows]
    Vp = [r["v_peak_ms"] for r in rows]
    x = np.arange(len(rows))
    plt.rcParams.update(_STYLE)
    fig, ax = plt.subplots(2, 2, figsize=(12, 9))
    fig.suptitle(title + "  ·  comparação entre repetições e índice de fadiga",
                 color=TEAL, fontweight="bold", fontsize=13)
    # A picos por rep + tendencia
    a = ax[0, 0]; w = 0.38
    a.bar(x - w / 2, Pp, w, color=TEAL, label="Potência pico (W)")
    a2 = a.twinx(); a2.plot(x, Vp, "-o", color=YEL, label="Vel. pico (m/s)")
    a2.grid(False); a.set_xticks(x); a.set_xticklabels(labels)
    a.set_ylabel("Potência pico (W)", color=TEAL); a2.set_ylabel("Vel. pico (m/s)", color=YEL)
    a.set_title("Pico de potência e velocidade por rep", color="#e6edf3", fontsize=11)
    # B concentrico vs excentrico (pico de queda)
    b = ax[0, 1]
    b.bar(x - w / 2, Pp, w, color=TEAL, label="subida (concêntrico)")
    b.bar(x + w / 2, Pe, w, color=RED, label="descida (pico de queda)")
    b.set_xticks(x); b.set_xticklabels(labels); b.set_ylabel("Potência pico (W)")
    b.legend(fontsize=8, facecolor="#171b22", edgecolor="#39424d")
    b.set_title("Concêntrico × excêntrico (pico de queda)", color="#e6edf3", fontsize=11)
    # C curvas de potencia normalizadas
    c = ax[1, 0]
    for i, (sid, ordv, lab, fsr, fe, nfr) in enumerate(reps):
        P = _series(con, sid, "power")
        if P is None:
            continue
        P = _smooth(P); xs = np.linspace(0, 100, len(P))
        c.plot(xs, P, lw=1.4, label=lab)
    c.axhline(0, color="#39424d", lw=.8); c.set_xlabel("% da repetição")
    c.set_ylabel("Potência (W)"); c.legend(fontsize=8, facecolor="#171b22", edgecolor="#39424d")
    c.set_title("Curvas de potência normalizadas (forma)", color="#e6edf3", fontsize=11)
    # D indices de fadiga
    d = ax[1, 1]
    keys = [("velocity_loss_pct", "Perda de\nvelocidade"), ("power_drop_pct", "Queda de\npotência"),
            ("fatigue_index_power_pct", "Índice fadiga\n(potência)"),
            ("fatigue_index_velocity_pct", "Índice fadiga\n(velocidade)")]
    vals = [fad.get(k, 0) or 0 for k, _ in keys]
    cols = [YEL, RED, TEAL, BLU]
    d.bar(range(len(keys)), vals, color=cols)
    d.set_xticks(range(len(keys))); d.set_xticklabels([lb for _, lb in keys], fontsize=9)
    d.set_ylabel("%"); d.set_title("Índice de fadiga", color="#e6edf3", fontsize=11)
    for i, vv in enumerate(vals):
        d.text(i, vv, f"{vv:.1f}%", ha="center", va="bottom", fontsize=9)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor()); plt.close(fig)
    return data


def fig_momentos(pose_path, reps, mass, load, mpp, out, title):
    d = json.load(open(pose_path)); LI = d["landmark_index"]; norm = d["norm"]
    W, H, fps = d["width"], d["height"], d["fps"]
    N = len(norm); t = np.arange(N) / fps
    P = {k: np.array([[fr[i][0] * W * mpp, fr[i][1] * H * mpp] for fr in norm], float)
         for k, i in LI.items()}
    COM, MASS = {}, {}
    for n, fr, pr, ds, r in DE_LEVA:
        COM[n] = P[pr] + r * (P[ds] - P[pr]); MASS[n] = fr * mass
    COM["load"] = P["wr_l"]; MASS["load"] = load

    def moment(j):
        xj = P[JOINT[j]][:, 0]; M = np.zeros(N)
        for s in ABOVE[j]:
            M += MASS[s] * 9.81 * (COM[s][:, 0] - xj)
        return np.abs(_smooth(M))
    Mh, Mk, Ma = moment("hip"), moment("knee"), moment("ankle")
    tr = [(t[r[3]], t[min(r[4], N - 1)], r[2]) for r in reps]
    plt.rcParams.update(_STYLE)
    fig = plt.figure(figsize=(12, 9))
    fig.suptitle(title + "  ·  momentos articulares (torque) e aplicação de forças",
                 color=TEAL, fontweight="bold", fontsize=12.5)
    gs = fig.add_gridspec(2, 2)
    axA = fig.add_subplot(gs[0, :]); axC = fig.add_subplot(gs[1, 0]); axD = fig.add_subplot(gs[1, 1])
    for s, e, lab in tr:
        axA.axvspan(s, e, color="#fff", alpha=0.03)
    axA.plot(t, Mh, color=TEAL, lw=1.6, label="quadril")
    axA.plot(t, Mk, color=YEL, lw=1.3, label="joelho")
    axA.plot(t, Ma, color=BLU, lw=1.1, label="tornozelo")
    k = int(np.argmax(Mh)); axA.plot(t[k], Mh[k], "o", color=RED)
    axA.annotate(f"quadril pico {Mh[k]:.0f} N·m", (t[k], Mh[k]), color=RED, fontsize=9,
                 xytext=(6, 6), textcoords="offset points")
    axA.set_ylabel("Momento (N·m)"); axA.set_xlabel("tempo (s)")
    axA.legend(loc="upper right", fontsize=9, facecolor="#171b22", edgecolor="#39424d")
    axA.set_title("Momento (torque) articular ao longo do tempo", color="#e6edf3", fontsize=11)
    x = np.arange(len(reps)); w = 0.26
    pk = lambda M: [np.nanmax(M[r[3]:r[4]]) for r in reps]
    axC.bar(x - w, pk(Mh), w, color=TEAL, label="quadril")
    axC.bar(x, pk(Mk), w, color=YEL, label="joelho")
    axC.bar(x + w, pk(Ma), w, color=BLU, label="tornozelo")
    axC.set_xticks(x); axC.set_xticklabels([r[2] for r in reps]); axC.set_ylabel("Momento pico (N·m)")
    axC.legend(fontsize=8, facecolor="#171b22", edgecolor="#39424d")
    axC.set_title("Momento pico por repetição", color="#e6edf3", fontsize=11)
    f0 = k
    for aa, bb in [("sh_l", "hip_l"), ("hip_l", "kn_l"), ("kn_l", "an_l"),
                   ("an_l", "foot_l"), ("sh_l", "el_l"), ("el_l", "wr_l"), ("ear_l", "sh_l")]:
        axD.plot([P[aa][f0, 0], P[bb][f0, 0]], [P[aa][f0, 1], P[bb][f0, 1]], color=GRY, lw=2)
    wr, hip = P["wr_l"][f0], P["hip_l"][f0]
    axD.annotate("", xy=(wr[0], wr[1] + 0.25), xytext=(wr[0], wr[1]),
                 arrowprops=dict(arrowstyle="-|>", color=RED, lw=2))
    axD.text(wr[0] + 0.02, wr[1] + 0.13, f"peso {load:.0f} kg", color=RED, fontsize=8)
    axD.plot([hip[0], wr[0]], [hip[1], hip[1]], color=YEL, ls="--", lw=1.5)
    axD.text((hip[0] + wr[0]) / 2, hip[1] - 0.04, f"braço {abs(wr[0]-hip[0])*100:.0f} cm",
             color=YEL, fontsize=8, ha="center")
    axD.plot(hip[0], hip[1], "o", color=RED, ms=7)
    axD.invert_yaxis(); axD.set_aspect("equal"); axD.grid(False)
    axD.set_xlabel("horizontal (m)"); axD.set_ylabel("vertical (m)")
    axD.set_title(f"Aplicação de força (t={t[f0]:.1f}s)", color="#e6edf3", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.955])
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor()); plt.close(fig)
    return {"hip_peak_Nm": float(Mh.max()), "knee_peak_Nm": float(Mk.max()),
            "ankle_peak_Nm": float(Ma.max())}


def main():
    ap = argparse.ArgumentParser(description="Gera todas as figuras analiticas de uma sessao.")
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--pose", default=None, help="pose json (p/ momentos)")
    ap.add_argument("--mass", type=float, default=80.0)
    ap.add_argument("--load", type=float, default=0.0)
    ap.add_argument("--mpp", type=float, default=0.003722, help="metros por pixel")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    con = _con()
    ses = con.execute("SELECT exercise FROM session WHERE id=?", (args.session,)).fetchone()
    title = f"De Lucca Esporte — {ses[0] if ses else 'Sessão'} (#{args.session})"
    reps, full = _reps_and_full(con, args.session)
    t = _series(con, full[0], "t")
    fs = 1.0 / float(np.median(np.gradient(t))) if t is not None else 30.0
    out = Path(args.out or (ROOT / "data" / "out" / f"analise_{args.session}"))
    out.mkdir(parents=True, exist_ok=True)

    fig_forca_potencia(con, full, reps, fs, out / "forca_potencia.png", title)
    fatiga = fig_fadiga(con, reps, out / "fadiga.png", title)
    momentos = None
    if args.pose and Path(args.pose).exists():
        momentos = fig_momentos(args.pose, reps, args.mass, args.load, args.mpp,
                                out / "momentos.png", title)
    metrics = {"session": args.session, "exercise": ses[0] if ses else None,
               "fs_hz": round(fs, 2), "picos_por_rep": fatiga["reps"],
               "fadiga": fatiga["fadiga"], "momentos_pico": momentos}
    (out / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2))
    con.close()
    print(f"[ok] figuras + metrics.json em {out}")
    print(json.dumps(metrics["fadiga"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
