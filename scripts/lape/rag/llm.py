"""Cliente Claude para os agentes.

Camada fina sobre o SDK oficial da Anthropic. Concentra num lugar so as
decisoes que os quatro agentes compartilham: modelo, esforco, pensamento
adaptativo, streaming e tratamento de erro. Nenhum agente fala com a API
diretamente.

Sem credencial, ``disponivel()`` devolve falso e os agentes explicam o que
falta em vez de estourar no meio do trabalho.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any, Iterable

from . import config

log = logging.getLogger("lape.rag.llm")


class LLMIndisponivel(RuntimeError):
    """Falta credencial ou o pacote anthropic nao esta instalado."""


@dataclass
class Resposta:
    texto: str
    modelo: str
    entrada: int = 0
    saida: int = 0
    cache_lido: int = 0
    parou_por: str = ""
    recusa: str | None = None

    @property
    def custo_estimado(self) -> float:
        """Estimativa em dolares para a familia Opus (5,00 / 25,00 por milhao)."""
        return (self.entrada * 5.0 + self.saida * 25.0) / 1_000_000


def disponivel() -> tuple[bool, str]:
    """Diz se da para chamar o modelo, e o que falta quando nao da."""
    try:
        import anthropic  # noqa: F401
    except ImportError:
        return False, ("o pacote anthropic nao esta instalado "
                       "(pip install anthropic)")
    if not (os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")
            or (os.path.expanduser("~/.config/anthropic") and
                os.path.isdir(os.path.expanduser("~/.config/anthropic")))):
        return False, ("nenhuma credencial encontrada: exporte ANTHROPIC_API_KEY "
                       "ou rode 'ant auth login'")
    return True, ""


_CLIENTE = None


def get_client():
    """Cliente unico, reutilizado entre chamadas."""
    global _CLIENTE
    if _CLIENTE is not None:
        return _CLIENTE
    ok, motivo = disponivel()
    if not ok:
        raise LLMIndisponivel(motivo)
    import anthropic
    _CLIENTE = anthropic.Anthropic()
    return _CLIENTE


def perguntar(system: str, mensagens: list[dict], *,
              modelo: str | None = None,
              max_tokens: int | None = None,
              esforco: str | None = None,
              cache_no_sistema: bool = True,
              stream: bool | None = None) -> Resposta:
    """Uma chamada ao modelo, com pensamento adaptativo.

    O prompt de sistema entra como bloco cacheavel: os agentes reusam o
    mesmo sistema em muitas chamadas, e o cache derruba o custo da parte
    estavel em cerca de 90%.
    """
    cliente = get_client()          # levanta LLMIndisponivel antes do import
    import anthropic

    modelo = modelo or config.LLM_MODEL
    max_tokens = max_tokens or config.LLM_MAX_TOKENS
    esforco = esforco or config.LLM_EFFORT
    usar_stream = (max_tokens > 16000) if stream is None else stream

    bloco_sistema: Any = (
        [{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}]
        if cache_no_sistema else system
    )
    argumentos = dict(
        model=modelo,
        max_tokens=max_tokens,
        system=bloco_sistema,
        messages=mensagens,
        thinking={"type": "adaptive"},
        output_config={"effort": esforco},
    )
    try:
        if usar_stream:
            with cliente.messages.stream(**argumentos) as fluxo:
                resposta = fluxo.get_final_message()
        else:
            resposta = cliente.messages.create(**argumentos)
    except anthropic.NotFoundError as exc:
        raise LLMIndisponivel(f"modelo '{modelo}' indisponivel: {exc}") from exc
    except anthropic.AuthenticationError as exc:
        raise LLMIndisponivel(f"credencial recusada: {exc}") from exc
    except anthropic.RateLimitError as exc:
        espera = exc.response.headers.get("retry-after", "?")
        raise RuntimeError(
            f"limite de requisicoes atingido; tente de novo em {espera}s") from exc
    except anthropic.APIStatusError as exc:
        raise RuntimeError(f"a API devolveu {exc.status_code}: {exc.message}") from exc
    except anthropic.APIConnectionError as exc:
        raise RuntimeError(f"falha de rede ao falar com a API: {exc}") from exc

    texto = "\n".join(b.text for b in resposta.content if b.type == "text")
    recusa = None
    if resposta.stop_reason == "refusal":
        detalhe = getattr(resposta, "stop_details", None)
        recusa = getattr(detalhe, "explanation", "") or "recusa sem detalhe"
    uso = resposta.usage
    return Resposta(
        texto=texto, modelo=resposta.model,
        entrada=getattr(uso, "input_tokens", 0),
        saida=getattr(uso, "output_tokens", 0),
        cache_lido=getattr(uso, "cache_read_input_tokens", 0) or 0,
        parou_por=resposta.stop_reason or "", recusa=recusa,
    )
