"""
app/quality.py — score de qualidade da análise (0-100) + nível + avisos,
inspirado no 'quality gate' de plataformas de avaliação. Penaliza taxa de
quadros baixa, poucos quadros, ausência de calibração, detecção/confiança
de pose baixas.
"""
from __future__ import annotations

from typing import Optional


def quality_report(*, n_frames: Optional[int] = None, fps: Optional[float] = None,
                   is_calibrated: bool = False, detected_ratio: float = 1.0,
                   mean_confidence: Optional[float] = None) -> dict:
    score = 100.0
    warnings: list[str] = []
    if fps and fps < 20:
        score -= 15
        warnings.append(f"Taxa de quadros baixa ({fps:.0f} fps) — recomendável ≥30 fps.")
    elif fps and fps < 30:
        score -= 5
        warnings.append(f"Taxa de quadros moderada ({fps:.0f} fps).")
    if n_frames is not None and n_frames < 30:
        score -= 20
        warnings.append(f"Poucos quadros analisados ({n_frames}).")
    if not is_calibrated:
        score -= 10
        warnings.append("Sem calibração métrica — forças/potências são estimativas relativas.")
    if detected_ratio < 0.9:
        score -= 15
        warnings.append(f"Detecção de pose baixa ({detected_ratio * 100:.0f}% dos quadros).")
    if mean_confidence is not None and mean_confidence < 0.8:
        score -= 10
        warnings.append(f"Confiança média da pose baixa ({mean_confidence:.2f}).")

    score = max(0.0, min(100.0, score))
    level = ("excelente" if score >= 85 else "bom" if score >= 70
             else "aceitavel" if score >= 50 else "ruim")
    return {"score": round(score, 1), "level": level, "warnings": warnings}
