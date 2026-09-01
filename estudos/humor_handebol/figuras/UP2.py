# -*- coding: utf-8 -*-
"""P4 e P5 — a assinatura dos seis perfis de humor e a sua prevalência.

P4: um painel por perfil, com o centroide observado neste elenco contra o
    centroide canônico de Parsons-Smith, Terry e Machin (2017), em escore T.
P5: os seis perfis sobrepostos em um único eixo, a comparação de prevalência
    com a referência e o dia e o estímulo em que cada um predomina.
"""
exec(open(__file__.replace('UP2.py','UVh.py')).read())
import sqlite3, collections

C=np.array(Q['C']); CAN=np.array(Q['CAN']); NOMES=PERF
PREV_REF=Q['PREV_REF']; lab=Q['lab_AD']; nAD=len(lab)
cnt=collections.Counter(lab); PREV=[100*cnt[i]/nAD for i in range(6)]
SERP=A3['SERP']
cx=sqlite3.connect(os.path.join(RAIZ,"base","humor_handebol.sqlite")); cx.row_factory=sqlite3.Row
PREV_E={(r['recorte'],r['perfil']):r['prevalencia'] for r in
        cx.execute("SELECT recorte,perfil,prevalencia FROM prevalencia "
                   "WHERE recorte_tipo='estimulo' AND unidade='U-AD'")}
cx.close()
EST=['Basal','HIIT','Amistoso','Técnico/força']
ABREV={'Basal':'basal','HIIT':'HIIT','Amistoso':'amistoso','Técnico/força':'téc./força'}
CURTO=['Tensão','Depres.','Raiva','Vigor','Fadiga','Confus.']
xs=np.arange(6)
YMIN,YMAX=28,140

def pico_dia(nm):
    y=np.array(SERP[nm]['y']); j=int(np.argmax(y)); return j+1, y[j]
def pico_est(nm):
    v=[(PREV_E.get((t,nm),np.nan),t) for t in EST]
    v=[(x,t) for x,t in v if x==x]
    return max(v)[1], max(v)[0]

# =============== P4: a assinatura de cada perfil ===============
fig,axs=plt.subplots(2,3,figsize=(14.6,8.4))
for i,nm in enumerate(NOMES):
    a=axs[i//3][i%3]; co=CPF[nm]
    a.axhspan(YMIN,50,color='#F4F7FA',zorder=0,lw=0)
    a.axhline(50,color=MUT,lw=1.2,ls=(0,(5,4)),zorder=2)
    a.fill_between(xs, 50, C[i], where=C[i]>=50, color=co, alpha=.22, lw=0, zorder=3,
                   interpolate=True)
    a.fill_between(xs, 50, C[i], where=C[i]<=50, color=co, alpha=.10, lw=0, zorder=3,
                   interpolate=True)
    a.plot(xs, CAN[i], lw=1.8, color=MUT, ls=(0,(3,2.5)), zorder=4)
    a.plot(xs, CAN[i], 'o', ms=4.2, mfc=SURF, mec=MUT, mew=1.3, zorder=4)
    a.plot(xs, C[i], '-', lw=3.2, color=co, zorder=6)
    a.plot(xs, C[i], 'o', ms=8.0, color=co, mec=SURF, mew=1.8, zorder=7)
    jmax=int(np.argmax(C[i])); jmin=int(np.argmin(C[i]))
    for j,rot in [(jmax,'top'),(jmin,'bot')]:
        # um pico muito alto invadiria a linha de cabeçalho: o rótulo desce
        dy = (-19 if C[i][j] > 105 else 11) if rot=='top' else -19
        a.annotate(vg(C[i][j],0), (xs[j], C[i][j]), textcoords='offset points',
                   xytext=(0, dy), ha='center', fontsize=9.2, color=co,
                   fontweight='bold', zorder=8,
                   bbox=dict(fc=SURF, ec='none', alpha=.86, pad=1.2))
    d_,pd_=pico_dia(nm); e_,pe_=pico_est(nm)
    a.text(.015,.975, nm, transform=a.transAxes, fontsize=12.0, fontweight='bold',
           color=co, va='top', bbox=dict(fc=SURF, ec='none', alpha=.86, pad=1.6), zorder=9)
    a.text(.015,.895, f"{vg(PREV[i],1)}% do elenco-dia   ·   referência 2017: {vg(PREV_REF[i],1)}%",
           transform=a.transAxes, fontsize=8.9, color=MUT, va='top', bbox=dict(fc=SURF, ec='none', alpha=.86, pad=1.6), zorder=9)
    a.text(.015,.828, f"predomina em D{d_} ({vg(pd_,1)}%) e nos dias de {ABREV[e_]} ({vg(pe_,1)}%)",
           transform=a.transAxes, fontsize=8.9, color=co, va='top', fontweight='bold', bbox=dict(fc=SURF, ec='none', alpha=.86, pad=1.6), zorder=9)
    a.set_xticks(xs); a.set_xticklabels(CURTO, fontsize=9.2)
    for t,s in zip(a.get_xticklabels(),SUB): t.set_color(CV[s])
    a.set_ylim(YMIN,YMAX); a.set_yticks([30,50,70,90,110,130]); gy(a)
    a.set_xlim(-.45,5.45)
    if i%3==0: a.set_ylabel('escore T (norma de atletas)')
fig.suptitle('Assinatura dos seis perfis de humor: o elenco contra a referência normativa',
             fontsize=12.6, fontweight='bold', x=.007, ha='left', y=1.060)
fig.legend(handles=[Line2D([],[],color=INK,lw=3.2,label='centroide observado neste elenco'),
                    Line2D([],[],color=MUT,lw=1.8,ls=(0,(3,2.5)),marker='o',ms=4.2,
                           mfc=SURF,mec=MUT,label='centroide canônico (Parsons-Smith et al., 2017)'),
                    Line2D([],[],color=MUT,lw=1.2,ls=(0,(5,4)),label='média normativa (T = 50)')],
           frameon=False, fontsize=9.4, ncol=3, loc='upper left', bbox_to_anchor=(.005,1.022))
plt.tight_layout(rect=[0,0,1,.955])
rod(fig,'Escore T calculado contra a norma de atletas de Terry e Lane (2000), em que 50 é a média e 10 o '
        'desvio-padrão da população de referência. Sobre os 166 pares atleta-dia.\nO iceberg tem vigor acima '
        'de 50 e as cinco dimensões negativas abaixo; o iceberg invertido e o Everest invertido espelham essa '
        'figura; a barbatana de tubarão combina fadiga alta com vigor baixo.', y=-.012)
salvar(fig,'P4fig')

# =============== P5: os seis juntos, e onde predominam ===============
fig=plt.figure(figsize=(14.6,5.6))
gs=fig.add_gridspec(1,3,width_ratios=[1.55,1,1],wspace=.28)

a=fig.add_subplot(gs[0])
a.axhspan(YMIN,50,color='#F4F7FA',zorder=0,lw=0)
a.axhline(50,color=MUT,lw=1.2,ls=(0,(5,4)),zorder=2)
ordem=np.argsort([-C[i].mean() for i in range(6)])
for i in ordem:
    a.plot(xs, C[i], '-', lw=3.0, color=CPF[NOMES[i]], zorder=5, label=NOMES[i], alpha=.95)
    a.plot(xs, C[i], 'o', ms=6.5, color=CPF[NOMES[i]], mec=SURF, mew=1.5, zorder=6)
a.set_xticks(xs); a.set_xticklabels(CURTO, fontsize=9.6)
for t,s in zip(a.get_xticklabels(),SUB): t.set_color(CV[s])
a.set_ylim(YMIN,YMAX); a.set_yticks([30,40,50,60,70,80,90,100,110,120]); gy(a)
a.set_xlim(-.45,5.45); a.set_ylabel('escore T')
a.set_title('a) Os seis perfis no mesmo eixo', fontsize=11.2, loc='left', pad=10, fontweight='bold')
a.legend(frameon=False, fontsize=9, ncol=2, loc='upper left', bbox_to_anchor=(.015,.985))

b=fig.add_subplot(gs[1])
yy=np.arange(6)[::-1]
b.barh(yy+.19, PREV, height=.36, color=[CPF[n] for n in NOMES], zorder=3)
b.barh(yy-.19, PREV_REF, height=.36, color=GRID, ec=MUT, lw=.9, zorder=3)
for i in range(6):
    b.text(PREV[i]+.7, yy[i]+.19, vg(PREV[i],1), va='center', fontsize=9,
           color=CPF[NOMES[i]], fontweight='bold')
    b.text(PREV_REF[i]+.7, yy[i]-.19, vg(PREV_REF[i],1), va='center', fontsize=9, color=MUT)
b.set_yticks(yy); b.set_yticklabels(NOMES, fontsize=9.6)
for t,nm in zip(b.get_yticklabels(),NOMES): t.set_color(CPF[nm]); t.set_fontweight('bold')
b.set_xlim(0,42); b.set_ylim(-.8,5.8); gx(b); b.set_xlabel('prevalência (%)')
b.tick_params(axis='y', pad=6)
b.set_title('b) Neste elenco e na referência', fontsize=11.2, loc='left', pad=10, fontweight='bold')
b.legend(handles=[Patch(fc=INK,ec='none',label='elenco'),
                  Patch(fc=GRID,ec=MUT,label='Parsons-Smith et al. (2017)')],
         frameon=False, fontsize=8.8, loc='lower right')

c=fig.add_subplot(gs[2])
for i,nm in enumerate(NOMES):
    y=np.array(SERP[nm]['y']); j=int(np.argmax(y))
    c.plot([1,7],[yy[i],yy[i]], '-', color=GRID, lw=1.4, zorder=2)
    c.scatter(x7, [yy[i]]*7, s=18+y*7.5, color=CPF[nm], alpha=.55, ec='none', zorder=3)
    c.scatter([j+1],[yy[i]], s=18+y[j]*7.5, facecolor='none', ec=INK, lw=2.0, zorder=5)
    c.text(j+1, yy[i]+.32, f"D{j+1}", ha='center', fontsize=8.6, color=INK, fontweight='bold')
c.set_yticks(yy); c.set_yticklabels([]); c.set_ylim(-.8,5.8)
CURTOEST={'Basal':'basal','HIIT':'HIIT','Amistoso':'amist.','Técnico/força':'téc/for'}
c.set_xticks(x7); c.set_xticklabels([f"D{d}\n{CURTOEST[TIPO[d]]}" for d in x7], fontsize=8.0)
c.set_xlim(.4,7.6)
for s in ('left','bottom'): c.spines[s].set_visible(False)
c.tick_params(axis='y',length=0); c.tick_params(axis='x',length=0)
c.set_title('c) Em que dia cada perfil predomina', fontsize=11.2, loc='left', pad=10, fontweight='bold')
fig.suptitle('Os seis perfis de humor lado a lado: forma, prevalência e dia de predomínio',
             fontsize=12.6, fontweight='bold', x=.007, ha='left', y=1.015)
fig.subplots_adjust(left=.045,right=.995,top=.855,bottom=.145)
rod(fig,'Os painéis b e c partilham a mesma ordem de linhas. No painel c o diâmetro do círculo é proporcional '
        'à prevalência do perfil naquele dia, e o círculo aberto marca o dia de maior prevalência.\nA '
        'referência de prevalência provém da amostra A (n = 2.364) de Parsons-Smith, Terry e Machin (2017).', y=-.11)
salvar(fig,'P5fig')
