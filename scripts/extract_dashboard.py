#!/usr/bin/env python3
"""
scripts/extract_dashboard.py

Extrai as estruturas de dados embutidas no dashboard HTML autocontido
(Dashboard_Atleta2.html) para um único arquivo JSON limpo, que é a fonte
de verdade do ETL (scripts/ingest.py).

Estratégia:
  * Percorre apenas o bloco <script> do HTML.
  * Captura toda declaração de topo (coluna 0) do tipo `const NOME = <valor>;`
    cujo valor comece com `{` ou `[` (objeto/array).
  * Usa brace-matching consciente de strings/escapes para delimitar o valor.
  * Ignora VIDEO_DATA (megabytes de base64) e identificadores internos (_*).
  * Normaliza cada valor com Node (JSON.stringify), o que aceita tanto JSON
    puro quanto literais JS com chaves sem aspas (ex.: VAR_CONFIG).

Uso:
  python3 scripts/extract_dashboard.py <input.html> [-o data/dashboard_extracted.json]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

# Declarações a ignorar (grandes demais ou irrelevantes para o backend).
SKIP = {"VIDEO_DATA"}

DECL_RE = re.compile(r"^(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*", re.MULTILINE)


def find_script_region(html: str) -> str:
    """Retorna a concatenação do conteúdo de todos os blocos <script> inline."""
    parts = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)
    if not parts:
        raise SystemExit("Nenhum bloco <script> inline encontrado no HTML.")
    return "\n".join(parts)


def match_value(text: str, start: int) -> tuple[str, int]:
    """
    A partir de `start` (posição de '{' ou '['), devolve (raw_value, end_index)
    fazendo balanceamento de chaves/colchetes ciente de strings JS.
    """
    depth = 0
    i = start
    n = len(text)
    in_str: str | None = None  # ', " ou `
    while i < n:
        c = text[i]
        if in_str is not None:
            if c == "\\":
                i += 2
                continue
            if c == in_str:
                in_str = None
            i += 1
            continue
        if c in ("'", '"', "`"):
            in_str = c
            i += 1
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            i = n if j == -1 else j
            continue
        if c == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c in "{[":
            depth += 1
        elif c in "}]":
            depth -= 1
            if depth == 0:
                return text[start : i + 1], i + 1
        i += 1
    raise ValueError(f"Valor não balanceado começando em offset {start}.")


def js_to_json(raw: str) -> object:
    """Normaliza um literal JS (JSON ou objeto com chaves sem aspas) via Node."""
    # Passa via stdin: valores grandes (DATA) estouram o limite de argv com -e.
    script = (
        "let s='';process.stdin.on('data',d=>s+=d);"
        "process.stdin.on('end',()=>{const V=eval('('+s+')');"
        "process.stdout.write(JSON.stringify(V));});"
    )
    out = subprocess.run(
        ["node", "-e", script],
        input=raw,
        capture_output=True,
        text=True,
    )
    if out.returncode != 0:
        raise ValueError(f"Node falhou ao parsear: {out.stderr.strip()[:300]}")
    return json.loads(out.stdout)


def extract(html: str) -> dict:
    script = find_script_region(html)
    result: dict[str, object] = {}
    for m in DECL_RE.finditer(script):
        name = m.group(1)
        if name in SKIP or name.startswith("_"):
            continue
        vstart = m.end()
        if vstart >= len(script) or script[vstart] not in "{[":
            continue  # não é objeto/array (ex.: números, chamadas de função)
        try:
            raw, _ = match_value(script, vstart)
            value = js_to_json(raw)
        except ValueError as exc:
            print(f"  [skip] {name}: {exc}", file=sys.stderr)
            continue
        result[name] = value
        print(f"  [ok]   {name} ({len(raw):,} chars)", file=sys.stderr)
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("input", help="Caminho do dashboard HTML")
    ap.add_argument(
        "-o",
        "--output",
        default="data/dashboard_extracted.json",
        help="Arquivo JSON de saída",
    )
    args = ap.parse_args()

    html = Path(args.input).read_text(encoding="utf-8")
    data = extract(html)

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n{len(data)} estruturas extraídas -> {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
