"""Geracao de vetores.

Quatro backends atras da mesma interface. A escolha automatica segue a
ordem: Voyage, OpenAI, modelo local, hash. O ultimo nao e semantico e
existe para que o sistema continue de pe sem chave e sem internet — ele
avisa de si mesmo em todo lugar onde aparece.

    >>> emb = get_embedder()
    >>> vetores = emb.embed_documents(["texto um", "texto dois"])
    >>> vetores.shape
    (2, 1024)

Todo vetor sai normalizado em L2, de modo que a similaridade do cosseno
seja um produto escalar simples no armazenamento.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import dataclass

import numpy as np

from . import config

log = logging.getLogger("lape.rag.embed")

VOYAGE_URL = "https://api.voyageai.com/v1/embeddings"
OPENAI_URL = "https://api.openai.com/v1/embeddings"


class EmbeddingError(RuntimeError):
    """Falha ao gerar vetores."""


@dataclass
class Embedder:
    """Interface comum. Subclasses implementam ``_encode``."""

    model: str
    dim: int
    semantic: bool = True

    def _encode(self, texts: list[str], kind: str) -> np.ndarray:
        raise NotImplementedError

    def embed_documents(self, texts: list[str]) -> np.ndarray:
        return self._run(texts, "document")

    def embed_query(self, text: str) -> np.ndarray:
        return self._run([text], "query")[0]

    def _run(self, texts: list[str], kind: str) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        saida = []
        for i in range(0, len(texts), config.EMBED_BATCH):
            lote = texts[i:i + config.EMBED_BATCH]
            saida.append(self._encode(lote, kind))
        vetores = np.vstack(saida).astype(np.float32)
        return normalizar(vetores)


def normalizar(v: np.ndarray) -> np.ndarray:
    normas = np.linalg.norm(v, axis=-1, keepdims=True)
    normas[normas == 0] = 1.0
    return (v / normas).astype(np.float32)


# ------------------------------------------------------------------ Voyage
class VoyageEmbedder(Embedder):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        super().__init__(model=model or config.DEFAULT_MODELS["voyage"], dim=1024)
        self.api_key = api_key or config.VOYAGE_API_KEY
        if not self.api_key:
            raise EmbeddingError("VOYAGE_API_KEY nao definida")

    def _encode(self, texts: list[str], kind: str) -> np.ndarray:
        import requests

        corpo = {
            "input": texts,
            "model": self.model,
            "input_type": "query" if kind == "query" else "document",
        }
        dados = _post_json(requests, VOYAGE_URL, corpo,
                           {"Authorization": f"Bearer {self.api_key}"})
        vetores = [item["embedding"] for item in sorted(dados["data"],
                                                        key=lambda d: d["index"])]
        arr = np.asarray(vetores, dtype=np.float32)
        self.dim = arr.shape[1]
        return arr


# ------------------------------------------------------------------ OpenAI
class OpenAIEmbedder(Embedder):
    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        super().__init__(model=model or config.DEFAULT_MODELS["openai"], dim=1536)
        self.api_key = api_key or config.OPENAI_API_KEY
        if not self.api_key:
            raise EmbeddingError("OPENAI_API_KEY nao definida")

    def _encode(self, texts: list[str], kind: str) -> np.ndarray:
        import requests

        dados = _post_json(requests, OPENAI_URL,
                           {"input": texts, "model": self.model},
                           {"Authorization": f"Bearer {self.api_key}"})
        vetores = [item["embedding"] for item in sorted(dados["data"],
                                                        key=lambda d: d["index"])]
        arr = np.asarray(vetores, dtype=np.float32)
        self.dim = arr.shape[1]
        return arr


def _post_json(requests, url: str, corpo: dict, headers: dict,
               tentativas: int = 4) -> dict:
    """POST com repeticao exponencial nos erros que valem repetir."""
    headers = {"Content-Type": "application/json", **headers}
    ultima: Exception | None = None
    for tentativa in range(tentativas):
        try:
            resposta = requests.post(url, json=corpo, headers=headers,
                                     timeout=config.EMBED_TIMEOUT)
        except requests.RequestException as exc:
            ultima = exc
        else:
            if resposta.status_code == 200:
                return resposta.json()
            if resposta.status_code in (408, 409, 429) or resposta.status_code >= 500:
                ultima = EmbeddingError(
                    f"{resposta.status_code}: {resposta.text[:200]}")
            else:
                raise EmbeddingError(
                    f"{url} devolveu {resposta.status_code}: {resposta.text[:300]}")
        espera = min(2 ** tentativa, 20)
        log.warning("embeddings: tentativa %d falhou (%s); nova tentativa em %ds",
                    tentativa + 1, ultima, espera)
        time.sleep(espera)
    raise EmbeddingError(f"{url} falhou apos {tentativas} tentativas: {ultima}")


# ------------------------------------------------------------------- local
class LocalEmbedder(Embedder):
    """Modelo local via sentence-transformers. Roda sem internet."""

    def __init__(self, model: str | None = None) -> None:
        nome = model or config.DEFAULT_MODELS["local"]
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise EmbeddingError(
                "backend local exige sentence-transformers "
                "(pip install sentence-transformers)"
            ) from exc
        self._modelo = SentenceTransformer(nome)
        super().__init__(model=nome,
                         dim=int(self._modelo.get_sentence_embedding_dimension()))

    def _encode(self, texts: list[str], kind: str) -> np.ndarray:
        return np.asarray(
            self._modelo.encode(texts, batch_size=min(32, config.EMBED_BATCH),
                                show_progress_bar=False, convert_to_numpy=True),
            dtype=np.float32)


# -------------------------------------------------------------------- hash
class HashEmbedder(Embedder):
    """Ultimo recurso: projecao deterministica por hashing de n-gramas.

    NAO e busca semantica. Ele encontra sobreposicao de forma, nao de
    sentido: nao liga "sono" a "sonolencia diurna" nem "vigor" a "energia".
    Existe para que a indexacao, os testes e a busca lexica funcionem sem
    chave e sem internet, e para que a troca por um backend de verdade nao
    exija reescrever nada.
    """

    def __init__(self, dim: int = 1024) -> None:
        super().__init__(model=f"hash-{dim}", dim=dim, semantic=False)

    @staticmethod
    def _termos(texto: str) -> list[str]:
        texto = texto.lower()
        palavras = re.findall(r"[0-9a-zà-öø-ÿ]{2,}", texto)
        termos = list(palavras)
        termos += [f"{a}_{b}" for a, b in zip(palavras, palavras[1:])]
        for palavra in palavras:
            if len(palavra) > 5:
                termos += [palavra[i:i + 4] for i in range(len(palavra) - 3)]
        return termos

    def _encode(self, texts: list[str], kind: str) -> np.ndarray:
        saida = np.zeros((len(texts), self.dim), dtype=np.float32)
        for linha, texto in enumerate(texts):
            for termo in self._termos(texto):
                digest = hashlib.blake2b(termo.encode("utf-8"), digest_size=8).digest()
                bruto = int.from_bytes(digest, "big")
                idx = bruto % self.dim
                sinal = 1.0 if (bruto >> 63) & 1 else -1.0
                saida[linha, idx] += sinal
        return saida


# ------------------------------------------------------------------ escolha
_CACHE: dict[str, Embedder] = {}


def get_embedder(backend: str | None = None, model: str | None = None,
                 use_cache: bool = True) -> Embedder:
    """Devolve o embedder configurado, com queda automatica.

    Em ``auto``, tenta Voyage, depois OpenAI, depois o modelo local e por
    fim o hash. Qualquer backend nomeado explicitamente falha alto: quem
    pediu Voyage precisa saber que Voyage nao subiu.
    """
    escolhido = (backend or config.EMBED_BACKEND or "auto").lower()
    chave = f"{escolhido}:{model or config.EMBED_MODEL}"
    if use_cache and chave in _CACHE:
        return _CACHE[chave]

    nome = model or config.EMBED_MODEL or None
    if escolhido == "auto":
        emb = _auto(nome)
    elif escolhido == "voyage":
        emb = VoyageEmbedder(nome)
    elif escolhido == "openai":
        emb = OpenAIEmbedder(nome)
    elif escolhido == "local":
        emb = LocalEmbedder(nome)
    elif escolhido == "hash":
        emb = HashEmbedder()
    else:
        raise EmbeddingError(
            f"backend '{escolhido}' desconhecido; use voyage, openai, local ou hash")
    if use_cache:
        _CACHE[chave] = emb
    return emb


def _auto(nome: str | None) -> Embedder:
    for construtor, rotulo in ((lambda: VoyageEmbedder(nome), "voyage"),
                               (lambda: OpenAIEmbedder(nome), "openai"),
                               (lambda: LocalEmbedder(nome), "local")):
        try:
            emb = construtor()
        except EmbeddingError as exc:
            log.debug("backend %s indisponivel: %s", rotulo, exc)
            continue
        log.info("embeddings por %s (%s, %d dimensoes)", rotulo, emb.model, emb.dim)
        return emb
    log.warning(
        "nenhum backend semantico disponivel; a busca cai no hash deterministico. "
        "Defina VOYAGE_API_KEY ou instale sentence-transformers para busca semantica."
    )
    return HashEmbedder()
