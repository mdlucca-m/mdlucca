# -*- coding: utf-8 -*-
import os; exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UVh.py")).read())

# ============ F1: desenho do microciclo + cadeia de processamento ============
fig=plt.figure(figsize=(17.6,10.4))
axA=fig.add_axes([0.055,0.615,0.90,0.345]); axA.axis('off'); axA.set_xlim(.5,7.5); axA.set_ylim(0,100)
fig.text(0.012,0.987,'(A) Microciclo terminal de pré-temporada — estímulos, carga e janelas observadas de coleta',
         fontsize=13,fontweight='bold',color=INK,va='top')
BW=.88
for d in range(1,8):
    t=TIPO[d]; c=CEST[t]; cg=CARGA[str(d)]
    axA.add_patch(FancyBboxPatch((d-BW/2,58),BW,34,boxstyle="round,pad=0.02,rounding_size=.05",
                  fc=FUN[t],ec=c,lw=2.0,zorder=3,mutation_aspect=.06))
    axA.text(d,84,f'Dia {d}',fontsize=12.5,fontweight='bold',ha='center',va='center',color=INK,zorder=4)
    axA.text(d,73,t,fontsize=10.6,ha='center',va='center',color=c,fontweight='bold',zorder=4)
    axA.text(d,63.5,f'{vg(cg["h"])} h · {cg["ses"]} '+('sessão' if cg['ses']==1 else 'sessões'),
             fontsize=9.4,ha='center',va='center',color=MUT,zorder=4)
    jan=[r['ts'][11:16] for r in B['registros'] if r['dia']==d]
    if d==1:
        axA.add_patch(FancyBboxPatch((d-BW/2,28),BW,20,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#2A2F33',ec='none',zorder=3,mutation_aspect=.06))
        axA.text(d,38,'JANELA ÚNICA\nnoturna\n20h42–01h19',fontsize=8.4,ha='center',va='center',
                 color='white',fontweight='bold',zorder=4,linespacing=1.35)
    else:
        w=BW/2-.045
        axA.add_patch(FancyBboxPatch((d-BW/2,28),w,20,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#FFFFFF',ec='#8A9299',lw=1.6,zorder=3,mutation_aspect=.06))
        axA.text(d-BW/2+w/2,38,f'PRÉ\n{min(jan)}',fontsize=8.6,ha='center',va='center',color=INK,zorder=4,linespacing=1.35)
        axA.add_patch(FancyBboxPatch((d+.045,28),w,20,boxstyle="round,pad=0.02,rounding_size=.05",
                      fc='#4A5257' if d<7 else '#8A9299',ec='none',zorder=3,mutation_aspect=.06))
        axA.text(d+.045+w/2,38,f'PÓS\n{max(jan)}',fontsize=8.6,ha='center',va='center',
                 color='white',fontweight='bold',zorder=4,linespacing=1.35)
        axA.add_patch(FancyArrowPatch((d-.10,38),(d+.02,38),arrowstyle='-|>',mutation_scale=12,lw=1.6,color='#C1440E',zorder=5))
    if d<7:
        axA.add_patch(FancyArrowPatch((d+BW/2+.015,38),(d+1-BW/2-.015,38),arrowstyle='-|>',
                      mutation_scale=12,lw=1.6,color='#2166AC',zorder=5,linestyle=(0,(2.5,1.8))))
axA.text(.55,14,'laranja = custo do dia (pré→pós)   ·   tracejada azul = restituição noturna   ·   '
                'em D7 não há medida noturna: o «pós» é do início da tarde',
         fontsize=9.6,color=MUT,style='italic',va='center')
axB=fig.add_axes([0.055,0.487,0.90,0.115])
ac=[CARGA[str(d)]['acum'] for d in range(1,8)]
axB.fill_between(x7,0,ac,color='#2166AC',alpha=.13,zorder=1)
axB.plot(x7,ac,'-o',color='#2166AC',lw=3.0,ms=8,mfc='white',mew=2.4,zorder=3)
for i_,v in enumerate(ac):
    axB.annotate(vg(v),xy=(i_+1,v),xytext=(0,9),textcoords='offset points',ha='center',fontsize=9,
                 fontweight='bold',color='#2166AC')
axB.set_xlim(.5,7.5); axB.set_ylim(0,28); axB.set_xticks(x7); axB.set_yticks([0,10,20])
axB.set_ylabel('Carga\nacumulada (h)',fontsize=9.5,linespacing=1.2)
axB.set_xticklabels([f'D{d}' for d in x7],fontsize=9.5); gy(axB)
axC=fig.add_axes([0.012,0.03,0.976,0.40]); axC.axis('off'); axC.set_xlim(0,100); axC.set_ylim(0,100)
axC.text(0,99,'(B) Cadeia de processamento — do formulário ao veredito',fontsize=13,fontweight='bold',color=INK,va='top')
et=[('1. Fonte-verdade\nexport do formulário\n457 registros','#F0F1F2','#6B7378'),
    ('2. Limpeza\ndia pelo carimbo (04h)\nórfãos devolvidos','#FDF3E4','#E0952B'),
    ('3. Unidade\num valor por atleta\ne por dia — 166 pares','#E7EFF7','#2166AC'),
    ('4. Padronização\nescore T contra norma\nexterna de atletas','#E4F1EC','#1A9070'),
    ('5. Classificação\nk-médias semeado nos\nseis perfis canônicos','#F1EAF9','#8A4FBF'),
    ('6. Suavização\nfiltro binomial 1-2-1\nsobre a série diária','#FBEAE3','#C1440E'),
    ('7. Derivadas e piso\n1.ª e 2.ª em unidades\ndo piso de ruído','#F7E4EC','#A31E52')]
bw=12.6; gap=1.6; bx=0.6
for i_,(t,fc,ec) in enumerate(et):
    X=bx+i_*(bw+gap)
    axC.add_patch(FancyBboxPatch((X,58),bw,28,boxstyle="round,pad=0.5,rounding_size=1.6",fc=fc,ec=ec,lw=2.0,zorder=3))
    axC.text(X+bw/2,72,t,fontsize=9.6,ha='center',va='center',color=INK,zorder=4,linespacing=1.55)
    if i_<6: axC.add_patch(FancyArrowPatch((X+bw+0.15,72),(X+bw+gap-0.15,72),arrowstyle='-|>',
                            mutation_scale=14,lw=1.9,color='#8A9299',zorder=2))
xdir=bx+(bw+gap)*6+bw
axC.plot([bx,xdir],[52,52],color='#8A9299',lw=1.9,zorder=2,solid_capstyle='round')
for xv in [bx+bw/2,bx+(bw+gap)*3+bw/2,xdir-bw/2]: axC.plot([xv,xv],[57.6,52],color='#8A9299',lw=1.9,zorder=2)
w1=bw*3+gap*2
axC.add_patch(FancyBboxPatch((bx,20),w1,24,boxstyle="round,pad=0.5,rounding_size=1.6",fc='#FFFFFF',ec='#2A2F33',lw=2.2,zorder=3))
axC.text(bx+w1/2,32,'Veredito de sinal\n|Δ D1→D7| > piso de ruído  →  variação real\ncaso contrário  →  flutuação amostral',
         fontsize=10.4,ha='center',va='center',color=INK,zorder=4,linespacing=1.55,fontweight='bold')
X2=bx+(bw+gap)*3.6; w2=bw*3.4+gap*2
axC.add_patch(FancyBboxPatch((X2,20),w2,24,boxstyle="round,pad=0.5,rounding_size=1.6",fc='#FFFFFF',ec='#2A2F33',lw=2.2,zorder=3))
axC.text(X2+w2/2,32,'Teste de cruzamento\ninversão só é declarada quando a diferença entre duas séries\nultrapassa o limiar antes e depois do ponto de troca',
         fontsize=10.4,ha='center',va='center',color=INK,zorder=4,linespacing=1.55,fontweight='bold')
for xv,ww in [(bx,w1),(X2,w2)]:
    axC.add_patch(FancyArrowPatch((xv+ww/2,52),(xv+ww/2,44.6),arrowstyle='-|>',mutation_scale=14,lw=1.9,color='#8A9299',zorder=2))
rod(fig,'Fonte: elaboração própria. Python 3 (openpyxl, NumPy, SciPy, statsmodels, matplotlib); tudo reproduzível por um comando.')
salvar(fig,'F1fig')

# ============ F2: as quatro unidades de análise (resultado da auditoria) ============
fig=plt.figure(figsize=(17.0,8.6))
gs=fig.add_gridspec(2,2,height_ratios=[1.0,1.05],width_ratios=[1.25,1.0],hspace=.42,wspace=.24)
UN=AU['UNIDADES']; REC=Q['REC']
a=fig.add_subplot(gs[0,:]); a.axis('off'); a.set_xlim(0,100); a.set_ylim(0,100)
a.text(0,98,'(A) As quatro unidades de análise que circulavam nos manuscritos',fontsize=12.5,fontweight='bold',va='top')
CU=['#6B7378','#E0952B','#1A9070','#8A4FBF']
for i_,u in enumerate(UN):
    X=1+i_*24.6
    esc = u['sigla']=='U-AD'
    a.add_patch(FancyBboxPatch((X,4),22.6,76,boxstyle="round,pad=0.6,rounding_size=1.6",
                fc='#F3F7F4' if esc else '#FFFFFF',ec=CU[i_],lw=3.0 if esc else 1.8,zorder=3))
    a.text(X+11.3,72,u['sigla'],fontsize=15,fontweight='bold',ha='center',color=CU[i_],zorder=4)
    a.text(X+11.3,63,u['nome'],fontsize=11,ha='center',color=INK,zorder=4)
    a.text(X+11.3,55,f"n = {u['n']}",fontsize=13,fontweight='bold',ha='center',color=CU[i_],zorder=4)
    import textwrap as _tw
    a.text(X+11.3,40,_tw.fill(u['regra'],34),fontsize=8.6,ha='center',va='center',color=INK,zorder=4,
           linespacing=1.55)
    a.text(X+11.3,17,_tw.fill(u['vies'],36),fontsize=8.2,ha='center',va='center',color=MUT,zorder=4,
           style='italic',linespacing=1.55)
    if esc: a.text(X+11.3,84,'▼ unidade adotada',fontsize=9.6,ha='center',fontweight='bold',color='#1A9070')
a2=fig.add_subplot(gs[1,0])
sig=[u['sigla'] for u in UN]
ic=[]
for u in sig:
    lb=np.array(Q['lab_AD']) if u=='U-AD' else None
prev=[REC[u]['prev'] for u in sig]
xb=np.arange(6); w=.2
for j,u in enumerate(sig):
    a2.bar(xb+(j-1.5)*w, prev[j], width=w-.03, color=CU[j], alpha=.92, edgecolor=SURF, lw=1.4,
           zorder=3, label=f"{u} (n = {REC[u]['n']})")
a2.plot(xb, Q['PREV_REF'], 'D', color='#2A2F33', ms=8, zorder=5, label='referência de 2017')
a2.set_xticks(xb); a2.set_xticklabels([p.replace(' de ','\nde ').replace(' invertido','\ninvertido') for p in PERF],fontsize=9)
a2.set_ylabel('Prevalência (%)',fontsize=11); a2.set_ylim(0,40)
a2.set_title('(B) A distribuição dos perfis muda pouco entre unidades…',fontsize=11.5,loc='left',fontweight='bold')
a2.legend(fontsize=8.8,frameon=False,ncol=2); gy(a2)
a3=fig.add_subplot(gs[1,1])
D17={'U-R':(35.4,21.7),'U-286':(22.2,21.6),'U-AD':(37.0,19.0),'U-PAR':(28.6,19.0)}
yb=np.arange(4)[::-1]
for i_,u in enumerate(sig):
    d1,d7=D17[u]; delta=d7-d1
    a3.plot([d1,d7],[yb[i_],yb[i_]],'-',color=CU[i_],lw=3.4,zorder=3,solid_capstyle='round')
    a3.plot([d1],[yb[i_]],'o',color=CU[i_],ms=11,mfc='white',mew=2.8,zorder=4)
    a3.plot([d7],[yb[i_]],'o',color=CU[i_],ms=11,zorder=4)
    a3.annotate(f'{vg(delta)} p.p.',xy=(max(d1,d7)+1.4,yb[i_]),va='center',fontsize=10.6,
                fontweight='bold',color=CU[i_])
a3.set_yticks(yb); a3.set_yticklabels(sig,fontsize=11)
for t,c in zip(a3.get_yticklabels(),CU): t.set_color(c); t.set_fontweight('bold')
a3.set_xlim(15,48); a3.set_xlabel('Prevalência do perfil iceberg (%)',fontsize=11)
a3.set_title('(C) …mas a variação de D1 a D7 vai de −0,6 a −18,0 p.p.',fontsize=11.5,loc='left',fontweight='bold')
a3.annotate('círculo vazado = D1   ·   cheio = D7',xy=(.98,.98),xycoords='axes fraction',ha='right',va='top',
            fontsize=9,color=MUT,style='italic')
gx(a3)
rod(fig,'Mesmos dados, mesma classificação, mesmos centroides. A única coisa que muda é quem conta como uma observação.')
salvar(fig,'F2fig')
