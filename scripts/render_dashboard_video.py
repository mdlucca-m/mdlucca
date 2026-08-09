#!/usr/bin/env python3
"""
scripts/render_dashboard_video.py

Compoe um VIDEO-DASHBOARD ao vivo: à esquerda o quadro do video com os
pontos anatomicos e o esqueleto ligado em tempo real; à direita graficos que
se desenham progressivamente (angulos, velocidade das maos, forca) e uma
tabela/tiles com angulos, velocidades, forca e potencia atualizando quadro a
quadro. Fonte dos numeros: as series ja calculadas no banco.

Uso:
  python3 scripts/render_dashboard_video.py --video clip.mp4 --pose pose.json \
      --db data/db.sqlite --session 3 --out data/dash.mp4 --fps 20.9
"""
from __future__ import annotations

import argparse
import json
import sqlite3

import cv2
import numpy as np

C = {"hip": (3, 183, 255), "knee": (139, 170, 67), "elbow": (255, 125, 199),
     "ankle": (240, 201, 76), "speed": (224, 208, 53), "force": (74, 88, 230),
     "power": (97, 162, 244), "bone": (215, 215, 215), "faint": (95, 95, 95),
     "bg": (16, 11, 6), "panel": (30, 22, 14), "line": (64, 39, 28),
     "txt": (235, 235, 235), "dim": (170, 150, 130), "accent": (224, 208, 53),
     "grid": (52, 33, 21)}

BONES_L = [((11, 13), "elbow"), ((13, 15), "elbow"), ((15, 19), "elbow"),
           ((11, 23), "hip"), ((23, 25), "hip"), ((25, 27), "knee"),
           ((27, 31), "ankle"), ((7, 11), "bone")]
BONES_R = [(12, 14), (14, 16), (24, 26), (26, 28)]
JOINTS = [11, 13, 15, 23, 25, 27, 7]
FONT = cv2.FONT_HERSHEY_SIMPLEX
FOND = cv2.FONT_HERSHEY_DUPLEX


def load(con, session):
    row = con.execute("SELECT id FROM submovement WHERE session_id=? AND kind='composite'", (session,)).fetchone() \
        or con.execute("SELECT id FROM submovement WHERE session_id=? ORDER BY n_frames DESC LIMIT 1", (session,)).fetchone()
    sm = {r[0]: np.asarray(json.loads(r[1]), float) for r in con.execute(
        "SELECT name,samples FROM series WHERE submovement_id=?", (row[0],))}
    return sm


def panel(img, x, y, w, h, col, alpha=1.0):
    if alpha >= 1:
        cv2.rectangle(img, (x, y), (x + w, y + h), col, -1)
    else:
        ov = img.copy(); cv2.rectangle(ov, (x, y), (x + w, y + h), col, -1)
        cv2.addWeighted(ov, alpha, img, 1 - alpha, 0, img)
    cv2.rectangle(img, (x, y), (x + w, y + h), C["line"], 1)


def chart(img, rect, series, ci, title, unit, fill=None):
    x, y, w, h = rect
    panel(img, x, y, w, h, C["panel"])
    cv2.putText(img, title, (x + 10, y + 18), FONT, 0.44, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(img, unit, (x + w - 46, y + 18), FONT, 0.4, C["dim"], 1, cv2.LINE_AA)
    px0, py0, pw, ph = x + 40, y + 26, w - 52, h - 40
    allv = np.concatenate([s[0] for s in series])
    mn, mx = float(np.nanmin(allv)), float(np.nanmax(allv))
    if mn == mx:
        mx += 1; mn -= 1
    n = len(series[0][0])
    sx = lambda i: px0 + pw * (i / max(1, n - 1))
    sy = lambda v: py0 + ph * (1 - (v - mn) / (mx - mn))
    for g in range(3):
        yv = mn + (mx - mn) * g / 2; yy = int(sy(yv))
        cv2.line(img, (px0, yy), (px0 + pw, yy), C["grid"], 1)
        cv2.putText(img, f"{yv:.0f}" if mx - mn > 6 else f"{yv:.1f}", (x + 4, yy + 4), FONT, 0.34, C["dim"], 1, cv2.LINE_AA)
    if mn < 0 < mx:
        yy = int(sy(0)); cv2.line(img, (px0, yy), (px0 + pw, yy), (70, 46, 30), 1)
    ci = max(1, min(ci, n - 1))
    for data, col in series:
        if fill:
            pts = [(int(sx(i)), int(sy(data[i]))) for i in range(ci + 1)]
            if len(pts) > 1:
                poly = np.array(pts + [(int(sx(ci)), int(sy(max(mn, 0)))), (int(sx(0)), int(sy(max(mn, 0))))], np.int32)
                ov = img.copy(); cv2.fillPoly(ov, [poly], col); cv2.addWeighted(ov, 0.12, img, 0.88, 0, img)
        pts = np.array([(int(sx(i)), int(sy(data[i]))) for i in range(ci + 1)], np.int32)
        if len(pts) > 1:
            cv2.polylines(img, [pts], False, col, 2, cv2.LINE_AA)
        cv2.circle(img, (int(sx(ci)), int(sy(data[ci]))), 3, col, -1, cv2.LINE_AA)
    # cursor vertical no tempo atual
    cv2.line(img, (int(sx(ci)), py0), (int(sx(ci)), py0 + ph), (90, 60, 40), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True)
    ap.add_argument("--pose", required=True)
    ap.add_argument("--db", default="data/db.sqlite")
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--out", default="data/dash.mp4")
    ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--brand", default="De Lucca Esporte")
    ap.add_argument("--move", default="")
    ap.add_argument("--cw", type=int, default=1600)
    ap.add_argument("--ch", type=int, default=900)
    args = ap.parse_args()

    P = json.loads(open(args.pose).read()); norm = P["norm"]
    con = sqlite3.connect(args.db); sm = load(con, args.session); con.close()
    n = min(len(norm), len(sm["t"]))

    cap = cv2.VideoCapture(args.video)
    CW, CH = args.cw, args.ch
    # painel de video à esquerda
    vh = CH - 40; vw0 = int(cap.get(3) * vh / cap.get(4)); vx, vy = 20, 20
    if vw0 > CW * 0.42:
        vw0 = int(CW * 0.42); vh = int(cap.get(4) * vw0 / cap.get(3)); vy = (CH - vh) // 2
    vw = vw0
    dx = vx + vw + 24                    # inicio do dashboard
    dw = CW - dx - 20
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (CW, CH))

    hip, knee, elbow = sm["hip_angle"], sm["knee_angle"], sm["elbow_angle"]
    hav, kav, eav = sm["hip_angvel"], sm["knee_angvel"], sm["elbow_angvel"]
    speed, force, power = sm["speed"], sm["force"], sm["power"]

    def sp(nx, ny):
        return int(vx + nx * vw), int(vy + ny * vh)

    for i in range(n):
        ok, frame = cap.read()
        if not ok:
            break
        canvas = np.full((CH, CW, 3), C["bg"], np.uint8)
        vfr = cv2.resize(frame, (vw, vh))
        canvas[vy:vy + vh, vx:vx + vw] = vfr
        lm = norm[i] if norm[i] is not None else None
        if lm is not None:
            for (a, b) in BONES_R:
                cv2.line(canvas, sp(*lm[a]), sp(*lm[b]), C["faint"], 2, cv2.LINE_AA)
            for (a, b), ck in BONES_L:
                cv2.line(canvas, sp(*lm[a]), sp(*lm[b]), C[ck], 3, cv2.LINE_AA)
            for idx in JOINTS:
                cv2.circle(canvas, sp(*lm[idx]), 5, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(canvas, sp(*lm[idx]), 5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.rectangle(canvas, (vx, vy), (vx + vw, vy + vh), C["line"], 1)

        # cabecalho do dashboard
        cv2.putText(canvas, args.brand, (dx, vy + 24), FOND, 0.8, C["accent"], 1, cv2.LINE_AA)
        cv2.putText(canvas, args.move or "Analise em tempo real", (dx, vy + 46), FONT, 0.46, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(canvas, f"t = {i/args.fps:5.2f} s", (dx + dw - 150, vy + 24), FOND, 0.6, C["txt"], 1, cv2.LINE_AA)

        gap = 12
        cy = vy + 60
        ch_h = 168
        chart(canvas, (dx, cy, dw, ch_h),
              [(hip[:n], C["hip"]), (knee[:n], C["knee"]), (elbow[:n], C["elbow"])], i,
              "ANGULOS  (quadril/joelho/cotovelo)", "graus")
        cy += ch_h + gap
        chart(canvas, (dx, cy, dw, ch_h), [(speed[:n], C["speed"])], i,
              "VELOCIDADE DAS MAOS", "m/s", fill=True)
        cy += ch_h + gap
        chart(canvas, (dx, cy, dw, ch_h), [(force[:n], C["force"])], i,
              "FORCA VERTICAL (estimada, CoM)", "N", fill=True)
        cy += ch_h + gap

        # ---- tabela ao vivo + tiles ----
        th = CH - cy - 20
        panel(canvas, dx, cy, dw, th, C["panel"])
        cv2.putText(canvas, "TABELA AO VIVO", (dx + 10, cy + 20), FONT, 0.44, C["dim"], 1, cv2.LINE_AA)
        cols = [dx + 14, dx + 170, dx + 300]
        cv2.putText(canvas, "ARTICULACAO", (cols[0], cy + 44), FONT, 0.4, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(canvas, "ANGULO", (cols[1], cy + 44), FONT, 0.4, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(canvas, "VEL.ANG", (cols[2], cy + 44), FONT, 0.4, C["dim"], 1, cv2.LINE_AA)
        rows = [("Quadril", hip, hav, "hip"), ("Joelho", knee, kav, "knee"), ("Cotovelo", elbow, eav, "elbow")]
        ry = cy + 70
        for name, ang, av, ck in rows:
            cv2.putText(canvas, name, (cols[0], ry), FONT, 0.5, C[ck], 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{ang[i]:5.0f} deg", (cols[1], ry), FOND, 0.52, C["txt"], 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{av[i]:6.0f}/s", (cols[2], ry), FOND, 0.52, C["txt"], 1, cv2.LINE_AA)
            ry += 30
        # tiles: velocidade / forca / potencia
        tiles = [("VEL. MAOS", f"{speed[i]:.2f}", "m/s", C["speed"]),
                 ("FORCA est", f"{force[i]:.0f}", "N", C["force"]),
                 ("POTENCIA est", f"{power[i]:+.0f}", "W", C["power"])]
        tx = dx + 440; tw = (dw - 440 - 14) // 1
        tly = cy + 40
        for lbl, val, u, col in tiles:
            panel(canvas, tx, tly, tw - 10, 44, C["bg"])
            cv2.putText(canvas, lbl, (tx + 10, tly + 17), FONT, 0.38, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(canvas, f"{val} {u}", (tx + 10, tly + 37), FOND, 0.62, col, 1, cv2.LINE_AA)
            tly += 50

        writer.write(canvas)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n} frames")
    writer.release(); cap.release()
    print(f"dashboard-video: {args.out}  ({n} frames, {n/args.fps:.1f}s, {CW}x{CH})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
