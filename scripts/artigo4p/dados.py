#!/usr/bin/env python3
"""Dados dos gráficos analíticos, transcritos das tabelas do estudo.

Cada bloco declara a tabela de origem no relatório completo
(data/ARTIGO_HUMOR_VERSAO_FINAL.docx). Nenhum valor é estimado ou suavizado.
As médias diárias aqui têm duas casas decimais porque vêm da Tabela 20, mais
precisa que a Tabela 53 usada no corpo do artigo; as duas são consistentes
depois do arredondamento.
"""
from __future__ import annotations

DIAS = [1, 2, 3, 4, 5, 6, 7]
DIAS_HIIT = [2, 4, 7]
DIAS_JOGO = [3, 5]

# ── Tabela 20: média diária de cada variável ao longo do microciclo ────────
DIARIO = {
    "PTH (TMD)":      [2.52, 4.61, 2.87, 4.76, 2.19, 4.80, 8.28],
    "Vigor":          [7.61, 5.66, 5.71, 5.28, 5.56, 5.74, 4.49],
    "Fadiga (BRUMS)": [3.96, 5.17, 5.00, 5.76, 5.27, 5.75, 7.46],
    "Fadiga física":  [4.20, 5.59, 5.94, 6.53, 5.93, 6.28, 7.56],
    "Fadiga mental":  [4.63, 4.44, 4.49, 4.38, 4.39, 4.62, 5.05],
    "Tensão":         [2.17, 1.64, 1.13, 1.37, 1.01, 1.49, 0.94],
    "Depressão":      [1.04, 1.23, 0.70, 1.13, 0.69, 1.06, 1.27],
    "Raiva":          [1.98, 1.72, 1.44, 1.37, 0.60, 1.66, 2.59],
    "Confusão":       [0.98, 0.52, 0.30, 0.41, 0.19, 0.59, 0.51],
}
# Aumento do escore é desfavorável em todas as variáveis, menos no vigor.
AUMENTO_DESFAVORAVEL = {k: k != "Vigor" for k in
                        list(DIARIO) + ["Sonolência", "PSS (estresse)"]}

# ── Tabela 19: efeito do dia no modelo misto ──────────────────────────────
EFEITO_DIA = {  # F, eta² parcial, p com FDR, ICC do atleta
    "Fadiga física":  (18.66, 0.200, "< 0,001", 0.47),
    "Vigor":          (8.26, 0.099, "< 0,001", 0.57),
    "Fadiga (BRUMS)": (8.11, 0.098, "< 0,001", 0.59),
    "PTH (TMD)":      (4.98, 0.062, "< 0,001", 0.60),
    "Raiva":          (3.78, 0.048, "0,002", 0.31),
    "Tensão":         (3.64, 0.046, "0,002", 0.71),
    "Confusão":       (3.45, 0.044, "0,003", 0.39),
    "Fadiga mental":  (3.39, 0.043, "0,003", 0.72),
    "Depressão":      (1.55, 0.020, "0,160", 0.68),
}

# ── Tabela 21: perfil de Morgan dia a dia ─────────────────────────────────
PERFIL_DIA = {                                    # dia: (% iceberg, % PTH > 0)
    1: (71.4, 47.6), 2: (48.9, 64.9), 3: (44.0, 54.7), 4: (41.7, 65.0),
    5: (53.5, 50.7), 6: (47.1, 55.9), 7: (32.6, 71.7),
}

# ── Tabela 22: perfis de Parsons-Smith ────────────────────────────────────
PARSONS = {                       # perfil: (global, dia 1, dia 7, HIIT, sem)
    "Superfície":         (56.8, 47.6, 60.9, 58.5, 57.0),
    "Iceberg":            (13.8, 21.4, 6.5, 10.0, 15.9),
    "Submerso":           (9.4, 7.1, 10.9, 8.5, 10.7),
    "Iceberg invertido":  (9.0, 9.5, 6.5, 10.5, 7.5),
    "Barbatana tubarão":  (7.2, 9.5, 10.9, 8.0, 6.1),
    "Everest invertido":  (3.7, 4.8, 4.3, 4.5, 2.8),
}

# ── Tabela 23: métricas do perfil em dias de HIIT e sem HIIT ──────────────
METRICAS_PERFIL = {          # métrica: (HIIT, sem HIIT, dz, ic inf, ic sup, p)
    "Índice iceberg (z)":   (-0.25, 0.08, -0.64, -1.10, -0.30, "0,004"),
    "Eixo vigor e fadiga":  (-0.90, 0.40, -0.67, -1.22, -0.28, "0,003"),
    "PTH (TMD)":            (5.64, 3.25, 0.54, 0.19, 0.99, "0,012"),
}

# ── Tabela 52: efeito do dia de HIIT no modelo misto ──────────────────────
BETA_HIIT = {                            # variável: (beta, ic inf, ic sup, p)
    "PTH (TMD)":      (2.70, 1.12, 4.29, "0,001"),
    "Fadiga (BRUMS)": (0.80, 0.20, 1.40, "0,009"),
    "Vigor":          (-0.70, -1.18, -0.22, "0,004"),
    "Fadiga física":  (0.61, 0.24, 0.97, "0,001"),
    "Sonolência":     (0.61, -0.13, 1.34, "0,105"),
    "PSS (estresse)": (0.52, -0.17, 1.20, "0,140"),
    "Fadiga mental":  (0.26, -0.12, 0.63, "0,180"),
}

# ── Tabela 34: mudança confiável do dia 1 ao dia 7, atleta a atleta ───────
MUDANCA_CONFIAVEL = {          # variável: (n, aumento, sem mudança, redução)
    "Fadiga física":  (21, 14, 7, 0),
    "Fadiga (BRUMS)": (21, 8, 12, 1),
    "PTH (TMD)":      (21, 8, 11, 2),
    "Vigor":          (21, 0, 16, 5),
}

# ── Tabela 65: acúmulo ao longo da semana e resposta aguda ────────────────
ACUMULO = {                  # variável: (delta por dia, traço, dz agudo, p<)
    "PTH (TMD)":      (0.43, 0.59, 0.44, True),
    "Fadiga física":  (0.34, 0.46, 0.76, True),
    "Fadiga (BRUMS)": (0.33, 0.59, 0.45, True),
    "Vigor":          (-0.26, 0.58, -0.39, True),
    "Fadiga mental":  (0.12, 0.72, 0.27, True),
}

ORDEM_GRADE = ["PTH (TMD)", "Vigor", "Fadiga (BRUMS)",
               "Fadiga física", "Fadiga mental", "Tensão",
               "Depressão", "Raiva", "Confusão"]


def inclinacao(serie: list[float]) -> float:
    """Inclinação de mínimos quadrados das médias diárias, por dia."""
    n = len(serie)
    mx = sum(DIAS) / n
    my = sum(serie) / n
    num = sum((x - mx) * (y - my) for x, y in zip(DIAS, serie))
    den = sum((x - mx) ** 2 for x in DIAS)
    return num / den


def reta(serie: list[float]) -> list[float]:
    b = inclinacao(serie)
    a = sum(serie) / len(serie) - b * (sum(DIAS) / len(DIAS))
    return [a + b * x for x in DIAS]


if __name__ == "__main__":
    print(f'{"variável":16s} {"D1":>6s} {"D7":>6s} {"Δ D7-D1":>8s} '
          f'{"incl./dia":>10s} {"Δ/dia misto":>12s}')
    for v in ORDEM_GRADE:
        s = DIARIO[v]
        misto = ACUMULO.get(v, (None,))[0]
        print(f"{v:16s} {s[0]:6.2f} {s[6]:6.2f} {s[6] - s[0]:+8.2f} "
              f"{inclinacao(s):+10.2f} "
              f'{f"{misto:+.2f}" if misto is not None else "n.a.":>12s}')
