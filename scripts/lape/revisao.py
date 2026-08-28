"""A revisao sistematica: da busca nas bases ate o PRISMA.

O ciclo inteiro vive aqui. A busca em cada base traz um monte de
registros; os duplicados sao juntados; cada pessoa da equipe le titulo e
resumo e decide; a divergencia vai para arbitragem; o que sobrou vai
para texto completo. O PRISMA e a conta desse caminho.

Tres regras governam o modulo, e todas existem para que o numero final
seja defensavel numa banca:

  1. **A decisao da equipe nao e digitada.** Ela e derivada das decisoes
     individuais em `screenings`. Ninguem "marca como incluido": as
     pessoas decidem, e o consenso -- ou a falta dele -- e consequencia.
  2. **Duplicado nao e apagado.** Ele aponta para o que ficou. O PRISMA
     precisa do numero de removidos, e uniao errada tem de poder ser
     desfeita.
  3. **As cegas de verdade.** Enquanto a referencia nao tem o numero de
     triagens necessario, ninguem ve a decisao de ninguem. Nao e
     enfeite: ver o voto do outro contamina o proprio.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Iterable

from . import referencias
from .db import Database
from .util import clean_text, norm_doi, to_int

ETAPAS = ("titulo_resumo", "texto_completo", "incluido", "excluido")
DECISOES = ("incluir", "excluir", "talvez")

# Motivos de exclusao que servem para qualquer revisao. Sao so o ponto de
# partida: o PRISMA pede "excluidos, com motivos", e uma lista pronta faz
# a equipe usar motivo em vez de deixar em branco.
MOTIVOS_PADRAO: tuple[tuple[str, str], ...] = (
    ("populacao", "População não elegível"),
    ("intervencao", "Intervenção não elegível"),
    ("comparador", "Comparador não elegível"),
    ("desfecho", "Desfecho não avaliado"),
    ("delineamento", "Delineamento não elegível"),
    ("idioma", "Idioma fora dos critérios"),
    ("duplicado", "Registro duplicado"),
    ("sem_texto", "Texto completo não localizado"),
    ("resumo_congresso", "Apenas resumo de congresso"),
    ("outro", "Outro motivo"),
)


# ----------------------------------------------------------------------
# A revisao
# ----------------------------------------------------------------------
def criar(db: Database, code: str, title: str, **campos: Any) -> int:
    """Abre uma revisao, ja com a lista de motivos de exclusao."""
    dados = {"code": _slug(code), "title": clean_text(title) or code}
    for campo in ("question", "population", "intervention", "comparison", "outcome",
                  "study_designs", "protocol_url", "status"):
        if campos.get(campo) is not None:
            dados[campo] = clean_text(campos[campo])
    for campo in ("blind", "reviewers_needed", "research_line_id", "created_by"):
        if campos.get(campo) is not None:
            dados[campo] = campos[campo]
    review_id = db.upsert("reviews", dados, conflict=("code",))
    for seq, (codigo, rotulo) in enumerate(MOTIVOS_PADRAO, start=1):
        db.upsert("exclusion_reasons",
                  {"review_id": review_id, "code": codigo, "label": rotulo, "seq": seq},
                  conflict=("review_id", "code"))
    db.conn.commit()
    return review_id


def equipe(db: Database, review_id: int, member_id: int, role: str = "triador") -> None:
    """Poe (ou promove) alguem na equipe da revisao.

    `review_members` tem chave composta e nao tem coluna `id`, entao o
    upsert generico do banco -- que devolve o id da linha -- nao serve
    aqui.
    """
    db.execute(
        "INSERT INTO review_members (review_id, member_id, role) VALUES (?, ?, ?)"
        " ON CONFLICT (review_id, member_id) DO UPDATE SET role = excluded.role",
        (review_id, member_id, role))
    db.conn.commit()


# ----------------------------------------------------------------------
# Importacao
# ----------------------------------------------------------------------
def chaves_de_uniao(registro: dict[str, Any]) -> list[str]:
    """Todas as chaves pelas quais este registro pode ser o mesmo trabalho.

    Sao duas, e as duas valem ao mesmo tempo -- essa e a parte que quase
    todo mundo erra:

      `doi:10.1177/...`             o identificador, quando existe
      `tit:anxiety and mood|2021`   titulo normalizado mais ano

    Se a chave fosse uma so, com preferencia pelo DOI, o mesmo estudo
    vindo da Scopus (com DOI) e do Rayyan (sem DOI) passaria por dois
    trabalhos distintos -- e a equipe leria o mesmo resumo duas vezes,
    com o PRISMA jurando que sao dois. Foi exatamente o que aconteceu no
    primeiro teste com dados de verdade.

    O ano entra na chave de titulo de proposito: o resumo de congresso e
    o artigo saem com o mesmo titulo em anos diferentes, e junta-los
    esconderia um dos dois.
    """
    chaves = []
    doi = norm_doi(registro.get("doi"))
    if doi:
        chaves.append("doi:" + doi)
    titulo = _normalizar(registro.get("title"))
    if titulo:
        chaves.append(f"tit:{titulo[:120]}|{registro.get('year') or ''}")
    return chaves


def chave_de_uniao(registro: dict[str, Any]) -> str:
    """A chave principal, que fica gravada na referencia."""
    chaves = chaves_de_uniao(registro)
    return chaves[0] if chaves else ""


def importar(db: Database, review_id: int, texto: str, nome: str = "",
             base: str | None = None, query: str | None = None,
             searched_on: str | None = None,
             formato: str | None = None) -> dict[str, Any]:
    """Le um arquivo de referencias e grava o que ainda nao existe.

    Devolve o que aconteceu, em numeros: quantos vieram, quantos entraram,
    quantos ja estavam. Reimportar o mesmo arquivo nao duplica nada -- e
    isso importa, porque numa revisao a mesma busca e refeita varias
    vezes ate ficar boa.
    """
    registros = referencias.ler(texto, nome, formato)
    search_id = db.insert("review_searches", {
        "review_id": review_id,
        "base": clean_text(base) or _base_pelo_nome(nome),
        "query": clean_text(query),
        "searched_on": clean_text(searched_on),
        "file": clean_text(nome),
        "n_retrieved": len(registros),
    })

    # O indice guarda as duas chaves de cada referencia que ficou, para o
    # registro novo casar por qualquer uma delas.
    existentes: dict[str, int] = {}
    for row in db.dicts("SELECT id, doi, title, year FROM refs"
                        " WHERE review_id = ? AND duplicate_of IS NULL", (review_id,)):
        for chave in chaves_de_uniao(row):
            existentes.setdefault(chave, row["id"])

    novos, repetidos, com_rayyan = 0, 0, 0
    for registro in registros:
        chaves = chaves_de_uniao(registro)
        chave = chaves[0] if chaves else ""
        ja_visto = next((existentes[k] for k in chaves if k in existentes), None)
        campos = {
            "review_id": review_id, "search_id": search_id, "dedup_key": chave or None,
            "origem": clean_text(base) or _base_pelo_nome(nome),
        }
        for campo in ("title", "abstract", "authors", "journal", "volume", "issue",
                      "pages", "doi", "pmid", "issn", "language", "keywords", "url",
                      "pub_type"):
            campos[campo] = clean_text(registro.get(campo))
        campos["year"] = to_int(registro.get("year"))
        if ja_visto is not None:
            # duplicado entre bases: fica no banco, apontando para o que veio
            # primeiro, porque o PRISMA conta quantos foram removidos
            campos["duplicate_of"] = ja_visto
            campos["stage"] = "excluido"
            db.insert("refs", campos)
            repetidos += 1
            # A triagem que vem junto NAO se perde por o registro ser
            # repetido: e o mesmo trabalho, e a equipe ja o julgou. Ela vai
            # para a referencia que ficou. Sem isto, quem exportasse do
            # Rayyan junto com as buscas perderia justamente a triagem que
            # motivou a migracao -- e sem erro nenhum na tela.
            if registro.get("rayyan"):
                com_rayyan += 1
                _trazer_do_rayyan(db, review_id, ja_visto, registro["rayyan"])
            continue
        ref_id = db.insert("refs", campos)
        for k in chaves:
            existentes.setdefault(k, ref_id)
        novos += 1
        if registro.get("rayyan"):
            com_rayyan += 1
            _trazer_do_rayyan(db, review_id, ref_id, registro["rayyan"])
    db.conn.commit()
    return {"lidos": len(registros), "novos": novos, "duplicados": repetidos,
            "com_triagem_do_rayyan": com_rayyan, "search_id": search_id,
            "formato": formato or referencias.formato_de(nome, texto)}


def _trazer_do_rayyan(db: Database, review_id: int, ref_id: int,
                      achado: dict[str, Any]) -> None:
    """Traz para dentro a triagem que a equipe ja fez no Rayyan.

    E a unica coisa que realmente prende alguem a uma ferramenta: o
    trabalho ja feito. Cada pessoa vira (ou encontra) um integrante, e a
    decisao dela entra como decisao dela -- nao como decisao anonima do
    sistema.
    """
    motivo_id = None
    motivos = achado.get("motivos") or []
    if motivos:
        motivo_id = _motivo_por_rotulo(db, review_id, motivos[0])
    for quem, decisao in (achado.get("decisoes") or {}).items():
        member_id = db.member_id(quem)
        if not member_id or decisao not in DECISOES:
            continue
        equipe(db, review_id, member_id)
        db.upsert("screenings", {
            "ref_id": ref_id, "member_id": member_id, "stage": "titulo_resumo",
            "decision": decisao,
            "reason_id": motivo_id if decisao == "excluir" else None,
            "notes": "trazido do Rayyan",
        }, conflict=("ref_id", "member_id", "stage"))
    if achado.get("etiquetas"):
        db.execute("UPDATE refs SET notes = ? WHERE id = ?",
                   ("; ".join(achado["etiquetas"]), ref_id))
    consolidar(db, ref_id)


def _motivo_por_rotulo(db: Database, review_id: int, rotulo: str) -> int | None:
    texto = clean_text(rotulo)
    if not texto:
        return None
    achado = db.query(
        "SELECT id FROM exclusion_reasons WHERE review_id = ? AND lower(label) = lower(?)",
        (review_id, texto))
    if achado:
        return int(achado[0]["id"])
    proximo = int(db.scalar(
        "SELECT COALESCE(MAX(seq), 0) + 1 FROM exclusion_reasons WHERE review_id = ?",
        (review_id,)) or 1)
    return db.upsert("exclusion_reasons", {
        "review_id": review_id, "code": _slug(texto)[:40], "label": texto, "seq": proximo,
    }, conflict=("review_id", "code"))


# ----------------------------------------------------------------------
# Triagem
# ----------------------------------------------------------------------
def decidir(db: Database, ref_id: int, member_id: int, decision: str,
            reason_id: int | None = None, notes: str | None = None,
            seconds: float | None = None) -> dict[str, Any]:
    """Registra a decisao de UMA pessoa sobre UMA referencia."""
    if decision not in DECISOES:
        raise ValueError(f"decisão desconhecida: {decision}. Use {', '.join(DECISOES)}")
    linha = db.dicts("SELECT id, stage, review_id FROM refs WHERE id = ?", (ref_id,))
    if not linha:
        raise ValueError(f"referência {ref_id} não existe")
    etapa = linha[0]["stage"] if linha[0]["stage"] in ("titulo_resumo", "texto_completo") \
        else "titulo_resumo"
    db.upsert("screenings", {
        "ref_id": ref_id, "member_id": member_id, "stage": etapa,
        "decision": decision, "reason_id": reason_id,
        "notes": clean_text(notes), "seconds": seconds,
        "decided_at": db.scalar("SELECT datetime('now')"),
    }, conflict=("ref_id", "member_id", "stage"))
    resultado = consolidar(db, ref_id)
    db.conn.commit()
    return resultado


def consolidar(db: Database, ref_id: int) -> dict[str, Any]:
    """Deriva a decisao da equipe a partir das decisoes individuais.

    Nada de votar por maioria: numa revisao, incluir por engano custa uma
    leitura de texto completo, e excluir por engano custa um estudo. Por
    isso, com as opinioes divididas a referencia fica em conflito, e
    alguem arbitra -- e enquanto isso ela nao sai da fila.

    Uma pessoa so na equipe (`reviewers_needed = 1`) e caso legitimo: e a
    revisao de escopo feita por quem esta sozinho. Ai a decisao dela e a
    decisao, e nunca ha conflito.
    """
    linha = db.dicts(
        "SELECT r.id, r.stage, r.review_id, rv.reviewers_needed"
        "  FROM refs r JOIN reviews rv ON rv.id = r.review_id WHERE r.id = ?", (ref_id,))
    if not linha:
        return {}
    ref = linha[0]
    etapa = ref["stage"] if ref["stage"] in ("titulo_resumo", "texto_completo") \
        else "titulo_resumo"
    votos = db.dicts(
        "SELECT decision, reason_id FROM screenings WHERE ref_id = ? AND stage = ?",
        (ref_id, etapa))
    precisa = max(1, int(ref["reviewers_needed"] or 1))
    incluir = [v for v in votos if v["decision"] == "incluir"]
    excluir = [v for v in votos if v["decision"] == "excluir"]
    talvez = [v for v in votos if v["decision"] == "talvez"]

    estado = {"n_triagens": len(votos), "conflito": False,
              "decision": None, "faltam": max(0, precisa - len(votos))}
    if len(votos) < precisa:
        _gravar_decisao(db, ref_id, None, None)
        return estado
    if incluir and excluir:
        estado["conflito"] = True
        _gravar_decisao(db, ref_id, None, None)
        return estado
    if incluir or talvez:
        # "talvez" de todo mundo sobe para texto completo: na duvida, le-se
        estado["decision"] = "incluir"
        _gravar_decisao(db, ref_id, "incluir", None)
    else:
        estado["decision"] = "excluir"
        motivo = next((v["reason_id"] for v in excluir if v["reason_id"]), None)
        _gravar_decisao(db, ref_id, "excluir", motivo)
    return estado


def _gravar_decisao(db: Database, ref_id: int, decision: str | None,
                    reason_id: int | None) -> None:
    db.execute(
        "UPDATE refs SET decision = ?, reason_id = ?,"
        "       decided_at = CASE WHEN ? IS NULL THEN NULL ELSE datetime('now') END,"
        "       updated_at = datetime('now')"
        " WHERE id = ?", (decision, reason_id, decision, ref_id))


def avancar_etapa(db: Database, review_id: int) -> dict[str, int]:
    """Leva para texto completo o que a triagem de titulo e resumo incluiu.

    E um passo explicito, e nao automatico a cada decisao: a equipe fecha a
    triagem, confere o numero, e so entao abre a proxima etapa. Fazer isso
    sozinho embaralharia as duas fases no meio do trabalho.
    """
    sobem = db.dicts(
        "SELECT id FROM refs WHERE review_id = ? AND stage = 'titulo_resumo'"
        "   AND decision = 'incluir' AND duplicate_of IS NULL", (review_id,))
    for ref in sobem:
        db.execute(
            "UPDATE refs SET stage = 'texto_completo', decision = NULL, reason_id = NULL,"
            "       decided_at = NULL, updated_at = datetime('now') WHERE id = ?",
            (ref["id"],))
    descem = db.dicts(
        "SELECT id FROM refs WHERE review_id = ? AND stage = 'titulo_resumo'"
        "   AND decision = 'excluir' AND duplicate_of IS NULL", (review_id,))
    db.conn.commit()
    return {"para_texto_completo": len(sobem), "excluidos_na_triagem": len(descem)}


def fechar_texto_completo(db: Database, review_id: int) -> dict[str, int]:
    """Fecha a leitura de texto completo: o que foi incluido vira incluido."""
    incluidos = db.dicts(
        "SELECT id FROM refs WHERE review_id = ? AND stage = 'texto_completo'"
        "   AND decision = 'incluir' AND duplicate_of IS NULL", (review_id,))
    for ref in incluidos:
        db.execute("UPDATE refs SET stage = 'incluido', updated_at = datetime('now')"
                   " WHERE id = ?", (ref["id"],))
    db.conn.commit()
    return {"incluidos": len(incluidos)}


# ----------------------------------------------------------------------
# Fila e conflitos
# ----------------------------------------------------------------------
def fila(db: Database, review_id: int, member_id: int, limite: int = 50,
         etapa: str = "titulo_resumo") -> list[dict[str, Any]]:
    """O que falta esta pessoa triar, na ordem em que vai aparecer.

    A referencia sai da fila dela assim que ela decide -- mesmo que a
    revisao ainda espere a decisao de outra pessoa. Triagem as cegas
    significa exatamente isto: cada um anda no seu ritmo, sem ver o
    resto.
    """
    return db.dicts(
        """
        SELECT r.id, r.title, r.abstract, r.authors, r.journal, r.year, r.doi, r.pmid,
               r.url, r.keywords, r.pub_type, r.language, r.notes
          FROM refs r
         WHERE r.review_id = ? AND r.duplicate_of IS NULL AND r.stage = ?
           AND NOT EXISTS (SELECT 1 FROM screenings s
                            WHERE s.ref_id = r.id AND s.member_id = ? AND s.stage = r.stage)
         ORDER BY r.id
         LIMIT ?
        """, (review_id, etapa, member_id, limite))


def conflitos(db: Database, review_id: int,
              etapa: str = "titulo_resumo") -> list[dict[str, Any]]:
    """Onde a equipe divergiu. Aqui, e so aqui, os votos aparecem com nome."""
    linhas = db.dicts(
        """
        SELECT r.id, r.title, r.abstract, r.journal, r.year, r.doi, r.url
          FROM v_refs r
         WHERE r.review_id = ? AND r.duplicate_of IS NULL AND r.stage = ?
           AND r.n_incluir > 0 AND r.n_excluir > 0
         ORDER BY r.id
        """, (review_id, etapa))
    for linha in linhas:
        linha["votos"] = db.dicts(
            "SELECT m.full_name AS quem, s.decision, s.notes, x.label AS motivo"
            "  FROM screenings s JOIN members m ON m.id = s.member_id"
            "  LEFT JOIN exclusion_reasons x ON x.id = s.reason_id"
            " WHERE s.ref_id = ? AND s.stage = ? ORDER BY s.decided_at",
            (linha["id"], etapa))
    return linhas


def arbitrar(db: Database, ref_id: int, member_id: int, decision: str,
             reason_id: int | None = None, notes: str | None = None) -> dict[str, Any]:
    """A palavra final de quem arbitra, por cima do empate.

    Nao apaga o voto de ninguem: a divergencia fica registrada, que e o
    que permite calcular a concordancia entre avaliadores depois.
    """
    if decision not in ("incluir", "excluir"):
        raise ValueError("a arbitragem decide incluir ou excluir")
    linha = db.dicts("SELECT stage FROM refs WHERE id = ?", (ref_id,))
    if not linha:
        raise ValueError(f"referência {ref_id} não existe")
    etapa = linha[0]["stage"]
    db.upsert("screenings", {
        "ref_id": ref_id, "member_id": member_id, "stage": etapa, "decision": decision,
        "reason_id": reason_id, "notes": clean_text(notes) or "arbitragem",
    }, conflict=("ref_id", "member_id", "stage"))
    _gravar_decisao(db, ref_id, decision, reason_id)
    db.conn.commit()
    return {"decision": decision, "arbitrada": True}


# ----------------------------------------------------------------------
# Numeros
# ----------------------------------------------------------------------
def prisma(db: Database, review_id: int) -> dict[str, Any]:
    """Os numeros do fluxograma, contados do banco -- nenhum digitado."""
    linhas = db.dicts("SELECT * FROM v_prisma WHERE review_id = ?", (review_id,))
    if not linhas:
        return {}
    dados = dict(linhas[0])
    dados["motivos"] = db.dicts(
        "SELECT x.label AS motivo, COUNT(*) AS n"
        "  FROM refs r JOIN exclusion_reasons x ON x.id = r.reason_id"
        " WHERE r.review_id = ? AND r.decision = 'excluir' AND r.duplicate_of IS NULL"
        " GROUP BY x.label ORDER BY n DESC", (review_id,))
    dados["por_base"] = db.dicts(
        "SELECT COALESCE(origem, 'não informada') AS base, COUNT(*) AS n,"
        "       SUM(CASE WHEN duplicate_of IS NOT NULL THEN 1 ELSE 0 END) AS duplicados"
        "  FROM refs WHERE review_id = ? GROUP BY 1 ORDER BY n DESC", (review_id,))
    return dados


def andamento(db: Database, review_id: int) -> list[dict[str, Any]]:
    """Quanto cada pessoa ja triou, e em quanto tempo."""
    return db.dicts(
        """
        SELECT m.id AS member_id, m.full_name AS quem, s.stage,
               COUNT(*) AS triadas,
               SUM(CASE WHEN s.decision = 'incluir' THEN 1 ELSE 0 END) AS incluiu,
               SUM(CASE WHEN s.decision = 'excluir' THEN 1 ELSE 0 END) AS excluiu,
               SUM(CASE WHEN s.decision = 'talvez'  THEN 1 ELSE 0 END) AS em_duvida,
               ROUND(AVG(s.seconds), 1) AS segundos_por_referencia
          FROM screenings s
          JOIN members m ON m.id = s.member_id
          JOIN refs r ON r.id = s.ref_id
         WHERE r.review_id = ?
         GROUP BY m.id, s.stage
         ORDER BY triadas DESC
        """, (review_id,))


def concordancia(db: Database, review_id: int, a: int, b: int,
                 etapa: str = "titulo_resumo") -> dict[str, Any]:
    """Kappa de Cohen entre duas pessoas.

    A concordancia bruta engana: se as duas excluem 95% de tudo, elas
    concordam em 95% por acaso. O kappa desconta esse acaso, e e o numero
    que a revista pede.
    """
    pares = db.dicts(
        """
        SELECT sa.decision AS a, sb.decision AS b
          FROM screenings sa
          JOIN screenings sb ON sb.ref_id = sa.ref_id AND sb.stage = sa.stage
          JOIN refs r ON r.id = sa.ref_id
         WHERE r.review_id = ? AND sa.stage = ? AND sa.member_id = ? AND sb.member_id = ?
        """, (review_id, etapa, a, b))
    n = len(pares)
    if n == 0:
        return {"n": 0, "concordancia": None, "kappa": None,
                "leitura": "ainda não há referência triada pelas duas pessoas"}
    iguais = sum(1 for p in pares if p["a"] == p["b"])
    po = iguais / n
    categorias = set(DECISOES)
    pe = sum((sum(1 for p in pares if p["a"] == c) / n)
             * (sum(1 for p in pares if p["b"] == c) / n) for c in categorias)
    kappa = None if pe >= 1 else round((po - pe) / (1 - pe), 3)
    return {"n": n, "concordancia": round(po, 3), "kappa": kappa,
            "leitura": _ler_kappa(kappa)}


def _ler_kappa(kappa: float | None) -> str:
    """A escala de Landis e Koch, que e a que as revistas citam."""
    if kappa is None:
        return "sem variação suficiente para calcular"
    if kappa < 0:
        return "pior que o acaso"
    if kappa < 0.21:
        return "leve"
    if kappa < 0.41:
        return "razoável"
    if kappa < 0.61:
        return "moderada"
    if kappa < 0.81:
        return "substancial"
    return "quase perfeita"


# ----------------------------------------------------------------------
def _normalizar(texto: Any) -> str:
    """Titulo sem acento, sem pontuacao e sem espaco sobrando."""
    limpo = clean_text(texto)
    if not limpo:
        return ""
    sem_acento = "".join(c for c in unicodedata.normalize("NFKD", limpo)
                         if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


def _slug(texto: Any) -> str:
    base = _normalizar(texto).replace(" ", "-")
    return base or "revisao"


def _base_pelo_nome(nome: str) -> str:
    """Adivinha a base pelo nome do arquivo -- 'scopus.ris' e da Scopus."""
    chave = _normalizar(nome)
    for base, marcas in (("PubMed", ("pubmed", "medline", "nbib")),
                         ("Scopus", ("scopus",)),
                         ("Web of Science", ("wos", "web of science", "webofscience", "savedrecs")),
                         ("Embase", ("embase",)),
                         ("SciELO", ("scielo",)),
                         ("Cochrane", ("cochrane", "central")),
                         ("LILACS", ("lilacs", "bvs")),
                         ("Rayyan", ("rayyan",))):
        if any(marca in chave for marca in marcas):
            return base
    return "não informada"
