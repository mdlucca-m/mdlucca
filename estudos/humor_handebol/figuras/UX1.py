# -*- coding: utf-8 -*-
"""X1 a X5 — as cinco figuras novas do relatório exploratório ampliado.

X1: caixa e bigodes de quatro variáveis, dia a dia (D1 a D7).
X2: histograma das sete variáveis do BRUMS.
X3: transição individual de perfil entre o primeiro e o sétimo dia.
X4: magnitude de mudança em cada uma das seis transições diárias.
X5: percentual de dias na faixa de risco, por atleta.
"""
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "UVh.py")).read())
EXP = json.load(open(f"{S}/V2_expl.json", encoding="utf-8"))
PAR = B['pares']; dia_arr = np.array([p['dia'] for p in PAR])
X = {v: np.array([p[v] for p in PAR], float) for v in V7}

# ==================== X1: caixa e bigodes por dia, com linha de tendência ====================
DEST = ['Tensão', 'Vigor', 'Fadiga', 'TMD']
fig, axs = plt.subplots(1, 4, figsize=(16.4, 4.2))
for a, v in zip(axs, DEST):
    dados = [X[v][dia_arr == d] for d in range(1, 8)]
    medianas = np.array([np.median(dd) for dd in dados])
    bp = a.boxplot(dados, widths=.6, patch_artist=True, showfliers=True, zorder=3,
                    flierprops=dict(marker='o', ms=3.2, mfc='none', mec=CV[v], alpha=.55),
                    medianprops=dict(color=SURF, lw=1.8, zorder=6), whiskerprops=dict(color=MUT, lw=1.1),
                    capprops=dict(color=MUT, lw=1.1))
    for p in bp['boxes']: p.set(facecolor=CV[v], alpha=.78, lw=0)
    # linha de tendência: mediana de cada dia, com sombra ±piso em torno dela
    piso = A1['SER'][v]['piso'] if v in A1['SER'] else None
    if piso:
        a.fill_between(range(1, 8), medianas - piso, medianas + piso, color=INK, alpha=.07, zorder=1, lw=0)
    a.plot(range(1, 8), medianas, '-', lw=2.2, color=INK, alpha=.75, zorder=5,
           marker='D', ms=5.0, mfc=SURF, mec=INK, mew=1.4)
    a.set_xticks(range(1, 8)); a.set_xticklabels([f"D{d}" for d in range(1, 8)], fontsize=9.4)
    a.set_title(L(v), fontsize=11.4, loc='left', fontweight='bold', color=CV[v])
    gy(a)
axs[0].set_ylabel('Escore bruto', fontsize=10.4)
rod(fig, 'Caixa: quartis; traço branco: mediana; pontos além dos bigodes: valores atípicos por 1,5 vez o intervalo '
        'interquartil. Losango e linha escura: tendência da mediana diária, com a banda cinza marcando ±1 piso de '
        'ruído em torno dela.')
fig.tight_layout(); salvar(fig, 'X1fig')

# ==================== X2: histograma das sete variáveis ====================
fig, axs = plt.subplots(2, 4, figsize=(16.4, 7.0))
for a, v in zip(axs.flat, V7):
    x = X[v]
    bins = np.arange(x.min() - .5, x.max() + 1.5, 1) if v != 'TMD' else 14
    a.hist(x, bins=bins, color=CV[v], alpha=.82, edgecolor=SURF, lw=.6)
    a.axvline(A1['DESC'][v]['md'], color=INK, lw=1.6, ls='--')
    a.set_title(L(v), fontsize=11, loc='left', fontweight='bold', color=CV[v])
    a.annotate(f"md {vg(A1['DESC'][v]['md'],1)}", xy=(.97, .92), xycoords='axes fraction',
               ha='right', fontsize=8.6, color=INK)
    gy(a)
axs.flat[-1].axis('off')
rod(fig, 'Linha tracejada: mediana. Distribuição sobre os 166 pares atleta-dia.')
fig.tight_layout(); salvar(fig, 'X2fig')

# ==================== X3: retenção e migração de perfil, D1 → D7 ====================
TRANS = EXP['TRANS']; NOMES_T = [nm for nm in EXP['NOMES_MATRIZ'] if TRANS[nm]['n_d1'] > 0]
NOMES_T.sort(key=lambda nm: TRANS[nm]['pct_ficou'])
PITCH = 1.7
yy = np.arange(len(NOMES_T))[::-1] * PITCH
fig, a = plt.subplots(figsize=(11.6, 1.15 * len(NOMES_T) + 1.3))
a.barh(yy, [100] * len(NOMES_T), height=1.0, color=GRID, alpha=.55, zorder=2)
for y, nm in zip(yy, NOMES_T):
    t = TRANS[nm]; pct = t['pct_ficou']
    a.barh(y, pct, height=1.0, color=CPF[nm], alpha=.92, edgecolor=CPF[nm], lw=1.4, zorder=3)
    dest = sorted(t['destinos'].items(), key=lambda x: -x[1])
    dtxt = '; '.join(f"{v}× {k}" for k, v in dest[:2]) if dest else 'nenhum outro caso'
    a.annotate(f"{vg(pct,0)}%  (n = {t['n_d1']})", xy=(pct, y), xytext=(8, 0), textcoords='offset points',
               va='center', fontsize=10.4, fontweight='bold', color=CPF[nm], zorder=5)
    a.annotate(f"migrou para: {dtxt}" if pct < 100 else 'sem migração no único caso',
               xy=(2, y - .62), va='top', fontsize=8.3, color=MUT, style='italic', zorder=5)
a.set_yticks(yy); a.set_yticklabels(NOMES_T, fontsize=10.6)
for t_, nm in zip(a.get_yticklabels(), NOMES_T): t_.set_color(CPF[nm]); t_.set_fontweight('bold')
a.set_ylim(-PITCH * .62, yy[0] + PITCH * .62)
a.set_xlim(0, 118); a.set_xticks([0, 25, 50, 75, 100])
a.set_xlabel('Permaneceu no mesmo perfil em D7 (%)', fontsize=10.8)
a.set_title(f'Retenção e migração de perfil, do primeiro ao sétimo dia (n = {EXP["n_pareados"]} atletas pareados)',
            fontsize=11.6, loc='left', fontweight='bold')
gx(a)
rod(fig, 'Barra clara: totalidade dos atletas que começaram no perfil, em D1 (sombra = 100%). Barra colorida: os '
        'que permaneceram nele em D7. Ordenado do que mais migra ao que menos migra; a barbatana de tubarão tem '
        'um único representante em D1 e a sua retenção de 100% não deve ser generalizada.', y=-.045)
fig.tight_layout(); salvar(fig, 'X3fig')

# ==================== X4: magnitude de mudança por transição ====================
MUD = EXP['MUDANCA']
fig, a = plt.subplots(figsize=(9.4, 4.6))
rots = [m['transicao'] for m in MUD]; vals = [m['soma_abs_pisos'] for m in MUD]
cores = ['#C1440E' if v > np.median(vals) else '#8A9299' for v in vals]
a.bar(range(6), vals, color=cores, width=.62, zorder=3)
for i, v in enumerate(vals):
    a.annotate(f"{vg(v,1)}", xy=(i, v), xytext=(0, 4), textcoords='offset points',
               ha='center', fontsize=10, fontweight='bold', color=INK)
a.set_xticks(range(6)); a.set_xticklabels(rots, fontsize=10.4)
a.set_ylabel('Soma dos módulos, em pisos de ruído\n(sete variáveis)', fontsize=10)
a.set_title('Magnitude de mudança em cada transição diária', fontsize=11.6, loc='left', fontweight='bold')
gy(a)
rod(fig, 'Quanto maior a barra, mais as sete variáveis se moveram, em conjunto, entre os dois dias.')
fig.tight_layout(); salvar(fig, 'X4fig')

# ==================== X5: magnitude do efeito, contraste D1×D7 ====================
import sqlite3
cxr = sqlite3.connect(os.path.join(RAIZ, "base", "humor_handebol.sqlite")); cxr.row_factory = sqlite3.Row
V11 = V7 + ['Fad.Física', 'Fad.Mental', 'Epworth', 'PSS']
EF = []
for v in V11:
    row = cxr.execute("SELECT p,efeito FROM resultado WHERE variavel=? AND recorte='D1–D7' "
                       "AND teste LIKE '%Wilcoxon%' AND via='não paramétrica'", (v,)).fetchone()
    if row: EF.append((v, row['efeito'], row['p']))
cxr.close()
EF.sort(key=lambda x: -abs(x[1]))
CVX = dict(CV); CVX.update({'Fad.Física': '#B3341A', 'Fad.Mental': '#5B3A99', 'Epworth': '#0F6E5C', 'PSS': '#87968F'})
fig, a = plt.subplots(figsize=(9.2, 6.2))
yy = np.arange(len(EF))[::-1]
for y, (v, r, p) in zip(yy, EF):
    cor = CVX.get(v, MUT)
    a.barh(y, abs(r), height=.62, color=cor, alpha=.90 if p < .05 else .35,
           edgecolor=cor, lw=1.4, zorder=3)
    a.annotate(f"{vg(abs(r),2)}{'  n.s.' if p >= .05 else ''}", xy=(abs(r), y), xytext=(6, 0),
               textcoords='offset points', va='center', fontsize=9.4,
               fontweight='bold' if p < .05 else 'normal', color=cor)
for lim, rot in [(.10, 'pequeno'), (.30, 'médio'), (.50, 'grande')]:
    a.axvline(lim, color=GRID, lw=1.1, ls='--', zorder=1)
a.set_yticks(yy); a.set_yticklabels([L(v) if v in V7 else v for v, _, _ in EF], fontsize=9.6)
a.set_xlabel('Tamanho de efeito |r|, contraste pareado D1×D7', fontsize=10.4)
a.set_xlim(0, max(abs(r) for _, r, _ in EF) * 1.18)
a.set_title('Magnitude do efeito entre o primeiro e o sétimo dia, por variável', fontsize=11.4,
            loc='left', fontweight='bold')
gx(a)
rod(fig, 'Linhas tracejadas: limiares de Cohen para r (pequeno 0,10; médio 0,30; grande 0,50). Barra clara: contraste sem significância.')
fig.tight_layout(); salvar(fig, 'X5fig')
