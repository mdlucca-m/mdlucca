# -*- coding: utf-8 -*-
"""Quatro análises complementares, no mesmo padrão visual do showcase:
 (1) RCI / MDC — mudança confiável por atleta (respondedores vs. ruído de medida);
 (2) TOST — testes de equivalência para os achados nulos (desacoplamento; HIIT vs sem);
 (3) Rede psicométrica (correlações parciais / modelo gráfico gaussiano);
 (4) Trajetória intradia pré → mid → pós (cinética aguda).
Gera resultados_extras.json e figuras escuras/transparentes em ../tese/showcase_figs/.
Uso: python extras.py"""
import os, json, numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
FIGD=os.path.join(ROOT,'tese','showcase_figs'); os.makedirs(FIGD,exist_ok=True)
bm=pd.read_csv(os.path.join(ROOT,'modelagem','base_modelagem.csv'))
conf={c['sub']:c for c in json.load(open(os.path.join(ROOT,'confiabilidade_invariancia','resultados_confiabilidade.json')))['A_confiabilidade']}
D=json.load(open(os.path.join(ROOT,'tese','dashboard_data.json')))

INK='#e8f1ff'; MUT='#8aa0c0'; FAINT='#5a6b86'; CYAN='#22d3ee'; TEAL='#2dd4bf'; CORAL='#ff4d6d'; VIOLET='#7c5cff'; GOLD='#ffd166'; GREEN='#34d399'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':'#3a4a66','axes.labelcolor':MUT,
 'xtick.color':MUT,'ytick.color':MUT,'axes.facecolor':'none','figure.facecolor':'none','savefig.facecolor':'none',
 'font.size':12,'axes.titlecolor':INK,'axes.titlesize':14,'axes.titleweight':'bold'})
GRID=dict(color='#8aa0c0',alpha=.14,lw=.9)
def clean(ax):
    for s in ['top','right']: ax.spines[s].set_visible(False)
    for s in ['left','bottom']: ax.spines[s].set_color('#3a4a66')
def save(fig,name): fig.savefig(os.path.join(FIGD,name),dpi=150,transparent=True,bbox_inches='tight'); plt.close(fig)
def vv(x): return f"{x:.2f}".replace('.',',')

OUT={}
SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']

# ============ (1) RCI / MDC ============
# SEM = DP * sqrt(1-alpha); MDC95 = 1.96*sqrt(2)*SEM; RCI_i = (pós-pré)/(SEM*sqrt(2))
pre=bm[bm.momento=='pre']; pos=bm[bm.momento=='pos']
rci_rows=[]
for s in SUBS:
    a=conf[s]['alpha']; sd=bm[s].std()
    sem=sd*np.sqrt(max(1-a,0)); mdc=1.96*np.sqrt(2)*sem
    # pares pré→pós por atleta-dia
    m=bm[bm.momento.isin(['pre','pos'])].pivot_table(index=['atleta','dia'],columns='momento',values=s,aggfunc='mean').dropna()
    delta=(m['pos']-m['pre']).values; rci=delta/(sem*np.sqrt(2)) if sem>0 else delta*0
    n=len(delta); up=int(np.sum(rci>1.96)); dn=int(np.sum(rci<-1.96))
    rci_rows.append({'sub':s,'alpha':round(a,3),'DP':round(sd,2),'SEM':round(sem,2),'MDC95':round(mdc,2),
        'n':n,'pct_aumento':round(100*up/n,1),'pct_queda':round(100*dn/n,1),'pct_mudanca':round(100*(up+dn)/n,1)})
OUT['rci']=rci_rows

fig,ax=plt.subplots(figsize=(7.4,4.6),dpi=150); order=sorted(rci_rows,key=lambda r:r['pct_mudanca'])
yl=[r['sub'] for r in order]; up=[r['pct_aumento'] for r in order]; dn=[r['pct_queda'] for r in order]
ax.barh(yl,up,color=CORAL,edgecolor='none',height=.66,label='mudança confiável ↑')
ax.barh(yl,[-x for x in dn],color=CYAN,edgecolor='none',height=.66,label='mudança confiável ↓')
ax.axvline(0,color=FAINT,lw=1)
for i,r in enumerate(order):
    if r['pct_aumento']>3: ax.text(r['pct_aumento']+1,i,f"{r['pct_aumento']:.0f}%",va='center',fontsize=9,color=INK)
    if r['pct_queda']>3: ax.text(-r['pct_queda']-1,i,f"{r['pct_queda']:.0f}%",va='center',ha='right',fontsize=9,color=INK)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_xlabel('% de pares pré→pós com mudança confiável (|RCI|>1,96)')
ax.set_title('Mudança confiável por atleta (RCI / MDC)',loc='left'); ax.legend(frameon=False,labelcolor=INK,fontsize=9,loc='lower right'); clean(ax)
save(fig,'17_rci.png')

# ============ (2) TOST equivalência ============
def tost_paired(dz,n,sesoi=0.5):
    se=1/np.sqrt(n); tl=(dz+sesoi)/se; tu=(dz-sesoi)/se
    pl=1-stats.t.cdf(tl,n-1); pu=stats.t.cdf(tu,n-1); p=max(pl,pu)
    return {'efeito_dz':round(dz,2),'n':n,'sesoi':sesoi,'p_TOST':round(float(p),3),'equivalente':bool(p<0.05)}
def tost_r(r,n,bound=0.3):
    z=np.arctanh(r); se=1/np.sqrt(n-3); zb=np.arctanh(bound)
    tl=(z+zb)/se; tu=(z-zb)/se; pl=1-stats.norm.cdf(tl); pu=stats.norm.cdf(tu); p=max(pl,pu)
    return {'r':round(r,2),'n':n,'bound':bound,'p_TOST':round(float(p),3),'equivalente':bool(p<0.05)}
tost=[]
# HIIT vs sem (dh.C) — equivalência em dz (SESOI 0.5)
for x in D['dh']['C']:
    t=tost_paired(x['dz'],D['dh']['n_C']); t.update({'teste':'HIIT vs sem · '+x['var'],'tipo':'dz'}); tost.append(t)
# desacoplamento carga↔humor (correlações; bound r=0.3)
tost.append({**tost_r(D['trimp']['TRIMP_x_humor']['r'],D['trimp']['TRIMP_x_humor']['n']),'teste':'TRIMP × ΔPTH (desacoplamento)','tipo':'r'})
ch=json.load(open(os.path.join(ROOT,'carga_humor','resultados_carga_humor.json')))
for p in ch['acoplamento']['tonico']['pares']:
    if p['carga']=='PSE' and p['humor'] in ('FadMen','Fadiga'):
        tost.append({**tost_r(p['r'],ch['acoplamento']['tonico']['n']),'teste':f"{p['carga']} × {p['humor']} (tônico)",'tipo':'r'})
OUT['tost']=tost

fig,ax=plt.subplots(figsize=(7.6,4.8),dpi=150)
rows=[t for t in tost if t['tipo']=='dz'][:5]+[t for t in tost if t['tipo']=='r']
labs=[t['teste'].replace(' · ',': ') for t in rows]; eff=[t.get('efeito_dz',t.get('r')) for t in rows]
bnd=[t['sesoi'] if t['tipo']=='dz' else t['bound'] for t in rows]; y=np.arange(len(rows))
ax.axvspan(-max(bnd),max(bnd),color=GREEN,alpha=.08)
for b in [-max(bnd),max(bnd)]: ax.axvline(b,color=GREEN,ls=':',lw=1)
ax.axvline(0,color=FAINT,lw=1)
cols=[GREEN if t['equivalente'] else GOLD for t in rows]
ax.scatter(eff,y,s=90,c=cols,edgecolor='white',linewidth=1.2,zorder=3)
for i,t in enumerate(rows): ax.text(eff[i],i+.28,('equiv.' if t['equivalente'] else 'inconcl.'),ha='center',fontsize=8,color=cols[i])
ax.set_yticks(y); ax.set_yticklabels(labs,fontsize=9.5,color=INK); ax.set_xlim(-.8,.8)
ax.grid(axis='x',**GRID); ax.set_axisbelow(True); ax.set_xlabel('efeito (dz ou r) · faixa verde = SESOI de equivalência')
ax.set_title('Testes de equivalência (TOST) dos achados nulos',loc='left'); clean(ax)
save(fig,'18_tost.png')

# ============ (3) Rede psicométrica (parciais) ============
X=bm[SUBS].dropna(); C=np.corrcoef(X.values.T); P=np.linalg.inv(C)
pc=np.zeros_like(P)
for i in range(len(SUBS)):
    for j in range(len(SUBS)): pc[i,j]=-P[i,j]/np.sqrt(P[i,i]*P[j,j])
strength={SUBS[i]:round(float(np.sum(np.abs(pc[i,:]))-1),2) for i in range(len(SUBS))}
edges=[]
for i in range(len(SUBS)):
    for j in range(i+1,len(SUBS)):
        if abs(pc[i,j])>=0.08: edges.append({'a':SUBS[i],'b':SUBS[j],'pcor':round(float(pc[i,j]),2)})
OUT['rede']={'strength':strength,'edges':sorted(edges,key=lambda e:-abs(e['pcor']))}

fig,ax=plt.subplots(figsize=(6.4,6.0),dpi=150); ax.set_aspect('equal'); ax.axis('off')
th=np.linspace(0,2*np.pi,len(SUBS),endpoint=False); pos={s:(np.cos(t),np.sin(t)) for s,t in zip(SUBS,th)}
mx=max(abs(e['pcor']) for e in edges) if edges else 1
for e in edges:
    x1,y1=pos[e['a']]; x2,y2=pos[e['b']]; c=CORAL if e['pcor']>0 else CYAN
    ax.plot([x1,x2],[y1,y2],color=c,lw=1+5*abs(e['pcor'])/mx,alpha=.5,zorder=1)
for s in SUBS:
    x,y=pos[s]; sz=380+900*strength[s]
    ax.scatter([x],[y],s=sz,c=VIOLET,edgecolor='white',linewidth=1.4,zorder=2,alpha=.9)
    ax.text(x*1.34,y*1.34,s,ha='center',va='center',fontsize=11,color=INK,fontweight='bold')
ax.set_xlim(-1.6,1.6); ax.set_ylim(-1.6,1.6)
ax.set_title('Rede psicométrica — correlações parciais',loc='left',color=INK,y=1.02)
ax.text(0,-1.55,'aresta coral = parcial +   ·   azul = parcial −   ·   tamanho do nó = força',ha='center',fontsize=8.5,color=MUT)
save(fig,'19_rede.png')

# ============ (4) Trajetória intradia pré → mid → pós ============
mom=['pre','mid','pos']; VARS=[('FadFis','Fadiga física',CORAL),('Fadiga','Fadiga',GOLD),('PTH','PTH (TMD)',VIOLET),('Vigor','Vigor',CYAN)]
intr={}; fig,ax=plt.subplots(figsize=(7.4,4.6),dpi=150)
for v,lb,c in VARS:
    ys=[bm[bm.momento==m][v].mean() for m in mom]; es=[bm[bm.momento==m][v].sem() for m in mom]
    intr[v]={'label':lb,'pre':round(ys[0],2),'mid':round(ys[1],2),'pos':round(ys[2],2)}
    ax.errorbar([0,1,2],ys,yerr=es,fmt='-o',color=c,lw=2.4,ms=7,capsize=3,label=lb)
ax.set_xticks([0,1,2]); ax.set_xticklabels(['pré','meio','pós']); ax.grid(axis='y',**GRID); ax.set_axisbelow(True)
ax.set_ylabel('escore (média ± EP)'); ax.set_title('Cinética intradia — pré → meio → pós',loc='left')
ax.legend(frameon=False,labelcolor=INK,fontsize=9,ncol=2); clean(ax)
save(fig,'20_intradia.png')
OUT['intradia']=intr

json.dump(OUT,open(os.path.join(HERE,'resultados_extras.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('RCI (% mudança confiável):',{r['sub']:r['pct_mudanca'] for r in rci_rows})
print('TOST equivalentes:',[t['teste'] for t in tost if t['equivalente']])
print('rede strength:',strength)
print('intradia FadFis:',intr['FadFis'])
print('OK — resultados_extras.json + 4 figuras em', FIGD)
