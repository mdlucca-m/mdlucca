#!/usr/bin/env python3
"""Verificacao de saude do contêiner: o servico responde em /api/health?"""
import os
import sys
import urllib.request

url = f"http://127.0.0.1:{os.environ.get('LAPE_PORT', '8000')}/api/health"
try:
    with urllib.request.urlopen(url, timeout=5) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception as exc:
    print(f"sem resposta em {url}: {exc}", file=sys.stderr)
    sys.exit(1)
