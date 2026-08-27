"""Camada HTTP comum: retentativa com espera exponencial, respeito a Retry-After,
limitação de taxa e gravação do corpo bruto para auditoria.

Usa apenas a biblioteca padrão, e honra HTTPS_PROXY / SSL_CERT_FILE do ambiente
(urllib os lê automaticamente). Nunca desabilita verificação de TLS.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

AGENTE = "revisao-handebol/1.0 (pesquisa academica; contato via repositorio)"
TENTATIVAS = 5
ESPERA_BASE = 2.0          # segundos; dobra a cada tentativa
ESPERA_MAX = 60.0


class ErroHTTP(RuntimeError):
    def __init__(self, status: int, url: str, corpo: str = ""):
        self.status, self.url, self.corpo = status, url, corpo
        super().__init__(f"HTTP {status} em {url.split('?')[0]}: {corpo[:200]}")


class BloqueioDeRede(RuntimeError):
    """CONNECT recusado pela política de egresso do ambiente (403/407 do proxy)."""


@dataclass
class Sessao:
    """Cliente HTTP com limite de taxa e gravação opcional do corpo bruto."""
    req_por_segundo: float = 3.0
    dir_bruto: Path | None = None
    _ultimo: float = field(default=0.0, repr=False)
    _seq: int = field(default=0, repr=False)

    def _esperar_vez(self) -> None:
        intervalo = 1.0 / self.req_por_segundo
        agora = time.monotonic()
        atraso = self._ultimo + intervalo - agora
        if atraso > 0:
            time.sleep(atraso)
        self._ultimo = time.monotonic()

    def _gravar(self, rotulo: str, corpo: bytes) -> None:
        if self.dir_bruto is None:
            return
        self.dir_bruto.mkdir(parents=True, exist_ok=True)
        self._seq += 1
        ext = "json" if corpo[:1] in (b"{", b"[") else "xml"
        (self.dir_bruto / f"{self._seq:04d}_{rotulo}.{ext}").write_bytes(corpo)

    def pedir(self, url: str, *, dados: dict | None = None,
              cabecalhos: dict | None = None, rotulo: str = "resposta") -> bytes:
        corpo = urllib.parse.urlencode(dados).encode() if dados else None
        cab = {"User-Agent": AGENTE, **(cabecalhos or {})}
        espera = ESPERA_BASE
        ultimo_erro: Exception | None = None

        for tentativa in range(1, TENTATIVAS + 1):
            self._esperar_vez()
            req = urllib.request.Request(url, data=corpo, headers=cab)
            try:
                with urllib.request.urlopen(req, timeout=90) as r:
                    dados_resp = r.read()
                self._gravar(rotulo, dados_resp)
                return dados_resp
            except urllib.error.HTTPError as e:
                texto = e.read().decode("utf-8", "replace")
                # 4xx que não adianta repetir
                if e.code in (400, 401, 403, 404) and "CONNECT" not in texto:
                    raise ErroHTTP(e.code, url, texto) from e
                ultimo_erro = ErroHTTP(e.code, url, texto)
                if e.code == 429:
                    ra = e.headers.get("Retry-After")
                    if ra and ra.isdigit():
                        espera = min(float(ra), ESPERA_MAX)
            except urllib.error.URLError as e:
                motivo = str(e.reason)
                if "403" in motivo or "407" in motivo or "Tunnel connection failed" in motivo:
                    raise BloqueioDeRede(
                        f"{urllib.parse.urlparse(url).hostname} recusado pela política de "
                        "egresso do ambiente. O host precisa ser liberado na configuração "
                        "de rede do ambiente remoto; não há contorno a partir daqui."
                    ) from e
                ultimo_erro = e

            if tentativa < TENTATIVAS:
                time.sleep(espera)
                espera = min(espera * 2, ESPERA_MAX)

        raise ultimo_erro if ultimo_erro else RuntimeError("falha desconhecida")

    def json(self, url: str, **kw) -> dict:
        return json.loads(self.pedir(url, **kw))
