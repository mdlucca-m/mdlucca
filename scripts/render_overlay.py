#!/usr/bin/env python3
"""
scripts/render_overlay.py

Renderiza um VIDEO ANOTADO pronto para postar: desenha o esqueleto de pose
sobre cada frame e sobrepoe a biomecanica ao vivo (angulos referenciados ao
padrao de 180 graus de extensao, velocidade da barra, fase, contador de reps).

Fonte dos numeros: as series ja calculadas no banco (submovimento composto
da sessao) — mesma cadeia pose->biomecanica da API.

Uso:
  python3 scripts/render_overlay.py --frames <dir> --pose data/pose.json \
      --db data/db.sqlite --session 2 --out data/overlay.mp4 --brand "De Lucca Esporte"
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sqlite3
from pathlib import Path

import cv2
import numpy as np

# Cores BGR (mesma identidade do dashboard).
C = {"hip": (3, 183, 255), "knee": (139, 170, 67), "elbow": (255, 125, 199),
     "ankle": (240, 201, 76), "bone": (210, 210, 210), "faint": (90, 90, 90),
     "bg": (18, 12, 6), "txt": (235, 235, 235), "dim": (170, 150, 130),
     "accent": (255, 229, 0), "good": (139, 200, 100), "warn": (70, 110, 230)}

EXT_STD = 180.0  # padrao de extensao completa

# conexoes (indices BlazePose) e cor por segmento
BONES_L = [((11, 13), "elbow"), ((13, 15), "elbow"), ((15, 19), "elbow"),
           ((11, 23), "hip"), ((23, 25), "hip"), ((25, 27), "knee"),
           ((27, 31), "ankle"), ((7, 11), "bone")]
BONES_R = [(12, 14), (14, 16), (24, 26), (26, 28)]  # lado oposto, esmaecido
JOINTS = {"sh": 11, "el": 13, "wr": 15, "hip": 23, "kn": 25, "an": 27}


def load_series(con, session_id):
    row = con.execute(
        "SELECT id FROM submovement WHERE session_id=? AND kind='composite'", (session_id,)).fetchone()
    if not row:
        row = con.execute("SELECT id FROM submovement WHERE session_id=? ORDER BY n_frames DESC LIMIT 1",
                          (session_id,)).fetchone()
    sid = row[0]
    sm = {r[0]: json.loads(r[1]) for r in con.execute(
        "SELECT name,samples FROM series WHERE submovement_id=?", (sid,))}
    reps = con.execute(
        "SELECT ordinal,label,frame_start,frame_end FROM submovement "
        "WHERE session_id=? AND kind!='composite' ORDER BY frame_start", (session_id,)).fetchall()
    return sm, [dict(ordinal=o, label=l, start=a, end=b) for o, l, a, b in reps]


def panel(img, x, y, w, h, alpha=0.62):
    ov = img.copy()
    cv2.rectangle(ov, (x, y), (x + w, y + h), C["bg"], -1)
    cv2.addWeighted(ov, alpha, img, 1 - alpha, 0, img)
    cv2.rectangle(img, (x, y), (x + w, y + h), (60, 48, 30), 1)


def bar_meter(img, x, y, w, frac, color, label):
    cv2.rectangle(img, (x, y), (x + w, y + 10), (50, 50, 50), -1)
    cv2.rectangle(img, (x, y), (x + int(w * max(0, min(1, frac))), y + 10), color, -1)
    cv2.putText(img, label, (x, y - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.42, C["dim"], 1, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--frames", help="pasta de frames PNG (ou use --video)")
    ap.add_argument("--video", help="le os frames direto de um arquivo de video (cv2)")
    ap.add_argument("--pose", default="data/pose.json")
    ap.add_argument("--db", default="data/db.sqlite")
    ap.add_argument("--session", type=int, default=2)
    ap.add_argument("--out", default="data/overlay.mp4")
    ap.add_argument("--brand", default="De Lucca Esporte")
    ap.add_argument("--move", default="", help="nome do movimento exibido no HUD")
    ap.add_argument("--fps", type=float, default=25.0)
    args = ap.parse_args()

    P = json.loads(Path(args.pose).read_text())
    norm = P["norm"]
    n = len(norm)
    con = sqlite3.connect(args.db)
    sm, reps = load_series(con, args.session)
    con.close()

    # fonte dos frames: video (cv2) ou pasta de PNGs
    cap_in = None
    if args.video:
        cap_in = cv2.VideoCapture(args.video)
        if not cap_in.isOpened():
            raise SystemExit(f"nao consegui abrir o video {args.video}")
        n_frames = int(cap_in.get(cv2.CAP_PROP_FRAME_COUNT))

        def read_frame(_i):
            ok, im = cap_in.read()
            return im if ok else None
        H = int(cap_in.get(4)); W = int(cap_in.get(3))
    else:
        files = sorted(glob.glob(os.path.join(args.frames, "*.png"))) if args.frames else []
        if not files:
            raise SystemExit("informe --video ou --frames")
        n_frames = len(files)

        def read_frame(i):
            return cv2.imread(files[i])
        H, W = cv2.imread(files[0]).shape[:2]

    def g(name, i):
        a = sm.get(name)
        return a[i] if a and i < len(a) else None

    bar_h = np.asarray(sm.get("bar_height_rel_hip", [0] * n), float)
    v_vert = np.gradient(bar_h)
    speed = np.asarray(sm.get("speed", [0] * n), float)
    vmax = float(np.nanmax(speed)) or 1.0
    peak_speed_rep = {}
    for r in reps:
        seg = speed[r["start"]:r["end"] + 1]
        peak_speed_rep[r["ordinal"]] = float(np.nanmax(seg)) if seg.size else 0.0

    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (W, H))

    def px(pt):
        return int(pt[0] * W), int(pt[1] * H)

    for i in range(n_frames):
        img = read_frame(i)
        if img is None:
            break
        lm = norm[i] if i < len(norm) and norm[i] is not None else None
        if lm is not None:
            for (a, b) in BONES_R:  # lado oposto esmaecido
                cv2.line(img, px(lm[a]), px(lm[b]), C["faint"], 2, cv2.LINE_AA)
            for (a, b), ckey in BONES_L:
                cv2.line(img, px(lm[a]), px(lm[b]), C[ckey], 4, cv2.LINE_AA)
            for _, idx in JOINTS.items():
                cv2.circle(img, px(lm[idx]), 5, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(img, px(lm[idx]), 5, (0, 0, 0), 1, cv2.LINE_AA)

        # --- HUD superior ---
        panel(img, 12, 12, 300, 96)
        cv2.putText(img, args.brand, (24, 38), cv2.FONT_HERSHEY_DUPLEX, 0.7, C["accent"], 1, cv2.LINE_AA)
        cv2.putText(img, (args.move or "Analise biomecanica | pose 3D"), (24, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, C["dim"], 1, cv2.LINE_AA)
        rep_now = next((r for r in reps if r["start"] <= i <= r["end"]), None)
        rep_lbl = f"REP {rep_now['ordinal']}/{len(reps)}" if rep_now else "-"
        phase = "SUBIDA" if v_vert[i] > 0.001 else ("DESCIDA" if v_vert[i] < -0.001 else "PAUSA")
        cv2.putText(img, f"{rep_lbl}   {phase}", (24, 88), cv2.FONT_HERSHEY_DUPLEX, 0.62,
                    C["good"] if phase == "SUBIDA" else C["txt"], 1, cv2.LINE_AA)
        cv2.putText(img, f"t={i/args.fps:0.1f}s", (238, 88), cv2.FONT_HERSHEY_SIMPLEX, 0.44,
                    C["dim"], 1, cv2.LINE_AA)

        # --- flash central de REP ao iniciar cada repeticao (~0.6s) ---
        if rep_now:
            df = i - rep_now["start"]
            if 0 <= df < int(args.fps * 0.6):
                a = 1.0 - df / (args.fps * 0.6)
                fs = 1.7 + a * 1.3
                txt = f"REP {rep_now['ordinal']}"
                (tw, th2), _ = cv2.getTextSize(txt, cv2.FONT_HERSHEY_DUPLEX, fs, 3)
                ov = img.copy()
                cv2.putText(ov, txt, (W // 2 - tw // 2, int(H * 0.42)), cv2.FONT_HERSHEY_DUPLEX,
                            fs, C["accent"], 3, cv2.LINE_AA)
                cv2.addWeighted(ov, min(0.9, a + 0.25), img, 1 - min(0.9, a + 0.25), 0, img)

        # --- HUD angulos (referencia 180 graus) ---
        panel(img, 12, H - 150, 330, 138)
        cv2.putText(img, "ANGULOS  (padrao extensao = 180)", (22, H - 128),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.44, C["dim"], 1, cv2.LINE_AA)
        rows = [("Quadril", "hip_angle", "hip"), ("Joelho", "knee_angle", "knee"),
                ("Cotovelo", "elbow_angle", "elbow")]
        yy = H - 104
        for name, key, ck in rows:
            v = g(key, i)
            if v is None:
                continue
            deficit = EXT_STD - v
            cv2.putText(img, f"{name:8s}", (22, yy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, C[ck], 1, cv2.LINE_AA)
            cv2.putText(img, f"{v:5.0f}", (140, yy), cv2.FONT_HERSHEY_DUPLEX, 0.6, C["txt"], 1, cv2.LINE_AA)
            col = C["good"] if deficit <= 10 else (C["warn"] if deficit > 35 else C["txt"])
            cv2.putText(img, f"def {deficit:4.0f}", (210, yy), cv2.FONT_HERSHEY_SIMPLEX, 0.46, col, 1, cv2.LINE_AA)
            # arco ate 180: barra de extensao (1 = 180 graus)
            bar_meter(img, 300, yy - 9, 28, v / 180.0, C[ck], "")
            yy += 34

        # --- HUD velocidade da barra ---
        panel(img, W - 210, 12, 198, 100)
        sv = float(speed[i]) if i < len(speed) else 0.0
        cv2.putText(img, "VELOCIDADE MAOS", (W - 200, 34), cv2.FONT_HERSHEY_SIMPLEX, 0.42, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(img, f"{sv:0.2f} m/s", (W - 200, 64), cv2.FONT_HERSHEY_DUPLEX, 0.74, C["accent"], 1, cv2.LINE_AA)
        bar_meter(img, W - 200, 76, 180, sv / vmax, C["accent"], "")
        if rep_now:
            cv2.putText(img, f"pico da rep: {peak_speed_rep[rep_now['ordinal']]:0.2f} m/s",
                        (W - 200, 102), cv2.FONT_HERSHEY_SIMPLEX, 0.4, C["dim"], 1, cv2.LINE_AA)

        writer.write(img)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n_frames} frames anotados")

    writer.release()
    if cap_in is not None:
        cap_in.release()
    print(f"video anotado: {args.out}  ({n_frames} frames, {n_frames/args.fps:0.1f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
