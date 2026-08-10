# -*- coding: utf-8 -*-
"""Gera gráficos ÚNICOS (um por figura), no padrão visual do Showcase — fundo
transparente, tema escuro futurista, paleta neon (ciano/coral/violeta/dourado).
Uso: python showcase_figs.py → showcase_figs/*.png
Dependências: numpy pandas matplotlib."""
import os, json, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
OUT=os.path.join(HERE,'showcase_figs'); os.makedirs(OUT,exist_ok=True)
D=json.load(open(os.path.join(HERE,'dashboard_data.json'),encoding='utf-8'))
EP=json.load(open(os.path.join(ROOT,'invariancia_multigrupo','resultados_estrita_parcial.json'),encoding='utf-8'))
HP=json.load(open(os.path.join(ROOT,'dias_hiit','resultados_hiit_protocolo.json'),encoding='utf-8'))
CH=json.load(open(os.path.join(ROOT,'carga_humor','resultados_carga_humor.json'),encoding='utf-8'))

INK='#e8f1ff'; MUT='#8aa0c0'; FAINT='#5a6b86'; CYAN='#22d3ee'; TEAL='#2dd4bf'; CORAL='#ff4d6d'; VIOLET='#7c5cff'; GOLD='#ffd166'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':'#3a4a66','axes.labelcolor':MUT,
 'xtick.color':MUT,'ytick.color':MUT,'axes.facecolor':'none','figure.facecolor':'none','savefig.facecolor':'none',
 'font.size':12,'axes.titlecolor':INK,'axes.titlesize':14,'axes.titleweight':'bold'})
GRID=dict(color='#8aa0c0',alpha=.14,lw=.9)
def clean(ax):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color('#3a4a66')
def save(fig,name):
    fig.savefig(os.path.join(OUT,name),dpi=150,transparent=True,bbox_inches='tight'); plt.close(fig)

# 1 — resposta aguda dz (barh)
ag=D['inf']['A_aguda']; ag=sorted(ag,key=lambda x:x['dz'])
labs=[x['label'] for x in ag]; vals=[x['dz'] for x in ag]
cols=[CYAN if v<0 else (VIOLET if 'PTH' in l else CORAL) for l,v in zip(labs,vals)]
fig,ax=plt.subplots(figsize=(7.4,4.4),dpi=150)
ax.barh(labs,vals,color=cols,edgecolor='none',height=.66)
ax.axvline(0,color=FAINT,lw=1); ax.grid(axis='x',**GRID); ax.set_axisbelow(True)
for i,v in enumerate(vals): ax.text(v+(.03 if v>=0 else -.03),i,('+' if v>=0 else '')+f'{v:.2f}'.replace('.',','),va='center',ha='left' if v>=0 else 'right',fontsize=10,color=INK)
ax.set_title('Resposta aguda pré→pós (dz)',loc='left'); ax.set_xlim(-.8,1.3); clean(ax)
save(fig,'01_dz.png')

# 2 — radar do perfil pré vs pós
subs=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; pre=D['pv']['perfil']['medias']['pre']; pos=D['pv']['perfil']['medias']['pos']
ang=np.linspace(0,2*np.pi,len(subs),endpoint=False); ang=np.concatenate([ang,ang[:1]])
fig=plt.figure(figsize=(5.6,5.2),dpi=150); ax=fig.add_subplot(111,polar=True)
for data,c,lb in [(pre,CYAN,'pré'),(pos,CORAL,'pós')]:
    v=[data[s] for s in subs]; v=v+v[:1]
    ax.plot(ang,v,color=c,lw=2.2,label=lb); ax.fill(ang,v,color=c,alpha=.14)
ax.set_xticks(ang[:-1]); ax.set_xticklabels(subs,color=INK,fontsize=10.5)
ax.set_yticklabels([]); ax.grid(color='#8aa0c0',alpha=.16); ax.spines['polar'].set_color('#3a4a66')
ax.set_title('Perfil de humor — pré vs. pós',loc='left',pad=18)
ax.legend(loc='upper right',bbox_to_anchor=(1.14,1.12),frameon=False,labelcolor=INK)
save(fig,'02_radar.png')

# 3 — HIIT: FC por fase (pico vs recuperação)
pf=HP['por_fase']; ROT={'aquec':'Aquec.','se1':'Série 1','se2':'Série 2','se3':'Série 3','se4':'Série 4'}
xs=[ROT[r['fase']] for r in pf]; pico=[r['fc_pos_m'] for r in pf]; recu=[r['fc_pre_m'] for r in pf]
fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=150); x=np.arange(len(xs))
ax.plot(x,pico,'-o',color=CORAL,lw=2.4,ms=7,label='FC ao fim (pico)')
ax.plot(x,recu,'-o',color=CYAN,lw=2.4,ms=7,label='FC ao início (recuperação)')
ax.set_xticks(x); ax.set_xticklabels(xs); ax.grid(axis='y',**GRID); ax.set_axisbelow(True)
ax.set_ylabel('bpm'); ax.set_title('HIIT — FC ao longo das séries',loc='left'); ax.legend(frameon=False,labelcolor=INK,fontsize=10); clean(ax)
save(fig,'03_hiit_fc.png')

# 4 — HIIT: PSE por fase
pse=[r['pse_m'] for r in pf]; psd=[r['pse_sd'] for r in pf]
fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=150)
ax.bar(x,pse,yerr=psd,color=GOLD,alpha=.9,edgecolor='none',width=.62,ecolor=MUT,capsize=3)
ax.set_xticks(x); ax.set_xticklabels(xs); ax.set_ylim(0,10.6); ax.grid(axis='y',**GRID); ax.set_axisbelow(True)
ax.set_ylabel('PSE (0–10)'); ax.set_title('HIIT — esforço percebido por fase',loc='left'); clean(ax)
save(fig,'04_hiit_pse.png')

# 5 — invariância: CFI ao longo da hierarquia
lv=['Configural','Métrica','Escalar','Estrita']; iv=D['rob']['invmg']
cfis=[iv['cfi_pre'],iv['metrico_conjunto'].get('cfi',iv['estrita']['cfi_metrico']),iv['estrita']['cfi_metrico'],iv['estrita']['cfi_estrito']]
fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=150); xx=np.arange(4)
ax.plot(xx,cfis,'-o',color=VIOLET,lw=2.6,ms=9)
for i,c in enumerate(cfis): ax.annotate(f'{c:.3f}'.replace('.',','),(i,c),textcoords='offset points',xytext=(0,10),ha='center',fontsize=10,color=INK)
ax.set_xticks(xx); ax.set_xticklabels(lv); ax.set_ylim(.85,.95); ax.grid(axis='y',**GRID); ax.set_axisbelow(True)
ax.set_ylabel('CFI (combinado)'); ax.set_title('Invariância — CFI na hierarquia',loc='left'); clean(ax)
save(fig,'05_inv_cfi.png')

# 6 — invariância: não-invariância por item (|resíduo de intercepto|)
di=EP['diagnostico_item']; di=sorted(di,key=lambda r:abs(r['residuo_intercepto']))
il=[r['item'] for r in di]; iv2=[abs(r['residuo_intercepto']) for r in di]
cc=[CORAL if r['item'] in EP['parcial']['itens_liberados'] else '#3f5170' for r in di]
fig,ax=plt.subplots(figsize=(7.4,5.0),dpi=150)
ax.barh(il,iv2,color=cc,edgecolor='none',height=.7); ax.axvline(0.2,color=MUT,ls=':',lw=1)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_title('Invariância — não-invariância por item',loc='left')
ax.set_xlabel('|resíduo de intercepto|'); clean(ax)
save(fig,'06_inv_item.png')

# 7 — preditores de fadiga (AUC), cor por confiabilidade
cp=sorted(CH['preditores_fadiga']['preditores'],key=lambda x:x['AUC'])
pl=[x['label'] for x in cp]; au=[x['AUC'] for x in cp]; icc=[x['ICC21'] or 0 for x in cp]
def lerp(a,b,t):
    import matplotlib.colors as mc; a=np.array(mc.to_rgb(a)); b=np.array(mc.to_rgb(b)); return tuple(a+(b-a)*t)
colp=[lerp('#3f5170',CYAN,min(max(i/0.85,0),1)) for i in icc]
fig,ax=plt.subplots(figsize=(7.4,4.6),dpi=150)
ax.barh(pl,au,color=colp,edgecolor='none',height=.7); ax.axvline(0.5,color=FAINT,lw=1)
for i,v in enumerate(au): ax.text(v+.01,i,f'{v:.2f}'.replace('.',','),va='center',fontsize=10,color=INK)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_xlim(.45,1.0); ax.set_xlabel('AUC (fadiga alta vs. baixa)')
ax.set_title('Preditores de fadiga — sensibilidade (cor = confiabilidade)',loc='left'); clean(ax)
save(fig,'07_pred.png')

# 8 — acoplamento carga × humor (heatmap tônico)
LO=['PSE','FC','TRIMP']; MO=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','PTH','FadFis','FadMen']
pares=CH['acoplamento']['tonico']['pares']
M=np.array([[next(p['r'] for p in pares if p['carga']==L and p['humor']==Mh) for Mh in MO] for L in LO])
fig,ax=plt.subplots(figsize=(7.6,3.2),dpi=150)
im=ax.imshow(M,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
ax.set_xticks(range(len(MO))); ax.set_xticklabels(MO,rotation=45,ha='right',fontsize=9,color=INK)
ax.set_yticks(range(len(LO))); ax.set_yticklabels(LO,fontsize=10,color=INK)
for i in range(len(LO)):
    for j in range(len(MO)): ax.text(j,i,f'{M[i,j]:+.2f}'.replace('.',','),ha='center',va='center',fontsize=7.5,color='white' if abs(M[i,j])>.5 else '#dbe6f5')
ax.set_title('Acoplamento carga × humor (r, nível do atleta)',loc='left',color=INK)
cb=fig.colorbar(im,fraction=.025,pad=.02); cb.ax.tick_params(colors=MUT,labelsize=8); cb.outline.set_edgecolor('#3a4a66')
save(fig,'08_acopl.png')

# 9 — acúmulo do PTH ao longo do microciclo
tr=D['dh']['trajetoria']; days=sorted(int(k) for k in tr); yv=[tr[str(d)] for d in days]
fig,ax=plt.subplots(figsize=(7.4,4.2),dpi=150)
ax.plot(days,yv,'-o',color=CYAN,lw=2.6,ms=7)
ax.fill_between(days,yv,min(yv)-.5,color=CYAN,alpha=.10)
for hd in D['dh']['dias_hiit']: ax.axvline(hd,color=CORAL,ls='--',lw=1,alpha=.6)
ax.text(D['dh']['dias_hiit'][-1],max(yv),'  dias de HIIT',color=CORAL,fontsize=9,va='top')
ax.set_xticks(days); ax.grid(axis='y',**GRID); ax.set_axisbelow(True)
ax.set_xlabel('dia do microciclo'); ax.set_ylabel('PTH (TMD)'); ax.set_title('Acúmulo da perturbação (D1→D7)',loc='left'); clean(ax)
save(fig,'09_acumulo.png')

# 10 — variância entre atletas (traço)
va=sorted(D['pv']['variabilidade'],key=lambda x:x['pct_entre'])
vl=[x['var'] for x in va]; vp=[x['pct_entre'] for x in va]
fig,ax=plt.subplots(figsize=(7.4,4.4),dpi=150)
ax.barh(vl,vp,color=[TEAL if p>=50 else GOLD for p in vp],edgecolor='none',height=.7); ax.axvline(50,color=MUT,ls=':',lw=1)
for i,v in enumerate(vp): ax.text(v+1,i,f'{v:.0f}%',va='center',fontsize=9.5,color=INK)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_xlim(0,100); ax.set_xlabel('% da variância entre atletas (traço)')
ax.set_title('Variância: traço vs. estado',loc='left'); clean(ax)
save(fig,'10_variancia.png')

# 11 — segmentação (perfil-z por grupo)
seg=D['pv']['segmentacao']['perfis']; gsubs=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
fig,ax=plt.subplots(figsize=(7.8,4.4),dpi=150); w=.26; xg=np.arange(len(gsubs))
gc={'Resiliente':TEAL,'Perturbado':GOLD,'Extremo':CORAL}
for k,g in enumerate(seg):
    ax.bar(xg+(k-1)*w,[g[s] for s in gsubs],w,color=gc.get(g['grupo'],VIOLET),edgecolor='none',label=g['grupo'])
ax.axhline(0,color=FAINT,lw=1); ax.set_xticks(xg); ax.set_xticklabels(gsubs,fontsize=9.5,color=INK)
ax.grid(axis='y',**GRID); ax.set_axisbelow(True); ax.set_ylabel('escore-z'); ax.set_title('Segmentação — perfil-z por grupo',loc='left')
ax.legend(frameon=False,labelcolor=INK,fontsize=9,ncol=3,loc='upper center',bbox_to_anchor=(.5,1.16)); clean(ax)
save(fig,'11_segmentacao.png')

# ---- dados extra ----
import pandas as pd
bm=pd.read_csv(os.path.join(ROOT,'modelagem','base_modelagem.csv'))
LIM=json.load(open(os.path.join(ROOT,'limites_derivadas','resultados_limites_derivadas.json'),encoding='utf-8'))

# 12 — curvas ROC (pós vs pré) por variável
def roc_pts(y,x):
    x=np.asarray(x,float); y=np.asarray(y,int); o=np.argsort(-x); y=y[o]
    P=y.sum(); N=len(y)-P; tp=fp=0; xs=[0]; ys=[0]
    for yi in y:
        if yi: tp+=1
        else: fp+=1
        xs.append(fp/N if N else 0); ys.append(tp/P if P else 0)
    trap=getattr(np,'trapezoid',None) or np.trapz
    auc=trap(ys,xs); return xs,ys,auc
pp=bm[bm.momento.isin(['pre','pos'])].dropna(subset=['FadFis','Fadiga','Vigor','PTH'])
y=(pp['momento']=='pos').astype(int).values
fig,ax=plt.subplots(figsize=(6.4,5.2),dpi=150)
for var,c,inv3 in [('FadFis',CORAL,1),('PTH',VIOLET,1),('Fadiga','#ff8aa8',1),('Vigor',CYAN,-1)]:
    xs,ys,auc=roc_pts(y,inv3*pp[var].values)
    ax.plot(xs,ys,color=c,lw=2.4,label=f'{var}  AUC {auc:.2f}'.replace('.',','))
ax.plot([0,1],[0,1],color=FAINT,ls='--',lw=1)
ax.set_xlim(0,1); ax.set_ylim(0,1.02); ax.grid(**GRID); ax.set_axisbelow(True)
ax.set_xlabel('1 − especificidade'); ax.set_ylabel('sensibilidade'); ax.set_title('Curvas ROC — separar pós de pré',loc='left')
ax.legend(frameon=False,labelcolor=INK,fontsize=9.5,loc='lower right'); clean(ax)
save(fig,'12_roc.png')

# 13 — cálculo: f(t), f'(t), f''(t)
cd=LIM['C_derivadas']; t=[r['dia'] for r in cd]; f=[r['f'] for r in cd]; f1=[r['f_linha'] for r in cd]; f2=[r['f_2linha'] for r in cd]
fig,ax=plt.subplots(figsize=(7.4,4.4),dpi=150)
ax.plot(t,f,'-o',color=CORAL,lw=2.6,ms=6,label="f(t) — fadiga física")
ax.fill_between(t,f,min(f)-.2,color=CORAL,alpha=.08)
ax2=ax.twinx(); ax2.plot(t,f1,'-o',color=CYAN,lw=2.2,ms=5,label="f′(t) — velocidade")
ax2.plot(t,f2,'-o',color=VIOLET,lw=1.8,ms=4,label="f″(t) — aceleração"); ax2.axhline(0,color=FAINT,lw=.8)
ax2.tick_params(colors=MUT); ax2.spines['top'].set_visible(False); ax2.set_ylabel("f′, f″",color=MUT)
ax.set_xticks(t); ax.grid(axis='y',**GRID); ax.set_axisbelow(True); ax.set_xlabel('dia (t)'); ax.set_ylabel('f(t)',color=CORAL)
ax.set_title('Cálculo — limites e derivadas do acúmulo',loc='left')
l1,la1=ax.get_legend_handles_labels(); l2,la2=ax2.get_legend_handles_labels()
ax.legend(l1+l2,la1+la2,frameon=False,labelcolor=INK,fontsize=9,loc='lower right'); clean(ax)
save(fig,'13_calculo.png')

# 14 — Bland–Altman (concordância BRUMS Fadiga × fadiga física externa, % do máx)
d2=bm.dropna(subset=['Fadiga','FadFis']).copy()
a=d2['Fadiga']/d2['Fadiga'].max()*100; b=d2['FadFis']/10*100
mean=(a+b)/2; diff=a-b; bias=diff.mean(); sd=diff.std(); lo,hi=bias-1.96*sd,bias+1.96*sd
fig,ax=plt.subplots(figsize=(7.0,4.6),dpi=150)
ax.scatter(mean,diff,s=26,c=CYAN,alpha=.45,edgecolor='none')
ax.axhline(bias,color=GOLD,lw=1.8,label=f'viés {bias:+.1f}%'.replace('.',','))
ax.axhline(hi,color=CORAL,ls='--',lw=1.4); ax.axhline(lo,color=CORAL,ls='--',lw=1.4,label='LoA 95%')
ax.grid(**GRID); ax.set_axisbelow(True); ax.set_xlabel('média dos dois métodos (% do máx)'); ax.set_ylabel('diferença (% do máx)')
ax.set_title('Bland–Altman — convergência, não equivalência',loc='left'); ax.legend(frameon=False,labelcolor=INK,fontsize=9.5); clean(ax)
save(fig,'14_bland.png')

# 15 — predição fora da amostra (R² LOAO)
reg=D['pred']['reg']; alvos=['PTH (TMD)','Fadiga física','Vigor']; preds=['Baseline (pré)','Baseline + contexto']
fig,ax=plt.subplots(figsize=(7.4,4.4),dpi=150); xa=np.arange(len(alvos)); w=.36
for k,pr in enumerate(preds):
    vals=[next((r['R2'] for r in reg if r['alvo']==al and r['preditores']==pr),0) for al in alvos]
    ax.bar(xa+(k-.5)*w,vals,w,color=[CYAN,VIOLET][k],edgecolor='none',label=pr)
ax.axhline(0,color=FAINT,lw=1); ax.set_xticks(xa); ax.set_xticklabels(alvos,fontsize=10,color=INK)
ax.grid(axis='y',**GRID); ax.set_axisbelow(True); ax.set_ylabel('R² fora da amostra')
ax.set_title('Predição LOAO — o sinal vem do baseline',loc='left'); ax.legend(frameon=False,labelcolor=INK,fontsize=9); clean(ax)
save(fig,'15_loao.png')

# 16 — correlações rm_corr (intra-sujeito) significativas
rc=[x for x in D['inf']['D_rmcorr'] if x['sig']]; rc=sorted(rc,key=lambda x:x['r'])[:10]
labs2=[f"{x['sub']}×{x['ext']}" for x in rc]; rv=[x['r'] for x in rc]
fig,ax=plt.subplots(figsize=(7.4,4.6),dpi=150)
ax.barh(labs2,rv,color=[CORAL if v>=0 else CYAN for v in rv],edgecolor='none',height=.7); ax.axvline(0,color=FAINT,lw=1)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_xlabel('r (medidas repetidas, intra-atleta)')
ax.set_title('Correlações intra-sujeito (validade convergente)',loc='left'); clean(ax)
save(fig,'16_rmcorr.png')

print('gerados', len(os.listdir(OUT)), 'gráficos em', OUT)
