#!/usr/bin/env python3
"""Sugestões de vídeo para os educativos de arranco.

    python3 videos_sugeridos.py            # mostra a lista, não grava nada
    python3 videos_sugeridos.py --aplicar  # grava no banco, depois de você confirmar

O QUE EU CONFERI E O QUE NÃO CONFERI
------------------------------------
Conferido: cada endereço abaixo apareceu em busca na web com o título que está
na tabela, e todos vêm da MESMA fonte — a Exercise Library da Catalyst
Athletics, de Greg Everett, que é referência em levantamento olímpico e mantém
um vídeo curto por exercício, sem narração longa.

NÃO conferido: eu não consegui abrir nenhum deles. O proxy desta máquina
bloqueia youtube.com e catalystathletics.com, e de qualquer forma eu não
assisto a vídeo. Não posso afirmar que o vídeo está no ar hoje, nem que a
execução que ele mostra é a que você quer que o seu elenco copie.

Por isso este arquivo não roda sozinho: assista, e só então rode com --aplicar.
Ou fixe outro endereço na aba Exercícios — é um campo de texto livre.
"""

import argparse
import sys

import banco

# nome no app  →  (título do vídeo, endereço)
SUGESTOES = {
    "Agachamento overhead": (
        "Overhead Squat | Olympic Weightlifting Exercise Library",
        "https://www.youtube.com/watch?v=m_fvfJi94D8"),
    "Arranco de força (muscle snatch)": (
        "Muscle Snatch | Olympic Weightlifting Exercise Library",
        "https://www.youtube.com/watch?v=nJmtGVutszE"),
    "Snatch balance": (
        "Snatch Balance | Olympic Weightlifting Exercise Library",
        "https://www.youtube.com/watch?v=8KKQTdnxWso"),
    "Arranco do joelho (hang)": (
        "Hang Snatch | Olympic Weightlifting Exercise Library",
        # o resultado da busca veio com uma barra sobrando no fim, que muda o
        # identificador do vídeo e quebra o link — removida aqui
        "https://www.youtube.com/watch?v=Php-RclQ1yU"),
    "Snatch pull / Hang high pull": (
        "Snatch Pull | Olympic Weightlifting Exercise Library",
        "https://www.youtube.com/watch?v=G1QygZ3Kd3w"),
}

# Sem sugestão, e o motivo de cada uma:
SEM_SUGESTAO = {
    "Arranco do alto (high hang)":
        "a Catalyst tem a página do High-Hang Snatch, mas não achei o vídeo "
        "solto com título que eu pudesse casar com segurança",
    "Passagem de bastão no agachamento":
        "é um educativo de bancada, sem vídeo canônico — vale mais você filmar",
    "Tríplice extensão com bastão":
        "idem: cada escola ensina de um jeito, e o seu jeito é o que vale",
}


def mostrar():
    print(__doc__)
    print("SUGESTÕES\n" + "─" * 78)
    for nome, (titulo, url) in SUGESTOES.items():
        print(f"\n  {nome}")
        print(f"    {titulo}")
        print(f"    {url}")
    print("\n\nSEM SUGESTÃO\n" + "─" * 78)
    for nome, motivo in SEM_SUGESTAO.items():
        print(f"\n  {nome}\n    {motivo}")
    print("\n" + "─" * 78)
    print("  Assista a cada um. Depois:  python3 videos_sugeridos.py --aplicar")
    print("  Para trocar qualquer um: aba Exercícios, campo do vídeo.\n")


def aplicar(caminho):
    with banco.conectar(caminho) as con:
        faltam = [n for n in SUGESTOES
                  if not con.execute("SELECT 1 FROM exercicios WHERE nome=?",
                                     (n,)).fetchone()]
        if faltam:
            print("  Estes exercícios não estão na biblioteca deste banco:")
            for n in faltam:
                print("   ·", n)
            print("  Rode o app uma vez para semear a biblioteca.\n")
            return 1
        ja = banco.dics(con.execute(
            "SELECT nome, video_url FROM exercicios"
            " WHERE nome IN ({}) AND video_url IS NOT NULL".format(
                ",".join("?" * len(SUGESTOES))), list(SUGESTOES)).fetchall())
        if ja:
            print("  Estes já têm vídeo fixado por você e NÃO serão tocados:")
            for e in ja:
                print(f"   · {e['nome']}  →  {e['video_url']}")
            print()
        n = 0
        for nome, (_titulo, url) in SUGESTOES.items():
            cur = con.execute(
                "UPDATE exercicios SET video_url=? WHERE nome=? AND video_url IS NULL",
                (url, nome))
            n += cur.rowcount
    print(f"  {n} vídeo(s) fixado(s). Troque qualquer um na aba Exercícios.\n")
    return 0


def main():
    p = argparse.ArgumentParser(description="Sugestões de vídeo para os educativos")
    p.add_argument("--aplicar", action="store_true",
                   help="grava as sugestões no banco (só onde ainda não há vídeo)")
    p.add_argument("--db", default=banco.CAMINHO)
    args = p.parse_args()
    mostrar()
    if not args.aplicar:
        return 0
    print("  Você assistiu a todos e quer fixá-los? [s/N] ", end="")
    if input().strip().lower() not in ("s", "sim"):
        print("  Nada gravado.\n")
        return 0
    return aplicar(args.db)


if __name__ == "__main__":
    sys.exit(main())
