"""Análise de carga, humor e prontidão.

Matemática pura, sem dependência externa. Cada função devolve `None` quando
não há base suficiente — e essa é a regra mais importante deste arquivo:
**um número inventado é pior do que número nenhum.** Um ACWR calculado sobre
dez dias de histórico parece um diagnóstico e não é; por isso ele vem marcado
com a quantidade de histórico que o sustenta, e a tela diz quando é pouco.
"""

import math
from datetime import date, timedelta

from banco import BRUMS_ITENS, SUBESCALAS, NEGATIVAS, dics


# ── Estatística de bolso ─────────────────────────────────────────────────────
def media(v):
    return sum(v) / len(v) if v else 0.0


def desvio(v):
    """Desvio padrão AMOSTRAL (n−1). Com n<2 não existe desvio: devolve 0."""
    if len(v) < 2:
        return 0.0
    m = media(v)
    return math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1))


def quartis(v):
    """Q1, mediana, Q3 e limites de Tukey. Menos de 5 pontos não é faixa."""
    x = sorted(float(i) for i in v if i is not None)
    if len(x) < 5:
        return None

    def q(p):
        i = (len(x) - 1) * p
        lo, hi = math.floor(i), math.ceil(i)
        return x[lo] if lo == hi else x[lo] + (x[hi] - x[lo]) * (i - lo)

    q1, med, q3 = q(0.25), q(0.5), q(0.75)
    iqr = q3 - q1
    return {"q1": q1, "mediana": med, "q3": q3, "iqr": iqr, "n": len(x),
            "inf": q1 - 1.5 * iqr, "sup": q3 + 1.5 * iqr}


def dentro_da_faixa(faixa, valor):
    if not faixa or valor is None:
        return None
    return faixa["inf"] <= valor <= faixa["sup"]


def postos(v):
    """Postos com empate recebendo a média — é o que o Spearman exige."""
    ordenado = sorted(range(len(v)), key=lambda i: v[i])
    r = [0.0] * len(v)
    i = 0
    while i < len(ordenado):
        j = i
        while j + 1 < len(ordenado) and v[ordenado[j + 1]] == v[ordenado[i]]:
            j += 1
        posto = (i + j) / 2 + 1
        for k in range(i, j + 1):
            r[ordenado[k]] = posto
        i = j + 1
    return r


def spearman(a, b):
    """Correlação dos postos. Menos de 6 pares não dá conclusão: devolve None.

    Spearman e não Pearson porque PSE e BRUMS são escalas ordinais, e um único
    dia extremo entorta um Pearson inteiro."""
    pares = [(x, y) for x, y in zip(a, b) if x is not None and y is not None]
    if len(pares) < 6:
        return None
    ra, rb = postos([p[0] for p in pares]), postos([p[1] for p in pares])
    ma, mb = media(ra), media(rb)
    sxy = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    sxx = sum((x - ma) ** 2 for x in ra)
    syy = sum((y - mb) ** 2 for y in rb)
    if not sxx or not syy:
        return None
    r = sxy / math.sqrt(sxx * syy)
    n = len(pares)
    t = abs(r) * math.sqrt((n - 2) / max(1e-9, 1 - r * r))
    return {"r": r, "n": n, "t": t, "forte": abs(r) >= 0.5 and t >= 2.0}


# ── Carga ────────────────────────────────────────────────────────────────────
def _dia(s):
    return date.fromisoformat(s)


def carga(con, atleta_id, hoje=None):
    """ACWR, monotonia, strain e os totais do atleta.

    ACWR = carga aguda (7 dias) ÷ crônica (média semanal de 28 dias).
    Monotonia = média ÷ desvio das cargas diárias da semana.
    Strain = monotonia × carga da semana.

    `hist_dias` vem junto porque ACWR com menos de 21 dias de histórico não
    significa nada — a tela precisa saber disso para não fingir diagnóstico.
    """
    h = (hoje or date.today()).isoformat()
    linhas = dics(con.execute(
        "SELECT data, carga_ua FROM sessoes"
        " WHERE atleta_id=? AND carga_ua>0 ORDER BY data", (atleta_id,)).fetchall())
    if not linhas:
        return {"n": 0, "total": 0, "aguda": 0, "cronica": 0, "acwr": 0,
                "monotonia": 0.0, "monotonia_indefinida": False, "strain": 0,
                "semanal": 0, "hist_dias": 0, "diarias": [0] * 7}

    def soma(ini, fim):
        return sum(x["carga_ua"] for x in linhas if ini <= x["data"] <= fim)

    ini7 = (_dia(h) - timedelta(days=6)).isoformat()
    ini28 = (_dia(h) - timedelta(days=27)).isoformat()
    aguda = soma(ini7, h)
    cronica = soma(ini28, h) / 4.0

    diarias = []
    for i in range(6, -1, -1):
        dia = (_dia(h) - timedelta(days=i)).isoformat()
        diarias.append(sum(x["carga_ua"] for x in linhas if x["data"] == dia))

    md, sd = media(diarias), desvio(diarias)
    semanal = sum(diarias)
    # Monotonia = média ÷ desvio das cargas diárias. Com desvio ZERO ela é
    # matematicamente indefinida — e devolver 0 seria a pior resposta possível:
    # 0 se lê como "ótima variação" quando é o caso MÁXIMO, carga idêntica todo
    # dia. Indefinida vira None e a tela diz o que é.
    mono = (md / sd) if sd > 0 else (None if semanal > 0 else 0.0)
    return {
        "n": len(linhas),
        "total": sum(x["carga_ua"] for x in linhas),
        "aguda": aguda, "cronica": cronica,
        "acwr": (aguda / cronica) if cronica > 0 else 0.0,
        "monotonia": mono,
        "monotonia_indefinida": mono is None,
        "strain": (mono * semanal) if mono is not None else None,
        "semanal": semanal,
        "hist_dias": (_dia(h) - _dia(linhas[0]["data"])).days + 1,
        "diarias": diarias,
    }


def zona_acwr(valor, hist_dias):
    """As faixas do velocímetro. Abaixo de 21 dias de histórico, nenhuma.

    Ressalva que fica na tela: o ACWR é apoio à decisão, não diagnóstico —
    a literatura tem crítica metodológica séria a ele (Impellizzeri, 2020)."""
    if not valor:
        return {"t": "Sem histórico", "c": ""}
    if hist_dias < 21:
        return {"t": "Histórico curto", "c": ""}
    if valor < 0.80:
        return {"t": "Subcarga", "c": "info"}
    if valor <= 1.30:
        return {"t": "Zona ideal", "c": "good"}
    if valor <= 1.50:
        return {"t": "Atenção", "c": "warn"}
    return {"t": "Risco elevado", "c": "crit"}


# ── Humor ────────────────────────────────────────────────────────────────────
def brums_por_data(con, atleta_id, momento="pre"):
    """{data: {subescala: soma, 'TMD': total}} para um atleta.

    TMD = soma das negativas − Vigor + 100. O 100 existe só para o número não
    ficar negativo; não tem significado clínico."""
    linhas = con.execute(
        "SELECT data, subescala, SUM(valor) AS s FROM brums"
        " WHERE atleta_id=? AND momento=? GROUP BY data, subescala",
        (atleta_id, momento)).fetchall()
    fora = {}
    for r in linhas:
        fora.setdefault(r["data"], {})[r["subescala"]] = r["s"]
    for data, sub in fora.items():
        for s in SUBESCALAS:
            sub.setdefault(s, 0)
        sub["TMD"] = sum(sub[s] for s in NEGATIVAS) - sub["Vigor"] + 100
    return fora


def z_movel(datas, valores, janela=30, minimo=5):
    """Z de cada ponto contra a janela ANTERIOR a ele.

    A janela não inclui o próprio ponto de propósito: comparar um valor com uma
    média que já o contém encolhe o desvio e esconde justamente o desvio que
    se quer enxergar."""
    saida = []
    for i, x in enumerate(valores):
        base = [valores[j] for j in range(i)
                if (_dia(datas[i]) - _dia(datas[j])).days <= janela]
        if len(base) < minimo:
            saida.append(None)
            continue
        s = desvio(base)
        saida.append((x - media(base)) / s if s > 0 else None)
    return saida


def z_hoje(con, atleta_id, janela=30):
    """A leitura mais recente, subescala por subescala, contra a base dele.

    Norma de grupo em humor engana: a Fadiga 10 do líbero pode ser a
    segunda-feira normal do central. A comparação é sempre dele com ele mesmo.
    """
    por_data = brums_por_data(con, atleta_id)
    datas = sorted(por_data)
    saida = []
    for sub in SUBESCALAS + ["TMD"]:
        vals = [por_data[dt][sub] for dt in datas]
        if len(vals) < 6:
            saida.append({"subescala": sub, "z": None, "n": len(vals),
                          "valor": vals[-1] if vals else None,
                          "media": None, "desvio": None, "faixa": None,
                          "ruim": 0.0})
            continue
        zs = z_movel(datas, vals, janela)
        ultimo = next((z for z in reversed(zs) if z is not None), None)
        i = len(vals) - 1
        base = [vals[j] for j in range(i)
                if (_dia(datas[i]) - _dia(datas[j])).days <= janela]
        saida.append({
            "subescala": sub, "z": ultimo, "valor": vals[i], "n": len(base),
            "media": media(base) if base else None,
            "desvio": desvio(base) if len(base) > 1 else None,
            "faixa": quartis(vals),
            # no Vigor, cair é que é ruim: o alerta é para baixo
            "ruim": (-(ultimo or 0.0)) if sub == "Vigor" else (ultimo or 0.0),
        })
    return saida


# ── Prontidão ────────────────────────────────────────────────────────────────
PESOS = {"sono": 0.20, "alerta": 0.15, "dor": 0.15,
         "humor": 0.25, "carga": 0.15}


def prontidao(con, atleta_id, hoje=None):
    """Índice 0–100 combinando sono, alerta, dor, humor e carga.

    Componente que falta é EXCLUÍDO da média, e o peso é redistribuído — não
    entra como zero. Um atleta que não respondeu a BRUMS não é um atleta com
    humor péssimo."""
    c = carga(con, atleta_id, hoje)
    w = dics(con.execute(
        "SELECT * FROM wellness WHERE atleta_id=? ORDER BY data DESC LIMIT 1",
        (atleta_id,)).fetchall())
    w = w[0] if w else {}
    zs = {x["subescala"]: x for x in z_hoje(con, atleta_id)}
    z_tmd = zs.get("TMD", {}).get("z")

    comp = {}
    if w.get("sono_qual") is not None:
        horas = min((w.get("sono_horas") or 0) / 8.0, 1.0)
        comp["sono"] = max(0.0, min(100.0, (w["sono_qual"] / 5) * 60 + horas * 40))
    if w.get("kss") is not None:
        comp["alerta"] = max(0.0, min(100.0, (9 - w["kss"]) / 8 * 100))
    if w.get("dor") is not None:
        comp["dor"] = max(0.0, min(100.0, (10 - w["dor"]) / 10 * 100))
    if z_tmd is not None:
        comp["humor"] = max(0.0, min(100.0, 50 - z_tmd * 20 + 25))
    z = zona_acwr(c["acwr"], c["hist_dias"])
    comp["carga"] = {"good": 100, "warn": 72, "crit": 45, "info": 78}.get(z["c"], 100)

    peso = sum(PESOS[k] for k in comp)
    valor = sum(comp[k] * PESOS[k] for k in comp) / peso if peso else None

    bandeiras = []
    if c["hist_dias"] >= 21 and c["acwr"] > 1.5:
        bandeiras.append(("ACWR acima de 1,50", "crit"))
    elif c["hist_dias"] >= 21 and 0 < c["acwr"] < 0.8:
        bandeiras.append(("ACWR abaixo de 0,80", "warn"))
    if c["monotonia"] is None and c["semanal"] > 0:
        bandeiras.append(("Carga idêntica todos os dias — nenhuma variação", "crit"))
    elif c["monotonia"] is not None and c["monotonia"] > 2:
        bandeiras.append(("Monotonia acima de 2,0", "warn"))
    if z_tmd is not None and z_tmd > 2:
        bandeiras.append(("Humor a mais de 2 desvios da própria base", "crit"))
    pior = max((x for x in z_hoje(con, atleta_id) if x["z"] is not None),
               key=lambda x: x["ruim"], default=None)
    if pior and pior["ruim"] >= 1.5:
        bandeiras.append((f"{pior['subescala']} atípica para ele", "warn"))
    if w.get("dor") is not None and w["dor"] >= 7:
        bandeiras.append(("Dor alta no último check-in", "warn"))

    criticas = sum(1 for _, k in bandeiras if k == "crit")
    nivel = 2 if (criticas or len(bandeiras) >= 3) else (1 if bandeiras else 0)
    return {"valor": valor, "componentes": comp, "carga": c, "zona": z,
            "bandeiras": bandeiras, "nivel": nivel, "z_tmd": z_tmd}


NIVEIS = [
    ("Liberado", "good", "Seguir a prescrição como está."),
    ("Atenção", "warn", "Manter a sessão, reduzir acessórios e reavaliar no próximo check-in."),
    ("Alerta", "crit", "Reduzir carga, cortar pliometria e conversar com o atleta hoje."),
]
