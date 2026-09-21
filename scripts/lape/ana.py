"""Ana -- a assistente que responde sobre o laboratorio sem inventar nada.

Ana NAO e um modelo de linguagem, e isso e uma decisao de projeto, nao
uma limitacao de orcamento. Um modelo generico responderia qualquer
pergunta com um numero plausivel -- e um numero plausivel sobre producao
cientifica e pior do que nenhum: ele vai parar num relatorio da CAPES, num
e-mail para a chefia, num slide de defesa. Quem le nao tem como saber que
aquele "23 artigos" foi estimado.

Entao Ana funciona ao contrario. Cada pergunta que ela entende esta
DECLARADA aqui embaixo, com as palavras que a disparam e a consulta que a
responde. A resposta traz sempre tres coisas:

  - o numero, que saiu de uma consulta ao banco e de mais lugar nenhum;
  - a lista por tras do numero, para quem quiser conferir item a item;
  - a FONTE, dizendo de que tabela e com que filtro ele veio.

E o que ela nao entende, ela diz que nao entende -- e mostra o que sabe
responder. Nao ha caminho aqui em que Ana chute.

Ela tambem respeita o perfil de quem pergunta: prazo de bolsa e etapa de
tese sao da coordenacao, e uma pergunta sobre isso vinda de quem tem
leitura e RECUSADA, nao respondida pela metade. Responder "nao posso
dizer" e honesto; responder um numero parcial sem avisar nao e.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any

from .db import Database
from .mapping import STATUS_MAP
from .util import strip_accents

NOME = "Ana"

# O perfil de quem pergunta quando ninguem disse qual e.
PERFIL_PADRAO = "leitura"

RANQUE = {"leitura": 0, "integrante": 1, "coordenacao": 2, "admin": 3}

SITUACAO_ROTULO = {
    "em_producao": "em produção", "submetido": "submetido",
    "em_revisao": "em revisão", "aceito": "aceito", "publicado": "publicado",
    "rejeitado": "rejeitado", "arquivado": "arquivado",
}

# Um manuscrito nestas situacoes ainda depende de alguem para andar.
EM_CURSO = ("em_producao", "submetido", "em_revisao", "aceito")

# Quantos dias sem nenhuma data nova ate um manuscrito contar como parado.
DIAS_PARA_PARAR = 90


def _hoje() -> date:
    return date.today()


def _palavras(pergunta: str) -> list[str]:
    """As palavras da pergunta, sem acento e sem pontuacao, NA ORDEM.

    "Quantos artigos publicámos?" e "quantos artigos publicamos" tem de
    cair na mesma intencao: quem digita as pressas nao acentua, e quem
    digita com calma acentua.

    A ordem importa e por isso e uma lista, nao um conjunto. Em "artigos
    submetidos ou aceitos" ha duas situacoes, e alguma delas tem de
    ganhar; com um conjunto quem ganhava era a ordem interna do Python --
    a mesma pergunta podia responder submetidos hoje e aceitos amanha, e
    nada na tela explicaria a diferenca. Ganha a primeira citada.
    """
    limpo = strip_accents(str(pergunta or "")).lower()
    return [p for p in re.split(r"[^a-z0-9]+", limpo) if p]


def _ano_da_pergunta(pergunta: str) -> int | None:
    """O ano citado, quando ha um -- e so um de quatro digitos plausivel."""
    anos = [int(a) for a in re.findall(r"\b(?:19|20)\d{2}\b", str(pergunta or ""))]
    return anos[0] if anos else None


def _situacao_da_pergunta(palavras: list[str]) -> str | None:
    """A situacao citada, pelo mesmo vocabulario que a planilha usa.

    Reusar o STATUS_MAP e o que faz "em analise", "no prelo" e "submetido"
    chegarem na mesma situacao aqui e na importacao. Vocabulario duplicado
    e vocabulario que diverge.
    """
    for palavra in palavras:
        # O plural tambem, porque ninguem pergunta "quais artigos submetido".
        # O STATUS_MAP fala no singular, que e como a planilha escreve.
        for tentativa in (palavra, palavra[:-1] if palavra.endswith("s") else palavra):
            canonica = STATUS_MAP.get(tentativa)
            if canonica:
                return canonica
    return None


# "Maria DAS Gracas" e "Jose DE Souza": a particula e do idioma, nao da
# pessoa. Sem tira-las, "quantos artigos DAS linhas de pesquisa" apontaria
# a Maria com toda a confianca -- e a resposta viria com o nome dela.
PARTICULAS = frozenset(
    {"de", "da", "do", "das", "dos", "e", "dr", "dra", "prof", "profa"})


def _pessoa_da_pergunta(db: Database, palavras: list[str]) -> dict[str, Any] | None:
    """O integrante citado pelo nome, quando ha um.

    Casa por PALAVRA INTEIRA do nome, e nao por pedaco: "Andrade" acha
    Alexandro Andrade, e "ana" nao acha "Juliana" -- procurar pedaco faria
    metade do cadastro casar com metade das perguntas.

    Fora as particulas, e fora o que tem menos de tres letras: "Sa" e
    "Wu" sao nomes, mas dentro de uma frase eles aparecem por acaso, e um
    acerto por acaso aqui poe o nome de uma pessoa numa resposta que nao e
    sobre ela.
    """
    achados: list[tuple[int, dict[str, Any]]] = []
    for pessoa in db.dicts("SELECT id, full_name, short_name, role FROM members"):
        nome = strip_accents(str(pessoa["full_name"] or "")).lower()
        partes = {p for p in re.split(r"[^a-z0-9]+", nome)
                  if len(p) >= 3 and p not in PARTICULAS}
        casadas = partes & set(palavras)
        if casadas:
            achados.append((len(casadas), pessoa))
    if not achados:
        return None
    achados.sort(key=lambda x: (-x[0], str(x[1]["full_name"])))
    return achados[0][1]


# ----------------------------------------------------------------------
# As respostas. Uma funcao por pergunta, uma consulta por funcao.
# ----------------------------------------------------------------------
def _acervo(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    por_situacao = db.dicts(
        "SELECT status, COUNT(*) AS n FROM articles GROUP BY status ORDER BY n DESC")
    total = sum(int(linha["n"]) for linha in por_situacao)
    if not total:
        return {"resposta": "Não há nenhum artigo cadastrado ainda.",
                "numero": 0, "itens": [],
                "fonte": "tabela de artigos, sem filtro"}
    return {
        "resposta": f"O laboratório tem {total} artigo(s) no acervo.",
        "numero": total,
        "itens": [{"rotulo": SITUACAO_ROTULO.get(l["status"], l["status"] or "sem situação"),
                   "valor": int(l["n"])} for l in por_situacao],
        "colunas": ("Situação", "Quantos"),
        "fonte": "tabela de artigos, contando todas as situações",
    }


def _publicados(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    ano = ctx.get("ano")
    suposto = ano is None
    ano = ano or ctx["hoje"].year
    artigos = db.dicts(
        "SELECT internal_code, title, journal FROM articles"
        " WHERE status = 'publicado' AND year_published = ?"
        " ORDER BY title", (ano,))
    if not artigos:
        resposta = f"Nenhum artigo publicado registrado em {ano}."
    else:
        resposta = f"{len(artigos)} artigo(s) publicado(s) em {ano}."
    if suposto:
        resposta += " (Você não disse o ano, então respondi sobre este.)"
    return {
        "resposta": resposta, "numero": len(artigos),
        "itens": [{"rotulo": a["title"], "valor": a["journal"] or "revista não declarada",
                   "code": a["internal_code"]} for a in artigos],
        "colunas": ("Artigo", "Revista"),
        "fonte": f"tabela de artigos, situação publicado e ano de publicação {ano}",
    }


def _por_situacao(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    situacao = ctx.get("situacao")
    if not situacao:
        return _acervo(db, ctx)
    artigos = db.dicts(
        "SELECT internal_code, title, journal, lead_name FROM articles"
        " WHERE status = ? ORDER BY title", (situacao,))
    rotulo = SITUACAO_ROTULO.get(situacao, situacao)
    return {
        "resposta": (f"{len(artigos)} artigo(s) {rotulo}."
                     if artigos else f"Nenhum artigo {rotulo} no momento."),
        "numero": len(artigos),
        "itens": [{"rotulo": a["title"], "valor": a["lead_name"] or "sem responsável",
                   "code": a["internal_code"]} for a in artigos],
        "colunas": ("Artigo", "Responsável"),
        "fonte": f"tabela de artigos, situação {situacao}",
    }


def _parados(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    """Manuscrito em curso sem nenhuma data nova ha muito tempo.

    "Parado" aqui e uma definicao, nao um julgamento: a ultima data
    registrada -- marco, submissao, revisao -- tem mais de noventa dias. A
    resposta diz a definicao junto, porque sem ela o numero acusa gente.
    """
    limite = (ctx["hoje"] - timedelta(days=DIAS_PARA_PARAR)).isoformat()
    marcas = ", ".join("?" for _ in EM_CURSO)
    artigos = db.dicts(
        "SELECT a.internal_code, a.title, a.status, a.lead_name,"
        "       COALESCE(MAX(m.occurred_on), a.started_on) AS ultima"
        "  FROM articles a"
        "  LEFT JOIN article_milestones m ON m.article_id = a.id"
        f" WHERE a.status IN ({marcas})"
        " GROUP BY a.id"
        " HAVING ultima IS NULL OR ultima < ?"
        " ORDER BY ultima", (*EM_CURSO, limite))
    return {
        "resposta": (f"{len(artigos)} manuscrito(s) sem data nova há mais de"
                     f" {DIAS_PARA_PARAR} dias."
                     if artigos else
                     f"Nenhum manuscrito em curso está há mais de {DIAS_PARA_PARAR}"
                     " dias sem data nova."),
        "numero": len(artigos),
        "itens": [{"rotulo": a["title"],
                   "valor": (f"última data: {a['ultima']}" if a["ultima"]
                             else "nenhuma data registrada"),
                   "code": a["internal_code"]} for a in artigos],
        "colunas": ("Manuscrito", "Última data"),
        "fonte": ("artigos em curso cruzados com a última data registrada"
                  f" (marcos e início), corte em {DIAS_PARA_PARAR} dias"),
    }


def _agenda(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    """A agenda de hoje, ou dos proximos sete dias."""
    hoje = ctx["hoje"]
    so_hoje = ctx.get("so_hoje", False)
    fim = hoje if so_hoje else hoje + timedelta(days=7)
    eventos = db.dicts(
        "SELECT title, kind, start_at, all_day, location_name FROM events"
        " WHERE date(start_at) BETWEEN ? AND ?"
        "   AND COALESCE(status, 'confirmado') <> 'cancelado'"
        " ORDER BY start_at", (hoje.isoformat(), fim.isoformat()))
    quando = "hoje" if so_hoje else "nos próximos 7 dias"
    return {
        "resposta": (f"{len(eventos)} compromisso(s) {quando}."
                     if eventos else f"Nada na agenda {quando}."),
        "numero": len(eventos),
        "itens": [{"rotulo": e["title"],
                   "valor": _quando_do_evento(e),
                   "code": e["kind"]} for e in eventos],
        "colunas": ("Compromisso", "Quando"),
        "fonte": (f"tabela de atividades, de {hoje.isoformat()} a {fim.isoformat()},"
                  " sem as canceladas"),
    }


def _quando_do_evento(evento: dict[str, Any]) -> str:
    """Data e hora do compromisso -- e so a data quando nao ha hora.

    Dia inteiro com "00:00" na frente e pior do que sem hora nenhuma: quem
    le entende que a reuniao e a meia-noite.
    """
    bruto = str(evento.get("start_at") or "")
    try:
        quando = datetime.fromisoformat(bruto.replace("Z", "+00:00"))
    except ValueError:
        return bruto or "sem data"
    dia = quando.strftime("%d/%m")
    if evento.get("all_day") or (quando.hour == 0 and quando.minute == 0):
        return f"{dia} (dia inteiro)"
    return f"{dia} às {quando.strftime('%H:%M')}"


def _da_pessoa(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    pessoa = ctx.get("pessoa")
    if not pessoa:
        return {
            "resposta": "Não reconheci o nome. Pergunte pelo sobrenome de quem está"
                        " no cadastro de integrantes.",
            "numero": None, "itens": [],
            "fonte": "cadastro de integrantes, comparando palavra por palavra",
        }
    linhas = db.dicts(
        "SELECT a.status, COUNT(DISTINCT a.id) AS n"
        "  FROM article_authors aa JOIN articles a ON a.id = aa.article_id"
        " WHERE aa.member_id = ? GROUP BY a.status ORDER BY n DESC", (pessoa["id"],))
    total = sum(int(l["n"]) for l in linhas)
    nome = pessoa["full_name"]
    return {
        "resposta": (f"{nome} assina {total} artigo(s) do acervo."
                     if total else f"{nome} ainda não assina nenhum artigo do acervo."),
        "numero": total,
        "itens": [{"rotulo": SITUACAO_ROTULO.get(l["status"], l["status"] or "sem situação"),
                   "valor": int(l["n"])} for l in linhas],
        "colunas": ("Situação", "Quantos"),
        "fonte": f"autoria dos artigos, integrante {nome} (id {pessoa['id']})",
    }


def _equipe(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    linhas = db.dicts(
        "SELECT COALESCE(role, 'sem vínculo declarado') AS vinculo, COUNT(*) AS n"
        "  FROM members"
        " WHERE COALESCE(is_external, 0) = 0 AND COALESCE(active, 1) <> 0"
        "   AND left_on IS NULL"
        " GROUP BY vinculo ORDER BY n DESC")
    total = sum(int(l["n"]) for l in linhas)
    return {
        "resposta": f"{total} pessoa(s) ativa(s) no laboratório.",
        "numero": total,
        "itens": [{"rotulo": l["vinculo"], "valor": int(l["n"])} for l in linhas],
        "colunas": ("Vínculo", "Quantas"),
        "fonte": ("cadastro de integrantes: sem os externos, sem os inativos"
                  " e sem quem já saiu"),
    }


def _linhas_de_pesquisa(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    linhas = db.dicts(
        "SELECT rl.name, rl.code,"
        "       (SELECT COUNT(*) FROM articles a WHERE a.research_line_id = rl.id) AS n"
        "  FROM research_lines rl WHERE COALESCE(rl.active, 1) <> 0"
        " ORDER BY n DESC, rl.name")
    return {
        "resposta": f"{len(linhas)} linha(s) de pesquisa declarada(s).",
        "numero": len(linhas),
        "itens": [{"rotulo": l["name"], "valor": f"{l['n']} artigo(s)",
                   "code": l["code"]} for l in linhas],
        "colunas": ("Linha de pesquisa", "Artigos"),
        "fonte": "tabela de linhas de pesquisa ativas, com os artigos de cada uma",
    }


def _lacunas(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    from .agents import curator

    conferencia = curator.validate(db)
    buracos = [i for i in conferencia["issues"] if int(i["n"]) > 0]
    return {
        "resposta": (f"{len(buracos)} lacuna(s) no cadastro."
                     if buracos else "Nenhuma lacuna conhecida no cadastro."),
        "numero": len(buracos),
        "itens": [{"rotulo": i["label"], "valor": int(i["n"])} for i in buracos],
        "colunas": ("O que falta", "Quantos"),
        "fonte": "a mesma conferência do curador (lape_agent.py status)",
    }


def _prazos(db: Database, ctx: dict[str, Any]) -> dict[str, Any]:
    from . import sustentabilidade

    quadro = sustentabilidade.saidas_previstas(db, hoje=ctx["hoje"])
    saem = quadro["saem"]
    itens = [{"rotulo": p["quem"],
              "valor": f"{p['quando']} — {p['motivo']}",
              "code": p.get("vinculo")} for p in saem]
    resposta = (f"{len(saem)} pessoa(s) com prazo nos próximos"
                f" {quadro['janela_meses']} meses."
                if saem else
                f"Ninguém com prazo declarado nos próximos {quadro['janela_meses']} meses.")
    if quadro["sem_prazo"]:
        resposta += (f" Outras {len(quadro['sem_prazo'])} pessoa(s) estão sem prazo"
                     " declarado — sobre essas o sistema não sabe dizer.")
    return {
        "resposta": resposta, "numero": len(saem), "itens": itens,
        "colunas": ("Quem", "Quando e por quê"),
        "fonte": ("bolsa e prazo de tese no cadastro de integrantes;"
                  " vale a primeira das duas datas"),
    }


# ----------------------------------------------------------------------
# O que Ana sabe responder. Fora desta tabela, ela diz que nao sabe.
# ----------------------------------------------------------------------
# `grupos` e uma conjuncao de disjuncoes: a pergunta precisa ter ao menos
# uma palavra de CADA grupo. Mais grupos satisfeitos e pergunta mais
# especifica, e e ela que ganha -- "quantos artigos publicados em 2026"
# nao pode cair no acervo inteiro so porque tem "artigos".
#
# Quem decide e o PESO, e nao a posicao na lista: o acervo esta declarado
# primeiro justamente para isso ficar visivel. Deixar a ordem decidir
# funciona ate alguem inserir uma pergunta nova no meio da lista e mudar,
# sem perceber, a resposta de outra.
PERGUNTAS: tuple[dict[str, Any], ...] = (
    {
        "code": "acervo",
        "exemplo": "quantos artigos o laboratório tem?",
        "minimo": "leitura",
        "grupos": (("artigo", "artigos", "acervo", "producao", "publicacoes"),),
        "responder": _acervo,
    },
    {
        "code": "publicados",
        "exemplo": "quantos artigos publicamos em 2026?",
        "minimo": "leitura",
        "grupos": (("artigo", "artigos", "publicacao", "publicacoes", "paper", "papers"),
                   ("publicado", "publicados", "publicada", "publicadas",
                    "publicamos", "publicou", "saiu", "sairam")),
        "responder": _publicados,
    },
    {
        "code": "parados",
        "exemplo": "quais artigos estão parados?",
        "minimo": "integrante",
        "grupos": (("artigo", "artigos", "manuscrito", "manuscritos", "trabalho",
                    "trabalhos"),
                   ("parado", "parados", "parada", "paradas", "travado", "travados",
                    "atrasado", "atrasados", "esquecido", "esquecidos")),
        "responder": _parados,
    },
    {
        "code": "situacao",
        "exemplo": "quais artigos estão submetidos?",
        "minimo": "leitura",
        "grupos": (("artigo", "artigos", "manuscrito", "manuscritos"),
                   ("submetido", "submetidos", "aceito", "aceitos", "revisao",
                    "rejeitado", "rejeitados", "producao", "arquivado", "arquivados",
                    "andamento", "escrita")),
        "responder": _por_situacao,
    },
    {
        "code": "pessoa",
        "exemplo": "quantos artigos do Vilarino?",
        "minimo": "leitura",
        "grupos": (("artigo", "artigos", "producao", "publicacoes", "assina",
                    "publicou"),),
        "responder": _da_pessoa,
        "exige_pessoa": True,
    },
    {
        "code": "agenda",
        "exemplo": "qual é a agenda de hoje?",
        "minimo": "leitura",
        "grupos": (("agenda", "calendario", "compromisso", "compromissos", "reuniao",
                    "reunioes", "atividade", "atividades", "acontece", "evento",
                    "eventos"),),
        "responder": _agenda,
    },
    {
        "code": "prazos",
        "exemplo": "quem sai do laboratório este ano?",
        "minimo": "coordenacao",
        "grupos": (("prazo", "prazos", "bolsa", "bolsas", "defesa", "defesas",
                    "sai", "saem", "saida", "saidas", "termina", "terminam",
                    "vence", "vencem"),),
        "responder": _prazos,
    },
    {
        "code": "lacunas",
        "exemplo": "o que falta preencher no cadastro?",
        "minimo": "integrante",
        "grupos": (("falta", "faltando", "lacuna", "lacunas", "incompleto",
                    "incompletos", "preencher", "vazio", "vazios"),),
        "responder": _lacunas,
    },
    {
        "code": "linhas",
        "exemplo": "quais são as linhas de pesquisa?",
        "minimo": "leitura",
        "grupos": (("linha", "linhas"),),
        "responder": _linhas_de_pesquisa,
    },
    {
        "code": "equipe",
        "exemplo": "quantas pessoas tem o laboratório?",
        "minimo": "leitura",
        "grupos": (("pessoa", "pessoas", "integrante", "integrantes", "equipe",
                    "gente", "alunos", "orientandos", "membros"),),
        "responder": _equipe,
    },
)


def exemplos(perfil: str = PERFIL_PADRAO) -> list[dict[str, str]]:
    """As perguntas que Ana sabe responder para ESTE perfil.

    Mostrar a quem tem leitura uma pergunta que ela vai recusar e ensinar
    o caminho da frustracao.
    """
    teto = RANQUE.get(perfil, 0)
    return [{"code": p["code"], "pergunta": p["exemplo"]}
            for p in PERGUNTAS if RANQUE[p["minimo"]] <= teto]


def entender(db: Database, pergunta: str) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    """Qual intencao a pergunta dispara, e o que ela carrega junto.

    Devolve (intencao, contexto). Intencao None e "nao entendi" -- e e uma
    resposta legitima, nao uma falha a ser disfarcada.
    """
    palavras = _palavras(pergunta)
    presentes = set(palavras)
    contexto: dict[str, Any] = {
        "hoje": _hoje(),
        "ano": _ano_da_pergunta(pergunta),
        "situacao": _situacao_da_pergunta(palavras),
        "pessoa": _pessoa_da_pergunta(db, palavras),
        "so_hoje": "hoje" in presentes,
    }
    melhor: tuple[int, dict[str, Any]] | None = None
    for intencao in PERGUNTAS:
        if intencao.get("exige_pessoa") and not contexto["pessoa"]:
            continue
        if not all(any(p in presentes for p in grupo) for grupo in intencao["grupos"]):
            continue
        peso = len(intencao["grupos"]) + (1 if intencao.get("exige_pessoa") else 0)
        if melhor is None or peso > melhor[0]:
            melhor = (peso, intencao)
    return (melhor[1] if melhor else None), contexto


def responder(db: Database, pergunta: str,
              perfil: str = PERFIL_PADRAO) -> dict[str, Any]:
    """A resposta de Ana: o numero, a lista, a fonte -- ou o "nao sei".

    Nunca levanta excecao por nao entender. A tela precisa mostrar alguma
    coisa util mesmo quando a pergunta nao casa com nada, e um erro 500
    nao e util.
    """
    texto = str(pergunta or "").strip()
    teto = RANQUE.get(perfil, 0)
    saida: dict[str, Any] = {
        "pergunta": texto, "quem_responde": NOME,
        "entendi": False, "intencao": None,
        "resposta": "", "numero": None, "itens": [], "fonte": None,
        # Cabecalho da lista. "Motriz" embaixo de "Quanto" nao e leitura:
        # a coluna mente sobre o que ha nela.
        "colunas": ("O quê", "Quanto"),
        "exemplos": exemplos(perfil),
    }
    if not texto:
        saida["resposta"] = ("Pergunte alguma coisa sobre o laboratório."
                             " Abaixo está o que eu sei responder.")
        return saida

    intencao, contexto = entender(db, texto)
    if intencao is None:
        saida["resposta"] = ("Não sei responder isso ainda -- e prefiro dizer isso a"
                             " inventar um número. Aqui está o que eu sei responder.")
        return saida

    saida["intencao"] = intencao["code"]
    if RANQUE[intencao["minimo"]] > teto:
        # Nao e um "nao entendi": Ana entendeu, e nao pode responder. Dizer
        # qual das duas coisas aconteceu evita a pessoa repetir a pergunta
        # de dez maneiras achando que errou as palavras.
        saida["resposta"] = (f"Entendi a pergunta, mas essa resposta é do perfil"
                             f" {intencao['minimo']}. Peça à coordenação.")
        saida["entendi"] = True
        saida["negado"] = True
        return saida

    resultado = intencao["responder"](db, contexto)
    saida.update(resultado)
    saida["entendi"] = True
    saida["intencao"] = intencao["code"]
    return saida
