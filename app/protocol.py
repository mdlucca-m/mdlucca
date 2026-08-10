"""
app/protocol.py  —  PADRAO DE ANALISE (laudo padronizado)

Define o protocolo unico de avaliacao biomecanica: a MESMA estrutura, as MESMAS
metricas-chave e as MESMAS checagens de literatura em TODA avaliacao, para
qualquer atleta ou exercicio. Metrica que nao pode ser calculada aparece como
'N/D' (nao disponivel) em vez de sumir do laudo — assim o relatorio fica
comparavel entre sessoes, atletas e exercicios (um verdadeiro padrao).

api.py consome estas definicoes para montar `_build_assessment`, o markdown e o
HTML a partir da MESMA fonte de verdade.
"""
from __future__ import annotations

PROTOCOL_VERSION = "padrao-1.0"

# Ordem canonica das secoes do laudo (sempre nesta ordem).
SECTIONS = [
    "Identificacao",
    "Classificacao do movimento",
    "Qualidade da analise",
    "Metricas-chave por repeticao",
    "Indice de fadiga e variabilidade",
    "Checagens de literatura",
    "Procedencia e metodologia",
]

# Rotulo "nao disponivel" usado em todo o laudo.
NA = "N/D"

# --------------------------------------------------------------------------
# Metricas-chave canonicas: exibidas SEMPRE, nesta ordem, com rotulo e unidade
# fixos. `sources` lista pares (analysis, name) do banco em ordem de preferencia
# — o primeiro que existir para a repeticao e usado. `fmt` = casas decimais.
# --------------------------------------------------------------------------
CANONICAL_METRICS = [
    {"key": "F_peak", "label": "Forca pico", "unit": "N", "fmt": 0,
     "sources": [("peaks", "F_peak"), ("peaks", "force_dynamic_peak"),
                 ("global_kpi", "peak_force")]},
    {"key": "P_peak", "label": "Potencia pico", "unit": "W", "fmt": 0,
     "sources": [("peaks", "P_peak"), ("peaks", "power_peak"),
                 ("global_kpi", "peak_power")]},
    {"key": "v_peak", "label": "Velocidade pico", "unit": "m/s", "fmt": 2,
     "sources": [("peaks", "v_peak"), ("derivatives", "v_peak"),
                 ("global_kpi", "peak_speed")]},
    {"key": "MPV", "label": "Vel. propulsiva media", "unit": "m/s", "fmt": 2,
     "sources": [("propulsive", "MPV"), ("vbt", "MPV")]},
    {"key": "RFD_peak", "label": "RFD pico", "unit": "N/s", "fmt": 0,
     "sources": [("peaks", "RFD_peak"), ("global_kpi", "peak_rfd")]},
    {"key": "tau_hip", "label": "Torque quadril pico", "unit": "N.m", "fmt": 0,
     "sources": [("peaks", "tau_hip_peak"), ("moments", "tau_hip"),
                 ("global_kpi", "peak_tau_hip")]},
    {"key": "hip_angvel", "label": "Vel. ang. quadril", "unit": "graus/s", "fmt": 0,
     "sources": [("peaks", "hip_angvel_peak"),
                 ("angular_velocity", "hip")]},
    {"key": "knee_angvel", "label": "Vel. ang. joelho", "unit": "graus/s", "fmt": 0,
     "sources": [("peaks", "knee_angvel_peak"),
                 ("angular_velocity", "knee")]},
]

# --------------------------------------------------------------------------
# Checagens de literatura canonicas: exibidas SEMPRE, nesta ordem.
#   ref    -> chave em reference_values.BANDS (traz faixa/status/fonte)
#   series -> serie articular usada para obter o valor (agg='max'); None p/ CV
#   agg    -> 'max' (pico da serie) ou 'cv' (CV% do pico de potencia entre reps)
# --------------------------------------------------------------------------
CANONICAL_CHECKS = [
    {"ref": "hip_extension_deg", "label": "Extensao de quadril",
     "series": "hip_angle", "agg": "max"},
    {"ref": "knee_extension_deg", "label": "Extensao de joelho",
     "series": "knee_angle", "agg": "max"},
    {"ref": "elbow_extension_deg", "label": "Extensao de cotovelo",
     "series": "elbow_angle", "agg": "max"},
    {"ref": "cv_pct", "label": "Variabilidade entre reps (CV)",
     "series": None, "agg": "cv"},
]

# Metricas usadas para o indice de fadiga (queda intra-serie), em ordem.
FATIGUE_METRICS = [
    {"key": "P_peak", "out": "power_drop_pct", "label": "Queda de potencia"},
    {"key": "v_peak", "out": "velocity_loss_pct", "label": "Perda de velocidade"},
]


def fmt_value(v, fmt: int = 1) -> str:
    """Formata um numero para o laudo, ou devolve 'N/D' quando ausente."""
    if v is None:
        return NA
    try:
        f = float(v)
    except (TypeError, ValueError):
        return NA
    if fmt <= 0:
        return f"{f:,.0f}".replace(",", ".")
    return f"{f:.{fmt}f}"


def drop_pct(values) -> float | None:
    """Queda percentual intra-serie: (melhor - pior) / melhor * 100.

    Convencao de fadiga (Sanchez-Medina & Gonzalez-Badillo 2011): a perda e
    medida do MELHOR (maior) valor da serie ate o menor. >=2 valores validos.
    """
    xs = [float(x) for x in values if x is not None]
    if len(xs) < 2:
        return None
    hi = max(xs)
    if hi <= 0:
        return None
    return round((hi - min(xs)) / hi * 100.0, 1)
