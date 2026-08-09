#!/usr/bin/env python3
"""
render_realtime_video.py — video REAL (boneco/esqueleto sobre a filmagem) +
graficos plotando EM TEMPO REAL e gerando os resultados (picos acumulados),
para TODAS as repeticoes, em camera lenta.

Esquerda: frames do video com o esqueleto (overlay). Direita: angulos, vel.
angular e forca/potencia desenhando ao vivo, com sombreamento das repeticoes e
um placar de resultados (picos ate o momento + repeticao atual).

Uso:
    python3 scripts/render_realtime_video.py --overlay data/out/overlay_XXXX.mp4 \
        --session 16 --out-fps 12 --out data/out/realtime_slow.mp4
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
TEAL, RED, YEL, BLU, ORG, GRY = "#2a9d8f", "#e63946", "#e9c46a", "#4aa8ff", "#f4a261", "#8b98a6"


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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--overlay", required=True, help="video com o esqueleto (overlay)")
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--out", default="data/out/realtime_slow.mp4")
    ap.add_argument("--out-fps", type=float, default=12.0)
    ap.add_argument("--height", type=int, default=720)
    ap.add_argument("--brand", default="De Lucca Esporte")
    args = ap.parse_args()

    con = sqlite3.connect(str(ROOT / "data" / "db.sqlite"))
    subs = con.execute("SELECT id,ordinal,label,frame_start,frame_end,n_frames "
                       "FROM submovement WHERE session_id=? ORDER BY ordinal",
                       (args.session,)).fetchall()
    full = max(subs, key=lambda r: r[5])
    reps = [s for s in subs if s[0] != full[0]]
    t = _series(con, full[0], "t")
    hip = _sm(_series(con, full[0], "hip_angle")); knee = _sm(_series(con, full[0], "knee_angle"))
    ank = _sm(_series(con, full[0], "ankle_angle"))
    hipw = _sm(_series(con, full[0], "hip_angvel")); kneew = _sm(_series(con, full[0], "knee_angvel"))
    force = _sm(_series(con, full[0], "force")); power = _sm(_series(con, full[0], "power"))
    speed = _sm(_series(con, full[0], "speed"))
    N = len(t)
    rep_of = np.zeros(N, int)
    for i, r in enumerate(reps, 1):
        rep_of[r[3]:r[4] + 1] = i
    cmaxF = np.maximum.accumulate(np.abs(force))
    cmaxP = np.maximum.accumulate(np.clip(power, 0, None))
    cmaxV = np.maximum.accumulate(np.abs(speed))

    cap = cv2.VideoCapture(args.overlay)
    Nv = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    Hc = args.height - args.height % 2

    # figura dos graficos (lado direito), tamanho em pixels ~ (Wg, Hc)
    plt.rcParams.update({"figure.facecolor": "#0e1116", "axes.facecolor": "#0e1116",
                         "text.color": "#e6edf3", "axes.edgecolor": "#39424d",
                         "axes.labelcolor": "#e6edf3", "xtick.color": GRY, "ytick.color": GRY})
    dpi = 100
    fig = plt.figure(figsize=(8.8, Hc / dpi), dpi=dpi)
    gs = fig.add_gridspec(3, 1, hspace=0.32, left=0.11, right=0.985, top=0.95, bottom=0.08)
    axA, axV, axF = (fig.add_subplot(gs[i]) for i in range(3))
    tr = [(t[r[3]], t[min(r[4], N - 1)], r[2]) for r in reps]

    def prep(ax, ymin, ymax, ylabel):
        ax.set_xlim(0, t[-1]); ax.set_ylim(ymin, ymax); ax.grid(color="#20262e")
        ax.set_ylabel(ylabel, fontsize=9); ax.tick_params(labelsize=8)
        ax.axhline(0, color="#39424d", lw=.6)
        for s, e, _ in tr:
            ax.axvspan(s, e, color="#fff", alpha=0.03)
    prep(axA, min(hip.min(), knee.min()) - 5, 190, "ângulo (°)")
    axA.axhline(180, color=RED, ls=":", lw=.8, alpha=.6)
    prep(axV, -max(np.abs(hipw).max(), np.abs(kneew).max()) * 1.1,
         max(np.abs(hipw).max(), np.abs(kneew).max()) * 1.1, "vel.ang (°/s)")
    fpm = max(np.abs(force).max(), np.abs(power).max()) * 1.1
    prep(axF, -fpm, fpm, "F(N)/P(W)"); axF.set_xlabel("tempo (s)", fontsize=9)
    lah, = axA.plot([], [], color=TEAL, lw=1.8, label="quadril")
    lak, = axA.plot([], [], color=YEL, lw=1.8, label="joelho")
    laa, = axA.plot([], [], color=BLU, lw=1.4, label="tornozelo")
    axA.legend(loc="lower right", fontsize=7, ncol=3, facecolor="#171b22", edgecolor="#39424d")
    lvh, = axV.plot([], [], color=TEAL, lw=1.8, label="quadril")
    lvk, = axV.plot([], [], color=YEL, lw=1.8, label="joelho")
    axV.legend(loc="upper right", fontsize=7, ncol=2, facecolor="#171b22", edgecolor="#39424d")
    lf, = axF.plot([], [], color=ORG, lw=1.8, label="força")
    lp, = axF.plot([], [], color=TEAL, lw=1.8, label="potência")
    axF.legend(loc="upper right", fontsize=7, ncol=2, facecolor="#171b22", edgecolor="#39424d")
    curs = [ax.axvline(0, color="#e6edf3", lw=.7, alpha=.4) for ax in (axA, axV, axF)]
    fig.suptitle(f"{args.brand} — resultados em tempo real", color=TEAL,
                 fontweight="bold", fontsize=12)
    fig.canvas.draw()
    Wg = fig.canvas.get_width_height()[0]

    vw_w = int(Hc * 1080 / 1920)                 # painel do video (retrato)
    W = (vw_w + Wg); W -= W % 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.out_fps, (W, Hc))

    for f in range(N):
        vf = int(round(f * (Nv - 1) / (N - 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, vf)
        ok, frame = cap.read()
        if not ok:
            continue
        vpanel = cv2.resize(frame, (vw_w, Hc))
        # placar de resultados (gerando os resultados ao vivo)
        r = rep_of[f]
        lines = [f"Rep {r}/{len(reps)}" if r else "setup",
                 f"F pico:  {cmaxF[f]:6.0f} N",
                 f"P pico:  {cmaxP[f]:6.0f} W",
                 f"V pico:  {cmaxV[f]:5.2f} m/s"]
        y0 = 26
        cv2.rectangle(vpanel, (8, 8), (vw_w - 8, y0 + 4 + 24 * len(lines)), (14, 17, 22), -1)
        for i, ln in enumerate(lines):
            cv2.putText(vpanel, ln, (16, y0 + 22 * i + 8), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (230, 237, 243), 1, cv2.LINE_AA)
        # graficos ao vivo
        lah.set_data(t[:f + 1], hip[:f + 1]); lak.set_data(t[:f + 1], knee[:f + 1])
        laa.set_data(t[:f + 1], ank[:f + 1])
        lvh.set_data(t[:f + 1], hipw[:f + 1]); lvk.set_data(t[:f + 1], kneew[:f + 1])
        lf.set_data(t[:f + 1], force[:f + 1]); lp.set_data(t[:f + 1], power[:f + 1])
        for c in curs:
            c.set_xdata([t[f], t[f]])
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), np.uint8).reshape(
            fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 4)
        gpanel = cv2.cvtColor(buf[:Hc, :Wg, :3], cv2.COLOR_RGB2BGR)
        comp = np.hstack([vpanel, gpanel])[:, :W]
        vw.write(comp)
    vw.release(); cap.release(); plt.close(fig)
    print(f"[ok] {args.out}  {N} frames @ {args.out_fps} fps "
          f"({30/args.out_fps:.1f}x mais lento)  {W}x{Hc}")


if __name__ == "__main__":
    main()
