# -*- coding: utf-8 -*-
"""P1 a P3 — os seis perfis de humor: segmentados, combinados e onde predominam."""
exec(open(__file__.replace('UP1.py','UVh.py')).read())
import sqlite3
SERP=A3['SERP']; NOMES=PERF
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite")); cx.row_factory=sqlite3.Row
PREV_E={(r['recorte'],r['perfil']):r['prevalencia'] for r in
        cx.execute("SELECT recorte,perfil,prevalencia FROM prevalencia "
                   "WHERE recorte_tipo='estimulo' AND unidade='U-AD'")}
NPOR={r['recorte']:r['n'] for r in cx.execute(
    "SELECT DISTINCT recorte,n FROM prevalencia WHERE recorte_tipo='estimulo' AND unidade='U-AD'")}
cx.close()
ND=[27,26,26,21,23,22,21]

# ---------------- P1: pequenos múltiplos, um painel por perfil ----------------
fig,axs=plt.subplots(2,3,figsize=(14.2,7.0))
for i,nm in enumerate(NOMES):
    a=axs[i//3][i%3]; d=SERP[nm]; y=np.array(d['y']); se=np.array(d['se']); sm=np.array(d['sm'])
    marcar(a,alpha=.75)
    a.fill_between(x7, y-se, y+se, color=CPF[nm], alpha=.15, lw=0, zorder=2)
    a.plot(x7, y, 'o', ms=6.5, color=CPF[nm], mec=SURF, mew=1.5, zorder=4, alpha=.55)
    a.plot(x7, sm, '-', lw=2.8, color=CPF[nm], zorder=5)
    j=int(np.argmax(y))
    a.plot([x7[j]],[y[j]],'o',ms=12,mfc='none',mec=CPF[nm],mew=2.2,zorder=6)
    # o pico entra na linha de cabeçalho: no gráfico basta o círculo aberto
    ver = 'não avaliável' if d.get('fragil') else ('sinal' if d['sinal'] else 'ruído')
    a.text(.015,.965, nm, transform=a.transAxes, fontsize=11.4, fontweight='bold',
           color=CPF[nm], va='top')
    a.text(.015,.875, f"D1 {vg(y[0],1)}% → D7 {vg(y[6],1)}%   ·   Δ {vg(d['dtot'],1)} p.p.   ·   {ver}",
           transform=a.transAxes, fontsize=8.8, color=MUT, va='top')
    a.text(.015,.790, f"pico em D{j+1}, com {vg(y[j],1)}%",
           transform=a.transAxes, fontsize=8.8, color=CPF[nm], va='top', fontweight='bold')
    a.set_xticks(x7); a.set_xticklabels([f"D{d_}" for d_ in x7], fontsize=9)
    a.set_ylim(-4,64); gy(a)
    if i%3==0: a.set_ylabel('prevalência (%)')
fig.suptitle('Prevalência diária de cada perfil de humor ao longo do microciclo terminal',
             fontsize=12.4, fontweight='bold', x=.007, ha='left', y=1.010)
fig.legend(handles=[Patch(fc=FUN[t],ec='none',label=t) for t in ['Basal','HIIT','Amistoso','Técnico/força']],
           frameon=False, fontsize=9.4, ncol=4, loc='upper right', bbox_to_anchor=(.995,1.018))
plt.tight_layout(rect=[0,0,1,.965])
rod(fig,'Sobre os 166 pares atleta-dia; n por dia = 27, 26, 26, 21, 23, 22 e 21. Banda = erro-padrão binomial; '
        'linha grossa = série suavizada pelo filtro 1-2-1.\nO círculo aberto marca o dia de maior prevalência. '
        'O veredito compara o deslocamento total ao piso de ruído da própria série.', y=-.015)
salvar(fig,'P1fig')

# ---------------- P2: composição do elenco, dia a dia ----------------
fig,axs=plt.subplots(1,2,figsize=(13.8,4.8),gridspec_kw=dict(width_ratios=[2.15,1],wspace=.20))
a=axs[0]
Y=np.array([SERP[nm]['y'] for nm in NOMES])
Y=Y/Y.sum(0)*100
base=np.zeros(7)
for i,nm in enumerate(NOMES):
    a.fill_between(x7, base, base+Y[i], color=CPF[nm], alpha=.90, lw=.8, ec=SURF, zorder=3, label=nm)
    for d in range(7):
        if Y[i][d]>=7.5:
            ha_='left' if d==0 else 'right' if d==6 else 'center'
            dx_=0.06 if d==0 else -0.06 if d==6 else 0
            a.text(x7[d]+dx_, base[d]+Y[i][d]/2, vg(Y[i][d],0), ha=ha_, va='center',
                   fontsize=8.6, color=SURF, fontweight='bold', zorder=5)
    base=base+Y[i]
ABREV2={'Basal':'basal','HIIT':'HIIT','Amistoso':'amistoso','Técnico/força':'téc./força'}
a.set_xticks(x7); a.set_xticklabels([f"D{d}\n{ABREV2[TIPO[d]]}" for d in x7], fontsize=8.8)
a.set_xlim(1,7); a.set_ylim(0,100); a.set_ylabel('composição do elenco (%)')
a.set_title('a) Como o elenco se distribui entre os seis perfis, dia a dia',
            fontsize=11, loc='left', pad=10, fontweight='bold')
a.legend(frameon=False, fontsize=9, ncol=3, loc='upper center', bbox_to_anchor=(.5,-.20))
b=axs[1]
faixas=['Favorável','Neutra','De risco']
CFX={'Favorável':'#1A7F5A','Neutra':'#87968F','De risco':'#B3341A'}
for nm in faixas:
    d=SERP[nm]; b.plot(x7, d['sm'], '-', lw=3.0, color=CFX[nm], zorder=4, label=nm)
    b.plot(x7, d['y'], 'o', ms=5.5, color=CFX[nm], mec=SURF, mew=1.3, alpha=.5, zorder=5)
marcar(b,alpha=.75)
cross=None
fav=np.array(SERP['Favorável']['sm']); ris=np.array(SERP['De risco']['sm'])
sig=np.sign(fav-ris)
for d in range(6):
    if sig[d]!=sig[d+1]:
        t=abs(fav[d]-ris[d])/(abs(fav[d]-ris[d])+abs(fav[d+1]-ris[d+1])); cross=1+d+t
if cross:
    b.axvline(cross, color=INK, lw=1.4, ls=(0,(4,3)), zorder=6)
    b.annotate(f'inversão em D{vg(cross,2)}', (cross+.12, 58), ha='left', fontsize=9,
               color=INK, fontweight='bold')
b.set_xticks(x7); b.set_xticklabels([f"D{d}" for d in x7], fontsize=9)
b.set_ylim(0,62); gy(b); b.set_ylabel('prevalência (%)')
b.legend(frameon=False, fontsize=9.4, loc='lower right')
b.set_title('b) As três faixas e o ponto em que a de risco ultrapassa a favorável',
            fontsize=11, loc='left', pad=10, fontweight='bold')
rod(fig,'A composição do painel a soma 100% em cada dia. As faixas do painel b agregam os perfis: favorável '
        'reúne o iceberg; neutra, a superfície e o submerso;\nde risco, a barbatana de tubarão, o iceberg '
        'invertido e o Everest invertido.', y=-.16)
salvar(fig,'P2fig')

# ---------------- P3: onde cada perfil predomina ----------------
fig,axs=plt.subplots(1,2,figsize=(14.6,5.4),gridspec_kw=dict(width_ratios=[1.35,1],wspace=.30))
a=axs[0]; marcar(a,alpha=.75)
M=np.array([SERP[nm]['y'] for nm in NOMES])
fin={nm: M[i][6] for i,nm in enumerate(NOMES)}
ordem=sorted(NOMES, key=lambda k: fin[k]); yp={}; ult=None
for k in ordem:
    val=fin[k]
    if ult is not None and val-ult<3.4: val=ult+3.4
    yp[k]=val; ult=val
for i,nm in enumerate(NOMES):
    y=M[i]; j=int(np.argmax(y))
    a.plot(x7, y, '-', lw=2.6, color=CPF[nm], zorder=4, alpha=.92)
    a.plot(x7, y, 'o', ms=5.6, color=CPF[nm], mec=SURF, mew=1.3, zorder=5)
    a.plot([x7[j]],[y[j]],'o',ms=12,mfc='none',mec=CPF[nm],mew=2.2,zorder=6)
    a.annotate(nm, xy=(7.14, yp[nm]), fontsize=9.2, fontweight='bold', color=CPF[nm],
               va='center', ha='left', zorder=6)
    if abs(yp[nm]-fin[nm])>.3:
        a.plot([7.02,7.12],[fin[nm],yp[nm]],color=CPF[nm],lw=1.1,clip_on=False,zorder=3)
ABREV={'Basal':'basal','HIIT':'HIIT','Amistoso':'amistoso','Técnico/força':'téc./força'}
a.set_xticks(x7); a.set_xticklabels([f"D{d}\n{ABREV[TIPO[d]]}" for d in x7], fontsize=8.6)
a.set_xlim(.6,9.6); a.set_ylabel('prevalência (%)'); gy(a)
a.set_title('a) Prevalência por dia — o círculo aberto marca o pico de cada perfil',
            fontsize=11, loc='left', pad=10, fontweight='bold')

b=axs[1]
EST=['Basal','HIIT','Amistoso','Técnico/força']
w=.13; xb=np.arange(len(EST))
for k,nm in enumerate(NOMES):
    v=[PREV_E.get((t,nm), np.nan) for t in EST]
    b.bar(xb+(k-2.5)*w, v, width=w-.015, color=CPF[nm], alpha=.92, edgecolor=SURF, lw=.9, zorder=3, label=nm)
b.set_xticks(xb); b.set_xticklabels([f"{t}\nn = {NPOR.get(t,0)}" for t in EST], fontsize=8.8)
for t,e in zip(b.get_xticklabels(),EST): t.set_color(CEST[e]); t.set_fontweight('bold')
b.set_ylabel('prevalência (%)'); gy(b)
b.legend(frameon=False, fontsize=8.2, ncol=2, loc='upper center', bbox_to_anchor=(.5,-.20))
b.set_title('b) Prevalência por tipo de estímulo', fontsize=11, loc='left', pad=10, fontweight='bold')
rod(fig,f"Percentual dos pares atleta-dia de cada recorte. O dia basal e o dia técnico e de força ocorrem uma "
        f"única vez no microciclo, de modo que a coluna do estímulo\ne a do dia coincidem para eles: o basal é D1 "
        f"e o técnico e de força é D6. Associação entre estímulo e perfil: χ² = {vg(A3['chi'],2)}; "
        + pv(A3['p_chi']) + ".", y=-.06)
fig.tight_layout(); salvar(fig,'P3fig')
