"""Editais, prazos e o dinheiro que entra -- e o que nao entrou.

O painel sabia dizer quanto o laboratorio TEM: `projects` guarda
financiador, processo, valor e vigencia. Nao sabia dizer as tres coisas
que fazem perder dinheiro:

  1. o EDITAL que fecha e ninguem viu a tempo;
  2. a VIGENCIA que termina -- com prestacao de contas junto -- e que so
     vira assunto quando ja e urgencia;
  3. a RECUSA, que nao vira projeto e por isso some do sistema. Sem as
     recusas nao existe taxa de aprovacao: existe a lembranca de quem
     aprovou, que e sempre melhor do que a realidade.

Duas regras de honestidade estao no codigo, e nao na tela:

  · taxa de aprovacao com poucas submissoes nao e taxa, e acaso com sinal
    de porcentagem. Abaixo de N_MINIMO_PARA_TAXA a funcao devolve None e
    diz por que -- em vez de anunciar "50%" que sao um sim e um nao.

  · somar reais de anos diferentes como se fossem a mesma moeda infla o
    total e ninguem percebe. Nao ha indice de inflacao nesta casa, entao
    o total sai SEMPRE com os anos que o compoem ao lado, e a tela e
    obrigada a mostrar isso. Inventar um deflator seria pior.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from .db import Database

# Abaixo disto, "taxa de aprovacao" e uma fracao de numeros pequenos: com
# tres submissoes ela so pode ser 0%, 33%, 67% ou 100%, e nenhum desses
# numeros diz nada sobre a proxima.
N_MINIMO_PARA_TAXA = 8

# O que conta como "fecha logo" e "termina logo". Sao prazos de trabalho,
# nao de susto: um edital de projeto pede semanas de escrita, e uma
# prestacao de contas pede o trimestre inteiro.
DIAS_EDITAL_PROXIMO = 45
DIAS_VIGENCIA_PROXIMA = 120

SITUACOES = (
    ("submetida", "Submetida"),
    ("aprovada", "Aprovada"),
    ("recusada", "Recusada"),
    ("retirada", "Retirada"),
)
DECIDIDAS = ("aprovada", "recusada")


def _hoje() -> date:
    return date.today()


def _data(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except ValueError:
        return None


def _dias_ate(valor: Any, hoje: date | None = None) -> int | None:
    alvo = _data(valor)
    if alvo is None:
        return None
    return (alvo - (hoje or _hoje())).days


def editais(db: Database, incluir_arquivados: bool = False) -> list[dict]:
    """Os editais declarados, com quantos dias faltam para fechar."""
    filtro = "" if incluir_arquivados else " WHERE arquivado = 0"
    linhas = db.dicts("SELECT * FROM editais" + filtro
                      + " ORDER BY fecha_em IS NULL, fecha_em, nome")
    hoje = _hoje()
    for linha in linhas:
        dias = _dias_ate(linha.get("fecha_em"), hoje)
        linha["dias"] = dias
        # "sem prazo declarado" NAO e "prazo longe": e desconhecido, e a
        # tela precisa poder distinguir os dois
        linha["estado"] = ("sem_prazo" if dias is None else
                           "fechado" if dias < 0 else
                           "fecha_logo" if dias <= DIAS_EDITAL_PROXIMO else "aberto")
    return linhas


def declarar_edital(db: Database, code: str, nome: str, **extra: Any) -> dict:
    campos = {"code": code, "nome": nome}
    for chave in ("agencia", "modalidade", "abre_em", "fecha_em",
                  "valor_teto", "url", "observacao", "arquivado"):
        if chave in extra:
            campos[chave] = extra[chave]
    novo_id = db.upsert("editais", campos, conflict=("code",))
    return db.dicts("SELECT * FROM editais WHERE id = ?", (novo_id,))[0]


def submissoes(db: Database, ano: int | None = None) -> list[dict]:
    args: tuple = ()
    filtro = ""
    if ano:
        filtro = " WHERE substr(s.submetido_em, 1, 4) = ?"
        args = (str(ano),)
    return db.dicts(
        "SELECT s.*, e.nome AS edital, e.agencia,"
        "       m.full_name AS proponente, l.name AS linha"
        "  FROM submissoes_fomento s"
        "  LEFT JOIN editais e ON e.id = s.edital_id"
        "  LEFT JOIN members m ON m.id = s.proponente_id"
        "  LEFT JOIN research_lines l ON l.id = s.linha_id"
        + filtro + " ORDER BY s.submetido_em DESC, s.id DESC", args)


def registrar_submissao(db: Database, titulo: str, **extra: Any) -> dict:
    campos: dict[str, Any] = {"titulo": titulo}
    for chave in ("edital_id", "project_id", "proponente_id", "linha_id",
                  "submetido_em", "situacao", "decidido_em", "valor_pedido",
                  "valor_aprovado", "observacao"):
        if chave in extra and extra[chave] is not None:
            campos[chave] = extra[chave]
    situacao = campos.get("situacao", "submetida")
    if situacao not in dict(SITUACOES):
        raise ValueError("situação desconhecida: %s" % situacao)
    if extra.get("id"):
        db.update_row("submissoes_fomento", int(extra["id"]), campos)
        return db.dicts("SELECT * FROM submissoes_fomento WHERE id = ?",
                        (int(extra["id"]),))[0]
    novo_id = db.insert("submissoes_fomento", campos)
    return db.dicts("SELECT * FROM submissoes_fomento WHERE id = ?", (novo_id,))[0]


def taxa_de_aprovacao(linhas: list[dict]) -> dict[str, Any]:
    """Aprovadas sobre DECIDIDAS -- e nunca sobre o total.

    Quem ainda nao foi julgado nao e recusa. Contar as pendentes no
    denominador faz a taxa despencar toda vez que o laboratorio submete
    algo novo, o que e exatamente o contrario do que a taxa deveria
    dizer.
    """
    decididas = [x for x in linhas if x.get("situacao") in DECIDIDAS]
    aprovadas = [x for x in decididas if x["situacao"] == "aprovada"]
    pendentes = [x for x in linhas if x.get("situacao") == "submetida"]
    saida = {
        "decididas": len(decididas), "aprovadas": len(aprovadas),
        "recusadas": len(decididas) - len(aprovadas),
        "pendentes": len(pendentes), "taxa": None, "aviso": None,
    }
    if len(decididas) < N_MINIMO_PARA_TAXA:
        saida["aviso"] = (
            "com %d submissão(ões) julgada(s) não há taxa: seriam %d%% ou "
            "%d%% conforme a próxima, e nenhum dos dois diria nada sobre o "
            "edital seguinte" % (
                len(decididas),
                round(100 * len(aprovadas) / (len(decididas) + 1)),
                round(100 * (len(aprovadas) + 1) / (len(decididas) + 1))))
        return saida
    saida["taxa"] = round(100.0 * len(aprovadas) / len(decididas), 1)
    return saida


def vigencias(db: Database) -> list[dict]:
    """Projetos com dinheiro e com fim de vigencia a vista."""
    linhas = db.dicts(
        "SELECT p.id, p.code, p.name, p.funder, p.grant_number, p.amount,"
        "       p.started_on, p.ended_on, p.status, l.name AS linha"
        "  FROM projects p"
        "  LEFT JOIN research_lines l ON l.id = p.research_line_id"
        " WHERE p.funder IS NOT NULL AND TRIM(p.funder) <> ''"
        " ORDER BY p.ended_on IS NULL, p.ended_on")
    hoje = _hoje()
    for linha in linhas:
        dias = _dias_ate(linha.get("ended_on"), hoje)
        linha["dias"] = dias
        linha["estado"] = ("sem_prazo" if dias is None else
                           "encerrada" if dias < 0 else
                           "termina_logo" if dias <= DIAS_VIGENCIA_PROXIMA
                           else "vigente")
    return linhas


def _valor_por_ano(linhas: list[dict], campo_data: str, campo_valor: str
                   ) -> list[dict]:
    """Soma por ano -- e por ano de proposito.

    Um total unico juntaria reais de 2015 com reais de hoje como se
    valessem o mesmo. Nao ha deflator aqui, e inventar um seria pior do
    que nao ter: o que da para fazer honestamente e mostrar os anos.
    """
    por_ano: dict[int, dict] = {}
    for linha in linhas:
        d = _data(linha.get(campo_data))
        valor = linha.get(campo_valor)
        if d is None or valor is None:
            continue
        alvo = por_ano.setdefault(d.year, {"ano": d.year, "valor": 0.0, "n": 0})
        alvo["valor"] += float(valor)
        alvo["n"] += 1
    return [por_ano[a] for a in sorted(por_ano)]


def painel(db: Database, ano: int | None = None) -> dict[str, Any]:
    """Tudo o que a aba de Fomento mostra, numa chamada."""
    hoje = _hoje()
    abertos = editais(db)
    todas = submissoes(db)
    do_ano = [x for x in todas
              if str(x.get("submetido_em") or "")[:4] == str(ano or hoje.year)]
    contratos = vigencias(db)

    aprovadas = [x for x in todas if x.get("situacao") == "aprovada"]
    captado = _valor_por_ano(aprovadas, "decidido_em", "valor_aprovado")
    anos = [x["ano"] for x in captado]

    return {
        "ano": ano or hoje.year,
        "hoje": hoje.isoformat(),
        "editais": abertos,
        "fecham_logo": [x for x in abertos if x["estado"] == "fecha_logo"],
        "submissoes": todas,
        "submissoes_do_ano": do_ano,
        "aprovacao": taxa_de_aprovacao(todas),
        "aprovacao_do_ano": taxa_de_aprovacao(do_ano),
        "vigencias": contratos,
        "terminam_logo": [x for x in contratos if x["estado"] == "termina_logo"],
        "captado_por_ano": captado,
        # o total vem acompanhado dos anos que o formam: quem ler sabe que
        # esta somando moedas de epocas diferentes
        "captado_total": round(sum(x["valor"] for x in captado), 2) if captado else 0.0,
        "captado_anos": [min(anos), max(anos)] if anos else None,
        "situacoes": [{"code": c, "label": r} for c, r in SITUACOES],
        "dias_edital": DIAS_EDITAL_PROXIMO,
        "dias_vigencia": DIAS_VIGENCIA_PROXIMA,
        "minimo_para_taxa": N_MINIMO_PARA_TAXA,
    }
