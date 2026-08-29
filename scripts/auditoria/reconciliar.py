#!/usr/bin/env python3
"""Reconciliação das classificações de perfil de humor que circulam no projeto.

Três séries distintas foram localizadas na auditoria de documentos. Elas usam
o mesmo conjunto de dados e chegam a resultados diferentes porque a regra de
classificação é diferente em cada uma. Este módulo põe as três lado a lado e
calcula as faixas de significado para cada uma.

    python3 scripts/auditoria/reconciliar.py
"""
from __future__ import annotations

import sys

# ── Série A · escore T e regra de forma ───────────────────────────────────
# Artigo_Perfil_de_humor__handebol.docx, Tabela 12. O método declara:
# "Para a classificação de perfis e a análise multivariada, os escores foram
# convertidos em escores T (M = 50; DP = 10)."
SERIE_A = {                       # perfil: (n dia 1, % dia 1, n dia 7, % dia 7)
    "Iceberg":              (17, 40.5, 8, 17.4),
    "Superfície":           (11, 26.2, 13, 28.3),
    "Everest invertido":    (6, 14.3, 4, 8.7),
    "Iceberg invertido":    (4, 9.5, 3, 6.5),
    "Submerso":             (3, 7.1, 5, 10.9),
    "Barbatana de tubarão": (1, 2.4, 13, 28.3),
}
N_A = (42, 46)

# ── Série B · padronização interna e centroide mais próximo ──────────────
# Artigo_Final_.docx, Tabela 21, replicada em ARTIGO_COMPLETO_20260726 e em
# ARTIGO_CORRIGIDO_20260724_REVISOR. O método declara: "Como não há normas
# populacionais (escore-T) para esta amostra, as subescalas foram
# padronizadas [dentro da amostra]".
SERIE_B = {                        # perfil: (% dia 1, % dia 7)
    "Iceberg":              (21.4, 6.5),
    "Superfície":           (47.6, 60.9),
    "Everest invertido":    (4.8, 4.3),
    "Iceberg invertido":    (9.5, 6.5),
    "Submerso":             (7.1, 10.9),
    "Barbatana de tubarão": (9.5, 10.9),
}

# ── Série C · critério de Morgan sobre escores brutos ────────────────────
# Artigo_Final_.docx, Tabela 20. Não classifica nos seis perfis: apenas
# separa iceberg de não iceberg pela ordem entre vigor e as cinco negativas.
SERIE_C = {"Perfil iceberg": (71.4, 32.6), "Humor perturbado": (47.6, 71.7)}

FAVORAVEL = ["Iceberg"]
NEUTRO = ["Superfície", "Submerso"]
RISCO = ["Barbatana de tubarão", "Iceberg invertido", "Everest invertido"]


def br(v: float, casas: int = 1) -> str:
    return f"{v:.{casas}f}".replace(".", ",")


def sinal(v: float, casas: int = 1) -> str:
    return f"{v:+.{casas}f}".replace(".", ",").replace("-", "−")


def faixas(serie: dict, i1: int, i7: int) -> dict:
    return {nome: (sum(serie[p][i1] for p in perfis),
                   sum(serie[p][i7] for p in perfis))
            for nome, perfis in (("Favorável", FAVORAVEL),
                                 ("Neutro", NEUTRO), ("De risco", RISCO))}


def imprimir() -> None:
    print("═" * 76)
    print("SÉRIE A · escore T com regra de forma")
    print("  fonte: Artigo_Perfil_de_humor__handebol.docx, Tabela 12")
    print(f"  denominador: {N_A[0]} observações no dia 1, {N_A[1]} no dia 7")
    print("═" * 76)
    print(f'{"perfil":24s}{"dia 1":>16s}{"dia 7":>16s}{"diferença":>12s}')
    for p, (n1, p1, n7, p7) in sorted(SERIE_A.items(), key=lambda x: -x[1][1]):
        print(f"{p:24s}{f'{n1} ({br(p1)}%)':>16s}"
              f"{f'{n7} ({br(p7)}%)':>16s}{sinal(p7 - p1) + ' p.p.':>12s}")
    fa = faixas(SERIE_A, 1, 3)
    print()
    for nome, (a, b) in fa.items():
        print(f"  faixa {nome:12s} {br(a):>6s}% → {br(b):>6s}%"
              f"   {sinal(b - a)} p.p.")

    print("\n" + "═" * 76)
    print("SÉRIE B · padronização interna com centroide mais próximo")
    print("  fonte: Artigo_Final_.docx, Tabela 21, e cópias")
    print("═" * 76)
    print(f'{"perfil":24s}{"dia 1":>16s}{"dia 7":>16s}{"diferença":>12s}')
    for p, (p1, p7) in sorted(SERIE_B.items(), key=lambda x: -x[1][0]):
        print(f"{p:24s}{br(p1) + '%':>16s}{br(p7) + '%':>16s}"
              f"{sinal(p7 - p1) + ' p.p.':>12s}")
    fb = faixas(SERIE_B, 0, 1)
    print()
    for nome, (a, b) in fb.items():
        print(f"  faixa {nome:12s} {br(a):>6s}% → {br(b):>6s}%"
              f"   {sinal(b - a)} p.p.")

    print("\n" + "═" * 76)
    print("SÉRIE C · critério de Morgan sobre escores brutos")
    print("  fonte: Artigo_Final_.docx, Tabela 20")
    print("═" * 76)
    for p, (p1, p7) in SERIE_C.items():
        print(f"{p:24s}{br(p1) + '%':>16s}{br(p7) + '%':>16s}"
              f"{sinal(p7 - p1) + ' p.p.':>12s}")

    print("\n" + "═" * 76)
    print("ONDE AS DUAS CLASSIFICAÇÕES DIVERGEM")
    print("═" * 76)
    print(f'{"perfil":24s}{"dia 1 A":>10s}{"dia 1 B":>10s}'
          f'{"dia 7 A":>10s}{"dia 7 B":>10s}')
    for p in SERIE_A:
        a1, a7 = SERIE_A[p][1], SERIE_A[p][3]
        b1, b7 = SERIE_B[p]
        marca = "  <<<" if abs(a1 - b1) > 5 or abs(a7 - b7) > 5 else ""
        print(f"{p:24s}{br(a1):>10s}{br(b1):>10s}{br(a7):>10s}{br(b7):>10s}"
              f"{marca}")
    print("\n  As linhas marcadas concentram toda a divergência. Submerso e")
    print("  iceberg invertido são idênticos nas duas séries, o que indica")
    print("  que a diferença está na regra de fronteira e não nos dados.")


if __name__ == "__main__":
    imprimir()
    sys.exit(0)
