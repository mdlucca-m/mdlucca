#!/usr/bin/env python3
"""
render_explainer_video.py — video em SUPER SLOW MOTION que explica o que
acontece numa repeticao: fases (excentrica/transicao/concentrica/lockout),
eventos-chave (pico de forca, de velocidade, de aceleracao do joelho) e leituras
ao vivo (angulos, velocidade angular, forca, potencia).

Suaviza e INTERPOLA os frames (camera lenta fluida) e escreve com OpenCV.

Uso:
    python3 scripts/render_explainer_video.py --pose data/out/pose_XXXX.json \
        --session 16 --rep auto --interp 4 --out-fps 12 --out data/out/slow.mp4
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np
import cv2  # noqa: E402
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.signal import savgol_filter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TEAL, RED, YEL, BLU, PUR, ORG, GRY = ("#2a9d8f", "#e63946", "#e9c46a", "#4aa8ff",
                                      "#c77dff", "#f4a261", "#8b98a6")


def _sm(y, w=11):
    n = len(y)
    if n < 5:
        return y
    w = min(w if w % 2 else w + 1, n - (1 - n % 2))
    return savgol_filter(y, max(5, w), 3)


def _series(con, sub, name):
    r = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                    (sub, name)).fetchone()
    return np.array(json.loads(r[0]), float) if r else None


def _upsample(a, k):
    """Interpola linearmente k subframes entre amostras (camera lenta fluida)."""
    n = len(a)
    xs = np.arange(n)
    xd = np.linspace(0, n - 1, (n - 1) * k + 1)
    if a.ndim == 1:
        return np.interp(xd, xs, a)
    return np.stack([np.interp(xd, xs, a[:, j]) for j in range(a.shape[1])], 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pose", required=True)
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--rep", default="auto", help="'auto' (maior ROM) ou ordinal (1..)")
    ap.add_argument("--interp", type=int, default=4, help="subframes interpolados")
    ap.add_argument("--out-fps", type=float, default=12.0)
    ap.add_argument("--out", default="data/out/explicativo.mp4")
    ap.add_argument("--brand", default="De Lucca Esporte")
    args = ap.parse_args()

    con = sqlite3.connect(str(ROOT / "data" / "db.sqlite"))
    subs = con.execute("SELECT id,ordinal,label,frame_start,frame_end,n_frames "
                       "FROM submovement WHERE session_id=? ORDER BY ordinal",
                       (args.session,)).fetchall()
    full = max(subs, key=lambda r: r[5])
    reps = [s for s in subs if s[0] != full[0]]
    d = json.load(open(args.pose)); LI, norm = d["landmark_index"], d["norm"]
    src_fps = d["fps"]
    Pall = {k: np.array([[fr[i][0], fr[i][1]] for fr in norm], float)
            for k, i in LI.items()}
    hip_full = _sm(_series(con, full[0], "hip_angle"))

    # escolhe a rep (maior amplitude de angulo do quadril = mais limpa)
    if args.rep == "auto":
        rep = max(reps, key=lambda r: np.ptp(hip_full[r[3]:r[4]]))
    else:
        rep = next(r for r in reps if r[1] == int(args.rep))
    a, b = rep[3], rep[4]
    sl = slice(a, b + 1)

    # series (fatia da rep) + upsample
    def S(name):
        s = _series(con, full[0], name)
        return _sm(s[sl]) if s is not None else None
    hip, knee, ank = S("hip_angle"), S("knee_angle"), S("ankle_angle")
    hipw, kneew = S("hip_angvel"), S("knee_angvel")
    force, power = S("force"), S("power")
    t = _series(con, full[0], "t")[sl]; t = t - t[0]
    P = {k: v[sl] for k, v in Pall.items()}

    K = args.interp
    hip, knee, ank = _upsample(hip, K), _upsample(knee, K), _upsample(ank, K)
    hipw = _upsample(hipw, K) if hipw is not None else None
    kneew = _upsample(kneew, K) if kneew is not None else None
    force = _upsample(force, K) if force is not None else None
    power = _upsample(power, K) if power is not None else None
    t = _upsample(t, K)
    P = {k: _upsample(v, K) for k, v in P.items()}
    M = len(t)

    # fases a partir da velocidade do angulo do quadril (extensao=subida)
    dhip = np.gradient(_sm(hip, 21), t)
    thr = 0.06 * np.max(np.abs(dhip))
    phase = np.where(dhip > thr, "SUBIDA (concêntrica)",
                     np.where(dhip < -thr, "DESCIDA (excêntrica)", "TRANSIÇÃO"))
    lockf = int(np.argmax(hip))
    if hip[lockf] > 155:
        lo = max(0, lockf - int(0.12 * M))
        for i in range(lo, min(M, lockf + int(0.12 * M))):
            phase[i] = "LOCKOUT (~180°)"
    EXPL = {
        "DESCIDA (excêntrica)": "Descida controlada: quadril e joelho flexionam, "
        "músculos alongam sob tensão (freio). Potência negativa.",
        "TRANSIÇÃO": "Ponto baixo / inversão: velocidade passa por zero — o "
        "sistema muda de freio para propulsão.",
        "SUBIDA (concêntrica)": "Tração: extensão de quadril e joelho. Força, "
        "velocidade e potência crescem — motor do movimento.",
        "LOCKOUT (~180°)": "Extensão completa: quadril e joelho próximos de 180°. "
        "Fim da fase concêntrica.",
    }
    # eventos-chave (indices no espaco upsampled)
    events = {}
    if force is not None:
        events[int(np.argmax(force))] = ("PICO DE FORÇA", RED)
    if power is not None:
        events[int(np.argmax(power))] = ("PICO DE POTÊNCIA", TEAL)
    spd = _series(con, full[0], "speed")
    if spd is not None:
        sp = _upsample(_sm(spd[sl]), K); events[int(np.argmax(sp))] = ("PICO DE VELOCIDADE", YEL)
    if kneew is not None:
        acc = np.abs(np.gradient(kneew, t)); events[int(np.argmax(acc))] = ("JOELHO: pico de aceleração", BLU)

    slow = (args.out_fps) / (src_fps * K)
    plt.rcParams.update({"figure.facecolor": "#0e1116", "axes.facecolor": "#0e1116",
                         "text.color": "#e6edf3", "axes.edgecolor": "#39424d",
                         "axes.labelcolor": "#e6edf3", "xtick.color": GRY, "ytick.color": GRY})
    fig = plt.figure(figsize=(12, 7), dpi=110)
    gs = fig.add_gridspec(3, 2, width_ratios=[1, 1.15], height_ratios=[1, 1, 0.9])
    axSk = fig.add_subplot(gs[:, 0])
    axAng = fig.add_subplot(gs[0, 1]); axVel = fig.add_subplot(gs[1, 1]); axFP = fig.add_subplot(gs[2, 1])
    fig.suptitle(f"{args.brand} — {rep[2]} em super slow ({1/slow:.0f}× mais lento) · o que acontece",
                 color=TEAL, fontweight="bold", fontsize=12)

    BONES = [("ear_l", "sh_l"), ("sh_l", "hip_l"), ("hip_l", "kn_l"), ("kn_l", "an_l"),
             ("an_l", "foot_l"), ("sh_l", "sh_r"), ("hip_l", "hip_r"),
             ("hip_r", "kn_r"), ("kn_r", "an_r"), ("an_r", "foot_r")]
    segc = {("sh_l", "hip_l"): PUR, ("hip_l", "kn_l"): TEAL, ("kn_l", "an_l"): ORG,
            ("an_l", "foot_l"): RED}
    axSk.set_xlim(0.05, 0.95); axSk.set_ylim(1, 0); axSk.axis("off")
    blines = {}
    for u, v in BONES:
        (ln,) = axSk.plot([], [], color=segc.get((u, v), GRY),
                          lw=6 if (u, v) in segc else 3, solid_capstyle="round")
        blines[(u, v)] = ln
    jpts, = axSk.plot([], [], "o", color="#e6edf3", ms=6)
    cap = axSk.text(0.5, 0.97, "", transform=axSk.transAxes, ha="center", va="bottom",
                    color="#0e1116", fontsize=12, fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.4", fc=TEAL, ec="none"))
    expl = axSk.text(0.5, 0.03, "", transform=axSk.transAxes, ha="center", va="top",
                     color="#e6edf3", fontsize=10, wrap=True)
    evt = axSk.text(0.5, 0.5, "", transform=axSk.transAxes, ha="center", va="center",
                    color="#fff", fontsize=15, fontweight="bold", alpha=0.0)

    def prep(ax, ymin, ymax, ylabel):
        ax.set_xlim(0, t[-1]); ax.set_ylim(ymin, ymax); ax.axhline(0, color="#39424d", lw=.6)
        ax.set_ylabel(ylabel, fontsize=9); ax.grid(color="#20262e")
        ax.tick_params(labelsize=8)
    prep(axAng, min(np.min(hip), np.min(knee)) - 5, 190, "ângulo (°)")
    prep(axVel, -max(np.max(np.abs(hipw)), np.max(np.abs(kneew))) * 1.1 if hipw is not None else -1,
         max(np.max(np.abs(hipw)), np.max(np.abs(kneew))) * 1.1 if hipw is not None else 1, "vel.ang (°/s)")
    fp_max = max(np.max(np.abs(force)) if force is not None else 1,
                 np.max(np.abs(power)) if power is not None else 1)
    prep(axFP, -fp_max * 1.1, fp_max * 1.1, "F(N) / P(W)"); axFP.set_xlabel("tempo real (s)", fontsize=9)
    axAng.axhline(180, color=RED, ls=":", lw=.8, alpha=.6)
    la_hip, = axAng.plot([], [], color=TEAL, lw=2, label="quadril")
    la_kn, = axAng.plot([], [], color=YEL, lw=2, label="joelho")
    la_an, = axAng.plot([], [], color=BLU, lw=1.5, label="tornozelo")
    axAng.legend(loc="lower right", fontsize=7, facecolor="#171b22", edgecolor="#39424d")
    lv_hip, = axVel.plot([], [], color=TEAL, lw=2, label="quadril")
    lv_kn, = axVel.plot([], [], color=YEL, lw=2, label="joelho")
    axVel.legend(loc="upper right", fontsize=7, facecolor="#171b22", edgecolor="#39424d")
    lf, = axFP.plot([], [], color=ORG, lw=2, label="força")
    lp, = axFP.plot([], [], color=TEAL, lw=2, label="potência")
    axFP.legend(loc="upper right", fontsize=7, facecolor="#171b22", edgecolor="#39424d")
    cursors = [ax.axvline(0, color="#e6edf3", lw=.7, alpha=.4) for ax in (axAng, axVel, axFP)]

    fig.canvas.draw()
    w0, h0 = fig.canvas.get_width_height(); w0 -= w0 % 2; h0 -= h0 % 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.out_fps, (w0, h0))
    ev_keys = sorted(events)
    for f in range(M):
        for (u, v), ln in blines.items():
            ln.set_data([P[u][f, 0], P[v][f, 0]], [P[u][f, 1], P[v][f, 1]])
        pts = ["hip_l", "kn_l", "an_l", "sh_l", "foot_l"]
        jpts.set_data([P[p][f, 0] for p in pts], [P[p][f, 1] for p in pts])
        cap.set_text(f"  {phase[f]}  ")
        cap.get_bbox_patch().set_facecolor(
            {"DESCIDA (excêntrica)": RED, "SUBIDA (concêntrica)": TEAL,
             "LOCKOUT (~180°)": YEL, "TRANSIÇÃO": GRY}.get(phase[f], TEAL))
        expl.set_text(EXPL.get(phase[f], ""))
        # evento-chave: aparece se estamos a <=3 subframes de um evento
        near = [(k, events[k]) for k in ev_keys if abs(k - f) <= max(2, K // 2)]
        if near:
            lab, col = near[0][1]; evt.set_text("◈ " + lab); evt.set_color(col); evt.set_alpha(0.95)
        else:
            evt.set_alpha(0.0)
        la_hip.set_data(t[:f + 1], hip[:f + 1]); la_kn.set_data(t[:f + 1], knee[:f + 1])
        la_an.set_data(t[:f + 1], ank[:f + 1])
        if hipw is not None:
            lv_hip.set_data(t[:f + 1], hipw[:f + 1]); lv_kn.set_data(t[:f + 1], kneew[:f + 1])
        if force is not None:
            lf.set_data(t[:f + 1], force[:f + 1]); lp.set_data(t[:f + 1], power[:f + 1])
        for c in cursors:
            c.set_xdata([t[f], t[f]])
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), np.uint8).reshape(
            fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 4)
        vw.write(cv2.cvtColor(buf[:h0, :w0, :3], cv2.COLOR_RGB2BGR))
    vw.release(); plt.close(fig)
    print(f"[ok] {args.out}  rep={rep[2]}  {M} frames @ {args.out_fps} fps "
          f"({1/slow:.1f}x mais lento)  {w0}x{h0}")


if __name__ == "__main__":
    main()
