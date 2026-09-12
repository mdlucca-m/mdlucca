"""Testes de hipotese, sem scipy -- porque a casa nao tem scipy.

O painel ja dizia MEDIA, DESVIO, INTERVALO e TAMANHO DE EFEITO, que e a
leitura boa. Falta o que periodico nenhum dispensa: o teste.

O modo de errar aqui nao e a conta -- e a ESCOLHA da conta. Roda-se teste
t por habito, sem conferir se os dados permitiam, e o resultado sai com
tres casas decimais e aparencia de verdade. Por isso as funcoes deste
modulo conferem a suposicao ANTES e dizem qual caminho tomaram:

    normalidade  -> D'Agostino-Pearson (assimetria + curtose)
    variancias   -> Levene na versao da mediana (Brown-Forsythe)
    passou       -> t de Student
    nao passou   -> Mann-Whitney ou Wilcoxon, e a tela diz por que

Tudo sai da mesma maquinaria: a beta incompleta regularizada da o t e o
F, a gama incompleta da o qui-quadrado. Sao as tres distribuicoes de que
um laboratorio de intervencao precisa.
"""
from __future__ import annotations

import math
import statistics
from typing import Any, Sequence

# ----------------------------------------------------------------------
# As tres distribuicoes
# ----------------------------------------------------------------------
_MINUSCULO = 1e-300


def _beta_cf(a: float, b: float, x: float, iteracoes: int = 300) -> float:
    """Fracao continuada de Lentz para a beta incompleta."""
    qab, qap, qam = a + b, a + 1.0, a - 1.0
    c, d = 1.0, 1.0 - qab * x / qap
    if abs(d) < _MINUSCULO:
        d = _MINUSCULO
    d = 1.0 / d
    h = d
    for m in range(1, iteracoes + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1.0 + aa * d
        if abs(d) < _MINUSCULO:
            d = _MINUSCULO
        c = 1.0 + aa / c
        if abs(c) < _MINUSCULO:
            c = _MINUSCULO
        d = 1.0 / d
        h *= d * c
        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1.0 + aa * d
        if abs(d) < _MINUSCULO:
            d = _MINUSCULO
        c = 1.0 + aa / c
        if abs(c) < _MINUSCULO:
            c = _MINUSCULO
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return h


def beta_regularizada(a: float, b: float, x: float) -> float:
    """I_x(a, b) -- a beta incompleta regularizada."""
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    frente = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
                      + a * math.log(x) + b * math.log1p(-x))
    if x < (a + 1.0) / (a + b + 2.0):
        return frente * _beta_cf(a, b, x) / a
    return 1.0 - frente * _beta_cf(b, a, 1.0 - x) / b


def gama_regularizada(a: float, x: float) -> float:
    """P(a, x) -- a gama incompleta inferior regularizada.

    Serie para x pequeno, fracao continuada para x grande: a serie
    converge devagar depois de `a + 1` e a fracao nao converge antes.
    """
    if x <= 0:
        return 0.0
    if x < a + 1.0:
        termo = 1.0 / a
        soma = termo
        for n in range(1, 500):
            termo *= x / (a + n)
            soma += termo
            if abs(termo) < abs(soma) * 1e-16:
                break
        return soma * math.exp(-x + a * math.log(x) - math.lgamma(a))
    b = x + 1.0 - a
    c = 1.0 / _MINUSCULO
    d = 1.0 / b
    h = d
    for i in range(1, 500):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < _MINUSCULO:
            d = _MINUSCULO
        c = b + an / c
        if abs(c) < _MINUSCULO:
            c = _MINUSCULO
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-15:
            break
    return 1.0 - h * math.exp(-x + a * math.log(x) - math.lgamma(a))


def t_cdf(t: float, gl: float) -> float:
    """P(T <= t), t de Student."""
    if gl <= 0:
        return float("nan")
    x = gl / (gl + t * t)
    cauda = 0.5 * beta_regularizada(gl / 2.0, 0.5, x)
    return 1.0 - cauda if t > 0 else cauda


def t_critico(gl: int, conf: float = 0.95) -> float:
    """O t que deixa `conf` no meio."""
    if gl <= 0:
        return float("nan")
    alvo = 1.0 - (1.0 - conf) / 2.0
    baixo, alto = 0.0, 400.0
    for _ in range(200):
        meio = (baixo + alto) / 2.0
        if t_cdf(meio, gl) < alvo:
            baixo = meio
        else:
            alto = meio
    return (baixo + alto) / 2.0


def f_cdf(f: float, gl1: float, gl2: float) -> float:
    """P(F <= f)."""
    if f <= 0:
        return 0.0
    return beta_regularizada(gl1 / 2.0, gl2 / 2.0, gl1 * f / (gl1 * f + gl2))


def qui2_cdf(x: float, gl: float) -> float:
    """P(X <= x), qui-quadrado."""
    if x <= 0:
        return 0.0
    return gama_regularizada(gl / 2.0, x / 2.0)


def p_bicaudal_t(t: float, gl: float) -> float:
    return 2.0 * (1.0 - t_cdf(abs(t), gl))


def p_bicaudal_z(z: float) -> float:
    return 2.0 * (1.0 - statistics.NormalDist().cdf(abs(z)))


# ----------------------------------------------------------------------
# As suposicoes
# ----------------------------------------------------------------------
N_MINIMO_NORMALIDADE = 8


def normalidade(valores: Sequence[float]) -> dict[str, Any]:
    """D'Agostino-Pearson: assimetria e curtose juntas, K2 ~ qui2(2).

    Devolve tambem os pontos do Q-Q, e isso nao e enfeite. Teste de
    normalidade com n pequeno nao detecta desvio nenhum, e com n grande
    reprova qualquer coisa; o desenho e mais honesto que o valor-p, e as
    duas leituras juntas sao mais honestas ainda.
    """
    limpos = [float(v) for v in valores if v is not None and math.isfinite(v)]
    n = len(limpos)
    saida: dict[str, Any] = {"n": n, "qq": _pontos_qq(limpos)}
    if n < N_MINIMO_NORMALIDADE:
        saida.update({"p": None, "normal": None,
                      "aviso": "com %d valores não há como testar normalidade "
                               "(são precisos ao menos %d); olhe o desenho"
                               % (n, N_MINIMO_NORMALIDADE)})
        return saida
    media = statistics.fmean(limpos)
    m2 = sum((v - media) ** 2 for v in limpos) / n
    if m2 <= 0:
        saida.update({"p": None, "normal": None, "aviso": "todos os valores iguais"})
        return saida
    m3 = sum((v - media) ** 3 for v in limpos) / n
    m4 = sum((v - media) ** 4 for v in limpos) / n
    assimetria = m3 / m2 ** 1.5
    curtose = m4 / m2 ** 2

    # assimetria (D'Agostino, 1970)
    y = assimetria * math.sqrt((n + 1) * (n + 3) / (6.0 * (n - 2)))
    beta2 = (3.0 * (n * n + 27 * n - 70) * (n + 1) * (n + 3)
             / ((n - 2.0) * (n + 5) * (n + 7) * (n + 9)))
    w2 = -1.0 + math.sqrt(2.0 * (beta2 - 1.0))
    delta = 1.0 / math.sqrt(0.5 * math.log(w2))
    alfa = math.sqrt(2.0 / (w2 - 1.0))
    z1 = delta * math.asinh(y / alfa)

    # curtose (Anscombe-Glynn, 1983)
    esperada = 3.0 * (n - 1) / (n + 1)
    variancia = (24.0 * n * (n - 2) * (n - 3)
                 / ((n + 1.0) ** 2 * (n + 3) * (n + 5)))
    x = (curtose - esperada) / math.sqrt(variancia)
    raiz_b1 = (6.0 * (n * n - 5 * n + 2) / ((n + 7.0) * (n + 9))
               * math.sqrt(6.0 * (n + 3) * (n + 5) / (n * (n - 2.0) * (n - 3))))
    a = 6.0 + 8.0 / raiz_b1 * (2.0 / raiz_b1 + math.sqrt(1.0 + 4.0 / raiz_b1 ** 2))
    termo = (1.0 - 2.0 / a) / (1.0 + x * math.sqrt(2.0 / (a - 4.0)))
    z2 = ((1.0 - 2.0 / (9.0 * a)) - (termo ** (1.0 / 3.0) if termo > 0
                                     else -((-termo) ** (1.0 / 3.0)))) \
        / math.sqrt(2.0 / (9.0 * a))

    k2 = z1 * z1 + z2 * z2
    p = 1.0 - qui2_cdf(k2, 2)
    saida.update({
        "assimetria": round(assimetria, 3), "curtose": round(curtose, 3),
        "z_assimetria": round(z1, 3), "z_curtose": round(z2, 3),
        "k2": round(k2, 3), "p": round(p, 4), "normal": p >= 0.05,
        "aviso": ("com %d valores o teste detecta pouco: confie mais no desenho"
                  % n) if n < 20 else None,
    })
    return saida


def _pontos_qq(valores: Sequence[float]) -> list[dict]:
    """Quantil observado x quantil esperado sob normalidade."""
    limpos = sorted(float(v) for v in valores if v is not None and math.isfinite(v))
    n = len(limpos)
    if n < 3:
        return []
    normal = statistics.NormalDist()
    media = statistics.fmean(limpos)
    dp = statistics.stdev(limpos) if n > 1 else 0.0
    pontos = []
    for i, valor in enumerate(limpos):
        # posicao de Blom: (i - 3/8) / (n + 1/4)
        p = (i + 1 - 0.375) / (n + 0.25)
        pontos.append({"esperado": round(media + dp * normal.inv_cdf(p), 3),
                       "observado": round(valor, 3)})
    return pontos


def levene(*grupos: Sequence[float]) -> dict[str, Any]:
    """Levene na versao da mediana (Brown-Forsythe): as variancias sao iguais?

    A versao da mediana, e nao a da media, porque e a que aguenta dado
    torto -- e dado de escala clinica e torto quase sempre.
    """
    limpos = [[float(v) for v in g if v is not None and math.isfinite(v)]
              for g in grupos]
    limpos = [g for g in limpos if len(g) > 1]
    k = len(limpos)
    if k < 2:
        return {"p": None, "iguais": None, "aviso": "são precisos dois grupos"}
    n = sum(len(g) for g in limpos)
    z = [[abs(v - statistics.median(g)) for v in g] for g in limpos]
    media_z = [statistics.fmean(g) for g in z]
    media_geral = statistics.fmean([v for g in z for v in g])
    entre = sum(len(g) * (media_z[i] - media_geral) ** 2 for i, g in enumerate(z))
    dentro = sum((v - media_z[i]) ** 2 for i, g in enumerate(z) for v in g)
    if dentro <= 0:
        return {"p": None, "iguais": None, "aviso": "sem variação dentro dos grupos"}
    w = (n - k) / (k - 1.0) * entre / dentro
    p = 1.0 - f_cdf(w, k - 1, n - k)
    return {"w": round(w, 4), "gl1": k - 1, "gl2": n - k,
            "p": round(p, 4), "iguais": p >= 0.05}


# ----------------------------------------------------------------------
# Os testes
# ----------------------------------------------------------------------
def _limpar(valores: Sequence[float]) -> list[float]:
    return [float(v) for v in valores if v is not None and math.isfinite(float(v))]


def t_independente(a: Sequence[float], b: Sequence[float],
                   variancias_iguais: bool = True) -> dict[str, Any]:
    """Duas amostras independentes. Welch quando as variancias diferem."""
    x, y = _limpar(a), _limpar(b)
    if len(x) < 2 or len(y) < 2:
        return {"teste": "t independente", "p": None,
                "aviso": "são precisos ao menos dois valores em cada grupo"}
    mx, my = statistics.fmean(x), statistics.fmean(y)
    vx, vy = statistics.variance(x), statistics.variance(y)
    nx, ny = len(x), len(y)
    if variancias_iguais:
        gl = nx + ny - 2
        agrupada = ((nx - 1) * vx + (ny - 1) * vy) / gl
        erro = math.sqrt(agrupada * (1.0 / nx + 1.0 / ny))
        nome = "t de Student (variâncias iguais)"
    else:
        erro = math.sqrt(vx / nx + vy / ny)
        gl = ((vx / nx + vy / ny) ** 2
              / ((vx / nx) ** 2 / (nx - 1) + (vy / ny) ** 2 / (ny - 1)))
        nome = "t de Welch (variâncias diferentes)"
    if erro <= 0:
        return {"teste": nome, "p": None, "aviso": "sem variação nos dados"}
    t = (mx - my) / erro
    return {"teste": nome, "t": round(t, 4), "gl": round(gl, 2),
            "p": round(p_bicaudal_t(t, gl), 4), "diferenca": round(mx - my, 3),
            "n": [nx, ny]}


def t_pareado(antes: Sequence[float], depois: Sequence[float]) -> dict[str, Any]:
    """Mesmas pessoas em dois momentos. Pares incompletos saem fora.

    Comparar a media de quem foi medido na linha de base com a media de
    quem foi medido no fim NAO e teste pareado: sao pessoas diferentes, e
    quem desistiu costuma ser justamente quem piorou.
    """
    pares = [(float(x), float(y)) for x, y in zip(antes, depois)
             if x is not None and y is not None
             and math.isfinite(float(x)) and math.isfinite(float(y))]
    if len(pares) < 2:
        return {"teste": "t pareado", "p": None,
                "aviso": "são precisos ao menos dois pares completos"}
    dif = [y - x for x, y in pares]
    n = len(dif)
    media = statistics.fmean(dif)
    dp = statistics.stdev(dif)
    if dp <= 0:
        return {"teste": "t pareado", "p": None,
                "aviso": "todas as diferenças são iguais"}
    t = media / (dp / math.sqrt(n))
    return {"teste": "t pareado", "t": round(t, 4), "gl": n - 1,
            "p": round(p_bicaudal_t(t, n - 1), 4),
            "diferenca": round(media, 3), "dp_diferenca": round(dp, 3), "n": n}


def _postos(valores: Sequence[float]) -> tuple[list[float], float]:
    """Postos com empate dividido, e a correcao de empates."""
    ordenados = sorted(range(len(valores)), key=lambda i: valores[i])
    postos = [0.0] * len(valores)
    correcao = 0.0
    i = 0
    while i < len(ordenados):
        j = i
        while j + 1 < len(ordenados) and valores[ordenados[j + 1]] == valores[ordenados[i]]:
            j += 1
        posto = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            postos[ordenados[k]] = posto
        empatados = j - i + 1
        if empatados > 1:
            correcao += empatados ** 3 - empatados
        i = j + 1
    return postos, correcao


def mann_whitney(a: Sequence[float], b: Sequence[float]) -> dict[str, Any]:
    """Duas amostras independentes, sem supor normalidade.

    Aproximacao normal com correcao de empates e de continuidade. Com
    amostra muito pequena a aproximacao fica grosseira, e a funcao diz
    isso em vez de fingir precisao de quatro casas.
    """
    x, y = _limpar(a), _limpar(b)
    nx, ny = len(x), len(y)
    if nx < 2 or ny < 2:
        return {"teste": "Mann-Whitney", "p": None,
                "aviso": "são precisos ao menos dois valores em cada grupo"}
    postos, correcao = _postos(x + y)
    soma_x = sum(postos[:nx])
    u = soma_x - nx * (nx + 1) / 2.0
    n = nx + ny
    media_u = nx * ny / 2.0
    var_u = nx * ny * (n + 1) / 12.0
    if correcao:
        var_u = nx * ny / 12.0 * ((n + 1) - correcao / (n * (n - 1.0)))
    if var_u <= 0:
        return {"teste": "Mann-Whitney", "p": None, "aviso": "sem variação nos dados"}
    z = (abs(u - media_u) - 0.5) / math.sqrt(var_u)
    return {"teste": "Mann-Whitney", "u": round(u, 1), "z": round(z, 4),
            "p": round(p_bicaudal_z(z), 4), "n": [nx, ny],
            "aviso": ("com %d e %d valores a aproximação é grosseira"
                      % (nx, ny)) if min(nx, ny) < 8 else None}


def wilcoxon(antes: Sequence[float], depois: Sequence[float]) -> dict[str, Any]:
    """Mesmas pessoas em dois momentos, sem supor normalidade."""
    pares = [(float(x), float(y)) for x, y in zip(antes, depois)
             if x is not None and y is not None
             and math.isfinite(float(x)) and math.isfinite(float(y))]
    dif = [y - x for x, y in pares if y != x]      # empates saem, como manda o método
    n = len(dif)
    if n < 2:
        return {"teste": "Wilcoxon", "p": None,
                "aviso": "são precisos ao menos dois pares com diferença"}
    postos, correcao = _postos([abs(d) for d in dif])
    mais = sum(p for p, d in zip(postos, dif) if d > 0)
    menos = sum(p for p, d in zip(postos, dif) if d < 0)
    w = min(mais, menos)
    media_w = n * (n + 1) / 4.0
    var_w = n * (n + 1) * (2 * n + 1) / 24.0 - correcao / 48.0
    if var_w <= 0:
        return {"teste": "Wilcoxon", "p": None, "aviso": "sem variação nas diferenças"}
    z = (abs(w - media_w) - 0.5) / math.sqrt(var_w)
    return {"teste": "Wilcoxon", "w": round(w, 1), "z": round(z, 4),
            "p": round(p_bicaudal_z(z), 4), "n": n,
            "aviso": ("com %d pares a aproximação é grosseira" % n) if n < 10 else None}


def anova_medidas_repetidas(medidas: Sequence[Sequence[float]]) -> dict[str, Any]:
    """Tres ou mais momentos nas mesmas pessoas.

    `medidas` e uma lista por PESSOA, cada uma com um valor por momento;
    so entram as pessoas com todos os momentos. Nao testa esfericidade --
    e diz isso: quando ela nao vale, o F fica liberal e o Friedman ao lado
    e a leitura mais segura.
    """
    completas = [[float(v) for v in linha] for linha in medidas
                 if all(v is not None and math.isfinite(float(v)) for v in linha)]
    n = len(completas)
    if n < 2:
        return {"teste": "ANOVA de medidas repetidas", "p": None,
                "aviso": "são precisas ao menos duas pessoas com todos os momentos"}
    k = len(completas[0])
    if k < 3 or any(len(linha) != k for linha in completas):
        return {"teste": "ANOVA de medidas repetidas", "p": None,
                "aviso": "são precisos ao menos três momentos"}
    todos = [v for linha in completas for v in linha]
    geral = statistics.fmean(todos)
    por_momento = [statistics.fmean([linha[j] for linha in completas]) for j in range(k)]
    por_pessoa = [statistics.fmean(linha) for linha in completas]
    sq_total = sum((v - geral) ** 2 for v in todos)
    sq_momento = n * sum((m - geral) ** 2 for m in por_momento)
    sq_pessoa = k * sum((p - geral) ** 2 for p in por_pessoa)
    sq_erro = sq_total - sq_momento - sq_pessoa
    gl_momento, gl_erro = k - 1, (k - 1) * (n - 1)
    if sq_erro <= 0 or gl_erro <= 0:
        return {"teste": "ANOVA de medidas repetidas", "p": None,
                "aviso": "sem variação residual"}
    f = (sq_momento / gl_momento) / (sq_erro / gl_erro)
    eta = sq_momento / (sq_momento + sq_erro)
    return {"teste": "ANOVA de medidas repetidas", "f": round(f, 4),
            "gl1": gl_momento, "gl2": gl_erro,
            "p": round(1.0 - f_cdf(f, gl_momento, gl_erro), 4),
            "eta2_parcial": round(eta, 3), "n": n, "momentos": k,
            "aviso": "a esfericidade não é testada aqui; se ela não valer, o F "
                     "fica liberal — compare com o Friedman ao lado"}


def friedman(medidas: Sequence[Sequence[float]]) -> dict[str, Any]:
    """A versao sem suposicao da ANOVA de medidas repetidas."""
    completas = [[float(v) for v in linha] for linha in medidas
                 if all(v is not None and math.isfinite(float(v)) for v in linha)]
    n = len(completas)
    if n < 2:
        return {"teste": "Friedman", "p": None,
                "aviso": "são precisas ao menos duas pessoas completas"}
    k = len(completas[0])
    if k < 3:
        return {"teste": "Friedman", "p": None, "aviso": "são precisos três momentos"}
    somas = [0.0] * k
    for linha in completas:
        postos, _ = _postos(linha)
        for j in range(k):
            somas[j] += postos[j]
    q = (12.0 / (n * k * (k + 1.0)) * sum(s * s for s in somas)) - 3.0 * n * (k + 1)
    return {"teste": "Friedman", "qui2": round(q, 4), "gl": k - 1,
            "p": round(1.0 - qui2_cdf(q, k - 1), 4), "n": n, "momentos": k}


# ----------------------------------------------------------------------
# Poder e tamanho de amostra
# ----------------------------------------------------------------------
# A conta que deveria vir ANTES da coleta e quase sempre e feita depois --
# quando ja nao muda nada. Um estudo com seis por grupo so detecta efeito
# gigante; se o efeito real for medio, ele vai dar "sem diferenca
# significativa" com altissima probabilidade, e essa frase sera lida como
# "o exercicio nao funcionou".
#
# A aproximacao usa o t critico no lugar do z, que e o refinamento usual
# e devolve os mesmos numeros das tabelas publicadas (d = 0,5 com 80% de
# poder pede 64 por grupo).

def poder(d: float, n_por_grupo: int, alfa: float = 0.05,
          pareado: bool = False) -> float:
    """Probabilidade de detectar um efeito de tamanho `d` com esse n."""
    if n_por_grupo < 2 or not d:
        return 0.0
    if pareado:
        gl = n_por_grupo - 1
        delta = abs(d) * math.sqrt(n_por_grupo)
    else:
        gl = 2 * n_por_grupo - 2
        delta = abs(d) * math.sqrt(n_por_grupo / 2.0)
    if gl < 1:
        return 0.0
    critico = t_critico(int(gl), 1 - alfa)
    normal = statistics.NormalDist()
    # a cauda do outro lado e desprezivel para delta moderado, mas entra
    # porque em efeito pequeno ela e o que sobra
    return (1.0 - normal.cdf(critico - delta)) + normal.cdf(-critico - delta)


def amostra_necessaria(d: float, poder_alvo: float = 0.80, alfa: float = 0.05,
                       pareado: bool = False, teto: int = 100000) -> dict[str, Any]:
    """Quantos por grupo para ter `poder_alvo` de detectar `d`."""
    if not d:
        return {"n": None, "aviso": "informe um tamanho de efeito diferente de zero"}
    baixo, alto = 2, teto
    if poder(d, alto, alfa, pareado) < poder_alvo:
        return {"n": None, "aviso": "nem com %d por grupo se alcança esse poder"
                                    % teto}
    while baixo < alto:
        meio = (baixo + alto) // 2
        if poder(d, meio, alfa, pareado) < poder_alvo:
            baixo = meio + 1
        else:
            alto = meio
    return {"n": baixo, "poder": round(poder(d, baixo, alfa, pareado), 3),
            "d": d, "alfa": alfa, "pareado": pareado,
            "total": baixo if pareado else baixo * 2}


def menor_efeito_detectavel(n_por_grupo: int, poder_alvo: float = 0.80,
                            alfa: float = 0.05, pareado: bool = False) -> float | None:
    """O menor efeito que este n consegue detectar com `poder_alvo`.

    E esta a pergunta honesta depois da coleta -- e nao o "poder
    observado", calculado a partir do efeito que se mediu. O poder
    observado e funcao monotona do proprio valor-p: ele nao acrescenta
    informacao nenhuma, e da a impressao de acrescentar. Um p de 0,30
    sempre devolve poder baixo, o que soa como "faltou gente" quando
    tambem pode significar "nao ha efeito".
    """
    if n_por_grupo < 2:
        return None
    baixo, alto = 0.001, 10.0
    for _ in range(200):
        meio = (baixo + alto) / 2.0
        if poder(meio, n_por_grupo, alfa, pareado) < poder_alvo:
            baixo = meio
        else:
            alto = meio
    return round((baixo + alto) / 2.0, 3)


def plano_amostral(n_por_grupo: int | None = None, alfa: float = 0.05,
                   pareado: bool = False) -> dict[str, Any]:
    """A tabela de planejamento: quanto custa cada tamanho de efeito.

    Devolve as duas leituras que um projeto precisa: quantos participantes
    cada efeito exige, e -- se ja houver gente -- o que a amostra atual
    alcanca.
    """
    tamanhos = [
        {"d": 0.2, "rotulo": "pequeno"},
        {"d": 0.5, "rotulo": "médio"},
        {"d": 0.8, "rotulo": "grande"},
        {"d": 1.2, "rotulo": "muito grande"},
    ]
    linhas = []
    for item in tamanhos:
        linha = {"d": item["d"], "rotulo": item["rotulo"]}
        for alvo in (0.80, 0.90):
            resultado = amostra_necessaria(item["d"], alvo, alfa, pareado)
            linha["n%d" % int(alvo * 100)] = resultado.get("n")
        if n_por_grupo:
            linha["poder_atual"] = round(poder(item["d"], n_por_grupo, alfa, pareado), 3)
        linhas.append(linha)
    saida: dict[str, Any] = {"linhas": linhas, "alfa": alfa, "pareado": pareado}
    if n_por_grupo:
        saida["n_atual"] = n_por_grupo
        saida["menor_detectavel_80"] = menor_efeito_detectavel(
            n_por_grupo, 0.80, alfa, pareado)
        saida["menor_detectavel_90"] = menor_efeito_detectavel(
            n_por_grupo, 0.90, alfa, pareado)
    return saida
