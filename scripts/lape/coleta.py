"""A bancada: coleta de dados com participantes.

O sistema sabia tudo sobre o artigo publicado e nada sobre o que foi
medido para escreve-lo. A escala de dor de quarenta mulheres com
fibromialgia, colhida na linha de base e depois de dezesseis semanas,
morava numa planilha no computador de quem coletou -- e era dali que
saiam a tabela do artigo, a defesa da dissertacao e o relatorio da
agencia. Planilha nao diz quem falta medir, nao avisa que a janela do
seguimento fechou e nao sobrevive ao fim da bolsa de quem a mantinha.

Este modulo e o outro lado do laboratorio. Tres cuidados o atravessam:

1. NINGUEM E NOMEADO. O participante e um codigo. Nao ha coluna de nome,
   e-mail ou telefone no esquema (ver sql/schema.sql), e nao ha aqui
   nenhuma funcao que aceite um. A lista que liga o codigo a pessoa fica
   fora do sistema, com quem coordena o estudo.

2. FALTA E DADO. Um painel de coleta que so mostra o que foi coletado
   nao serve para coletar: serve para admirar. O que este modulo procura
   e o buraco -- quem nao tem linha de base, quem passou da janela do
   seguimento, quem parou de aparecer.

3. NUMERO PEQUENO SE ANUNCIA. Com seis participantes por grupo, um
   tamanho de efeito e um numero bonito sem significado nenhum. As
   funcoes devolvem `n` sempre ao lado da estatistica, e marcam como
   instavel o que foi calculado com pouca gente -- porque o d de Cohen
   nao avisa sozinho que nasceu de seis pessoas.
"""
from __future__ import annotations

import statistics
from datetime import date, datetime
from typing import Any

from .db import Database

# Abaixo disto o tamanho de efeito e ruido com casa decimal. Nao e um
# limiar de publicacao -- e o ponto a partir do qual a conta para de
# dizer mais do que os numeros crus ja dizem.
N_MINIMO_PARA_EFEITO = 10

# Para que lado de cada instrumento e melhora. Sem isso "caiu 4 pontos"
# nao se interpreta: em dor e bom, em qualidade de vida e ruim.
DIRECOES = {
    "maior_melhor": "quanto maior, melhor",
    "menor_melhor": "quanto menor, melhor",
    "neutro": "sem direcao de melhora",
}

SITUACOES = {
    "ativo": "Ativo",
    "concluiu": "Concluiu o protocolo",
    "desistiu": "Desistiu",
    "excluido": "Excluído por critério",
    "perdido": "Perda de seguimento",
}


def _hoje() -> date:
    return date.today()


def _data(valor: Any) -> date | None:
    if not valor:
        return None
    try:
        return datetime.fromisoformat(str(valor)[:10]).date()
    except ValueError:
        return None


# ----------------------------------------------------------------------
# Catalogo: instrumentos, protocolos e momentos
# ----------------------------------------------------------------------
def instrumentos(db: Database, incluir_inativos: bool = False) -> list[dict]:
    onde = "" if incluir_inativos else " WHERE ativo = 1"
    linhas = db.dicts("SELECT * FROM instrumentos" + onde + " ORDER BY nome")
    for linha in linhas:
        linha["direcao_label"] = DIRECOES.get(linha.get("direcao") or "", "")
        linha["subescalas_lista"] = [
            s.strip() for s in str(linha.get("subescalas") or "").split(";") if s.strip()]
        linha["n_coletas"] = db.scalar(
            "SELECT COUNT(*) FROM coletas WHERE instrumento_id = ?", (linha["id"],)) or 0
    return linhas


def declarar_instrumento(db: Database, code: str, nome: str, **extra: Any) -> dict:
    if not code or not nome:
        raise ValueError("instrumento precisa de código e nome")
    direcao = extra.get("direcao") or "maior_melhor"
    if direcao not in DIRECOES:
        raise ValueError("direção desconhecida: %s. Use %s"
                         % (direcao, ", ".join(DIRECOES)))
    dados = {"code": code.strip(), "nome": nome.strip(), "direcao": direcao,
             "descricao": extra.get("descricao"), "unidade": extra.get("unidade"),
             "minimo": extra.get("minimo"), "maximo": extra.get("maximo"),
             "subescalas": extra.get("subescalas"),
             "ativo": 1 if extra.get("ativo", 1) else 0}
    ident = db.upsert("instrumentos", dados, conflict=("code",))
    db.execute("UPDATE instrumentos SET updated_at = datetime('now') WHERE id = ?", (ident,))
    db.conn.commit()
    return db.dicts("SELECT * FROM instrumentos WHERE id = ?", (ident,))[0]


def protocolos(db: Database) -> list[dict]:
    linhas = db.dicts(
        "SELECT p.*, pr.name AS projeto"
        "  FROM protocolos p LEFT JOIN projects pr ON pr.id = p.project_id"
        " ORDER BY p.ativo DESC, p.nome")
    for linha in linhas:
        linha["momentos"] = db.dicts(
            "SELECT * FROM momentos WHERE protocolo_id = ? ORDER BY ordem, id",
            (linha["id"],))
        linha["n_participantes"] = db.scalar(
            "SELECT COUNT(*) FROM participantes WHERE protocolo_id = ?", (linha["id"],)) or 0
    return linhas


def declarar_protocolo(db: Database, code: str, nome: str, **extra: Any) -> dict:
    if not code or not nome:
        raise ValueError("protocolo precisa de código e nome")
    ident = db.upsert("protocolos", {
        "code": code.strip(), "nome": nome.strip(),
        "descricao": extra.get("descricao"), "project_id": extra.get("project_id"),
        "ativo": 1 if extra.get("ativo", 1) else 0}, conflict=("code",))
    db.conn.commit()
    return db.dicts("SELECT * FROM protocolos WHERE id = ?", (ident,))[0]


def declarar_momento(db: Database, protocolo_id: int, code: str, nome: str,
                     ordem: int = 1, dias_apos: int | None = None,
                     janela_dias: int = 14) -> dict:
    if not db.dicts("SELECT id FROM protocolos WHERE id = ?", (protocolo_id,)):
        raise ValueError("protocolo não existe")
    ident = db.upsert("momentos", {
        "protocolo_id": protocolo_id, "code": code.strip(), "nome": nome.strip(),
        "ordem": ordem, "dias_apos": dias_apos, "janela_dias": janela_dias},
        conflict=("protocolo_id", "code"))
    db.conn.commit()
    return db.dicts("SELECT * FROM momentos WHERE id = ?", (ident,))[0]


# ----------------------------------------------------------------------
# Participantes
# ----------------------------------------------------------------------
def inscrever(db: Database, codigo: str, protocolo_id: int | None = None,
              **extra: Any) -> dict:
    """Entra um participante. `codigo` e tudo o que o sistema sabe dele.

    Qualquer campo que identifique a pessoa e recusado aqui, e nao apenas
    ausente do esquema: quem escreve `inscrever(db, "P01", nome="Maria")`
    precisa receber um erro, e nao ver o nome sumir em silencio e achar
    que foi gravado.
    """
    proibidos = [k for k in extra
                 if any(marca in k.lower() for marca in
                        ("nome", "name", "email", "mail", "telefone", "phone",
                         "cpf", "rg", "documento", "endereco", "prontuario"))]
    if proibidos:
        raise ValueError(
            "o sistema não guarda dado que identifique o participante (%s). "
            "Use só o código; a lista que liga código e pessoa fica fora daqui."
            % ", ".join(sorted(proibidos)))
    if not codigo or not str(codigo).strip():
        raise ValueError("participante precisa de um código")
    situacao = extra.get("situacao") or "ativo"
    if situacao not in SITUACOES:
        raise ValueError("situação desconhecida: %s" % situacao)
    ident = db.upsert("participantes", {
        "codigo": str(codigo).strip(), "protocolo_id": protocolo_id,
        "grupo": extra.get("grupo"), "sexo": extra.get("sexo"),
        "ano_nascimento": extra.get("ano_nascimento"),
        "entrou_em": extra.get("entrou_em") or _hoje().isoformat(),
        "situacao": situacao, "observacao": extra.get("observacao")},
        conflict=("codigo",))
    db.conn.commit()
    return db.dicts("SELECT * FROM participantes WHERE id = ?", (ident,))[0]


def encerrar(db: Database, participante_id: int, situacao: str,
             motivo: str | None = None, em: str | None = None) -> dict:
    """Sai do protocolo. Desistencia com data e motivo e dado de estudo.

    Uma desistencia apagada nao vira "nunca existiu": vira n menor sem
    explicacao, e e assim que um ensaio perde a chance de contar o proprio
    fluxo no CONSORT.
    """
    if situacao not in SITUACOES:
        raise ValueError("situação desconhecida: %s" % situacao)
    if not db.dicts("SELECT id FROM participantes WHERE id = ?", (participante_id,)):
        raise ValueError("participante não existe")
    db.execute(
        "UPDATE participantes SET situacao = ?, motivo_saida = ?, saiu_em = ?,"
        "       updated_at = datetime('now') WHERE id = ?",
        (situacao, motivo, (em or _hoje().isoformat()) if situacao != "ativo" else None,
         participante_id))
    db.conn.commit()
    return db.dicts("SELECT * FROM participantes WHERE id = ?", (participante_id,))[0]


def participantes(db: Database, protocolo_id: int | None = None) -> list[dict]:
    onde, args = "", ()
    if protocolo_id:
        onde, args = " WHERE p.protocolo_id = ?", (protocolo_id,)
    linhas = db.dicts(
        "SELECT p.*, pr.nome AS protocolo FROM participantes p"
        " LEFT JOIN protocolos pr ON pr.id = p.protocolo_id" + onde
        + " ORDER BY p.codigo", args)
    for linha in linhas:
        linha["situacao_label"] = SITUACOES.get(linha["situacao"], linha["situacao"])
        linha["n_coletas"] = db.scalar(
            "SELECT COUNT(*) FROM coletas WHERE participante_id = ?", (linha["id"],)) or 0
        linha["idade"] = (_hoje().year - int(linha["ano_nascimento"])
                          if linha.get("ano_nascimento") else None)
    return linhas


# ----------------------------------------------------------------------
# A medida
# ----------------------------------------------------------------------
def registrar(db: Database, participante_id: int, instrumento_id: int,
              valor: float, momento_id: int | None = None,
              subescala: str | None = None, **extra: Any) -> dict:
    """Grava uma medida. Fora da faixa declarada, recusa.

    Um valor impossivel entra tao facil quanto um possivel -- 77 numa
    escala de 0 a 10 e um dedo escorregando no teclado --, e depois some
    dentro de uma media. O instrumento ja declara minimo e maximo; a
    recusa aqui e o unico lugar onde isso e barato de corrigir.
    """
    inst = db.dicts("SELECT * FROM instrumentos WHERE id = ?", (instrumento_id,))
    if not inst:
        raise ValueError("instrumento não existe")
    inst = inst[0]
    if not db.dicts("SELECT id FROM participantes WHERE id = ?", (participante_id,)):
        raise ValueError("participante não existe")
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError("valor precisa ser número") from None
    if inst["minimo"] is not None and numero < inst["minimo"]:
        raise ValueError("%s vai de %g a %g; %g está fora"
                         % (inst["nome"], inst["minimo"], inst["maximo"] or 0, numero))
    if inst["maximo"] is not None and numero > inst["maximo"]:
        raise ValueError("%s vai de %g a %g; %g está fora"
                         % (inst["nome"], inst["minimo"] or 0, inst["maximo"], numero))
    # A gravacao e explicita, e nao um upsert: a unicidade da medida mora
    # num indice sobre COALESCE(momento_id, -1) e COALESCE(subescala, ''),
    # porque em SQL NULL nao colide com NULL -- e um ON CONFLICT por nome
    # de coluna nao alcanca um indice de expressao. Procurar e depois
    # decidir entre UPDATE e INSERT faz a mesma coisa, e diz o que faz.
    quando = extra.get("coletado_em") or _hoje().isoformat()
    existente = db.dicts(
        "SELECT id FROM coletas"
        " WHERE participante_id = ? AND instrumento_id = ?"
        "   AND COALESCE(momento_id, -1) = COALESCE(?, -1)"
        "   AND COALESCE(subescala, '') = COALESCE(?, '')",
        (participante_id, instrumento_id, momento_id, subescala))
    if existente:
        ident = existente[0]["id"]
        db.execute(
            "UPDATE coletas SET valor = ?, coletado_em = ?, coletado_por = ?,"
            "       observacao = ?, updated_at = datetime('now') WHERE id = ?",
            (numero, quando, extra.get("coletado_por"), extra.get("observacao"), ident))
    else:
        cursor = db.execute(
            "INSERT INTO coletas (participante_id, instrumento_id, momento_id,"
            "                     subescala, valor, coletado_em, coletado_por, observacao)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (participante_id, instrumento_id, momento_id, subescala, numero,
             quando, extra.get("coletado_por"), extra.get("observacao")))
        ident = cursor.lastrowid
    db.conn.commit()
    return db.dicts("SELECT * FROM coletas WHERE id = ?", (ident,))[0]


# ----------------------------------------------------------------------
# Onde esta o buraco
# ----------------------------------------------------------------------
def matriz(db: Database, protocolo_id: int, instrumento_id: int | None = None) -> dict:
    """Participante x momento: o que ha, o que falta e o que atrasou.

    E a tela de trabalho da coleta. "Atrasado" so existe porque o momento
    declara `dias_apos` e `janela_dias` -- sem eles nao ha prazo, e sem
    prazo nao ha atraso: ha apenas o que ainda nao foi coletado, para
    sempre.
    """
    momentos = db.dicts(
        "SELECT * FROM momentos WHERE protocolo_id = ? ORDER BY ordem, id",
        (protocolo_id,))
    gente = participantes(db, protocolo_id)
    args: tuple = (protocolo_id,)
    filtro = ""
    if instrumento_id:
        filtro = " AND c.instrumento_id = ?"
        args = (protocolo_id, instrumento_id)
    feitas = db.dicts(
        "SELECT c.participante_id, c.momento_id, c.instrumento_id, c.valor, c.coletado_em"
        "  FROM coletas c JOIN participantes p ON p.id = c.participante_id"
        " WHERE p.protocolo_id = ?" + filtro, args)
    indice: dict[tuple, list] = {}
    for linha in feitas:
        indice.setdefault((linha["participante_id"], linha["momento_id"]), []).append(linha)

    hoje = _hoje()
    linhas, faltam, atrasadas, fora = [], 0, 0, 0
    for pessoa in gente:
        entrou = _data(pessoa.get("entrou_em"))
        celulas = []
        for momento in momentos:
            achadas = indice.get((pessoa["id"], momento["id"]), [])
            estado = "feita" if achadas else "falta"
            vence = None
            if entrou and momento.get("dias_apos") is not None:
                from datetime import timedelta
                vence = entrou + timedelta(
                    days=int(momento["dias_apos"]) + int(momento.get("janela_dias") or 0))
            if not achadas:
                # quem saiu do estudo nao esta atrasado: esta fora
                if pessoa["situacao"] != "ativo":
                    estado = "fora"
                    fora += 1
                elif vence and vence < hoje:
                    estado = "atrasada"
                    atrasadas += 1
                else:
                    faltam += 1
            celulas.append({
                "momento_id": momento["id"], "momento": momento["nome"],
                "estado": estado, "n": len(achadas),
                "vence_em": vence.isoformat() if vence else None,
            })
        linhas.append({"participante_id": pessoa["id"], "codigo": pessoa["codigo"],
                       "grupo": pessoa["grupo"], "situacao": pessoa["situacao"],
                       "situacao_label": pessoa["situacao_label"], "celulas": celulas})
    total = len(gente) * len(momentos)
    feitas_n = sum(1 for linha in linhas for c in linha["celulas"] if c["estado"] == "feita")
    return {
        "momentos": momentos, "linhas": linhas,
        "total_celulas": total, "feitas": feitas_n,
        # Os quatro estados somam o total. Sem `fora`, a composicao exibida
        # fechava em 38 de 42 e ninguem sabia onde estavam as outras quatro
        # -- eram as celulas de quem saiu do estudo.
        "faltam": faltam, "atrasadas": atrasadas, "fora": fora,
        "completude": round(100 * feitas_n / total, 1) if total else None,
    }


def aderencia(db: Database, protocolo_id: int) -> dict:
    """Quantos entraram, quantos seguem, quantos sairam e por que."""
    gente = participantes(db, protocolo_id)
    por_situacao: dict[str, int] = {}
    for pessoa in gente:
        por_situacao[pessoa["situacao"]] = por_situacao.get(pessoa["situacao"], 0) + 1
    saidas: dict[str, int] = {}
    for pessoa in gente:
        if pessoa["situacao"] != "ativo" and pessoa.get("motivo_saida"):
            saidas[pessoa["motivo_saida"]] = saidas.get(pessoa["motivo_saida"], 0) + 1
    total = len(gente)
    perdidos = sum(n for s, n in por_situacao.items() if s in ("desistiu", "perdido"))
    return {
        "total": total,
        "por_situacao": [{"situacao": s, "label": SITUACOES.get(s, s), "n": n}
                         for s, n in sorted(por_situacao.items(), key=lambda x: -x[1])],
        "motivos": [{"motivo": m, "n": n}
                    for m, n in sorted(saidas.items(), key=lambda x: -x[1])],
        "perda": round(100 * perdidos / total, 1) if total else None,
        "grupos": _contar(gente, "grupo"),
    }


def _contar(linhas: list[dict], campo: str) -> list[dict]:
    conta: dict[str, int] = {}
    for linha in linhas:
        chave = linha.get(campo) or "sem grupo"
        conta[chave] = conta.get(chave, 0) + 1
    return [{"chave": k, "n": v} for k, v in sorted(conta.items(), key=lambda x: -x[1])]


# ----------------------------------------------------------------------
# A analise
# ----------------------------------------------------------------------
def _resumo(valores: list[float]) -> dict:
    limpos = [float(v) for v in valores if v is not None]
    if not limpos:
        return {"n": 0, "media": None, "dp": None, "mediana": None,
                "minimo": None, "maximo": None}
    return {
        "n": len(limpos),
        "media": round(statistics.fmean(limpos), 3),
        "dp": round(statistics.stdev(limpos), 3) if len(limpos) > 1 else None,
        "mediana": round(statistics.median(limpos), 3),
        "minimo": min(limpos), "maximo": max(limpos),
    }


def efeito(antes: list[float], depois: list[float]) -> dict:
    """Tamanho de efeito entre dois momentos, com o desvio agrupado.

    Devolve `n` e `instavel` junto: o d de Cohen nao avisa sozinho que
    nasceu de seis pessoas, e um 0,82 calculado com seis nao e a mesma
    coisa que um 0,82 calculado com sessenta. Quem le a tela precisa
    receber as duas informacoes no mesmo lugar.
    """
    a, b = _resumo(antes), _resumo(depois)
    if a["n"] < 2 or b["n"] < 2 or a["dp"] is None or b["dp"] is None:
        return {"antes": a, "depois": b, "d": None, "instavel": True,
                "motivo": "gente de menos para calcular desvio"}
    agrupado = ((a["dp"] ** 2 + b["dp"] ** 2) / 2) ** 0.5
    if not agrupado:
        return {"antes": a, "depois": b, "d": None, "instavel": True,
                "motivo": "sem variação entre as medidas"}
    d = (b["media"] - a["media"]) / agrupado
    menor = min(a["n"], b["n"])
    return {
        "antes": a, "depois": b,
        "delta": round(b["media"] - a["media"], 3),
        "d": round(d, 3), "dp_agrupado": round(agrupado, 3),
        "instavel": menor < N_MINIMO_PARA_EFEITO,
        "motivo": ("calculado com %d participante(s) por momento -- "
                   "abaixo de %d o número é instável"
                   % (menor, N_MINIMO_PARA_EFEITO)) if menor < N_MINIMO_PARA_EFEITO else None,
    }


def analise(db: Database, protocolo_id: int, instrumento_id: int,
            subescala: str | None = None) -> dict:
    """Do primeiro ao ultimo momento, por grupo, com o efeito ao lado."""
    inst = db.dicts("SELECT * FROM instrumentos WHERE id = ?", (instrumento_id,))
    if not inst:
        raise ValueError("instrumento não existe")
    inst = inst[0]
    momentos = db.dicts(
        "SELECT * FROM momentos WHERE protocolo_id = ? ORDER BY ordem, id",
        (protocolo_id,))
    if len(momentos) < 2:
        return {"instrumento": inst, "momentos": momentos, "series": [],
                "aviso": "o protocolo precisa de pelo menos dois momentos declarados"}

    args: list = [protocolo_id, instrumento_id]
    filtro = ""
    if subescala:
        filtro = " AND c.subescala = ?"
        args.append(subescala)
    linhas = db.dicts(
        "SELECT c.valor, c.momento_id, p.grupo, p.id AS participante_id"
        "  FROM coletas c JOIN participantes p ON p.id = c.participante_id"
        " WHERE p.protocolo_id = ? AND c.instrumento_id = ?" + filtro, tuple(args))

    grupos = sorted({(linha["grupo"] or "sem grupo") for linha in linhas})
    series = []
    for grupo in grupos:
        do_grupo = [x for x in linhas if (x["grupo"] or "sem grupo") == grupo]
        pontos = []
        for momento in momentos:
            valores = [x["valor"] for x in do_grupo if x["momento_id"] == momento["id"]]
            pontos.append({"momento": momento["nome"], "momento_id": momento["id"],
                           **_resumo(valores)})
        primeiro = [x["valor"] for x in do_grupo if x["momento_id"] == momentos[0]["id"]]
        ultimo = [x["valor"] for x in do_grupo if x["momento_id"] == momentos[-1]["id"]]
        series.append({"grupo": grupo, "pontos": pontos,
                       "efeito": efeito(primeiro, ultimo)})
    return {"instrumento": inst, "momentos": momentos, "series": series,
            "direcao": DIRECOES.get(inst.get("direcao") or "", ""),
            "subescala": subescala}


# ----------------------------------------------------------------------
# O ano, e a saida
# ----------------------------------------------------------------------
def resumo_anual(db: Database, ano: int | None = None) -> dict:
    """O ano da bancada numa pagina: quem entrou, quem saiu, o que se mediu."""
    ano = int(ano or _hoje().year)
    inicio, fim = "%d-01-01" % ano, "%d-12-31" % ano
    entraram = db.scalar(
        "SELECT COUNT(*) FROM participantes WHERE entrou_em BETWEEN ? AND ?",
        (inicio, fim)) or 0
    sairam = db.dicts(
        "SELECT situacao, motivo_saida, COUNT(*) AS n FROM participantes"
        " WHERE saiu_em BETWEEN ? AND ? GROUP BY situacao, motivo_saida"
        " ORDER BY n DESC", (inicio, fim))
    medidas = db.scalar(
        "SELECT COUNT(*) FROM coletas WHERE coletado_em BETWEEN ? AND ?",
        (inicio, fim)) or 0
    por_instrumento = db.dicts(
        "SELECT i.nome, i.code, COUNT(*) AS n FROM coletas c"
        "  JOIN instrumentos i ON i.id = c.instrumento_id"
        " WHERE c.coletado_em BETWEEN ? AND ? GROUP BY i.id ORDER BY n DESC",
        (inicio, fim))
    por_mes = []
    for mes in range(1, 13):
        por_mes.append(db.scalar(
            "SELECT COUNT(*) FROM coletas WHERE coletado_em LIKE ?",
            ("%d-%02d-%%" % (ano, mes),)) or 0)
    ativos = db.scalar(
        "SELECT COUNT(*) FROM participantes WHERE situacao = 'ativo'") or 0
    return {
        "ano": ano, "entraram": entraram, "ativos": ativos,
        "sairam": sairam, "medidas": medidas,
        "por_instrumento": por_instrumento, "por_mes": por_mes,
        "protocolos": db.scalar("SELECT COUNT(*) FROM protocolos WHERE ativo = 1") or 0,
    }


def exportar_longo(db: Database, protocolo_id: int | None = None) -> list[dict]:
    """Uma linha por medida, em formato longo -- o que R, SPSS e jamovi leem.

    Formato longo e nao largo de proposito: largo (uma coluna por momento)
    quebra assim que o protocolo ganha um momento, e obriga a reescrever a
    analise. Longo cresce sem mudar de forma.

    Nao sai nome nenhum daqui porque nao ha nome nenhum no banco.
    """
    onde, args = "", ()
    if protocolo_id:
        onde, args = " WHERE p.protocolo_id = ?", (protocolo_id,)
    return db.dicts(
        "SELECT p.codigo AS participante, p.grupo, p.sexo, p.ano_nascimento,"
        "       p.situacao, pr.code AS protocolo,"
        "       i.code AS instrumento, i.nome AS instrumento_nome, i.unidade,"
        "       c.subescala, m.code AS momento, m.ordem AS momento_ordem,"
        "       c.valor, c.coletado_em"
        "  FROM coletas c"
        "  JOIN participantes p ON p.id = c.participante_id"
        "  JOIN instrumentos i ON i.id = c.instrumento_id"
        "  LEFT JOIN momentos m ON m.id = c.momento_id"
        "  LEFT JOIN protocolos pr ON pr.id = p.protocolo_id" + onde
        + " ORDER BY p.codigo, i.code, m.ordem", args)
