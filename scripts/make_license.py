#!/usr/bin/env python3
"""
make_license.py — ferramenta do FABRICANTE para emitir licencas de acesso.

Voce (dono do produto) usa isto para:
  * gerar seu par de chaves uma unica vez (--genkey) e embutir a PUBLICA no app;
  * EMITIR uma licenca para quem pagar (ou uma cortesia gratis) com validade;
  * verificar/inspecionar uma licenca.

A chave privada (data/vendor_private.key) NUNCA vai para o cliente nem para o git.

Exemplos:
  # 1) uma vez: gerar o par e ver a chave publica para colar em app/licensing.py
  python3 scripts/make_license.py --genkey

  # 2) emitir licenca paga (1 ano) para um cliente, com a marca dele
  python3 scripts/make_license.py issue --licensee "Academia X" \
      --brand "X Performance" --plan pro --days 365 --out academia_x.key

  # 3) cortesia gratis por 30 dias
  python3 scripts/make_license.py issue --licensee "Amigo" --plan cortesia --days 30

  # 4) verificar uma licenca
  python3 scripts/make_license.py verify --file academia_x.key
"""
from __future__ import annotations

import argparse
import base64
import json
import secrets
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import licensing as Lic  # noqa: E402

PRIV_PATH = ROOT / "data" / "vendor_private.key"


def _genkey():
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    priv = Ed25519PrivateKey.generate()
    raw_priv = priv.private_bytes(serialization.Encoding.Raw,
                                  serialization.PrivateFormat.Raw,
                                  serialization.NoEncryption())
    raw_pub = priv.public_key().public_bytes(serialization.Encoding.Raw,
                                             serialization.PublicFormat.Raw)
    PRIV_PATH.parent.mkdir(exist_ok=True)
    PRIV_PATH.write_text(base64.b64encode(raw_priv).decode())
    pub_b64 = base64.b64encode(raw_pub).decode()
    print(f"[ok] chave privada -> {PRIV_PATH}  (NAO versionar, NAO compartilhar)")
    print(f"\nCole esta chave publica em app/licensing.py (VENDOR_PUBLIC_KEY_B64):\n{pub_b64}")


def _issue(a):
    if not PRIV_PATH.is_file():
        sys.exit("chave privada nao encontrada; rode antes: make_license.py --genkey")
    priv_b64 = PRIV_PATH.read_text().strip()
    today = date.today()
    payload = {"id": "lic_" + secrets.token_hex(4), "licensee": a.licensee,
               "plan": a.plan, "issued": today.isoformat(),
               "features": a.features.split(",") if a.features else ["*"]}
    if a.brand:
        payload["brand"] = a.brand
    if a.days and a.days > 0:
        payload["expires"] = (today + timedelta(days=a.days)).isoformat()
    if a.max_athletes:
        payload["limits"] = {"max_athletes": a.max_athletes}
    token = Lic.make_token(payload, priv_b64)
    out = Path(a.out) if a.out else (ROOT / "data" / f"{payload['id']}.key")
    out.write_text(token)
    print(f"[ok] licenca emitida -> {out}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print("\nEntregue ESTE arquivo/token ao cliente. Ele ativa com:")
    print(f"  MDLUCCA_LICENSE_FILE={out.name}  (ou copie para data/license.key)")


def _verify(a):
    token = Path(a.file).read_text().strip() if a.file else a.token
    payload = Lic.verify_token(token)
    if not payload:
        sys.exit("[X] licenca INVALIDA (assinatura nao confere)")
    print("[ok] assinatura valida")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def main():
    ap = argparse.ArgumentParser(description="Emissor de licencas (fabricante).")
    ap.add_argument("--genkey", action="store_true", help="gera o par de chaves do fabricante")
    sub = ap.add_subparsers(dest="cmd")
    pi = sub.add_parser("issue", help="emitir uma licenca")
    pi.add_argument("--licensee", required=True)
    pi.add_argument("--brand", default=None, help="trava a marca do cliente (opcional)")
    pi.add_argument("--plan", default="pro")
    pi.add_argument("--days", type=int, default=365, help="validade em dias (0 = perpetua)")
    pi.add_argument("--features", default="", help="lista separada por virgula (vazio = tudo)")
    pi.add_argument("--max-athletes", type=int, default=0, dest="max_athletes")
    pi.add_argument("--out", default=None)
    pv = sub.add_parser("verify", help="verificar uma licenca")
    pv.add_argument("--file", default=None)
    pv.add_argument("--token", default=None)
    args = ap.parse_args()

    if args.genkey:
        _genkey()
    elif args.cmd == "issue":
        _issue(args)
    elif args.cmd == "verify":
        _verify(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
