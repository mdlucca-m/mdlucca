#!/usr/bin/env python3
"""
scripts/watch_inbox.py

Gatilho estilo n8n "Local File Trigger": observa uma pasta e roda o pipeline
completo em cada video novo, movendo o arquivo para processed/ ao terminar.
Alternativa self-hosted a um trigger do n8n, sem depender de servidor externo.

Uso:
  MDLUCCA_POSE_MODEL=/caminho/pose_landmarker_full.task \
  python3 scripts/watch_inbox.py --inbox data/inbox --out data/out --interval 5
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXTS = {".mp4", ".mkv", ".mov", ".avi", ".webm"}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--inbox", default=str(ROOT / "data" / "inbox"))
    ap.add_argument("--out", default=str(ROOT / "data" / "out"))
    ap.add_argument("--model", default=os.environ.get("MDLUCCA_POSE_MODEL"))
    ap.add_argument("--mass", type=float, default=80.0)
    ap.add_argument("--legs3d", action="store_true")
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--once", action="store_true", help="processa a fila atual e sai")
    args = ap.parse_args()

    if not args.model or not Path(args.model).exists():
        raise SystemExit("modelo de pose ausente: use --model ou MDLUCCA_POSE_MODEL")
    inbox = Path(args.inbox); inbox.mkdir(parents=True, exist_ok=True)
    processed = inbox / "processed"; processed.mkdir(exist_ok=True)
    failed = inbox / "failed"; failed.mkdir(exist_ok=True)

    print(f"observando {inbox}  (intervalo {args.interval}s)  Ctrl-C para sair")
    while True:
        vids = sorted(p for p in inbox.iterdir() if p.suffix.lower() in EXTS and p.is_file())
        for v in vids:
            print(f"\n>>> novo video: {v.name}")
            cmd = [sys.executable, str(ROOT / "scripts" / "pipeline.py"), "--video", str(v),
                   "--model", args.model, "--athlete", v.stem, "--exercise", v.stem,
                   "--mass", str(args.mass), "--out", args.out]
            if args.legs3d:
                cmd.append("--legs3d")
            rc = subprocess.run(cmd).returncode
            dest = (processed if rc == 0 else failed) / v.name
            v.rename(dest)
            print(f"<<< {v.name} -> {dest.parent.name}/ (rc={rc})")
        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    raise SystemExit(main())
