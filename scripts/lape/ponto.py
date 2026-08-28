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

from datetime import date, datetime, timedelta
from typing import Any

from .db import Database
from .util import clean_text

# Acima disto ninguem esta trabalhando: esqueceu de sair.
LIMITE_HORAS = 12

# Abaixo disto e clique errado, nao sessao de trabalho.
MINIMO_MINUTOS = 2

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
    """Acrescenta a duracao e diz se ela conta."""
    horas = duracao_horas(registro.get("entrada"), registro.get("saida"))
    registro["horas"] = round(horas, 2) if horas is not None else None
    # Fechada pelo sistema: houve trabalho, mas nao se sabe quanto.
    registro["conta"] = bool(horas is not None and not registro.get("fechado_sozinho"))
    return registro


# ----------------------------------------------------------------------
# Bater o ponto
# ----------------------------------------------------------------------
def fechar_esquecidos(db: Database, limite_horas: int = LIMITE_HORAS) -> int:
    """Fecha as sessoes que passaram do limite, marcando que foi o sistema.

    Roda antes de qualquer leitura: uma sessao de tres dias aberta na tela
    apareceria como "trabalhando ha 72 horas", e entraria em toda soma.
    """
    corte = (datetime.now() - timedelta(hours=limite_horas)).strftime(FORMATO)
    cursor = db.execute(
        "UPDATE ponto SET saida = entrada, fechado_sozinho = 1"
        " WHERE saida IS NULL AND entrada < ?", (corte,))
    if cursor.rowcount:
        db.conn.commit()
    return cursor.rowcount


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
           project_id: Any = None, article_id: Any = None) -> dict[str, Any]:
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
            "fechou_anterior": bool(anterior)}


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
        f"SELECT p.entrada, p.saida, p.fechado_sozinho FROM ponto p WHERE {onde}",
        params)
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
            f"SELECT p.entrada, p.saida, p.fechado_sozinho FROM ponto p WHERE {onde}",
            params):
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
        "       p.entrada, p.saida, p.fechado_sozinho"
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
