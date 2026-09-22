"""Atualizar todos os acervos de uma vez, sem travar a tela.

Existe porque "atualizar tudo" e uma tarefa de dez minutos, e uma
requisicao de dez minutos nao chega ao fim: o navegador desiste, o tunel
corta, e quem apertou fica sem saber se o trabalho aconteceu ou nao. O
resultado pratico era pior do que um erro -- era apertar de novo, e
gastar a cota da base duas vezes pela mesma duvida.

Aqui a atualizacao roda ao lado, numa linha de execucao propria, e a
tela pergunta "como vai?" de tantos em tantos segundos. Tres
consequencias deliberadas:

  * so uma atualizacao por vez. Duas pessoas apertando ao mesmo tempo
    fariam as mesmas noventa buscas em paralelo, e a PubMed responde a
    isso com bloqueio -- nao com o dobro de artigos;
  * o estado vive na memoria do servidor. Se o servidor for reiniciado
    no meio, o acompanhamento se perde -- mas o TRABALHO nao: cada
    acervo grava o que achou ao terminar, e `rodada_em` em cada busca
    diz onde parou. Reiniciar e apertar de novo retoma de onde estava,
    porque busca que ja rodou hoje traz os mesmos artigos e eles nao
    entram duas vezes;
  * um acervo falhar nao cancela os outros. E a mesma escolha que
    `biblioteca.atualizar` faz entre as buscas, um nivel acima.
"""

from __future__ import annotations

import threading
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from .db import Database


class JaRodando(RuntimeError):
    """Uma atualizacao ja esta em andamento -- e duas seriam pior que uma."""


_lock = threading.Lock()
_estado: dict[str, Any] = {"rodando": False}


def estado() -> dict[str, Any]:
    """Uma copia do estado, para a tela mostrar.

    Copia porque quem le esta noutra linha de execucao: devolver o dicionario
    vivo faria a tela ler um numero que muda no meio da serializacao.
    """
    with _lock:
        copia = dict(_estado)
        copia["acervos"] = [dict(x) for x in _estado.get("acervos", [])]
        return copia


def _marcar(**campos: Any) -> None:
    with _lock:
        _estado.update(campos)


def iniciar(db_path: Path | str, codes: list[str], quem: str = "") -> dict[str, Any]:
    """Comeca a atualizacao dos acervos pedidos e volta na hora.

    Volta ANTES de terminar, de proposito: quem chama recebe o estado
    inicial e passa a acompanhar por `estado()`.
    """
    if not codes:
        raise ValueError("nenhum acervo para atualizar")
    with _lock:
        if _estado.get("rodando"):
            raise JaRodando(
                "uma atualização já está em andamento — espere ela terminar")
        _estado.clear()
        _estado.update({
            "rodando": True, "quem": quem,
            "comecou_em": datetime.now().isoformat(timespec="seconds"),
            "terminou_em": None, "pedidos": list(codes),
            "total": 0, "feitas": 0, "agora": None,
            "acervos": [], "novos": 0, "achados": 0, "erros": 0,
            "erro": None,
        })
    threading.Thread(target=_rodar, args=(Path(db_path), list(codes)),
                     name="lape-atualizar-tudo", daemon=True).start()
    return estado()


def _rodar(db_path: Path, codes: list[str]) -> None:
    from . import biblioteca

    db = None
    try:
        # Conexao propria: a do pedido web pertence a outra linha de
        # execucao, e o sqlite3 recusa uma conexao usada fora dela.
        db = Database(db_path)

        total = 0
        for code in codes:
            try:
                total += biblioteca.quantas_buscas(db, code)
            except ValueError:
                pass
        _marcar(total=total)

        def progresso(passo: dict[str, Any]) -> None:
            with _lock:
                _estado["feitas"] = _estado.get("feitas", 0) + 1
                _estado["agora"] = passo

        for code in codes:
            _marcar(agora={"acervo": code, "situacao": "comecando"})
            try:
                r = biblioteca.atualizar(db, code, progresso=progresso)
            except Exception as erro:  # noqa: BLE001 -- um acervo nao derruba os outros
                traceback.print_exc()
                with _lock:
                    _estado["acervos"].append(
                        {"code": code, "erro": f"{type(erro).__name__}: {erro}"})
                    _estado["erros"] = _estado.get("erros", 0) + 1
                continue
            with _lock:
                _estado["acervos"].append({
                    "code": code, "titulo": r["biblioteca"],
                    "buscas": r["buscas"], "achados": r["achados"],
                    "novos": r["novos"], "erros": r["erros"],
                    "sem_chave": r["sem_chave"],
                    "cortadas": r.get("cortadas", []),
                    "repetidos_juntados": r.get("repetidos_juntados", 0),
                })
                _estado["novos"] = _estado.get("novos", 0) + r["novos"]
                _estado["achados"] = _estado.get("achados", 0) + r["achados"]
                _estado["erros"] = _estado.get("erros", 0) + r["erros"]
    except Exception as erro:  # noqa: BLE001
        traceback.print_exc()
        _marcar(erro=f"{type(erro).__name__}: {erro}")
    finally:
        # O finally e o que impede a tela de ficar dizendo "atualizando"
        # para sempre depois de um erro que ninguem previu.
        if db is not None:
            db.close()
        _marcar(rodando=False, agora=None,
                terminou_em=datetime.now().isoformat(timespec="seconds"))
