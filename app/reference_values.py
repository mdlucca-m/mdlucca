"""
app/reference_values.py

Padroes metodologicos de literatura internacional que o sistema segue, e
faixas de referencia para comparar medicoes. As referencias metodologicas sao
consolidadas e citadas; as faixas de desempenho vem rotuladas como criterio
tecnico ou como INDICATIVAS (validar contra a populacao/nivel do atleta).
"""
from __future__ import annotations

# --------------------------------------------------------------------------
# Padroes metodologicos (o "como medir" conforme a literatura)
# --------------------------------------------------------------------------
STANDARDS = [
    {"area": "Filtragem de sinal",
     "standard": "Butterworth passa-baixa 4a ordem, fase zero (filtfilt), corte ~6 Hz "
                 "para movimento humano; escolha do corte por analise de residuo.",
     "aplicado": True,
     "citation": "Winter DA (2009). Biomechanics and Motor Control of Human Movement, 4th ed. Wiley."},
    {"area": "Parametros de segmento (CoM / inercia)",
     "standard": "Fracoes de massa e posicao do centro de massa de De Leva.",
     "aplicado": True,
     "citation": "De Leva P (1996). J Biomechanics 29(9):1223-1230."},
    {"area": "Convencao de angulos articulares",
     "standard": "Sistemas de coordenadas articulares recomendados pela ISB.",
     "aplicado": True,
     "citation": "Wu G et al. (2002, 2005). J Biomechanics — ISB recommendations."},
    {"area": "Normalizacao por tamanho corporal",
     "standard": "Escala alometrica (forca ~ massa^0.67).",
     "aplicado": True,
     "citation": "Jaric S (2002). Sports Medicine 32(10):615-631."},
    {"area": "Amostragem (frames)",
     "standard": "fs >= 2x a maior frequencia de interesse (Nyquist); movimentos "
                 "explosivos/impacto pedem 120-240 Hz. Aqui: 20-30 Hz (limitacao de camera).",
     "aplicado": False,
     "citation": "Robertson DGE et al. Research Methods in Biomechanics; Winter (2009)."},
    {"area": "Velocidade propulsiva (VBT)",
     "standard": "MPV = velocidade media enquanto a aceleracao >= -g (fase propulsiva).",
     "aplicado": True,
     "citation": "Sanchez-Medina L, Gonzalez-Badillo JJ (2011). Med Sci Sports Exerc 43(9):1725-1734."},
    {"area": "Forca explosiva (RFD/TDF)",
     "standard": "RFD/TDF em janelas fixas a partir do onset (0-50/100/150/200 ms).",
     "aplicado": True,
     "citation": "Maffiuletti NA et al. (2016). Eur J Appl Physiol 116:1091-1116."},
]

# --------------------------------------------------------------------------
# Faixas de referencia (criterio tecnico ou indicativo)
# --------------------------------------------------------------------------
# tipo: 'target_max' -> ideal e chegar ao valor 'ideal' (ex.: 180 graus)
#       'range'      -> ideal ficar dentro de [lo, hi]
BANDS = {
    "knee_extension_deg": {
        "type": "target_max", "ideal": 180, "tol_good": 10, "tol_ok": 25, "unit": "deg",
        "kind": "criterio tecnico",
        "note": "Extensao completa do joelho = 180 graus (perna reta).",
        "source": "Convencao anatomica / ISB (Wu et al. 2002)."},
    "hip_extension_deg": {
        "type": "target_max", "ideal": 180, "tol_good": 10, "tol_ok": 25, "unit": "deg",
        "kind": "criterio tecnico",
        "note": "Extensao completa de quadril = 180 graus.",
        "source": "Convencao anatomica / ISB."},
    "split_angle_deg": {
        "type": "target_max", "ideal": 180, "tol_good": 15, "tol_ok": 35, "unit": "deg",
        "kind": "criterio tecnico (ginastica)",
        "note": "Espacate completo / abertura da passada = 180 graus.",
        "source": "Criterio de execucao (Codigo de Pontuacao FIG)."},
    "elbow_extension_deg": {
        "type": "target_max", "ideal": 180, "tol_good": 10, "tol_ok": 25, "unit": "deg",
        "kind": "criterio tecnico",
        "note": "Extensao completa de cotovelo = 180 graus.",
        "source": "Convencao anatomica / ISB."},
    "cv_pct": {
        "type": "range", "lo": 0, "hi": 10, "ok_hi": 15, "unit": "%",
        "kind": "criterio estatistico",
        "note": "CV < 10% = consistente entre repeticoes; 10-15% moderado; >15% variavel.",
        "source": "Atkinson & Nevill (1998), Sports Medicine 26(4):217-238 (reliability)."},
}


def evaluate(metric: str, value: float) -> dict:
    """Compara um valor medido a faixa de referencia e devolve status."""
    b = BANDS.get(metric)
    if b is None:
        return {"metric": metric, "value": value, "status": "sem_referencia"}
    out = {"metric": metric, "value": value, "unit": b["unit"], "kind": b["kind"],
           "note": b["note"], "source": b["source"]}
    if b["type"] == "target_max":
        deficit = b["ideal"] - value
        out["ideal"] = b["ideal"]; out["deficit"] = round(deficit, 1)
        out["status"] = ("otimo" if deficit <= b["tol_good"]
                         else "adequado" if deficit <= b["tol_ok"] else "abaixo")
    else:  # range
        if value <= b["hi"]:
            out["status"] = "otimo"
        elif value <= b["ok_hi"]:
            out["status"] = "adequado"
        else:
            out["status"] = "fora"
        out["range_ideal"] = [b["lo"], b["hi"]]
    return out
