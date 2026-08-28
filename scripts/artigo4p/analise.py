#!/usr/bin/env python3
"""Análise descritiva e de sensibilidade por tipo de estímulo.

O microciclo alterna, nos cinco primeiros dias, repouso, HIIT, jogo, HIIT e
jogo. Esse bloco permite comparar dois dias de HIIT (2 e 4) e dois dias de jogo
(3 e 5) entre si e contra o repouso (dia 1), sem que a comparação seja
contaminada pelo acúmulo dos dias finais.

Fontes dos dados, todas do conjunto de análises já realizado:
  · médias diárias e teste de Friedman ....... Tabela 6 do relatório de perfil
  · pós-teste de cada dia contra o dia 1 ..... Tabela 8 do relatório de perfil
  · consistência das medidas repetidas ....... Tabela 7 do relatório de perfil
  · resposta aguda pré e pós, corrigida ...... Tabela 23 do relatório completo
  · efeito piso por subescala ................ Tabela 2 do relatório completo

Nenhum valor é estimado. As médias por condição são a média aritmética das
médias diárias dos dias que compõem cada condição.
"""
from __future__ import annotations

BASELINE = [1]
HIIT = [2, 4]
JOGO = [3, 5]
ACUMULO = [6, 7]

# Médias diárias por dimensão, dias 1 a 7.
DIARIO = {
    "Vigor":     [7.5, 5.8, 5.2, 5.3, 5.9, 5.8, 4.7],
    "Fadiga":    [3.7, 5.2, 5.7, 6.3, 5.2, 6.0, 7.5],
    "PTH":       [2.0, 4.7, 4.5, 5.7, 1.8, 4.5, 8.0],
    "Tensão":    [1.8, 1.7, 1.2, 1.4, 1.2, 1.2, 1.3],
    "Depressão": [1.1, 1.2, 0.8, 1.4, 0.5, 1.0, 1.1],
    "Raiva":     [2.0, 1.8, 1.6, 1.5, 0.6, 1.6, 2.4],
    "Confusão":  [1.0, 0.6, 0.3, 0.4, 0.2, 0.5, 0.5],
}
# Friedman entre os sete dias: qui-quadrado, p e W de Kendall.
FRIEDMAN = {
    "Vigor":     (14.7, "0,022", 0.13),
    "Fadiga":    (13.2, "0,040", 0.12),
    "PTH":       (7.6, "0,269", 0.07),
    "Tensão":    (13.2, "0,039", 0.12),
    "Depressão": (1.8, "0,936", 0.02),
    "Raiva":     (12.3, "0,056", 0.11),
    "Confusão":  (25.8, "< 0,001", 0.23),
}
# Pós-teste do modelo misto: dias com diferença significativa contra o dia 1.
DIFERE_DO_BASELINE = {
    "Vigor": {2, 3, 4, 5, 6, 7},
    "Fadiga": {3, 4, 6, 7},
    "Fadiga física": {2, 3, 4, 5, 6, 7},
}
# Resposta aguda dentro da sessão, já corrigida a pseudorreplicação.
AGUDO = {
    "Fadiga":    (0.45, "0,003", True),
    "PTH":       (0.44, "0,004", True),
    "Vigor":     (-0.39, "0,005", True),
    "Depressão": (0.19, "0,133", False),
    "Tensão":    (0.15, "0,131", False),
    "Raiva":     (0.14, "0,310", False),
    "Confusão":  (-0.04, "0,680", False),
}
PISO = {"Vigor": 8.6, "Fadiga": 7.7, "PTH": 21.9, "Tensão": 49.6,
        "Depressão": 67.1, "Raiva": 59.6, "Confusão": 80.5}
ICC = {"Vigor": 0.57, "Fadiga": 0.69, "Tensão": 0.67, "Depressão": 0.79,
       "Raiva": 0.37, "Confusão": 0.50}

ORDEM = ["PTH", "Vigor", "Fadiga", "Tensão", "Depressão", "Raiva", "Confusão"]


def media(dim: str, dias: list[int]) -> float:
    return sum(DIARIO[dim][d - 1] for d in dias) / len(dias)


def condicoes(dim: str) -> dict[str, float]:
    return {"baseline": media(dim, BASELINE), "hiit": media(dim, HIIT),
            "jogo": media(dim, JOGO), "acumulo": media(dim, ACUMULO)}


def variacao_percentual(valor: float, base: float) -> float:
    return 100.0 * (valor - base) / base if base else float("nan")


def sensibilidade() -> list[dict]:
    """Três índices, todos derivados das médias por condição.

    resposta_hiit  quanto a variável se afasta do repouso nos dias de HIIT
    resposta_jogo  quanto se afasta do repouso nos dias de jogo
    especificidade quanto separa uma condição da outra, em unidades do repouso
    """
    saida = []
    for dim in ORDEM:
        c = condicoes(dim)
        base = c["baseline"]
        r_hiit = abs(variacao_percentual(c["hiit"], base))
        r_jogo = abs(variacao_percentual(c["jogo"], base))
        espec = abs(c["hiit"] - c["jogo"]) / base * 100 if base else 0.0
        saida.append({
            "dimensao": dim, "baseline": base, "hiit": c["hiit"],
            "jogo": c["jogo"], "acumulo": c["acumulo"],
            "d_hiit": c["hiit"] - base, "d_jogo": c["jogo"] - base,
            "p_hiit": variacao_percentual(c["hiit"], base),
            "p_jogo": variacao_percentual(c["jogo"], base),
            "dif_hj": c["hiit"] - c["jogo"],
            "resposta_hiit": r_hiit, "resposta_jogo": r_jogo,
            "especificidade": espec,
            "w_kendall": FRIEDMAN[dim][2], "p_friedman": FRIEDMAN[dim][1],
            "qui": FRIEDMAN[dim][0], "piso": PISO[dim],
            "dz_agudo": AGUDO[dim][0], "p_agudo": AGUDO[dim][1],
            "sobrevive": AGUDO[dim][2],
        })
    return saida


def ranking(chave: str) -> list[str]:
    return [x["dimensao"] for x in
            sorted(sensibilidade(), key=lambda x: -x[chave])]


MENOS = "\u2212"  # sinal de menos, não hífen nem traço de meia risca


def br(v: float, casas: int = 2) -> str:
    if abs(v) < 0.5 * 10 ** -casas:
        v = 0.0
    return f"{v:.{casas}f}".replace(".", ",").replace("-", MENOS)


def sinal(v: float, casas: int = 2) -> str:
    """Valor com sinal explícito. Zero sai sem sinal, para não sugerir
    direção onde não há diferença."""
    if abs(v) < 0.5 * 10 ** -casas:
        return f"{0.0:.{casas}f}".replace(".", ",")
    return f"{v:+.{casas}f}".replace(".", ",").replace("-", MENOS)


if __name__ == "__main__":
    print(f'{"dimensão":11s} {"repouso":>8s} {"HIIT":>7s} {"jogo":>7s} '
          f'{"Δ%HIIT":>8s} {"Δ%jogo":>8s} {"espec.":>8s} {"W":>5s}')
    for x in sensibilidade():
        print(f'{x["dimensao"]:11s} {br(x["baseline"],1):>8s} '
              f'{br(x["hiit"],2):>7s} {br(x["jogo"],2):>7s} '
              f'{sinal(x["p_hiit"],0):>8s} {sinal(x["p_jogo"],0):>8s} '
              f'{br(x["especificidade"],0):>8s} {br(x["w_kendall"],2):>5s}')
    print()
    print("mais responsiva ao HIIT :", " > ".join(ranking("resposta_hiit")[:4]))
    print("mais responsiva ao jogo :", " > ".join(ranking("resposta_jogo")[:4]))
    print("mais específica ao tipo :", " > ".join(ranking("especificidade")[:4]))
