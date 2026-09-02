# -*- coding: utf-8 -*-
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UVh.py")).read())
PAR=B['pares']; dia=np.array([p['dia'] for p in PAR])
X={v:np.array([p[v] for p in PAR],float) for v in V7}
D=A1['DESC']

# ============ F3: distribuição das sete variáveis e efeito de piso ============
fig,ax=plt.subplots(1,2,figsize=(16.8,6.4),gridspec_kw={'width_ratios':[1.5,1.0]})
a=ax[0]
rng=np.random.default_rng(3)
for i,v in enumerate(V7):
    x=X[v]; c=CV[v]
    y=i+rng.normal(0,.085,len(x))
    a.scatter(x,y,s=13,color=c,alpha=.28,zorder=2,lw=0)
    q1,md,q3=np.percentile(x,[25,50,75])
    a.add_patch(Rectangle((q1,i-.20),q3-q1,.40,fc='white',ec=c,lw=2.2,zorder=3))
    a.plot([md,md],[i-.20,i+.20],color=c,lw=3.4,zorder=4)
    a.plot([D[v]['tm']],[i],marker='D',ms=8,color='#2A2F33',zorder=5,mfc='white',mew=2)
    a.annotate(f"md {vg(md)} · apar. {vg(D[v]['tm'])}",xy=(x.max()+.6,i),va='center',
               fontsize=9.2,color=c,fontweight='bold')
a.set_yticks(range(7)); a.set_yticklabels([L(v) for v in V7],fontsize=11)
for t,v in zip(a.get_yticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
a.set_xlim(-11,63); a.set_xlabel('Escore bruto',fontsize=11)
a.set_title('(A) Distribuição das sete variáveis nos 166 pares atleta-dia',fontsize=12,loc='left',fontweight='bold')
a.annotate('caixa = quartis · traço = mediana · losango = média aparada a 20%',
           xy=(.99,.03),xycoords='axes fraction',ha='right',fontsize=9,color=MUT,style='italic')
gx(a)
a2=ax[1]
piso=[D[v]['piso'] for v in V7]; ordem=np.argsort(piso)[::-1]
yb=np.arange(7)
a2.axvline(15,color='#C1440E',lw=1.8,ls='--',zorder=4)
for k,i in enumerate(ordem):
    v=V7[i]
    a2.barh(yb[k],piso[i],height=.6,color=CV[v],alpha=.92 if piso[i]>15 else .35,
            edgecolor=CV[v],lw=1.8,zorder=3)
    a2.annotate(f"{vg(piso[i])}%",xy=(piso[i],yb[k]),xytext=(7,0),textcoords='offset points',
                va='center',fontsize=10,fontweight='bold' if piso[i]>15 else 'normal',color=CV[v])
a2.set_yticks(yb); a2.set_yticklabels([L(V7[i]) for i in ordem],fontsize=11)
for t,i in zip(a2.get_yticklabels(),ordem): t.set_color(CV[V7[i]]); t.set_fontweight('bold')
a2.invert_yaxis(); a2.set_xlim(0,78); a2.set_xlabel('Respostas no valor mínimo da escala (%)',fontsize=11)
a2.set_title('(B) Efeito de piso',fontsize=12,loc='left',fontweight='bold')
a2.annotate('linha vermelha: limite de 15%\n(Terwee et al., 2007)',xy=(.97,.06),xycoords='axes fraction',
            ha='right',va='bottom',fontsize=9.4,color=INK,linespacing=1.4,
            bbox=dict(boxstyle='round,pad=.4',fc='#FFFFFF',ec='#8A9299',lw=1.2))
gx(a2)
rod(fig,'Quatro das seis subescalas concentram mais de 40% das respostas no zero: há margem para piorar, quase nenhuma para melhorar.')
fig.tight_layout(); salvar(fig,'F3fig')

# ============ F4: trajetória em escore T e teste de tendência ============
fig,ax=plt.subplots(1,2,figsize=(16.8,6.4),gridspec_kw={'width_ratios':[1.45,1.0]})
a=ax[0]; marcar(a); a.axhline(50,color='#8A9299',lw=1.5,ls='--',zorder=2)
fin={}
for v in SUB:
    y=[Tv(v,A1['SER'][v]['med'][d-1]) for d in range(1,8)]
    a.plot(x7,y,'-o',color=CV[v],lw=3.4,ms=8,mfc='white',mew=2.4,zorder=4); fin[v]=y[-1]
ordem=sorted(SUB,key=lambda k:fin[k]); yp={}; ult=None
for k in ordem:
    val=fin[k]
    if ult is not None and val-ult<1.4: val=ult+1.4
    yp[k]=val; ult=val
for k in SUB:
    a.annotate(k,xy=(7.14,yp[k]),fontsize=10.8,fontweight='bold',color=CV[k],va='center',ha='left')
    if abs(yp[k]-fin[k])>.12: a.plot([7.02,7.12],[fin[k],yp[k]],color=CV[k],lw=1.2,clip_on=False,zorder=3)
a.set_xlim(.5,8.9); a.set_xticks(x7); a.set_xticklabels([f'D{d}' for d in x7],fontsize=11)
a.set_ylabel('Escore T (norma externa de atletas)',fontsize=11)
a.set_title('(A) Trajetória das seis subescalas',fontsize=12,loc='left',fontweight='bold')
a.legend(handles=[Patch(fc=FUN[t],ec=CEST[t],lw=1.4,label=r) for t,r in
                  [('Basal','Basal (D1)'),('HIIT','HIIT (D2, D4, D7)'),
                   ('Amistoso','Amistoso (D3, D5)'),('Técnico/força','Técnico/força (D6)')]],
         fontsize=9.6,frameon=False,ncol=4,loc='upper center',bbox_to_anchor=(.5,-.085))
gy(a)
a2=ax[1]; NP=A2['NP']
ord2=sorted(SUB,key=lambda k:NP[k]['z']); yb=np.arange(6)
a2.axvspan(-1.96,1.96,color='#F3F4F5',zorder=0); a2.axvline(0,color='#8A9299',lw=1.3,zorder=2)
for i,k in enumerate(ord2):
    z=NP[k]['z']; p=NP[k]['pz']; sig=p<.05
    a2.barh(yb[i],z,height=.56,color=CV[k],alpha=.92 if sig else .28,edgecolor=CV[k],lw=1.8,zorder=3)
    a2.annotate(f'z = {vg(z,2)}\n{pv(p)}',xy=(z,yb[i]),xytext=(7 if z>0 else -7,0),
                textcoords='offset points',ha='left' if z>0 else 'right',va='center',
                fontsize=9.2,fontweight='bold',color=INK,linespacing=1.35)
a2.set_yticks(yb); a2.set_yticklabels(ord2,fontsize=11)
for t,k in zip(a2.get_yticklabels(),ord2): t.set_color(CV[k]); t.set_fontweight('bold')
a2.set_xlim(-5.0,5.0); a2.set_xlabel('z do teste de tendência de Page',fontsize=11)
a2.set_title('(B) Tendência ordenada D1→D7',fontsize=12,loc='left',fontweight='bold')
a2.annotate('faixa cinza: |z| < 1,96',xy=(.60,.05),xycoords='axes fraction',fontsize=9,color=MUT,style='italic')
gx(a2)
rod(fig,'166 pares atleta-dia. T = 50 é a média normativa; fadiga alta e vigor baixo indicam pior estado.')
fig.tight_layout(); salvar(fig,'F4fig')

# ============ F5: sinal, ruído e suavização ============
fig,ax=plt.subplots(2,3,figsize=(17.2,9.0))
for i,v in enumerate(SUB):
    a=ax[i//3][i%3]; marcar(a,alpha=.75)
    d=A1['SER'][v]; m=np.array(d['med']); ep=np.array(d['ep']); sm=np.array(d['sm']); pi=d['piso']
    a.fill_between(x7,m-ep,m+ep,color=CV[v],alpha=.16,zorder=2,lw=0)
    a.plot(x7,m,'-o',color=CV[v],lw=1.6,ms=6,alpha=.45,zorder=3,mfc='white',mew=1.4)
    a.plot(x7,sm,'-',color=CV[v],lw=4.2,zorder=4,solid_capstyle='round')
    a.axhline(sm[0],color=MUT,lw=1.2,ls='--',zorder=2)
    a.axhspan(sm[0]-pi,sm[0]+pi,color='#6B7378',alpha=.11,zorder=1,lw=0)
    for c in d['choque']:
        a.plot([c,c+1],[sm[c-1],sm[c]],lw=9.0,color=CV[v],alpha=.26,zorder=3,solid_capstyle='round')
        a.plot([c,c+1],[sm[c-1],sm[c]],lw=1.9,color='#2A2F33',ls=(0,(1.1,1.5)),zorder=6)
        a.plot([(2*c+1)/2],[(sm[c-1]+sm[c])/2],marker='o',ms=8.5,mfc='#2A2F33',mec='white',mew=1.8,zorder=7)
    a.set_xlim(.5,7.5); a.set_xticks(x7); a.set_xticklabels([f'D{k}' for k in x7],fontsize=9.6)
    if i%3==0: a.set_ylabel('Escore bruto (0–16)',fontsize=10)
    a.text(.035,.94,v,transform=a.transAxes,fontsize=12.5,fontweight='bold',color=CV[v],va='top')
    y0,y1=a.get_ylim(); a.set_ylim(y0-(y1-y0)*.11,y1); y0,y1=a.get_ylim()
    baixo=(sm[0]-y0)/(y1-y0)<.40
    a.text(.035,.79 if baixo else .045,
           f"Δ D1→D7 = {vg(d['dtot'],2)}\npiso = ±{vg(pi,2)}  ·  |Δ|/piso = {vg(d['razao'],1)}",
           transform=a.transAxes,fontsize=9.3,color=MUT,va='top' if baixo else 'bottom',linespacing=1.45)
    a.add_patch(Rectangle((.72,.885),.25,.095,transform=a.transAxes,zorder=6,
                fc=CV[v] if d['sinal'] else '#FFFFFF',ec=CV[v],lw=1.8))
    a.text(.845,.9325,'SINAL' if d['sinal'] else 'RUÍDO',transform=a.transAxes,fontsize=10,
           fontweight='bold',ha='center',va='center',color='white' if d['sinal'] else CV[v],zorder=7)
    gy(a)
fig.legend(handles=[Line2D([],[],color=MUT,lw=1.6,marker='o',mfc='white',alpha=.5,label='série observada ± EPM'),
  Line2D([],[],color=MUT,lw=4.2,label='série suavizada (filtro binomial 1-2-1)'),
  Patch(fc='#6B7378',alpha=.22,label='banda do piso de ruído em torno do basal'),
  Line2D([],[],color='#2A2F33',lw=1.9,ls=(0,(1.1,1.5)),marker='o',ms=8.5,mfc='#2A2F33',mec='white',
         mew=1.8,label='transição de choque (|1.ª derivada| > piso)')],
  fontsize=10,frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.015))
fig.suptitle('Decomposição sinal–ruído das seis subescalas do BRUMS',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.005)
fig.tight_layout(rect=[0,.035,1,.99]); salvar(fig,'F5fig')

# ============ F6: derivadas normalizadas pelo piso, em linha ============
fig,ax=plt.subplots(1,2,figsize=(16.4,6.2))
D1=np.array([[A1['SER'][v]['d1'][t]/A1['SER'][v]['piso'] for t in range(6)] for v in SUB])
D2=np.array([[A1['SER'][v]['d2'][t]/A1['SER'][v]['piso'] for t in range(5)] for v in SUB])
xv=np.arange(1,7); xa=np.arange(2,7)
for idx,(M,xx,tit,xlab) in enumerate([
        (D1,xv,'(A) 1.ª derivada — velocidade diária',[f'D{d}→D{d+1}' for d in range(1,7)]),
        (D2,xa,'(B) 2.ª derivada — aceleração',[f'em D{d}' for d in range(2,7)])]):
    a=ax[idx]
    a.axhspan(-1,1,color=INK,alpha=.07,zorder=1,lw=0)
    a.axhline(0,color=MUT,lw=1.2,zorder=2)
    for k in (1,-1): a.axhline(k,color='#8A9299',lw=1.0,ls=(0,(4,3)),zorder=2)
    fin={v:M[SUB.index(v)][-1] for v in SUB}; rng=fin[max(fin,key=fin.get)]-fin[min(fin,key=fin.get)]
    gap=max(rng*.075,.14)
    ordem=sorted(SUB,key=lambda k:fin[k]); yp={}; ult=None
    for k in ordem:
        val=fin[k]
        if ult is not None and val-ult<gap: val=ult+gap
        yp[k]=val; ult=val
    for v in SUB:
        y=M[SUB.index(v)]
        a.plot(xx,y,'-o',color=CV[v],lw=2.4,ms=6.4,mfc=SURF,mec=CV[v],mew=1.7,zorder=4,alpha=.92)
        forte=np.abs(y)>1
        if forte.any():
            a.plot(xx[forte],y[forte],'o',ms=11,mfc='none',mec=CV[v],mew=2.0,zorder=5)
        a.annotate(L(v),xy=(xx[-1]+.32,yp[v]),fontsize=9.6,fontweight='bold',color=CV[v],
                   va='center',ha='left',zorder=6)
        if abs(yp[v]-fin[v])>gap*.15:
            a.plot([xx[-1]+.06,xx[-1]+.28],[fin[v],yp[v]],color=CV[v],lw=1.0,clip_on=False,zorder=3)
    a.set_xticks(xx); a.set_xticklabels(xlab,fontsize=9.6)
    a.set_xlim(xx[0]-.4,xx[-1]+1.55)
    a.set_ylabel('derivada, em unidades do piso de ruído',fontsize=10.2)
    a.set_title(tit,fontsize=12,loc='left',fontweight='bold')
    gy(a)
rod(fig,'Faixa sombreada e linhas tracejadas: ±1 piso de ruído — a variação que a amostragem, sozinha, já produz. '
        'Círculo aberto: dia em que a derivada excede essa faixa. A 2.ª derivada é avaliada no dia central de cada '
        'par de transições.',y=-.04)
fig.suptitle('Derivadas padronizadas pelo piso de ruído de cada subescala',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.02)
fig.tight_layout(); salvar(fig,'F6fig')
