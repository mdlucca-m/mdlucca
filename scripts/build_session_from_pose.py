#!/usr/bin/env python3
"""
scripts/build_session_from_pose.py

Transforma os landmarks de pose (pose_extract.py) numa SESSÃO completa no
banco: computa séries cinemáticas a partir dos WORLD landmarks 3D (metros),
estima a cinética pelo método do centro de massa (massa assumida, sem
plataforma de força), segmenta repetições e insere tudo via sql/schema.sql.

Depois disso, TODAS as análises da API (kinematics, biomech, analyses)
rodam sobre a nova sessão.

Uso:
  python3 scripts/build_session_from_pose.py --pose data/pose.json \
      --db data/db.sqlite --athlete "Atleta Vídeo" --mass 80 --append
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np
from scipy import signal as _sig

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import signals as S           # noqa: E402
from app.analyses import DE_LEVA_SEGMENTS  # noqa: E402

G = 9.81

# De Leva por segmento a partir dos world landmarks (bilateral quando aplicavel).
# (chave_De_Leva, indice_proximal, indice_distal, n_lados)
COG = [
    ("head_neck", 0, None, 1),   # nariz como proxy da cabeca (segmento tratado a parte)
    ("trunk", None, None, 1),    # mid-ombro -> mid-quadril (tratado a parte)
    ("upper_arm", 11, 13, 1), ("upper_arm", 12, 14, 1),
    ("forearm_hand", 13, 15, 1), ("forearm_hand", 14, 16, 1),
    ("thigh", 23, 25, 1), ("thigh", 24, 26, 1),
    ("shank_foot", 25, 27, 1), ("shank_foot", 26, 28, 1),
]


def angle(a, b, c):
    """Angulo (graus) no vertice b entre b->a e b->c, por frame. a,b,c: (n,3)."""
    v1, v2 = a - b, c - b
    cos = (v1 * v2).sum(1) / (np.linalg.norm(v1, axis=1) * np.linalg.norm(v2, axis=1) + 1e-9)
    return np.degrees(np.arccos(np.clip(cos, -1, 1)))


def deriv(y, t, w=9):
    return S.derivative(y, t, smooth_window=w)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pose", default="data/pose.json")
    ap.add_argument("--db", default="data/db.sqlite")
    ap.add_argument("--schema", default="sql/schema.sql")
    ap.add_argument("--athlete", default="Atleta Vídeo")
    ap.add_argument("--exercise", default="Landmine Clean & Press (vídeo)")
    ap.add_argument("--mass", type=float, default=80.0, help="massa corporal assumida (kg)")
    ap.add_argument("--append", action="store_true", help="não recria o banco")
    args = ap.parse_args()

    P = json.loads(Path(args.pose).read_text())
    fps = P["fps"]
    Lm = P["landmark_index"]
    world = P["world"]
    norm = P["norm"]
    vis = P["visibility"]
    n = len(world)

    # interpola frames sem pose (linear entre vizinhos) — corrige o antigo
    # bug de repetir o 1o quadro em cada frame faltante.
    n_missing = sum(1 for w in world if w is None)
    W = S.stack_frames(world, (33, 3))
    N = S.stack_frames(norm, (33, 2))
    Vs = np.array([v if v is not None else [0.0] * 33 for v in vis], dtype=float)
    if n_missing:
        print(f"Quadros sem pose interpolados: {n_missing}/{n}")
    t = np.arange(n) / fps

    up = lambda idx: -W[:, idx, 1]                 # vertical (m), para cima positivo
    pt = lambda idx: W[:, idx]                      # ponto 3D (n,3)

    # --- angulos 3D (lado esquerdo, camera-facing) ------------------------
    ang = {
        "hip_angle": angle(pt(11), pt(23), pt(25)),
        "knee_angle": angle(pt(23), pt(25), pt(27)),
        "elbow_angle": angle(pt(11), pt(13), pt(15)),
        "ankle_angle": angle(pt(25), pt(27), pt(31)),
        "shoulder_angle": angle(pt(13), pt(11), pt(23)),
    }
    for k in list(ang):
        ang[k] = S.savgol(ang[k], 11, 3)

    smooth3 = lambda a: _sig.savgol_filter(a, 11, 3, axis=0)  # suaviza no tempo (eixo 0)

    # --- barra (punho esquerdo) ------------------------------------------
    wr = pt(15)
    bar_speed = np.linalg.norm(np.gradient(smooth3(wr), t, axis=0), axis=1)
    bar_accel = deriv(bar_speed, t, 11)
    bar_up = up(15)
    hip_up = up(23)
    bar_h_rel_hip = bar_up - hip_up

    # --- centro de massa (De Leva, world 3D) ------------------------------
    seg_c, seg_w = [], []
    head = (pt(7) + pt(8)) / 2
    msh = (pt(11) + pt(12)) / 2
    mhip = (pt(23) + pt(24)) / 2
    seg_c.append(head + DE_LEVA_SEGMENTS["head_neck"]["cog_frac"] * (msh - head)); seg_w.append(DE_LEVA_SEGMENTS["head_neck"]["mass_frac"])
    seg_c.append(msh + DE_LEVA_SEGMENTS["trunk"]["cog_frac"] * (mhip - msh)); seg_w.append(DE_LEVA_SEGMENTS["trunk"]["mass_frac"])
    for key, pi, di, _ in COG:
        if pi is None or di is None:
            continue
        f = DE_LEVA_SEGMENTS[key]["cog_frac"]
        seg_c.append(pt(pi) + f * (pt(di) - pt(pi))); seg_w.append(DE_LEVA_SEGMENTS[key]["mass_frac"])
    w = np.array(seg_w); w = w / w.sum()
    com = np.tensordot(w, np.stack(seg_c), axes=(0, 0))  # (n,3)
    cog_up = -com[:, 1]
    cog_speed = np.linalg.norm(np.gradient(smooth3(com), t, axis=0), axis=1)

    # --- cinetica ESTIMADA pelo metodo do CoM (massa assumida) ------------
    a_com_v = deriv(np.gradient(S.savgol(cog_up, 15, 3), t), t, 15)  # acel vertical do CoM
    v_com_v = np.gradient(S.savgol(cog_up, 15, 3), t)
    force = args.mass * (a_com_v + G)              # GRF vertical estimada (N)
    force = np.clip(force, 0, None)
    power = force * v_com_v
    force_grav = np.full(n, args.mass * G)
    force_dyn = args.mass * a_com_v
    tang_accel = bar_accel

    # velocidades angulares/aceleracoes
    series = {"t": t}
    series.update(ang)
    for j in ("hip", "knee", "elbow", "ankle"):
        series[f"{j}_angvel"] = deriv(ang[f"{j}_angle"], t, 9)
        series[f"{j}_aa"] = deriv(series[f"{j}_angvel"], t, 11)
    series["wrist_angvel"] = deriv(angle(pt(13), pt(15), pt(19)), t, 9)
    series.update({
        "speed": bar_speed, "accel": bar_accel, "tangential_accel": tang_accel,
        "propulsive_velocity": np.clip(bar_speed, 0, None),
        "force": force, "power": power, "force_gravity": force_grav, "force_dynamic": force_dyn,
        "cog_y": cog_up - cog_up.min(), "cog_speed": cog_speed,
        "bar_height_rel_hip": bar_h_rel_hip, "body_speed": cog_speed,
        "rfd": deriv(force, t, 11),
    })

    # --- segmentacao de repeticoes pela altura da barra -------------------
    bh = S.savgol(bar_up, 15, 3)
    prom = (bh.max() - bh.min()) * 0.35
    peaks, _ = _sig.find_peaks(bh, prominence=prom, distance=int(fps * 1.0))
    # vales entre picos = fronteiras
    bounds = [0]
    for i in range(len(peaks) - 1):
        seg = bh[peaks[i]:peaks[i + 1]]
        bounds.append(peaks[i] + int(np.argmin(seg)))
    bounds.append(n - 1)
    reps = [(bounds[i], bounds[i + 1]) for i in range(len(bounds) - 1)]
    reps = [(a, b) for a, b in reps if b - a > int(fps * 0.6)]
    if not reps:
        reps = [(0, n - 1)]
    print(f"Repeticoes detectadas: {len(reps)} (picos de barra: {len(peaks)})")

    # --- monta submovimentos ----------------------------------------------
    def slice_series(a, b):
        out = {}
        for k, arr in series.items():
            out[k] = [round(float(x), 4) for x in np.asarray(arr)[a:b + 1]]
        return out

    efforts = []
    for i, (a, b) in enumerate(reps, 1):
        a, b = int(a), int(b)
        ss = slice_series(a, b)
        efforts.append({"ordinal": i, "label": f"Rep {i}", "kind": "pull",
                        "frame_start": a, "frame_end": b, "n_frames": b - a + 1,
                        "dt": 1.0 / fps, "series": ss})
    # composto (movimento inteiro)
    ss = slice_series(0, n - 1)
    efforts.append({"ordinal": len(reps) + 1, "label": "Sessão completa", "kind": "composite",
                    "frame_start": 0, "frame_end": int(n - 1), "n_frames": int(n), "dt": 1.0 / fps, "series": ss})

    # esqueleto (norm 2D esquerdo) para o endpoint de cinematica (aspect=1, video quadrado)
    def sk_lm(idx_l): return [[round(float(N[f, idx_l, 0]), 4), round(float(N[f, idx_l, 1]), 4)] for f in range(n)]
    skeleton_full = {"ear": sk_lm(7), "sh": sk_lm(11), "el": sk_lm(13), "wr": sk_lm(15),
                     "hip": sk_lm(23), "kn": sk_lm(25), "an": sk_lm(27), "idx_finger": sk_lm(19)}

    # confianca por articulacao (visibilidade media)
    conf = {}
    idxmap = {"ear": 7, "sh": 11, "el": 13, "wr": 15, "hip": 23, "kn": 25, "an": 27}
    for name, idx in idxmap.items():
        conf[name] = {"mean": round(float(Vs[:, idx].mean()), 4),
                      "min": round(float(Vs[:, idx].min()), 4),
                      "pct_low_confidence": round(float(100 * (Vs[:, idx] < 0.5).mean()), 1)}

    # --- insere no banco ---------------------------------------------------
    dbp = Path(args.db)
    con = sqlite3.connect(dbp)
    con.execute("PRAGMA foreign_keys=ON")
    if not args.append:
        con.executescript(Path(args.schema).read_text())
    cur = con.cursor()

    # ext_key unico por atleta de video (evita colisao ao anexar varios videos)
    ext_key = "video_" + re.sub(r"[^a-z0-9]+", "_", args.athlete.lower()).strip("_")
    if cur.execute("SELECT 1 FROM athlete WHERE ext_key=?", (ext_key,)).fetchone():
        ext_key = f"{ext_key}_{Path(args.pose).stem}"
    cur.execute("INSERT INTO athlete(ext_key,name,body_mass_kg,notes) VALUES (?,?,?,?)",
                (ext_key, args.athlete, args.mass,
                 "massa corporal ASSUMIDA (sem balança); cinética estimada pelo método do CoM"))
    athlete_id = cur.lastrowid
    meta = {"source_video": "VID_39550929_221256_717.mkv", "fps": fps,
            "resolution": f"{P['width']}x{P['height']}", "pose_detected_frames": P["detected"],
            "side_used": "left (maior visibilidade)", "kinetics": "estimada (metodo CoM, massa assumida)",
            "is_calibrated": False, "coordinate_system": "metric_3d (world landmarks MediaPipe)"}
    cur.execute("""INSERT INTO session(athlete_id,exercise,load_kg,gravity,pose_source,pose_model,
                     n_submovements,meta,notes) VALUES (?,?,?,?,?,?,?,?,?)""",
                (athlete_id, args.exercise, None, G, "mediapipe",
                 "MediaPipe PoseLandmarker (BlazePose GHUM 3D, world landmarks)",
                 len(efforts), json.dumps(meta, ensure_ascii=False),
                 "Sessão derivada de vídeo real via pipeline pose->biomecânica."))
    session_id = cur.lastrowid

    sub_ids = {}
    for e in efforts:
        cur.execute("""INSERT INTO submovement(session_id,ordinal,label,kind,frame_start,frame_end,
                        n_frames,dt) VALUES (?,?,?,?,?,?,?,?)""",
                    (session_id, e["ordinal"], e["label"], e["kind"], e["frame_start"],
                     e["frame_end"], e["n_frames"], e["dt"]))
        sid = cur.lastrowid; sub_ids[e["ordinal"]] = sid
        units = {"t": "s", "speed": "m/s", "accel": "m/s^2", "force": "N", "power": "W",
                 "cog_y": "m", "cog_speed": "m/s", "bar_height_rel_hip": "m", "rfd": "N/s"}
        for k, arr in e["series"].items():
            u = units.get(k, "deg" if "angle" in k else ("deg/s" if "angvel" in k else
                          ("deg/s^2" if k.endswith("_aa") else ("N" if "force" in k else None))))
            cur.execute("INSERT INTO series(submovement_id,name,unit,n,samples) VALUES (?,?,?,?,?)",
                        (sid, k, u, len(arr), json.dumps(arr)))
        # peaks
        arrf = np.asarray(e["series"]["force"]); arrp = np.asarray(e["series"]["power"])
        pk = {"F_peak": float(arrf.max()), "P_peak": float(arrp.max()),
              "v_peak": float(np.asarray(e["series"]["speed"]).max()),
              "hip_min": float(np.asarray(e["series"]["hip_angle"]).min()),
              "hip_max": float(np.asarray(e["series"]["hip_angle"]).max())}
        for name, v in pk.items():
            cur.execute("INSERT INTO metric(session_id,submovement_id,analysis,name,value_num) VALUES (?,?,?,?,?)",
                        (session_id, sid, "peaks", name, v))

    # skeleton por rep (fatia)
    for e in efforts:
        a, b = e["frame_start"], e["frame_end"]
        sk = {k: v[a:b + 1] for k, v in skeleton_full.items()}
        cur.execute("INSERT INTO dataset(session_id,submovement_id,kind,name,payload) VALUES (?,?,?,?,?)",
                    (session_id, sub_ids[e["ordinal"]], "skeleton", "skeleton", json.dumps(sk)))
        for name, c in conf.items():
            cur.execute("INSERT INTO joint_confidence(submovement_id,joint,mean_vis,min_vis,pct_low_confidence) VALUES (?,?,?,?,?)",
                        (sub_ids[e["ordinal"]], name, c["mean"], c["min"], c["pct_low_confidence"]))

    # global kpis
    gk = {"peak_force": float(np.asarray(series["force"]).max()),
          "peak_power": float(np.asarray(series["power"]).max()),
          "peak_speed": float(np.asarray(series["speed"]).max()),
          "n_efforts": len(reps)}
    for k, v in gk.items():
        cur.execute("INSERT INTO metric(session_id,submovement_id,analysis,name,value_num) VALUES (?,?,?,?,?)",
                    (session_id, None, "global_kpi", k, v))

    con.commit()
    print(f"Sessão inserida: id={session_id}  ({len(efforts)} submovimentos)  athlete_id={athlete_id}")
    print("submovimentos:", sub_ids)
    con.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
