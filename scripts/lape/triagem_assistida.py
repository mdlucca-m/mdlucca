"""O assistente da triagem: ordem da fila, sinais, criterios e regra de parada.

A triagem as cegas (`revisao.py`) decide QUEM VOTOU O QUE. Este modulo ajuda
cada pessoa a votar mais rapido e com mais informacao, sem tocar em nenhuma
das tres regras daquele modulo:

  1. **O assistente nunca decide.** Ele devolve uma SUGESTAO com o porque.
     Quem registra a decisao e a pessoa, pelo mesmo caminho de sempre
     (`revisao.decidir`). Nao existe "excluir em massa pelo modelo".
  2. **Nao ha vazamento entre revisores.** O modelo aprendido de cada pessoa
     usa so as decisoes DELA. O voto do colega continua invisivel ate haver
     conflito -- treinar com o voto alheio contaminaria o proprio.
  3. **Tudo e explicavel.** Cada sinal diz de onde veio (qual palavra, qual
     criterio). Uma estrela sem motivo nao ajuda ninguem a discordar dela.

O que o modulo entrega:

  * `perfil`            sinais do registro (desenho do estudo, n amostral,
                        resumo ausente...) por regra, em portugues e ingles;
  * `avaliar_criterios` checklist: cada criterio da revisao achado ou nao;
  * `fila_assistida`    a fila com relevancia prevista (1-5 estrelas) e
                        sugestao; pode vir ordenada do mais ao menos provavel
                        (triagem priorizada: os incluidos aparecem primeiro);
  * `painel`            qualidade do modelo, incluidos esperados ainda na
                        fila, recall estimado e a regra de parada;
  * `lote`              as sugestoes de maior confianca para a pessoa
                        confirmar de uma vez (cada uma vira decisao DELA).
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from collections import Counter
from typing import Any

from .db import Database
from .util import clean_text

GRUPOS = ("populacao", "intervencao", "comparador", "desfecho", "delineamento", "outro")
TONS = ("incluir", "excluir")

# Quantas decisoes proprias, e de cada lado, antes de o modelo aprendido
# entrar. Abaixo disso ele so decora o que a pessoa fez e erra com confianca.
MIN_TREINO = 15
MIN_POR_CLASSE = 3
# Decisoes necessarias para medir a qualidade (com poucas, o teste e ruido).
MIN_QUALIDADE = 20
# A partir de quantas decisoes o modelo pesa o maximo contra as regras.
TREINO_PESO_CHEIO = 80
# Estrelas: limites de probabilidade para 2, 3, 4 e 5.
LIMITES_ESTRELAS = (0.15, 0.35, 0.55, 0.75)
LIMITE_SUGERIR_INCLUIR = 0.80
LIMITE_SUGERIR_EXCLUIR = 0.15
MAX_CANDIDATAS = 4000

_PARADAS = frozenset("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob
sobre entre ate que se ao aos e ou mas como foi sao ser sua seu suas seus
the of and or in on at to for with without by from as is are was were be been
this that these those an a its their his her it we our study studies results
result methods method background objective objectives conclusion conclusions
using used use based
""".split())


# ----------------------------------------------------------------------
# Texto
# ----------------------------------------------------------------------
def _norm(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", base.lower()).strip()


def _tokens(texto: Any) -> list[str]:
    out = []
    for t in re.findall(r"[a-z][a-z0-9\-]{2,}", _norm(texto)):
        if t not in _PARADAS:
            out.append(t[:-1] if t.endswith("s") and len(t) > 4 else t)
    return out


def _tracos(ref: dict[str, Any]) -> list[str]:
    """Os atributos de uma referencia para o modelo: palavras do titulo
    (peso dobrado, por isso repetidas), do resumo e das palavras-chave."""
    titulo = _tokens(ref.get("title"))
    return titulo + titulo + _tokens(ref.get("abstract")) + _tokens(ref.get("keywords"))


def _termo_para_regex(termo: str) -> re.Pattern[str] | None:
    """`handebol*` casa o radical; sem asterisco casa a palavra/frase inteira."""
    t = _norm(termo)
    if not t:
        return None
    curinga = t.endswith("*")
    t = t.rstrip("*").strip()
    if not t:
        return None
    corpo = re.escape(t).replace(r"\ ", r"\s+")
    return re.compile(r"(?<![a-z0-9])" + corpo + ("" if curinga else r"(?![a-z0-9])"))


def _lista_de_termos(texto: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;\n|]", texto or "") if p.strip()]


# ----------------------------------------------------------------------
# Sinais automaticos do registro
# ----------------------------------------------------------------------
# (codigo, rotulo, tom, motivo sugerido, regex sobre texto normalizado)
_DESENHOS: tuple[tuple[str, str, str, str | None, str], ...] = (
    ("protocolo", "Protocolo de estudo", "alerta", "delineamento",
     r"\b(study protocol|protocolo de (estudo|pesquisa)|trial protocol|protocol for)\b"),
    ("editorial", "Editorial, carta ou comentário", "alerta", "delineamento",
     r"\b(editorial|letter to the editor|carta ao editor|commentary|comentario|comment on|reply to)\b"),
    ("caso", "Relato de caso", "alerta", "delineamento",
     r"\b(case report|relato de caso|case study of a single)\b"),
    ("erratum", "Errata, correção ou retratação", "alerta", "delineamento",
     r"\b(erratum|corrigendum|correction to|retraction|retracted|errata)\b"),
    ("congresso", "Resumo de congresso", "alerta", "resumo_congresso",
     r"\b(conference abstract|meeting abstract|poster presentation|anais|abstracts? of the)\b"),
    ("revisao_sistematica", "Revisão sistemática ou meta-análise", "info", "delineamento",
     r"\b(systematic review|meta-?analys[ie]s|revisao sistematica|meta-?analise)\b"),
    ("revisao_escopo", "Revisão de escopo ou narrativa", "info", "delineamento",
     r"\b(scoping review|narrative review|literature review|revisao (de escopo|narrativa|da literatura)|mapping review)\b"),
    ("ensaio", "Ensaio clínico randomizado", "ok", None,
     r"\b(randomi[sz]ed (controlled |clinical )?trial|ensaio (clinico )?(controlado )?randomizado|\brct\b)\b"),
    ("quase_exp", "Estudo quase-experimental", "ok", None,
     r"\b(quasi-?experiment\w*|quase-?experiment\w*|non-?randomi[sz]ed)\b"),
    ("coorte", "Coorte ou longitudinal", "ok", None,
     r"\b(cohort|coorte|longitudinal|prospective study|prospectivo)\b"),
    ("transversal", "Estudo transversal", "ok", None,
     r"\b(cross-?sectional|transversal)\b"),
    ("qualitativo", "Estudo qualitativo", "ok", None,
     r"\b(qualitative|qualitativ[oa]|interview|entrevista|focus group|grupo focal)\b"),
)
_N_AMOSTRA = (
    re.compile(r"\bn\s*=\s*(\d{1,6})\b"),
    re.compile(r"\b(\d{1,6})\s+(?:participants|athletes|players|patients|subjects|students|"
               r"children|adolescents|women|men|atletas|jogadores|jogadoras|participantes|"
               r"pacientes|estudantes|criancas|adolescentes)\b"),
)


def perfil(ref: dict[str, Any]) -> dict[str, Any]:
    """Sinais do registro. Cada um diz o que e, o tom e o motivo de exclusao
    que ele sugere (quando ha)."""
    texto = _norm(" ".join(str(ref.get(k) or "") for k in
                           ("title", "abstract", "pub_type", "keywords", "notes")))
    sinais: list[dict[str, Any]] = []
    for codigo, rotulo, tom, motivo, padrao in _DESENHOS:
        if re.search(padrao, texto):
            sinais.append({"codigo": codigo, "rotulo": rotulo, "tom": tom, "motivo": motivo})
    resumo = clean_text(ref.get("abstract")) or ""
    if not resumo:
        sinais.append({"codigo": "sem_resumo", "rotulo": "Sem resumo", "tom": "info", "motivo": None})
    elif len(resumo) < 300:
        sinais.append({"codigo": "resumo_curto", "rotulo": "Resumo curto", "tom": "info", "motivo": None})
    n = None
    for rx in _N_AMOSTRA:
        achado = rx.search(texto)
        if achado:
            n = int(achado.group(1))
            break
    if n is not None:
        sinais.append({"codigo": "n_amostra", "rotulo": f"n = {n}", "tom": "info", "motivo": None})
    return {"sinais": sinais, "n_amostra": n}


# ----------------------------------------------------------------------
# Criterios
# ----------------------------------------------------------------------
def criterios(db: Database, review_id: int) -> list[dict[str, Any]]:
    return db.dicts(
        "SELECT id, kind, grupo, label, keywords, motivo_code, seq"
        "  FROM review_criteria WHERE review_id = ? ORDER BY kind, seq, id", (review_id,))


def salvar_criterios(db: Database, review_id: int, lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Troca TODOS os criterios da revisao pelos enviados (a tela manda o conjunto)."""
    limpos = []
    for i, c in enumerate(lista or [], 1):
        label = clean_text(c.get("label"))
        kind = c.get("kind") if c.get("kind") in TONS else "incluir"
        if not label:
            continue
        limpos.append((kind, c.get("grupo") if c.get("grupo") in GRUPOS else "outro",
                       label, "; ".join(_lista_de_termos(str(c.get("keywords") or ""))),
                       clean_text(c.get("motivo_code")), i))
    db.execute("DELETE FROM review_criteria WHERE review_id = ?", (review_id,))
    for kind, grupo, label, kw, motivo, seq in limpos:
        db.execute(
            "INSERT OR IGNORE INTO review_criteria"
            " (review_id, kind, grupo, label, keywords, motivo_code, seq)"
            " VALUES (?, ?, ?, ?, ?, ?, ?)", (review_id, kind, grupo, label, kw, motivo, seq))
    db.conn.commit()
    return criterios(db, review_id)


def avaliar_criterios(ref: dict[str, Any], lista: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Cada criterio contra titulo + resumo + palavras-chave.

    `estado`: "sim" achou palavra do criterio; "nao" nao achou (e ha resumo
    para procurar); "sem_dado" nao achou mas tambem nao ha resumo -- ausencia
    de evidencia, nao evidencia de ausencia."""
    texto = _norm(" ".join(str(ref.get(k) or "") for k in ("title", "abstract", "keywords")))
    tem_resumo = bool(clean_text(ref.get("abstract")))
    saida = []
    for c in lista:
        achados = []
        for termo in _lista_de_termos(c.get("keywords") or ""):
            rx = _termo_para_regex(termo)
            if rx and rx.search(texto):
                achados.append(termo)
        estado = "sim" if achados else ("nao" if tem_resumo else "sem_dado")
        saida.append({"id": c.get("id"), "kind": c["kind"], "grupo": c.get("grupo"),
                      "label": c["label"], "estado": estado, "termos": achados[:4],
                      "motivo_code": c.get("motivo_code")})
    return saida


# ----------------------------------------------------------------------
# Relevancia prevista
# ----------------------------------------------------------------------
def _sigmoide(z: float) -> float:
    z = max(-30.0, min(30.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def _logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def _z_regras(ref: dict[str, Any], pf: dict[str, Any], crit: list[dict[str, Any]],
              termos: list[dict[str, Any]]) -> tuple[float, list[str]]:
    """Soma de evidencias das regras, em escala de log-odds, e o porque."""
    z, porque = 0.0, []
    por_grupo: dict[str, list[dict[str, Any]]] = {}
    for c in crit:
        if c["kind"] == "incluir":
            por_grupo.setdefault(c["grupo"], []).append(c)
        elif c["estado"] == "sim":
            z -= 1.6
            porque.append(f"critério de exclusão: {c['label']} ({', '.join(c['termos'][:2])})")
    for grupo, itens in por_grupo.items():
        if any(i["estado"] == "sim" for i in itens):
            z += 0.9
        elif all(i["estado"] == "nao" for i in itens):
            z -= 0.5
            porque.append(f"não achei {grupo}: {itens[0]['label']}")
    for s in pf["sinais"]:
        if s["tom"] == "alerta":
            z -= 1.2
            porque.append(s["rotulo"])
        elif s["codigo"].startswith("revisao_"):
            z -= 0.6
            porque.append(s["rotulo"])
        elif s["tom"] == "ok":
            z += 0.2
    texto = _norm(" ".join(str(ref.get(k) or "") for k in ("title", "abstract", "keywords")))
    bonus = 0.0
    for t in termos:
        rx = _termo_para_regex(t["term"])
        if rx and rx.search(texto):
            bonus += 0.4 if t["tone"] == "incluir" else -0.5
    z += max(-2.0, min(2.0, bonus))
    return z, porque


class Modelo:
    """Naive Bayes multinomial sobre as decisoes de UMA pessoa.

    O escore de um registro e o log-odds MEDIO por palavra (escalado), nao a
    soma: a soma cresce com o tamanho do resumo e faria todo resumo longo
    parecer certeza. Palavras que a pessoa nunca viu nao pesam."""

    def __init__(self) -> None:
        self.llr: dict[str, float] = {}
        self.n_inc = self.n_exc = 0

    def treinar(self, exemplos: list[tuple[list[str], bool]]) -> "Modelo":
        inc, exc = Counter(), Counter()
        self.n_inc = sum(1 for _, y in exemplos if y)
        self.n_exc = len(exemplos) - self.n_inc
        for toks, y in exemplos:
            (inc if y else exc).update(set(toks))
        vocab = set(inc) | set(exc)
        for t in vocab:
            if inc[t] + exc[t] < 2:
                continue
            p_i = (inc[t] + 1) / (self.n_inc + 2)
            p_e = (exc[t] + 1) / (self.n_exc + 2)
            self.llr[t] = math.log(p_i / p_e)
        return self

    def z(self, toks: list[str]) -> float | None:
        vistos = [self.llr[t] for t in set(toks) if t in self.llr]
        if len(vistos) < 3:
            return None
        return max(-4.0, min(4.0, sum(vistos) / len(vistos) * 8.0))


def _exemplos(db: Database, review_id: int, member_id: int) -> list[tuple[int, list[str], bool]]:
    """As decisoes da PROPRIA pessoa (talvez fica de fora: nao ensina nada)."""
    linhas = db.dicts(
        "SELECT r.id, r.title, r.abstract, r.keywords, s.decision"
        "  FROM screenings s JOIN refs r ON r.id = s.ref_id"
        " WHERE r.review_id = ? AND s.member_id = ? AND s.stage = 'titulo_resumo'"
        "   AND s.decision IN ('incluir', 'excluir') ORDER BY s.decided_at, s.id",
        (review_id, member_id))
    return [(l["id"], _tracos(l), l["decision"] == "incluir") for l in linhas]


def _auc(pares: list[tuple[float, bool]]) -> float | None:
    pos = [s for s, y in pares if y]
    neg = [s for s, y in pares if not y]
    if not pos or not neg:
        return None
    ganhos = sum(1.0 if p > n else 0.5 if p == n else 0.0 for p in pos for n in neg)
    return ganhos / (len(pos) * len(neg))


def _qualidade(exemplos: list[tuple[int, list[str], bool]], base_z: dict[int, float]) -> dict[str, Any] | None:
    """Treina em 3 de cada 4 decisoes e testa na quarta (a cada 4a, em cada classe):
    o numero que diz se a estrela merece confianca. Nao e "os 25% finais" de
    proposito -- na triagem priorizada o fim e so exclusao, e um teste sem
    nenhum incluido nao mede nada. So existe com decisoes suficientes."""
    if len(exemplos) < MIN_QUALIDADE:
        return None
    treino, teste = [], []
    for classe in (True, False):                 # a quarta de CADA classe, nao do conjunto
        do_lado = [e for e in exemplos if e[2] is classe]
        for i, e in enumerate(do_lado):
            (teste if i % 4 == 3 else treino).append(e)
    if sum(1 for _, _, y in treino if y) < MIN_POR_CLASSE or \
       sum(1 for _, _, y in treino if not y) < MIN_POR_CLASSE:
        return None
    m = Modelo().treinar([(t, y) for _, t, y in treino])
    pares = []
    for rid, toks, y in teste:
        z = m.z(toks)
        pares.append(((z or 0.0) + base_z.get(rid, 0.0), y))
    auc = _auc(pares)
    if auc is None:
        return None
    pos = sorted((s for s, y in pares if y))
    metade = sorted(s for s, _ in pares)[len(pares) // 2]
    recall_metade = (sum(1 for s in pos if s >= metade) / len(pos)) if pos else None
    return {"auc": round(auc, 3), "n_teste": len(teste),
            "recall_na_melhor_metade": None if recall_metade is None else round(recall_metade, 3)}


def _pendentes(db: Database, review_id: int, member_id: int, etapa: str, limite: int) -> list[dict[str, Any]]:
    return db.dicts(
        """
        SELECT r.id, r.title, r.abstract, r.authors, r.journal, r.year, r.doi, r.pmid,
               r.url, r.keywords, r.pub_type, r.language, r.notes
          FROM refs r
         WHERE r.review_id = ? AND r.duplicate_of IS NULL AND r.stage = ?
           AND NOT EXISTS (SELECT 1 FROM screenings s
                            WHERE s.ref_id = r.id AND s.member_id = ? AND s.stage = r.stage)
         ORDER BY r.id LIMIT ?
        """, (review_id, etapa, member_id, limite))


def _contexto(db: Database, review_id: int, member_id: int) -> dict[str, Any]:
    crit = criterios(db, review_id)
    termos = db.dicts("SELECT term, tone FROM review_terms WHERE review_id = ?", (review_id,))
    motivos = {m["code"]: m["id"] for m in db.dicts(
        "SELECT id, code FROM exclusion_reasons WHERE review_id = ?", (review_id,))}
    exemplos = _exemplos(db, review_id, member_id)
    n_inc = sum(1 for _, _, y in exemplos if y)
    n_exc = len(exemplos) - n_inc
    modelo = None
    if len(exemplos) >= MIN_TREINO and n_inc >= MIN_POR_CLASSE and n_exc >= MIN_POR_CLASSE:
        modelo = Modelo().treinar([(t, y) for _, t, y in exemplos])
    return {"criterios": crit, "termos": termos, "motivos": motivos, "exemplos": exemplos,
            "modelo": modelo, "n_inc": n_inc, "n_exc": n_exc}


def _avaliar(ref: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    pf = perfil(ref)
    crit = avaliar_criterios(ref, ctx["criterios"])
    z_reg, porque = _z_regras(ref, pf, crit, ctx["termos"])
    z_mod = ctx["modelo"].z(_tracos(ref)) if ctx["modelo"] else None
    peso = min(1.0, len(ctx["exemplos"]) / TREINO_PESO_CHEIO) if z_mod is not None else 0.0
    z = z_reg + (z_mod or 0.0) * (0.6 + 0.4 * peso)
    if ctx["modelo"] is not None and z_mod is None:
        # o modelo nao reconhece nenhuma palavra: cai na taxa de inclusao da
        # propria pessoa (5% numa triagem tipica), nao em 50%, que inflaria
        # o "incluidos esperados" da regra de parada
        total = ctx["n_inc"] + ctx["n_exc"]
        z += _logit(min(0.98, max(0.02, ctx["n_inc"] / total)))
    p = _sigmoide(z)
    estrelas = 1 + sum(1 for lim in LIMITES_ESTRELAS if p >= lim)
    if z_mod is not None and abs(z_mod) >= 1.0:
        porque.append("parecido com o que você " + ("incluiu" if z_mod > 0 else "excluiu"))
    return {"p": round(p, 3), "estrelas": estrelas, "sinais": pf["sinais"],
            "n_amostra": pf["n_amostra"], "criterios": crit, "porque": porque[:4],
            "sugestao": _sugestao(p, pf, crit, porque, ctx["motivos"]),
            "modelo_ativo": z_mod is not None}


def _sugestao(p: float, pf: dict[str, Any], crit: list[dict[str, Any]],
              porque: list[str], motivos: dict[str, int]) -> dict[str, Any] | None:
    if p >= LIMITE_SUGERIR_INCLUIR:
        return {"decisao": "incluir", "motivo_id": None, "motivo": None, "porque": porque[:3]}
    if p > LIMITE_SUGERIR_EXCLUIR:
        return None
    codigo = next((c["motivo_code"] for c in crit
                   if c["kind"] == "excluir" and c["estado"] == "sim" and c["motivo_code"]), None)
    codigo = codigo or next((s["motivo"] for s in pf["sinais"] if s["tom"] == "alerta" and s["motivo"]), None)
    if codigo is None:
        falta = next((c for c in crit if c["kind"] == "incluir" and c["estado"] == "nao"
                      and c["grupo"] in ("populacao", "intervencao", "comparador", "desfecho")), None)
        codigo = falta["grupo"] if falta else None
    return {"decisao": "excluir", "motivo_id": motivos.get(codigo) if codigo else None,
            "motivo": codigo, "porque": porque[:3]}


# ----------------------------------------------------------------------
# A fila
# ----------------------------------------------------------------------
def fila_assistida(db: Database, review_id: int, member_id: int, limite: int = 50,
                   etapa: str = "titulo_resumo", ordem: str = "relevancia") -> list[dict[str, Any]]:
    """O que falta a esta pessoa triar, com o assistente colado em cada item.

    `ordem="relevancia"`: do mais ao menos provavel de ser incluido (triagem
    priorizada). Qualquer outro valor mantem a ordem da importacao."""
    ctx = _contexto(db, review_id, member_id)
    candidatas = _pendentes(db, review_id, member_id, etapa, MAX_CANDIDATAS)
    for r in candidatas:
        r["assist"] = _avaliar(r, ctx)
    if ordem == "relevancia":
        candidatas.sort(key=lambda r: (-r["assist"]["p"], r["id"]))
    return candidatas[:limite]


def painel(db: Database, review_id: int, member_id: int, etapa: str = "titulo_resumo") -> dict[str, Any]:
    ctx = _contexto(db, review_id, member_id)
    pend = _pendentes(db, review_id, member_id, etapa, MAX_CANDIDATAS)
    ps = [_avaliar(r, ctx)["p"] for r in pend]
    qualidade = _qualidade_do(db, ctx)
    esperados = sum(ps)
    achados = ctx["n_inc"]
    recall = achados / (achados + esperados) if (achados + esperados) > 0 else None
    # sequencia de excluidos seguidos, do fim para tras
    seq = 0
    for _, _, y in reversed(ctx["exemplos"]):
        if y:
            break
        seq += 1
    total = len(pend) + len(ctx["exemplos"])
    minimo_seq = max(30, int(0.1 * total))
    pode_parar = bool(ps and ctx["modelo"] is not None and qualidade is not None
                      and (qualidade["auc"] or 0) >= 0.7 and seq >= minimo_seq and esperados < 1.0)
    faixas = [0, 0, 0, 0, 0]
    for p in ps:
        faixas[1 + sum(1 for lim in LIMITES_ESTRELAS if p >= lim) - 1] += 1
    tempos = db.dicts(
        "SELECT s.seconds FROM screenings s JOIN refs r ON r.id = s.ref_id"
        " WHERE r.review_id = ? AND s.member_id = ? AND s.seconds IS NOT NULL", (review_id, member_id))
    seg = sorted(t["seconds"] for t in tempos)
    mediana = seg[len(seg) // 2] if seg else None
    return {
        "treino": {"n": len(ctx["exemplos"]), "incluir": ctx["n_inc"], "excluir": ctx["n_exc"],
                   "modelo_ativo": ctx["modelo"] is not None,
                   "minimo": MIN_TREINO, "minimo_por_classe": MIN_POR_CLASSE},
        "qualidade": qualidade,
        "pendentes": len(pend),
        "faixas_estrelas": faixas,
        "incluidos_esperados": round(esperados, 1),
        "recall_estimado": None if recall is None else round(recall, 3),
        "excluidas_seguidas": seq,
        "regra_de_parada": {"pode_parar": pode_parar, "minimo_seguidas": minimo_seq,
                            "motivo": _porque_parar(pode_parar, ctx, qualidade, seq, minimo_seq, esperados)},
        "mediana_segundos": mediana,
        "alta_confianca": {"excluir": sum(1 for p in ps if p <= 0.08),
                           "incluir": sum(1 for p in ps if p >= 0.92)},
        "criterios": len(ctx["criterios"]),
    }


def _qualidade_do(db: Database, ctx: dict[str, Any]) -> dict[str, Any] | None:
    base_z: dict[int, float] = {}
    for rid, _, _ in ctx["exemplos"]:
        ref = db.dicts("SELECT id, title, abstract, keywords, pub_type, notes FROM refs WHERE id = ?", (rid,))[0]
        base_z[rid] = _z_regras(ref, perfil(ref), avaliar_criterios(ref, ctx["criterios"]), ctx["termos"])[0]
    return _qualidade(ctx["exemplos"], base_z)


def _porque_parar(ok: bool, ctx: dict[str, Any], q: dict[str, Any] | None,
                  seq: int, minimo: int, esperados: float) -> str:
    if ok:
        return (f"{seq} exclusões seguidas e menos de 1 incluído esperado na fila: dá para "
                "considerar parar (a decisão de parar é da equipe, e deve constar no relato).")
    if ctx["modelo"] is None:
        return f"Faltam decisões para o modelo aprender (mínimo {MIN_TREINO}, com {MIN_POR_CLASSE} de cada lado)."
    if q is None:
        return "Ainda não há decisões suficientes para medir a qualidade do modelo."
    if (q["auc"] or 0) < 0.7:
        return f"O modelo ainda acerta pouco (AUC {q['auc']}); não use a regra de parada."
    if seq < minimo:
        return f"Só {seq} exclusões seguidas; a regra pede {minimo}."
    return f"Ainda se esperam ~{esperados:.1f} incluídos na fila."


def lote(db: Database, review_id: int, member_id: int, tipo: str = "excluir",
         limite: int = 30, etapa: str = "titulo_resumo") -> list[dict[str, Any]]:
    """As sugestoes de maior confianca, para a pessoa CONFIRMAR em bloco.

    Nada e gravado aqui: a tela devolve as que a pessoa aceitou pelo mesmo
    POST de decisoes de sempre, e cada uma vira decisao DELA."""
    ctx = _contexto(db, review_id, member_id)
    if ctx["modelo"] is not None:
        # modelo aprendido so entra em lote se a qualidade medida for boa
        q = _qualidade_do(db, ctx)
        if q is None or (q["auc"] or 0) < 0.75:
            return []
    if tipo == "excluir":
        alvo = lambda p: p <= 0.08          # noqa: E731
        chave = lambda r: r["assist"]["p"]  # noqa: E731
    else:
        alvo = lambda p: p >= 0.92          # noqa: E731
        chave = lambda r: -r["assist"]["p"] # noqa: E731
    itens = []
    for r in _pendentes(db, review_id, member_id, etapa, MAX_CANDIDATAS):
        r["assist"] = _avaliar(r, ctx)
        if alvo(r["assist"]["p"]) and r["assist"]["sugestao"] and r["assist"]["sugestao"]["decisao"] == tipo:
            itens.append(r)
    itens.sort(key=chave)
    return [{"id": r["id"], "title": r["title"], "year": r["year"], "journal": r["journal"],
             "p": r["assist"]["p"], "porque": r["assist"]["porque"],
             "decisao": tipo, "motivo_id": r["assist"]["sugestao"]["motivo_id"],
             "motivo": r["assist"]["sugestao"]["motivo"]} for r in itens[:limite]]
