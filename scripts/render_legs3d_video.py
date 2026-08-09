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

import sys
from pathlib import Path

import cv2
import numpy as np
from scipy import signal as _sig

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import segments as Seg  # noqa: E402

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


def compute(P, fps, stature_m=None):
    L = P["landmark_index"]; Wpx, Hpx = P["width"], P["height"]
    N = np.array([x if x is not None else P["norm"][0] for x in P["norm"]], float)
    Wd = np.array([w if w is not None else P["world"][0] for w in P["world"]], float)
    t = np.arange(len(N)) / fps

    def ang(a, b, c):
        v1 = Wd[:, a] - Wd[:, b]; v2 = Wd[:, c] - Wd[:, b]
        cs = (v1 * v2).sum(1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-9)
        return smf(np.degrees(np.arccos(np.clip(cs, -1, 1))))

    kneeL = ang(L['hip_l'], L['kn_l'], L['an_l']); kneeR = ang(L['hip_r'], L['kn_r'], L['an_r'])
    # angulo de abertura da passada (split): entre as duas pernas, no quadril
    hipm = (Wd[:, L['hip_l']] + Wd[:, L['hip_r']]) / 2
    vL = Wd[:, L['an_l']] - hipm; vR = Wd[:, L['an_r']] - hipm
    cs = (vL * vR).sum(1) / (np.linalg.norm(vL, axis=1) * np.linalg.norm(vR, axis=1) + 1e-9)
    split = smf(np.degrees(np.arccos(np.clip(cs, -1, 1))))
    def dd(a):
        v = np.gradient(a, t); ac = np.gradient(smf(v), t); return v, ac
    kvL, kaL = dd(kneeL); kvR, kaR = dd(kneeR)
    stand = slice(0, int(fps * 1.2))
    trunk_m = np.median(np.linalg.norm(((Wd[:, L['sh_l']] + Wd[:, L['sh_r']]) / 2)
                                       - ((Wd[:, L['hip_l']] + Wd[:, L['hip_r']]) / 2), axis=1)[stand])
    sh_y = (N[:, L['sh_l'], 1] + N[:, L['sh_r'], 1]) / 2 * Hpx
    hip_y = (N[:, L['hip_l'], 1] + N[:, L['hip_r'], 1]) / 2 * Hpx
    mpp = trunk_m / (np.median(np.abs(sh_y - hip_y)[stand]) or 1)
    calib_src = "trunk_estimate"
    if stature_m:                       # calibracao por estatura real (nariz->tornozelo)
        nose_y = N[:, 0, 1] * Hpx
        ank_y = (N[:, L['an_l'], 1] + N[:, L['an_r'], 1]) / 2 * Hpx
        px = np.median(np.abs(ank_y - nose_y)[stand]) or 1
        mpp = (stature_m * 0.936) / px
        calib_src = f"stature {stature_m:.2f}m"
    footL_y = N[:, L['foot_l'], 1] * Hpx; footR_y = N[:, L['foot_r'], 1] * Hpx
    ground = np.median(np.maximum(footL_y, footR_y)[stand])
    hFootL = (ground - smf(footL_y)) * mpp * 100
    hFootR = (ground - smf(footR_y)) * mpp * 100
    hHip = (ground - smf(hip_y)) * mpp * 100
    win = slice(int(fps * 3.5), int(fps * 8.5))
    apex = win.start + int(np.argmax(hHip[win]))
    return dict(N=N, Wd=Wd, L=L, t=t, kneeL=kneeL, kneeR=kneeR, kvL=kvL, kvR=kvR,
                kaL=kaL, kaR=kaR, hFootL=hFootL, hFootR=hFootR, hHip=hHip, split=split,
                apex=apex, hip_stand=float(np.median(hHip[stand])),
                ground_px=float(ground), Hpx=Hpx, Wpx=Wpx, mpp=mpp, calib_src=calib_src)


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
SEG_COLOR = {"perna_E": LC, "perna_D": RC, "tronco": TR, "cabeca": TR,
             "braco_E": (120, 200, 255), "braco_D": (200, 140, 255)}


def build_bones(spec):
    """(bones_com_cor, pontos, tem_pernas) a partir da selecao de segmentos."""
    sel = Seg.resolve(spec or "sem_bracos")
    bones = []
    for name in sel["segments"]:
        col = SEG_COLOR.get(name, TR)
        for (a, b) in Seg.SEGMENTS[name]["bones"]:
            if a <= 32 and b <= 32:
                bones.append(((a, b), col))
    has_legs = ("perna_E" in sel["segments"]) or ("perna_D" in sel["segments"])
    return bones, sel["points"], has_legs, sel["segments"]


def draw_2d(cv, lm, vx, vy, vw, vh, bones, points):
    sp = lambda p: (int(vx + p[0] * vw), int(vy + p[1] * vh))
    for (a, b), col in bones:
        w = 4 if col in (LC, RC) else 2
        cv2.line(cv, sp(lm[a]), sp(lm[b]), col, w, cv2.LINE_AA)
    for idx in points:
        cv2.circle(cv, sp(lm[idx]), 4, (255, 255, 255), -1, cv2.LINE_AA)


def draw_rulers(cv, lm, vx, vy, vw, vh, ground_ny, hFL, hFR, hHip):
    """Reta que mede a altura em tempo real: solo -> ponta de cada pe (E/D)."""
    sp = lambda p: (int(vx + p[0] * vw), int(vy + p[1] * vh))
    gy = int(vy + ground_ny * vh)
    cv2.line(cv, (vx, gy), (vx + vw, gy), (110, 110, 140), 1, cv2.LINE_AA)   # solo
    cv2.putText(cv, "solo", (vx + 6, gy - 6), F, 0.42, (140, 140, 165), 1, cv2.LINE_AA)
    for idx, val, col, tag in [(31, hFL, LC, "E"), (32, hFR, RC, "D")]:
        fx, fy = sp(lm[idx]); fx = max(vx + 2, min(fx, vx + vw - 2))
        cv2.line(cv, (fx, gy), (fx, fy), col, 2, cv2.LINE_AA)               # reta vertical
        for yy in range(min(fy, gy), gy, 20):                               # tracinhos da regua
            cv2.line(cv, (fx - 4, yy), (fx + 4, yy), col, 1, cv2.LINE_AA)
        cv2.circle(cv, (fx, fy), 4, col, -1, cv2.LINE_AA)
        lx = max(vx + 4, min(fx + 8, vx + vw - 118))                        # rotulo dentro do quadro
        cv2.putText(cv, f"{tag} {val:.0f} cm", (lx, max(fy - 4, vy + 18)), FD, 0.6, col, 2, cv2.LINE_AA)
    # altura do quadril (salto) — linha de referencia pontilhada
    hx, hy = sp(lm[23])
    for yy in range(min(hy, gy), gy, 12):
        cv2.line(cv, (hx, yy), (hx, yy + 5), (200, 140, 255), 1, cv2.LINE_AA)
    cv2.putText(cv, f"quadril {hHip:.0f} cm", (hx + 8, hy - 4), FD, 0.55, (200, 140, 255), 1, cv2.LINE_AA)


def draw_stick3d(cv, rect, W, theta_deg, ground_y_world, split_deg, hFootL, hFootR,
                 bones, points, has_legs, elev_deg=20.0):
    x, y, w, h = rect; panel(cv, x, y, w, h)
    cv2.putText(cv, "BONECO 3D 360  (E=ciano  D=magenta)", (x + 10, y + 18), F, 0.42, COL["dim"], 1, cv2.LINE_AA)
    th = np.radians(theta_deg); ct, st = np.cos(th), np.sin(th)
    ph = np.radians(elev_deg); cp, sp2 = np.cos(ph), np.sin(ph)
    cx, cy = x + w // 2, y + int(h * 0.54)
    scale = h * 0.40

    def proj(px, py, pz):
        xr = px * ct + pz * st          # azimute (giro em torno da vertical)
        zr = -px * st + pz * ct
        yr = py * cp - zr * sp2         # elevacao (inclina p/ visao 3/4)
        return int(cx + xr * scale), int(cy + yr * scale)

    def pj(idx):
        return proj(*W[idx])
    # chao (grade que gira junto, com elevacao)
    for gz in np.linspace(-0.5, 0.5, 5):
        p1 = proj(-0.6, ground_y_world, gz); p2 = proj(0.6, ground_y_world, gz)
        cv2.line(cv, p1, p2, COL["grid"], 1)
    for gx in np.linspace(-0.5, 0.5, 5):
        p1 = proj(gx, ground_y_world, -0.5); p2 = proj(gx, ground_y_world, 0.5)
        cv2.line(cv, p1, p2, COL["grid"], 1)
    hipm = (int((pj(23)[0] + pj(24)[0]) / 2), int((pj(23)[1] + pj(24)[1]) / 2))
    if has_legs:
        # retas de altura (solo -> ponta do pe) no 3D, por perna
        for idx, hc, col in [(31, hFootL, LC), (32, hFootR, RC)]:
            fx, fy, fz = W[idx]
            top = proj(fx, fy, fz); base = proj(fx, ground_y_world, fz)
            cv2.line(cv, base, top, col, 1, cv2.LINE_AA)
            cv2.putText(cv, f"{hc:.0f}cm", (top[0] + 4, top[1] - 2), F, 0.34, col, 1, cv2.LINE_AA)
        # base do 'triangulo' da passada + abertura
        aL, aR = pj(27), pj(28)
        cv2.line(cv, aL, aR, (110, 110, 150), 1, cv2.LINE_AA)
        cv2.line(cv, hipm, aL, (110, 110, 150), 1, cv2.LINE_AA)
        cv2.line(cv, hipm, aR, (110, 110, 150), 1, cv2.LINE_AA)
        cv2.putText(cv, f"abertura {split_deg:.0f} deg", (hipm[0] - 40, hipm[1] - 8), F, 0.42, COL["accent"], 1, cv2.LINE_AA)
    for (a, b), col in bones:
        cv2.line(cv, pj(a), pj(b), col, 3, cv2.LINE_AA)
    for idx in points:
        cv2.circle(cv, pj(idx), 4, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.putText(cv, f"giro {theta_deg:03.0f}", (x + w - 90, y + h - 10), F, 0.36, COL["dim"], 1, cv2.LINE_AA)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True); ap.add_argument("--pose", required=True)
    ap.add_argument("--out", default="data/legs3d.mp4"); ap.add_argument("--fps", type=float, default=25.0)
    ap.add_argument("--brand", default="De Lucca Esporte")
    ap.add_argument("--stature", type=float, default=None, help="estatura real do atleta (m) p/ calibrar")
    ap.add_argument("--segments", default="sem_bracos",
                    help="segmentos a desenhar: grupo (all|sem_bracos|pernas|bracos) ou lista")
    args = ap.parse_args()

    bones, points, has_legs, seg_names = build_bones(args.segments)
    P = json.loads(open(args.pose).read()); D = compute(P, args.fps, stature_m=args.stature)
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
    cx0 = dx + 448; cw = CW - cx0 - 18; chh = 185; cgap = 10
    rot_period_s = 6.0                                  # 1 volta a cada 6 s

    for i in range(n):
        ok, fr = cap.read()
        if not ok:
            break
        cv = np.full((CH, CW, 3), COL["bg"], np.uint8)
        cv[vy:vy + vh, vx:vx + vw] = cv2.resize(fr, (vw, vh))
        lm = N[i] if N[i] is not None else N[0]
        draw_2d(cv, lm, vx, vy, vw, vh, bones, points)
        draw_rulers(cv, lm, vx, vy, vw, vh, D['ground_px'] / D['Hpx'],
                    D['hFootL'][i], D['hFootR'][i], D['hHip'][i])
        cv2.rectangle(cv, (vx, vy), (vx + vw, vy + vh), COL["line"], 1)
        cv2.putText(cv, args.brand, (dx, 34), FD, 0.8, COL["accent"], 1, cv2.LINE_AA)
        cv2.putText(cv, f"Analise das 2 pernas  |  t={i/args.fps:4.1f}s  |  escala: {D['calib_src']}",
                    (dx, 52), F, 0.44, COL["dim"], 1, cv2.LINE_AA)

        theta = (i * 360.0 / (rot_period_s * args.fps)) % 360   # rotacao continua 360
        draw_stick3d(cv, s3d, Wd[i], theta, ground_world, D['split'][i],
                     D['hFootL'][i], D['hFootR'][i], bones, points, has_legs, elev_deg=20.0)

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
            ("Abertura passada max", f"{rpk(D['split'],i):.0f} deg (def {180-rpk(D['split'],i):.0f})", COL["accent"]),
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
        y += chh + cgap
        chart(cv, (cx0, y, cw, chh), [(D['split'][:n], COL["accent"])], i,
              "ANGULO DE ABERTURA DA PASSADA (split)  (espacate = 180)", "deg", hline=180, marker=apex)
        y += chh + cgap
        chart(cv, (cx0, y, cw, chh), [(D['kvL'][:n], LC), (D['kvR'][:n], RC)], i,
              "VELOCIDADE ANGULAR DO JOELHO  E x D", "deg/s")
        y += chh + cgap
        chart(cv, (cx0, y, cw, chh), [(D['hFootL'][:n], LC), (D['hFootR'][:n], RC)], i,
              "ALTURA DA PONTA DOS PES AO SOLO  E x D", "cm")
        y += chh + cgap
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
