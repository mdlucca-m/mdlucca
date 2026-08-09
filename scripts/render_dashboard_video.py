#!/usr/bin/env python3
"""
scripts/render_dashboard_video.py

Video-dashboard ao vivo: pontos anatomicos + esqueleto ligado em tempo real,
graficos que se desenham progressivamente (angulos, velocidade dos membros,
vel. das maos/propulsiva, altura do quadril), painel de PICOS por variavel,
ALTURA DO SALTO (com selo no apex sobre o video) e tabela ao vivo.

Layouts:  paisagem 1920x1080 (padrao)  |  --vertical 1080x1920 (Reels)

Uso:
  python3 scripts/render_dashboard_video.py --video A.mp4 --pose pose_A.json \
      --db data/db.sqlite --session 3 --out data/dash.mp4 --fps 20.9 [--vertical]
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
     "dim": (170, 150, 130), "accent": (224, 208, 53), "grid": (52, 33, 21)}
# Bracos EXCLUIDos: apenas tronco, cabeca/pescoco e pernas.
BONES_L = [((11, 23), "hip"), ((23, 25), "hip"), ((25, 27), "knee"),
           ((27, 31), "ankle"), ((7, 11), "faint"), ((11, 12), "faint"), ((23, 24), "faint")]
BONES_R = [(24, 26), (26, 28), (28, 32)]
JOINTS = [11, 23, 25, 27]
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
    mpp = trunk_m / trunk_px
    hip_up_cm = sm3(-hip_y) * mpp * 100
    hip_up_cm = hip_up_cm - np.median(hip_up_cm[stand])

    def ispeed(idx):
        p = np.stack([N[:, idx, 0] * Wpx * mpp, N[:, idx, 1] * Hpx * mpp], 1)
        return np.linalg.norm(np.gradient(sm3(p), t, axis=0), axis=1)

    ex = {"hand_L": ispeed(L['wr_l']), "hand_R": ispeed(L['wr_r']),
          "foot_L": ispeed(L['an_l']), "foot_R": ispeed(L['an_r']), "hip_up_cm": hip_up_cm}
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


def chart(img, rect, series, ci, title, unit, fill=None, marker=None, small=False):
    x, y, w, h = rect
    panel(img, x, y, w, h, C["panel"])
    ts = 0.4 if small else 0.44
    cv2.putText(img, title, (x + 10, y + 17), F, ts, C["dim"], 1, cv2.LINE_AA)
    cv2.putText(img, unit, (x + w - 52, y + 17), F, 0.38, C["dim"], 1, cv2.LINE_AA)
    px0, py0, pw, ph = x + 42, y + 24, w - 54, h - 36
    allv = np.concatenate([s[0] for s in series]); mn, mx = float(np.nanmin(allv)), float(np.nanmax(allv))
    if mn == mx:
        mx += 1; mn -= 1
    n = len(series[0][0]); sx = lambda i: px0 + pw * (i / max(1, n - 1)); sy = lambda v: py0 + ph * (1 - (v - mn) / (mx - mn))
    for g in range(3):
        yv = mn + (mx - mn) * g / 2; yy = int(sy(yv))
        cv2.line(img, (px0, yy), (px0 + pw, yy), C["grid"], 1)
        cv2.putText(img, (f"{yv:.0f}" if mx - mn > 6 else f"{yv:.1f}"), (x + 4, yy + 4), F, 0.32, C["dim"], 1, cv2.LINE_AA)
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
    if marker is not None and marker <= ci:
        mxp, myp = int(sx(marker)), int(sy(series[0][0][marker]))
        cv2.circle(img, (mxp, myp), 6, C["accent"], 2, cv2.LINE_AA)
        cv2.putText(img, "APEX", (mxp - 16, myp - 10), F, 0.38, C["accent"], 1, cv2.LINE_AA)
    cv2.line(img, (int(sx(ci)), py0), (int(sx(ci)), py0 + ph), (90, 60, 40), 1)


def draw_skeleton(cv, lm, vx, vy, vw, vh):
    sp = lambda nx, ny: (int(vx + nx * vw), int(vy + ny * vh))
    if lm is None:
        return
    for a, b in BONES_R:
        cv2.line(cv, sp(*lm[a]), sp(*lm[b]), C["faint"], 2, cv2.LINE_AA)
    for (a, b), ck in BONES_L:
        cv2.line(cv, sp(*lm[a]), sp(*lm[b]), C[ck], 3, cv2.LINE_AA)
    for idx in JOINTS:
        cv2.circle(cv, sp(*lm[idx]), 5, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(cv, sp(*lm[idx]), 5, (0, 0, 0), 1, cv2.LINE_AA)


def apex_seal(cv, i, apex_i, jump_cm, fps, cx, cy):
    """Selo 'SALTO x cm' que aparece por ~1.2s ao redor do apex."""
    dt = abs(i - apex_i)
    win = int(fps * 0.6)
    if dt > win:
        return
    a = 1 - dt / win
    bw, bh = 220, 62
    x, y = int(cx - bw / 2), int(cy - bh / 2)
    ov = cv.copy()
    cv2.rectangle(ov, (x, y), (x + bw, y + bh), (12, 9, 5), -1)
    cv2.rectangle(ov, (x, y), (x + bw, y + bh), C["accent"], 2)
    cv2.putText(ov, "SALTO", (x + 16, y + 26), FD, 0.72, C["accent"], 1, cv2.LINE_AA)
    cv2.putText(ov, f"{jump_cm:.0f} cm", (x + 16, y + 52), FD, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    al = min(0.92, a + 0.3)
    cv2.addWeighted(ov, al, cv, 1 - al, 0, cv)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True); ap.add_argument("--pose", required=True)
    ap.add_argument("--db", default="data/db.sqlite"); ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--out", default="data/dash.mp4"); ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--brand", default="De Lucca Esporte"); ap.add_argument("--move", default="")
    ap.add_argument("--vertical", action="store_true", help="layout 1080x1920 (Reels)")
    args = ap.parse_args()

    P = json.loads(open(args.pose).read()); norm = P["norm"]
    con = sqlite3.connect(args.db); sm = load_series(con, args.session); con.close()
    ex = compute_extras(P, args.fps)
    n = min(len(norm), len(sm["t"]), len(ex["hand_L"]))
    speed = sm["speed"]; tang = sm.get("tangential_accel", np.zeros_like(speed))
    prop = np.where(tang >= -G, speed, 0.0)
    hip, knee, ankle = sm["hip_angle"], sm["knee_angle"], sm["ankle_angle"]
    hav, kav, aav = sm["hip_angvel"], sm["knee_angvel"], sm["ankle_angvel"]
    force, power = sm["force"], sm["power"]
    rpk = lambda a, i: float(np.nanmax(a[:i + 1]))
    apex = ex["apex_i"]

    cap = cv2.VideoCapture(args.video); srcW, srcH = cap.get(3), cap.get(4)
    CW, CH = (1080, 1920) if args.vertical else (1920, 1080)
    if args.vertical:
        top = 1120; vw = int(min(CW, top * srcW / srcH)); vh = int(vw * srcH / srcW)
        vx = (CW - vw) // 2; vy = 8
        dx, dy, dw, dh = 14, vy + vh + 10, CW - 28, CH - (vy + vh + 10) - 12
    else:
        vh = CH - 40; vw = int(srcW * vh / srcH); vx, vy = 20, 20
        if vw > CW * 0.34:
            vw = int(CW * 0.34); vh = int(srcH * vw / srcW); vy = (CH - vh) // 2
        dx = vx + vw + 22; dy = vy + 58; dw = CW - dx - 18

    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (CW, CH))

    def peaks_panel(cv, x, y, w, h, i, cols=1):
        panel(cv, x, y, w, h, C["panel"])
        cv2.putText(cv, "PICOS POR VARIAVEL (ao vivo)", (x + 10, y + 20), F, 0.44, C["accent"], 1, cv2.LINE_AA)
        items = [("Ang. quadril max", f"{rpk(hip,i):.0f} deg", C["hip"]),
                 ("Ang. joelho max", f"{rpk(knee,i):.0f} deg", C["knee"]),
                 ("Ang. tornozelo max", f"{rpk(ankle,i):.0f} deg", C["ankle"]),
                 ("Vel.ang quadril", f"{rpk(np.abs(hav),i):.0f} /s", C["hip"]),
                 ("Vel.ang joelho", f"{rpk(np.abs(kav),i):.0f} /s", C["knee"]),
                 ("Vel. pes", f"{max(rpk(ex['foot_L'],i),rpk(ex['foot_R'],i)):.2f} m/s", C["footR"]),
                 ("Forca (est)", f"{rpk(force,i):.0f} N", C["force"]),
                 ("Potencia (est)", f"{rpk(power,i):.0f} W", C["power"])]
        ry = y + 46; colw = w // cols; k = 0
        for lbl, val, col in items:
            cxx = x + 14 + (k % cols) * colw
            yy = ry + (k // cols) * 30
            cv2.putText(cv, lbl, (cxx, yy), F, 0.44, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, val, (cxx + colw - 165, yy), FD, 0.54, col, 1, cv2.LINE_AA)
            k += 1
        yy = ry + ((len(items) + cols - 1) // cols) * 30 + 4
        jh = ex["jump_cm"] if i >= apex else float(np.nanmax(ex["hip_up_cm"][:i + 1]))
        panel(cv, x + 12, yy, w - 24, 46, C["bg"])
        cv2.putText(cv, "ALTURA DO SALTO", (x + 22, yy + 28), F, 0.46, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"{jh:.0f} cm", (x + w - 150, yy + 32), FD, 0.85, C["accent"], 2, cv2.LINE_AA)

    def table_panel(cv, x, y, w, h, i):
        panel(cv, x, y, w, h, C["panel"])
        cv2.putText(cv, "TABELA AO VIVO", (x + 10, y + 20), F, 0.44, C["dim"], 1, cv2.LINE_AA)
        c0, c1, c2 = x + 14, x + 180, x + 320
        cv2.putText(cv, "ARTICULACAO", (c0, y + 44), F, 0.38, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, "ANGULO", (c1, y + 44), F, 0.38, C["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, "VEL.ANG", (c2, y + 44), F, 0.38, C["dim"], 1, cv2.LINE_AA)
        ry = y + 72
        for name, ang, av, ck in [("Quadril", hip, hav, "hip"), ("Joelho", knee, kav, "knee"), ("Tornozelo", ankle, aav, "ankle")]:
            cv2.putText(cv, name, (c0, ry), F, 0.5, C[ck], 1, cv2.LINE_AA)
            cv2.putText(cv, f"{ang[i]:5.0f} deg", (c1, ry), FD, 0.52, C["txt"], 1, cv2.LINE_AA)
            cv2.putText(cv, f"{av[i]:6.0f}/s", (c2, ry), FD, 0.52, C["txt"], 1, cv2.LINE_AA)
            ry += 30
        ry += 4
        for lbl, val, col in [("VEL. PES", f"{max(ex['foot_L'][i],ex['foot_R'][i]):.2f} m/s", C["footR"]),
                              ("ALTURA QUADRIL", f"{ex['hip_up_cm'][i]:+.0f} cm", C["height"]),
                              ("FORCA / POT (est)", f"{force[i]:.0f} N / {power[i]:+.0f} W", C["power"])]:
            cv2.putText(cv, lbl, (c0, ry), F, 0.42, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, val, (c1, ry), FD, 0.52, col, 1, cv2.LINE_AA)
            ry += 28

    for i in range(n):
        ok, frame = cap.read()
        if not ok:
            break
        cv = np.full((CH, CW, 3), C["bg"], np.uint8)
        cv[vy:vy + vh, vx:vx + vw] = cv2.resize(frame, (vw, vh))
        lm = norm[i] if norm[i] is not None else None
        draw_skeleton(cv, lm, vx, vy, vw, vh)
        cv2.rectangle(cv, (vx, vy), (vx + vw, vy + vh), C["line"], 1)
        # selo de salto no apex (perto do quadril)
        if lm is not None:
            hx = int(vx + (lm[23][0] + lm[24][0]) / 2 * vw); hy = int(vy + (lm[23][1] + lm[24][1]) / 2 * vh)
            apex_seal(cv, i, apex, ex["jump_cm"], args.fps, min(max(hx, vx + 120), vx + vw - 120), max(hy - 90, vy + 50))

        if args.vertical:
            cv2.putText(cv, args.brand, (dx, vy + 34), FD, 0.9, C["accent"], 1, cv2.LINE_AA)
            cv2.putText(cv, f"t={i/args.fps:4.1f}s", (CW - 150, vy + 34), FD, 0.7, C["txt"], 1, cv2.LINE_AA)
            cg = 10; cW = (dw - cg) // 2; cH = 150; yy = dy
            chart(cv, (dx, yy, cW, cH), [(hip[:n], C["hip"]), (knee[:n], C["knee"]), (ankle[:n], C["ankle"])], i, "ANGULOS (perna)", "deg", small=True)
            chart(cv, (dx + cW + cg, yy, cW, cH), [(ex["hip_up_cm"][:n], C["height"])], i, "ALTURA QUADRIL", "cm", fill=True, marker=apex, small=True)
            yy += cH + cg
            chart(cv, (dx, yy, cW, cH), [(ex["foot_L"][:n], C["footL"]), (ex["foot_R"][:n], C["footR"])], i, "VEL. PES E/D", "m/s", small=True)
            chart(cv, (dx + cW + cg, yy, cW, cH), [(hav[:n], C["hip"]), (kav[:n], C["knee"]), (aav[:n], C["ankle"])], i, "VEL. ANGULAR", "deg/s", small=True)
            yy += cH + cg
            bh = dy + dh - yy - 4
            peaks_panel(cv, dx, yy, cW, bh, i, cols=1)
            table_panel(cv, dx + cW + cg, yy, cW, bh, i)
        else:
            cv2.putText(cv, args.brand, (dx, vy + 24), FD, 0.8, C["accent"], 1, cv2.LINE_AA)
            cv2.putText(cv, args.move or "Analise em tempo real", (dx, vy + 46), F, 0.46, C["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, f"t = {i/args.fps:5.2f} s", (dx + dw - 150, vy + 24), FD, 0.6, C["txt"], 1, cv2.LINE_AA)
            cg = 12; cW = (dw - cg) // 2; cH = 176; yy = dy
            chart(cv, (dx, yy, cW, cH), [(hip[:n], C["hip"]), (knee[:n], C["knee"]), (ankle[:n], C["ankle"])], i, "ANGULOS  quadril/joelho/tornozelo", "graus")
            chart(cv, (dx + cW + cg, yy, cW, cH), [(ex["foot_L"][:n], C["footL"]), (ex["foot_R"][:n], C["footR"])], i, "VELOCIDADE DOS PES  E/D", "m/s")
            yy += cH + cg
            chart(cv, (dx, yy, cW, cH), [(hav[:n], C["hip"]), (kav[:n], C["knee"]), (aav[:n], C["ankle"])], i, "VELOCIDADE ANGULAR  quadril/joelho/tornozelo", "deg/s")
            chart(cv, (dx + cW + cg, yy, cW, cH), [(ex["hip_up_cm"][:n], C["height"])], i, "ALTURA DO QUADRIL (rel. em pe)", "cm", fill=True, marker=apex)
            yy += cH + cg
            bh = CH - yy - 18; pkw = int(dw * 0.5)
            peaks_panel(cv, dx, yy, pkw, bh, i, cols=1)
            table_panel(cv, dx + pkw + 14, yy, dw - pkw - 14, bh, i)

        writer.write(cv)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n} frames")
    writer.release(); cap.release()
    print(f"dashboard-video: {args.out}  ({n} frames, {n/args.fps:.1f}s, {CW}x{CH})  salto={ex['jump_cm']:.0f}cm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
