# -*- coding: utf-8 -*-
import os, textwrap as tw
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UVh.py")).read())
NP=A2['NP']; PA=A2['PA']; LMM=A3['LMM']; D=A1['DESC']
TIPOS=['HIIT','Amistoso','Técnico/força']

# ============ G1: as três vias e a árvore de decisão ============
fig=plt.figure(figsize=(17.4,9.4)); gs=fig.add_gridspec(2,1,height_ratios=[1.0,1.15],hspace=.16)
a=fig.add_subplot(gs[0]); a.axis('off'); a.set_xlim(0,100); a.set_ylim(0,100)
a.text(0,98,'(A) As três vias de análise aplicadas à mesma hipótese',fontsize=13,fontweight='bold',va='top')
VIAS=[('Não paramétrica','#2166AC','Friedman + W de Kendall\nL de Page\nWilcoxon + Holm',
       'usa postos; imune à assimetria\ne ao efeito de piso',
       'exige casos completos:\n19 dos 27 atletas (70% descartados)'),
      ('Paramétrica clássica','#E0952B','ANOVA de medidas repetidas\nGreenhouse-Geisser\nt pareado',
       'estima magnitude (η²p, dz)\ne intervalos de confiança',
       'pressupõe normalidade e esfericidade;\ntambém exige casos completos'),
      ('Modelo linear misto','#1A9070','intercepto aleatório por atleta\nefeito fixo do dia\nCCI do atleta',
       'aproveita os 166 pares:\nnenhum atleta é descartado',
       'pressupõe resíduos aproximadamente\nnormais e efeito linear no dia')]
for i,(nome,cor,testes,forca,limite) in enumerate(VIAS):
    X=2+i*32.6
    a.add_patch(FancyBboxPatch((X,6),30,80,boxstyle="round,pad=0.7,rounding_size=1.8",
                fc='#FFFFFF',ec=cor,lw=2.6,zorder=3))
    a.add_patch(FancyBboxPatch((X,72),30,14,boxstyle="round,pad=0.7,rounding_size=1.8",fc=cor,ec=cor,lw=2.6,zorder=4))
    a.text(X+15,79,nome,fontsize=12.5,fontweight='bold',ha='center',va='center',color='white',zorder=5)
    a.text(X+15,60,testes,fontsize=10,ha='center',va='center',color=INK,zorder=5,linespacing=1.7)
    a.text(X+15,42,'força',fontsize=9,ha='center',color=cor,fontweight='bold',zorder=5)
    a.text(X+15,34,forca,fontsize=9.2,ha='center',va='center',color=INK,zorder=5,linespacing=1.5)
    a.text(X+15,21,'limite',fontsize=9,ha='center',color='#A31E52',fontweight='bold',zorder=5)
    a.text(X+15,13,limite,fontsize=9.2,ha='center',va='center',color=MUT,zorder=5,linespacing=1.5)
a2=fig.add_subplot(gs[1]); a2.axis('off'); a2.set_xlim(0,100); a2.set_ylim(0,100)
a2.text(0,99,'(B) Árvore de decisão adotada — qual via governa a conclusão',fontsize=13,fontweight='bold',va='top')
def cx_(x,y,w,h,txt,fc,ec,fs=9.6,bold=False):
    a2.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.55,rounding_size=1.5",fc=fc,ec=ec,lw=2.0,zorder=3))
    a2.text(x+w/2,y+h/2,txt,fontsize=fs,ha='center',va='center',color=INK,zorder=4,linespacing=1.5,
            fontweight='bold' if bold else 'normal')
def seta(x1,y1,x2,y2,rot=None,cor='#8A9299'):
    a2.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=14,lw=1.9,color=cor,zorder=2))
    if rot: a2.text((x1+x2)/2,(y1+y2)/2+2.4,rot,fontsize=9,ha='center',color=cor,fontweight='bold',zorder=5)
cx_(36,80,28,13,'A variável tem efeito de piso\nacima de 15%?','#F0F1F2','#6B7378',bold=True)
seta(43,79.5,26,68,'sim','#C1440E'); seta(57,79.5,74,68,'não','#1A9070')
cx_(10,55,32,13,'Distribuição fortemente assimétrica:\na via não paramétrica governa','#E7EFF7','#2166AC')
cx_(58,55,34,13,'Normalidade e esfericidade\nverificadas?','#F0F1F2','#6B7378',bold=True)
seta(70,54.5,56,42,'sim','#1A9070'); seta(84,54.5,90,42,'não','#C1440E')
cx_(40,29,32,13,'As três vias devem convergir;\nreportar magnitude com IC','#FDF3E4','#E0952B')
cx_(76,29,22,13,'Corrigir por\nGreenhouse-Geisser','#FBEAE3','#C1440E')
cx_(4,29,32,13,'Casos completos < 75% da amostra?','#F0F1F2','#6B7378',bold=True)
seta(26,54.5,20,42,'','#2166AC')
seta(20,28.5,26,15,'sim','#1A9070')
cx_(16,2,44,13,'Acrescentar o modelo misto: ele retém os 166 pares e\nrecupera o poder que o descarte de casos incompletos custa',
    '#E4F1EC','#1A9070',bold=True)
seta(56,28.5,44,15,'','#E0952B'); seta(87,28.5,52,15,'','#C1440E')
rod(fig,'A discordância entre vias não é ruído: ela informa qual pressuposto está sob tensão em cada variável.',y=-.02)
salvar(fig,'G1fig')

# ============ G2: confronto das três vias — o centro do artigo ============
fig,ax=plt.subplots(1,2,figsize=(17.2,6.6),gridspec_kw={'width_ratios':[1.20,1.0]})
a=ax[0]; vars_=V7; yb=np.arange(len(vars_))[::-1]
VIA=[('Friedman  (n = 19)','#2166AC',lambda v: NP[v]['p']),
     ('ANOVA-MR com GG  (n = 19)','#E0952B',lambda v: PA[v]['pGG']),
     ('Modelo misto  (n = 166)','#1A9070',lambda v: LMM[v].get('p'))]
a.axvspan(1e-6,.05,color='#E4F1EC',zorder=0)
a.axvline(.05,color='#1A9070',lw=1.8,ls='--',zorder=4)
for i,v in enumerate(vars_):
    ps=[f(v) for _,_,f in VIA]
    a.plot([min(ps),max(ps)],[yb[i],yb[i]],color='#C6CBCE',lw=2.4,zorder=3)
    if len({pp<.05 for pp in ps})>1:
        a.add_patch(Rectangle((2.2e-5,yb[i]-.34),1.2e-4,.68,fc='#A31E52',ec='none',zorder=6))
        a.annotate('discordam',xy=(1.9e-4,yb[i]),va='center',fontsize=9.4,fontweight='bold',color='#A31E52',zorder=6)
for j,(nome,cor,f) in enumerate(VIA):
    a.scatter([f(v) for v in vars_],[y+(1-j)*.24 for y in yb],s=155,color=cor,zorder=5,
              edgecolor='white',lw=1.8,label=nome)
a.set_xscale('log'); a.set_xlim(2e-5,1.35)
a.set_yticks(yb); a.set_yticklabels([L(v) for v in vars_],fontsize=11.5)
for t,v in zip(a.get_yticklabels(),vars_): t.set_color(CV[v]); t.set_fontweight('bold')
a.set_xlabel('valor de p (escala logarítmica)',fontsize=11)
a.set_title('(A) A mesma hipótese, três vias, sete variáveis',fontsize=12.5,loc='left',fontweight='bold')
a.legend(fontsize=10,frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.10))
a.annotate('faixa verde: p < 0,05   ·   exigir os sete dias completos descarta 88% das observações',
           xy=(.5,-.185),xycoords='axes fraction',ha='center',fontsize=9,color=MUT,style='italic')
gx(a)
a2=ax[1]
dz=[PA[v]['dz'] for v in vars_]
ep=[(PA[v]['ic'][1]-PA[v]['ic'][0])/2 for v in vars_]
sd=[abs((PA[v]['dif']/PA[v]['dz'])) if PA[v]['dz'] else 1 for v in vars_]
lo=[(PA[v]['ic'][0])/s_ for v,s_ in zip(vars_,sd)]; hi=[(PA[v]['ic'][1])/s_ for v,s_ in zip(vars_,sd)]
a2.axvline(0,color='#4A5257',lw=1.5,zorder=4)
for x_,lab_ in [(0.2,'pequeno'),(0.5,'médio'),(0.8,'grande')]:
    for sgn in (1,-1):
        a2.plot([sgn*x_,sgn*x_],[-.7,len(vars_)-.3],color='#DDE0E2',lw=1.2,ls=':',zorder=1)
    a2.annotate(lab_,xy=(x_,len(vars_)-.52),ha='center',fontsize=8.4,color=MUT,style='italic')
for i,v in enumerate(vars_):
    c=CV[v]; sig=PA[v]['pt']<.05
    a2.plot([lo[i],hi[i]],[yb[i],yb[i]],color=c,lw=3.0,solid_capstyle='round',
            alpha=.95 if sig else .38,zorder=3)
    a2.plot([dz[i]],[yb[i]],'o',ms=13,color=c,zorder=5,mec='white',mew=2,alpha=.95 if sig else .38)
    a2.annotate(f"dz = {vg(dz[i],2)}"+("  *" if sig else ""),
                xy=(2.02,yb[i]),ha='right',va='center',fontsize=9.8,
                fontweight='bold' if sig else 'normal',color=c)
a2.set_yticks(yb); a2.set_yticklabels([L(v) for v in vars_],fontsize=11.5)
for t,v in zip(a2.get_yticklabels(),vars_): t.set_color(CV[v]); t.set_fontweight('bold')
a2.set_xlim(-2.1,3.1); a2.set_ylim(-.7,len(vars_)-.3)
a2.set_xlabel('Tamanho de efeito padronizado do contraste D1→D7 (dz), com IC 95%',fontsize=10.6)
a2.set_title('(B) Magnitude, e não apenas presença de efeito',fontsize=12.5,loc='left',fontweight='bold')
a2.annotate('* p < 0,05 no t pareado (n = 21)',xy=(.02,.03),xycoords='axes fraction',
            fontsize=9,color=MUT,style='italic')
gx(a2)
rod(fig,'Três das sete variáveis mudam de veredito conforme a via. Nenhuma delas é ruído: são pressupostos diferentes '
        'sobre os mesmos dados. Só a via paramétrica entrega intervalo de confiança para a magnitude.')
fig.tight_layout(); salvar(fig,'G2fig')

# ============ G3: pressupostos ============
fig,ax=plt.subplots(1,3,figsize=(17.4,5.8))
a=ax[0]
W=[D[v]['W'] for v in V7]; pW=[D[v]['pW'] for v in V7]
yb=np.arange(len(V7))[::-1]
a.axvline(.95,color='#8A9299',lw=1.5,ls='--',zorder=4)
for i,v in enumerate(V7):
    a.barh(yb[i],W[i],height=.6,color=CV[v],alpha=.92 if pW[i]>=.05 else .35,edgecolor=CV[v],lw=1.8,zorder=3)
    a.annotate(f"W={vg(W[i],3)}  {pv(pW[i])}",xy=(W[i],yb[i]),xytext=(7,0),textcoords='offset points',
               va='center',fontsize=9.4,color=INK,fontweight='bold' if pW[i]>=.05 else 'normal')
a.set_yticks(yb); a.set_yticklabels([L(v) for v in V7],fontsize=10.5)
for t,v in zip(a.get_yticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
a.set_xlim(.4,1.28); a.set_xlabel('W de Shapiro-Wilk',fontsize=11)
a.set_title('(A) Normalidade',fontsize=12,loc='left',fontweight='bold')
a.annotate('barras esmaecidas: normalidade rejeitada',xy=(.02,.03),xycoords='axes fraction',
           fontsize=9,color=MUT,style='italic'); gx(a)
a2=ax[1]
eps=[PA[v]['eps'] for v in V7]
for i,v in enumerate(V7):
    a2.barh(yb[i],eps[i],height=.6,color=CV[v],alpha=.92 if eps[i]>.75 else .35,edgecolor=CV[v],lw=1.8,zorder=3)
    a2.annotate(f"ε={vg(eps[i],3)}",xy=(eps[i],yb[i]),xytext=(7,0),textcoords='offset points',
                va='center',fontsize=9.6,color=INK,fontweight='bold')
a2.axvline(.75,color='#C1440E',lw=1.8,ls='--',zorder=4)
a2.set_yticks(yb); a2.set_yticklabels([L(v) for v in V7],fontsize=10.5)
for t,v in zip(a2.get_yticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
a2.set_xlim(0,1.18); a2.set_xlabel('ε de Greenhouse-Geisser',fontsize=11)
a2.set_title('(B) Esfericidade',fontsize=12,loc='left',fontweight='bold')
a2.annotate('ε < 0,75: correção indispensável',xy=(.02,.03),xycoords='axes fraction',
            fontsize=9,color=MUT,style='italic'); gx(a2)
a3=ax[2]
piso=[D[v]['piso'] for v in V7]; lev=[PA[v]['lev'] for v in V7]
a3.scatter(piso,lev,s=[220]*len(V7),c=[CV[v] for v in V7],zorder=4,edgecolor='white',lw=2)
for i,v in enumerate(V7):
    a3.annotate(L(v),xy=(piso[i],lev[i]),xytext=(0,13),textcoords='offset points',ha='center',
                fontsize=9.6,fontweight='bold',color=CV[v])
a3.axvline(15,color='#C1440E',lw=1.8,ls='--',zorder=3)
a3.axhline(.05,color='#8A9299',lw=1.5,ls='--',zorder=3)
a3.set_xlabel('Efeito de piso (%)',fontsize=11); a3.set_ylabel('p do teste de Levene',fontsize=11)
a3.set_xlim(-4,76); a3.set_ylim(-.06,1.12)
a3.set_title('(C) Piso e homogeneidade de variâncias',fontsize=12,loc='left',fontweight='bold')
a3.annotate('quadrante inferior direito:\npiso severo e variâncias heterogêneas —\na via paramétrica não se sustenta',
            xy=(.97,.97),xycoords='axes fraction',ha='right',va='top',fontsize=9.2,color=INK,linespacing=1.45,
            bbox=dict(boxstyle='round,pad=.45',fc='#F7F8F8',ec='#8A9299',lw=1.2))
gy(a3); gx(a3)
fig.suptitle('Pressupostos das vias paramétricas, variável a variável',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.02)
fig.tight_layout(); salvar(fig,'G3fig')

# ============ G4: perfis por estímulo ============
EST4=['Basal']+TIPOS
fig,ax=plt.subplots(1,2,figsize=(16.6,6.4),gridspec_kw={'width_ratios':[1.55,1.0]})
a=ax[0]; w=.20; xb=np.arange(6)
for j,e in enumerate(EST4):
    v=[A3['PREV_EST'][nm][e] for nm in PERF]; n=A3['NPOR'][e]
    ep=[100*np.sqrt(max(p/100*(1-p/100),0)/n) for p in v]
    a.bar(xb+(j-1.5)*w,v,width=w-.028,color=CEST[e],alpha=.90,edgecolor=SURF,lw=1.6,zorder=3,
          label=f'{e} (n = {n})')
    a.errorbar(xb+(j-1.5)*w,v,yerr=ep,fmt='none',ecolor='#4A5257',elinewidth=1.5,capsize=3,zorder=4)
    for i_,vv in enumerate(v):
        if vv>0.5: a.annotate(vg(vv),xy=(xb[i_]+(j-1.5)*w,vv+ep[i_]),xytext=(0,4),
                              textcoords='offset points',ha='center',fontsize=8.4,color=INK,rotation=90,va='bottom')
a.set_xticks(xb); a.set_xticklabels([p.replace(' de ','\n de ').replace(' invertido','\ninvertido') for p in PERF],fontsize=10)
a.set_ylabel('Prevalência de pares atleta-dia (%)',fontsize=11); a.set_ylim(0,62)
a.legend(fontsize=10,frameon=False,ncol=4,loc='upper center',bbox_to_anchor=(.5,-.10))
a.set_title('(A) Distribuição dos seis perfis por tipo de estímulo',fontsize=12,loc='left',fontweight='bold')
a.annotate(f"χ² = {vg(A3['chi'],2)}; gl = {A3['gl']}; {pv(A3['p_chi'])} — a distribuição\ndos perfis não difere entre os estímulos",
           xy=(.985,.99),xycoords='axes fraction',ha='right',va='top',fontsize=10,color=INK,linespacing=1.4,
           bbox=dict(boxstyle='round,pad=0.5',fc='#F7F8F8',ec='#8A9299',lw=1.3)); gy(a)
a2=ax[1]; FX=['Favorável','Neutra','Risco']; CFX={'Favorável':'#1A9070','Neutra':'#6B7378','Risco':'#C1440E'}
bot=np.zeros(4)
for f_ in FX:
    v=np.array([A3['FAIXA_EST'][f_][e] for e in EST4])
    a2.bar(np.arange(4),v,bottom=bot,width=.66,color=CFX[f_],alpha=.92,edgecolor=SURF,lw=2.0,zorder=3,label=f_)
    for i_ in range(4):
        if v[i_]>4: a2.text(i_,bot[i_]+v[i_]/2,vg(v[i_]),ha='center',va='center',fontsize=10.6,color='white',fontweight='bold',zorder=5)
    bot=bot+v
a2.set_xticks(range(4)); a2.set_xticklabels([f"{e}\n(n = {A3['NPOR'][e]})" for e in EST4],fontsize=10.4)
a2.set_ylim(0,112); a2.set_yticks([0,20,40,60,80,100]); a2.set_ylabel('Composição da faixa (%)',fontsize=11)
a2.legend(fontsize=10,frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.16))
a2.set_title('(B) Faixa de humor por tipo de estímulo',fontsize=12,loc='left',fontweight='bold')
a2.annotate(f"χ² = {vg(A3['chi_f'],2)}; gl = {A3['gl_f']}; {pv(A3['p_f'])}",xy=(.5,.99),xycoords='axes fraction',
            ha='center',va='top',fontsize=10.4,color=INK,
            bbox=dict(boxstyle='round,pad=0.42',fc='#FFFFFF',ec='#8A9299',lw=1.3)); gy(a2)
rod(fig,'166 pares atleta-dia. Barras de erro: erro-padrão binomial. Nenhuma associação significativa entre estímulo e perfil ou faixa.')
fig.tight_layout(); salvar(fig,'G4fig')

# ============ G5: Spearman × Pearson ============
MAT=A3['MAT']
def par(i,j,campo):
    k=f"{V7[i]}×{V7[j]}"
    return MAT[k][campo] if k in MAT else MAT[f"{V7[j]}×{V7[i]}"][campo]
fig,ax=plt.subplots(1,3,figsize=(17.4,6.2),gridspec_kw={'width_ratios':[1,1,.95]})
for idx,(campo,pcam,tit) in enumerate([('rho','ph','(A) Spearman (ρ) — via não paramétrica'),
                                        ('r','phr','(B) Pearson (r) — via paramétrica')]):
    a=ax[idx]; M=np.full((7,7),np.nan)
    for i in range(7):
        for j in range(7):
            if i!=j: M[i,j]=par(i,j,campo)
    im=a.imshow(M,cmap=DIV,vmin=-.85,vmax=.85,aspect='equal')
    for i in range(7):
        a.add_patch(Rectangle((i-.5,i-.5),1,1,fc='#F2F3F4',ec=SURF,lw=2.4,zorder=4))
        for j in range(7):
            if i==j: continue
            val=par(i,j,campo); pa=par(i,j,pcam)
            est='**' if pa<.01 else ('*' if pa<.05 else '')
            a.text(j,i,f"{vg(val,2)}{est}",ha='center',va='center',fontsize=9.0,
                   color='white' if abs(val)>.55 else INK,fontweight='bold' if est else 'normal')
    a.set_xticks(range(7)); a.set_xticklabels([L(v) for v in V7],fontsize=9.4,rotation=40,ha='right')
    a.set_yticks(range(7)); a.set_yticklabels([L(v) for v in V7],fontsize=9.4)
    for t,v in zip(a.get_xticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
    for t,v in zip(a.get_yticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
    a.set_xticks(np.arange(8)-.5,minor=True); a.set_yticks(np.arange(8)-.5,minor=True)
    a.grid(which='minor',color=SURF,lw=2.4); a.tick_params(which='minor',length=0)
    for sp in a.spines.values(): sp.set_visible(False)
    a.set_title(tit,fontsize=12,loc='left',fontweight='bold',pad=22)
    a.annotate('* Holm p < 0,05    ** Holm p < 0,01',xy=(1.0,1.012),xycoords='axes fraction',
               ha='right',va='bottom',fontsize=8.8,color=MUT,style='italic')
a3=ax[2]
rho=[]; rr=[]; cores=[]; rot=[]
for i in range(7):
    for j in range(i+1,7):
        rho.append(par(i,j,'rho')); rr.append(par(i,j,'r')); cores.append(CV[V7[i]])
        rot.append(f"{L(V7[i])}×{L(V7[j])}")
a3.plot([-1,1],[-1,1],color='#8A9299',lw=1.5,ls='--',zorder=2)
a3.scatter(rho,rr,s=90,c=cores,alpha=.85,zorder=4,edgecolor='white',lw=1.4)
dif=np.abs(np.array(rho)-np.array(rr)); k=int(np.argmax(dif))
a3.annotate(rot[k],xy=(rho[k],rr[k]),xytext=(12,-14),textcoords='offset points',fontsize=9.4,
            fontweight='bold',color=cores[k],
            arrowprops=dict(arrowstyle='-',lw=1.2,color=cores[k]))
a3.set_xlim(-.9,.95); a3.set_ylim(-.9,.95)
a3.set_xlabel('ρ de Spearman',fontsize=11); a3.set_ylabel('r de Pearson',fontsize=11)
a3.set_title('(C) As duas concordam?',fontsize=12,loc='left',fontweight='bold',pad=22)
a3.annotate(f"maior discrepância: {vg(dif.max(),3)}\nmediana das discrepâncias: {vg(float(np.median(dif)),3)}",
            xy=(.03,.95),xycoords='axes fraction',va='top',fontsize=9.6,color=INK,linespacing=1.45,
            bbox=dict(boxstyle='round,pad=.45',fc='#F7F8F8',ec='#8A9299',lw=1.2))
gy(a3); gx(a3)
fig.suptitle('Estrutura de associação pelas duas vias',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.01)
fig.tight_layout(); salvar(fig,'G5fig')

# ============ G6: modelo misto ============
fig,ax=plt.subplots(1,2,figsize=(16.4,6.0))
a=ax[0]; yb=np.arange(len(V7))[::-1]
a.axvline(0,color='#4A5257',lw=1.5,zorder=4)
for i,v in enumerate(V7):
    d=LMM[v]; c=CV[v]; sig=d['p']<.05
    a.plot([d['ic'][0],d['ic'][1]],[yb[i],yb[i]],color=c,lw=3.2,solid_capstyle='round',
           alpha=.95 if sig else .35,zorder=3)
    a.plot([d['b_dia']],[yb[i]],'o',ms=13,color=c,mec='white',mew=2,zorder=5,alpha=.95 if sig else .35)
    a.annotate(f"b = {vg(d['b_dia'],3)}  {pv(d['p'])}",xy=(1.02,yb[i]),ha='right',va='center',
               fontsize=9.8,fontweight='bold' if sig else 'normal',color=c)
a.set_yticks(yb); a.set_yticklabels([L(v) for v in V7],fontsize=11.5)
for t,v in zip(a.get_yticklabels(),V7): t.set_color(CV[v]); t.set_fontweight('bold')
a.set_xlim(-.75,1.55); a.set_xlabel('Mudança por dia, em pontos da escala (IC 95%)',fontsize=11)
a.set_title('(A) Efeito linear do dia — modelo misto sobre os 166 pares',fontsize=12,loc='left',fontweight='bold')
gx(a)
a2=ax[1]
icc=[LMM[v]['icc'] for v in V7]; ordem=np.argsort(icc)[::-1]
for k,i in enumerate(ordem):
    v=V7[i]
    a2.barh(k,icc[i],height=.6,color=CV[v],alpha=.92,edgecolor=CV[v],lw=1.8,zorder=3)
    a2.annotate(vg(icc[i],3),xy=(icc[i],k),xytext=(7,0),textcoords='offset points',va='center',
                fontsize=10,fontweight='bold',color=CV[v])
a2.set_yticks(range(7)); a2.set_yticklabels([L(V7[i]) for i in ordem],fontsize=11.5)
for t,i in zip(a2.get_yticklabels(),ordem): t.set_color(CV[V7[i]]); t.set_fontweight('bold')
a2.invert_yaxis(); a2.set_xlim(0,.95); a2.set_xlabel('Proporção da variância que é estável entre atletas',fontsize=11)
a2.set_title('(B) Quanto do humor é do atleta e não do dia',fontsize=12,loc='left',fontweight='bold')
a2.annotate('valores altos: a diferença entre atletas domina;\nvalores baixos: o estado do dia domina',
            xy=(.97,.06),xycoords='axes fraction',ha='right',va='bottom',fontsize=9.4,color=INK,linespacing=1.45,
            bbox=dict(boxstyle='round,pad=.45',fc='#F7F8F8',ec='#8A9299',lw=1.2))
gx(a2)
rod(fig,'O modelo misto retém os 166 pares e estima, ao mesmo tempo, a tendência do ciclo e quanto da variação pertence ao atleta.')
fig.tight_layout(); salvar(fig,'G6fig')
