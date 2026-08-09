#!/usr/bin/env python3
"""
scripts/render_dashboard_video.py

Video-dashboard ao vivo: à esquerda o quadro com pontos anatomicos e esqueleto
ligado em tempo real; à direita graficos que se desenham progressivamente
(angulos, velocidade dos membros, velocidade das maos/propulsiva, altura do
quadril), um painel de PICOS por variavel que cresce ao vivo, e uma tabela
com angulo/velocidade angular por articulacao. Inclui ALTURA DO SALTO
(subida do quadril x escala metrica) e velocidade propulsiva.

Uso:
  python3 scripts/render_dashboard_video.py --video A.mp4 --pose pose_A.json \
      --db data/db.sqlite --session 3 --out data/dash.mp4 --fps 20.9
"""
from __future__ import annotations

import argparse
import json
import sqlite3

import cv2
import numpy as np
from scipy import signal as _sig

C = {"hip": (3, 183, 255), "knee": (139, 170, 67), "elbow": (255, 125, 199),
     "ankle": (240, 201, 76), "handL": (224, 208, 53), "handR": (120, 200, 255),
     "footL": (139, 200, 100), "footR": (90, 130, 245), "speed": (224, 208, 53),
     "prop": (120, 255, 180), "force": (74, 88, 230), "power": (97, 162, 244),
     "height": (200, 140, 255), "faint": (95, 95, 95), "bg": (16, 11, 6),
     "panel": (30, 22, 14), "line": (64, 39, 28), "txt": (235, 235, 235),
     "dim": (170, 150, 130), "accent": (224, 208, 53), "grid": (52, 33, 21),
     "hot": (90, 90, 235)}
BONES_L = [((11, 13), "elbow"), ((13, 15), "elbow"), ((15, 19), "elbow"),
           ((11, 23), "hip"), ((23, 25), "hip"), ((25, 27), "knee"),
           ((27, 31), "ankle"), ((7, 11), "faint")]
BONES_R = [(12, 14), (14, 16), (24, 26), (26, 28)]
JOINTS = [11, 13, 15, 23, 25, 27]
F, FD = cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX
G = 9.81


def load_series(con, session):
    row = con.execute("SELECT id FROM submovement WHERE session_id=? AND kind='composite'", (session,)).fetchone() \
        or con.execute("SELECT id FROM submovement WHERE session_id=? ORDER BY n_frames DESC LIMIT 1", (session,)).fetchone()
    return {r[0]: np.asarray(json.loads(r[1]), float) for r in con.execute(
        "SELECT name,samples FROM series WHERE submovement_id=?", (row[0],))}


def sm3(a):
    return _sig.savgol_filter(a, 11, 3, axis=0)


def compute_extras(P, fps):
    L = P["landmark_index"]; Wpx, Hpx = P["width"], P["height"]
    N = np.array([x if x is not None else P["norm"][0] for x in P["norm"]], float)
    Wd = np.array([w if w is not None else P["world"][0] for w in P["world"]], float)
    t = np.arange(len(N)) / fps
    stand = slice(0, int(fps * 1.2))
    trunk_m = np.median(np.linalg.norm(((Wd[:, L['sh_l']] + Wd[:, L['sh_r']]) / 2)
                                       - ((Wd[:, L['hip_l']] + Wd[:, L['hip_r']]) / 2), axis=1)[stand])
    sh_y = (N[:, L['sh_l'], 1] + N[:, L['sh_r'], 1]) / 2 * Hpx
    hip_y = (N[:, L['hip_l'], 1] + N[:, L['hip_r'], 1]) / 2 * Hpx
    trunk_px = np.median(np.abs(sh_y - hip_y)[stand]) or 1.0
    mpp = trunk_m / trunk_px                                   # metros por pixel
    hip_up_cm = sm3(-hip_y) * mpp * 100
    hip_up_cm = hip_up_cm - np.median(hip_up_cm[stand])        # 0 = altura em pe

    def ispeed(idx):
        p = np.stack([N[:, idx, 0] * Wpx * mpp, N[:, idx, 1] * Hpx * mpp], 1)
        return np.linalg.norm(np.gradient(sm3(p), t, axis=0), axis=1)

    ex = {
        "hand_L": ispeed(L['wr_l']), "hand_R": ispeed(L['wr_r']),
        "foot_L": ispeed(L['an_l']), "foot_R": ispeed(L['an_r']),
        "hip_up_cm": hip_up_cm,
    }
    win = slice(int(fps * 3.5), int(fps * 8.5))
    apex_i = win.start + int(np.argmax(hip_up_cm[win]))
    ex["jump_cm"] = float(hip_up_cm[apex_i]); ex["apex_i"] = int(apex_i)
    return ex


def panel(img, x, y, w, h, col, alpha=1.0):
    if alpha >= 1:
        cv2.rectangle(img, (x, y), (x + w, y + h), col, -1)
    else:
        ov = img.copy(); cv2.rectangle(ov, (x, y), (x + w, y + h), col, -1)
        cv2.addWeighted(ov, alpha, img, 1 - alpha, 0, img)
    cv2.rectangle(img, (x, y), (x + w, y + h), C["line"], 1)


def chart(img, rect, series, ci, title, unit, fill=None, marker=None):
    x, y, w, h = rect
    panel(img, x, y, w, h, C["panel"])
    cv2.putText(img, title, (x + 10, y + 18), F, 0.44, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(img, unit, (x + w - 52, y + 18), F, 0.4, C["dim"], 1, cv2.LINE_AA)
    px0, py0, pw, ph = x + 42, y + 26, w - 54, h - 40
    allv = np.concatenate([s[0] for s in series])
    mn, mx = float(np.nanmin(allv)), float(np.nanmax(allv))
    if mn == mx:
        mx += 1; mn -= 1
    n = len(series[0][0]); sx = lambda i: px0 + pw * (i / max(1, n - 1)); sy = lambda v: py0 + ph * (1 - (v - mn) / (mx - mn))
    for g in range(3):
        yv = mn + (mx - mn) * g / 2; yy = int(sy(yv))
        cv2.line(img, (px0, yy), (px0 + pw, yy), C["grid"], 1)
        cv2.putText(img, (f"{yv:.0f}" if mx - mn > 6 else f"{yv:.1f}"), (x + 4, yy + 4), F, 0.34, C["dim"], 1, cv2.LINE_AA)
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
    if marker is not None and marker <= ci:            # marcador de apex (salto)
        mxp, myp = int(sx(marker)), int(sy(series[0][0][marker]))
        cv2.circle(img, (mxp, myp), 6, C["accent"], 2, cv2.LINE_AA)
        cv2.putText(img, "APEX", (mxp - 16, myp - 10), F, 0.4, C["accent"], 1, cv2.LINE_AA)
    cv2.line(img, (int(sx(ci)), py0), (int(sx(ci)), py0 + ph), (90, 60, 40), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True); ap.add_argument("--pose", required=True)
    ap.add_argument("--db", default="data/db.sqlite"); ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--out", default="data/dash.mp4"); ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--brand", default="De Lucca Esporte"); ap.add_argument("--move", default="")
    ap.add_argument("--cw", type=int, default=1920); ap.add_argument("--ch", type=int, default=1080)
    args = ap.parse_args()

    P = json.loads(open(args.pose).read()); norm = P["norm"]
    con = sqlite3.connect(args.db); sm = load_series(con, args.session); con.close()
    ex = compute_extras(P, args.fps)
    n = min(len(norm), len(sm["t"]), len(ex["hand_L"]))

    # velocidade propulsiva: velocidade das maos enquanto acel. tangencial >= -g
    speed = sm["speed"]; tang = sm.get("tangential_accel", np.zeros_like(speed))
    prop = np.where(tang >= -G, speed, 0.0)
    hip, knee, elbow = sm["hip_angle"], sm["knee_angle"], sm["elbow_angle"]
    hav, kav, eav = sm["hip_angvel"], sm["knee_angvel"], sm["elbow_angvel"]
    force, power = sm["force"], sm["power"]

    cap = cv2.VideoCapture(args.video); CW, CH = args.cw, args.ch
    vh = CH - 40; vw = int(cap.get(3) * vh / cap.get(4)); vx, vy = 20, 20
    if vw > CW * 0.34:
        vw = int(CW * 0.34); vh = int(cap.get(4) * vw / cap.get(3)); vy = (CH - vh) // 2
    dx = vx + vw + 22; dw = CW - dx - 18
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (CW, CH))
    sp = lambda nx, ny: (int(vx + nx * vw), int(vy + ny * vh))

    # peaks running helper
    def rpk(a, i):
        return float(np.nanmax(a[:i + 1]))

    cgap = 12; cW = (dw - cgap) // 2; cH = 176
    for i in range(n):
        ok, frame = cap.read()
        if not ok:
            break
        cv = np.full((CH, CW, 3), C["bg"], np.uint8)
        cv[vy:vy + vh, vx:vx + vw] = cv2.resize(frame, (vw, vh))
        lm = norm[i] if norm[i] is not None else None
        if lm is not None:
            for a, b in BONES_R:
                cv2.line(cv, sp(*lm[a]), sp(*lm[b]), C["faint"], 2, cv2.LINE_AA)
            for (a, b), ck in BONES_L:
                cv2.line(cv, sp(*lm[a]), sp(*lm[b]), C[ck], 3, cv2.LINE_AA)
            for idx in JOINTS:
                cv2.circle(cv, sp(*lm[idx]), 5, (255, 255, 255), -1, cv2.LINE_AA)
                cv2.circle(cv, sp(*lm[idx]), 5, (0, 0, 0), 1, cv2.LINE_AA)
        cv2.rectangle(cv, (vx, vy), (vx + vw, vy + vh), C["line"], 1)

        cv2.putText(cv, args.brand, (dx, vy + 24), FD, 0.8, C["accent"], 1, cv2.LINE_AA)
        cv2.putText(cv, args.move or "Analise em tempo real", (dx, vy + 46), F, 0.46, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"t = {i/args.fps:5.2f} s", (dx + dw - 150, vy + 24), FD, 0.6, C["txt"], 1, cv2.LINE_AA)

        y0 = vy + 58
        chart(cv, (dx, y0, cW, cH), [(hip[:n], C["hip"]), (knee[:n], C["knee"]), (elbow[:n], C["elbow"])], i,
              "ANGULOS  quadril/joelho/cotovelo", "graus")
        chart(cv, (dx + cW + cgap, y0, cW, cH),
              [(ex["hand_L"][:n], C["handL"]), (ex["hand_R"][:n], C["handR"]),
               (ex["foot_L"][:n], C["footL"]), (ex["foot_R"][:n], C["footR"])], i,
              "VELOCIDADE DOS MEMBROS  maos/pes", "m/s")
        y0 += cH + cgap
        chart(cv, (dx, y0, cW, cH), [(speed[:n], C["speed"]), (prop[:n], C["prop"])], i,
              "VEL. MAOS + VEL. PROPULSIVA", "m/s", fill=True)
        chart(cv, (dx + cW + cgap, y0, cW, cH), [(ex["hip_up_cm"][:n], C["height"])], i,
              "ALTURA DO QUADRIL (rel. em pe)", "cm", fill=True, marker=ex["apex_i"])
        y0 += cH + cgap

        # ---- PICOS (running) ----
        ph = CH - y0 - 18
        pkw = int(dw * 0.5)
        panel(cv, dx, y0, pkw, ph, C["panel"])
        cv2.putText(cv, "PICOS POR VARIAVEL (ao vivo)", (dx + 10, y0 + 20), F, 0.44, C["accent"], 1, cv2.LINE_AA)
        picos = [
            ("Ang. quadril max", f"{rpk(hip,i):.0f} deg", C["hip"]),
            ("Ang. joelho max", f"{rpk(knee,i):.0f} deg", C["knee"]),
            ("Vel.ang quadril", f"{rpk(np.abs(hav),i):.0f} /s", C["hip"]),
            ("Vel. maos", f"{max(rpk(ex['hand_L'],i),rpk(ex['hand_R'],i)):.2f} m/s", C["handL"]),
            ("Vel. pes", f"{max(rpk(ex['foot_L'],i),rpk(ex['foot_R'],i)):.2f} m/s", C["footR"]),
            ("Vel. propulsiva", f"{rpk(prop,i):.2f} m/s", C["prop"]),
            ("Forca (est)", f"{rpk(force,i):.0f} N", C["force"]),
            ("Potencia (est)", f"{rpk(power,i):.0f} W", C["power"]),
        ]
        ry = y0 + 46
        for lbl, val, col in picos:
            cv2.putText(cv, lbl, (dx + 14, ry), F, 0.46, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, val, (dx + pkw - 150, ry), FD, 0.56, col, 1, cv2.LINE_AA)
            ry += 30
        # destaque ALTURA DO SALTO
        reached = i >= ex["apex_i"]
        jh = ex["jump_cm"] if reached else float(np.nanmax(ex["hip_up_cm"][:i + 1]))
        panel(cv, dx + 14, ry - 6, pkw - 28, 46, C["bg"])
        cv2.putText(cv, "ALTURA DO SALTO", (dx + 24, ry + 12), F, 0.44, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"{jh:.0f} cm", (dx + pkw - 150, ry + 20), FD, 0.8, C["accent"], 2, cv2.LINE_AA)

        # ---- TABELA AO VIVO ----
        tx = dx + pkw + 14; tw = dw - pkw - 14
        panel(cv, tx, y0, tw, ph, C["panel"])
        cv2.putText(cv, "TABELA AO VIVO", (tx + 10, y0 + 20), F, 0.44, C["dim"], 1, cv2.LINE_AA)
        c0, c1, c2 = tx + 14, tx + 180, tx + 320
        cv2.putText(cv, "ARTICULACAO", (c0, y0 + 44), F, 0.4, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, "ANGULO", (c1, y0 + 44), F, 0.4, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, "VEL.ANG", (c2, y0 + 44), F, 0.4, C["dim"], 1, cv2.LINE_AA)
        ry = y0 + 72
        for name, ang, av, ck in [("Quadril", hip, hav, "hip"), ("Joelho", knee, kav, "knee"), ("Cotovelo", elbow, eav, "elbow")]:
            cv2.putText(cv, name, (c0, ry), F, 0.52, C[ck], 1, cv2.LINE_AA)
            cv2.putText(cv, f"{ang[i]:5.0f} deg", (c1, ry), FD, 0.54, C["txt"], 1, cv2.LINE_AA)
            cv2.putText(cv, f"{av[i]:6.0f}/s", (c2, ry), FD, 0.54, C["txt"], 1, cv2.LINE_AA)
            ry += 32
        ry += 6
        for lbl, val, col in [("VEL. MAOS", f"{speed[i]:.2f} m/s", C["speed"]),
                              ("VEL. PROPULSIVA", f"{prop[i]:.2f} m/s", C["prop"]),
                              ("FORCA / POT (est)", f"{force[i]:.0f} N / {power[i]:+.0f} W", C["power"])]:
            cv2.putText(cv, lbl, (c0, ry), F, 0.44, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, val, (c1, ry), FD, 0.54, col, 1, cv2.LINE_AA)
            ry += 30

        writer.write(cv)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n} frames")
    writer.release(); cap.release()
    print(f"dashboard-video: {args.out}  ({n} frames, {n/args.fps:.1f}s, {CW}x{CH})  salto={ex['jump_cm']:.0f}cm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
