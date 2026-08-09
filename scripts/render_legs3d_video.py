#!/usr/bin/env python3
"""
scripts/render_legs3d_video.py

Analise das DUAS PERNAS (esquerda x direita) do salto de ginastica:
- video com esqueleto 2D das pernas (E=ciano, D=magenta), sem bracos;
- boneco-palito 3D (world landmarks) com varredura de angulo, diferenciando
  as pernas;
- graficos ao vivo: extensao do joelho E/D com referencia de 180 graus,
  velocidade angular, altura da ponta dos pes ao solo, altura do quadril ao
  solo (com marcador de MAX EXTENSAO);
- picos por perna: extensao maxima (proximidade de 180), vel. angular e
  aceleracao de pico, altura de pe maxima, altura do quadril na max extensao.

Uso:
  python3 scripts/render_legs3d_video.py --video A.mp4 --pose pose_A.json \
      --out data/legs3d.mp4 --fps 20.9
"""
from __future__ import annotations

import argparse
import json

import cv2
import numpy as np
from scipy import signal as _sig

LC = (235, 206, 66)     # perna ESQUERDA (ciano-esverdeado) BGR
RC = (206, 92, 230)     # perna DIREITA (magenta) BGR
TR = (170, 170, 170)    # tronco/cabeca
COL = {"bg": (16, 11, 6), "panel": (30, 22, 14), "line": (64, 39, 28),
       "txt": (235, 235, 235), "dim": (170, 150, 130), "accent": (224, 208, 53),
       "grid": (52, 33, 21), "ref": (90, 200, 120)}
F, FD = cv2.FONT_HERSHEY_SIMPLEX, cv2.FONT_HERSHEY_DUPLEX
G = 9.81


def smf(a):
    return _sig.savgol_filter(a, 11, 3, axis=0)


def compute(P, fps):
    L = P["landmark_index"]; Wpx, Hpx = P["width"], P["height"]
    N = np.array([x if x is not None else P["norm"][0] for x in P["norm"]], float)
    Wd = np.array([w if w is not None else P["world"][0] for w in P["world"]], float)
    t = np.arange(len(N)) / fps

    def ang(a, b, c):
        v1 = Wd[:, a] - Wd[:, b]; v2 = Wd[:, c] - Wd[:, b]
        cs = (v1 * v2).sum(1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-9)
        return smf(np.degrees(np.arccos(np.clip(cs, -1, 1))))

    kneeL = ang(L['hip_l'], L['kn_l'], L['an_l']); kneeR = ang(L['hip_r'], L['kn_r'], L['an_r'])
    def dd(a):
        v = np.gradient(a, t); ac = np.gradient(smf(v), t); return v, ac
    kvL, kaL = dd(kneeL); kvR, kaR = dd(kneeR)
    stand = slice(0, int(fps * 1.2))
    trunk_m = np.median(np.linalg.norm(((Wd[:, L['sh_l']] + Wd[:, L['sh_r']]) / 2)
                                       - ((Wd[:, L['hip_l']] + Wd[:, L['hip_r']]) / 2), axis=1)[stand])
    sh_y = (N[:, L['sh_l'], 1] + N[:, L['sh_r'], 1]) / 2 * Hpx
    hip_y = (N[:, L['hip_l'], 1] + N[:, L['hip_r'], 1]) / 2 * Hpx
    mpp = trunk_m / (np.median(np.abs(sh_y - hip_y)[stand]) or 1)
    footL_y = N[:, L['foot_l'], 1] * Hpx; footR_y = N[:, L['foot_r'], 1] * Hpx
    ground = np.median(np.maximum(footL_y, footR_y)[stand])
    hFootL = (ground - smf(footL_y)) * mpp * 100
    hFootR = (ground - smf(footR_y)) * mpp * 100
    hHip = (ground - smf(hip_y)) * mpp * 100
    win = slice(int(fps * 3.5), int(fps * 8.5))
    apex = win.start + int(np.argmax(hHip[win]))
    return dict(N=N, Wd=Wd, L=L, t=t, kneeL=kneeL, kneeR=kneeR, kvL=kvL, kvR=kvR,
                kaL=kaL, kaR=kaR, hFootL=hFootL, hFootR=hFootR, hHip=hHip,
                apex=apex, hip_stand=float(np.median(hHip[stand])))


def panel(img, x, y, w, h, col=COL["panel"]):
    cv2.rectangle(img, (x, y), (x + w, y + h), col, -1)
    cv2.rectangle(img, (x, y), (x + w, y + h), COL["line"], 1)


def chart(img, rect, series, ci, title, unit, hline=None, marker=None, fill=None):
    x, y, w, h = rect; panel(img, x, y, w, h)
    cv2.putText(img, title, (x + 10, y + 17), F, 0.42, COL["dim"], 1, cv2.LINE_AA)
    cv2.putText(img, unit, (x + w - 52, y + 17), F, 0.38, COL["dim"], 1, cv2.LINE_AA)
    px0, py0, pw, ph = x + 44, y + 24, w - 56, h - 36
    allv = np.concatenate([s[0] for s in series] + ([np.array([hline])] if hline is not None else []))
    mn, mx = float(np.nanmin(allv)), float(np.nanmax(allv))
    if mn == mx:
        mx += 1; mn -= 1
    n = len(series[0][0]); sx = lambda i: px0 + pw * (i / max(1, n - 1)); sy = lambda v: py0 + ph * (1 - (v - mn) / (mx - mn))
    for g in range(3):
        yv = mn + (mx - mn) * g / 2; yy = int(sy(yv))
        cv2.line(img, (px0, yy), (px0 + pw, yy), COL["grid"], 1)
        cv2.putText(img, (f"{yv:.0f}" if mx - mn > 6 else f"{yv:.1f}"), (x + 4, yy + 4), F, 0.32, COL["dim"], 1, cv2.LINE_AA)
    if hline is not None:
        yy = int(sy(hline))
        for xseg in range(px0, px0 + pw, 12):
            cv2.line(img, (xseg, yy), (xseg + 6, yy), COL["ref"], 1)
        cv2.putText(img, f"{hline:.0f}", (px0 + pw - 26, yy - 4), F, 0.34, COL["ref"], 1, cv2.LINE_AA)
    ci = max(1, min(ci, n - 1))
    for data, col in series:
        if fill:
            pts = [(int(sx(i)), int(sy(data[i]))) for i in range(ci + 1)]
            if len(pts) > 1:
                poly = np.array(pts + [(int(sx(ci)), int(sy(max(mn, 0)))), (int(sx(0)), int(sy(max(mn, 0))))], np.int32)
                ov = img.copy(); cv2.fillPoly(ov, [poly], col); cv2.addWeighted(ov, 0.12, img, 0.88, 0, img)
        p = np.array([(int(sx(i)), int(sy(data[i]))) for i in range(ci + 1)], np.int32)
        if len(p) > 1:
            cv2.polylines(img, [p], False, col, 2, cv2.LINE_AA)
        cv2.circle(img, (int(sx(ci)), int(sy(data[ci]))), 3, col, -1, cv2.LINE_AA)
    if marker is not None and marker <= ci:
        mxp, myp = int(sx(marker)), int(sy(series[0][0][marker]))
        cv2.circle(img, (mxp, myp), 6, COL["accent"], 2, cv2.LINE_AA)
        cv2.putText(img, "MAX EXT", (mxp - 26, myp - 10), F, 0.36, COL["accent"], 1, cv2.LINE_AA)
    cv2.line(img, (int(sx(ci)), py0), (int(sx(ci)), py0 + ph), (90, 60, 40), 1)


LEGS2D = {"L": [(23, 25), (25, 27), (27, 31)], "R": [(24, 26), (26, 28), (28, 32)]}
TRUNK = [(11, 23), (12, 24), (11, 12), (23, 24), (7, 11), (8, 12)]


def draw_2d(cv, lm, vx, vy, vw, vh):
    sp = lambda p: (int(vx + p[0] * vw), int(vy + p[1] * vh))
    for a, b in TRUNK:
        cv2.line(cv, sp(lm[a]), sp(lm[b]), TR, 2, cv2.LINE_AA)
    for a, b in LEGS2D["L"]:
        cv2.line(cv, sp(lm[a]), sp(lm[b]), LC, 4, cv2.LINE_AA)
    for a, b in LEGS2D["R"]:
        cv2.line(cv, sp(lm[a]), sp(lm[b]), RC, 4, cv2.LINE_AA)
    for idx in (23, 25, 27, 31, 24, 26, 28, 32):
        cv2.circle(cv, sp(lm[idx]), 4, (255, 255, 255), -1, cv2.LINE_AA)


def draw_stick3d(cv, rect, W, theta_deg, ground_y_world):
    x, y, w, h = rect; panel(cv, x, y, w, h)
    cv2.putText(cv, "BONECO 3D  (E=ciano  D=magenta)", (x + 10, y + 18), F, 0.42, COL["dim"], 1, cv2.LINE_AA)
    th = np.radians(theta_deg); ct, st = np.cos(th), np.sin(th)
    cx, cy = x + w // 2, y + int(h * 0.56)
    scale = h * 0.40
    def pj(idx):
        px, py, pz = W[idx]
        xr = px * ct + pz * st
        return int(cx + xr * scale), int(cy + py * scale)
    # chao (grade simples)
    for gz in np.linspace(-0.5, 0.5, 5):
        p1 = (-0.6 * ct + gz * st, ground_y_world); p2 = (0.6 * ct + gz * st, ground_y_world)
        cv2.line(cv, (int(cx + p1[0] * scale), int(cy + p1[1] * scale)),
                 (int(cx + p2[0] * scale), int(cy + p1[1] * scale)), COL["grid"], 1)
    for a, b in TRUNK:
        cv2.line(cv, pj(a), pj(b), TR, 2, cv2.LINE_AA)
    for a, b in LEGS2D["L"]:
        cv2.line(cv, pj(a), pj(b), LC, 3, cv2.LINE_AA)
    for a, b in LEGS2D["R"]:
        cv2.line(cv, pj(a), pj(b), RC, 3, cv2.LINE_AA)
    for idx, c in [(31, LC), (32, RC), (27, LC), (28, RC), (25, LC), (26, RC)]:
        cv2.circle(cv, pj(idx), 4, c, -1, cv2.LINE_AA)
    cv2.putText(cv, f"giro {theta_deg:+.0f}", (x + w - 90, y + h - 10), F, 0.36, COL["dim"], 1, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True); ap.add_argument("--pose", required=True)
    ap.add_argument("--out", default="data/legs3d.mp4"); ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--brand", default="De Lucca Esporte")
    args = ap.parse_args()

    P = json.loads(open(args.pose).read()); D = compute(P, args.fps)
    N = P["norm"]; Wd = D["Wd"]; L = D["L"]; n = len(D["t"])
    apex = D["apex"]
    # solo em coordenada world (para o chao do boneco): y do pe em pe (y aponta p/ baixo)
    ground_world = float(np.median(np.maximum(Wd[:int(args.fps), L['foot_l'], 1],
                                              Wd[:int(args.fps), L['foot_r'], 1])))

    cap = cv2.VideoCapture(args.video); srcW, srcH = cap.get(3), cap.get(4)
    CW, CH = 1920, 1080
    vh = CH - 40; vw = int(srcW * vh / srcH); vx, vy = 20, 20
    if vw > CW * 0.32:
        vw = int(CW * 0.32); vh = int(srcH * vw / srcW); vy = (CH - vh) // 2
    writer = cv2.VideoWriter(args.out, cv2.VideoWriter_fourcc(*"mp4v"), args.fps, (CW, CH))
    rpk = lambda a, i: float(np.nanmax(a[:i + 1]))
    rpkabs = lambda a, i: float(np.nanmax(np.abs(a[:i + 1])))

    dx = vx + vw + 20
    s3d = (dx, 60, 430, 430)
    mx0 = dx; my0 = 60 + 430 + 12
    cx0 = dx + 448; cw = CW - cx0 - 18; chh = 232

    for i in range(n):
        ok, fr = cap.read()
        if not ok:
            break
        cv = np.full((CH, CW, 3), COL["bg"], np.uint8)
        cv[vy:vy + vh, vx:vx + vw] = cv2.resize(fr, (vw, vh))
        lm = N[i] if N[i] is not None else N[0]
        draw_2d(cv, lm, vx, vy, vw, vh)
        cv2.rectangle(cv, (vx, vy), (vx + vw, vy + vh), COL["line"], 1)
        cv2.putText(cv, args.brand, (dx, 34), FD, 0.8, COL["accent"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"Analise das 2 pernas  |  t={i/args.fps:4.1f}s", (dx, 52), F, 0.44, COL["dim"], 1, cv2.LINE_AA)

        theta = 40 * np.sin(2 * np.pi * i / n)          # varredura -40..40
        draw_stick3d(cv, s3d, Wd[i], theta, ground_world)

        # metricas por perna
        panel(cv, mx0, my0, 430, CH - my0 - 18)
        cv2.putText(cv, "PICOS POR PERNA (ao vivo)", (mx0 + 10, my0 + 22), F, 0.44, COL["accent"], 1, cv2.LINE_AA)
        rows = [
            ("Joelho E: ext.max", f"{rpk(D['kneeL'],i):.0f} deg (def {180-rpk(D['kneeL'],i):.0f})", LC),
            ("Joelho D: ext.max", f"{rpk(D['kneeR'],i):.0f} deg (def {180-rpk(D['kneeR'],i):.0f})", RC),
            ("Vel.ang joelho E", f"{rpkabs(D['kvL'],i):.0f} /s", LC),
            ("Vel.ang joelho D", f"{rpkabs(D['kvR'],i):.0f} /s", RC),
            ("Acel. joelho E", f"{rpkabs(D['kaL'],i):.0f} /s2", LC),
            ("Acel. joelho D", f"{rpkabs(D['kaR'],i):.0f} /s2", RC),
            ("Altura pe E (max)", f"{rpk(D['hFootL'],i):.0f} cm", LC),
            ("Altura pe D (max)", f"{rpk(D['hFootR'],i):.0f} cm", RC),
        ]
        ry = my0 + 50
        for lbl, val, c in rows:
            cv2.putText(cv, lbl, (mx0 + 14, ry), F, 0.44, COL["dim"], 1, cv2.LINE_AA)
            cv2.putText(cv, val, (mx0 + 220, ry), FD, 0.5, c, 1, cv2.LINE_AA)
            ry += 30
        # altura do quadril ao solo (atual e na max extensao)
        ry += 6
        panel(cv, mx0 + 12, ry, 406, 74, COL["bg"])
        cv2.putText(cv, "ALTURA DO QUADRIL AO SOLO", (mx0 + 22, ry + 22), F, 0.44, COL["dim"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"agora {D['hHip'][i]:.0f} cm", (mx0 + 22, ry + 50), FD, 0.62, COL["txt"], 1, cv2.LINE_AA)
        jh = D['hHip'][apex] if i >= apex else float(np.nanmax(D['hHip'][:i + 1]))
        cv2.putText(cv, f"MAX EXT {jh:.0f} cm", (mx0 + 220, ry + 50), FD, 0.62, COL["accent"], 1, cv2.LINE_AA)

        # graficos (direita)
        y = 60
        chart(cv, (cx0, y, cw, chh), [(D['kneeL'][:n], LC), (D['kneeR'][:n], RC)], i,
              "EXTENSAO DO JOELHO  E x D  (reta = 180)", "deg", hline=180)
        y += chh + 12
        chart(cv, (cx0, y, cw, chh), [(D['kvL'][:n], LC), (D['kvR'][:n], RC)], i,
              "VELOCIDADE ANGULAR DO JOELHO  E x D", "deg/s")
        y += chh + 12
        chart(cv, (cx0, y, cw, chh), [(D['hFootL'][:n], LC), (D['hFootR'][:n], RC)], i,
              "ALTURA DA PONTA DOS PES AO SOLO  E x D", "cm", fill=None)
        y += chh + 12
        chart(cv, (cx0, y, cw, chh), [(D['hHip'][:n], (200, 140, 255))], i,
              "ALTURA DO QUADRIL AO SOLO", "cm", marker=apex, fill=True)

        writer.write(cv)
        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{n} frames")
    writer.release(); cap.release()
    print(f"legs3d: {args.out}  ({n} frames, {n/args.fps:.1f}s)  hip_maxext={D['hHip'][apex]:.0f}cm")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
