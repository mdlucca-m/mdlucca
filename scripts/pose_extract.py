#!/usr/bin/env python3
"""
scripts/pose_extract.py

Roda o MediaPipe PoseLandmarker (Tasks API) sobre uma pasta de frames PNG e
salva os landmarks por frame em JSON. Usa os WORLD landmarks (3D em metros,
origem no quadril) — sem a distorcao de aspect ratio da pose 2D normalizada.

Uso:
  python3 scripts/pose_extract.py <dir_frames> <modelo.task> -o pose.json --fps 25
"""
from __future__ import annotations

import argparse
import glob
import json
import os
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

# 33 landmarks BlazePose — indices usados.
L = dict(nose=0, ear_l=7, ear_r=8, sh_l=11, sh_r=12, el_l=13, el_r=14,
         wr_l=15, wr_r=16, idx_l=19, idx_r=20, hip_l=23, hip_r=24,
         kn_l=25, kn_r=26, an_l=27, an_r=28, foot_l=31, foot_r=32)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("frames_dir")
    ap.add_argument("model")
    ap.add_argument("-o", "--output", default="data/pose.json")
    ap.add_argument("--fps", type=float, default=25.0)
    args = ap.parse_args()

    frames = sorted(glob.glob(os.path.join(args.frames_dir, "*.png")))
    if not frames:
        raise SystemExit(f"nenhum frame PNG em {args.frames_dir}")

    opts = vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=args.model),
        running_mode=vision.RunningMode.IMAGE,
        output_segmentation_masks=False,
    )
    landmarker = vision.PoseLandmarker.create_from_options(opts)

    world, norm, vis, detected = [], [], [], 0
    h = w = None
    for i, fp in enumerate(frames):
        img = cv2.imread(fp)
        if img is None:
            world.append(None); norm.append(None); vis.append(None); continue
        h, w = img.shape[:2]
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        res = landmarker.detect(mp_img)
        if not res.pose_world_landmarks:
            world.append(None); norm.append(None); vis.append(None); continue
        detected += 1
        wl = res.pose_world_landmarks[0]
        nl = res.pose_landmarks[0]
        world.append([[round(p.x, 5), round(p.y, 5), round(p.z, 5)] for p in wl])
        norm.append([[round(p.x, 5), round(p.y, 5)] for p in nl])
        vis.append([round(p.visibility, 4) for p in nl])
        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{len(frames)} frames ({detected} com pose)")

    out = {
        "fps": args.fps, "n_frames": len(frames), "width": w, "height": h,
        "detected": detected, "landmark_index": L,
        "world": world, "norm": norm, "visibility": vis,
    }
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(out), encoding="utf-8")
    print(f"pose salva: {args.output}  ({detected}/{len(frames)} frames com pose)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
