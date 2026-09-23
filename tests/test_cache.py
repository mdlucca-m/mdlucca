"""Testes para o módulo de cache."""
import time
import sys
sys.path.insert(0, "scripts")

from lape import cache


def test_cache_simples():
    """Armazena e recupera um valor em cache."""
    cache.set("chave1", {"valor": 42})
    assert cache.get("chave1", ttl=60) == {"valor": 42}


def test_cache_ttl_expirado():
    """Valor expira após TTL."""
    cache.set("chave2", "valor")
    # TTL de 0.01 segundos expira imediatamente
    time.sleep(0.02)
    assert cache.get("chave2", ttl=0.01) is None


def test_cache_computar():
    """Computa e cachea um valor."""
    count = [0]

    def computar():
        count[0] += 1
        return count[0]

    # Primeira chamada computa
    resultado1 = cache.computar("chave3", computar, ttl=60)
    assert resultado1 == 1

    # Segunda chamada vem do cache
    resultado2 = cache.computar("chave3", computar, ttl=60)
    assert resultado2 == 1  # Same, from cache
    assert count[0] == 1  # Só rodou uma vez


def test_cache_limpar():
    """Limpa todo o cache."""
    cache.set("a", 1)
    cache.set("b", 2)
    cache.limpar()
    assert cache.get("a", ttl=60) is None
    assert cache.get("b", ttl=60) is None
