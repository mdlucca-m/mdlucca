#!/usr/bin/env python3
"""Gera o relatório de auditoria das duas revisões."""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "comum"))
sys.path.insert(0, str(RAIZ / "scripts" / "artigos"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import abnt  # noqa: E402
import conteudo  # noqa: E402

if __name__ == "__main__":
    saida = Path(sys.argv[1] if len(sys.argv) > 1
                 else "data/AUDITORIA_REVISOES_HUMOR.docx")
    blocos = [(b[0], conteudo.TABELAS[b[1]]) if b[0] == "tab" else b
              for b in conteudo.BLOCOS]
    info = abnt.montar(blocos, saida, titulo=conteudo.TITULO,
                       subtitulo=conteudo.SUBTITULO)
    abnt.limpar_settings(saida)
    print("gerado:", saida)
    for k, v in info.items():
        print(f"  {k}: {v}")
