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

print('gerados', len(os.listdir(OUT)), 'gráficos em', OUT)
