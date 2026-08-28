#!/usr/bin/env python3
"""Gera os manuscritos da série em padrão ABNT.

    python3 scripts/artigos/gerar.py 1        # Artigo 1
    python3 scripts/artigos/gerar.py 2        # Artigo 2
    python3 scripts/artigos/gerar.py 1 2      # os dois
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "scripts" / "comum"))
sys.path.insert(0, str(RAIZ / "scripts" / "artigo4p"))
sys.path.insert(0, str(RAIZ / "scripts" / "plano"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import abnt  # noqa: E402
import artigo1  # noqa: E402
import artigo2  # noqa: E402
import figuras_artigos  # noqa: E402
import figuras_analiticas  # noqa: E402
import figuras_plano  # noqa: E402

SAIDA = {1: "ARTIGO1_PERFIS_HUMOR_HANDEBOL.docx",
         2: "ARTIGO2_FADIGA_PERFIS_HANDEBOL.docx"}
MODULO = {1: artigo1, 2: artigo2}


def montar(numero: int, saida: Path, dir_figuras: Path) -> dict:
    figuras_artigos.gerar_artigo1(dir_figuras) if numero == 1 else \
        figuras_artigos.gerar_artigo2(dir_figuras)
    if numero == 1:
        figuras_plano.figura_prevalencia(dir_figuras)
    else:
        figuras_analiticas.figura_perfis(dir_figuras)

    mod = MODULO[numero]
    blocos = [(b[0], mod.TABELAS[b[1]]) if b[0] == "tab" else b
              for b in mod.BLOCOS]
    return abnt.montar(blocos, saida, titulo=mod.TITULO,
                       subtitulo=mod.SUBTITULO, abertura=mod.ABERTURA,
                       fonte_tabela=mod.FONTE_TABELA,
                       fonte_figura=mod.FONTE_FIGURA,
                       dir_figuras=dir_figuras)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("numeros", nargs="*", type=int, default=[1, 2],
                    choices=[1, 2])
    ap.add_argument("--dir", type=Path, default=Path("data"))
    ap.add_argument("--figuras", type=Path, default=Path("data/figartigos"))
    a = ap.parse_args()
    for numero in a.numeros or [1, 2]:
        saida = a.dir / SAIDA[numero]
        info = montar(numero, saida, a.figuras)
        print(f"\ngerado: {saida}")
        for k, v in info.items():
            print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
