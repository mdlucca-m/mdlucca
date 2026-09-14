"""Sistema de treinamento contínuo — sem limite de semanas.

Os blocos da periodização são UM macrociclo, não a temporada. Aqui eles voltam
ao começo quantas vezes for preciso: semana 9 é a posição 1 do ciclo 2, semana
100 é a posição 4 do ciclo 13.

O que faz o ciclo seguinte valer mais que o anterior não é mudar o percentual —
é o 1RM ter subido. Por isso a última sessão de cada Realização é um RETESTE:
os mesmos 85% passam a significar mais quilos porque a referência mudou. Um
sistema que repete o bloco sem retestar repete também a carga, e a temporada
anda parada.
"""

from banco import mais_dias, plano_sessao, semana_de

# Três sessões de sala por semana. O resto é quadra, e a carga de quadra entra
# pela PSE do check-out — não se prescreve aqui.
DIAS = [
    {"off": 0, "hora": "09:00", "tipo": "Força", "nome": "A", "obj": "Força máxima"},
    {"off": 2, "hora": "09:00", "tipo": "Potência", "nome": "B", "obj": "Potência"},
    {"off": 4, "hora": "09:00", "tipo": "LPO", "nome": "C", "obj": "Força-velocidade"},
]

# Séries × reps do levantamento principal, por posição no macrociclo. Escrito à
# mão e não derivado de fórmula, para você poder discordar de um número sem ter
# de entender uma conta.
PRINCIPAL = {
    1: (4, "6", 150), 2: (5, "5", 180), 3: (5, "4", 180), 4: (3, "4", 150),
    5: (5, "3", 180), 6: (4, "3", 180), 7: (4, "2", 210), 8: (3, "2", 210),
}
# O levantamento olímpico anda atrás em percentual: quem trava a barra é a
# técnica, não a força.
OLIMPICO = {
    1: (4, "3", -0.14), 2: (5, "3", -0.12), 3: (5, "3", -0.10), 4: (3, "3", -0.14),
    5: (5, "2", -0.08), 6: (5, "2", -0.06), 7: (4, "2", -0.05), 8: (3, "2", -0.05),
}


def _ex(nome, grupo, series, reps, pausa, pct=None, ref=None,
        tempo=None, rir=None, vel=None, obs=""):
    return {"nome": nome, "grupo": grupo, "series": series, "reps": str(reps),
            "pausa": pausa, "pct_rm": pct, "ref1rm": ref, "tempo": tempo,
            "rir": rir, "vel": vel, "obs": obs}


def posicao_no_ciclo(semana, n_blocos):
    return (semana - 1) % n_blocos + 1


def ciclo_de(semana, n_blocos):
    return (semana - 1) // n_blocos + 1


def e_semana_reteste(semana, n_blocos):
    return posicao_no_ciclo(semana, n_blocos) == n_blocos


def _vol(b, n):
    return max(2, round(n * b["volume"]))


def _saltos(b, fatia, por_serie):
    """Contatos: o bloco define o TOTAL da semana, repartido entre os
    EXERCÍCIOS — não entre as sessões. Repartir por sessão e pôr dois
    exercícios pliométricos dentro dela estoura o alvo, porque cada um
    receberia a fatia inteira."""
    return max(2, round(b["plio"] * fatia / por_serie))


def _ombro():
    return _ex("Rotadores do ombro com elástico", "Força", 3, 15, 60, rir=3,
               obs="Antes de qualquer trabalho de ombro. No voleibol isto não é "
                   "aquecimento, é manutenção.")


def sessao_a(b, pos):
    s, r, pausa = PRINCIPAL[pos]
    os_, orr, opct = OLIMPICO[pos]
    i = b["intensidade"]
    return [
        _ombro(),
        _ex("Arranco", "LPO", os_, orr, pausa, round(i + opct, 2), "Arranco",
            obs="Primeiro exercício com barra: o mais técnico e o mais neural. "
                "Parar a série se a barra desacelerar."),
        _ex("Agachamento", "Força", s, r, pausa, i, "Agachamento",
            obs="Exercício-âncora do bloco. É por ele que se mede se a semana rendeu."),
        _ex("Supino", "Força", s, r, pausa, i, "Supino"),
        _ex("Stiff com barra", "Força", _vol(b, 4), 6, 120, round(i - 0.18, 2),
            "Stiff com barra", tempo="3-0-1-0", obs="Excêntrica de 3 s."),
        _ex("Nórdico de isquiotibiais (excêntrico)", "Força", _vol(b, 3), 6, 90,
            rir=2, obs="É a dose que reduz lesão de posterior."),
        _ex("Abdominal reto com braços esticados", "Força", _vol(b, 3), 25, 45, rir=2),
    ]


def sessao_b(b, pos, semana, n_blocos):
    os_, orr, opct = OLIMPICO[pos]
    i = b["intensidade"]
    # Em semana normal a B leva 60% dos contatos e a C os outros 40%. Na semana
    # de Realização a C vira reteste e não salta — e os contatos do bloco são
    # justamente o que mantém a reatividade antes de competir. Então a B carrega
    # a semana inteira.
    tudo = e_semana_reteste(semana, n_blocos)
    dj = _saltos(b, 0.65 if tudo else 0.40, 5)
    cx = _saltos(b, 0.35 if tudo else 0.20, 5)
    return [
        _ombro(),
        _ex("Clean", "LPO", os_, orr, 180, round(i + opct, 2), "Clean",
            obs="Velocidade da barra manda. Se cair, a série acabou — mesmo que "
                "sobre repetição."),
        _ex("Agachamento com salto sob carga (jump squat)", "Potência", 4, 4, 180,
            0.25, "Agachamento", vel="1,0",
            obs="Acima de 1,0 m/s. Carga leve: aqui se treina velocidade."),
        _ex("Drop jump 40 cm", "Pliometria", dj, 5, 120,
            obs="Contato curto com o solo. Qualidade acima da contagem."),
        _ex("Salto no caixote", "Pliometria", cx, 5, 90,
            obs="Subir saltando, DESCER andando — a descida do caixote é contato "
                "extra sem ganho."),
        _ex("Remada serrote", "Força", _vol(b, 4), 8, 90, round(i - 0.20, 2),
            "Remada serrote"),
        _ex("Dorsal perdigueiro", "Força", _vol(b, 3), 12, 45, rir=2),
    ]


def sessao_c(b, pos):
    s, r, _ = PRINCIPAL[pos]
    os_, _orr, _opct = OLIMPICO[pos]
    i = b["intensidade"]
    return [
        _ombro(),
        _ex("Snatch pull / Hang high pull", "LPO", os_, 3, 150, round(i - 0.02, 2),
            "Clean pull", obs="Puxada alta: a parte do arranco que aguenta mais carga."),
        _ex("Agachamento frontal", "Força", max(3, s - 1), r, 150, round(i - 0.10, 2),
            "Agachamento frontal", obs="Mais exigência de tronco, menos carga."),
        _ex("Saltos consecutivos sobre barreiras", "Pliometria", _saltos(b, 0.40, 6),
            6, 120, obs="Sem pausa entre as barreiras. É aqui que se treina a "
                        "rigidez do tornozelo."),
        _ex("Sprints de 10 e 20 m com mudança de direção", "Potência", 6, 1, 120,
            obs="Semana de choque: cortar se a sessão já estiver longa."
                if b["micro"] == "CHOQUE" else "Recuperação completa entre tiros."),
        _ex("Afundo frontal sem passada", "Força", _vol(b, 3), 8, 90, rir=2,
            obs="Oito de cada perna."),
        _ex("Elevação de calcanhares", "Força", _vol(b, 3), 8, 60, tempo="3-0-1-0",
            obs="Descida lenta de 3 s."),
    ]


def sessao_reteste():
    """A sexta da Realização não treina: mede. É o que reabastece o ciclo."""
    return [
        _ombro(),
        _ex("Agachamento", "Força", 1, 1, 300, ref="Agachamento",
            obs="1RM. De 3 a 5 tentativas, 3 a 5 min entre elas. Lançar em Testes."),
        _ex("Supino", "Força", 1, 1, 300, ref="Supino", obs="1RM, mesmo protocolo."),
        _ex("Clean", "LPO", 1, 1, 300, ref="Clean",
            obs="1RM técnico: a maior carga com a recepção ainda limpa, não a maior "
                "que sobe de qualquer jeito."),
        _ex("Salto no caixote", "Pliometria", 3, 1, 120,
            obs="CMJ para o registro de salto. Três tentativas, vale a melhor."),
    ]


def gerar(blocos, macro_inicio, de_semana, ate_semana, datas_ocupadas=()):
    """Sessões das semanas `de` a `ate`. Dia já prescrito é PULADO, nunca
    sobrescrito: regerar depois de ajustar um bloco não desfaz o seu ajuste."""
    n = len(blocos)
    if not n:
        return [], []
    ocupadas = set(datas_ocupadas)
    saida, pulados = [], []
    for semana in range(de_semana, ate_semana + 1):
        pos = posicao_no_ciclo(semana, n)
        b = blocos[pos - 1]
        ciclo = ciclo_de(semana, n)
        inicio = mais_dias(macro_inicio, 7 * (semana - 1))
        for dia in DIAS:
            data = mais_dias(inicio, dia["off"])
            if data in ocupadas:
                pulados.append(data)
                continue
            reteste = e_semana_reteste(semana, n) and dia["nome"] == "C"
            if reteste:
                exs = sessao_reteste()
            elif dia["nome"] == "A":
                exs = sessao_a(b, pos)
            elif dia["nome"] == "B":
                exs = sessao_b(b, pos, semana, n)
            else:
                exs = sessao_c(b, pos)
            saida.append({
                "data": data, "hora": dia["hora"],
                "tipo": "Força" if reteste else dia["tipo"],
                "objetivo": "Reteste de 1RM e salto" if reteste else dia["obj"],
                "bloco": b["bloco"],
                "notas": (f"Ciclo {ciclo} · semana {semana} ({pos}/{n}) · "
                          f"{b['micro']} · {b['enfase']}"
                          + (" · RETESTE" if reteste else f" · sessão {dia['nome']}")),
                "exercicios": exs,
            })
            ocupadas.add(data)
    return saida, pulados


def resumo(sessoes, blocos, macro_inicio):
    """O que a geração custa, semana a semana, na mesma conta que o app usa."""
    n = len(blocos)
    por = {}
    for s in sessoes:
        sem = semana_de(s["data"], macro_inicio)
        p = plano_sessao(s["exercicios"], s["tipo"], s.get("dur_prev"))
        r = por.setdefault(sem, {"semana": sem, "ua": 0, "contatos": 0,
                                 "sessoes": 0, "min": 0})
        r["ua"] += p["ua"]
        r["contatos"] += p["contatos"]
        r["min"] += p["dur"]
        r["sessoes"] += 1
    for sem, r in por.items():
        b = blocos[posicao_no_ciclo(sem, n) - 1]
        r["alvo_contatos"] = b["plio"]
        r["bloco"] = b["bloco"]
        r["micro"] = b["micro"]
        r["ciclo"] = ciclo_de(sem, n)
        r["posicao"] = posicao_no_ciclo(sem, n)
        r["reteste"] = e_semana_reteste(sem, n)
    return [por[k] for k in sorted(por)]
