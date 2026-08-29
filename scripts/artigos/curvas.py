#!/usr/bin/env python3
"""Análise das curvas diárias: suavização, derivada e pontos de cruzamento.

Toda a seção analítica do Artigo 1 sobre o comportamento das variáveis ao
longo da semana sai daqui. Nenhum valor é digitado à mão: as séries vêm de
dados.DIARIO, que é a estimativa em dois passos do relatório completo, e
tudo o mais é derivado delas pelas funções abaixo.

Três operações, na ordem em que o artigo as usa:

  suavizar   filtro binomial de três pontos, pesos 1, 2 e 1, extremidades
             preservadas. É o de menor ordem capaz de atenuar a oscilação
             ponto a ponto sem deslocar máximos e mínimos.
  derivar    diferença entre dias consecutivos da série suavizada, em
             unidades da escala por dia.
  cruzar     dia em que duas séries trocam de posição, obtido por
             interpolação linear entre os dois dias adjacentes. Devolve o
             dia fracionário, o valor no cruzamento e a direção da troca.

O piso de ruído de cada série contínua é o erro-padrão da média do dia,
estimado pelo desvio-padrão da subescala dividido pela raiz do n daquele
dia, e promediado na semana. Ele cumpre para as curvas contínuas o mesmo
papel que o erro-padrão binomial cumpre para as proporções de perfil.
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
import fonte as F  # noqa: E402
from dados import DIARIO, DIAS, EFEITO_DIA, N_DIA  # noqa: E402

# Nome curto usado no artigo e chave em dados.DIARIO.
CHAVE = {
    "PTH": "PTH (TMD)",
    "Vigor": "Vigor",
    "Fadiga": "Fadiga (BRUMS)",
    "Fadiga física": "Fadiga física",
    "Fadiga mental": "Fadiga mental",
    "Tensão": "Tensão",
    "Depressão": "Depressão",
    "Raiva": "Raiva",
    "Confusão": "Confusão",
}
SERIE = {curto: list(DIARIO[chave]) for curto, chave in CHAVE.items()}

# Direção favorável: só o vigor melhora ao subir.
SOBE_E_BOM = {"Vigor"}

# Desvio-padrão da subescala, da Tabela 2 (F.DESCRITIVA), para o piso de
# ruído das séries contínuas. As duas fadigas segmentadas não constam da
# tabela descritiva e herdam o desvio da fadiga do BRUMS.
_DP = {curto: F.DESCRITIVA.get(curto, F.DESCRITIVA["Fadiga"])[1]
       for curto in CHAVE}


def suavizar(serie: list[float]) -> list[float]:
    """Filtro binomial 1-2-1 com extremidades preservadas."""
    saida = list(serie)
    for i in range(1, len(serie) - 1):
        saida[i] = (serie[i - 1] + 2 * serie[i] + serie[i + 1]) / 4
    return saida


def derivar(serie: list[float]) -> list[float]:
    """Diferença entre dias consecutivos, em unidades da escala por dia."""
    return [serie[i + 1] - serie[i] for i in range(len(serie) - 1)]


def piso(nome: str) -> float:
    """Erro-padrão médio da média diária, em unidades da escala."""
    return sum(_DP[nome] / sqrt(N_DIA[d]) for d in DIAS) / len(DIAS)


def cruzar(a: list[float], b: list[float]) -> list[tuple[float, float, str]]:
    """Cruzamentos de duas séries, por interpolação linear.

    Devolve (dia fracionário, valor no cruzamento, direção), com direção
    igual a "a sobe" quando a passa a superar b e "a cai" no caso oposto.
    """
    saida = []
    dif = [x - y for x, y in zip(a, b)]
    for i in range(len(dif) - 1):
        d0, d1 = dif[i], dif[i + 1]
        if d0 == 0 or d0 * d1 >= 0:
            continue
        fracao = d0 / (d0 - d1)
        dia = DIAS[i] + fracao
        valor = a[i] + fracao * (a[i + 1] - a[i])
        saida.append((dia, valor, "a sobe" if d1 > 0 else "a cai"))
    return saida


def ruido_par(a: str, b: str) -> float:
    """Piso de ruído da diferença entre duas séries.

    A diferença de duas médias independentes tem erro-padrão igual à raiz
    da soma dos quadrados dos erros-padrão de cada uma. É esse o limiar
    contra o qual a separação entre duas curvas é julgada.
    """
    return sqrt(PISO[a] ** 2 + PISO[b] ** 2)


def reversao(a: str, b: str) -> dict:
    """Testa se a troca de posição entre duas curvas está estabelecida.

    Um cruzamento visível na figura não basta. Para afirmar que duas
    variáveis trocaram de posição é preciso que a separação entre elas
    seja maior que o ruído nas duas pontas da semana, e com sinais
    opostos. Quando só uma das pontas supera o ruído, o que a série mostra
    é divergência a partir de um ponto comum, e não inversão de uma ordem
    previamente estabelecida. A distinção muda a leitura prática e por
    isso é reportada.
    """
    lim = ruido_par(a, b)
    d1 = SERIE[a][0] - SERIE[b][0]
    d7 = SERIE[a][-1] - SERIE[b][-1]
    return {"limiar": lim, "dif_dia1": d1, "dif_dia7": d7,
            "dia1_acima": abs(d1) > lim, "dia7_acima": abs(d7) > lim,
            "troca_de_sinal": d1 * d7 < 0,
            "inversao_estabelecida": abs(d1) > lim and abs(d7) > lim
                                     and d1 * d7 < 0}


def indice(serie: list[float]) -> list[float]:
    """Série reexpressa em percentual do dia 1, que vale 100."""
    base = serie[0]
    return [100.0 * v / base for v in serie]


# ══════════════════════════════════════════════════ séries derivadas ═══
SUAVE = {nome: suavizar(s) for nome, s in SERIE.items()}
DERIVADA = {nome: derivar(SUAVE[nome]) for nome, s in SERIE.items()}
PISO = {nome: piso(nome) for nome in SERIE}
INDICE = {nome: indice(s) for nome, s in SERIE.items()}

# Pares cujo cruzamento tem leitura clínica declarada a priori.
PARES = [
    ("Vigor", "Fadiga",
     "inversão do balanço energético: a fadiga passa a superar o vigor"),
    ("Fadiga mental", "Fadiga física",
     "dissociação das duas fadigas: a física passa a superar a mental"),
    ("Tensão", "Raiva",
     "troca do afeto negativo dominante, de tensão para raiva"),
    ("Tensão", "Depressão",
     "troca do afeto negativo dominante, de tensão para depressão"),
]

CRUZAMENTOS = [(a, b, leitura, cruzar(SUAVE[a], SUAVE[b]), reversao(a, b))
               for a, b, leitura in PARES]


def amplitude(nome: str) -> tuple[float, float, float]:
    """Mínimo, máximo e amplitude da série observada."""
    s = SERIE[nome]
    return min(s), max(s), max(s) - min(s)


def variacao_total(nome: str) -> float:
    """Diferença entre o dia 7 e o dia 1, na escala original."""
    return SERIE[nome][-1] - SERIE[nome][0]


def dias_acima_do_piso(nome: str) -> list[int]:
    """Dias em que a derivada supera o piso de ruído da série."""
    lim = PISO[nome]
    return [DIAS[i] for i, d in enumerate(DERIVADA[nome]) if abs(d) > lim]


if __name__ == "__main__":
    print(f'{"variável":15s} {"dia 1":>7s} {"dia 7":>7s} {"Δ":>7s} '
          f'{"amplit.":>8s} {"piso":>6s} {"η²":>6s}  dias de choque')
    for nome in SERIE:
        chave = CHAVE[nome]
        eta = EFEITO_DIA[chave][1]
        mn, mx, amp = amplitude(nome)
        print(f'{nome:15s} {F.br(SERIE[nome][0], 2):>7s} '
              f'{F.br(SERIE[nome][-1], 2):>7s} '
              f'{F.sinal(variacao_total(nome), 2):>7s} '
              f'{F.br(amp, 2):>8s} {F.br(PISO[nome], 2):>6s} '
              f'{F.br(eta, 3):>6s}  '
              f'{dias_acima_do_piso(nome)}')
    print()
    for a, b, leitura, cruz, rev in CRUZAMENTOS:
        marca = ("INVERSÃO ESTABELECIDA" if rev["inversao_estabelecida"]
                 else "divergência, não inversão")
        dias = ", ".join(F.br(d, 2) for d, _, _ in cruz) or "nenhum"
        print(f"{a:14s} x {b:14s} cruza em {dias:22s} "
              f"limiar {F.br(rev['limiar'], 2)}  "
              f"dia 1 {F.sinal(rev['dif_dia1'], 2)}"
              f"{'*' if rev['dia1_acima'] else ' '}  "
              f"dia 7 {F.sinal(rev['dif_dia7'], 2)}"
              f"{'*' if rev['dia7_acima'] else ' '}  {marca}")
