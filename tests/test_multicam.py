"""
Teste do nucleo de reconstrucao 3D multi-camera (app/multicam.py): projeta um
ponto 3D conhecido em 3 cameras sinteticas e verifica que a triangulacao DLT o
recupera com erro desprezivel.
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import multicam as MC  # noqa: E402


def _rot_y(deg):
    a = np.radians(deg)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def _cam(angle_deg, name):
    # intrinsecos simples (f=1000 px, centro 640x360)
    K = np.array([[1000, 0, 640], [0, 1000, 360], [0, 0, 1]], float)
    R = _rot_y(angle_deg)
    # camera a 3 m de distancia, olhando para a origem
    C = R @ np.array([0, 0, 3.0])          # centro da camera no mundo
    t = -R @ C
    return MC.Camera.from_krt(K, R, t, name)


def test_triangulation_recovers_point():
    cams = [_cam(-40, "esq"), _cam(0, "frontal"), _cam(40, "dir")]
    X_true = np.array([0.12, -0.05, 0.20])
    pts = [c.project(X_true) for c in cams]
    X = MC.triangulate_point(cams, pts)
    assert X is not None
    assert np.allclose(X, X_true, atol=1e-6)
    assert MC.reprojection_error(cams, X, pts) < 1e-3


def test_needs_two_views():
    cams = [_cam(-40, "esq"), _cam(0, "frontal")]
    # so uma vista valida -> nao triangula
    assert MC.triangulate_point(cams, [cams[0].project([0, 0, 0]), None]) is None


def test_landmarks_and_visibility_weighting():
    cams = [_cam(-30, "a"), _cam(10, "b"), _cam(45, "c")]
    lms_true = [np.array([0.0, 0.0, 0.0]), np.array([0.1, 0.2, -0.1])]
    views = [[c.project(X) for X in lms_true] for c in cams]
    vis = [[1.0, 1.0] for _ in cams]
    out = MC.triangulate_landmarks(cams, views, vis)
    assert len(out) == 2
    for X, Xt in zip(out, lms_true):
        assert X is not None and np.allclose(X, Xt, atol=1e-5)


if __name__ == "__main__":
    print("rode com pytest")
