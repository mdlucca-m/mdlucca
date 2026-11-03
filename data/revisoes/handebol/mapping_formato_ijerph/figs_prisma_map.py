"""Fluxograma PRISMA 2020 da revisão de mapeamento (modelo oficial), em 4K, com os números por etapa, a coluna de
outras fontes e o número de estudos que respondem a cada questão de pesquisa.

    python3 figs_prisma_map.py   -> figuras/fig1_prisma_v2.png
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIG = Path(__file__).parent / "figuras"
D = json.load(open("/home/user/corrigidos/revisada/dados_rev.json", encoding="utf-8"))
P = D["prisma"]
B = {r[0]: r for r in D["prisma_bases"][1:9]}
mil = lambda n: f"{int(n):,}".replace(",", ".")
AMAR, AZUL, CINZA = "#FFC000", "#9DC3E6", "#F2F2F2"
FS = 10.5


def caixa(ax, x, y, w, h, txt, fc="white", fs=FS, bold=False, ha="left"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="square,pad=0", fc=fc, ec="black", lw=1.1))
    tx = x + 0.12 if ha == "left" else x + w / 2
    ax.text(tx, y + h / 2, txt, ha=ha, va="center", fontsize=fs, fontweight="bold" if bold else "normal",
            linespacing=1.35, family="DejaVu Sans")


def fase(ax, y, h, txt):
    ax.add_patch(FancyBboxPatch((0.1, y), 0.55, h, boxstyle="round,pad=0,rounding_size=0.12", fc=AZUL, ec="#5b8bb8",
                                lw=1.1))
    ax.text(0.375, y + h / 2, txt, rotation=90, ha="center", va="center", fontsize=11.5, fontweight="bold",
            family="DejaVu Sans")


def seta(ax, x0, y0, x1, y1):
    ax.annotate("", (x1, y1), (x0, y0), arrowprops=dict(arrowstyle="-|>", lw=1.2, color="black", mutation_scale=14))


def figura():
    fig = plt.figure(figsize=(11, 12.35), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 11)
    ax.set_ylim(1.25, 13.6)
    ax.axis("off")
    # cabeçalhos
    caixa(ax, 0.9, 12.9, 6.55, 0.5, "Identificação de estudos por meio de bases de dados", fc=AMAR, bold=True, ha="center")
    caixa(ax, 7.65, 12.9, 3.2, 0.5, "Identificação por outras fontes", fc=CINZA, bold=True, ha="center", fs=10)
    # identificação
    fase(ax, 9.75, 3.0, "Identificação")
    bases = "\n".join(f"   {k} (n = {mil(B[k][1])})" for k in ["OpenAlex", "Scopus", "Web of Science", "Europe PMC",
                                                                   "PubMed", "Crossref", "LILACS", "SciELO"])
    caixa(ax, 0.9, 9.75, 3.3, 3.0, f"Registros identificados nas\noito bases (n = {mil(4144)}):\n{bases}", fs=9.8)
    caixa(ax, 4.45, 10.55, 3.0, 2.2, f"Registros removidos antes\nda triagem:\n   Duplicatas entre bases\n   (n = {mil(P['Duplicatas (passagens repetidas entre bases)'])})\n"
                                  f"   Fora do escopo pelo filtro\n   de termos (OpenAlex e\n   Crossref) (n = {mil(P['Fora do escopo pelo filtro da busca (OpenAlex e Crossref)'])})", fs=9.6)
    caixa(ax, 7.65, 10.55, 3.2, 2.2, "Listas de referências\ndos estudos incluídos:\n   novos registros\n   elegíveis (n = 0)", fs=9.8)
    seta(ax, 4.2, 11.6, 4.45, 11.6)
    # triagem
    fase(ax, 5.15, 4.25, "Triagem")
    caixa(ax, 0.9, 8.35, 3.3, 1.05, f"Registros distintos\n(n = {mil(2582)}), dos quais\ntriados (n = {mil(969)})", fs=10)
    caixa(ax, 4.45, 8.35, 3.0, 1.05, f"Excluídos pelo título e pelo\nresumo, por não atenderem\nà estratégia PECOS (n = {P['Excluídos por título e resumo']})", fs=9.6)
    seta(ax, 2.55, 9.75, 2.55, 9.4); seta(ax, 4.2, 8.87, 4.45, 8.87)
    caixa(ax, 0.9, 6.75, 3.3, 1.05, "Relatórios que avançaram\nda triagem (n = 392)", fs=10)
    caixa(ax, 4.45, 6.75, 3.0, 1.05, f"Relatórios em dúvida, sem\nconfirmação de elegibilidade\n(n = {P['Em dúvida, sem confirmação de elegibilidade']})", fs=9.6)
    seta(ax, 2.55, 8.35, 2.55, 7.8); seta(ax, 4.2, 7.27, 4.45, 7.27)
    caixa(ax, 0.9, 5.15, 3.3, 1.05, "Relatórios avaliados quanto\nà elegibilidade (n = 249)", fs=10)
    caixa(ax, 4.45, 5.15, 3.0, 1.05, f"Excluídos na conferência de\nelegibilidade, por não\natenderem aos critérios (n = {P['Retirados na conferência']})", fs=9.6)
    seta(ax, 2.55, 6.75, 2.55, 6.2); seta(ax, 4.2, 5.67, 4.45, 5.67)
    caixa(ax, 7.65, 5.15, 3.2, 1.05, "Relatórios das listas de\nreferências avaliados (n = 0)", fs=9.8)
    seta(ax, 9.25, 10.55, 9.25, 6.2)
    # incluídos
    fase(ax, 1.35, 3.45, "Incluídos")
    caixa(ax, 0.9, 3.85, 3.3, 0.95, "Estudos incluídos\nna revisão (n = 199)", fs=10.5, bold=True)
    seta(ax, 2.55, 5.15, 2.55, 4.8)
    qp = ("Estudos que responderam a cada questão de pesquisa:\n"
          "   QP1. Características, populações e países: 199 estudos (186 com amostra relatada; 51 países)\n"
          "   QP2. Variáveis e domínios conceituais: 199 estudos, 40 variáveis em 7 domínios\n"
          "   QP3. Contextos e períodos: 173 estudos com contexto relatado; 199 por período de publicação\n"
          "   QP4. Delineamentos e intervenções: 28 estudos experimentais, 24 com intervenção\n"
          "   QP5. Resultados e lacunas: 193 estudos com resultado classificado (6 não determináveis)")
    caixa(ax, 0.9, 1.35, 9.95, 2.2, qp, fs=9.8, fc="#fbfbfb")
    seta(ax, 2.55, 3.85, 2.55, 3.55)
    fig.savefig(FIG / "fig1_prisma_v2.png", dpi=380, facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    figura()
    print("ok")
