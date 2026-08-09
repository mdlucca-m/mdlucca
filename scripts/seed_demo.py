#!/usr/bin/env python3
"""
seed_demo.py — gera MASSA DE TESTE (dados ficticios) para exercitar o sistema
e o gerador de relatorio de ponta a ponta, sem depender de video/pose.

Cria atletas ficticios (ext_key 'demo'), uma sessao por atleta com varias
repeticoes e um conjunto realista de metricas por repeticao (potencia, forca,
velocidade, RFD, velocidade angular, impulso...). Opcionalmente ja gera os
LINKS compartilhaveis de cada sessao.

Uso:
    python3 scripts/seed_demo.py --db data/db.sqlite --reset
    python3 scripts/seed_demo.py --db data/db.sqlite --athletes 5 --reps 5 --shares

Determinista (seed fixo) — mesma massa de teste a cada execucao.
"""
from __future__ import annotations

import argparse
import random
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DEMO_KEY = "demo"          # prefixo dos ext_key (cada atleta: demo-0, demo-1, ...)
DEMO_LIKE = "demo-%"

_NAMES = [
    ("Ana Ribeiro", "F", 62.0, 1.66),
    ("Bruno Carvalho", "M", 84.0, 1.82),
    ("Carla Menezes", "F", 58.5, 1.60),
    ("Diego Fontes", "M", 91.0, 1.88),
    ("Eduarda Lima", "F", 68.0, 1.72),
    ("Felipe Souza", "M", 78.0, 1.79),
]
_EXERCISES = ["Agachamento", "Levantamento Terra", "Landmine Clean & Press",
              "Salto Vertical", "Supino"]

# (analysis, name, unit, base p/ 80 kg, fator de dispersao)
_METRIC_SPEC = [
    ("peaks", "power_peak", "W", 2200.0, 0.18),
    ("peaks", "F_peak", "N", 1600.0, 0.15),
    ("peaks", "v_peak", "m/s", 2.4, 0.20),
    ("peaks", "RFD_peak", "N/s", 6000.0, 0.30),
    ("peaks", "hip_angvel_peak", "deg/s", 340.0, 0.20),
    ("peaks", "a_peak", "m/s2", 18.0, 0.20),
    ("ballistic", "impulso_propulsivo", "N.s", 260.0, 0.15),
    ("moments", "tau_hip", "N.m", 300.0, 0.18),
    ("moments", "tau_knee", "N.m", 900.0, 0.20),
    ("joint_power", "hip.work_pos", "J", 420.0, 0.20),
    ("ssc", "rsi_modificado", "", 0.55, 0.22),
    ("vbt", "MPV", "m/s", 0.9, 0.18),
]


def _bmi(mass, height):
    return round(mass / (height * height), 1) if mass and height else None


def clear_demo(con: sqlite3.Connection) -> int:
    """Remove toda a massa de teste anterior (atletas demo e cascata)."""
    ids = [r[0] for r in con.execute(
        "SELECT id FROM athlete WHERE ext_key LIKE ?", (DEMO_LIKE,))]
    for aid in ids:
        sids = [r[0] for r in con.execute(
            "SELECT id FROM session WHERE athlete_id=?", (aid,))]
        for sid in sids:
            sub = [r[0] for r in con.execute(
                "SELECT id FROM submovement WHERE session_id=?", (sid,))]
            if sub:
                q = ",".join("?" * len(sub))
                con.execute(f"DELETE FROM metric WHERE submovement_id IN ({q})", sub)
                con.execute(f"DELETE FROM share WHERE kind='submovement' "
                            f"AND ref_id IN ({q})", sub)
            con.execute("DELETE FROM submovement WHERE session_id=?", (sid,))
            con.execute("DELETE FROM share WHERE kind='session' AND ref_id=?", (sid,))
            con.execute("DELETE FROM metric WHERE session_id=?", (sid,))
        con.execute("DELETE FROM session WHERE athlete_id=?", (aid,))
    con.execute("DELETE FROM athlete WHERE ext_key LIKE ?", (DEMO_LIKE,))
    con.commit()
    return len(ids)


def _ensure_share_table(con: sqlite3.Connection) -> None:
    con.executescript(
        "CREATE TABLE IF NOT EXISTS share (token TEXT PRIMARY KEY, kind TEXT NOT NULL,"
        " ref_id INTEGER NOT NULL, title TEXT, audience TEXT, created_at TEXT NOT NULL,"
        " views INTEGER NOT NULL DEFAULT 0);")
    con.commit()


def seed(con: sqlite3.Connection, n_athletes: int = 4, n_reps: int = 5,
         make_shares: bool = False, seed_val: int = 42) -> list[dict]:
    """Popula o banco com massa de teste. Devolve resumo por sessao."""
    rng = random.Random(seed_val)
    _ensure_share_table(con)
    now = datetime.now(timezone.utc).isoformat()
    out = []
    for i in range(min(n_athletes, len(_NAMES))):
        name, sex, mass, height = _NAMES[i]
        cur = con.execute(
            "INSERT INTO athlete (ext_key,name,body_mass_kg,height_m,bmi,sex,notes) "
            "VALUES (?,?,?,?,?,?,?)",
            (f"{DEMO_KEY}-{i}", name, mass, height, _bmi(mass, height), sex,
             "massa de teste"))
        aid = cur.lastrowid
        exercise = _EXERCISES[i % len(_EXERCISES)]
        load = round(rng.uniform(0.6, 1.4) * mass, 1)
        cur = con.execute(
            "INSERT INTO session (athlete_id,exercise,load_kg,pct_bodyweight,gravity,"
            "pose_source,pose_model,n_submovements,captured_at,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (aid, exercise, load, round(100 * load / mass, 1), 9.81, "demo",
             "massa de teste (sintetica)", n_reps, now, "gerada por seed_demo.py"))
        sid = cur.lastrowid
        scale = mass / 80.0                       # metricas escalam com a massa
        for r in range(n_reps):
            fatigue = 1.0 - 0.04 * r               # leve queda a cada rep
            nfr = rng.randint(90, 260)
            sub = con.execute(
                "INSERT INTO submovement (session_id,ordinal,label,kind,frame_start,"
                "frame_end,n_frames,dt,is_slowmo_2x) VALUES (?,?,?,?,?,?,?,?,0)",
                (sid, r + 1, f"Rep {r + 1}", "composite", 0, nfr, nfr, 0.02))
            sub_id = sub.lastrowid
            for ns, nm, unit, base, disp in _METRIC_SPEC:
                val = base * scale * fatigue * (1 + rng.uniform(-disp, disp) * 0.5)
                con.execute(
                    "INSERT INTO metric (session_id,submovement_id,analysis,name,"
                    "value_num,unit) VALUES (?,?,?,?,?,?)",
                    (sid, sub_id, ns, nm, round(val, 2), unit))
        rec = {"athlete_id": aid, "athlete": name, "session_id": sid,
               "exercise": exercise, "reps": n_reps}
        if make_shares:
            tok = secrets.token_urlsafe(8)
            con.execute(
                "INSERT INTO share (token,kind,ref_id,title,audience,created_at,views) "
                "VALUES (?,?,?,?,?,?,0)",
                (tok, "session", sid, exercise, "ambos", now))
            rec["report_url"] = f"/r/{tok}"
        out.append(rec)

    # Atleta extra para TESTE DE CARGAS (varias cargas -> perfil F-V-P)
    lt = con.execute(
        "INSERT INTO athlete (ext_key,name,body_mass_kg,height_m,bmi,sex,notes) "
        "VALUES (?,?,?,?,?,?,?)",
        (f"{DEMO_KEY}-lt", "Teste de Cargas - Demo", 85.0, 1.80,
         _bmi(85.0, 1.80), "M", "massa de teste (perfil F-V)"))
    lt_id = lt.lastrowid
    for k, load in enumerate([40.0, 55.0, 70.0, 85.0, 100.0]):
        mpv = round(1.30 - 0.010 * load + rng.uniform(-0.02, 0.02), 3)   # cai com a carga
        cur = con.execute(
            "INSERT INTO session (athlete_id,exercise,load_kg,pct_bodyweight,gravity,"
            "pose_source,pose_model,n_submovements,captured_at,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (lt_id, "Agachamento", load, round(100 * load / 85.0, 1), 9.81, "demo",
             "massa de teste (sintetica)", 1, now, "teste de cargas"))
        sid = cur.lastrowid
        sub = con.execute(
            "INSERT INTO submovement (session_id,ordinal,label,kind,frame_start,"
            "frame_end,n_frames,dt,is_slowmo_2x) VALUES (?,?,?,?,?,?,?,?,0)",
            (sid, 1, f"{load:.0f} kg", "composite", 0, 120, 120, 0.02))
        sub_id = sub.lastrowid
        con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,"
                    "value_num,unit) VALUES (?,?,?,?,?,?)",
                    (sid, sub_id, "vbt", "MPV", mpv, "m/s"))
    out.append({"athlete_id": lt_id, "athlete": "Teste de Cargas - Demo",
                "session_id": None, "exercise": "Agachamento (5 cargas)", "reps": 5,
                "fvp": f"/athletes/{lt_id}/fvp"})

    # Atleta extra para MODO SALTO (Samozino): saltos com colete (cargas)
    jp = con.execute(
        "INSERT INTO athlete (ext_key,name,body_mass_kg,height_m,bmi,sex,notes) "
        "VALUES (?,?,?,?,?,?,?)",
        (f"{DEMO_KEY}-jp", "Salto Samozino - Demo", 70.0, 1.75,
         _bmi(70.0, 1.75), "M", "massa de teste (saltos com carga)"))
    jp_id = jp.lastrowid
    push_off = 0.32
    for added, h in [(0.0, 0.36), (10.0, 0.305), (20.0, 0.26), (30.0, 0.22)]:
        cur = con.execute(
            "INSERT INTO session (athlete_id,exercise,load_kg,pct_bodyweight,gravity,"
            "pose_source,pose_model,n_submovements,captured_at,notes) "
            "VALUES (?,?,?,?,?,?,?,?,?,?)",
            (jp_id, "Salto Vertical", added, round(100 * added / 70.0, 1), 9.81, "demo",
             "massa de teste (sintetica)", 1, now, "salto com colete"))
        sid = cur.lastrowid
        sub = con.execute(
            "INSERT INTO submovement (session_id,ordinal,label,kind,frame_start,"
            "frame_end,n_frames,dt,is_slowmo_2x) VALUES (?,?,?,?,?,?,?,?,0)",
            (sid, 1, f"+{added:.0f} kg", "composite", 0, 90, 90, 0.02))
        sub_id = sub.lastrowid
        for ns, nm, val, unit in [("jump", "height", h, "m"),
                                  ("jump", "push_off", push_off, "m")]:
            con.execute("INSERT INTO metric (session_id,submovement_id,analysis,name,"
                        "value_num,unit) VALUES (?,?,?,?,?,?)",
                        (sid, sub_id, ns, nm, val, unit))
    out.append({"athlete_id": jp_id, "athlete": "Salto Samozino - Demo",
                "session_id": None, "exercise": "Salto Vertical (4 cargas)", "reps": 4,
                "samozino": f"/athletes/{jp_id}/samozino"})

    con.commit()
    return out


def main():
    ap = argparse.ArgumentParser(description="Gera massa de teste (dados ficticios).")
    ap.add_argument("--db", default=str(Path(__file__).resolve().parents[1]
                                        / "data" / "db.sqlite"))
    ap.add_argument("--athletes", type=int, default=4)
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--reset", action="store_true", help="limpa massa de teste anterior")
    ap.add_argument("--shares", action="store_true", help="ja gera os links de relatorio")
    args = ap.parse_args()

    con = sqlite3.connect(args.db)
    con.execute("PRAGMA foreign_keys=ON")
    if args.reset:
        n = clear_demo(con)
        print(f"[reset] removidos {n} atleta(s) demo anteriores")
    recs = seed(con, args.athletes, args.reps, make_shares=args.shares)
    con.close()

    print(f"\n[ok] massa de teste criada: {len(recs)} atleta(s), "
          f"{args.reps} rep(s) cada, {len(_METRIC_SPEC)} metricas/rep\n")
    for r in recs:
        line = f"  #{r['session_id']:>2}  {r['athlete']:<18} {r['exercise']}"
        if r.get("report_url"):
            line += f"   -> {r['report_url']}"
        print(line)
    if args.shares:
        print("\nAbra os relatorios em:  http://127.0.0.1:8000<report_url>")
    else:
        print("\nGere os links na tela /app/gerir.html (botao 'Gerar link') "
              "ou rode com --shares.")


if __name__ == "__main__":
    main()
