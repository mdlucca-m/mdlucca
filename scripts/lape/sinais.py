"""Sinais e calculo sobre a curva de producao: limite, derivada, integral,
area de crescimento, decomposicao em tendencia + estacao + ruido, e os
pontos de inflexao.

`curva.py` faz isto por ANO, para a tela de calculo do painel. Aqui a
grao e o MES, porque e nele que aparecem as coisas que o ano esconde: a
sazonalidade (a revista publica no numero de dezembro, o congresso e em
setembro), o ruido (um mes com quatro artigos entre dois meses com zero)
e a inflexao (o momento em que a producao parou de acelerar).

Toda a matematica e discreta e escrita aqui mesmo, sem numpy: sao no
maximo uns cento e poucos pontos.

O que cada numero e, e o que nao e:

  DERIVADA  -- diferenca central: (v[i+1] - v[i-1]) / 2. Nos extremos,
               diferenca simples. Unidade: publicacoes por mes por mes.
  INTEGRAL  -- area sob o ACUMULADO, pelo trapezio: "artigo-mes", quanto
               de acervo o laboratorio manteve de pe ao longo da janela.
               Sobre o fluxo mensal a area seria o proprio acumulado, e
               esse se sabe pela soma exata -- e a soma que se devolve.
  TENDENCIA -- media movel CENTRADA de doze meses (2x12, por ser par).
               Nas pontas, a janela encolhe em vez de sumir: um buraco
               de seis meses em cada ponta seria a tela dizendo "sem
               dado" onde ha dado.
  ESTACAO   -- media, por mes do calendario, do que sobra depois de tirar
               a tendencia, centrada em zero. Um valor positivo em
               dezembro diz que dezembro publica mais do que a tendencia
               explica.
  RUIDO     -- o que sobra depois da tendencia e da estacao.
  SINAL/RUIDO -- desvio-padrao da tendencia sobre o do ruido. Abaixo de 1
               a curva e mais ruido do que sinal, e a tela diz isso.
  INFLEXAO  -- onde a segunda derivada da TENDENCIA troca de sinal. Da
               serie crua ela trocaria de sinal todo mes.
  LIMITE    -- o teto de um ajuste logistico ao acumulado, por busca em
               grade. Quando o melhor ajuste bate no teto da grade, nao
               ha limite a vista, e e isso que se devolve -- inventar um
               teto para uma curva que ainda e reta seria a pior das
               leituras.
"""
from __future__ import annotations

import math
from datetime import date
from typing import Any

from .db import Database

MESES_DA_JANELA = 60
PERIODO = 12
NOMES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


# ----------------------------------------------------------------------
# a serie
# ----------------------------------------------------------------------
def _meses(ate: date, n: int) -> list[str]:
    ano, mes = ate.year, ate.month
    saida = []
    for _ in range(n):
        saida.append(f"{ano:04d}-{mes:02d}")
        mes -= 1
        if mes == 0:
            mes, ano = 12, ano - 1
    return list(reversed(saida))


def serie_mensal(db: Database, hoje: date | None = None,
                 meses: int = MESES_DA_JANELA) -> dict[str, Any]:
    """Publicados por mes, so de quem tem a data completa.

    Quem so tem o ano e contado a parte e dito: espalhar esses artigos
    por um mes qualquer daria uma curva bonita e falsa.
    """
    hoje = hoje or date.today()
    rotulos = _meses(hoje, meses)
    conta = {l["m"]: int(l["n"]) for l in db.dicts(
        "SELECT substr(published_on, 1, 7) AS m, COUNT(*) AS n FROM articles"
        " WHERE status = 'publicado' AND published_on IS NOT NULL"
        "   AND length(published_on) >= 7 AND substr(published_on, 1, 7) BETWEEN ? AND ?"
        " GROUP BY 1", (rotulos[0], rotulos[-1]))}
    antes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado' AND published_on IS NOT NULL"
        "   AND length(published_on) >= 7 AND substr(published_on, 1, 7) < ?",
        (rotulos[0],)) or 0)
    sem_mes = int(db.scalar(
        "SELECT COUNT(*) FROM articles WHERE status = 'publicado'"
        "   AND (published_on IS NULL OR length(published_on) < 7)") or 0)
    return {"labels": rotulos, "valores": [conta.get(m, 0) for m in rotulos],
            "base_antes": antes, "sem_mes": sem_mes}


# ----------------------------------------------------------------------
# calculo discreto
# ----------------------------------------------------------------------
def acumulado(valores: list[float], base: float = 0.0) -> list[float]:
    saida, total = [], float(base)
    for v in valores:
        total += v
        saida.append(total)
    return saida


def derivada(valores: list[float]) -> list[float]:
    """Diferenca central; simples nas pontas. Uma serie de um ponto nao
    tem derivada -- devolve zero, e nao um erro, porque a tela desenha
    o que houver."""
    n = len(valores)
    if n < 2:
        return [0.0] * n
    saida = []
    for i in range(n):
        if i == 0:
            saida.append(float(valores[1] - valores[0]))
        elif i == n - 1:
            saida.append(float(valores[-1] - valores[-2]))
        else:
            saida.append((valores[i + 1] - valores[i - 1]) / 2.0)
    return [round(x, 4) for x in saida]


def integral(valores: list[float]) -> dict[str, Any]:
    """Area sob a curva pelo trapezio, com a area acumulada ponto a ponto."""
    if len(valores) < 2:
        return {"area": 0.0, "acumulada": [0.0] * len(valores)}
    acumulada, area = [0.0], 0.0
    for i in range(1, len(valores)):
        area += (valores[i] + valores[i - 1]) / 2.0
        acumulada.append(round(area, 3))
    return {"area": round(area, 3), "acumulada": acumulada}


def media_movel_centrada(valores: list[float], periodo: int = PERIODO) -> list[float]:
    """2 x periodo quando o periodo e par; nas pontas a janela encolhe
    DOS DOIS LADOS por igual.

    Encolher so do lado que falta deixaria a janela torta: no primeiro
    ponto de uma reta, a media dos seis seguintes fica acima do ponto, e
    a "estacao" ganharia um degrau que nao existe. Simetrica, a media de
    uma reta e a propria reta em todo ponto -- e no extremo, com raio
    zero, e o proprio valor.
    """
    n = len(valores)
    if n == 0:
        return []
    meio = periodo // 2

    def media(de: int, ate: int) -> float:
        fatia = valores[de:ate]
        return sum(fatia) / len(fatia) if fatia else 0.0

    saida = []
    for i in range(n):
        if i < meio or i > n - 1 - meio:
            r = min(i, n - 1 - i)
            saida.append(round(media(i - r, i + r + 1), 4))
        elif periodo % 2 == 1:
            saida.append(round(media(i - meio, i + meio + 1), 4))
        else:
            # par: media das duas medias moveis deslocadas, o 2xMA classico
            saida.append(round((media(i - meio, i + meio) + media(i - meio + 1, i + meio + 1)) / 2.0, 4))
    return saida


def _desvio(valores: list[float]) -> float:
    if len(valores) < 2:
        return 0.0
    m = sum(valores) / len(valores)
    return math.sqrt(sum((v - m) ** 2 for v in valores) / (len(valores) - 1))


def decompor(valores: list[float], rotulos: list[str] | None = None,
             periodo: int = PERIODO) -> dict[str, Any]:
    """Tendencia + estacao + ruido, e quanto e sinal e quanto e ruido."""
    n = len(valores)
    tendencia = media_movel_centrada(valores, periodo)
    resto = [valores[i] - tendencia[i] for i in range(n)]
    # o mes do calendario vem do rotulo; sem rotulo, da posicao
    def mes_de(i: int) -> int:
        if rotulos and len(rotulos) == n:
            try:
                return int(rotulos[i][5:7]) - 1
            except ValueError:
                pass
        return i % periodo
    por_mes: dict[int, list[float]] = {}
    for i in range(n):
        por_mes.setdefault(mes_de(i), []).append(resto[i])
    medias = {m: sum(v) / len(v) for m, v in por_mes.items()}
    if medias:
        centro = sum(medias.values()) / len(medias)
        medias = {m: v - centro for m, v in medias.items()}
    sazonal = [round(medias.get(mes_de(i), 0.0), 4) for i in range(n)]
    ruido = [round(valores[i] - tendencia[i] - sazonal[i], 4) for i in range(n)]
    dp_sinal, dp_ruido = _desvio(tendencia), _desvio(ruido)
    razao = None if dp_ruido == 0 else round(dp_sinal / dp_ruido, 3)
    perfil = [round(medias.get(m, 0.0), 4) for m in range(periodo)]
    return {"tendencia": tendencia, "sazonal": sazonal, "ruido": ruido,
            "perfil_sazonal": perfil, "sinal_ruido": razao,
            "dp_sinal": round(dp_sinal, 4), "dp_ruido": round(dp_ruido, 4)}


def inflexoes(tendencia: list[float], rotulos: list[str] | None = None,
              minimo: float = 1e-6) -> list[dict[str, Any]]:
    """Onde a segunda derivada da tendencia troca de sinal.

    `minimo` ignora a troca entre dois valores que sao zero na pratica:
    uma tendencia reta oscila em torno de zero por erro de ponto
    flutuante, e cada oscilacao viraria uma inflexao.
    """
    seg = derivada(derivada(tendencia))
    achadas = []
    anterior = 0.0
    for i, s in enumerate(seg):
        if abs(s) < minimo:
            continue
        if anterior and (s > 0) != (anterior > 0):
            achadas.append({"i": i, "rotulo": rotulos[i] if rotulos and i < len(rotulos) else str(i),
                            "sentido": "passa a acelerar" if s > 0 else "passa a desacelerar",
                            "valor": round(tendencia[i], 3)})
        anterior = s
    return achadas


def intervalo_da_tendencia(tendencia: list[float], dp_ruido: float,
                           periodo: int = PERIODO, z: float = 1.96) -> dict[str, list[float]]:
    """A faixa de 95% em volta da media movel: +- z * dp_ruido / raiz(n da janela).

    A janela encolhe nas pontas, e a faixa alarga junto: nos extremos, com
    um ponto so, ela e o proprio desvio do ruido -- e e assim que se le
    que a ponta da tendencia e a parte menos firme da curva.
    """
    n = len(tendencia)
    meio = periodo // 2
    alto, baixo = [], []
    for i in range(n):
        if i < meio or i > n - 1 - meio:
            largura = 2 * min(i, n - 1 - i) + 1
        else:
            largura = periodo
        erro = z * dp_ruido / math.sqrt(max(1, largura))
        alto.append(round(tendencia[i] + erro, 4))
        # publicacao nao e negativa: a faixa para no chao
        baixo.append(round(max(0.0, tendencia[i] - erro), 4))
    return {"alto": alto, "baixo": baixo}


def regressao(valores: list[float], z: float = 1.96) -> dict[str, Any]:
    """A reta de minimos quadrados: a DERIVA da serie, com o intervalo de
    confianca da reta e da inclinacao.

    Deriva e o que a serie faz em media, mes apos mes, descontado o ruido:
    +0,03 publicacoes por mes por mes e uma producao que cresce devagar;
    zero e uma producao estavel. O r2 diz quanto da variacao a reta explica.
    """
    n = len(valores)
    if n < 3:
        return {"a": None, "b": None, "r2": None, "linha": [], "alto": [], "baixo": [],
                "deriva_mes": None, "deriva_ano": None, "ic_deriva": None, "erro_padrao": None}
    xs = list(range(n))
    xm = (n - 1) / 2.0
    ym = sum(valores) / n
    sxx = sum((x - xm) ** 2 for x in xs)
    sxy = sum((x - xm) * (v - ym) for x, v in zip(xs, valores))
    b = sxy / sxx if sxx else 0.0
    a = ym - b * xm
    linha = [a + b * x for x in xs]
    ss_res = sum((v - f) ** 2 for v, f in zip(valores, linha))
    ss_tot = sum((v - ym) ** 2 for v in valores)
    r2 = 1.0 - ss_res / ss_tot if ss_tot else 1.0
    s2 = ss_res / (n - 2)
    erro = math.sqrt(s2)
    alto = [round(f + z * erro * math.sqrt(1.0 / n + (x - xm) ** 2 / sxx), 4) for x, f in zip(xs, linha)]
    baixo = [round(f - z * erro * math.sqrt(1.0 / n + (x - xm) ** 2 / sxx), 4) for x, f in zip(xs, linha)]
    erro_b = math.sqrt(s2 / sxx) if sxx else 0.0
    return {"a": round(a, 4), "b": round(b, 5), "r2": round(r2, 4),
            "linha": [round(f, 4) for f in linha], "alto": alto, "baixo": baixo,
            "deriva_mes": round(b, 4), "deriva_ano": round(12 * b, 3),
            "ic_deriva": [round(b - z * erro_b, 4), round(b + z * erro_b, 4)],
            "erro_padrao": round(erro, 4)}


def limites_de_controle(valores: list[float], k: float = 2.0) -> dict[str, Any]:
    """Media e media +- k desvios: a faixa em que um mes comum cai.

    E a carta de controle: um mes fora da faixa e um mes que merece
    pergunta -- um numero especial da revista, uma tese que rendeu tres
    artigos --, e nao um mes que a tendencia explica.
    """
    if not valores:
        return {"media": None, "alto": None, "baixo": None, "fora": []}
    media = sum(valores) / len(valores)
    dp = _desvio(valores)
    alto, baixo = media + k * dp, max(0.0, media - k * dp)
    fora = [i for i, v in enumerate(valores) if v > alto or v < baixo]
    return {"media": round(media, 4), "alto": round(alto, 4), "baixo": round(baixo, 4),
            "dp": round(dp, 4), "fora": fora}


def projetar(tendencia: list[float], deriva: float | None, dp_ruido: float,
             n: int = 6, z: float = 1.96) -> dict[str, Any]:
    """Os proximos `n` meses pela deriva, a partir da ponta da tendencia,
    com a faixa que alarga com a distancia: raiz(k) vezes o desvio.

    E projecao, e a tela a desenha tracejada: o que ainda nao aconteceu
    nao se desenha com a tinta do que aconteceu.
    """
    if not tendencia or deriva is None:
        return {"valores": [], "alto": [], "baixo": []}
    base = tendencia[-1]
    valores, alto, baixo = [base], [base], [base]
    for k in range(1, n + 1):
        v = max(0.0, base + deriva * k)
        erro = z * dp_ruido * math.sqrt(k) / math.sqrt(PERIODO)
        valores.append(round(v, 4)); alto.append(round(v + erro, 4)); baixo.append(round(max(0.0, v - erro), 4))
    return {"valores": valores, "alto": alto, "baixo": baixo}


def _meses_adiante(ultimo: str, n: int) -> list[str]:
    ano, mes = int(ultimo[:4]), int(ultimo[5:7])
    saida = []
    for _ in range(n):
        mes += 1
        if mes == 13:
            mes, ano = 1, ano + 1
        saida.append(f"{ano:04d}-{mes:02d}")
    return saida


def _logistica(K: float, r: float, t0: float, t: float) -> float:
    x = -r * (t - t0)
    if x > 60:
        return 0.0
    return K / (1.0 + math.exp(x))


def limite(acum: list[float]) -> dict[str, Any]:
    """O teto de uma logistica ajustada ao acumulado, por busca em grade.

    Devolve `K` so quando o melhor ajuste nao bateu na borda da grade e
    explica mais do que uma reta. Fora disso, "sem limite a vista".
    """
    n = len(acum)
    if n < 6 or acum[-1] <= 0:
        return {"K": None, "porque": "poucos pontos para ajustar uma curva de saturação"}
    ts = list(range(n))
    topo = acum[-1]
    media = sum(acum) / n
    ss_tot = sum((v - media) ** 2 for v in acum) or 1.0
    melhor = None
    fatores = [1.02, 1.05, 1.1, 1.2, 1.35, 1.5, 1.75, 2.0, 2.5, 3.0, 4.0, 6.0, 10.0]
    for f in fatores:
        K = topo * f
        for r in (0.02, 0.04, 0.06, 0.08, 0.1, 0.13, 0.16, 0.2, 0.25, 0.3, 0.4, 0.5):
            for t0 in range(-n, 2 * n, max(1, n // 30)):
                sse = sum((_logistica(K, r, t0, t) - v) ** 2 for t, v in zip(ts, acum))
                if melhor is None or sse < melhor[0]:
                    melhor = (sse, K, r, t0, f)
    sse, K, r, t0, f = melhor
    r2 = 1.0 - sse / ss_tot
    # a reta, para comparar: se a logistica nao explica melhor do que
    # ela, o acumulado ainda esta na fase linear e nao tem teto a vista
    xm = (n - 1) / 2.0
    b = sum((t - xm) * (v - media) for t, v in zip(ts, acum)) / (sum((t - xm) ** 2 for t in ts) or 1.0)
    a = media - b * xm
    sse_reta = sum((a + b * t - v) ** 2 for t, v in zip(ts, acum))
    r2_reta = 1.0 - sse_reta / ss_tot
    na_borda = f == fatores[-1]
    if na_borda or r2 <= r2_reta + 0.01:
        return {"K": None, "r2": round(r2, 4), "r2_reta": round(r2_reta, 4),
                "porque": "o acumulado ainda cresce como uma reta: não há teto à vista"}
    ajuste = [round(_logistica(K, r, t0, t), 3) for t in ts]
    # a faixa do ajuste: o desvio dos residuos, para cada lado
    dp = math.sqrt(sse / max(1, n - 3))
    return {"K": round(K, 1), "r": r, "t0": t0, "r2": round(r2, 4), "r2_reta": round(r2_reta, 4),
            "atingido": round(100.0 * acum[-1] / K, 1), "ajuste": ajuste,
            "alto": [round(v + 1.96 * dp, 3) for v in ajuste],
            "baixo": [round(max(0.0, v - 1.96 * dp), 3) for v in ajuste],
            "porque": "ajuste logístico ao acumulado, por busca em grade; o teto é o K da curva"}


# ----------------------------------------------------------------------
# tudo junto
# ----------------------------------------------------------------------
def analisar(db: Database, hoje: date | None = None,
             meses: int = MESES_DA_JANELA) -> dict[str, Any]:
    serie = serie_mensal(db, hoje, meses)
    v = [float(x) for x in serie["valores"]]
    rot = serie["labels"]
    acum = acumulado(v, serie["base_antes"])
    d1 = derivada(v)
    d2 = derivada(d1)
    integ = integral(acum)
    dec = decompor(v, rot)
    infl = inflexoes(dec["tendencia"], rot)
    lim = limite(acum)
    tendencia_ic = intervalo_da_tendencia(dec["tendencia"], dec["dp_ruido"])
    reg = regressao(v)
    controle = limites_de_controle(v)
    d1_suave = media_movel_centrada(d1, 3)
    dp_d1 = _desvio([a - b for a, b in zip(d1, d1_suave)])
    derivada_ic = {"alto": [round(x + 1.96 * dp_d1 / math.sqrt(3), 4) for x in d1_suave],
                   "baixo": [round(x - 1.96 * dp_d1 / math.sqrt(3), 4) for x in d1_suave]}
    proj = projetar(dec["tendencia"], reg["deriva_mes"], dec["dp_ruido"])
    proj_rotulos = [rot[-1]] + _meses_adiante(rot[-1], len(proj["valores"]) - 1) if proj["valores"] else []
    ultimos = v[-PERIODO:] if len(v) >= PERIODO else v
    anteriores = v[-2 * PERIODO:-PERIODO] if len(v) >= 2 * PERIODO else []
    ritmo = sum(ultimos) / len(ultimos) if ultimos else 0.0
    ritmo_antes = sum(anteriores) / len(anteriores) if anteriores else None
    leituras = []
    if serie["sem_mes"]:
        leituras.append(f"{serie['sem_mes']} publicado(s) só têm o ano e ficam fora da curva mensal.")
    leituras.append(f"Ritmo dos últimos {len(ultimos)} meses: {ritmo:.2f} publicação(ões)/mês"
                    + (f", contra {ritmo_antes:.2f} nos {len(anteriores)} anteriores." if ritmo_antes is not None else "."))
    if dec["sinal_ruido"] is not None:
        leituras.append(("A curva é mais sinal do que ruído" if dec["sinal_ruido"] >= 1
                         else "A curva é mais ruído do que sinal")
                        + f" (razão {dec['sinal_ruido']:.2f}: desvio da tendência / desvio do ruído).")
    if infl:
        u = infl[-1]
        leituras.append(f"Última inflexão em {u['rotulo']}: a tendência {u['sentido']}.")
    else:
        leituras.append("Sem inflexão na tendência: ela não trocou de curvatura na janela.")
    if lim.get("K"):
        leituras.append(f"Limite à vista: o ajuste logístico aponta um teto de {lim['K']:.0f} artigos "
                        f"({lim['atingido']:.0f}% já atingido, R² {lim['r2']:.2f}).")
    else:
        leituras.append("Sem limite à vista: " + lim.get("porque", "") + ".")
    if reg["deriva_mes"] is not None:
        sinal = "sobe" if reg["deriva_mes"] > 0 else ("desce" if reg["deriva_mes"] < 0 else "não muda")
        leituras.append(f"Deriva: a produção {sinal} {abs(reg['deriva_ano']):.2f} publicação(ões)/mês por ano "
                        f"(IC 95% da inclinação {reg['ic_deriva'][0]:+.3f} a {reg['ic_deriva'][1]:+.3f} por mês; "
                        f"R² {reg['r2']:.2f}).")
    if controle["fora"]:
        leituras.append(f"{len(controle['fora'])} mês(es) fora dos limites de controle (média ± 2 desvios): "
                        + ", ".join(rot[i] for i in controle["fora"][-4:]) + ".")
    leituras.append(f"Área sob o acumulado: {integ['area']:.0f} artigo-mês na janela "
                    f"— quanto de acervo ficou de pé ao longo dela.")
    return {
        "labels": rot, "meses": [f"{NOMES[int(m[5:7]) - 1]}/{m[2:4]}" for m in rot],
        "valores": v, "acumulado": acum, "base_antes": serie["base_antes"], "sem_mes": serie["sem_mes"],
        "derivada": d1, "segunda_derivada": d2, "integral": integ,
        "tendencia": dec["tendencia"], "sazonal": dec["sazonal"], "ruido": dec["ruido"],
        "perfil_sazonal": dec["perfil_sazonal"], "sinal_ruido": dec["sinal_ruido"],
        "dp_sinal": dec["dp_sinal"], "dp_ruido": dec["dp_ruido"],
        "inflexoes": infl, "limite": lim,
        "tendencia_ic": tendencia_ic, "regressao": reg, "controle": controle,
        "derivada_suave": d1_suave, "derivada_ic": derivada_ic,
        "projecao": {"labels": proj_rotulos,
                     "meses": [f"{NOMES[int(m[5:7]) - 1]}/{m[2:4]}" for m in proj_rotulos],
                     "valores": proj["valores"], "alto": proj["alto"], "baixo": proj["baixo"]},
        "ritmo": round(ritmo, 3), "ritmo_antes": None if ritmo_antes is None else round(ritmo_antes, 3),
        "soma": int(sum(v)), "leituras": leituras,
    }
