"""
app/licensing.py — licenciamento white-label por chave assinada (Ed25519).

O FABRICANTE (voce) tem a chave privada e emite licencas com scripts/make_license.py.
O software carrega a chave publica embutida e VALIDA a licenca (assinatura +
validade). Assim so quem tem uma licenca sua consegue ativar o produto, e ninguem
consegue forjar (a privada nunca sai das suas maos).

Formato do token de licenca:  base64url(payload_json) + "." + base64url(assinatura)
Payload (exemplo):
  {"id":"lic_ab12","licensee":"Academia X","brand":"X Performance","plan":"pro",
   "issued":"2026-08-09","expires":"2027-08-09","features":["video","fvp"],
   "limits":{"max_athletes":500}}

Carregamento (nesta ordem): variavel MDLUCCA_LICENSE (token) -> arquivo em
MDLUCCA_LICENSE_FILE -> data/license.key. Sem licenca valida: modo NAO LICENCIADO
(a API funciona para leitura/demonstracao, mas recursos "premium" ficam bloqueados;
em desenvolvimento use MDLUCCA_DEV=1 para liberar tudo).
"""
from __future__ import annotations

import base64
import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Chave PUBLICA do fabricante (troque pela sua ao gerar seu proprio par).
VENDOR_PUBLIC_KEY_B64 = "gvih0vD/yAMGAhHkIsOE5C+cev1Nl4sI2UGx+Xu0kBQ="

_ROOT = Path(__file__).resolve().parents[1]


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def verify_token(token: str, public_key_b64: str = VENDOR_PUBLIC_KEY_B64) -> Optional[dict]:
    """Valida a assinatura e devolve o payload; None se invalido."""
    try:
        payload_b64, sig_b64 = token.strip().split(".", 1)
        payload = _b64url_decode(payload_b64)
        sig = _b64url_decode(sig_b64)
        pub = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))
        pub.verify(sig, payload)                 # levanta se assinatura nao bate
        return json.loads(payload)
    except (ValueError, InvalidSignature, json.JSONDecodeError):
        return None


def _load_token() -> Optional[str]:
    tok = os.environ.get("MDLUCCA_LICENSE")
    if tok:
        return tok
    for p in (os.environ.get("MDLUCCA_LICENSE_FILE"), str(_ROOT / "data" / "license.key")):
        if p and Path(p).is_file():
            return Path(p).read_text().strip()
    return None


def _days_left(expires: Optional[str]) -> Optional[int]:
    if not expires:
        return None
    try:
        exp = datetime.strptime(expires, "%Y-%m-%d").date()
        return (exp - date.today()).days
    except ValueError:
        return None


def status() -> dict:
    """Estado atual da licenca (para /license e para os gates)."""
    if os.environ.get("MDLUCCA_DEV") == "1":
        return {"valid": True, "mode": "dev", "licensee": "DEV", "plan": "dev",
                "features": ["*"], "reason": "MDLUCCA_DEV=1"}
    tok = _load_token()
    if not tok:
        return {"valid": False, "mode": "unlicensed", "reason": "sem licenca"}
    payload = verify_token(tok)
    if not payload:
        return {"valid": False, "mode": "invalid", "reason": "assinatura invalida"}
    dl = _days_left(payload.get("expires"))
    if dl is not None and dl < 0:
        return {"valid": False, "mode": "expired", "licensee": payload.get("licensee"),
                "expires": payload.get("expires"), "reason": "licenca expirada"}
    return {
        "valid": True, "mode": "licensed",
        "id": payload.get("id"), "licensee": payload.get("licensee"),
        "brand": payload.get("brand"), "plan": payload.get("plan", "standard"),
        "issued": payload.get("issued"), "expires": payload.get("expires"),
        "days_left": dl, "features": payload.get("features", []),
        "limits": payload.get("limits", {}),
    }


def is_valid() -> bool:
    return bool(status().get("valid"))


def has_feature(name: str) -> bool:
    st = status()
    if not st.get("valid"):
        return False
    feats = st.get("features", [])
    return "*" in feats or name in feats


def make_token(payload: dict, private_key_b64: str) -> str:
    """Assina um payload com a chave privada do fabricante (uso do make_license)."""
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    priv = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    sig = priv.sign(body)
    return b64url_encode(body) + "." + b64url_encode(sig)
