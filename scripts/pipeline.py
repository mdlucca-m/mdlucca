#!/usr/bin/env python3
"""
scripts/pipeline.py

Orquestrador do pipeline biomecanico (automacao estilo n8n): encadeia "nos"
determinísticos a partir de UM comando, do video cru ate os entregaveis.

Nos (em ordem):
  1. pose        -> extrai landmarks 3D (MediaPipe)        -> data/pose_<key>.json
  2. session     -> monta series + insere sessao no banco  -> nova sessao (id)
  3. overlay     -> video anotado (esqueleto + reps)        -> <out>/overlay_<key>.mp4
  4. dashboard   -> dashboard ao vivo (graficos/picos)      -> <out>/dashboard_<key>.mp4
  5. legs3d      -> analise das 2 pernas + boneco 3D        -> <out>/legs3d_<key>.mp4  (opcional)
  6. manifest    -> JSON com tudo que foi produzido         -> <out>/manifest_<key>.json

Cada no e idempotente (pula se a saida existe, salvo --force) e reporta
status/tempo. Serve tanto para rodar na mao quanto para ser disparado pela
API (POST /pipeline/run) ou por um watcher de pasta (scripts/watch_inbox.py).

Uso:
  python3 scripts/pipeline.py --video clip.mp4 --model pose_landmarker_full.task \
      --athlete "Atleta X" --mass 80 --out data/out --key X [--legs3d] [--force]
"""
from __future__ import annotations

import argparse
import json
import shlex
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sh(cmd: list[str]) -> tuple[int, str]:
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, (p.stdout + p.stderr)


def max_session(db: str) -> int:
    con = sqlite3.connect(db)
    try:
        r = con.execute("SELECT COALESCE(MAX(id),0) FROM session").fetchone()[0]
        return int(r)
    finally:
        con.close()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--video", required=True)
    ap.add_argument("--model", required=True, help="pose_landmarker_*.task")
    ap.add_argument("--athlete", default="Atleta")
    ap.add_argument("--exercise", default="Video")
    ap.add_argument("--mass", type=float, default=80.0)
    ap.add_argument("--brand", default="De Lucca Esporte")
    ap.add_argument("--db", default=str(ROOT / "data" / "db.sqlite"))
    ap.add_argument("--out", default=str(ROOT / "data" / "out"))
    ap.add_argument("--key", default=None, help="rotulo curto (default: nome do arquivo)")
    ap.add_argument("--legs3d", action="store_true", help="tambem gera a analise 3D das 2 pernas")
    ap.add_argument("--stature", type=float, default=None, help="estatura real do atleta (m) p/ calibrar")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    video = Path(args.video)
    key = args.key or video.stem.split("_")[0][:12]
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    pose_json = out / f"pose_{key}.json"
    overlay = out / f"overlay_{key}.mp4"
    dashboard = out / f"dashboard_{key}.mp4"
    legs3d = out / f"legs3d_{key}.mp4"
    manifest_path = out / f"manifest_{key}.json"

    steps: list[dict] = []
    fps = None
    session_id = None

    def node(name, cmd, produces: Path, skip_if=True):
        rec = {"node": name, "cmd": " ".join(shlex.quote(c) for c in cmd)}
        t0 = time.time()
        if produces.exists() and skip_if and not args.force:
            rec.update(status="skipped", seconds=0.0, output=str(produces))
            steps.append(rec); print(f"[skip] {name} -> {produces.name} (existe)")
            return True
        print(f"[run ] {name} ...")
        code, log = sh(cmd)
        rec.update(status="ok" if code == 0 else "error", seconds=round(time.time() - t0, 1),
                   output=str(produces) if code == 0 else None, returncode=code)
        if code != 0:
            rec["log_tail"] = log.strip().splitlines()[-6:]
        steps.append(rec)
        print(f"[{'ok  ' if code==0 else 'FAIL'}] {name} ({rec['seconds']}s)")
        return code == 0

    py = [sys.executable]

    # 1. POSE
    if not node("pose", py + [str(ROOT / "scripts/pose_extract.py"), "--video", str(video),
                              args.model, "-o", str(pose_json)], pose_json):
        return _finish(manifest_path, steps, key, str(video), None, None, error="pose falhou")
    fps = json.loads(pose_json.read_text())["fps"]

    # 2. SESSION (sempre roda: insere nova sessao)
    before = max_session(args.db)
    session_cmd = py + [str(ROOT / "scripts/build_session_from_pose.py"),
                        "--pose", str(pose_json), "--db", args.db, "--athlete", args.athlete,
                        "--exercise", args.exercise, "--mass", str(args.mass), "--append"]
    if args.stature:
        session_cmd += ["--stature", str(args.stature)]
    ok = node("session", session_cmd, manifest_path, skip_if=False)  # sempre executa
    if not ok:
        return _finish(manifest_path, steps, key, str(video), None, fps, error="session falhou")
    session_id = max_session(args.db)
    if session_id == before:
        session_id = before  # nada inserido (raro)

    # 3. OVERLAY
    node("overlay", py + [str(ROOT / "scripts/render_overlay.py"), "--video", str(video),
                          "--pose", str(pose_json), "--db", args.db, "--session", str(session_id),
                          "--out", str(overlay), "--brand", args.brand, "--fps", str(fps)], overlay)

    # 4. DASHBOARD
    node("dashboard", py + [str(ROOT / "scripts/render_dashboard_video.py"), "--video", str(video),
                            "--pose", str(pose_json), "--db", args.db, "--session", str(session_id),
                            "--out", str(dashboard), "--fps", str(fps), "--brand", args.brand], dashboard)

    # 5. LEGS3D (opcional)
    if args.legs3d:
        legs_cmd = py + [str(ROOT / "scripts/render_legs3d_video.py"), "--video", str(video),
                         "--pose", str(pose_json), "--out", str(legs3d), "--fps", str(fps),
                         "--brand", args.brand]
        if args.stature:
            legs_cmd += ["--stature", str(args.stature)]
        node("legs3d", legs_cmd, legs3d)

    return _finish(manifest_path, steps, key, str(video), session_id, fps,
                   outputs={"pose": str(pose_json), "overlay": str(overlay),
                            "dashboard": str(dashboard),
                            "legs3d": str(legs3d) if args.legs3d else None})


def _finish(manifest_path, steps, key, video, session_id, fps, outputs=None, error=None):
    manifest = {"key": key, "video": video, "session_id": session_id, "fps": fps,
                "ok": error is None and all(s["status"] != "error" for s in steps),
                "error": error, "steps": steps, "outputs": outputs or {}}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nmanifest -> {manifest_path}  (ok={manifest['ok']}, session={session_id})")
    return 0 if manifest["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
