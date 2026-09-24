"""A rotina que roda sozinha: producao nova das bases, citacoes e acervos.

A pergunta que motivou isto veio pelo WhatsApp: "novos artigos publicados,
adicionados no Lattes do professor, sao captados automaticamente, ou
vamos alimentando manual?". A resposta honesta era "manual": o botao
"Importar producao" existia, o de citacoes tambem, o de acervos tambem
-- e nada apertava nenhum deles sem uma pessoa na frente da tela.

O Lattes em si nao tem API e pede captcha; nao ha como le-lo por
programa. O que HA e a mesma producao nas bases publicas -- PubMed e
OpenAlex --, com DOI conferido, afiliacao e citacoes. E o que esta rotina
traz, para as pessoas declaradas em `ingest_autor.PESQUISADORES`.

Cinco passos, cada um com o seu intervalo, e cada um registrado em
`ingest_log` com `source = 'rotina'`:

  producao   traz os artigos novos das bases         (a cada dia)
  citacoes   atualiza o numero de citacoes por DOI   (a cada dia)
  acervos    roda as buscas de todos os acervos      (a cada semana)
  descobrir  procura producao nova na OpenAlex        (a cada dia)
             e so PROPOE -- fica em "Achados do rastreador" ate a
             coordenacao aceitar ou descartar; nada entra sozinho
  perfis     atualiza o indice h publico de quem      (a cada semana)
             nao tem numero conferido a mao

Fora daqui fica "Rodar curador": ele recarrega planilha e recalcula o que
ja esta gravado, nao busca nada de fora -- entao nao tem "vencido" e
continua botao.

O intervalo de cada passo e contado a partir da ULTIMA RODADA QUE DEU
CERTO, gravada no banco -- e nao da subida do servidor. Um computador
que reinicia todo dia nao pode reimportar tudo a cada subida, e um que
fica um mes desligado precisa rodar assim que volta.

Nada aqui derruba o servico: um passo que falha vira uma linha no
registro, com o erro, e o proximo passo roda do mesmo jeito. E nada aqui
apaga ou sobrescreve o que o laboratorio digitou -- sao as mesmas funcoes
dos botoes, que so preenchem lacuna.
"""
from __future__ import annotations

import os
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from .db import Database

# (passo, rotulo, intervalo em horas, o que faz)
PASSOS: tuple[tuple[str, str, float], ...] = (
    ("producao", "Produção nova das bases públicas", 24.0),
    ("citacoes", "Citações por DOI", 24.0),
    ("acervos", "Buscas dos acervos", 24.0 * 7),
    ("descobrir", "Descobertas (OpenAlex, para revisão)", 24.0),
    ("perfis", "Índice h dos perfis (OpenAlex)", 24.0 * 7),
)
# "Rodar curador" fica de fora de propósito: ele recarrega planilha e
# recalcula o banco a partir do que já está gravado -- não busca nada de
# fora, então não há "vencido" para ele. Continua um botão.
ROTULOS = {code: rotulo for code, rotulo, _ in PASSOS}
INTERVALO_H = {code: horas for code, _, horas in PASSOS}

# Quanto esperar depois da subida antes do primeiro passo, e de quanto em
# quanto tempo conferir se algum passo venceu. A espera inicial existe
# para o servidor responder a primeira pessoa antes de sair para a rede.
ATRASO_INICIAL_S = int(os.environ.get("LAPE_ROTINA_ATRASO_S", "120"))
CHECAGEM_S = int(os.environ.get("LAPE_ROTINA_CHECAGEM_S", "900"))

_lock = threading.Lock()
_estado: dict[str, Any] = {"rodando": False, "passo": None, "comecou_em": None}


def ligada() -> bool:
    return os.environ.get("LAPE_ROTINA", "1") != "0"


def _horas(code: str) -> float:
    return float(os.environ.get(f"LAPE_ROTINA_{code.upper()}_H", INTERVALO_H[code]))


def ultima(db: Database, code: str, so_ok: bool = True) -> dict[str, Any] | None:
    """A ultima rodada gravada do passo -- por padrao, a ultima que deu certo."""
    filtro = " AND status = 'ok'" if so_ok else ""
    achada = db.dicts(
        "SELECT run_at, status, message, rows_written FROM ingest_log"
        f" WHERE source = 'rotina' AND target = ?{filtro} ORDER BY id DESC LIMIT 1", (code,))
    return achada[0] if achada else None


def vencidos(db: Database, agora: datetime | None = None) -> list[str]:
    """Os passos cuja ultima rodada boa e mais velha do que o intervalo."""
    agora = agora or datetime.now()
    saida = []
    for code, _rotulo, _h in PASSOS:
        if _horas(code) <= 0:
            continue
        u = ultima(db, code)
        if u is None:
            saida.append(code)
            continue
        try:
            quando = datetime.fromisoformat(str(u["run_at"]).replace(" ", "T"))
        except ValueError:
            saida.append(code)
            continue
        if agora - quando >= timedelta(hours=_horas(code)):
            saida.append(code)
    return saida


# ----------------------------------------------------------------------
# os passos
# ----------------------------------------------------------------------
def _passo_producao(db: Database) -> tuple[int, str]:
    from . import hooks, ingest_autor

    resultado = ingest_autor.trazer_todos(db)
    novos = sum(p.get("gravado", {}).get("novos", 0) for p in resultado["pessoas"])
    erros = [p for p in resultado["pessoas"] if p.get("erro")]
    if erros and len(erros) == len(resultado["pessoas"]):
        raise RuntimeError("; ".join(f"{p['quem']}: {p['erro']}" for p in erros))
    if novos:
        hooks.emit(db, "producao.importada", entity="articles",
                   detail=f"{novos} artigo(s) novo(s) das bases públicas", actor="rotina")
    partes = [f"{novos} novo(s)"]
    partes += [f"{p['quem']}: {p['erro']}" for p in erros]
    return novos, "; ".join(partes)


def _passo_citacoes(db: Database) -> tuple[int, str]:
    from . import hooks, ingest_citations

    r = ingest_citations.update_citations(db, verbose=False)
    trazidos = int(r.get("scopus", 0)) + int(r.get("wos", 0)) + int(r.get("openalex", 0))
    if trazidos:
        hooks.emit(db, "citacoes.atualizadas", entity="articles",
                   detail=f"{trazidos} número(s) de citação atualizado(s)", actor="rotina")
    return trazidos, (f"{trazidos} número(s) trazido(s) de {r.get('consultados', 0)} artigo(s) com DOI"
                      + (f"; {r['erros']} erro(s)" if r.get("erros") else ""))


def _passo_acervos(db: Database) -> tuple[int, str]:
    from . import biblioteca, hooks

    codes = [b["code"] for b in db.dicts("SELECT code FROM biblioteca WHERE ativa = 1 ORDER BY code")]
    novos, erros = 0, []
    for code in codes:
        try:
            r = biblioteca.atualizar(db, code)
            novos += int(r.get("novos", 0) or 0)
        except Exception as erro:  # noqa: BLE001 -- um acervo nao derruba os outros
            erros.append(f"{code}: {type(erro).__name__}: {erro}")
    if novos:
        hooks.emit(db, "acervos.atualizados", entity="biblioteca",
                   detail=f"{novos} registro(s) novo(s) nos acervos", actor="rotina")
    if erros and len(erros) == len(codes):
        raise RuntimeError("; ".join(erros))
    return novos, f"{novos} novo(s) em {len(codes)} acervo(s)" + ("; " + "; ".join(erros) if erros else "")


def _passo_descobrir(db: Database) -> tuple[int, str]:
    """Procura producao nova na OpenAlex e so PROPOE -- nada entra em
    `articles` sozinho. Quem promove e a coordenacao, em "Achados do
    rastreador"; a rotina so evita que ninguem lembre de apertar o botao.
    """
    from .agents import tracker

    r = tracker.discover(db, verbose=False)
    mensagem = f"{r['new']} descoberta(s) de {r['authors']} pesquisador(es) consultados"
    if r.get("errors"):
        mensagem += f"; {len(r['errors'])} erro(s)"
    return r["new"], mensagem


def _passo_perfis(db: Database) -> tuple[int, str]:
    """Indice h publico (OpenAlex) de quem nao tem numero conferido a mao.

    So preenche lacuna: `profiles()` ja nunca sobrescreve o que a
    coordenacao declarou (ver `indice_h.declarar`).
    """
    from .agents import tracker

    r = tracker.profiles(db, verbose=False)
    mensagem = f"{r['updated']} indice(s) h atualizado(s)"
    if r.get("errors"):
        mensagem += f"; {len(r['errors'])} erro(s)"
    return r["updated"], mensagem


FAZ: dict[str, Callable[[Database], tuple[int, str]]] = {
    "producao": _passo_producao, "citacoes": _passo_citacoes, "acervos": _passo_acervos,
    "descobrir": _passo_descobrir, "perfis": _passo_perfis,
}


def rodar_passo(db: Database, code: str) -> dict[str, Any]:
    """Roda UM passo agora e grava o resultado, bom ou ruim."""
    if code not in FAZ:
        raise ValueError(f"passo desconhecido: {code}")
    with _lock:
        _estado.update({"rodando": True, "passo": code,
                        "comecou_em": datetime.now().isoformat(timespec="seconds")})
    try:
        n, mensagem = FAZ[code](db)
        db.log_ingest("rotina", target=code, rows_written=int(n), status="ok", message=mensagem)
        return {"passo": code, "status": "ok", "n": int(n), "mensagem": mensagem}
    except Exception as erro:  # noqa: BLE001 -- vira registro, nao derruba
        mensagem = f"{type(erro).__name__}: {erro}"
        db.log_ingest("rotina", target=code, status="erro", message=mensagem)
        return {"passo": code, "status": "erro", "n": 0, "mensagem": mensagem}
    finally:
        with _lock:
            _estado.update({"rodando": False, "passo": None})


def rodar_vencidos(db: Database, agora: datetime | None = None) -> list[dict[str, Any]]:
    return [rodar_passo(db, code) for code in vencidos(db, agora)]


def situacao(db: Database) -> dict[str, Any]:
    """O que a tela mostra: cada passo, quando rodou, o que trouxe, quando volta."""
    agora = datetime.now()
    passos = []
    for code, rotulo, _h in PASSOS:
        boa = ultima(db, code)
        qualquer = ultima(db, code, so_ok=False)
        proxima = None
        if boa:
            try:
                proxima = (datetime.fromisoformat(str(boa["run_at"]).replace(" ", "T"))
                           + timedelta(hours=_horas(code))).isoformat(timespec="minutes")
            except ValueError:
                proxima = None
        passos.append({
            "passo": code, "rotulo": rotulo, "intervalo_h": _horas(code),
            "ultima_boa": boa["run_at"] if boa else None,
            "trouxe": int(boa["rows_written"] or 0) if boa else None,
            "ultima": qualquer["run_at"] if qualquer else None,
            "status": qualquer["status"] if qualquer else "nunca rodou",
            "mensagem": qualquer["message"] if qualquer else None,
            "proxima": proxima if ligada() else None,
            "vencido": code in vencidos(db, agora),
        })
    with _lock:
        estado = dict(_estado)
    return {"ligada": ligada(), "checagem_s": CHECAGEM_S, "passos": passos, **estado}


# ----------------------------------------------------------------------
# a linha de execucao
# ----------------------------------------------------------------------
def agendar(db_path: Path | str) -> threading.Event:
    """Acorda de tempos em tempos e roda o que venceu. Igual ao backup."""
    parar = threading.Event()
    if not ligada():
        return parar

    def laco() -> None:
        if parar.wait(ATRASO_INICIAL_S):
            return
        while not parar.is_set():
            try:
                db = Database(db_path)
                try:
                    for feito in rodar_vencidos(db):
                        marca = "" if feito["status"] == "ok" else "! "
                        print(f"  {marca}rotina {feito['passo']}: {feito['mensagem']}")
                finally:
                    db.close()
            except Exception:  # noqa: BLE001 -- nunca derruba o servico
                traceback.print_exc()
            parar.wait(CHECAGEM_S)

    threading.Thread(target=laco, name="lape-rotina", daemon=True).start()
    return parar


def rodar_agora(db_path: Path | str, passos: list[str] | None = None) -> dict[str, Any]:
    """O botao: roda ao lado, e volta na hora. Um por vez."""
    with _lock:
        if _estado.get("rodando"):
            raise RuntimeError("a rotina já está rodando — espere ela terminar")
    pedidos = [p for p in (passos or [c for c, _, _ in PASSOS]) if p in FAZ]
    if not pedidos:
        raise ValueError("nenhum passo conhecido para rodar")

    def correr() -> None:
        db = Database(db_path)
        try:
            for code in pedidos:
                rodar_passo(db, code)
        finally:
            db.close()

    threading.Thread(target=correr, name="lape-rotina-agora", daemon=True).start()
    return {"iniciada": True, "passos": pedidos}
