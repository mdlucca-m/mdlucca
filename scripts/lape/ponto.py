"""Ponto do laboratorio: entrada, saida, e o que esta acontecendo agora.

Tres decisoes governam este modulo, e as tres existem porque um ponto mal
feito mente com cara de numero:

1. **Check-out esquecido nao vira hora trabalhada.** Entra na sexta,
   esquece de sair, e a segunda mostra setenta e duas horas. Sessao acima
   de `LIMITE_HORAS` e fechada pelo sistema e marcada; a duracao dela fica
   de fora da soma, porque nao foi medida.

2. **Hora presente nao e produtividade.** Este modulo conta HORAS
   REGISTRADAS, e diz isso no nome das coisas. O que o laboratorio produz
   esta em `articles` e `submissions`, e as duas leituras aparecem lado a
   lado -- juntar as duas num indice so esconderia qual delas mudou.

3. **Comparar periodo com periodo exige periodo fechado.** Comparar a
   semana atual (que tem tres dias) com a passada (que tem sete) sempre
   acusa queda. A comparacao e feita ate o MESMO ponto da semana.
"""
from __future__ import annotations

import random
from datetime import date, datetime, timedelta
from typing import Any

from .db import Database
from .util import clean_text

# Acima disto ninguem esta trabalhando: esqueceu de sair.
LIMITE_HORAS = 12

# Abaixo disto e clique errado, nao sessao de trabalho.
MINIMO_MINUTOS = 2

# Quanto tempo sem sinal de vida ja conta como "nao esta mais ai". A tela do
# ponto avisa que continua aberta a cada poucos minutos enquanto a pessoa
# tem a pagina aberta; passado este intervalo sem nenhum aviso, ou a pessoa
# fechou o navegador ou o sistema caiu -- e nos dois casos ela nao esta
# trabalhando desde entao.
SILENCIO_MINUTOS = 20

FORMATO = "%Y-%m-%d %H:%M:%S"


def _agora() -> str:
    """Hora local da maquina -- que e a hora do laboratorio.

    Nao e UTC de proposito: quem bate o ponto as 14h quer ver 14h, e a
    unica maquina que serve este sistema fica na sala.
    """
    return datetime.now().strftime(FORMATO)


def _ler(texto: Any) -> datetime | None:
    try:
        return datetime.strptime(str(texto)[:19], FORMATO)
    except (TypeError, ValueError):
        return None


def duracao_horas(entrada: Any, saida: Any) -> float | None:
    """Horas entre entrada e saida, ou None se nao da para dizer."""
    ini, fim = _ler(entrada), _ler(saida)
    if ini is None or fim is None or fim < ini:
        return None
    # Igual e zero, nao "nao sei": quem acabou de bater entrada esta ha
    # zero hora dentro, e a tela dizia "ha --" no primeiro minuto.
    return (fim - ini).total_seconds() / 3600


def _linha(registro: dict[str, Any]) -> dict[str, Any]:
    """Acrescenta a duracao, diz se ela conta e se foi estimada."""
    horas = duracao_horas(registro.get("entrada"), registro.get("saida"))
    registro["horas"] = round(horas, 2) if horas is not None else None

    # Fechada pelo sistema no ultimo sinal de vida: houve trabalho e sabe-se
    # aproximadamente quanto. Antes, TODA sessao fechada pelo sistema era
    # descartada -- e foi assim que uma tarde inteira de trabalho, cortada
    # por falta de luz, virou zero hora sem que nada na tela explicasse.
    # Estimada e a sessao que o sistema fechou no ultimo sinal de vida. E o
    # `visto_em` que distingue, e nao a duracao: sem sinal nenhum o unico
    # horario conhecido e o da entrada, e ai a sessao vale zero -- houve
    # trabalho, mas nao ha como dizer quanto sem inventar.
    registro["estimado"] = bool(registro.get("fechado_sozinho")
                                and registro.get("visto_em"))
    registro["conta"] = bool(horas is not None
                             and (registro["estimado"]
                                  or not registro.get("fechado_sozinho")))
    return registro


# ----------------------------------------------------------------------
# Bater o ponto
# ----------------------------------------------------------------------
def fechar_esquecidos(db: Database, limite_horas: int = LIMITE_HORAS) -> int:
    """Fecha as sessoes que passaram do limite, marcando que foi o sistema.

    Roda antes de qualquer leitura: uma sessao de tres dias aberta na tela
    apareceria como "trabalhando ha 72 horas", e entraria em toda soma.

    Fecha no ULTIMO SINAL DE VIDA, e nao na hora da entrada. Fechar na
    entrada era descartar a sessao inteira: quem entrou as 13h, trabalhou
    ate as 18h e perdeu o registro numa queda de energia recebia zero hora,
    sem nada na tela dizendo que aquelas cinco horas existiram. O ultimo
    sinal e uma estimativa, e a tela a marca como estimativa -- que e
    diferente de inventar e diferente de apagar.
    """
    corte = (datetime.now() - timedelta(hours=limite_horas)).strftime(FORMATO)
    cursor = db.execute(
        "UPDATE ponto SET saida = COALESCE(visto_em, entrada), fechado_sozinho = 1"
        " WHERE saida IS NULL AND entrada < ?", (corte,))
    if cursor.rowcount:
        db.conn.commit()
    return cursor.rowcount


def marcar_presenca(db: Database, member_id: int) -> None:
    """Anota que a pessoa ainda esta aqui.

    A tela do ponto chama isto enquanto estiver aberta. E o unico jeito de
    o sistema saber depois, olhando para tras, ate que horas alguem ficou
    quando a sessao nao foi encerrada a mao.
    """
    cursor = db.execute(
        "UPDATE ponto SET visto_em = ? WHERE member_id = ? AND saida IS NULL",
        (_agora(), int(member_id)))
    if cursor.rowcount:
        db.conn.commit()


def fechar_na_volta(db: Database, silencio_minutos: int = SILENCIO_MINUTOS) -> list[dict[str, Any]]:
    """Fecha o que ficou aberto enquanto o sistema esteve fora do ar.

    Roda na subida. Se o servico caiu -- falta de luz, maquina desligada,
    reinicio --, ninguem estava batendo ponto nesse intervalo, e esperar as
    doze horas do limite deixaria a sessao contando tempo que nao houve.

    A janela de silencio existe para o reinicio rapido: quem esta com a
    tela aberta e deu sinal de vida ha dois minutos continua trabalhando, e
    subir o sistema de novo nao pode expulsar essa pessoa do proprio turno.
    """
    corte = (datetime.now() - timedelta(minutes=silencio_minutos)).strftime(FORMATO)
    abertas = db.dicts(
        "SELECT p.id, p.member_id, p.entrada, p.visto_em, m.full_name AS quem"
        "  FROM ponto p JOIN members m ON m.id = p.member_id"
        " WHERE p.saida IS NULL AND COALESCE(p.visto_em, p.entrada) < ?", (corte,))
    if not abertas:
        return []
    db.execute(
        "UPDATE ponto SET saida = COALESCE(visto_em, entrada), fechado_sozinho = 1"
        " WHERE saida IS NULL AND COALESCE(visto_em, entrada) < ?", (corte,))
    db.conn.commit()
    fechadas = []
    for linha in abertas:
        horas = duracao_horas(linha["entrada"], linha["visto_em"] or linha["entrada"])
        fechadas.append({"quem": linha["quem"], "entrada": linha["entrada"],
                         "saida": linha["visto_em"] or linha["entrada"],
                         "horas": round(horas or 0, 2),
                         "sem_sinal": not linha["visto_em"]})
    return fechadas


# ----------------------------------------------------------------------
# Reinicio rapido vs queda de verdade
# ----------------------------------------------------------------------
# O sinal de vida de cada pessoa (visto_em, acima) so bate com a aba do
# ponto em PRIMEIRO PLANO -- de proposito, para uma janela minimizada a
# noite inteira nao contar como trabalho. Consequencia: o visto_em de
# quem so nao esta OLHANDO para a aba agora mesmo -- a maior parte do
# expediente, para a maior parte das pessoas -- fica "velho" o tempo
# todo. Sem esta distincao aqui, `fechar_na_volta()` fechava o ponto de
# quem estivesse com a aba aberta mas sem foco a cada atualizacao
# publicada (uma troca de poucos segundos), tratando isso como se o
# laboratorio inteiro tivesse ficado fora do ar.
REINICIO_RAPIDO_MINUTOS = 3


def marcar_servidor_vivo(db: Database) -> None:
    """Registra que o servidor respondeu agora.

    Chamado na subida e de tempos em tempos enquanto o servico roda, para
    o PROXIMO reinicio conseguir perguntar "a ultima vez que alguem
    respondeu foi ha pouco, ou faz tempo?" -- e so essa pergunta, feita
    ANTES de olhar o visto_em de cada pessoa, distingue as duas causas.
    """
    db.execute(
        "INSERT INTO estado_sistema (chave, valor) VALUES ('servidor_visto_em', ?)"
        " ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor", (_agora(),))
    db.conn.commit()


def reinicio_foi_rapido(db: Database, limite_minutos: int = REINICIO_RAPIDO_MINUTOS) -> bool:
    """True quando o servidor respondeu ha pouco -- sinal de que esta
    subida e so a troca de uma atualizacao publicada, nao uma queda de
    verdade (falta de luz, maquina desligada, travamento).

    Banco novo (nunca rodou) devolve False: nao ha reinicio nenhum para
    ser "rapido" na primeira subida, e nada esta aberto para fechar.
    """
    visto = _ler(db.scalar(
        "SELECT valor FROM estado_sistema WHERE chave = 'servidor_visto_em'"))
    if visto is None:
        return False
    return (datetime.now() - visto) < timedelta(minutes=limite_minutos)


def aberto(db: Database, member_id: int) -> dict[str, Any] | None:
    """A sessao em aberto desta pessoa, se houver."""
    fechar_esquecidos(db)
    linhas = db.dicts(
        "SELECT p.*, pr.name AS projeto, a.title AS artigo"
        "  FROM ponto p"
        "  LEFT JOIN projects pr ON pr.id = p.project_id"
        "  LEFT JOIN articles a ON a.id = p.article_id"
        " WHERE p.member_id = ? AND p.saida IS NULL"
        " ORDER BY p.entrada DESC LIMIT 1", (member_id,))
    if not linhas:
        return None
    linha = linhas[0]
    linha["ha_horas"] = duracao_horas(linha["entrada"], _agora())
    return linha


def entrar(db: Database, member_id: int, atividade: Any = None,
           project_id: Any = None, article_id: Any = None,
           nome: Any = None) -> dict[str, Any]:
    """Marca a entrada. Bater duas vezes fecha a anterior, nao duplica."""
    anterior = aberto(db, member_id)
    if anterior:
        sair(db, member_id, observacao="fechada ao bater entrada de novo")
    ponto_id = db.execute(
        "INSERT INTO ponto (member_id, entrada, atividade, project_id, article_id)"
        " VALUES (?, ?, ?, ?, ?)",
        (member_id, _agora(), clean_text(atividade), project_id, article_id)).lastrowid
    db.conn.commit()
    return {"id": ponto_id, "entrada": _agora(),
            "fechou_anterior": bool(anterior),
            "saudacao": saudacao_entrada(nome)}


# Uma frase por bater-entrada, sorteada dentro da faixa da hora -- para nao
# virar um carimbo sempre igual pra quem bate ponto todo santo dia. O
# vocativo (primeiro nome) so entra quando ha nome pra chamar.
_SAUDACOES_MANHA = [
    "Bom dia{v}! Que seu dia de estudos e trabalho seja produtivo.",
    "Bom dia{v}! Começando bem -- bom trabalho hoje.",
    "Bom dia{v}! Foco e uma boa produção pela frente.",
]
_SAUDACOES_TARDE = [
    "Boa tarde{v}! Siga com foco no que falta do dia -- bom trabalho.",
    "Boa tarde{v}! Bom trabalho no restante da tarde.",
    "Boa tarde{v}! Mais um turno produtivo pela frente.",
]
_SAUDACOES_NOITE = [
    "Boa noite{v}! Obrigado pelo empenho -- bom trabalho.",
    "Boa noite{v}! Seu esforço faz diferença no laboratório.",
    "Boa noite{v}! Bom trabalho, e não esqueça de descansar.",
]


def saudacao_entrada(nome: Any = None, agora: datetime | None = None) -> str:
    """Mensagem de boas-vindas ao bater entrada -- varia com a hora do dia
    e, quando ha nome, chama a pessoa pelo primeiro nome."""
    hora = (agora or datetime.now()).hour
    opcoes = _SAUDACOES_MANHA if hora < 12 else _SAUDACOES_TARDE if hora < 18 else _SAUDACOES_NOITE
    primeiro = str(nome or "").strip().split()[0] if str(nome or "").strip() else ""
    return random.choice(opcoes).format(v=(f", {primeiro}" if primeiro else ""))


def sair(db: Database, member_id: int, observacao: Any = None) -> dict[str, Any]:
    """Marca a saida da sessao aberta. Sem sessao aberta, nao inventa uma."""
    linhas = db.dicts(
        "SELECT id, entrada FROM ponto WHERE member_id = ? AND saida IS NULL"
        " ORDER BY entrada DESC LIMIT 1", (member_id,))
    if not linhas:
        return {"fechou": False, "porque": "não havia entrada em aberto"}
    linha = linhas[0]
    agora = _agora()
    horas = duracao_horas(linha["entrada"], agora) or 0
    if horas * 60 < MINIMO_MINUTOS:
        # Clique errado: apagar e mais honesto que gravar zero minuto de
        # trabalho, que depois entra na media e a puxa para baixo.
        db.execute("DELETE FROM ponto WHERE id = ?", (linha["id"],))
        db.conn.commit()
        return {"fechou": False, "porque": "entrada de menos de "
                f"{MINIMO_MINUTOS} minutos foi descartada"}
    db.execute("UPDATE ponto SET saida = ?, observacao = COALESCE(?, observacao)"
               " WHERE id = ?", (agora, clean_text(observacao), linha["id"]))
    db.conn.commit()
    return {"fechou": True, "horas": round(horas, 2), "saida": agora}


def pendentes_sem_sinal(db: Database, member_id: int) -> list[dict[str, Any]]:
    """Sessoes desta pessoa fechadas pelo sistema SEM nenhum sinal de vida --
    as unicas que de verdade valem zero hora, porque nao ha como estimar
    quanto tempo houve trabalho (ver `_linha`, campo `estimado`). Sao a
    lista que a tela mostra como "voce esqueceu de bater saida aqui" --
    quem esteve lá é quem sabe até que horas ficou, não o sistema.
    """
    linhas = db.dicts(
        "SELECT id, entrada FROM ponto"
        " WHERE member_id = ? AND fechado_sozinho = 1 AND visto_em IS NULL"
        " ORDER BY entrada DESC", (member_id,))
    return linhas


def informar_saida(db: Database, member_id: int, ponto_id: int,
                   saida_informada: Any) -> dict[str, Any]:
    """A propria pessoa diz até que horas ficou numa sessão sem sinal nenhum.

    Diferente de `fechar_na_volta` (que estima pelo ÚLTIMO SINAL, dado do
    sistema) e diferente de inventar (que este módulo recusa a fazer
    sozinho): aqui quem preenche a lacuna é quem estava lá. Por isso só
    vale para sessão SEM visto_em -- uma que já tem estimativa do sistema
    não é reaberta para a pessoa escrever por cima.
    """
    linhas = db.dicts(
        "SELECT id, entrada, member_id, visto_em FROM ponto WHERE id = ?", (ponto_id,))
    if not linhas or linhas[0]["member_id"] != member_id:
        return {"informou": False, "porque": "sessão não encontrada"}
    linha = linhas[0]
    if linha["visto_em"] is not None:
        return {"informou": False,
                "porque": "esta sessão já tem uma estimativa do sistema"}
    saida_txt = str(saida_informada)[:19]
    horas = duracao_horas(linha["entrada"], saida_txt)
    if horas is None:
        return {"informou": False, "porque": "horário inválido"}
    if _ler(saida_txt) > datetime.now():
        return {"informou": False, "porque": "esse horário ainda não aconteceu"}
    if horas > LIMITE_HORAS:
        return {"informou": False,
                "porque": f"mais de {LIMITE_HORAS}h numa sessão só -- confira o horário"}
    nota = f"saída informada pela própria pessoa em {_agora()} (sessão sem sinal de vida)"
    db.execute(
        "UPDATE ponto SET saida = ?, visto_em = ?,"
        " observacao = TRIM(COALESCE(observacao || ' -- ', '') || ?) WHERE id = ?",
        (saida_txt, saida_txt, nota, ponto_id))
    db.conn.commit()
    return {"informou": True, "horas": round(horas, 2), "saida": saida_txt}


def anotar(db: Database, member_id: int, atividade: Any) -> dict[str, Any]:
    """Troca o que a pessoa esta fazendo, sem fechar a sessao."""
    linhas = db.dicts(
        "SELECT id FROM ponto WHERE member_id = ? AND saida IS NULL"
        " ORDER BY entrada DESC LIMIT 1", (member_id,))
    if not linhas:
        return {"anotou": False, "porque": "não havia entrada em aberto"}
    db.execute("UPDATE ponto SET atividade = ? WHERE id = ?",
               (clean_text(atividade), linhas[0]["id"]))
    db.conn.commit()
    return {"anotou": True}


# ----------------------------------------------------------------------
# O que esta acontecendo agora
# ----------------------------------------------------------------------
def agora(db: Database) -> list[dict[str, Any]]:
    """Quem esta no laboratorio neste instante, e fazendo o que."""
    fechar_esquecidos(db)
    linhas = db.dicts(
        "SELECT p.id, p.member_id, p.entrada, p.atividade,"
        "       m.full_name AS quem, m.role AS vinculo,"
        "       pr.name AS projeto, a.title AS artigo"
        "  FROM ponto p JOIN members m ON m.id = p.member_id"
        "  LEFT JOIN projects pr ON pr.id = p.project_id"
        "  LEFT JOIN articles a ON a.id = p.article_id"
        " WHERE p.saida IS NULL ORDER BY p.entrada")
    agora_txt = _agora()
    for linha in linhas:
        linha["ha_horas"] = duracao_horas(linha["entrada"], agora_txt)
    return linhas


# ----------------------------------------------------------------------
# Quanto tempo, e comparado com quando
# ----------------------------------------------------------------------
def _somar(db: Database, member_id: int | None, de: str, ate: str) -> dict[str, Any]:
    """Horas e sessoes num intervalo [de, ate)."""
    onde = "p.entrada >= ? AND p.entrada < ?"
    params: list[Any] = [de, ate]
    if member_id is not None:
        onde += " AND p.member_id = ?"
        params.append(member_id)
    linhas = db.dicts(
        f"SELECT p.entrada, p.saida, p.fechado_sozinho, p.visto_em"
        f"  FROM ponto p WHERE {onde}", params)
    horas, sessoes, esquecidas = 0.0, 0, 0
    for linha in linhas:
        pronta = _linha(dict(linha))
        if pronta["conta"]:
            horas += pronta["horas"] or 0
            sessoes += 1
        elif linha["fechado_sozinho"]:
            esquecidas += 1
    return {"horas": round(horas, 2), "sessoes": sessoes,
            "esquecidas": esquecidas}


def _janelas(hoje: date) -> dict[str, tuple[date, date, date, date]]:
    """Inicio e fim de cada periodo, e do periodo anterior comparavel.

    O anterior vai so ate o MESMO ponto do periodo: comparar uma semana de
    tres dias com uma de sete acusa queda toda segunda-feira, e a queda
    seria do calendario, nao do trabalho.
    """
    amanha = hoje + timedelta(days=1)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    inicio_mes = hoje.replace(day=1)
    mes_passado_fim = inicio_mes
    mes_passado_ini = (inicio_mes - timedelta(days=1)).replace(day=1)
    # mesmo dia do mes, para o mes anterior nao ser comparado inteiro
    dia = hoje.day
    try:
        mes_passado_ate = mes_passado_ini.replace(day=dia) + timedelta(days=1)
    except ValueError:                      # o mes anterior e mais curto
        mes_passado_ate = mes_passado_fim
    return {
        "dia": (hoje, amanha, hoje - timedelta(days=1), hoje),
        "semana": (inicio_semana, amanha,
                   inicio_semana - timedelta(days=7),
                   amanha - timedelta(days=7)),
        "mes": (inicio_mes, amanha, mes_passado_ini,
                min(mes_passado_ate, mes_passado_fim)),
    }


def _dia_txt(d: date) -> str:
    return d.strftime("%Y-%m-%d 00:00:00")


def resumo(db: Database, member_id: int | None = None,
           hoje: date | None = None) -> dict[str, Any]:
    """Horas do dia, da semana e do mes, cada uma contra a anterior."""
    fechar_esquecidos(db)
    hoje = hoje or date.today()
    saida: dict[str, Any] = {}
    for nome, (de, ate, de0, ate0) in _janelas(hoje).items():
        atual = _somar(db, member_id, _dia_txt(de), _dia_txt(ate))
        antes = _somar(db, member_id, _dia_txt(de0), _dia_txt(ate0))
        variacao = None
        if antes["horas"] > 0:
            variacao = round((atual["horas"] - antes["horas"]) / antes["horas"] * 100, 1)
        elif atual["horas"] > 0:
            variacao = None          # sem base, "aumento infinito" nao diz nada
        saida[nome] = dict(atual, antes=antes["horas"], variacao=variacao,
                           de=_dia_txt(de)[:10], ate=_dia_txt(ate)[:10])
    saida["aberto"] = aberto(db, member_id) if member_id is not None else None
    return saida


def serie(db: Database, member_id: int | None = None, dias: int = 30,
          hoje: date | None = None) -> list[dict[str, Any]]:
    """Horas por dia, do mais antigo ao mais novo, sem buracos.

    Dia sem registro entra com zero: uma serie que pula os dias vazios
    desenha uma linha continua de trabalho que nunca houve.
    """
    fechar_esquecidos(db)
    hoje = hoje or date.today()
    inicio = hoje - timedelta(days=dias - 1)
    onde = "p.entrada >= ?"
    params: list[Any] = [_dia_txt(inicio)]
    if member_id is not None:
        onde += " AND p.member_id = ?"
        params.append(member_id)
    por_dia: dict[str, float] = {}
    for linha in db.dicts(
            f"SELECT p.entrada, p.saida, p.fechado_sozinho, p.visto_em"
            f"  FROM ponto p WHERE {onde}", params):
        pronta = _linha(dict(linha))
        if not pronta["conta"]:
            continue
        chave = str(linha["entrada"])[:10]
        por_dia[chave] = por_dia.get(chave, 0) + (pronta["horas"] or 0)
    return [{"dia": (inicio + timedelta(days=i)).isoformat(),
             "horas": round(por_dia.get((inicio + timedelta(days=i)).isoformat(), 0), 2)}
            for i in range(dias)]


def historico(db: Database, member_id: int, limite: int = 40) -> list[dict[str, Any]]:
    """As ultimas sessoes desta pessoa, para ela conferir e corrigir."""
    fechar_esquecidos(db)
    linhas = db.dicts(
        "SELECT p.*, pr.name AS projeto, a.title AS artigo"
        "  FROM ponto p"
        "  LEFT JOIN projects pr ON pr.id = p.project_id"
        "  LEFT JOIN articles a ON a.id = p.article_id"
        " WHERE p.member_id = ? ORDER BY p.entrada DESC LIMIT ?",
        (member_id, limite))
    return [_linha(dict(linha)) for linha in linhas]


def por_pessoa(db: Database, dias: int = 30,
               hoje: date | None = None) -> list[dict[str, Any]]:
    """Horas de cada integrante no periodo -- a visao da coordenacao."""
    fechar_esquecidos(db)
    hoje = hoje or date.today()
    inicio = _dia_txt(hoje - timedelta(days=dias - 1))
    linhas = db.dicts(
        "SELECT p.member_id, m.full_name AS quem, m.role AS vinculo,"
        "       p.entrada, p.saida, p.fechado_sozinho, p.visto_em"
        "  FROM ponto p JOIN members m ON m.id = p.member_id"
        " WHERE p.entrada >= ?", (inicio,))
    por_id: dict[int, dict[str, Any]] = {}
    for linha in linhas:
        item = por_id.setdefault(linha["member_id"], {
            "member_id": linha["member_id"], "quem": linha["quem"],
            "vinculo": linha["vinculo"], "horas": 0.0, "sessoes": 0,
            "esquecidas": 0, "dias": set()})
        pronta = _linha(dict(linha))
        if pronta["conta"]:
            item["horas"] += pronta["horas"] or 0
            item["sessoes"] += 1
            item["dias"].add(str(linha["entrada"])[:10])
        elif linha["fechado_sozinho"]:
            item["esquecidas"] += 1
    saida = []
    for item in por_id.values():
        item["dias_com_registro"] = len(item.pop("dias"))
        item["horas"] = round(item["horas"], 2)
        item["media_por_dia"] = (round(item["horas"] / item["dias_com_registro"], 2)
                                 if item["dias_com_registro"] else 0)
        saida.append(item)
    saida.sort(key=lambda x: -x["horas"])
    return saida


# ----------------------------------------------------------------------
# Meta semanal obrigatoria e banco de horas -- quem tem bolsa
# ----------------------------------------------------------------------
# Bolsista de IC ou de extensao cumpre a carga sempre; mestrando e
# doutorando so tem essa obrigacao quando, ALEM do vinculo, tem bolsa
# registrada (mesmo sinal que a coordenacao ja usa para achar quem
# recebe bolsa -- ver vinculo.py). Professor, tecnico, voluntario,
# graduando e colaborador nao tem carga fixa nenhuma aqui.
HORAS_SEMANAIS_BOLSA = 20.0
_CARGOS_BOLSA_SEMPRE = ("bolsista_ic", "bolsista_extensao")
_CARGOS_BOLSA_SE_TEM_BOLSA = ("mestrando", "doutorando")


def meta_semanal_horas(db: Database, member_id: int) -> float | None:
    """Quantas horas por semana esta pessoa e obrigada a cumprir, ou None
    se o cargo dela nao exige carga fixa (ou exige so com bolsa, e ela
    nao tem uma registrada)."""
    linhas = db.dicts("SELECT role, scholarship FROM members WHERE id = ?", (member_id,))
    if not linhas:
        return None
    role = linhas[0].get("role")
    tem_bolsa = bool((linhas[0].get("scholarship") or "").strip())
    if role in _CARGOS_BOLSA_SEMPRE:
        return HORAS_SEMANAIS_BOLSA
    if role in _CARGOS_BOLSA_SE_TEM_BOLSA and tem_bolsa:
        return HORAS_SEMANAIS_BOLSA
    return None


def banco_de_horas(db: Database, member_id: int, meta_semanal: float,
                   semanas: int = 12, hoje: date | None = None) -> dict[str, Any]:
    """Semana a semana (segunda a domingo) contra a meta obrigatoria, com
    saldo acumulado -- e a semana EM ANDAMENTO à parte, porque uma semana
    que ainda não fechou não pode virar déficit definitivo no banco: ainda
    dá tempo de cumprir o que falta.

    Nunca volta antes do PRIMEIRO ponto que esta pessoa já bateu. Achado
    ao vivo: com a janela fixa de `semanas`, um bolsista recém-cadastrado
    via cada semana anterior ao próprio primeiro registro contar como
    déficit total (ninguém bateu ponto porque a obrigação nem existia
    ainda) -- um saldo de "-200h" no primeiro dia. Mesma ideia de "não
    inventar hora" do resto do módulo, aplicada ao outro lado da conta:
    sem nenhum dado, não é déficit, é ausência de dado.
    """
    fechar_esquecidos(db)
    hoje = hoje or date.today()
    inicio_atual = hoje - timedelta(days=hoje.weekday())
    primeiro = _ler(db.scalar(
        "SELECT MIN(entrada) FROM ponto WHERE member_id = ?", (member_id,)))
    primeira_semana = (primeiro.date() - timedelta(days=primeiro.date().weekday())
                       if primeiro else inicio_atual)

    semanas_fechadas: list[dict[str, Any]] = []
    saldo = 0.0
    for i in range(semanas, 0, -1):
        fim = inicio_atual - timedelta(days=7 * (i - 1))
        ini = fim - timedelta(days=7)
        if ini < primeira_semana:
            continue
        horas = _somar(db, member_id, _dia_txt(ini), _dia_txt(fim))["horas"]
        delta = round(horas - meta_semanal, 2)
        saldo = round(saldo + delta, 2)
        semanas_fechadas.append({
            "inicio": ini.isoformat(), "fim": (fim - timedelta(days=1)).isoformat(),
            "horas": horas, "delta": delta, "saldo_acumulado": saldo,
        })
    atual = _somar(db, member_id, _dia_txt(inicio_atual), _dia_txt(hoje + timedelta(days=1)))
    return {
        "meta_semanal": meta_semanal,
        "semanas": semanas_fechadas,
        "saldo_acumulado": saldo,
        "semana_atual": {
            "inicio": inicio_atual.isoformat(),
            "horas": atual["horas"],
            "faltam": round(max(0.0, meta_semanal - atual["horas"]), 2),
            "excedente": round(max(0.0, atual["horas"] - meta_semanal), 2),
        },
    }


def producao_no_periodo(db: Database, member_id: int | None = None,
                        dias: int = 30, hoje: date | None = None) -> dict[str, int]:
    """O que saiu de trabalho no mesmo periodo -- para nao ler hora sozinha.

    Hora presente nao e produtividade. Estas contagens ficam ao lado das
    horas justamente para que a diferenca entre as duas apareca.
    """
    hoje = hoje or date.today()
    corte = (hoje - timedelta(days=dias - 1)).isoformat()
    filtro, params = "", [corte]
    if member_id is not None:
        filtro = (" AND EXISTS (SELECT 1 FROM article_authors aa"
                  " WHERE aa.article_id = a.id AND aa.member_id = ?)")
        params.append(member_id)
    def conta(campo: str) -> int:
        return int(db.scalar(
            f"SELECT COUNT(*) FROM articles a WHERE a.{campo} >= ?{filtro}",
            params) or 0)
    return {
        "publicados": conta("published_on"),
        "aceitos": conta("accepted_on"),
        "submetidos": conta("first_submission_on"),
        "iniciados": conta("started_on"),
        "dias": dias,
    }
