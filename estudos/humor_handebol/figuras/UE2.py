# -*- coding: utf-8 -*-
import os
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"UEh.py")).read())
DIV=LinearSegmentedColormap.from_list('div',['#17456F','#2166AC','#8FB4D4','#F2F3F4',
                                             '#E9A98D','#C1440E','#7E2C09'])
TR=[f'D{d}→D{d+1}' for d in range(1,7)]
TRC=[CEST[TIPO[d+1]] for d in range(1,7)]

# ===================== E4: derivadas normalizadas pelo piso de ruído =====================
fig,ax=plt.subplots(1,2,figsize=(16.4,6.2),gridspec_kw={'width_ratios':[1,1]})
M1=np.array([[S2['SER'][k]['d1'][t]/S2['SER'][k]['piso'] for t in range(6)] for k in SUB])
M2=np.array([[S2['SER'][k]['d2'][t]/S2['SER'][k]['piso'] for t in range(5)] for k in SUB])
lim=float(np.abs(np.concatenate([M1.ravel(),M2.ravel()])).max())
for idx,(M,lab,tit) in enumerate([(M1,TR,'(A) 1.ª derivada — velocidade diária'),
        (M2,[f'em D{d}' for d in range(2,7)],'(B) 2.ª derivada — aceleração')]):
    a=ax[idx]
    im=a.imshow(M,cmap=DIV,vmin=-lim,vmax=lim,aspect='auto')
    for i in range(6):
        for j in range(M.shape[1]):
            v=M[i,j]
            forte=abs(v)>1
            a.text(j,i,vg(v,2),ha='center',va='center',fontsize=10.6,
                   color='white' if abs(v)>lim*.62 else INK,
                   fontweight='bold' if forte else 'normal')
            if forte:
                a.add_patch(Rectangle((j-.5,i-.5),1,1,fill=False,ec='#2A2F33',lw=2.4,zorder=5))
    a.set_xticks(range(M.shape[1])); a.set_xticklabels(lab,fontsize=10)
    a.set_yticks(range(6)); a.set_yticklabels(SUB,fontsize=11)
    cols=TRC if idx==0 else [CEST[TIPO[d]] for d in range(2,7)]
    for t,c in zip(a.get_xticklabels(),cols): t.set_color(c); t.set_fontweight('bold')
    for t,k in zip(a.get_yticklabels(),SUB): t.set_color(CV[k]); t.set_fontweight('bold')
    a.set_title(tit,fontsize=12,loc='left',fontweight='bold')
    a.set_xticks(np.arange(M.shape[1]+1)-.5,minor=True); a.set_yticks(np.arange(7)-.5,minor=True)
    a.grid(which='minor',color=SURF,lw=2.4); a.tick_params(which='minor',length=0)
    for sp in a.spines.values(): sp.set_visible(False)
cb=fig.colorbar(im,ax=ax,fraction=.030,pad=.02)
cb.set_label('derivada em unidades do piso de ruído da variável',fontsize=10.2)
cb.outline.set_visible(False)
fig.suptitle('Derivadas das séries diárias padronizadas pelo piso de ruído de cada subescala',
             fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.0)
fig.text(.011,-.035,'Moldura preta e negrito: |derivada| > 1 piso de ruído — variação que excede a flutuação amostral. '
         'A 2.ª derivada é avaliada no dia central de cada par de transições. Cores dos rótulos de coluna indicam o estímulo desse dia '
         '(laranja = HIIT, azul = amistoso, verde = técnico/força, cinza = basal).',
         fontsize=9,color=MUT,style='italic')
fig.savefig(f"{SAIDA}/E4fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E4 ok")

# ===================== E5: séries de prevalência dos seis perfis =====================
SP=E['SER_PERF']
fig,ax=plt.subplots(2,3,figsize=(17.2,9.0))
for i,nm in enumerate(PERF):
    a=ax[i//3][i%3]; marcar(a,alpha=.75)
    d=SP[nm]; y=np.array(d['y']); se=np.array(d['se']); sm=np.array(d['sm']); piso=d['piso']
    c=CPF[nm]
    a.fill_between(x7,y-se,y+se,color=c,alpha=.15,zorder=2,lw=0)
    a.plot(x7,y,'-o',color=c,lw=1.6,ms=6,alpha=.45,zorder=3,mfc='white',mew=1.4)
    a.plot(x7,sm,'-',color=c,lw=4.2,zorder=4,solid_capstyle='round')
    a.axhline(y[0],color=MUT,lw=1.2,ls='--',zorder=2)
    a.axhspan(y[0]-piso,y[0]+piso,color='#6B7378',alpha=.11,zorder=1,lw=0)
    for cc in d['choque']:
        a.plot([cc,cc+1],[sm[cc-1],sm[cc]],lw=9.0,color=c,alpha=.26,zorder=3,solid_capstyle='round')
        a.plot([cc,cc+1],[sm[cc-1],sm[cc]],lw=1.9,color='#2A2F33',ls=(0,(1.1,1.5)),zorder=6)
        a.plot([(2*cc+1)/2],[(sm[cc-1]+sm[cc])/2],marker='o',ms=8.5,mfc='#2A2F33',mec='white',
               mew=1.8,zorder=7)
    a.set_ylim(-3,58); a.set_xlim(.5,7.5); a.set_xticks(x7)
    a.set_xticklabels([f'D{v}' for v in x7],fontsize=9.6)
    if i%3==0: a.set_ylabel('Prevalência (%)',fontsize=10)
    a.text(.035,.955,nm,transform=a.transAxes,fontsize=12.2,fontweight='bold',color=c,va='top')
    a.text(.035,.845,f'Δ D1→D7 = {vg(d["dtot"])} p.p.\npiso de ruído = ±{vg(piso)} p.p.',
           transform=a.transAxes,fontsize=9.4,color=MUT,va='top',linespacing=1.45)
    frag=max(d['y'])<10
    rot='NÃO AVALIÁVEL' if frag else ('SINAL' if d['sinal'] else 'RUÍDO')
    larg=.38 if frag else .26
    a.add_patch(Rectangle((.97-larg,.90),larg,.085,transform=a.transAxes,zorder=6,
                fc=c if (d['sinal'] and not frag) else '#FFFFFF',ec=c,lw=1.8))
    a.text(.97-larg/2,.9425,rot,transform=a.transAxes,fontsize=9.4 if frag else 10,
           fontweight='bold',ha='center',va='center',
           color='white' if (d['sinal'] and not frag) else c,zorder=7)
    if max(d['y'])<10:
        a.annotate('prevalência ≤ 1 atleta por dia: o piso binomial\nencolhe e o critério deixa de discriminar',
                   xy=(.035,.40),xycoords='axes fraction',fontsize=8.8,color='#A31E52',
                   style='italic',linespacing=1.35,va='top')
    gy(a)
h=[Line2D([],[],color=MUT,lw=1.6,marker='o',mfc='white',alpha=.5,label='prevalência observada ± erro-padrão binomial'),
   Line2D([],[],color=MUT,lw=4.2,label='série suavizada (filtro binomial 1-2-1)'),
   Patch(fc='#6B7378',alpha=.22,label='banda do piso de ruído em torno do dia basal'),
   Line2D([],[],color='#2A2F33',lw=1.9,ls=(0,(1.1,1.5)),marker='o',ms=8.5,mfc='#2A2F33',mec='white',mew=1.8,label='transição de choque (|1.ª derivada| > piso)')]
fig.legend(handles=h,fontsize=10,frameon=False,ncol=4,loc='lower center',bbox_to_anchor=(.5,-.015))
fig.suptitle('Prevalência diária dos seis perfis de humor — sinal, ruído e transições de choque',
             fontsize=13.5,fontweight='bold',x=.011,ha='left',y=1.005)
fig.tight_layout(rect=[0,.035,1,.99])
fig.savefig(f"{SAIDA}/E5fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E5 ok")

# ===================== E6: perfis por tipo de estímulo =====================
EST4=['Basal','HIIT','Amistoso','Técnico']
fig,ax=plt.subplots(1,2,figsize=(16.6,6.2),gridspec_kw={'width_ratios':[1.55,1.0]})
a=ax[0]
w=.20; xb=np.arange(6)
for j,e in enumerate(EST4):
    v=[E['PREV_EST'][nm][e] for nm in PERF]
    n=E['NPOR'][e]
    ep=[100*np.sqrt(max(p/100*(1-p/100),0)/n) for p in v]
    a.bar(xb+(j-1.5)*w,v,width=w-.028,color=CEST[e],alpha=.90,edgecolor=SURF,lw=1.6,zorder=3,
          label=f'{e} (n = {n})')
    a.errorbar(xb+(j-1.5)*w,v,yerr=ep,fmt='none',ecolor='#4A5257',elinewidth=1.5,capsize=3,zorder=4)
    for i_,vv in enumerate(v):
        if vv>0.5:
            a.annotate(vg(vv),xy=(xb[i_]+(j-1.5)*w,vv+ep[i_]),xytext=(0,4),textcoords='offset points',
                       ha='center',fontsize=8.4,color=INK,rotation=90,va='bottom')
a.set_xticks(xb); a.set_xticklabels([p.replace(' de ','\nde ') for p in PERF],fontsize=10)
a.set_ylabel('Prevalência de pares atleta-dia (%)',fontsize=11); a.set_ylim(0,62)
a.legend(fontsize=10,frameon=False,ncol=4,loc='upper center',bbox_to_anchor=(.5,-.10))
a.set_title('(A) Distribuição dos seis perfis por tipo de estímulo',fontsize=12,loc='left',fontweight='bold')
a.annotate(f'χ² = {vg(E["chi"],2)}; gl = {E["gl"]}; {pv(E["p_chi"])} — a distribuição dos perfis\n'
           'não difere entre os tipos de estímulo',
           xy=(.985,.99),xycoords='axes fraction',ha='right',va='top',fontsize=10,color=INK,
           linespacing=1.4,bbox=dict(boxstyle='round,pad=0.5',fc='#F7F8F8',ec='#8A9299',lw=1.3))
gy(a)
a2=ax[1]
FX=['Favorável','Neutra','Risco']
CFX={'Favorável':'#1A9070','Neutra':'#6B7378','Risco':'#C1440E'}
bot=np.zeros(4)
for f in FX:
    v=np.array([E['FAIXA_EST'][f][e] for e in EST4])
    a2.bar(np.arange(4),v,bottom=bot,width=.66,color=CFX[f],alpha=.92,edgecolor=SURF,lw=2.0,
           zorder=3,label=f)
    for i_ in range(4):
        if v[i_]>4:
            a2.text(i_,bot[i_]+v[i_]/2,vg(v[i_]),ha='center',va='center',fontsize=10.6,
                    color='white',fontweight='bold',zorder=5)
    bot=bot+v
a2.set_xticks(range(4)); a2.set_xticklabels([f'{e}\n(n = {E["NPOR"][e]})' for e in EST4],fontsize=10.4)
a2.set_ylim(0,112); a2.set_yticks([0,20,40,60,80,100]); a2.set_ylabel('Composição da faixa de humor (%)',fontsize=11)
a2.legend(fontsize=10,frameon=False,ncol=3,loc='upper center',bbox_to_anchor=(.5,-.16))
a2.set_title('(B) Faixa de humor por tipo de estímulo',fontsize=12,loc='left',fontweight='bold')
a2.annotate(f'χ² = {vg(E["chi_f"],2)}; gl = {E["gl_f"]}; {pv(E["p_f"])}',
            xy=(.5,.99),xycoords='axes fraction',ha='center',va='top',fontsize=10.4,color=INK,
            bbox=dict(boxstyle='round,pad=0.42',fc='#FFFFFF',ec='#8A9299',lw=1.3))
gy(a2)
rodape(fig,'166 pares atleta-dia. Barras de erro: erro-padrão binomial. Nenhuma associação significativa entre '
           'tipo de estímulo e perfil ou faixa de humor.')
fig.tight_layout(); fig.savefig(f"{SAIDA}/E6fig.png",bbox_inches='tight',facecolor=SURF); plt.close(fig)
print("E6 ok")
