#!/usr/bin/env python3
"""
render_angvel_video.py — video com plotagem EM TEMPO REAL das velocidades
angulares por ARTICULACAO (quadril, joelho, tornozelo) e por SEGMENTO (tronco,
coxa, perna, pe), a partir da pose extraida (MediaPipe).

Esquerda: esqueleto (pernas + tronco) com segmentos coloridos, atualizando.
Direita (cima): velocidade angular das articulacoes ao vivo.
Direita (baixo): velocidade angular dos segmentos ao vivo.
Cursor de tempo varre os graficos conforme o movimento avanca.

Uso:
    python3 scripts/render_angvel_video.py --pose data/out/pose_XXXX.json \
        --out data/out/angvel.mp4 --fps 30
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import cv2  # noqa: E402
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.signal import savgol_filter  # noqa: E402

TEAL, RED, YEL, BLU, PUR, ORG, GRY = ("#2a9d8f", "#e63946", "#e9c46a", "#4aa8ff",
                                      "#c77dff", "#f4a261", "#8b98a6")


def _ang_of(v):
    """angulo absoluto (graus) do vetor, desenrolado."""
    a = np.degrees(np.arctan2(v[:, 1], v[:, 0]))
    return np.unwrap(np.radians(a)) * 180 / np.pi


def _joint_angle(p, vx, a, b):
    """angulo interno (graus) no vertice a entre a->prev e a->next."""
    u = p[b] - p[a]
    w = p[vx] - p[a]
    cos = np.sum(u * w, 1) / (np.linalg.norm(u, axis=1) * np.linalg.norm(w, axis=1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def _smooth(y, w=15):
    n = len(y)
    w = min(w if w % 2 else w + 1, n - (1 - n % 2))
    return savgol_filter(y, max(5, w), 3) if n > 5 else y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pose", required=True)
    ap.add_argument("--out", default="data/out/angvel.mp4")
    ap.add_argument("--fps", type=float, default=None)
    ap.add_argument("--brand", default="De Lucca Esporte")
    ap.add_argument("--step", type=int, default=1, help="pula frames (1=todos)")
    args = ap.parse_args()

    d = json.load(open(args.pose))
    LI, norm = d["landmark_index"], d["norm"]
    fps = args.fps or d["fps"]
    N = len(norm)
    P = {k: np.array([[fr[i][0], fr[i][1]] for fr in norm], float) for k, i in LI.items()}
    t = np.arange(N) / fps
    dt = 1.0 / fps

    # velocidades angulares das ARTICULACOES (graus/s)
    hip_a = _joint_angle(P, "sh_l", "hip_l", "kn_l")     # tronco-coxa no quadril
    knee_a = _joint_angle(P, "hip_l", "kn_l", "an_l")    # coxa-perna no joelho
    ank_a = _joint_angle(P, "kn_l", "an_l", "foot_l")    # perna-pe no tornozelo
    joints = {
        "Quadril": (_smooth(np.gradient(_smooth(hip_a), dt)), TEAL),
        "Joelho": (_smooth(np.gradient(_smooth(knee_a), dt)), YEL),
        "Tornozelo": (_smooth(np.gradient(_smooth(ank_a), dt)), BLU),
    }
    # velocidades angulares dos SEGMENTOS (graus/s, angulo absoluto)
    seg_def = {"Tronco": ("sh_l", "hip_l", PUR), "Coxa": ("hip_l", "kn_l", TEAL),
               "Perna": ("kn_l", "an_l", ORG), "Pé": ("an_l", "foot_l", RED)}
    segs = {}
    for name, (a, b, col) in seg_def.items():
        ang = _ang_of(P[b] - P[a])
        segs[name] = (_smooth(np.gradient(_smooth(ang), dt)), col)

    # aceleracao angular das ARTICULACOES (graus/s^2) = derivada da vel. angular
    accels = {name: (_smooth(np.gradient(v, dt), 19), col)
              for name, (v, col) in joints.items()}

    ymax_j = max(np.max(np.abs(v)) for v, _ in joints.values()) * 1.1
    ymax_s = max(np.max(np.abs(v)) for v, _ in segs.values()) * 1.1
    ymax_a = max(np.max(np.abs(v)) for v, _ in accels.values()) * 1.1

    plt.rcParams.update({"figure.facecolor": "#0e1116", "axes.facecolor": "#0e1116",
                         "axes.edgecolor": "#39424d", "text.color": "#e6edf3",
                         "axes.labelcolor": "#e6edf3", "xtick.color": GRY,
                         "ytick.color": GRY, "font.size": 11})
    fig = plt.figure(figsize=(12, 8.8), dpi=110)
    gs = fig.add_gridspec(3, 2, width_ratios=[1, 1.7], hspace=0.42, right=0.985)
    axSk = fig.add_subplot(gs[:, 0])
    axJ = fig.add_subplot(gs[0, 1]); axS = fig.add_subplot(gs[1, 1]); axA = fig.add_subplot(gs[2, 1])
    axJ.tick_params(labelbottom=False); axS.tick_params(labelbottom=False)
    fig.suptitle(f"{args.brand} — vel. e aceleração angular em tempo real (articulações e segmentos)",
                 color=TEAL, fontweight="bold", fontsize=12)

    # esqueleto: pernas + tronco (esquerda em destaque)
    BONES = [("ear_l", "sh_l"), ("sh_l", "hip_l"), ("hip_l", "kn_l"),
             ("kn_l", "an_l"), ("an_l", "foot_l"),
             ("sh_l", "sh_r"), ("hip_l", "hip_r"),
             ("hip_r", "kn_r"), ("kn_r", "an_r"), ("an_r", "foot_r")]
    seg_bone_col = {("sh_l", "hip_l"): PUR, ("hip_l", "kn_l"): TEAL,
                    ("kn_l", "an_l"): ORG, ("an_l", "foot_l"): RED}
    axSk.set_xlim(0, 1); axSk.set_ylim(1, 0); axSk.axis("off")
    axSk.set_title("segmentos", color=GRY, fontsize=10)
    bone_lines = {}
    for a, b in BONES:
        col = seg_bone_col.get((a, b), GRY)
        lw = 5 if (a, b) in seg_bone_col else 2.5
        (ln,) = axSk.plot([], [], color=col, lw=lw, solid_capstyle="round")
        bone_lines[(a, b)] = ln
    joint_pts, = axSk.plot([], [], "o", color="#e6edf3", ms=5)

    def setup(ax, series, ymax, title, unit="°/s"):
        ax.set_xlim(0, t[-1]); ax.set_ylim(-ymax, ymax)
        ax.axhline(0, color="#39424d", lw=.8)
        ax.set_ylabel(unit); ax.set_title(title, color="#e6edf3", fontsize=11)
        lines = {}
        for name, (v, col) in series.items():
            (ln,) = ax.plot([], [], color=col, lw=1.8, label=name)
            lines[name] = ln
        ax.legend(loc="upper right", ncol=len(series), fontsize=8,
                  facecolor="#171b22", edgecolor="#39424d")
        cur = ax.axvline(0, color="#e6edf3", lw=.8, alpha=.5)
        return lines, cur
    jl, jc = setup(axJ, joints, ymax_j, "Articulações — vel. angular")
    sl, sc = setup(axS, segs, ymax_s, "Segmentos — vel. angular")
    al, ac = setup(axA, accels, ymax_a, "Articulações — aceleração angular", unit="°/s²")
    axA.set_xlabel("tempo (s)")
    val_txt = axSk.text(0.02, 0.02, "", color="#e6edf3", fontsize=9, va="top",
                        family="monospace", transform=axSk.transAxes)

    # writer via OpenCV (ffmpeg CLI pode nao existir no ambiente)
    fig.canvas.draw()
    w0, h0 = fig.canvas.get_width_height()
    w0 -= w0 % 2; h0 -= h0 % 2
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    vw = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"),
                         fps / args.step, (w0, h0))
    frames = list(range(0, N, args.step))
    for f in frames:
        for (a, b), ln in bone_lines.items():
            ln.set_data([P[a][f, 0], P[b][f, 0]], [P[a][f, 1], P[b][f, 1]])
        pts = ["hip_l", "kn_l", "an_l", "sh_l", "foot_l"]
        joint_pts.set_data([P[p][f, 0] for p in pts], [P[p][f, 1] for p in pts])
        for name, (v, _) in joints.items():
            jl[name].set_data(t[:f + 1], v[:f + 1])
        for name, (v, _) in segs.items():
            sl[name].set_data(t[:f + 1], v[:f + 1])
        for name, (v, _) in accels.items():
            al[name].set_data(t[:f + 1], v[:f + 1])
        jc.set_xdata([t[f], t[f]]); sc.set_xdata([t[f], t[f]]); ac.set_xdata([t[f], t[f]])
        lines_txt = "  ".join(f"{n[:4]}:{v[f]:>5.0f}" for n, (v, _) in joints.items())
        seg_txt = "  ".join(f"{n[:4]}:{v[f]:>5.0f}" for n, (v, _) in segs.items())
        acc_txt = "  ".join(f"{n[:4]}:{v[f]:>6.0f}" for n, (v, _) in accels.items())
        val_txt.set_text(f"t={t[f]:4.1f}s\nvel °/s   artic {lines_txt}\n"
                         f"          seg   {seg_txt}\nacel °/s² artic {acc_txt}")
        fig.canvas.draw()
        buf = np.frombuffer(fig.canvas.buffer_rgba(), np.uint8).reshape(
            fig.canvas.get_width_height()[1], fig.canvas.get_width_height()[0], 4)
        frame = cv2.cvtColor(buf[:h0, :w0, :3], cv2.COLOR_RGB2BGR)
        vw.write(frame)
    vw.release()
    plt.close(fig)
    print(f"[ok] {args.out}  ({len(frames)} frames @ {fps/args.step:.1f} fps, {w0}x{h0})")
    print("picos (graus/s):",
          {n: round(float(np.max(np.abs(v))), 0) for n, (v, _) in {**joints, **segs}.items()})


if __name__ == "__main__":
    main()
