#!/usr/bin/env python3
"""Dados dos gráficos analíticos do projeto.

Depois que a base por atleta e por dia foi disponibilizada, as séries que
podem ser calculadas passaram a vir dela, por scripts/comum/classificar.py,
e não mais transcritas das tabelas do relatório: as médias diárias, o número
de atletas por dia e a classificação nos seis perfis. As séries que dependem
de modelos ajustados fora deste repositório continuam transcritas, e cada
bloco declara a tabela de origem no relatório completo
(data/ARTIGO_HUMOR_VERSAO_FINAL.docx). Nenhum valor é estimado ou suavizado.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "comum"))
import classificar as _C  # noqa: E402

DIAS = [1, 2, 3, 4, 5, 6, 7]
DIAS_HIIT = [2, 4, 7]
DIAS_JOGO = [3, 5]

# ── Média diária de cada variável, calculada da base bruta ───────────────
DIARIO = _C.medias_diarias()
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

# ── Perfil de Morgan dia a dia, calculado da base bruta ──────────────────
PERFIL_DIA = _C.perfil_morgan()

# Número de atletas com coleta válida em cada dia, da base bruta.
N_DIA = {d: _C.N_DIA_ATLETAS[d] for d in _C.DIAS}

# ── Classificação nos seis perfis, série adotada ──────────────────────────
# Tabela 12 de Artigo_Perfil_de_humor__handebol.docx. O método daquele
# documento converte os escores em T, com média 50 e desvio 10, que é a escala
# sobre a qual os seis perfis foram definidos na literatura. É a série que a
# auditoria de scripts/auditoria/ elegeu; ver data/AUDITORIA_PERFIS_HUMOR.docx.
# ── Classificação nos seis perfis, calculada a partir da base bruta ──────
# Antes desta versão, os valores vinham da Tabela 12 do documento de origem,
# cujo método de classificação nunca foi declarado, e existiam apenas para o
# primeiro e o último dia. Com a base por atleta e por dia disponível, a
# classificação passou a ser calculada aqui, pelo centroide publicado mais
# próximo sobre escores T internos. O procedimento está em
# scripts/comum/classificar.py e a comparação com a série anterior está
# registrada em data/AUDITORIA_PERFIS_HUMOR.docx.
PERFIS_T = {              # perfil: (n dia 1, % dia 1, n dia 7, % dia 7)
    p: (_C.contagem(1)[p], _C.percentual(1)[p],
        _C.contagem(7)[p], _C.percentual(7)[p])
    for p in _C.ORDEM
}
N_PERFIL = {d: _C.N_DIA_OBS[d] for d in _C.DIAS}
FAVORAVEL = _C.FAVORAVEL
NEUTRO = _C.NEUTRO
RISCO = _C.RISCO


def faixa(nome: str, dia: int) -> float:
    """Soma dos perfis de uma faixa de significado, em percentual.

    Vale para qualquer um dos sete dias, e não apenas para o primeiro e o
    último, desde que a classificação passou a ser calculada da base bruta.
    """
    return _C.faixa(nome, dia)


# ── Tabela 22: classificação por centroide, série substituída ─────────────
# Mantida apenas para a discussão de método: ela padroniza dentro da própria
# amostra e atribui ao centroide mais próximo, o que infla o perfil superfície.
# Não deve ser usada como resultado.
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
