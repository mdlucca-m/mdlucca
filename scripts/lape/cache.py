"""Cache simples com TTL para evitar queries repetidas."""
from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_CACHE: dict[str, tuple[Any, float]] = {}
DEFAULT_TTL = 60


def limpar() -> None:
    """Limpa todo o cache."""
    _CACHE.clear()


def get(chave: str, ttl: int = DEFAULT_TTL) -> Any | None:
    """Recupera valor em cache se ainda válido."""
    if chave not in _CACHE:
        return None
    valor, timestamp = _CACHE[chave]
    if time.time() - timestamp > ttl:
        del _CACHE[chave]
        return None
    return valor


def set(chave: str, valor: Any) -> None:
    """Armazena valor em cache com timestamp."""
    _CACHE[chave] = (valor, time.time())


def computar(chave: str, fn: Callable[[], T], ttl: int = DEFAULT_TTL) -> T:
    """Se em cache, devolve; senão computa, cachea e devolve."""
    em_cache = get(chave, ttl)
    if em_cache is not None:
        return em_cache
    valor = fn()
    set(chave, valor)
    return valor
