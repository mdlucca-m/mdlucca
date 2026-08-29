#!/usr/bin/env python3
"""Gera o relatório de auditoria em padrão ABNT."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "comum"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import abnt  # noqa: E402
import conteudo  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("-o", "--saida", type=Path,
                    default=Path("data/AUDITORIA_PERFIS_HUMOR.docx"))
    a = ap.parse_args()
    blocos = [(b[0], conteudo.TABELAS[b[1]]) if b[0] == "tab" else b
              for b in conteudo.BLOCOS]
    info = abnt.montar(blocos, a.saida, titulo=conteudo.TITULO,
                       subtitulo=conteudo.SUBTITULO,
                       abertura=conteudo.ABERTURA,
                       fonte_tabela=conteudo.FONTE_TABELA,
                       fonte_figura=conteudo.FONTE_FIGURA)
    print(f"gerado: {a.saida}")
    for k, v in info.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
