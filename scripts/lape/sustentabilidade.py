"""O laboratorio se sustenta? -- as pessoas, os prazos e o que esta em curso.

O `fomento.py` ja responde pelo dinheiro: editais que fecham, taxa de
aprovacao, vigencia de projeto, captado por ano. Falta o outro lado, e e o
que de fato limita um laboratorio academico: GENTE COM PRAZO. Bolsa
termina, tese e defendida, e a pessoa vai embora -- levando consigo o
manuscrito que estava escrevendo.

A pergunta que este modulo responde nao e "quantos vao sair" -- essa a
lista de integrantes ja responde. E:

    quantos manuscritos em curso ficam SEM NINGUEM quando os prazos
    chegarem?

Um manuscrito em que todos os autores do laboratorio estao saindo nao tem
quem o termine. Um em que alguem fica tem. A diferenca entre os dois e a
unica coisa nesta tela que muda uma decisao -- e nenhuma media de
"producao por pesquisador" a mostra, porque media trata pessoas como
intercambiaveis, e o autor de um manuscrito nao e substituivel por outro.

DUAS REGRAS DE HONESTIDADE, porque esta tela fala do futuro:

  1. quem nao tem prazo declarado NAO conta como quem fica. Fica numa
     lista propria, "sem prazo declarado". A alternativa -- tratar a
     ausencia de data como permanencia -- faria a tela afirmar que o
     laboratorio esta seguro justamente onde ele nao sabe;
  2. nada aqui e projecao. Sao as datas que a coordenacao declarou, lidas
     contra hoje. Onde nao ha data declarada, a tela diz que nao ha.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .db import Database

# Uma janela de um ano: e o horizonte em que uma coordenacao consegue agir
# -- abrir edital, pedir bolsa, redistribuir manuscrito. Em seis meses ja
# nao da para pedir bolsa nova; em tres anos qualquer numero e ficcao.
MESES_DA_JANELA = 12

# O que faz alguem sair, e o nome de cada motivo na tela.
MOTIVOS = {
    "scholarship_until": "fim da bolsa",
    "thesis_due_on": "prazo da tese",
}

# Situacoes de artigo que contam como EM CURSO. Publicado e rejeitado nao
# entram: um nao precisa de ninguem, o outro nao tem para onde ir.
EM_CURSO = ("em_producao", "submetido", "em_revisao", "aceito")


def _hoje() -> date:
    return date.today()


def _data(valor: Any) -> date | None:
    texto = str(valor or "")[:10]
    if len(texto) != 10:
        return None
    try:
        return date.fromisoformat(texto)
    except ValueError:
        return None


def saidas_previstas(db: Database, meses: int = MESES_DA_JANELA,
                     hoje: date | None = None) -> dict[str, Any]:
    """Quem tem prazo para sair, e por que -- dentro e fora da janela.

    Quando as duas datas existem, vale a PRIMEIRA: e ela que tira a pessoa
    do laboratorio. Somar as duas, ou usar a ultima, diria que a pessoa
    fica mais tempo do que fica.
    """
    hoje = hoje or _hoje()
    limite = hoje + timedelta(days=int(meses * 30.44))
    pessoas = db.dicts(
        "SELECT id, full_name, short_name, role, scholarship,"
        "       scholarship_until, thesis_due_on, thesis_status"
        "  FROM members"
        " WHERE COALESCE(is_external, 0) = 0 AND COALESCE(active, 1) <> 0"
        "   AND left_on IS NULL"
        " ORDER BY full_name")

    saem: list[dict[str, Any]] = []
    depois: list[dict[str, Any]] = []
    sem_prazo: list[dict[str, Any]] = []
    for p in pessoas:
        prazos = [(_data(p[campo]), campo) for campo in MOTIVOS
                  if _data(p[campo]) is not None]
        if not prazos:
            sem_prazo.append({"id": p["id"], "quem": p["full_name"],
                              "vinculo": p["role"]})
            continue
        quando, campo = min(prazos)
        ficha = {
            "id": p["id"], "quem": p["full_name"], "vinculo": p["role"],
            "quando": quando.isoformat(), "motivo": MOTIVOS[campo],
            "dias": (quando - hoje).days,
            "ja_passou": quando < hoje,
            "bolsa": p["scholarship"],
            "etapa_da_tese": p["thesis_status"],
        }
        (saem if quando <= limite else depois).append(ficha)
    saem.sort(key=lambda x: x["quando"])
    depois.sort(key=lambda x: x["quando"])
    return {"janela_meses": meses, "hoje": hoje.isoformat(),
            "limite": limite.isoformat(),
            "saem": saem, "depois": depois, "sem_prazo": sem_prazo,
            "n_ativos": len(pessoas)}


def trabalho_em_risco(db: Database, meses: int = MESES_DA_JANELA,
                      hoje: date | None = None) -> dict[str, Any]:
    """Os manuscritos em curso, separados por quem sobra para termina-los.

    Tres caixas, e a do meio e a que interessa:

      * `orfaos`  -- TODOS os autores do laboratorio saem na janela. Nao
                     ha quem termine, e isto e uma decisao a tomar agora;
      * `parciais` -- alguem sai e alguem fica. O manuscrito perde tempo,
                     nao perde dono;
      * `firmes`  -- ninguem sai na janela.

    Coautor externo nao conta como quem fica: ele nao responde pelo
    manuscrito no laboratorio, e contar com ele transformaria um orfao em
    "parcial" sem que ninguem tenha assumido nada.
    """
    hoje = hoje or _hoje()
    saidas = saidas_previstas(db, meses=meses, hoje=hoje)
    quem_sai = {x["id"]: x for x in saidas["saem"]}

    marcas = ",".join("?" * len(EM_CURSO))
    artigos = db.dicts(
        f"SELECT id, internal_code, title, status, lead_name, started_on"
        f"  FROM articles WHERE status IN ({marcas})"
        f" ORDER BY started_on IS NULL, started_on", EM_CURSO)

    orfaos: list[dict[str, Any]] = []
    parciais: list[dict[str, Any]] = []
    firmes: list[dict[str, Any]] = []
    sem_autoria = 0
    for artigo in artigos:
        autores = db.dicts(
            "SELECT aa.member_id, aa.author_name, aa.author_order,"
            "       COALESCE(m.is_external, 1) AS externo"
            "  FROM article_authors aa"
            "  LEFT JOIN members m ON m.id = aa.member_id"
            " WHERE aa.article_id = ? ORDER BY aa.author_order", (artigo["id"],))
        # So quem e do laboratorio responde pelo manuscrito aqui dentro.
        internos = [a for a in autores
                    if a["member_id"] is not None and not a["externo"]]
        saindo = [a for a in internos if a["member_id"] in quem_sai]
        ficha = {
            "id": artigo["id"], "code": artigo["internal_code"],
            "titulo": artigo["title"], "status": artigo["status"],
            "n_internos": len(internos),
            "saindo": [{"quem": a["author_name"],
                        "quando": quem_sai[a["member_id"]]["quando"],
                        "motivo": quem_sai[a["member_id"]]["motivo"]}
                       for a in saindo],
            "ficam": [a["author_name"] for a in internos
                      if a["member_id"] not in quem_sai],
        }
        if not internos:
            # Sem nenhum autor do laboratorio identificado, nao ha o que
            # afirmar: em `firmes` seria dizer que esta seguro, em
            # `orfaos` seria dizer que esta perdido. Fica de fora, e a
            # contagem de fora aparece na tela -- um numero alto aqui
            # significa autoria nao cadastrada, e nao risco.
            sem_autoria += 1
            continue
        if saindo and not ficha["ficam"]:
            orfaos.append(ficha)
        elif saindo:
            parciais.append(ficha)
        else:
            firmes.append(ficha)

    return {"janela_meses": meses, "em_curso": len(artigos),
            "orfaos": orfaos, "parciais": parciais, "firmes": firmes,
            "sem_autoria_interna": sem_autoria}


def renovacao(db: Database, janela: int = 5,
              hoje: date | None = None) -> list[dict[str, Any]]:
    """Quantos entraram e quantos sairam, por ano.

    Um laboratorio que forma gente perde gente por construcao -- a saida
    de um mestrando que defendeu e um sucesso, e nao uma perda. O que a
    serie mostra e se a reposicao acompanha: dois anos seguidos com mais
    saidas do que entradas e um laboratorio encolhendo, e a contagem de
    hoje nao diz isso.
    """
    hoje = hoje or _hoje()
    anos = list(range(hoje.year - janela + 1, hoje.year + 1))
    saida: list[dict[str, Any]] = []
    for ano in anos:
        entraram = int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE COALESCE(is_external, 0) = 0"
            "   AND substr(joined_on, 1, 4) = ?", (str(ano),)) or 0)
        sairam = int(db.scalar(
            "SELECT COUNT(*) FROM members WHERE COALESCE(is_external, 0) = 0"
            "   AND substr(left_on, 1, 4) = ?", (str(ano),)) or 0)
        saida.append({"ano": ano, "entraram": entraram, "sairam": sairam,
                      "saldo": entraram - sairam})
    return saida


def panorama(db: Database, meses: int = MESES_DA_JANELA,
             hoje: date | None = None) -> dict[str, Any]:
    """As pessoas, o trabalho em curso, a reposicao -- e o dinheiro.

    O dinheiro vem inteiro do `fomento.painel`: editais, vigencias e
    captacao ja tem dono, e refazer a conta aqui daria duas respostas
    para a mesma pergunta.
    """
    from . import fomento

    hoje = hoje or _hoje()
    saidas = saidas_previstas(db, meses=meses, hoje=hoje)
    risco = trabalho_em_risco(db, meses=meses, hoje=hoje)
    try:
        dinheiro = fomento.painel(db)
    except Exception:  # noqa: BLE001 -- sem fomento a tela das pessoas continua
        dinheiro = None
    return {
        "hoje": hoje.isoformat(),
        "janela_meses": meses,
        "pessoas": saidas,
        "trabalho": risco,
        "renovacao": renovacao(db, hoje=hoje),
        "dinheiro": dinheiro,
    }
