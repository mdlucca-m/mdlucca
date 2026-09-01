# -*- coding: utf-8 -*-
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UVh.py")).read())
SERP=A3['SERP']; EST={d:TIPO[d] for d in range(1,8)}

# ============ F7: prevalência diária dos seis perfis ============
fig,ax=plt.subplots(2,3,figsize=(17.2,9.0))
for i,nm in enumerate(PERF):
    a=ax[i//3][i%3]; marcar(a,alpha=.75)
    d=SERP[nm]; y=np.array(d['y']); se=np.array(d['se']); sm=np.array(d['sm']); pi=d['piso']; c=CPF[nm]
    a.fill_between(x7,y-se,y+se,color=c,alpha=.15,zorder=2,lw=0)
    a.plot(x7,y,'-o',color=c,lw=1.6,ms=6,alpha=.45,zorder=3,mfc='white',mew=1.4)
    a.plot(x7,sm,'-',color=c,lw=4.2,zorder=4,solid_capstyle='round')
    a.axhline(y[0],color=MUT,lw=1.2,ls='--',zorder=2)
    a.axhspan(y[0]-pi,y[0]+pi,color='#6B7378',alpha=.11,zorder=1,lw=0)
    for cc in d['choque']:
        a.plot([cc,cc+1],[sm[cc-1],sm[cc]],lw=9.0,color=c,alpha=.26,zorder=3,solid_capstyle='round')
        a.plot([cc,cc+1],[sm[cc-1],sm[cc]],lw=1.9,color='#2A2F33',ls=(0,(1.1,1.5)),zorder=6)
        a.plot([(2*cc+1)/2],[(sm[cc-1]+sm[cc])/2],marker='o',ms=8.5,mfc='#2A2F33',mec='white',mew=1.8,zorder=7)
    a.set_ylim(-3,58); a.set_xlim(.5,7.5); a.set_xticks(x7)
    a.set_xticklabels([f'D{k}' for k in x7],fontsize=9.6)
    if i%3==0: a.set_ylabel('Prevalência (%)',fontsize=10)
    a.text(.035,.955,nm,transform=a.transAxes,fontsize=12.2,fontweight='bold',color=c,va='top')
    a.text(.035,.845,f"Δ D1→D7 = {vg(d['dtot'])} p.p.\npiso = ±{vg(pi)} p.p.",transform=a.transAxes,
           fontsize=9.4,color=MUT,va='top',linespacing=1.45)
    frag=d.get('fragil',False)
    rot='NÃO AVALIÁVEL' if frag else ('SINAL' if d['sinal'] else 'RUÍDO'); larg=.38 if frag else .26
    a.add_patch(Rectangle((.97-larg,.90),larg,.085,transform=a.transAxes,zorder=6,
                fc=c if (d['sinal'] and not frag) else '#FFFFFF',ec=c,lw=1.8))
    a.text(.97-larg/2,.9425,rot,transform=a.transAxes,fontsize=9.4 if frag else 10,fontweight='bold',
           ha='center',va='center',color='white' if (d['sinal'] and not frag) else c,zorder=7)
    if frag: a.annotate('prevalência ≤ 1 atleta por dia: o piso binomial\nencolhe e o critério deixa de discriminar',
                        xy=(.035,.40),xycoords='axes fraction',fontsize=8.8,color='#A31E52',
                        style='italic',linespacing=1.35,va='top')
    gy(a)
fig.legend(handles=[Line2D([],[],color=MUT,lw=1.6,marker='o',mfc='white',alpha=.5,label='prevalência observada ± erro-padrão binomial'),
  Line2D([],[],color=MUT,lw=4.2,label='série suavizada'),
  Patch(fc='#6B7378',alpha=.22,label='banda do piso de ruído em torno do dia basal'),
  Line2D([],[],color='#2A2F33',lw=1.9,ls=(0,(1.1,1.5)),marker='o',ms=8.5,mfc='#2A2F33',mec='white',mew=1.8,
         label='transição de choque')],fontsize=10,frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.015))
fig.suptitle('Prevalência diária dos seis perfis de humor',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.005)
fig.tight_layout(rect=[0,.035,1,.99]); salvar(fig,'F7fig')

# ============ F8: teste formal de cruzamento ============
fig,ax=plt.subplots(1,3,figsize=(17.4,5.9))
FAV=np.array(A3['FAV']); NEU=np.array(A3['NEU']); RIS=np.array(A3['RIS'])
def cruzp(A_,B_,pa,pb):
    dif=np.array(A_)-np.array(B_); lim=float(np.hypot(pa,pb)); cs=[]
    for i in range(6):
        if dif[i]*dif[i+1]<0: cs.append(float(i+1+dif[i]/(dif[i]-dif[i+1])))
    est=bool(cs and abs(dif[0])>lim and abs(dif[-1])>lim)
    return dif,lim,cs,est
dif,lim,cs,est=cruzp(FAV,RIS,SERP['Favorável']['piso'],SERP['De risco']['piso'])
a=ax[0]; marcar(a,alpha=.7)
a.plot(x7,FAV,'-o',color='#1A9070',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Faixa favorável')
a.plot(x7,NEU,'-o',color='#6B7378',lw=2.2,ms=7,mfc='white',mew=2.0,zorder=3,alpha=.75,label='Faixa neutra')
a.plot(x7,RIS,'-o',color='#C1440E',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Faixa de risco')
for i_,c in enumerate(cs):
    a.axvline(c,color='#2A2F33',lw=1.6,ls=(0,(3,2)),zorder=5)
    a.annotate(f'D{vg(c,2)}',xy=(c,[60,56,60][i_%3]),ha='center',va='center',fontsize=9,color=INK,
               fontweight='bold',zorder=6,bbox=dict(boxstyle='round,pad=.25',fc='white',ec='#8A9299',lw=1.0))
a.set_xlim(.5,7.5); a.set_ylim(0,64); a.set_xticks(x7); a.set_xticklabels([f'D{d}' for d in x7],fontsize=10.5)
a.set_ylabel('Prevalência (%)',fontsize=11)
a.set_title('(A) As três faixas ao longo da semana',fontsize=12,loc='left',fontweight='bold')
a.legend(fontsize=9.6,frameon=False,loc='lower left'); gy(a)
a2=ax[1]; marcar(a2,alpha=.7)
a2.axhspan(-lim,lim,color='#6B7378',alpha=.16,zorder=1,lw=0); a2.axhline(0,color='#2A2F33',lw=1.6,zorder=3)
a2.plot(x7,dif,'-o',color='#8A4FBF',lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4)
for c in cs: a2.plot([c],[0],marker='X',ms=13,color='#2A2F33',zorder=6,mec='white',mew=1.6)
a2.set_xlim(.5,7.5); a2.set_xticks(x7); a2.set_xticklabels([f'D{d}' for d in x7],fontsize=10.5)
a2.set_ylabel('Favorável − De risco (p.p.)',fontsize=11)
a2.set_title('(B) Diferença entre as faixas e limiar',fontsize=12,loc='left',fontweight='bold')
a2.annotate(f"limiar = ±{vg(lim)} p.p.\n{len(cs)} cruzamento(s)\n"
            +("inversão estabelecida" if est else "divergência, não inversão estabelecida"),
            xy=(.03,.045),xycoords='axes fraction',fontsize=9.4,color=INK,va='bottom',linespacing=1.5,
            bbox=dict(boxstyle='round,pad=.45',fc='#FFFFFF',ec='#8A9299',lw=1.2)); gy(a2)
a3=ax[2]; marcar(a3,alpha=.7)
vv=np.array(A1['SER']['Vigor']['sm']); ff=np.array(A1['SER']['Fadiga']['sm']); cz=A1['CRZ']['Vigor×Fadiga']
a3.plot(x7,vv,'-o',color=CV['Vigor'],lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Vigor')
a3.plot(x7,ff,'-o',color=CV['Fadiga'],lw=4.0,ms=9,mfc='white',mew=2.6,zorder=4,label='Fadiga')
if cz['cs']:
    a3.axvline(cz['cs'][0],color='#2A2F33',lw=1.8,ls=(0,(3,2)),zorder=5)
    a3.annotate(f"cruzamento em D{vg(cz['cs'][0],2)}",xy=(cz['cs'][0],8.0),xytext=(-8,0),
                textcoords='offset points',ha='right',fontsize=10,color=INK,fontweight='bold',
                bbox=dict(boxstyle='round,pad=.3',fc='white',ec='#8A9299',lw=1.1))
a3.fill_between(x7,vv,ff,where=(vv>=ff),color=CV['Vigor'],alpha=.11,zorder=1)
a3.fill_between(x7,vv,ff,where=(vv<ff),color=CV['Fadiga'],alpha=.11,zorder=1)
a3.set_xlim(.5,7.5); a3.set_ylim(3,8.8); a3.set_xticks(x7); a3.set_xticklabels([f'D{d}' for d in x7],fontsize=10.5)
a3.set_ylabel('Escore bruto suavizado',fontsize=11)
a3.set_title('(C) Vigor e fadiga',fontsize=12,loc='left',fontweight='bold')
a3.legend(fontsize=10,frameon=False,loc='center left')
a3.annotate(f"limiar = ±{vg(cz['lim'],2)}; diferença em D1 = {vg(cz['d1'],2)}\ne em D7 = {vg(cz['d7'],2)} → "
            +("inversão estabelecida" if cz['est'] else "divergência"),
            xy=(.03,.045),xycoords='axes fraction',fontsize=9.4,color=INK,va='bottom',linespacing=1.5,
            bbox=dict(boxstyle='round,pad=.45',fc='#FFFFFF',ec='#8A9299',lw=1.2)); gy(a3)
fig.suptitle('Teste formal de cruzamento: quando uma troca de posição é real',fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.02)
fig.tight_layout()
fig.text(.011,-.035,'O limiar de cada par é o piso de ruído combinado das duas séries. Só se declara inversão quando a '
         'diferença ultrapassa o limiar antes e depois do cruzamento.',fontsize=8.8,color=MUT,style='italic')
salvar(fig,'F8fig')

# ============ F9: custo do dia e migração intradiária ============
TIPOS=['HIIT','Amistoso','Técnico/força']
fig=plt.figure(figsize=(16.8,9.2))
gs=fig.add_gridspec(2,2,height_ratios=[1.0,.86],width_ratios=[5.2,1.0],hspace=.44,wspace=.16)
AG=A3['AG']
def barras(a, vars_, titulo, ylab):
    xb=np.arange(len(vars_)); w=.26
    for j,t in enumerate(TIPOS):
        vals=[AG[v][t]['d'] for v in vars_]; ps=[AG[v][t]['p'] for v in vars_]
        a.bar(xb+(j-1)*w, vals, width=w-.04, color=CEST[t], alpha=.92, edgecolor=SURF, lw=1.4, zorder=3,
              label=f"{t} (n = {AG['Vigor'][t]['n']})")
        for i_,(vv,pp) in enumerate(zip(vals,ps)):
            if pp<.05:
                a.annotate('*',xy=(xb[i_]+(j-1)*w, vv+(.06 if vv>0 else -.20)*max(1,abs(max(vals,key=abs)))),
                           ha='center',fontsize=17,fontweight='bold',color=CEST[t])
    a.axhline(0,color='#4A5257',lw=1.4,zorder=4)
    a.set_xticks(xb); a.set_xticklabels([L(v) for v in vars_],fontsize=11)
    if ylab: a.set_ylabel('Variação da manhã para a noite',fontsize=11)
    a.set_title(titulo,fontsize=12.5,loc='left',fontweight='bold')
    y0,y1=a.get_ylim(); a.set_ylim(y0-(y1-y0)*.10, y1+(y1-y0)*.14); gy(a)
a=fig.add_subplot(gs[0,0]); barras(a,SUB,'(A) Custo do dia por tipo de estímulo — seis subescalas (0–16)',True)
a.legend(fontsize=10,frameon=False,ncol=3,loc='upper left')
a.annotate('* p < 0,05 no teste de Wilcoxon para a diferença entre a noite e a manhã',
           xy=(.99,.04),xycoords='axes fraction',ha='right',fontsize=9,color=MUT,style='italic')
aP=fig.add_subplot(gs[0,1]); barras(aP,['TMD'],'(B) PTH (−16 a 80)',False)
aP.set_xticklabels([''])
a2=fig.add_subplot(gs[1,:])
MCN=A3['MCN']; ordem=['TODOS']+TIPOS; yb=np.arange(len(ordem))[::-1]
for i_,t in enumerate(ordem):
    m=MCN[t]
    a2.barh(yb[i_]+.17,m['entra'],height=.30,color='#C1440E',alpha=.92,zorder=3,
            label='entram na faixa de risco' if i_==0 else None)
    a2.barh(yb[i_]-.17,-m['sai'],height=.30,color='#1A9070',alpha=.92,zorder=3,
            label='saem da faixa de risco' if i_==0 else None)
    a2.annotate(str(m['entra']),xy=(m['entra'],yb[i_]+.17),xytext=(7,0),textcoords='offset points',
                va='center',fontsize=11,fontweight='bold',color='#C1440E')
    a2.annotate(str(m['sai']),xy=(-m['sai'],yb[i_]-.17),xytext=(-7,0),textcoords='offset points',
                va='center',ha='right',fontsize=11,fontweight='bold',color='#1A9070')
    txt=f"χ² = {vg(m['chi'],2)}; {pv(m['p'])}" + (f"; Holm {pv(m['ph'])}" if m.get('ph') is not None else "")
    a2.annotate(txt,xy=(28,yb[i_]),ha='left',va='center',fontsize=10.4,
                color=INK if m['p']<.05 else MUT,fontweight='bold' if m['p']<.05 else 'normal')
a2.axvline(0,color='#4A5257',lw=1.5,zorder=4)
a2.set_yticks(yb); a2.set_yticklabels([f"{t}\n(n = {MCN[t]['n']})" for t in ordem],fontsize=11)
for tk,t in zip(a2.get_yticklabels(),ordem): tk.set_color(CEST.get(t,'#2A2F33')); tk.set_fontweight('bold')
a2.set_xlim(-14,52); a2.set_xticks([-10,-5,0,5,10,15,20,25])
a2.set_xticklabels(['10','5','0','5','10','15','20','25'],fontsize=10)
a2.set_xlabel('Pares atleta-dia que mudam de faixa entre a manhã e a noite',fontsize=11)
a2.set_title('(C) Migração intradiária para a faixa de risco — teste de McNemar',fontsize=12.5,loc='left',fontweight='bold')
a2.legend(fontsize=10,frameon=False,ncol=2,loc='upper center',bbox_to_anchor=(.35,-.16)); gx(a2)
rod(fig,'A migração é robusta no conjunto dos 119 pares completos; repartida por estímulo, só o HIIT alcança '
        'significância bruta, e ela não sobrevive à correção de Holm.',y=-.055)
salvar(fig,'F9fig')
