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
# Expoente alometrico (normalizacao por tamanho corporal): forca ~ massa^0.67.
# Jaric S (2002). Sports Medicine 32(10):615-631.
# --------------------------------------------------------------------------
ALLOMETRIC_EXPONENT = 0.67

# --------------------------------------------------------------------------
# Metricas-chave canonicas, organizadas em GRUPOS tematicos. Exibidas SEMPRE,
# nesta ordem, com rotulo e unidade fixos. Resolucao em cascata por repeticao:
#   1) `db`     -> pares (analysis, name) gravados no banco (primeiro que existir)
#   2) `series` -> (nome_da_serie, agg) fatiada na janela [frame_start..frame_end]
#                  do full-session; agg: 'peak' (|max|), 'max', 'min', 'range',
#                  'mean', 'meanpos'
#   3) `derive` -> ('allo', base_key): base_key / massa^0.67 (ajuste alometrico)
# Metrica que nao resolve vira None -> 'N/D' no laudo (comparavel entre sessoes).
# `fmt` = casas decimais.
# --------------------------------------------------------------------------
METRIC_GROUPS = [
    {"title": "Força e potência", "metrics": [
        {"key": "F_peak", "label": "Força pico", "unit": "N", "fmt": 0,
         "db": [("peaks", "F_peak"), ("peaks", "force_dynamic_peak"),
                ("global_kpi", "peak_force")], "series": ("force", "peak")},
        {"key": "P_peak", "label": "Potência pico", "unit": "W", "fmt": 0,
         "db": [("peaks", "P_peak"), ("peaks", "power_peak"),
                ("global_kpi", "peak_power")], "series": ("power", "peak")},
        {"key": "RFD_peak", "label": "TDF/RFD pico", "unit": "N/s", "fmt": 0,
         "db": [("peaks", "RFD_peak"), ("global_kpi", "peak_rfd")],
         "series": ("rfd", "peak")},
        {"key": "MPV", "label": "Vel. propulsiva média", "unit": "m/s", "fmt": 2,
         "db": [("propulsive", "MPV"), ("vbt", "MPV")],
         "series": ("propulsive_velocity", "meanpos")},
    ]},
    {"title": "Cinemática linear (vetorial)", "metrics": [
        {"key": "v_peak", "label": "Velocidade vetorial pico", "unit": "m/s", "fmt": 2,
         "db": [("peaks", "v_peak"), ("derivatives", "v_peak"),
                ("global_kpi", "peak_speed")], "series": ("speed", "peak")},
        {"key": "a_peak", "label": "Aceleração vetorial pico", "unit": "m/s²", "fmt": 2,
         "db": [("derivatives", "a_peak")], "series": ("accel", "peak")},
    ]},
    {"title": "Cinemática angular (velocidade e aceleração)", "metrics": [
        {"key": "hip_angvel", "label": "Vel. ang. quadril", "unit": "°/s", "fmt": 0,
         "db": [("peaks", "hip_angvel_peak")], "series": ("hip_angvel", "peak")},
        {"key": "knee_angvel", "label": "Vel. ang. joelho", "unit": "°/s", "fmt": 0,
         "db": [("peaks", "knee_angvel_peak")], "series": ("knee_angvel", "peak")},
        {"key": "ankle_angvel", "label": "Vel. ang. tornozelo", "unit": "°/s", "fmt": 0,
         "db": [("peaks", "ankle_angvel_peak")], "series": ("ankle_angvel", "peak")},
        {"key": "hip_aa", "label": "Acel. ang. quadril", "unit": "°/s²", "fmt": 0,
         "db": [("peaks", "hip_aa_peak")], "series": ("hip_aa", "peak")},
        {"key": "knee_aa", "label": "Acel. ang. joelho", "unit": "°/s²", "fmt": 0,
         "db": [("peaks", "knee_aa_peak")], "series": ("knee_aa", "peak")},
    ]},
    {"title": "Centro de gravidade (CoM · De Leva 1996)", "metrics": [
        {"key": "cog_speed", "label": "Velocidade do CoM pico", "unit": "m/s", "fmt": 2,
         "db": [("cog", "cog_speed_peak")], "series": ("cog_speed", "peak")},
        {"key": "cog_exc_v", "label": "Excursão vertical do CoM", "unit": "m", "fmt": 3,
         "db": [("cog", "y_excursion")], "series": ("cog_y", "range")},
    ]},
    {"title": "Ajuste alométrico (Jaric 2002 · massa^0.67)", "metrics": [
        {"key": "F_allo", "label": "Força alométrica", "unit": "N/kg^0.67", "fmt": 1,
         "db": [("allometric", "F_allo")], "derive": ("allo", "F_peak")},
        {"key": "P_allo", "label": "Potência alométrica", "unit": "W/kg^0.67", "fmt": 1,
         "db": [("allometric", "P_allo")], "derive": ("allo", "P_peak")},
    ]},
]

# Lista achatada (ordem canonica) — mantida para compatibilidade.
CANONICAL_METRICS = [m for g in METRIC_GROUPS for m in g["metrics"]]

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
    # Convencao cientifica: inteiros sem separador de milhar, decimais com ponto
    # (evita ambiguidade entre 1028 e 1.04 no mesmo laudo).
    if fmt <= 0:
        return f"{f:.0f}"
    return f"{f:.{fmt}f}"


def agg_series(values, how: str = "peak") -> float | None:
    """Agrega uma serie (ou fatia dela) conforme `how`. Ignora None.

    'peak'    -> maior valor em modulo (magnitude do pico)
    'max'/'min'/'mean'/'range' -> obvios
    'meanpos' -> media apenas dos valores positivos (fase propulsiva)
    """
    arr = [float(x) for x in values if x is not None]
    if not arr:
        return None
    if how == "peak":
        return abs(max(arr, key=abs))
    if how == "max":
        return max(arr)
    if how == "min":
        return min(arr)
    if how == "range":
        return max(arr) - min(arr)
    if how == "mean":
        return sum(arr) / len(arr)
    if how == "meanpos":
        pos = [x for x in arr if x > 0]
        return (sum(pos) / len(pos)) if pos else None
    return None


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
