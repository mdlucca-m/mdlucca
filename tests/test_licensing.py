"""
Testes do licenciamento white-label: assinatura Ed25519 (emitir/validar),
resistencia a forja e o gate de acesso da API (402 sem licenca).
"""
import base64
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from cryptography.hazmat.primitives import serialization  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402

from app import licensing as Lic  # noqa: E402


def _keypair():
    priv = Ed25519PrivateKey.generate()
    raw_priv = priv.private_bytes(serialization.Encoding.Raw,
                                  serialization.PrivateFormat.Raw,
                                  serialization.NoEncryption())
    raw_pub = priv.public_key().public_bytes(serialization.Encoding.Raw,
                                             serialization.PublicFormat.Raw)
    return base64.b64encode(raw_priv).decode(), base64.b64encode(raw_pub).decode()


def test_sign_and_verify_roundtrip():
    priv, pub = _keypair()
    tok = Lic.make_token({"licensee": "Academia X", "plan": "pro"}, priv)
    payload = Lic.verify_token(tok, pub)
    assert payload and payload["licensee"] == "Academia X"


def test_tampered_payload_rejected():
    priv, pub = _keypair()
    tok = Lic.make_token({"licensee": "Academia X", "plan": "free"}, priv)
    _, sig = tok.split(".", 1)
    forged = Lic.b64url_encode(json.dumps({"licensee": "HACKER", "plan": "pro"})
                               .encode()) + "." + sig
    assert Lic.verify_token(forged, pub) is None


def test_wrong_key_rejected():
    priv1, _ = _keypair()
    _, pub2 = _keypair()
    tok = Lic.make_token({"licensee": "X"}, priv1)
    assert Lic.verify_token(tok, pub2) is None          # assinada por outra chave


def test_days_left():
    assert Lic._days_left(None) is None
    assert Lic._days_left("2000-01-01") < 0             # no passado
    assert Lic._days_left("2999-01-01") > 0


def test_api_gate_blocks_without_license(monkeypatch):
    monkeypatch.delenv("MDLUCCA_DEV", raising=False)
    monkeypatch.setattr(Lic, "_load_token", lambda: None)   # simula sem licenca
    from fastapi.testclient import TestClient
    from app.api import app
    c = TestClient(app)
    assert c.get("/health").status_code == 200          # aberto
    assert c.get("/branding").status_code == 200        # aberto
    assert c.get("/license").json()["valid"] is False
    assert c.get("/sessions").status_code == 402         # gated


def test_api_gate_allows_in_dev(monkeypatch):
    monkeypatch.setenv("MDLUCCA_DEV", "1")
    from fastapi.testclient import TestClient
    from app.api import app
    c = TestClient(app)
    assert c.get("/license").json()["valid"] is True
    assert c.get("/sessions").status_code != 402        # gate liberado


if __name__ == "__main__":
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    print(f"rode com pytest ({len(fns)} testes)")
