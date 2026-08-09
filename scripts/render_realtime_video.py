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
    ap.add_argument("--layout", choices=["horizontal", "vertical"], default="horizontal")
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
    vert = args.layout == "vertical"

    plt.rcParams.update({"figure.facecolor": "#0e1116", "axes.facecolor": "#0e1116",
                         "text.color": "#e6edf3", "axes.edgecolor": "#39424d",
                         "axes.labelcolor": "#e6edf3", "xtick.color": GRY, "ytick.color": GRY})
    dpi = 100
    tr = [(t[r[3]], t[min(r[4], N - 1)], r[2]) for r in reps]
    updates, curs = [], []                       # (linha, serie) e cursores

    def prep(ax, ymin, ymax, ylabel, fs=9):
        ax.set_xlim(0, t[-1]); ax.set_ylim(ymin, ymax); ax.grid(color="#20262e")
        ax.set_ylabel(ylabel, fontsize=fs); ax.tick_params(labelsize=fs - 1)
        ax.axhline(0, color="#39424d", lw=.6)
        for s, e, _ in tr:
            ax.axvspan(s, e, color="#fff", alpha=0.03)
        curs.append(ax.axvline(0, color="#e6edf3", lw=.7, alpha=.4))

    def line(ax, y, color, label, lw=1.8):
        (ln,) = ax.plot([], [], color=color, lw=lw, label=label); updates.append((ln, y))

    fpm = max(np.abs(force).max(), np.abs(power).max()) * 1.1
    vmax = max(np.abs(hipw).max(), np.abs(kneew).max()) * 1.1

    if vert:                                     # ---- Reels/Stories 9:16 ----
        CW, CH = 720, 1280
        strip_h = 470
        fig = plt.figure(figsize=(CW / dpi, strip_h / dpi), dpi=dpi)
        gs = fig.add_gridspec(1, 2, wspace=0.28, left=0.09, right=0.99, top=0.88, bottom=0.13)
        axA = fig.add_subplot(gs[0]); axF = fig.add_subplot(gs[1])
        prep(axA, min(hip.min(), knee.min()) - 5, 190, "ângulo (°)", 8)
        axA.axhline(180, color=RED, ls=":", lw=.8, alpha=.6)
        line(axA, hip, TEAL, "quadril"); line(axA, knee, YEL, "joelho")
        axA.legend(loc="lower right", fontsize=7, facecolor="#171b22", edgecolor="#39424d")
        prep(axF, -fpm, fpm, "F(N)/P(W)", 8)
        line(axF, force, ORG, "força"); line(axF, power, TEAL, "potência")
        axF.legend(loc="upper right", fontsize=7, facecolor="#171b22", edgecolor="#39424d")
        axA.set_xlabel("t (s)", fontsize=8); axF.set_xlabel("t (s)", fontsize=8)
        fig.suptitle(f"{args.brand} — em tempo real", color=TEAL, fontweight="bold", fontsize=12)
        top_h = CH - strip_h
        sc = min(720 / 1080, top_h / 1920); vw_w, vh = int(1080 * sc), int(1920 * sc)
        vx = (CW - vw_w) // 2
        W, Hc = CW, CH
    else:                                        # ---- horizontal 16:9 ----
        Hc = args.height - args.height % 2
        fig = plt.figure(figsize=(8.8, Hc / dpi), dpi=dpi)
        gs = fig.add_gridspec(3, 1, hspace=0.32, left=0.11, right=0.985, top=0.95, bottom=0.08)
        axA, axV, axF = (fig.add_subplot(gs[i]) for i in range(3))
        prep(axA, min(hip.min(), knee.min()) - 5, 190, "ângulo (°)")
        axA.axhline(180, color=RED, ls=":", lw=.8, alpha=.6)
        line(axA, hip, TEAL, "quadril"); line(axA, knee, YEL, "joelho"); line(axA, ank, BLU, "tornozelo", 1.4)
        axA.legend(loc="lower right", fontsize=7, ncol=3, facecolor="#171b22", edgecolor="#39424d")
        prep(axV, -vmax, vmax, "vel.ang (°/s)")
        line(axV, hipw, TEAL, "quadril"); line(axV, kneew, YEL, "joelho")
        axV.legend(loc="upper right", fontsize=7, ncol=2, facecolor="#171b22", edgecolor="#39424d")
        prep(axF, -fpm, fpm, "F(N)/P(W)"); axF.set_xlabel("tempo (s)", fontsize=9)
        line(axF, force, ORG, "força"); line(axF, power, TEAL, "potência")
        axF.legend(loc="upper right", fontsize=7, ncol=2, facecolor="#171b22", edgecolor="#39424d")
        fig.suptitle(f"{args.brand} — resultados em tempo real", color=TEAL, fontweight="bold", fontsize=12)
        vw_w = int(Hc * 1080 / 1920)
        W = (vw_w + fig.canvas.get_width_height()[0]); W -= W % 2

    fig.canvas.draw()
    Wg, Hg = fig.canvas.get_width_height()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.out_fps, (W, Hc))

    def scoreboard(img, f, x=8, y=8):
        r = rep_of[f]
        rows = [f"Rep {r}/{len(reps)}" if r else "setup",
                f"F pico: {cmaxF[f]:5.0f} N", f"P pico: {cmaxP[f]:5.0f} W",
                f"V pico: {cmaxV[f]:4.2f} m/s"]
        cv2.rectangle(img, (x, y), (x + 210, y + 18 + 24 * len(rows)), (14, 17, 22), -1)
        for i, ln in enumerate(rows):
            cv2.putText(img, ln, (x + 8, y + 22 * i + 22), cv2.FONT_HERSHEY_SIMPLEX,
                        0.6, (230, 237, 243), 1, cv2.LINE_AA)

    for f in range(N):
        vf = int(round(f * (Nv - 1) / (N - 1)))
        cap.set(cv2.CAP_PROP_POS_FRAMES, vf)
        ok, frame = cap.read()
        if not ok:
            continue
        for ln, y in updates:
            ln.set_data(t[:f + 1], y[:f + 1])
        for c in curs:
            c.set_xdata([t[f], t[f]])
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), np.uint8).reshape(Hg, Wg, 4)
        gpanel = cv2.cvtColor(buf[:, :, :3], cv2.COLOR_RGB2BGR)
        if vert:
            comp = np.full((Hc, W, 3), (14, 17, 22), np.uint8)
            vpanel = cv2.resize(frame, (vw_w, vh))
            comp[0:vh, vx:vx + vw_w] = vpanel
            gh = min(Hg, Hc - top_h)
            comp[top_h:top_h + gh, 0:min(Wg, W)] = gpanel[:gh, :min(Wg, W)]
            scoreboard(comp, f, x=vx + 6, y=10)
        else:
            vpanel = cv2.resize(frame, (vw_w, Hc)); scoreboard(vpanel, f)
            comp = np.hstack([vpanel, gpanel])[:, :W]
        vw.write(comp)
    vw.release(); cap.release(); plt.close(fig)
    print(f"[ok] {args.out}  layout={args.layout}  {N} frames @ {args.out_fps} fps "
          f"({30/args.out_fps:.1f}x mais lento)  {W}x{Hc}")


if __name__ == "__main__":
    main()
