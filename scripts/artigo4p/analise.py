#!/usr/bin/env python3
"""Análise descritiva e de sensibilidade por tipo de estímulo.

O microciclo alterna, nos cinco primeiros dias, repouso, HIIT, jogo, HIIT e
jogo. Esse bloco permite comparar dois dias de HIIT (2 e 4) e dois dias de jogo
(3 e 5) entre si e contra o repouso (dia 1), sem que a comparação seja
contaminada pelo acúmulo dos dias finais. Os dias 6 e 7 entram como condição de
acúmulo, nunca na média do HIIT.

As médias diárias vêm da estimativa em dois passos, que agrega primeiro por
atleta e só depois por dia, e por isso já corrige a pseudorreplicação. O
relatório completo também traz a média bruta por dia, com valores distintos; a
nota de reconciliação daquele relatório registra a divergência. Aqui vale a
estimativa em dois passos, que é a série usada pelo próprio relatório na seção
sobre o comportamento de cada variável ao longo da semana.

Fontes, todas do relatório completo (data/ARTIGO_HUMOR_VERSAO_FINAL.docx):
  · médias diárias em dois passos .............. Tabela 19
  · efeito do dia no modelo misto .............. Tabela 19 de resultados
  · resposta aguda pré e pós, com IC ........... Tabela 24
  · efeito piso por subescala .................. Tabela 3
  · ICC(2,1) entre dias ........................ Tabela 57

Nenhum valor é estimado. As médias por condição são a média aritmética das
médias diárias dos dias que compõem cada condição.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import dados  # noqa: E402

BASELINE = [1]
HIIT = [2, 4]
JOGO = [3, 5]
ACUMULO = [6, 7]

# Nome curto usado no artigo e chave correspondente em dados.py.
CHAVE = {
    "PTH": "PTH (TMD)",
    "Vigor": "Vigor",
    "Fadiga": "Fadiga (BRUMS)",
    "Tensão": "Tensão",
    "Depressão": "Depressão",
    "Raiva": "Raiva",
    "Confusão": "Confusão",
}
ORDEM = list(CHAVE)
DIARIO = {curto: dados.DIARIO[chave] for curto, chave in CHAVE.items()}

# Tabela 19 de resultados: efeito do dia no modelo misto (F, eta², p com FDR).
EFEITO_DIA = {curto: dados.EFEITO_DIA[chave] for curto, chave in CHAVE.items()}

# Tabela 24: resposta aguda pré e pós, corrigida a pseudorreplicação.
AGUDO = {                    # dz, IC inferior, IC superior, p com FDR, sobrevive
    "Fadiga":    (0.45, 0.23, 0.66, "0,003", True),
    "PTH":       (0.44, 0.20, 0.70, "0,004", True),
    "Vigor":     (-0.39, -0.61, -0.16, "0,005", True),
    "Depressão": (0.19, -0.03, 0.36, "0,133", False),
    "Tensão":    (0.15, -0.01, 0.30, "0,131", False),
    "Raiva":     (0.14, -0.10, 0.34, "0,310", False),
    "Confusão":  (-0.04, -0.21, 0.10, "0,680", False),
}
# Tabela 3: percentual de respostas no valor mínimo da subescala.
PISO = {"PTH": 21.9, "Vigor": 8.6, "Fadiga": 7.7, "Tensão": 49.6,
        "Depressão": 67.1, "Raiva": 59.6, "Confusão": 80.5}
# Tabela 57: ICC(2,1) entre dias, com o erro-padrão de medida e o MDC.
ICC = {"PTH": 0.76, "Vigor": 0.70, "Fadiga": 0.69, "Tensão": 0.88,
       "Depressão": 0.85, "Raiva": 0.55, "Confusão": 0.50}

MENOS = "−"  # sinal de menos, não hífen nem traço de meia risca


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
        f, eta, p_dia, icc_misto = EFEITO_DIA[dim]
        dz, ic_inf, ic_sup, p_agudo, sobrevive = AGUDO[dim]
        saida.append({
            "dimensao": dim, "baseline": base, "hiit": c["hiit"],
            "jogo": c["jogo"], "acumulo": c["acumulo"],
            "d_hiit": c["hiit"] - base, "d_jogo": c["jogo"] - base,
            "p_hiit": variacao_percentual(c["hiit"], base),
            "p_jogo": variacao_percentual(c["jogo"], base),
            "dif_hj": c["hiit"] - c["jogo"],
            "resposta_hiit": abs(variacao_percentual(c["hiit"], base)),
            "resposta_jogo": abs(variacao_percentual(c["jogo"], base)),
            "especificidade": abs(c["hiit"] - c["jogo"]) / base * 100,
            "f_dia": f, "eta": eta, "p_dia": p_dia, "icc_misto": icc_misto,
            "piso": PISO[dim], "icc": ICC[dim],
            "dz_agudo": dz, "ic_inf": ic_inf, "ic_sup": ic_sup,
            "p_agudo": p_agudo, "sobrevive": sobrevive,
        })
    return saida


def ranking(chave: str) -> list[str]:
    return [x["dimensao"] for x in
            sorted(sensibilidade(), key=lambda x: -x[chave])]


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
          f'{"acúmulo":>8s} {"Δ%HIIT":>8s} {"Δ%jogo":>8s} {"espec.":>7s} '
          f'{"η²":>6s}')
    for x in sensibilidade():
        print(f'{x["dimensao"]:11s} {br(x["baseline"],2):>8s} '
              f'{br(x["hiit"],2):>7s} {br(x["jogo"],2):>7s} '
              f'{br(x["acumulo"],2):>8s} {sinal(x["p_hiit"],0):>8s} '
              f'{sinal(x["p_jogo"],0):>8s} {br(x["especificidade"],0):>7s} '
              f'{br(x["eta"],3):>6s}')
    print()
    print("mais responsiva ao HIIT :", " > ".join(ranking("resposta_hiit")[:4]))
    print("mais responsiva ao jogo :", " > ".join(ranking("resposta_jogo")[:4]))
    print("mais específica ao tipo :", " > ".join(ranking("especificidade")[:4]))
