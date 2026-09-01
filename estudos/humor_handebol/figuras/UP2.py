# -*- coding: utf-8 -*-
"""P4 a P6 — a assinatura dos seis perfis, a sua prevalência e o cruzamento
entre vigor, fadiga e perturbação total do humor.

P4: um painel por perfil, com o centroide observado neste elenco contra o
    centroide canônico de Parsons-Smith, Terry e Machin (2017), em escore T.
    Cinco painéis partilham o mesmo eixo; o Everest invertido, cujo centroide
    é a média de dois pares atleta-dia, recebe escala própria e declarada.
P5: os seis perfis sobrepostos, a comparação de prevalência com a referência
    e o dia em que cada perfil predomina.
P6: vigor, fadiga e perturbação total ao longo da semana, com os pontos de
    cruzamento e o teste formal de inversão.
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
CURTOEST={'Basal':'basal','HIIT':'HIIT','Amistoso':'amist.','Técnico/força':'téc/for'}
CURTO=['Tensão','Depres.','Raiva','Vigor','Fadiga','Confus.']
xs=np.arange(6)
# eixo comum: cabe os cinco perfis com mais de dois casos (37,7 a 86,1)
COM=(32,92); AMP=(32,130)
def pico_dia(nm):
    y=np.array(SERP[nm]['y']); j=int(np.argmax(y)); return j+1, y[j]
def pico_est(nm):
    v=[(PREV_E.get((t,nm),np.nan),t) for t in EST]
    v=[(x,t) for x,t in v if x==x]
    return max(v)[1], max(v)[0]

# =================== P4: a assinatura de cada perfil ===================
fig,axs=plt.subplots(2,3,figsize=(15.0,10.2))
fig.subplots_adjust(left=.055,right=.995,top=.855,bottom=.185,hspace=.60,wspace=.20)
for i,nm in enumerate(NOMES):
    a=axs[i//3][i%3]; co=CPF[nm]
    amplo = C[i].max()>COM[1] or CAN[i].max()>COM[1]
    lo,hi = AMP if amplo else COM
    a.axhspan(lo,50,color='#F4F7FA',zorder=0,lw=0)
    a.axhline(50,color=MUT,lw=1.2,ls=(0,(5,4)),zorder=2)
    if amplo:
        a.axhline(COM[1],color='#C9CDD1',lw=1.0,ls=(0,(2,3)),zorder=2)
        a.text(5.38, COM[1]+1.5, 'topo do eixo comum', fontsize=7.6, color=MUT,
               ha='right', va='bottom', style='italic', zorder=3)
    a.fill_between(xs, 50, C[i], where=C[i]>=50, color=co, alpha=.22, lw=0, zorder=3, interpolate=True)
    a.fill_between(xs, 50, C[i], where=C[i]<=50, color=co, alpha=.10, lw=0, zorder=3, interpolate=True)
    a.plot(xs, CAN[i], lw=1.8, color=MUT, ls=(0,(3,2.5)), zorder=4)
    a.plot(xs, CAN[i], 'o', ms=4.4, mfc=SURF, mec=MUT, mew=1.3, zorder=4)
    a.plot(xs, C[i], '-', lw=3.2, color=co, zorder=6)
    a.plot(xs, C[i], 'o', ms=8.2, color=co, mec=SURF, mew=1.8, zorder=7)
    for j,dy in ((int(np.argmax(C[i])), 13), (int(np.argmin(C[i])), -21)):
        # um vale rente ao piso do eixo colidiria com o rótulo do eixo x: sobe
        subiu = dy < 0 and (C[i][j]-lo)/(hi-lo) < .18
        if subiu: dy = 19
        a.annotate(vg(C[i][j],0), (xs[j], C[i][j]), textcoords='offset points',
                   xytext=(0, dy), ha='center', fontsize=9.4,
                   color=co, fontweight='bold', zorder=10,
                   bbox=dict(fc=SURF, ec='none', alpha=.88, pad=1.2) if subiu else None)
    # o cabeçalho fica ACIMA da área de dados: nunca colide com a curva
    d_,pd_=pico_dia(nm); e_,pe_=pico_est(nm)
    a.text(0,1.255, nm, transform=a.transAxes, fontsize=12.4, fontweight='bold', color=co, va='top')
    a.text(0,1.145, f"{vg(PREV[i],1)}% dos pares atleta-dia   ·   referência 2017: {vg(PREV_REF[i],1)}%",
           transform=a.transAxes, fontsize=9.0, color=MUT, va='top')
    a.text(0,1.055, f"predomina em D{d_} ({vg(pd_,1)}%) e nos dias de {ABREV[e_]} ({vg(pe_,1)}%)",
           transform=a.transAxes, fontsize=9.0, color=co, va='top', fontweight='bold')
    if amplo:
        a.text(1,1.255, 'escala própria', transform=a.transAxes, fontsize=9.0, color='#B3341A',
               va='top', ha='right', fontweight='bold')
    a.set_xticks(xs); a.set_xticklabels(CURTO, fontsize=9.4)
    for t,s_ in zip(a.get_xticklabels(),SUB): t.set_color(CV[s_])
    a.set_ylim(lo,hi); a.set_xlim(-.45,5.45)
    a.set_yticks(np.arange(40,hi+1,10) if not amplo else np.arange(40,hi+1,20)); gy(a)
    if i%3==0: a.set_ylabel('escore T (norma de atletas)')
fig.suptitle('Assinatura dos seis perfis de humor: o elenco contra a referência normativa',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.985)
fig.legend(handles=[Line2D([],[],color=INK,lw=3.2,label='centroide observado neste elenco'),
                    Line2D([],[],color=MUT,lw=1.8,ls=(0,(3,2.5)),marker='o',ms=4.4,
                           mfc=SURF,mec=MUT,label='centroide canônico (Parsons-Smith et al., 2017)'),
                    Line2D([],[],color=MUT,lw=1.2,ls=(0,(5,4)),label='média normativa (T = 50)')],
           frameon=False, fontsize=9.6, ncol=3, loc='upper left', bbox_to_anchor=(.004,.955))
rod(fig,'Escore T contra a norma de atletas de Terry e Lane (2000), em que 50 é a média e 10 o desvio-padrão '
        'da população de referência. Sobre os 166 pares atleta-dia.\nCinco painéis partilham o eixo de 32 a 92, '
        'que cobre por inteiro os cinco perfis com mais de dois casos. O Everest invertido reúne dois pares no '
        'conjunto e recebe escala própria,\nassinalada pela linha pontilhada no topo do eixo comum: o seu '
        'centroide é a média de duas observações e não deve ser lido como característica do elenco.', y=.135)
salvar(fig,'P4fig')

# =============== P5: os seis juntos, e onde predominam ===============
fig=plt.figure(figsize=(15.0,6.9))
gs=fig.add_gridspec(1,3,width_ratios=[1.45,1.05,.92],wspace=.34,
                    left=.045,right=.988,top=.830,bottom=.300)
a=fig.add_subplot(gs[0])
a.axhspan(AMP[0],50,color='#F4F7FA',zorder=0,lw=0)
a.axhline(50,color=MUT,lw=1.2,ls=(0,(5,4)),zorder=2)
for i in np.argsort([-C[k].mean() for k in range(6)]):
    a.plot(xs, C[i], '-', lw=3.0, color=CPF[NOMES[i]], zorder=5, alpha=.95,
           label=NOMES[i])
    a.plot(xs, C[i], 'o', ms=6.5, color=CPF[NOMES[i]], mec=SURF, mew=1.5, zorder=6)
a.set_xticks(xs); a.set_xticklabels(CURTO, fontsize=9.6)
for t,s_ in zip(a.get_xticklabels(),SUB): t.set_color(CV[s_])
a.set_ylim(AMP); a.set_yticks(np.arange(40,131,20)); gy(a)
a.set_xlim(-.45,5.45); a.set_ylabel('escore T')
_h,_l=a.get_legend_handles_labels()
_o=[_l.index(n) for n in NOMES]
a.legend([_h[k] for k in _o],[_l[k] for k in _o], frameon=False, fontsize=9.2, ncol=3,
         loc='upper left', bbox_to_anchor=(-.015,-.115), handlelength=1.6,
         columnspacing=1.4, labelspacing=.40)
a.set_title('a) Os seis perfis no mesmo eixo', fontsize=11.4, loc='left', pad=10, fontweight='bold')

b=fig.add_subplot(gs[1])
yy=np.arange(6)[::-1]
b.barh(yy+.19, PREV, height=.36, color=[CPF[n] for n in NOMES], zorder=3)
b.barh(yy-.19, PREV_REF, height=.36, color=GRID, ec=MUT, lw=.9, zorder=3)
for i in range(6):
    b.text(PREV[i]+.8, yy[i]+.19, vg(PREV[i],1), va='center', fontsize=9.2,
           color=CPF[NOMES[i]], fontweight='bold')
    b.text(PREV_REF[i]+.8, yy[i]-.19, vg(PREV_REF[i],1), va='center', fontsize=9.2, color=MUT)
    b.text(-1.2, yy[i], NOMES[i], va='center', ha='right', fontsize=9.4,
           color=CPF[NOMES[i]], fontweight='bold')
b.set_yticks(yy); b.set_yticklabels([]); b.tick_params(axis='y', length=0)
b.set_xlim(0,44); b.set_ylim(-.8,5.8); gx(b); b.set_xlabel('prevalência (%)')
b.set_title('b) Neste elenco e na referência', fontsize=11.4, loc='left', pad=10, fontweight='bold')
b.legend(handles=[Patch(fc=INK,ec='none',label='elenco'),
                  Patch(fc=GRID,ec=MUT,label='Parsons-Smith et al. (2017)')],
         frameon=False, fontsize=8.8, loc='lower right', bbox_to_anchor=(1.02,.035))

c=fig.add_subplot(gs[2])
for i,nm in enumerate(NOMES):
    y=np.array(SERP[nm]['y']); j=int(np.argmax(y))
    c.plot([1,7],[yy[i],yy[i]], '-', color=GRID, lw=1.4, zorder=2)
    c.scatter(x7, [yy[i]]*7, s=16+y*7.0, color=CPF[nm], alpha=.55, ec='none', zorder=3)
    c.scatter([j+1],[yy[i]], s=16+y[j]*7.0, facecolor='none', ec=INK, lw=2.0, zorder=5)
    c.text(j+1, yy[i]+.34, f"D{j+1}", ha='center', fontsize=8.6, color=INK, fontweight='bold')
c.set_yticks(yy); c.set_yticklabels([]); c.set_ylim(-.8,5.8)
c.set_xticks(x7); c.set_xticklabels([f"D{d}\n{CURTOEST[TIPO[d]]}" for d in x7], fontsize=8.0)
c.set_xlim(.4,7.6)
for s_ in ('left','bottom'): c.spines[s_].set_visible(False)
c.tick_params(length=0)
c.set_title('c) Em que dia cada perfil predomina', fontsize=11.4, loc='left', pad=10, fontweight='bold')
fig.suptitle('Os seis perfis de humor lado a lado: forma, prevalência e dia de predomínio',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.975)
rod(fig,'Os painéis b e c partilham a mesma ordem de linhas. No painel c o diâmetro do círculo é proporcional '
        'à prevalência do perfil naquele dia, e o círculo aberto marca o dia de maior prevalência.\nA '
        'referência de prevalência provém da amostra A (n = 2.364) de Parsons-Smith, Terry e Machin (2017).', y=.085)
salvar(fig,'P5fig')

# ====== P6: vigor, fadiga e perturbação total, e onde se cruzam ======
def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z
TRI=['Vigor','Fadiga','TMD']
SM={v:suav(A1['SER'][v]['med']) for v in TRI}
OB={v:np.array(A1['SER'][v]['med']) for v in TRI}
EP={v:np.array(A1['SER'][v]['ep']) for v in TRI}
PI={v:A1['SER'][v]['piso'] for v in TRI}
def par(a_,b_):
    d=SM[a_]-SM[b_]; lim=float(np.hypot(PI[a_],PI[b_])); cs=[]
    for i in range(6):
        if d[i]==0 or d[i]*d[i+1]<0: cs.append(1+i+abs(d[i])/(abs(d[i])+abs(d[i+1])))
    return d, lim, cs, bool(abs(d[0])>lim and abs(d[-1])>lim)
PARES=[('Vigor','Fadiga'),('Vigor','TMD'),('Fadiga','TMD')]
CPAR={('Vigor','Fadiga'):'#C1440E',('Vigor','TMD'):'#2166AC',('Fadiga','TMD'):'#8A4FBF'}

fig=plt.figure(figsize=(15.2,6.8))
gs=fig.add_gridspec(1,2,width_ratios=[1.30,1],wspace=.19,
                    left=.048,right=.988,top=.845,bottom=.215)

# ---- painel a: as três trajetórias
a=fig.add_subplot(gs[0]); marcar(a,alpha=.85)
for v in TRI:
    a.errorbar(x7, OB[v], yerr=EP[v], fmt='none', ecolor=CV[v], elinewidth=1.3,
               capsize=3.2, capthick=1.3, alpha=.55, zorder=3)
    a.plot(x7, OB[v], 'o', ms=5.6, color=CV[v], mec=SURF, mew=1.3, alpha=.60, zorder=4)
    a.plot(x7, SM[v], '-', lw=3.4, color=CV[v], zorder=5)
    a.annotate(L(v), (7, SM[v][-1]), textcoords='offset points', xytext=(10,0),
               ha='left', va='center', fontsize=11.0, color=CV[v], fontweight='bold', zorder=8)
# os três cruzamentos, rotulados na faixa livre da parte de baixo
ALT={('Vigor','Fadiga'):1.55, ('Vigor','TMD'):0.55, ('Fadiga','TMD'):-0.45}
for (u,w) in PARES:
    d,lim,cs,est = par(u,w); co=CPAR[(u,w)]
    for cpos in cs:
        k=int(np.floor(cpos))-1; t=cpos-np.floor(cpos)
        yv=SM[u][k]+t*(SM[u][k+1]-SM[u][k])
        yl=ALT[(u,w)]
        a.plot([cpos,cpos],[yl+.30,yv],color=co,lw=1.3,ls=(0,(3,3)),zorder=3)
        a.plot([cpos],[yv],'o',ms=13,mfc=SURF,mec=co,mew=2.6,zorder=9)
        a.annotate(f"{L(u)} × {L(w)}  ·  cruza em D{vg(cpos,2)}", (cpos, yl),
                   ha='center', va='center', fontsize=9.0, color=co, fontweight='bold',
                   zorder=10, bbox=dict(fc=SURF, ec=co, lw=1.0, alpha=.95,
                                        boxstyle='round,pad=.30'))
a.set_xticks(x7); a.set_xticklabels([f"D{d}\n{CURTOEST[TIPO[d]]}" for d in x7], fontsize=8.8)
a.set_xlim(.55,7.85); a.set_ylim(-1.6,10.2); gy(a)
a.set_ylabel('pontos da escala')
a.set_title('a) As três trajetórias e os pontos em que se cruzam',
            fontsize=11.4, loc='left', pad=10, fontweight='bold')
a.legend(handles=[Patch(fc=FUN[t],ec='#D5D9DC',lw=.8,label=t) for t in EST],
         frameon=False, fontsize=8.8, ncol=4, loc='upper right', bbox_to_anchor=(1.005,1.005))

# ---- painel b: a diferença de cada par contra o limiar
b=fig.add_subplot(gs[1])
DESL={('Vigor','Fadiga'):-26, ('Vigor','TMD'):-44, ('Fadiga','TMD'):-62}
for (u,w) in PARES:
    d,lim,cs,est = par(u,w); co=CPAR[(u,w)]
    b.plot([1,7],[ lim, lim], color=co, lw=1.1, ls=(0,(4,3)), alpha=.75, zorder=2)
    b.plot([1,7],[-lim,-lim], color=co, lw=1.1, ls=(0,(4,3)), alpha=.75, zorder=2)
    b.plot(x7, d, '-', lw=3.0, color=co, zorder=5,
           label=f"{L(u)} − {L(w)}   ·   limiar ±{vg(lim,2)}")
    b.plot(x7, d, 'o', ms=5.8, color=co, mec=SURF, mew=1.3, zorder=6)
    for cpos in cs:
        b.plot([cpos],[0],'o',ms=12,mfc=SURF,mec=co,mew=2.6,zorder=8)
        b.annotate(f"D{vg(cpos,2)}", (cpos,0), textcoords='offset points',
                   xytext=(0,DESL[(u,w)]), ha='center', fontsize=9.0, color=co,
                   fontweight='bold', zorder=9, arrowprops=dict(arrowstyle='-', color=co,
                   lw=.9, shrinkA=1, shrinkB=6),
                   bbox=dict(fc=SURF, ec=co, lw=1.0, alpha=.95, boxstyle='round,pad=.26'))
    b.annotate('inversão estabelecida' if est else 'divergência',
               (7, d[-1]), textcoords='offset points', xytext=(10,0), ha='left', va='center',
               fontsize=8.8, color=co if est else MUT, fontweight='bold' if est else 'normal', zorder=9)
b.axhline(0,color=INK,lw=1.4,zorder=4)
b.set_xticks(x7); b.set_xticklabels([f"D{d}" for d in x7], fontsize=9)
b.set_xlim(.55,8.75); b.set_ylim(-6.6,9.6); gy(b)
b.set_ylabel('diferença entre as séries (pontos)')
b.set_title('b) A diferença de cada par contra o seu limiar combinado',
            fontsize=11.4, loc='left', pad=10, fontweight='bold')
b.legend(frameon=False, fontsize=9.0, loc='upper right', bbox_to_anchor=(1.005,1.00))

fig.suptitle('Vigor, fadiga e perturbação total do humor: onde as trajetórias se cruzam',
             fontsize=12.8, fontweight='bold', x=.006, ha='left', y=.972)
rod(fig,'Painel a: pontos = médias diárias observadas com o respectivo erro-padrão; linha grossa = série '
        'suavizada pelo filtro binomial 1-2-1. O círculo aberto marca o cruzamento, obtido por interpolação '
        'linear entre os dois dias que o cercam.\nPainel b: as linhas tracejadas delimitam o limiar combinado '
        'de cada par, definido como a raiz da soma dos quadrados dos dois pisos de ruído. A inversão só é '
        'declarada estabelecida quando a diferença\nsupera o limiar antes e depois do cruzamento; do contrário, '
        'a troca de posição é classificada como divergência.', y=.150)
salvar(fig,'P6fig')
