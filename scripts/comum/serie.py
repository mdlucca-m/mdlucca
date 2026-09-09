#!/usr/bin/env python3
"""Análise de série temporal das variáveis e dos perfis, com bandas.

Sete pontos por série, medidas repetidas dentro de atleta e adesão desigual
entre dias. Esse desenho manda em todas as escolhas deste módulo.

Incerteza. Não há scipy neste ambiente e, mais importante, não há razão
para confiar em distribuição tabelada com n pequeno, distribuições
assimétricas e efeito piso em quatro das seis subescalas. Toda banda e todo
intervalo saem de reamostragem por atleta: a unidade sorteada, com
reposição, é o atleta inteiro, com todas as observações dele. Reamostrar
observações soltas trataria como independentes respostas do mesmo
participante e estreitaria a banda de forma indevida. São 10 mil
reamostragens, semente fixa, e o intervalo é o percentil 2,5 a 97,5.

Decomposição. Cada série é separada em duas partes que somam o observado:
a tendência linear, ajustada por mínimos quadrados sobre o dia, e o desvio
em relação a ela. A fração da variância que a reta explica mede quanto do
movimento é monótono; o resto é o que a reta não descreve, e é onde ficam
os platôs e as reversões. Uma série com R² alto pede leitura de tendência;
uma com R² baixo e derivadas grandes pede leitura de choques.

Derivada, ruído e virada. A derivada é a diferença entre dias consecutivos
da série suavizada por filtro binomial de três pontos. O piso de ruído é o
erro-padrão médio da série, e nenhuma derivada abaixo dele é interpretada.
Um ponto de virada é um dia em que a derivada troca de sinal, isto é, um
máximo ou um mínimo local; ele é chamado de sustentado quando ao menos uma
das duas derivadas que o formam supera o piso. A distinção evita chamar de
virada o que é oscilação amostral, que com sete pontos é frequente.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import classificar as K  # noqa: E402

REPETICOES = 10_000
SEMENTE = 20240421          # data da primeira coleta
_rng = np.random.default_rng(SEMENTE)

ATLETAS = K.ATLETAS
DIAS = np.array(K.DIAS, dtype=float)
VARIAVEIS = list(K.CAMPO_DIARIO)


def _matriz_media(campo: str) -> np.ndarray:
    """Média do atleta em cada dia, em matriz atletas por dias, com nan."""
    m = np.full((len(ATLETAS), len(K.DIAS)), np.nan)
    for i, a in enumerate(ATLETAS):
        for j, d in enumerate(K.DIAS):
            v = [o[campo] for o in K.OBS
                 if o["atleta"] == a and o["dia"] == d and o.get(campo) is not None]
            if v:
                m[i, j] = float(np.mean(v))
    return m


def _matriz_perfil(perfil: str) -> tuple[np.ndarray, np.ndarray]:
    """Contagem no perfil e total de observações, por atleta e por dia."""
    acerto = np.zeros((len(ATLETAS), len(K.DIAS)))
    total = np.zeros((len(ATLETAS), len(K.DIAS)))
    for o, p in zip(K.OBS, K.PERFIL):
        i, j = ATLETAS.index(o["atleta"]), K.DIAS.index(o["dia"])
        total[i, j] += 1
        if p == perfil:
            acerto[i, j] += 1
    return acerto, total


MATRIZ = {v: _matriz_media(c) for v, c in K.CAMPO_DIARIO.items()}
MATRIZ_PERFIL = {p: _matriz_perfil(p) for p in K.ORDEM}


def _media_colunas(m: np.ndarray) -> np.ndarray:
    with np.errstate(invalid="ignore"):
        return np.nanmean(m, axis=0)


def _proporcao(acerto: np.ndarray, total: np.ndarray) -> np.ndarray:
    soma_a, soma_t = acerto.sum(axis=0), total.sum(axis=0)
    return np.where(soma_t > 0, 100.0 * soma_a / np.maximum(soma_t, 1), np.nan)


def _sorteios() -> np.ndarray:
    return _rng.integers(0, len(ATLETAS), size=(REPETICOES, len(ATLETAS)))


_SORTEIOS = _sorteios()


def banda_variavel(nome: str) -> dict:
    """Série diária da variável, com banda de 95% por reamostragem."""
    m = MATRIZ[nome]
    obs = _media_colunas(m)
    amostras = np.empty((REPETICOES, len(K.DIAS)))
    for b in range(REPETICOES):
        amostras[b] = _media_colunas(m[_SORTEIOS[b]])
    lo, hi = np.nanpercentile(amostras, [2.5, 97.5], axis=0)
    return {"serie": obs, "inferior": lo, "superior": hi,
            "erro": np.nanstd(amostras, axis=0)}


def banda_perfil(perfil: str) -> dict:
    """Prevalência diária do perfil, com banda de 95% por reamostragem."""
    acerto, total = MATRIZ_PERFIL[perfil]
    obs = _proporcao(acerto, total)
    amostras = np.empty((REPETICOES, len(K.DIAS)))
    for b in range(REPETICOES):
        s = _SORTEIOS[b]
        amostras[b] = _proporcao(acerto[s], total[s])
    lo, hi = np.nanpercentile(amostras, [2.5, 97.5], axis=0)
    return {"serie": obs, "inferior": lo, "superior": hi,
            "erro": np.nanstd(amostras, axis=0)}


def _ajuste(y: np.ndarray) -> tuple[float, float]:
    """Mínimos quadrados de y sobre o dia. Devolve inclinação e intercepto."""
    bom = ~np.isnan(y)
    if bom.sum() < 3:
        return float("nan"), float("nan")
    x = DIAS[bom]
    a, b = np.polyfit(x, y[bom], 1)
    return float(a), float(b)


def regressao_variavel(nome: str) -> dict:
    m = MATRIZ[nome]
    return _regressao(m, _media_colunas)


def regressao_perfil(perfil: str) -> dict:
    acerto, total = MATRIZ_PERFIL[perfil]
    return _regressao((acerto, total),
                      lambda t: _proporcao(t[0], t[1]))


def _regressao(dados, calcular) -> dict:
    """Reta sobre o dia, com IC da inclinação e da própria reta.

    A inclinação é reportada em unidades da variável por dia. O IC vem da
    mesma reamostragem por atleta usada nas bandas, o que faz com que a
    incerteza da reta herde a estrutura de medidas repetidas.
    """
    def serie(indices=None):
        if isinstance(dados, tuple):
            a, t = dados
            return calcular((a[indices], t[indices]) if indices is not None
                            else (a, t))
        return calcular(dados[indices] if indices is not None else dados)

    y = serie()
    inclinacao, intercepto = _ajuste(y)
    incs = np.empty(REPETICOES)
    retas = np.empty((REPETICOES, len(K.DIAS)))
    for b in range(REPETICOES):
        a_b, b_b = _ajuste(serie(_SORTEIOS[b]))
        incs[b] = a_b
        retas[b] = a_b * DIAS + b_b
    lo, hi = np.nanpercentile(incs, [2.5, 97.5])
    faixa_lo, faixa_hi = np.nanpercentile(retas, [2.5, 97.5], axis=0)
    ajustado = inclinacao * DIAS + intercepto
    bom = ~np.isnan(y)
    ss_tot = float(np.sum((y[bom] - np.mean(y[bom])) ** 2))
    ss_res = float(np.sum((y[bom] - ajustado[bom]) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    # p bilateral por reamostragem: fração de reamostras com sinal oposto,
    # duplicada. É o p de que a inclinação verdadeira seja zero.
    proporcao = float(np.mean(incs * np.sign(inclinacao) <= 0))
    p = min(1.0, 2 * proporcao)
    return {"inclinacao": inclinacao, "intercepto": intercepto,
            "ic_inferior": float(lo), "ic_superior": float(hi),
            "r2": r2, "p": p, "ajustado": ajustado,
            "faixa_inferior": faixa_lo, "faixa_superior": faixa_hi,
            "cruza_zero": bool(lo <= 0 <= hi)}


def suavizar(y: np.ndarray) -> np.ndarray:
    s = y.astype(float).copy()
    s[1:-1] = (y[:-2] + 2 * y[1:-1] + y[2:]) / 4
    return s


def derivada(y: np.ndarray) -> np.ndarray:
    return np.diff(suavizar(y))


def piso(erro: np.ndarray) -> float:
    """Piso de ruído: erro-padrão médio da série, por reamostragem."""
    return float(np.nanmean(erro))


def viradas(y: np.ndarray, limiar: float) -> list[dict]:
    """Dias em que a derivada troca de sinal, com a qualificação de ruído."""
    d = derivada(y)
    saida = []
    for i in range(len(d) - 1):
        if d[i] == 0 or d[i] * d[i + 1] >= 0:
            continue
        dia = K.DIAS[i + 1]
        sustentada = max(abs(d[i]), abs(d[i + 1])) > limiar
        saida.append({"dia": dia, "tipo": "máximo" if d[i] > 0 else "mínimo",
                      "antes": float(d[i]), "depois": float(d[i + 1]),
                      "sustentada": sustentada})
    return saida


def decomposicao(nome: str, perfil: bool = False) -> dict:
    """Reúne série, banda, reta, derivada, piso e viradas de uma série."""
    b = banda_perfil(nome) if perfil else banda_variavel(nome)
    r = regressao_perfil(nome) if perfil else regressao_variavel(nome)
    lim = piso(b["erro"])
    d = derivada(b["serie"])
    return {**b, **r, "piso": lim, "derivada": d,
            "choques": [K.DIAS[i] for i, v in enumerate(d) if abs(v) > lim],
            "viradas": viradas(b["serie"], lim),
            "residuo": b["serie"] - r["ajustado"]}


def d1_d7_variavel(nome: str) -> dict:
    """Comparação pareada do dia 1 com o dia 7, só quem respondeu nos dois."""
    m = MATRIZ[nome]
    par = ~np.isnan(m[:, 0]) & ~np.isnan(m[:, -1])
    dif = m[par, -1] - m[par, 0]
    n = int(par.sum())
    media = float(np.mean(dif))
    dz = media / float(np.std(dif, ddof=1)) if n > 1 else float("nan")
    amostras = np.array([np.mean(dif[_rng.integers(0, n, n)])
                         for _ in range(REPETICOES)])
    lo, hi = np.percentile(amostras, [2.5, 97.5])
    p = min(1.0, 2 * float(np.mean(amostras * np.sign(media) <= 0)))
    return {"n": n, "dia1": float(np.mean(m[par, 0])),
            "dia7": float(np.mean(m[par, -1])), "diferenca": media,
            "ic_inferior": float(lo), "ic_superior": float(hi),
            "dz": dz, "p": p, "cruza_zero": bool(lo <= 0 <= hi)}


def d1_d7_perfil(perfil: str) -> dict:
    """Diferença de prevalência entre o dia 1 e o dia 7, com IC."""
    acerto, total = MATRIZ_PERFIL[perfil]
    def dif(indices):
        a, t = acerto[indices], total[indices]
        p1 = 100.0 * a[:, 0].sum() / max(t[:, 0].sum(), 1)
        p7 = 100.0 * a[:, -1].sum() / max(t[:, -1].sum(), 1)
        return p7 - p1
    todos = np.arange(len(ATLETAS))
    obs = dif(todos)
    amostras = np.array([dif(_SORTEIOS[b]) for b in range(REPETICOES)])
    lo, hi = np.percentile(amostras, [2.5, 97.5])
    p = min(1.0, 2 * float(np.mean(amostras * np.sign(obs) <= 0)))
    return {"dia1": K.percentual(1)[perfil], "dia7": K.percentual(7)[perfil],
            "diferenca": float(obs), "ic_inferior": float(lo),
            "ic_superior": float(hi), "p": p,
            "cruza_zero": bool(lo <= 0 <= hi)}


DECOMP_VAR = {v: decomposicao(v) for v in VARIAVEIS}
DECOMP_PERFIL = {p: decomposicao(p, perfil=True) for p in K.ORDEM}
D1D7_VAR = {v: d1_d7_variavel(v) for v in VARIAVEIS}
D1D7_PERFIL = {p: d1_d7_perfil(p) for p in K.ORDEM}


if __name__ == "__main__":
    def f(v, c=2):
        return f"{v:.{c}f}".replace(".", ",").replace("-", "−")

    def ic(x, chave_lo="ic_inferior", chave_hi="ic_superior", c=2):
        return "[" + f(x[chave_lo], c) + ", " + f(x[chave_hi], c) + "]"

    print(f"reamostragem por atleta, {REPETICOES} repetições, semente "
          f"{SEMENTE}\n")
    print("── variáveis: reta sobre o dia ──")
    print(f'{"variável":16s}{"inclinação":>12s}{"IC 95%":>20s}{"R²":>7s}'
          f'{"p":>8s}{"piso":>7s}  choques / viradas')
    for v in VARIAVEIS:
        d = DECOMP_VAR[v]
        vir = ", ".join(f"{x['dia']}{'*' if x['sustentada'] else ''}"
                        for x in d["viradas"]) or "nenhuma"
        print(f'{v:16s}{f(d["inclinacao"], 3):>12s}{ic(d, c=3):>20s}'
              f'{f(d["r2"], 2):>7s}{f(d["p"], 3):>8s}{f(d["piso"], 2):>7s}  '
              f'{d["choques"]} / {vir}')
    print("\n── perfis: reta sobre o dia ──")
    for p in K.ORDEM:
        d = DECOMP_PERFIL[p]
        vir = ", ".join(f"{x['dia']}{'*' if x['sustentada'] else ''}"
                        for x in d["viradas"]) or "nenhuma"
        print(f'{p:22s}{f(d["inclinacao"], 2):>10s}{ic(d):>20s}'
              f'{f(d["r2"], 2):>7s}{f(d["p"], 3):>8s}{f(d["piso"], 2):>7s}  '
              f'{d["choques"]} / {vir}')
    print("\n── dia 1 contra dia 7, variáveis pareadas por atleta ──")
    print(f'{"variável":16s}{"n":>4s}{"dia 1":>8s}{"dia 7":>8s}'
          f'{"dif.":>8s}{"IC 95%":>20s}{"dz":>7s}{"p":>8s}')
    for v in VARIAVEIS:
        x = D1D7_VAR[v]
        print(f'{v:16s}{x["n"]:>4d}{f(x["dia1"]):>8s}{f(x["dia7"]):>8s}'
              f'{f(x["diferenca"]):>8s}{ic(x):>20s}'
              f'{f(x["dz"]):>7s}{f(x["p"], 3):>8s}')
    print("\n── dia 1 contra dia 7, perfis ──")
    for p in K.ORDEM:
        x = D1D7_PERFIL[p]
        print(f'{p:22s}{f(x["dia1"], 1):>7s}{f(x["dia7"], 1):>7s}'
              f'{f(x["diferenca"], 1):>8s}{ic(x, c=1):>20s}'
              f'{f(x["p"], 3):>8s}')
