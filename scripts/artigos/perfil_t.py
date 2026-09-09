#!/usr/bin/env python3
"""Perfil de humor do grupo em escores T, dia a dia.

Por que este módulo existe. A prevalência dos seis perfis é conhecida
apenas no dia 1 e no dia 7, porque a classificação nos seis perfis é feita
observação a observação e a base por atleta e por dia não está disponível
neste repositório. O que existe para os sete dias é a média diária de cada
subescala, e é dela que sai a análise abaixo: o perfil de humor do grupo,
em escores T, em cada um dos sete dias.

A distinção importa e é declarada em todo lugar onde o resultado aparece.
O perfil do grupo é a forma que o atleta médio assume em cada dia; ele não
é, e não substitui, a distribuição dos atletas pelos seis perfis. Uma
média pode ter forma de iceberg com metade do elenco fora dele.

Padronização. T = 50 + 10 vezes o desvio da média, com média e
desvio-padrão da própria amostra, conforme a Tabela 3 do estudo de perfil,
que é o mesmo procedimento adotado por aquele documento para classificar o
dia 1 e o dia 7. A padronização é interna, e por isso os escores T deste
estudo não são comparáveis aos escores T de estudos que padronizam contra
normas populacionais. Essa foi, aliás, a origem da divergência entre as
três séries de classificação documentada em AUDITORIA_PERFIS_HUMOR.docx.

Amplitude esperada. O desvio-padrão usado no denominador é o de todas as
observações, e reúne a variância entre atletas e a variância entre dias.
Como a variância entre atletas é a maior das duas, a média de um dia se
afasta pouco de 50 mesmo quando a mudança na escala bruta é grande. Os
escores T daqui descrevem, portanto, a posição do dia dentro da própria
semana, e não a intensidade do estado.
"""
from __future__ import annotations

import sys
from math import sqrt
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI.parent / "artigo4p"))
import fonte as F  # noqa: E402
from dados import DIARIO, DIAS, N_DIA  # noqa: E402

# Ordem de leitura do gráfico de perfil, com o vigor primeiro, como nas
# figuras de Morgan e nas dos seis perfis.
SUBESCALAS = ["Vigor", "Fadiga", "Tensão", "Depressão", "Raiva", "Confusão"]
_CHAVE = {"Fadiga": "Fadiga (BRUMS)"}

# Faixa central adotada para dizer que uma subescala está sobre a média.
# É escolha operacional deste estudo, declarada no método: meio desvio para
# cada lado, isto é, T entre 45 e 55.
FAIXA_CENTRAL = 5.0


def t_escore(subescala: str, bruto: float) -> float:
    media, desvio = F.DESCRITIVA[subescala][0], F.DESCRITIVA[subescala][1]
    return 50.0 + 10.0 * (bruto - media) / desvio


PERFIL_T_DIA = {
    d: {s: t_escore(s, DIARIO[_CHAVE.get(s, s)][i]) for s in SUBESCALAS}
    for i, d in enumerate(DIAS)
}


def posicao(t: float) -> str:
    if t > 50 + FAIXA_CENTRAL:
        return "acima"
    if t < 50 - FAIXA_CENTRAL:
        return "abaixo"
    return "na média"


def assinatura(dia: int) -> dict:
    """Descreve a forma do dia: posição de cada subescala e extremos."""
    p = PERFIL_T_DIA[dia]
    negativas = {s: p[s] for s in SUBESCALAS if s != "Vigor"}
    return {
        "posicoes": {s: posicao(v) for s, v in p.items()},
        "vigor": p["Vigor"],
        "maior_negativa": max(negativas, key=negativas.get),
        "maior_negativa_t": max(negativas.values()),
        "amplitude": max(p.values()) - min(p.values()),
        "vigor_acima_da_fadiga": p["Vigor"] > p["Fadiga"],
    }


def piso_t(dia: int) -> float:
    """Erro-padrão da média diária, em unidades de escore T.

    Vale exatamente 10 dividido pela raiz do n do dia, e não depende da
    subescala: como T reescala pelo desvio-padrão da amostra, o
    erro-padrão da média, que é o desvio sobre a raiz do n, vira 10 sobre
    a raiz do n. É esse o limiar abaixo do qual a distância de um escore T
    à média não é distinguível de flutuação amostral.
    """
    return 10.0 / sqrt(N_DIA[dia])


PISO_T = {d: piso_t(d) for d in DIAS}
PISO_T_MEDIO = sum(PISO_T.values()) / len(DIAS)

# Amplitude do perfil: distância entre a subescala mais alta e a mais
# baixa do dia. Mede o quanto o perfil tem forma, e não em que direção. Um
# perfil achatado tem amplitude próxima de zero, e um perfil marcado, seja
# iceberg ou invertido, tem amplitude alta.
AMPLITUDE = {d: max(PERFIL_T_DIA[d].values()) - min(PERFIL_T_DIA[d].values())
             for d in DIAS}
# Diferença entre vigor e fadiga em unidades T, que é o eixo energético.
GAP_ENERGIA = {d: PERFIL_T_DIA[d]["Vigor"] - PERFIL_T_DIA[d]["Fadiga"]
               for d in DIAS}


def cruzamento_da_media(subescala: str) -> list[float]:
    """Dias em que a subescala cruza a linha média de T igual a 50."""
    serie = [PERFIL_T_DIA[d][subescala] for d in DIAS]
    saida = []
    for i in range(len(serie) - 1):
        a, b = serie[i] - 50.0, serie[i + 1] - 50.0
        if a == 0 or a * b >= 0:
            continue
        saida.append(DIAS[i] + a / (a - b))
    return saida


# ══════════════════════════ o que falta para a curva dos seis perfis ═══
# A rotina abaixo produz a prevalência diária dos seis perfis assim que a
# base por atleta e por dia existir. Ela não é executada porque essa base
# não está no repositório, e nenhum número dela entra no manuscrito. Fica
# registrada para que o cálculo seja um comando, e não um reprojeto, e
# para que o procedimento esteja auditável desde já.
def prevalencia_diaria(observacoes: list[dict]) -> dict:
    """Prevalência dos seis perfis em cada dia.

    Espera uma lista de observações, cada uma com as chaves dia, atleta e
    os seis escores brutos. Padroniza contra a média e o desvio de toda a
    amostra, exatamente como em t_escore, classifica cada observação pelo
    centroide mais próximo em distância euclidiana e devolve a contagem e
    o percentual por perfil em cada dia.

    Exige CENTROIDES, que são os centroides dos seis agrupamentos em
    escores T. Eles precisam vir da mesma fonte usada para classificar o
    dia 1 e o dia 7, sob pena de repetir a divergência entre séries já
    documentada. Enquanto essa fonte não estiver declarada, a função
    levanta erro em vez de devolver número.
    """
    raise NotImplementedError(
        "Faltam duas coisas: a base por atleta e por dia, e a declaração "
        "explícita dos centroides usados para classificar o dia 1 e o dia "
        "7. Sem as duas, a prevalência diária não é reproduzível.")


if __name__ == "__main__":
    print("Perfil de humor do grupo em escores T, por dia\n")
    print(f'{"dia":>4}', "".join(f"{s:>11s}" for s in SUBESCALAS),
          f'{"amplit.":>9s}')
    for d in DIAS:
        p = PERFIL_T_DIA[d]
        a = assinatura(d)
        print(f"{d:>4}", "".join(f"{F.br(p[s], 1):>11s}" for s in SUBESCALAS),
              f"{F.br(a['amplitude'], 1):>9s}")
    print(f"\npiso de ruído médio: {F.br(PISO_T_MEDIO, 2)} pontos T "
          f"(10 sobre a raiz do n do dia)\n")
    print(f'{"dia":>4} {"amplitude":>10s} {"acima do piso":>14s} '
          f'{"vigor − fadiga":>15s}')
    for d in DIAS:
        print(f"{d:>4} {F.br(AMPLITUDE[d], 1):>10s} "
              f"{'sim' if AMPLITUDE[d] > 2 * PISO_T[d] else 'não':>14s} "
              f"{F.sinal(GAP_ENERGIA[d], 1):>15s}")
