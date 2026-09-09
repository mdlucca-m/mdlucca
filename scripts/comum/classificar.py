#!/usr/bin/env python3
"""Classificação das observações nos seis perfis de humor, dia a dia.

Esta é a rotina que a seção 4.6 anunciava como pendente. Ela deixou de ser
pendente quando a base por atleta e por dia foi disponibilizada.

Origem dos dados. data/brums_diario.csv vem da aba "Diário - Treino" do
banco do estudo, com 457 respostas registradas por formulário eletrônico.
Foram descartadas 4 respostas sem identificação do atleta, que impedem a
agregação por participante, e 1 resposta fora da janela dos sete dias, o
que deixa 452 observações de 27 atletas entre 21 e 27 de abril de 2024. O
arquivo do repositório é anonimizado: os nomes foram substituídos por
códigos A01 a A27 e nenhuma data de nascimento foi copiada.

Procedimento de classificação, em três passos.

  1. Padronização. Cada subescala é convertida em escore T de média 50 e
     desvio-padrão 10 contra a média e o desvio-padrão de todas as 452
     observações. A padronização é interna porque não existem normas de
     escore T para handebol, e é a mesma adotada pelo documento de origem
     do estudo. A consequência está declarada no artigo: estes escores T
     não são comparáveis aos de estudos que padronizam contra normas de
     população.

  2. Atribuição ao centroide mais próximo. Cada observação recebe o perfil
     cujo centroide publicado está a menor distância euclidiana quadrática
     no espaço das seis subescalas. Os centroides são os da Amostra A de
     Parsons-Smith, Terry e Machin (2017), Tabela 8, com n de 2364.

  3. Verificação. A rotina confere a distribuição obtida contra a Tabela
     12 do documento de origem, que classificou o dia 1 e o dia 7 por
     método não declarado, e contra a prevalência normativa da Amostra A.

Por que o centroide mais próximo, e não a k-médias semeada. A k-médias
semeada é o procedimento das amostras grandes (Rohlfs, Noce e Wilke, 2024,
com 898 atletas). Aplicada aqui, ela converge, mas desloca o centroide do
perfil superfície em 19,9 pontos T e o do Everest invertido em 20,6, porque
esta amostra tem pouquíssimos casos extremos para sustentá-los. Centroides
deslocados nessa magnitude deixam de significar o que a literatura definiu,
e o rótulo perde comparabilidade, que é a razão de usar os seis perfis. A
k-médias semeada é reportada como análise de sensibilidade, e a
concordância entre os dois procedimentos é calculada.
"""
from __future__ import annotations

import csv
import statistics as st
from math import sqrt
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
BASE = RAIZ / "data" / "brums_diario.csv"

SUBESCALAS = ["Tensão", "Depressão", "Raiva", "Vigor", "Fadiga", "Confusão"]
DIAS = list(range(1, 8))

# Parsons-Smith, Terry e Machin (2017), Tabela 8, Amostra A (n = 2364).
# A correspondência entre número de agrupamento e nome vem da Tabela 7 do
# mesmo artigo, cuja matriz de classificação é diagonal.
CENTROIDES = {
    "Iceberg":              [42.84, 44.98, 46.26, 57.33, 45.72, 44.80],
    "Everest invertido":    [67.70, 87.17, 79.05, 42.50, 68.80, 80.39],
    "Iceberg invertido":    [56.65, 63.86, 59.82, 45.73, 60.80, 63.20],
    "Barbatana de tubarão": [44.42, 48.97, 48.00, 41.12, 64.16, 47.47],
    "Submerso":             [43.23, 46.34, 46.50, 42.52, 46.99, 45.99],
    "Superfície":           [51.90, 50.68, 52.26, 53.51, 51.46, 54.20],
}
# Prevalência da Amostra A, calculada da Tabela 7 do mesmo artigo.
NORMATIVO = {"Iceberg": 695, "Everest invertido": 64, "Iceberg invertido": 244,
             "Barbatana de tubarão": 409, "Submerso": 603, "Superfície": 349}
N_NORMATIVO = sum(NORMATIVO.values())

ORDEM = ["Iceberg", "Superfície", "Submerso", "Barbatana de tubarão",
         "Iceberg invertido", "Everest invertido"]
FAVORAVEL = ["Iceberg"]
NEUTRO = ["Superfície", "Submerso"]
RISCO = ["Barbatana de tubarão", "Iceberg invertido", "Everest invertido"]

# Tabela 12 do documento de origem, para conferência. O método daquele
# documento não está declarado, e por isso a comparação é de referência, e
# não de validação.
ORIGEM = {"Iceberg": (17, 8), "Superfície": (11, 13), "Everest invertido": (6, 4),
          "Iceberg invertido": (4, 3), "Submerso": (3, 5),
          "Barbatana de tubarão": (1, 13)}


def carregar() -> list[dict]:
    with open(BASE, encoding="utf-8") as fh:
        linhas = []
        for r in csv.DictReader(fh):
            reg = {"atleta": r["atleta"], "dia": int(r["dia"]),
                   "periodo": r["periodo"], "hora": r["hora"]}
            for s in SUBESCALAS:
                reg[s] = float(r[s])
            for extra in ("PTH", "FadigaFisica", "FadigaMental", "TQR", "PSS",
                          "Epworth"):
                reg[extra] = float(r[extra]) if r[extra] not in ("", None) else None
            linhas.append(reg)
    return linhas


OBS = carregar()
MEDIA = {s: st.mean(o[s] for o in OBS) for s in SUBESCALAS}
DESVIO = {s: st.pstdev(o[s] for o in OBS) for s in SUBESCALAS}


def em_t(o: dict) -> list[float]:
    return [50.0 + 10.0 * (o[s] - MEDIA[s]) / DESVIO[s] for s in SUBESCALAS]


def _distancia(t: list[float], centro: list[float]) -> float:
    return sum((a - b) ** 2 for a, b in zip(t, centro))


def atribuir(centroides: dict) -> list[str]:
    return [min(centroides, key=lambda p: _distancia(em_t(o), centroides[p]))
            for o in OBS]


def kmedias_semeada(maximo: int = 100) -> tuple[list[str], dict, int]:
    """K-médias com sementes nos centroides publicados, para sensibilidade."""
    cent = {p: list(v) for p, v in CENTROIDES.items()}
    ts = [em_t(o) for o in OBS]
    rotulos = []
    for iteracao in range(maximo):
        rotulos = [min(cent, key=lambda p: _distancia(t, cent[p])) for t in ts]
        novo = {}
        for p in cent:
            grupo = [t for t, r in zip(ts, rotulos) if r == p]
            novo[p] = ([st.mean(x[i] for x in grupo) for i in range(6)]
                       if grupo else cent[p])
        if max(abs(novo[p][i] - cent[p][i]) for p in cent for i in range(6)) < 1e-9:
            return rotulos, novo, iteracao
        cent = novo
    return rotulos, cent, maximo


PERFIL = atribuir(CENTROIDES)
PERFIL_KM, CENTROIDES_KM, _ITERACOES = kmedias_semeada()
CONCORDANCIA = sum(1 for a, b in zip(PERFIL, PERFIL_KM) if a == b) / len(OBS)
DESLOCAMENTO = {p: max(abs(CENTROIDES_KM[p][i] - CENTROIDES[p][i])
                       for i in range(6)) for p in CENTROIDES}

N_DIA_OBS = {d: sum(1 for o in OBS if o["dia"] == d) for d in DIAS}
N_DIA_ATLETAS = {d: len({o["atleta"] for o in OBS if o["dia"] == d}) for d in DIAS}
ATLETAS = sorted({o["atleta"] for o in OBS})


# Nomes das variáveis contínuas como o resto do projeto os usa, e a coluna
# correspondente na base bruta.
CAMPO_DIARIO = {
    "PTH (TMD)": "PTH", "Vigor": "Vigor", "Fadiga (BRUMS)": "Fadiga",
    "Fadiga física": "FadigaFisica", "Fadiga mental": "FadigaMental",
    "Tensão": "Tensão", "Depressão": "Depressão", "Raiva": "Raiva",
    "Confusão": "Confusão",
}


def medias_diarias() -> dict:
    """Média diária de cada variável, pela estimativa em dois passos.

    Agrega primeiro por atleta dentro do dia e só depois entre atletas, de
    modo que quem respondeu mais vezes não pesa mais na média do dia.
    """
    saida = {}
    for nome, campo in CAMPO_DIARIO.items():
        serie = []
        for d in DIAS:
            por_atleta = {}
            for o in OBS:
                if o["dia"] == d and o.get(campo) is not None:
                    por_atleta.setdefault(o["atleta"], []).append(o[campo])
            serie.append(st.mean(st.mean(v) for v in por_atleta.values())
                         if por_atleta else float("nan"))
        saida[nome] = serie
    return saida


NEGATIVAS = ["Tensão", "Depressão", "Raiva", "Fadiga", "Confusão"]


def perfil_morgan() -> dict:
    """Critério de Morgan sobre escores brutos, dia a dia.

    Devolve, para cada dia, o percentual de observações em perfil iceberg,
    definido como vigor acima de todas as cinco subescalas negativas, e o
    percentual em humor perturbado, definido como perturbação total do
    humor acima de zero. As duas regras reproduzem a Tabela 21 do relatório
    completo dentro de dois pontos percentuais, o que confirma que era esse
    o critério ali adotado.
    """
    saida = {}
    for d in DIAS:
        sub = [o for o in OBS if o["dia"] == d]
        ice = sum(1 for o in sub if all(o["Vigor"] > o[s] for s in NEGATIVAS))
        per = sum(1 for o in sub if o["PTH"] is not None and o["PTH"] > 0)
        saida[d] = (100.0 * ice / len(sub), 100.0 * per / len(sub))
    return saida


def descritivas() -> dict:
    """Média, desvio, mediana, intervalo interquartil, assimetria, curtose
    e percentual de respostas no valor mínimo, por subescala."""
    def quantil(v, q):
        v = sorted(v)
        pos = q * (len(v) - 1)
        i = int(pos)
        return v[i] + (pos - i) * (v[min(i + 1, len(v) - 1)] - v[i])

    saida = {}
    for nome, campo in [("PTH (TMD)", "PTH")] + [(s, s) for s in SUBESCALAS]:
        v = [o[campo] for o in OBS if o.get(campo) is not None]
        m, dp = st.mean(v), st.pstdev(v)
        z = [(x - m) / dp for x in v] if dp else [0.0] * len(v)
        assim = sum(x ** 3 for x in z) / len(z)
        curt = sum(x ** 4 for x in z) / len(z) - 3.0
        # O efeito piso só faz sentido onde o zero é o mínimo da escala. A
        # perturbação total do humor é escore composto, vai de menos 16 a
        # 80 e não tem piso: para ela o campo fica vazio. O relatório de
        # origem declarava 21,9% ali, valor que a base não reproduz por
        # nenhuma definição de piso testada.
        piso = (None if campo == "PTH"
                else 100.0 * sum(1 for x in v if x == 0) / len(v))
        saida[nome] = (m, dp, quantil(v, 0.5), quantil(v, 0.75) - quantil(v, 0.25),
                       assim, curt, piso)
    return saida


def percentis() -> dict:
    """Percentis 5, 25, 50, 75 e 95 de cada subescala e da PTH."""
    def quantil(v, q):
        v = sorted(v)
        pos = q * (len(v) - 1)
        i = int(pos)
        return v[i] + (pos - i) * (v[min(i + 1, len(v) - 1)] - v[i])

    saida = {}
    for nome, campo in [("PTH (TMD)", "PTH")] + [(s, s) for s in SUBESCALAS]:
        v = [o[campo] for o in OBS if o.get(campo) is not None]
        saida[nome] = tuple(round(quantil(v, q)) for q in (.05, .25, .5, .75, .95))
    return saida


def contagem(dia: int, rotulos: list[str] = None) -> dict:
    r = rotulos if rotulos is not None else PERFIL
    return {p: sum(1 for o, x in zip(OBS, r) if o["dia"] == dia and x == p)
            for p in ORDEM}


def percentual(dia: int, rotulos: list[str] = None) -> dict:
    c = contagem(dia, rotulos)
    n = N_DIA_OBS[dia]
    return {p: 100.0 * v / n for p, v in c.items()}


SERIE = {p: [percentual(d)[p] for d in DIAS] for p in ORDEM}
CONTAGEM = {p: [contagem(d)[p] for d in DIAS] for p in ORDEM}


def faixa(nome: str, dia: int) -> float:
    grupos = {"Favorável": FAVORAVEL, "Neutro": NEUTRO, "De risco": RISCO}[nome]
    return sum(percentual(dia)[p] for p in grupos)


SERIE_FAIXA = {nome: [faixa(nome, d) for d in DIAS]
               for nome in ("Favorável", "Neutro", "De risco")}


def erro_padrao(p: float, n: int) -> float:
    q = p / 100.0
    return 100.0 * sqrt(max(q * (1 - q), 0.0) / n)


PISO = {p: sum(erro_padrao(SERIE[p][i], N_DIA_OBS[d])
               for i, d in enumerate(DIAS)) / len(DIAS) for p in ORDEM}


def suavizar(serie: list[float]) -> list[float]:
    s = list(serie)
    for i in range(1, len(serie) - 1):
        s[i] = (serie[i - 1] + 2 * serie[i] + serie[i + 1]) / 4
    return s


SUAVE = {p: suavizar(SERIE[p]) for p in ORDEM}
DERIVADA = {p: [SUAVE[p][i + 1] - SUAVE[p][i] for i in range(len(DIAS) - 1)]
            for p in ORDEM}


def dias_de_choque(perfil: str) -> list[int]:
    return [DIAS[i] for i, d in enumerate(DERIVADA[perfil])
            if abs(d) > PISO[perfil]]


def cruzar(a: list[float], b: list[float]) -> list[float]:
    saida = []
    dif = [x - y for x, y in zip(a, b)]
    for i in range(len(dif) - 1):
        if dif[i] == 0 or dif[i] * dif[i + 1] >= 0:
            continue
        saida.append(DIAS[i] + dif[i] / (dif[i] - dif[i + 1]))
    return saida


if __name__ == "__main__":
    print(f"{len(OBS)} observações de {len(ATLETAS)} atletas em {len(DIAS)} dias\n")
    print(f'{"perfil":22s}' + "".join(f'{"d"+str(d):>11s}' for d in DIAS)
          + f'{"semana":>11s}{"norma":>8s}')
    for p in ORDEM:
        linha = "".join(f"{CONTAGEM[p][i]:4d} ({SERIE[p][i]:4.1f})"
                        for i in range(len(DIAS)))
        tot = sum(CONTAGEM[p])
        print(f"{p:22s}{linha}{tot:5d} ({100*tot/len(OBS):4.1f})"
              f"{100*NORMATIVO[p]/N_NORMATIVO:7.1f}")
    print(f'{"n de observações":22s}'
          + "".join(f"{N_DIA_OBS[d]:11d}" for d in DIAS) + f"{len(OBS):11d}")
    print(f'{"n de atletas":22s}'
          + "".join(f"{N_DIA_ATLETAS[d]:11d}" for d in DIAS))

    print("\nfaixas de significado, por dia:")
    for nome, s in SERIE_FAIXA.items():
        print(f"  {nome:11s}" + "".join(f"{v:8.1f}" for v in s))

    print("\npiso de ruído e dias de choque:")
    for p in ORDEM:
        print(f"  {p:22s} piso {PISO[p]:5.2f} p.p.  choques em "
              f"{dias_de_choque(p) or 'nenhum'}")

    print("\nconferência contra a Tabela 12 do documento de origem:")
    for p in ORDEM:
        print(f"  {p:22s} dia 1: {contagem(1)[p]:2d} obtido x {ORIGEM[p][0]:2d} "
              f"declarado | dia 7: {contagem(7)[p]:2d} x {ORIGEM[p][1]:2d}")

    print(f"\nsensibilidade: k-médias semeada convergiu em {_ITERACOES} iterações, "
          f"concordância de {100*CONCORDANCIA:.1f}%")
    for p in ORDEM:
        print(f"  {p:22s} centroide deslocado em até {DESLOCAMENTO[p]:5.2f} pontos T")

    c = cruzar(SUAVE["Iceberg"], SUAVE["Barbatana de tubarão"])
    print("\niceberg cruza a barbatana de tubarão em:",
          ", ".join(f"{d:.2f}" for d in c) or "nunca")
