#!/usr/bin/env python3
"""Gera o plano editorial em padrão ABNT.

    python3 scripts/plano/gerar_plano.py -o data/PLANO_EDITORIAL.docx
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "comum"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import abnt  # noqa: E402
import conteudo  # noqa: E402
import figuras_plano  # noqa: E402


def montar(saida: Path, dir_figuras: Path) -> dict:
    figuras_plano.gerar_todas(dir_figuras)
    blocos = [(b[0], conteudo.TABELAS[b[1]]) if b[0] == "tab" else b
              for b in conteudo.BLOCOS]
    return abnt.montar(blocos, saida, titulo=conteudo.TITULO,
                       subtitulo=conteudo.SUBTITULO,
                       abertura=conteudo.ABERTURA,
                       fonte_tabela=conteudo.FONTE_TABELA,
                       fonte_figura=conteudo.FONTE_FIGURA,
                       dir_figuras=dir_figuras)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--saida", type=Path,
                    default=Path("data/PLANO_EDITORIAL_HUMOR_HANDEBOL.docx"))
    ap.add_argument("--figuras", type=Path, default=Path("data/figplano"))
    a = ap.parse_args()
    info = montar(a.saida, a.figuras)
    print(f"\ngerado: {a.saida}")
    for k, v in info.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
