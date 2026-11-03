"""Mapa temático simplificado (formas planas, sem efeito 3D, sem tendências ou triangulação): os 199 estudos no
centro, os cinco temas e as variáveis de cada tema, com o número de estudos.

    python3 figs_tematico_simples.py   -> figuras/Figura_MapaTematico.png (4K)
"""
import json
import math
import sys
from pathlib import Path
sys.path.insert(0, "/home/user/corrigidos/revisada")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, FancyBboxPatch
import modelos as M
from figs_c import nome_sub

FIG = Path(__file__).parent / "figuras"
D = json.load(open("/home/user/corrigidos/revisada/dados_rev.json", encoding="utf-8"))
TXT = M.TXT


def clara(c, f=0.85):
    import matplotlib.colors as mc
    r, g, b = mc.to_rgb(c)
    return (r + (1 - r) * f, g + (1 - g) * f, b + (1 - b) * f)


def figura():
    CT, SUBS = D["conhecimento_temas"], D["conhecimento_subs"]
    fig = plt.figure(figsize=(14, 9.2), facecolor="white")
    ax = fig.add_axes([0, 0, 1, 1])
    pos = {1: (-4.4, 0.6), 2: (4.4, 0.6), 3: (0, 2.75), 4: (-2.1, -2.45), 5: (2.6, -2.45)}
    fan = {1: (98, 246, 2.25), 2: (62, -72, 2.2), 3: (158, 22, 1.9), 4: (172, 318, 1.65), 5: (192, 335, 1.6)}
    for i, (tx, ty) in pos.items():
        ax.plot([0, tx], [0, ty], color=clara(M.TEMA[i], 0.45), lw=4, zorder=1, solid_capstyle="butt")
    for i, (tx, ty) in pos.items():
        c_, t = M.TEMA[i], CT[i - 1]
        subs = [s for s in SUBS if s["tema"] == i]
        a0, a1, rr = fan[i]
        k = len(subs)
        for j, s in enumerate(subs):
            aa = math.radians(a0 + (a1 - a0) * j / max(k - 1, 1))
            rj = rr + (0.62 if math.sin(aa) < -0.85 else 0)
            sx, sy = tx + rj * math.cos(aa), ty + rj * math.sin(aa)
            ax.plot([tx, sx], [ty, sy], color=clara(c_, 0.55), lw=1.2, zorder=2)
            r = 0.17 + 0.2 * (s["estudos"] / 58) ** 0.5
            ax.add_patch(Circle((sx, sy), r, fc=c_, ec="white", lw=1.2, zorder=5))
            ax.text(sx, sy, f"{s['estudos']}", ha="center", va="center", fontsize=9.5, fontweight="bold",
                    color="white", zorder=7)
            ca, sa = math.cos(aa), math.sin(aa)
            nm = nome_sub(s["sub"])
            kw = dict(fontsize=9.5, color=TXT, zorder=7, linespacing=1.0)
            if abs(ca) < 0.3 and sa < 0:
                ax.text(sx, sy - r - 0.1, nm, ha="center", va="top", **kw)
            elif abs(ca) < 0.3:
                ax.text(sx, sy + r + 0.08, nm, ha="center", va="bottom", **kw)
            else:
                ax.text(sx + (r + 0.1) * (1 if ca > 0 else -1), sy, nm, ha="left" if ca > 0 else "right",
                        va="center", **kw)
        w, h = 2.25, 1.35
        ax.add_patch(FancyBboxPatch((tx - w / 2, ty - h / 2), w, h, boxstyle="round,pad=0,rounding_size=0.18",
                                    fc=c_, ec="white", lw=2, zorder=8))
        ax.text(tx, ty + 0.2, M.TEMA_3L[i].replace("\n", " ").replace("  ", " ") if False else M.TEMA_3L[i],
                ha="center", va="center", fontsize=9.6, fontweight="bold", color="white", zorder=9, linespacing=1.0)
        ax.text(tx, ty - 0.45, f"{t['estudos']} estudos", ha="center", va="center", fontsize=11, fontweight="bold",
                color="white", zorder=9)
    ax.add_patch(Circle((0, 0), 0.92, fc="white", ec="#94a3b8", lw=2.2, zorder=10))
    ax.text(0, 0.32, "Psicologia do\nesporte", ha="center", va="center", fontsize=10, color=TXT, fontweight="bold",
            zorder=11, linespacing=1.0)
    ax.text(0, -0.2, "199", ha="center", va="center", fontsize=24, fontweight="bold", color=TXT, zorder=11)
    ax.text(0, -0.58, "estudos", ha="center", va="center", fontsize=9, color=TXT, zorder=11)
    ax.text(0, -5.55, "Número no círculo: estudos que investigaram a variável; um estudo pode compor mais de um tema.",
            ha="center", va="center", fontsize=10, color="#4b5563", style="italic")
    ax.set_xlim(-9.0, 9.0)
    ax.set_ylim(-5.8, 5.15)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.savefig(FIG / "Figura_MapaTematico.png", dpi=300, facecolor="white", bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)


if __name__ == "__main__":
    figura()
    print("ok")
