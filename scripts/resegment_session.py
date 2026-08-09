#!/usr/bin/env python3
"""
resegment_session.py — re-segmenta as repeticoes de uma sessao pela regra
DE PE -> DE PE (extensao a extensao), usando app.phases.segment_cycles.

A subida inicial (chao/agachado ate a 1a extensao) NAO e contada como rep
(vira "entrada/setup"); a descida final vira "saida". Atualiza o banco:
apaga os submovimentos 'Rep%' antigos (e suas metricas) e cria os novos, com
os picos basicos (forca/potencia/velocidade/vel.ang do quadril) por rep.

Uso:
    python3 scripts/resegment_session.py --session 16 --primary hip_angle
"""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT))
from app import phases as Ph  # noqa: E402

PEAKS = [("force", "F_peak"), ("power", "power_peak"), ("speed", "v_peak"),
         ("hip_angvel", "hip_angvel_peak"), ("knee_angvel", "knee_angvel_peak")]


def _ser(con, sub, name):
    r = con.execute("SELECT samples FROM series WHERE submovement_id=? AND name=?",
                    (sub, name)).fetchone()
    return np.array(json.loads(r[0]), float) if r else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--session", type=int, required=True)
    ap.add_argument("--primary", default="hip_angle")
    ap.add_argument("--stand-frac", type=float, default=0.85)
    ap.add_argument("--bottom-frac", type=float, default=0.60)
    args = ap.parse_args()

    con = sqlite3.connect(str(ROOT / "data" / "db.sqlite"))
    con.execute("PRAGMA foreign_keys=ON")
    subs = con.execute("SELECT id,label,n_frames FROM submovement WHERE session_id=? "
                       "ORDER BY ordinal", (args.session,)).fetchall()
    if not subs:
        raise SystemExit("sessao sem submovimentos")
    full = max(subs, key=lambda r: r[2])
    prim = _ser(con, full[0], args.primary)
    if prim is None:
        raise SystemExit(f"serie '{args.primary}' inexistente no submov {full[0]}")

    seg = Ph.segment_cycles(prim, stand_frac=args.stand_frac, bottom_frac=args.bottom_frac)
    reps = seg["reps"]
    if not reps:
        raise SystemExit("nenhum ciclo de-pe->de-pe detectado")

    dt = float(np.median(np.gradient(_ser(con, full[0], "t"))))
    # apaga reps antigas (mantem o submov 'completo')
    old = [r[0] for r in subs if r[0] != full[0] and str(r[1]).lower().startswith("rep")]
    for oid in old:
        con.execute("DELETE FROM metric WHERE submovement_id=?", (oid,))
        con.execute("DELETE FROM share WHERE kind='submovement' AND ref_id=?", (oid,))
        con.execute("DELETE FROM submovement WHERE id=?", (oid,))

    base_ord = 0
    created = []
    for i, (a, b) in enumerate(reps, 1):
        nf = b - a + 1
        cur = con.execute(
            "INSERT INTO submovement (session_id,ordinal,label,kind,frame_start,"
            "frame_end,n_frames,dt,is_slowmo_2x) VALUES (?,?,?,?,?,?,?,?,0)",
            (args.session, base_ord + i, f"Rep {i}", "composite", a, b, nf, dt))
        sid = cur.lastrowid
        created.append((sid, i, a, b))
        for sname, mname in PEAKS:
            s = _ser(con, full[0], sname)
            if s is None:
                continue
            val = float(np.max(np.abs(s[a:b + 1]))) if sname != "power" \
                else float(np.max(s[a:b + 1]))
            con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,"
                        "value_num,unit) VALUES (?,?,?,?,?,?)",
                        (args.session, sid, "peaks", mname, round(val, 2),
                         {"force": "N", "power": "W", "speed": "m/s"}.get(sname, "deg/s")))
    con.execute("UPDATE session SET n_submovements=? WHERE id=?",
                (len(created) + 1, args.session))
    con.commit()

    t = _ser(con, full[0], "t")
    print(f"[ok] sessao {args.session}: {len(reps)} reps (de pe -> de pe)")
    if seg["entry"]:
        e = seg["entry"]; print(f"  entrada (setup, nao contada): f{e[0]}->{e[1]} "
                                f"t{t[e[0]]:.1f}->{t[e[1]]:.1f}s")
    for sid, i, a, b in created:
        bottom = a + int(np.argmin(Ph.S.savgol(_ser(con, full[0], args.primary))[a:b + 1]))
        print(f"  Rep {i}: f{a}->{b}  t{t[a]:.1f}->{t[b]:.1f}s  fundo t{t[bottom]:.1f}s")
    if seg["exit"]:
        x = seg["exit"]; print(f"  saida (nao contada): f{x[0]}->{x[1]} "
                               f"t{t[x[0]]:.1f}->{t[x[1]]:.1f}s")
    con.close()


if __name__ == "__main__":
    main()
