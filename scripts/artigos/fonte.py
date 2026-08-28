#!/usr/bin/env python3
"""Tabelas de origem dos dois artigos, transcritas do relatório completo.

Cada bloco declara a tabela de origem em data/ARTIGO_HUMOR_VERSAO_FINAL.docx.
Nenhum valor é estimado.
"""
from __future__ import annotations

MENOS = "−"


def br(v, casas=2):
    if isinstance(v, str):
        return v
    if abs(v) < 0.5 * 10 ** -casas:
        v = 0.0
    return f"{v:.{casas}f}".replace(".", ",").replace("-", MENOS)


def sinal(v, casas=2):
    if abs(v) < 0.5 * 10 ** -casas:
        return f"{0.0:.{casas}f}".replace(".", ",")
    return f"{v:+.{casas}f}".replace(".", ",").replace("-", MENOS)


SUBESCALAS = ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"]

# ── Tabela 3: descritivas e efeito piso ───────────────────────────────────
DESCRITIVA = {  # média, DP, mediana, IQR, assimetria, curtose, % piso
    "PTH (TMD)":      (4.39, 9.64, 2, 10, 1.48, 3.31, 21.9),
    "Vigor":          (5.70, 3.12, 6, 4, 0.03, -0.24, 8.6),
    "Fadiga":         (5.65, 3.89, 5, 5, 0.59, -0.40, 7.7),
    "Tensão":         (1.39, 1.84, 1, 2, 1.43, 1.50, 49.6),
    "Depressão":      (1.00, 2.31, 0, 1, 3.63, 14.93, 67.1),
    "Raiva":          (1.60, 2.73, 0, 2, 2.07, 4.22, 59.6),
    "Confusão":       (0.45, 1.19, 0, 0, 3.73, 16.96, 80.5),
}

# ── Tabela 74: percentis observados ───────────────────────────────────────
PERCENTIS = {
    "Tensão":    (0, 0, 1, 2, 6),
    "Depressão": (0, 0, 0, 1, 5),
    "Raiva":     (0, 0, 0, 2, 8),
    "Vigor":     (0, 4, 6, 8, 11),
    "Fadiga":    (0, 3, 5, 8, 13),
    "Confusão":  (0, 0, 0, 0, 3),
    "PTH (TMD)": (-6, -2, 2, 8, 22),
}

# ── Tabela 6: confiabilidade interna ──────────────────────────────────────
CONFIABILIDADE = {  # alfa, alfa ordinal, ômega ordinal, split-half, item-total
    "Depressão": (0.85, 0.94, 0.94, 0.89, 0.66),
    "Raiva":     (0.87, 0.93, 0.93, 0.89, 0.66),
    "Fadiga":    (0.80, 0.81, 0.85, 0.81, 0.23),
    "Vigor":     (0.68, 0.74, 0.80, 0.74, 0.11),
    "Confusão":  (0.66, None, None, 0.67, 0.20),
    "Tensão":    (0.43, None, None, 0.54, 0.11),
}

# ── Tabela 7: estabilidade de uma coleta e da média de sete dias ─────────
ESTABILIDADE = {  # ICC(1,1), ICC(1,7)
    "Tensão": (0.59, 0.91), "Depressão": (0.56, 0.90), "Vigor": (0.55, 0.90),
    "Fadiga": (0.53, 0.89), "Confusão": (0.35, 0.79), "Raiva": (0.31, 0.76),
}

# ── Tabela 11: correlação entre as subescalas ────────────────────────────
CORRELACAO = {
    ("Depressão", "Tensão"): 0.45,
    ("Raiva", "Tensão"): 0.39, ("Raiva", "Depressão"): 0.61,
    ("Vigor", "Tensão"): 0.33, ("Vigor", "Depressão"): 0.48,
    ("Vigor", "Raiva"): 0.51,
    ("Fadiga", "Tensão"): 0.28, ("Fadiga", "Depressão"): 0.73,
    ("Fadiga", "Raiva"): 0.55, ("Fadiga", "Vigor"): 0.67,
    ("Confusão", "Tensão"): 0.75, ("Confusão", "Depressão"): 0.74,
    ("Confusão", "Raiva"): 0.42, ("Confusão", "Vigor"): 0.43,
    ("Confusão", "Fadiga"): 0.48,
}

# ── Tabela 10: ajuste do modelo de seis fatores ──────────────────────────
AJUSTE = {"CFI": 0.960, "RMSEA": 0.027}

# ── Tabela 72: carga do microciclo ────────────────────────────────────────
CARGA = [
    (1, "Dom 21/04", "Repouso", 0, "n.a.", "n.a.", "n.a.", "n.a.", "Repouso"),
    (2, "Seg 22/04", "HIIT e técnico-tático", 2, "2,0 a 2,5 h", "47%", "184",
     "8,5", "Alta intensidade"),
    (3, "Ter 23/04", "Técnico-tático, força e amistoso", 3, "4,5 a 5,0 h",
     "100%", "n.d.", "n.d.", "Alto volume"),
    (4, "Qua 24/04", "HIIT e técnico-tático", 2, "2,0 a 2,5 h", "47%", "183",
     "8,5", "Alta intensidade"),
    (5, "Qui 25/04", "Técnico-tático, força e amistoso", 3, "4,5 a 5,0 h",
     "100%", "n.d.", "n.d.", "Alto volume"),
    (6, "Sex 26/04", "Técnico-tático e força", 3, "4,5 a 5,0 h", "100%",
     "n.d.", "n.d.", "Alto volume"),
    (7, "Sáb 27/04", "HIIT e técnico-tático", 2, "2,0 a 2,5 h", "47%", "181",
     "9,1", "Alta intensidade"),
]

# ── Tabela 69: progressão entre as três sessões de HIIT ──────────────────
SESSOES = {   # S1 (dia 2), S2 (dia 4), S3 (dia 7), inclinação, ICC entre sessões
    "PTH (TMD)":       (4.8, 5.7, 8.0, 1.76, True, 0.72),
    "Fadiga física":   (5.6, 6.9, 7.6, 1.01, True, 0.63),
    "Fadiga (BRUMS)":  (5.2, 6.3, 7.5, 1.08, True, 0.71),
    "Vigor":           (5.7, 5.3, 4.7, -0.68, True, 0.58),
    "TQR (recuperação)": (11.5, 11.0, 9.6, -0.83, True, 0.49),
    "Sonolência":      (9.2, 9.9, 11.2, 1.05, True, 0.79),
    "Fadiga mental":   (4.3, 4.8, 5.1, 0.54, True, 0.77),
    "PSS (estresse)":  (23.0, 22.9, 21.8, -0.42, False, 0.73),
}
ESTIMULO = {  # o que a sessão entregou, contra o que ela custou
    "FC de pico (bpm)": (184, 183, 181, "Friedman p = 0,001"),
    "PSE final (0 a 10)": (8.5, 8.5, 9.1, "Friedman p = 0,004"),
    "Recuperação da FC em 1 min (bpm)": (25.2, 27.4, 27.8, "Friedman p = 0,001"),
    "Deriva cardíaca (%)": (6.7, 8.8, 8.5, "Friedman p = 0,042"),
}

# ── Tabela 71: contraste entre sessões, com fator de Bayes ───────────────
BAYES = {  # dz e fator de Bayes de S1 para S3
    "Fadiga física":  (1.87, "> 10⁵", "decisiva"),
    "Vigor":          (-0.79, "23", "forte"),
    "Fadiga (BRUMS)": (0.65, "6,3", "moderada"),
    "Sonolência":     (0.64, "5,7", "moderada"),
    "TQR (recuperação)": (-0.47, "1,3", "anedótica"),
    "Fadiga mental":  (0.53, "2,5", "anedótica"),
    "PTH (TMD)":      (0.40, "≈ 1", "ausente"),
    "PSS (estresse)": (-0.30, "BF₀₁ 2,0", "a favor da nulidade"),
}

# ── Tabela 33: recuperação noturna e deslocamento da linha de base ───────
RECUPERACAO = {
    "Fadiga física":  (66.8, 3.36),
    "Fadiga (BRUMS)": (69.3, 3.98),
    "PTH (TMD)":      (68.1, 8.70),
    "Vigor":          (113.2, -3.72),
}

# ── Tabela 46: resposta padronizada e proporção acima do MDC ────────────
MDC = {  # SRM agudo, % > MDC agudo, SRM semanal, % > MDC semanal
    "PTH (TMD)":  (0.57, 22, 0.53, 52),
    "Vigor":      (-0.45, 4, -1.18, 52),
    "Fadiga":     (0.59, 19, 0.82, 62),
    "Tensão":     (0.40, 0, -0.59, 24),
    "Depressão":  (0.18, 7, 0.22, 24),
    "Raiva":      (0.13, 15, 0.08, 48),
    "Confusão":   (-0.06, 0, -0.57, 24),
}

# ── Tabela 34: mudança confiável do dia 1 ao dia 7 ──────────────────────
MUDANCA = {  # n, aumento, sem mudança, redução, MDC95
    "Fadiga física":  (21, 14, 7, 0, 2.60),
    "Fadiga (BRUMS)": (21, 8, 12, 1, 4.01),
    "PTH (TMD)":      (21, 8, 11, 2, 8.87),
    "Vigor":          (21, 0, 16, 5, 5.04),
}
# Subir é ruim em todas, menos onde a escala mede recurso e não sintoma.
SOBE_E_BOM = {"Vigor", "TQR (recuperação)"}
AUMENTO_RUIM = {k: k not in SOBE_E_BOM for k in
                list(MUDANCA) + list(SESSOES) + list(RECUPERACAO)}

AMOSTRA = {
    "atletas": 27, "idade": "22,2 ± 3,7 (17,8 a 38,2)",
    "experiencia": "11,3 ± 3,2",
    "posicao": "armadores 44%, pivôs 33%, alas 22%",
    "completos": "19 atletas (70%)",
}
