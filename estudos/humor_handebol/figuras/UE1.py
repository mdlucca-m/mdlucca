# -*- coding: utf-8 -*-
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UEh.py")).read())

# ===================== E1: desenho do microciclo + cadeia analítica =====================
fig=plt.figure(figsize=(17.6,10.2))
axA=fig.add_axes([0.055,0.615,0.90,0.345]); axA.axis('off')
axA.set_xlim(.5,7.5); axA.set_ylim(0,100)
fig.text(0.012,0.985,'(A) Microciclo terminal de pré-temporada — estímulos, carga e janelas de coleta',
         fontsize=13,fontweight='bold',color=INK,va='top')
h=[CARGA[str(d)]['h'] for d in range(1,8)]
BW=.88
for d in range(1,8):
    t=TIPO[d]; c=CEST[t]
    axA.add_patch(FancyBboxPatch((d-BW/2,58),BW,34,boxstyle="round,pad=0.02,rounding_size=.05",
                  fc={'Basal':'#F0F1F2','HIIT':'#FBEAE3','Amistoso':'#E7EFF7','Técnico/força':'#E4F1EC'}[t],
                  ec=c,lw=2.0,zorder=3,mutation_aspect=.06))
    axA.text(d,84,f'Dia {d}',fontsize=12.5,fontweight='bold',ha='center',va='center',color=INK,zorder=4)
    axA.text(d,73,t,fontsize=10.6,ha='center',va='center',color=c,fontweight='bold',zorder=4)
    axA.text(d,63.5,f'{vg(h[d-1])} h · {CARGA[str(d)]["ses"]} ' + ('sessão' if CARGA[str(d)]["ses"]==1 else 'sessões'),fontsize=9.4,ha='center',va='center',color=MUT,zorder=4)
    if d==1:
        axA.add_patch(FancyBboxPatch((d-BW/2,30),BW,18,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#2A2F33',ec='none',zorder=3,mutation_aspect=.06))
        axA.text(d,39,'BASAL\n1 coleta (noite)',fontsize=9.0,ha='center',va='center',
                 color='white',fontweight='bold',zorder=4,linespacing=1.3)
    else:
        w=BW/2-.045
        axA.add_patch(FancyBboxPatch((d-BW/2,30),w,18,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#FFFFFF',ec='#8A9299',lw=1.6,zorder=3,mutation_aspect=.06))
        axA.text(d-BW/2+w/2,39,'PRÉ\nmanhã',fontsize=9.0,ha='center',va='center',color=INK,zorder=4,linespacing=1.3)
        axA.add_patch(FancyBboxPatch((d+.045,30),w,18,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#4A5257',ec='none',zorder=3,mutation_aspect=.06))
        axA.text(d+.045+w/2,39,'PÓS\nnoite',fontsize=9.0,ha='center',va='center',
                 color='white',fontweight='bold',zorder=4,linespacing=1.3)
        axA.add_patch(FancyArrowPatch((d-.10,39),(d+.02,39),arrowstyle='-|>',
                      mutation_scale=12,lw=1.6,color='#C1440E',zorder=5))
    if d<7:
        axA.add_patch(FancyArrowPatch((d+BW/2+.015,39),(d+1-BW/2-.015,39),arrowstyle='-|>',
                      mutation_scale=12,lw=1.6,color='#2166AC',zorder=5,linestyle=(0,(2.5,1.8))))
axA.text(.55,17,'seta interna (laranja) = custo do dia (pré→pós)      ·      '
                'seta tracejada (azul) = restituição noturna (pós→pré do dia seguinte)',
         fontsize=10,color=MUT,style='italic',va='center')
axB=fig.add_axes([0.055,0.487,0.90,0.115])
ac=[CARGA[str(d)]['acum'] for d in range(1,8)]
axB.fill_between(x7,0,ac,color='#2166AC',alpha=.13,zorder=1)
axB.plot(x7,ac,'-o',color='#2166AC',lw=3.0,ms=8,mfc='white',mew=2.4,zorder=3)
for i_,v in enumerate(ac):
    axB.annotate(vg(v),xy=(i_+1,v),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9,
                 fontweight='bold',color='#2166AC')
axB.set_xlim(.5,7.5); axB.set_ylim(0,28); axB.set_xticks(x7); axB.set_yticks([0,10,20])
axB.set_ylabel('Carga\nacumulada (h)',fontsize=9.5,linespacing=1.2)
axB.set_xticklabels([f'D{d}' for d in x7],fontsize=9.5)
gy(axB)
axC=fig.add_axes([0.012,0.03,0.976,0.40]); axC.axis('off')
axC.set_xlim(0,100); axC.set_ylim(0,100)
axC.text(0,99,'(B) Cadeia de processamento — do escore bruto ao veredito de sinal',
         fontsize=13,fontweight='bold',color=INK,va='top')
et=[('1. Importação\nopenpyxl → matriz\n166 pares atleta-dia','#F0F1F2','#6B7378'),
    ('2. Padronização\nescore T contra norma\nexterna de atletas','#E7EFF7','#2166AC'),
    ('3. Classificação\nk-means semeado nos\nseis perfis canônicos','#E4F1EC','#1A9070'),
    ('4. Série diária\nprevalência e média\npor dia (D1–D7)','#FDF3E4','#E0952B'),
    ('5. Suavização\nfiltro binomial 1-2-1\n(atenua ruído amostral)','#FBEAE3','#C1440E'),
    ('6. Derivadas\n1.ª (velocidade) e\n2.ª (aceleração)','#F1EAF9','#8A4FBF'),
    ('7. Piso de ruído\nmédia dos EPM diários\n→ limiar de decisão','#F7E4EC','#A31E52')]
bw=12.6; gap=1.6; bx=0.6
for i_,(t,fc,ec) in enumerate(et):
    X=bx+i_*(bw+gap)
    axC.add_patch(FancyBboxPatch((X,58),bw,28,boxstyle="round,pad=0.5,rounding_size=1.6",
                  fc=fc,ec=ec,lw=2.0,zorder=3))
    axC.text(X+bw/2,72,t,fontsize=9.6,ha='center',va='center',color=INK,zorder=4,linespacing=1.55)
    if i_<6:
        axC.add_patch(FancyArrowPatch((X+bw+0.15,72),(X+bw+gap-0.15,72),arrowstyle='-|>',
                      mutation_scale=14,lw=1.9,color='#8A9299',zorder=2))
w1=bw*3+gap*2
axC.add_patch(FancyBboxPatch((bx,20),w1,24,boxstyle="round,pad=0.5,rounding_size=1.6",
              fc='#FFFFFF',ec='#2A2F33',lw=2.2,zorder=3))
axC.text(bx+w1/2,32,'Veredito de sinal\n|Δ total| > piso de ruído  →  variação real\n'
         'caso contrário  →  flutuação amostral',
         fontsize=10.4,ha='center',va='center',color=INK,zorder=4,linespacing=1.55,fontweight='bold')
X2=bx+(bw+gap)*3.6; w2=bw*3.4+gap*2
axC.add_patch(FancyBboxPatch((X2,20),w2,24,boxstyle="round,pad=0.5,rounding_size=1.6",
              fc='#FFFFFF',ec='#2A2F33',lw=2.2,zorder=3))
axC.text(X2+w2/2,32,'Teste de cruzamento\ninversão declarada apenas quando a diferença entre duas séries\n'
         'ultrapassa o limiar dos dois lados do ponto de cruzamento',
         fontsize=10.4,ha='center',va='center',color=INK,zorder=4,linespacing=1.55,fontweight='bold')
xdir=bx+(bw+gap)*6+bw
axC.plot([bx,xdir],[52,52],color='#8A9299',lw=1.9,zorder=2,solid_capstyle='round')
for xv in [bx+bw/2,bx+(bw+gap)*3+bw/2,xdir-bw/2]:
    axC.plot([xv,xv],[57.6,52],color='#8A9299',lw=1.9,zorder=2)
axC.add_patch(FancyArrowPatch((bx+w1/2,52),(bx+w1/2,44.6),arrowstyle='-|>',mutation_scale=14,lw=1.9,color='#8A9299',zorder=2))
axC.add_patch(FancyArrowPatch((X2+w2/2,52),(X2+w2/2,44.6),arrowstyle='-|>',mutation_scale=14,lw=1.9,color='#8A9299',zorder=2))
rodape(fig,'Fonte: elaboração própria. Toda a cadeia foi executada em Python 3 (NumPy, SciPy, openpyxl, matplotlib).')
fig.savefig(f"{SAIDA}/E1fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E1 ok")

# ===================== E2: comportamento das seis subescalas =====================
fig,ax=plt.subplots(1,2,figsize=(16.8,6.4),gridspec_kw={'width_ratios':[1.45,1.0]})
a=ax[0]; marcar(a)
a.axhline(50,color='#8A9299',lw=1.5,ls='--',zorder=2)
fin={}
for k in SUB:
    y=[Tv(k,d['m']) for d in B1['DIA'][k]]
    a.plot(x7,y,'-o',color=CV[k],lw=3.4,ms=8,mfc='white',mew=2.4,zorder=4,label=k)
    fin[k]=y[-1]
ordem=sorted(SUB,key=lambda k:fin[k])
ypos={}; ult=None
for k in ordem:
    v=fin[k]
    if ult is not None and v-ult<1.35: v=ult+1.35
    ypos[k]=v; ult=v
for k in SUB:
    a.annotate(k,xy=(7.14,ypos[k]),xytext=(0,0),textcoords='offset points',fontsize=10.8,
               fontweight='bold',color=CV[k],va='center',ha='left')
    if abs(ypos[k]-fin[k])>.12:
        a.plot([7.02,7.12],[fin[k],ypos[k]],color=CV[k],lw=1.2,zorder=3,clip_on=False)
a.set_xlim(.5,8.9); a.set_xticks(x7); a.set_xticklabels([f'D{d}' for d in x7],fontsize=11)
a.set_ylabel('Escore T (norma externa de atletas)',fontsize=11)
a.set_title('(A) Trajetória das seis subescalas do BRUMS ao longo da semana',
            fontsize=12,loc='left',fontweight='bold')
a.annotate('linha tracejada: média normativa (T = 50)',xy=(.015,.035),xycoords='axes fraction',
           fontsize=9,color=MUT,style='italic')
gy(a)
leg=[Patch(fc='#F0F1F2',ec='#6B7378',lw=1.4,label='Basal (D1)'),
     Patch(fc='#FBEAE3',ec='#C1440E',lw=1.4,label='HIIT (D2, D4, D7)'),
     Patch(fc='#E7EFF7',ec='#2166AC',lw=1.4,label='Amistoso (D3, D5)'),
     Patch(fc='#E4F1EC',ec='#1A9070',lw=1.4,label='Técnico/força (D6)')]
a.legend(handles=leg,fontsize=9.6,frameon=False,ncol=4,loc='upper center',bbox_to_anchor=(.5,-.085))
a2=ax[1]
zs={k:B1['PAGE'][k]['z'] for k in SUB}
ord2=sorted(SUB,key=lambda k:zs[k])
yp=np.arange(6)
a2.axvspan(-1.96,1.96,color='#F3F4F5',zorder=0)
a2.axvline(0,color='#8A9299',lw=1.3,zorder=2)
for i_,k in enumerate(ord2):
    z=zs[k]; pp=B1['PAGE'][k]['p']; sig=pp<.05
    a2.barh(yp[i_],z,height=.56,color=CV[k],alpha=.92 if sig else .28,
            edgecolor=CV[k],lw=1.8,zorder=3)
    a2.annotate(f'z = {vg(z,2)}\n{pv(pp)}',xy=(z,yp[i_]),xytext=(7 if z>0 else -7,0),
                textcoords='offset points',ha='left' if z>0 else 'right',va='center',
                fontsize=9.2,fontweight='bold',color=INK,linespacing=1.35)
a2.set_yticks(yp); a2.set_yticklabels(ord2,fontsize=11)
a2.set_xlim(-5.4,5.4); a2.set_xlabel('z do teste de tendência de Page (L)',fontsize=11)
a2.set_title('(B) Tendência ordenada D1→D7 — teste de Page',fontsize=12,loc='left',fontweight='bold')
a2.grid(axis='x',color=GRID,lw=.8,zorder=0); a2.set_axisbelow(True)
a2.annotate('faixa cinza: |z| < 1,96 (sem tendência monotônica);\nbarras esmaecidas: p ≥ 0,05',
            xy=(.60,.045),xycoords='axes fraction',fontsize=9,color=MUT,style='italic',linespacing=1.35)
rodape(fig,'166 pares atleta-dia. Escore T padronizado contra norma externa de atletas; 50 = média normativa. '
           'Fadiga em T alto indica mais fadiga; vigor em T baixo indica menos vigor.')
fig.tight_layout(); fig.savefig(f"{SAIDA}/E2fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E2 ok")

# ===================== E3: sinal, ruído e suavização =====================
fig,ax=plt.subplots(2,3,figsize=(17.2,9.0))
for i,k in enumerate(SUB):
    a=ax[i//3][i%3]; marcar(a,alpha=.75)
    d=S2['SER'][k]; m=np.array(d['med']); ep=np.array(d['ep']); sm=np.array(d['sm']); piso=d['piso']
    a.fill_between(x7,m-ep,m+ep,color=CV[k],alpha=.16,zorder=2,lw=0)
    a.plot(x7,m,'-o',color=CV[k],lw=1.6,ms=6,alpha=.45,zorder=3,mfc='white',mew=1.4)
    a.plot(x7,sm,'-',color=CV[k],lw=4.2,zorder=4,solid_capstyle='round')
    base=sm[0]
    a.axhline(base,color=MUT,lw=1.2,ls='--',zorder=2)
    a.axhspan(base-piso,base+piso,color='#6B7378',alpha=.10,zorder=1,lw=0)
    for c in d['choque']:
        a.plot([c,c+1],[sm[c-1],sm[c]],lw=9.0,color=CV[k],alpha=.26,zorder=3,solid_capstyle='round')
        a.plot([c,c+1],[sm[c-1],sm[c]],lw=1.9,color='#2A2F33',ls=(0,(1.1,1.5)),zorder=6)
        a.plot([(2*c+1)/2],[(sm[c-1]+sm[c])/2],marker='o',ms=8.5,mfc='#2A2F33',mec='white',
               mew=1.8,zorder=7)
    dt=sm[-1]-sm[0]
    ver='SINAL' if d['sinal'] else 'RUÍDO'
    a.text(.035,.94,f'{k}',transform=a.transAxes,fontsize=12.5,fontweight='bold',color=CV[k],va='top')
    y0,y1=a.get_ylim(); a.set_ylim(y0-(y1-y0)*.11,y1)
    y0,y1=a.get_ylim()
    baixo=(sm[0]-y0)/(y1-y0)<.40
    a.text(.035,.79 if baixo else .045,f'Δ D1→D7 = {vg(dt,2)}\npiso de ruído = ±{vg(piso,2)}',
           transform=a.transAxes,fontsize=9.4,color=MUT,
           va='top' if baixo else 'bottom',linespacing=1.45)
    a.add_patch(Rectangle((.72,.88),.25,.10,transform=a.transAxes,zorder=6,
                fc=CV[k] if d['sinal'] else '#FFFFFF',ec=CV[k],lw=1.8))
    a.text(.845,.93,ver,transform=a.transAxes,fontsize=10,fontweight='bold',ha='center',va='center',
           color='white' if d['sinal'] else CV[k],zorder=7)
    a.set_xlim(.5,7.5); a.set_xticks(x7); a.set_xticklabels([f'D{v}' for v in x7],fontsize=9.6)
    if i%3==0: a.set_ylabel('Escore bruto (0–16)',fontsize=10)
    gy(a)
h=[Line2D([],[],color=MUT,lw=1.6,marker='o',mfc='white',alpha=.5,label='série observada ± EPM'),
   Line2D([],[],color=MUT,lw=4.2,label='série suavizada (filtro binomial 1-2-1)'),
   Patch(fc='#6B7378',alpha=.22,label='banda do piso de ruído em torno do basal'),
   Line2D([],[],color='#2A2F33',lw=1.9,ls=(0,(1.1,1.5)),marker='o',ms=8.5,mfc='#2A2F33',mec='white',mew=1.8,label='transição de choque (|1.ª derivada| > piso)')]
fig.legend(handles=h,fontsize=10,frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.015))
fig.suptitle('Decomposição sinal–ruído das seis subescalas do BRUMS ao longo do microciclo',
             fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.005)
fig.tight_layout(rect=[0,.035,1,.99])
fig.savefig(f"{SAIDA}/E3fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E3 ok")
