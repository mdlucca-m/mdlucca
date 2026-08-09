# -*- coding: utf-8 -*-
"""Perfil de humor, distribuições, variabilidade e robustez (BRUMS × HIIT).

Camada descritiva/exploratória + verificações de robustez:
  · PERFIL de humor (iceberg) pré vs pós e qui-quadrado do perfil × momento
  · DISTRIBUIÇÕES: box plot, histograma, dispersão
  · VARIABILIDADE intra vs entre indivíduos (componentes de variância) e
    entre GRUPOS (segmentação por agrupamento; separação por η²)
  · SEGMENTAÇÃO: k-means (k=3) sobre o perfil-z médio por atleta
  · Robustez: teste de PERMUTAÇÃO (sign-flip pareado), análise de
    sensibilidade à transformação LOGARÍTMICA e à exclusão do outlier

Autocontido: lê ../modelagem/base_modelagem.csv (anonimizado A01–A27).
Uso: python perfil_variabilidade.py → resultados + duas figuras.
Dependências: numpy pandas scipy scikit-learn matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore'); RS=np.random.RandomState(7)
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GREEN='#2E8B57',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
SUBS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
NEG=['Tensão','Depressão','Raiva','Fadiga','Confusão']
out={}

# ---------- pares por atleta (média pré / média pós) ----------
def agg(m): return df[df.momento==m].groupby('atleta')[SUBS+['PTH','FadFis']].mean()
PRE=agg('pre'); POS=agg('pos'); ath=PRE.index.intersection(POS.index)
PRE=PRE.loc[ath]; POS=POS.loc[ath]; nA=len(ath)

# ========== 1. PERFIL (iceberg) + QUI-QUADRADO ==========
prof={'pre':{s:round(float(df[df.momento=='pre'][s].mean()),2) for s in SUBS},
      'pos':{s:round(float(df[df.momento=='pos'][s].mean()),2) for s in SUBS}}
# indicador iceberg por observação: vigor acima da média das negativas
d2=df[df.momento.isin(['pre','pos'])].copy()
d2['iceberg']=(d2['Vigor']>d2[NEG].mean(axis=1)).astype(int)
ct=pd.crosstab(d2['momento'],d2['iceberg'])  # linhas pré/pós, colunas 0/1
chi2,pchi,dof,exp=stats.chi2_contingency(ct)
nn=ct.values.sum(); cramV=float(np.sqrt(chi2/(nn*(min(ct.shape)-1))))
out['perfil']=dict(medias=prof,
  iceberg_prev={'pre':round(float(d2[d2.momento=='pre']['iceberg'].mean()),3),
                'pos':round(float(d2[d2.momento=='pos']['iceberg'].mean()),3)},
  quiquadrado=dict(chi2=round(float(chi2),3),df=int(dof),p=round(float(pchi),4),
                   cramer_V=round(cramV,3),tabela=ct.to_dict()))
print(f"1. Iceberg pré={out['perfil']['iceberg_prev']['pre']} pós={out['perfil']['iceberg_prev']['pos']} · χ²({dof})={chi2:.2f} p={pchi:.4f} V={cramV:.2f}")

# ========== 2. VARIABILIDADE intra vs entre ==========
varc=[]
for s in SUBS+['PTH','FadFis']:
    g=df.groupby('atleta')[s]
    entre=float(g.mean().var(ddof=1))                 # variância das médias dos atletas
    intra=float(g.var(ddof=1).mean())                 # média das variâncias intra-atleta
    tot=entre+intra
    varc.append(dict(var=s, entre=round(entre,2), intra=round(intra,2),
                     pct_entre=round(100*entre/tot,1) if tot>0 else None,
                     CV_intra=round(100*np.sqrt(intra)/abs(df[s].mean()),1) if df[s].mean()!=0 else None))
out['variabilidade']=varc
print("2. Variância % entre-atletas:",{v['var']:v['pct_entre'] for v in varc})

# ========== 3. SEGMENTAÇÃO (k-means k=3 no perfil-z médio) ==========
M=df.groupby('atleta')[SUBS].mean(); Z=(M-M.mean())/M.std()
km=KMeans(n_clusters=3,n_init=25,random_state=7).fit(Z.values)
lab=km.labels_
# ordena grupos por "perturbação" (soma das negativas - vigor no centroide)
score=[(Z.values[lab==k].mean(0)[[0,1,2,4,5]].sum()-Z.values[lab==k].mean(0)[3]) for k in range(3)]
order=np.argsort(score); remap={old:new for new,old in enumerate(order)}
lab2=np.array([remap[l] for l in lab]); names=['Resiliente','Perturbado','Extremo']
seg={'grupos':[]}
for k in range(3):
    idx=np.where(lab2==k)[0]
    seg['grupos'].append(dict(grupo=names[k], n=int(len(idx)),
        atletas=list(M.index[idx]),
        centroide={s:round(float(Z.values[lab2==k].mean(0)[i]),2) for i,s in enumerate(SUBS)}))
# η² separação entre grupos (no PTH médio por atleta)
pth_m=df.groupby('atleta')['PTH'].mean().loc[M.index].values
gm=pth_m.mean(); ssb=sum((pth_m[lab2==k].mean()-gm)**2*np.sum(lab2==k) for k in range(3))
sst=((pth_m-gm)**2).sum(); seg['eta2_PTH_entre_grupos']=round(float(ssb/sst),3)
out['segmentacao']=seg
print("3. Segmentação:",[(g['grupo'],g['n']) for g in seg['grupos']],"· η²(PTH)=",seg['eta2_PTH_entre_grupos'])

# ========== 4. PERMUTAÇÃO (sign-flip pareado) + parametrico ==========
def perm_paired(dif,nperm=20000):
    obs=dif.mean(); signs=RS.choice([-1,1],size=(nperm,len(dif)))
    null=(signs*dif).mean(1); p=(np.sum(np.abs(null)>=abs(obs))+1)/(nperm+1)
    return float(obs),float(p),null
TESTV={'FadFis':'Fadiga física','PTH':'PTH (TMD)','Vigor':'Vigor','Fadiga':'Fadiga',
       'Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Confusão':'Confusão'}
perm=[]; null_fadfis=None
for v,lab_ in TESTV.items():
    dif=(POS[v]-PRE[v]).values
    obs,pp,null=perm_paired(dif); t,pt=stats.ttest_rel(POS[v],PRE[v])
    if v=='FadFis': null_fadfis=(null,obs)
    perm.append(dict(var=lab_,delta=round(obs,3),p_perm=round(pp,4),p_t=round(float(pt),4),
                     concordam=bool((pp<0.05)==(pt<0.05))))
out['permutacao']=perm
print("4. Permutação vs t (concordância):",all(r['concordam'] for r in perm))

# ========== 5. SENSIBILIDADE: log-transform + exclusão do outlier ==========
sens={'log':[], 'sem_outlier':[]}
# 5a log: desloca p/ positivo e aplica log
for v in ['FadFis','PTH','Fadiga','Vigor']:
    sh=1-min(df[v].min(),0)  # deslocamento
    lp=np.log(PRE[v].values+sh); lo=np.log(POS[v].values+sh)
    t0,p0=stats.ttest_rel(POS[v],PRE[v]); t1,p1=stats.ttest_rel(lo,lp)
    sens['log'].append(dict(var=TESTV[v],p_raw=round(float(p0),4),p_log=round(float(p1),4),
                            decisao_mantem=bool((p0<0.05)==(p1<0.05))))
# 5b outlier: remove o atleta do grupo Extremo
ext=[g['atletas'] for g in seg['grupos'] if g['grupo']=='Extremo'][0]
keep=[a for a in ath if a not in ext]
for v in ['FadFis','PTH','Fadiga','Vigor']:
    dz_all=(POS[v]-PRE[v]).mean()/(POS[v]-PRE[v]).std(ddof=1)
    dif2=(POS.loc[keep,v]-PRE.loc[keep,v]); dz_k=dif2.mean()/dif2.std(ddof=1)
    t0,p0=stats.ttest_rel(POS[v],PRE[v]); t1,p1=stats.ttest_rel(POS.loc[keep,v],PRE.loc[keep,v])
    sens['sem_outlier'].append(dict(var=TESTV[v],dz_com=round(float(dz_all),2),dz_sem=round(float(dz_k),2),
                                    p_com=round(float(p0),4),p_sem=round(float(p1),4),
                                    decisao_mantem=bool((p0<0.05)==(p1<0.05))))
sens['outlier_excluido']=ext
out['sensibilidade']=sens
print(f"5. Sensibilidade log: {'robusto' if all(r['decisao_mantem'] for r in sens['log']) else 'atenção'} · sem outlier {ext}: {'robusto' if all(r['decisao_mantem'] for r in sens['sem_outlier']) else 'atenção'}")

json.dump(out,open(os.path.join(HERE,'resultados_perfil_variabilidade.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= FIGURA 1: perfil + distribuições =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.5),dpi=150)
# A perfil iceberg
ax=axs[0,0]; xs=np.arange(len(SUBS))
ax.plot(xs,[prof['pre'][s] for s in SUBS],'-o',color=P['BLUE'],lw=2,label='Pré',ms=6)
ax.plot(xs,[prof['pos'][s] for s in SUBS],'-o',color=P['RED'],lw=2,label='Pós',ms=6)
ax.axvspan(2.5,3.5,color=P['TEAL'],alpha=.08)
ax.set_xticks(xs); ax.set_xticklabels(SUBS,rotation=18,fontsize=8.5); ax.set_ylabel('escore médio (0–16)')
ax.legend(frameon=False,fontsize=9); ax.set_title('A · Perfil de humor (iceberg) pré vs pós',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
ax.annotate('vigor',(3,prof['pre']['Vigor']),fontsize=8,color=P['TEAL'],ha='center',va='bottom')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B boxplots pré vs pós por subescala
ax=axs[0,1]
data=[]; poss=[]; cols=[]
for i,s in enumerate(SUBS):
    data.append(df[df.momento=='pre'][s].dropna()); poss.append(i*2.4); cols.append(P['BLUE'])
    data.append(df[df.momento=='pos'][s].dropna()); poss.append(i*2.4+0.9); cols.append(P['RED'])
bp=ax.boxplot(data,positions=poss,widths=0.8,patch_artist=True,showfliers=False)
for b,c in zip(bp['boxes'],cols): b.set(facecolor=c,alpha=.55,edgecolor=c)
for med in bp['medians']: med.set(color=P['NAVY'],lw=1.3)
ax.set_xticks([i*2.4+0.45 for i in range(len(SUBS))]); ax.set_xticklabels(SUBS,rotation=18,fontsize=8.5)
ax.set_ylabel('escore'); ax.set_title('B · Box plot por subescala (azul=pré, vermelho=pós)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C histograma PTH raw vs log
ax=axs[1,0]
ax.hist(df['PTH'].dropna(),bins=20,color=P['BLUE'],alpha=.7,edgecolor='white')
ax.set_xlabel('PTH (TMD)'); ax.set_ylabel('frequência')
ax.set_title('C · Histograma do PTH (assimetria +1,48)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
axins=ax.inset_axes([0.55,0.5,0.42,0.45])
sh=1-min(df['PTH'].min(),0); axins.hist(np.log(df['PTH'].dropna()+sh),bins=18,color=P['GREEN'],alpha=.8,edgecolor='white')
axins.set_title('log(PTH+%d)'%sh,fontsize=7.5,color=P['MUT']); axins.tick_params(labelsize=6)
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D dispersão vigor×fadiga por grupo
ax=axs[1,1]; gc=[P['TEAL'],P['GOLD'],P['RED']]
Mm=df.groupby('atleta')[SUBS].mean()
for k in range(3):
    idx=np.where(lab2==k)[0]
    ax.scatter(Mm['Vigor'].values[idx],Mm['Fadiga'].values[idx],s=60,color=gc[k],alpha=.8,edgecolor='white',lw=.7,label=f'{names[k]} (n={len(idx)})')
ax.set_xlabel('Vigor (média do atleta)'); ax.set_ylabel('Fadiga (média do atleta)')
ax.legend(frameon=False,fontsize=8); ax.set_title('D · Dispersão vigor×fadiga por grupo',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'perfil_fig.png'),facecolor='white'); plt.close()

# ================= FIGURA 2: variabilidade + segmentação + permutação =================
fig,axs=plt.subplots(2,2,figsize=(13,9.5),dpi=150)
# A componentes de variância (% entre vs intra)
ax=axs[0,0]; vv=[v for v in varc]; ys=np.arange(len(vv))
pe=[v['pct_entre'] for v in vv]; pi=[100-v['pct_entre'] for v in vv]
ax.barh(ys,pe,color=P['VIO'],label='entre atletas'); ax.barh(ys,pi,left=pe,color=P['GRID'],label='intra atleta')
ax.set_yticks(ys); ax.set_yticklabels([v['var'] for v in vv],fontsize=8.5); ax.set_xlabel('% da variância total')
ax.axvline(50,ls='--',color=P['MUT'],lw=1); ax.legend(frameon=False,fontsize=8,loc='lower right')
ax.set_title('A · Variabilidade: entre atletas vs intra atleta',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B caterpillar PTH: média ± SD intra por atleta (ordenado)
ax=axs[0,1]
g=df.groupby('atleta')['PTH']; mm=g.mean(); sd=g.std(ddof=1).fillna(0); o=mm.sort_values().index
yy=np.arange(len(o))
ax.errorbar(mm.loc[o].values,yy,xerr=sd.loc[o].values,fmt='o',color=P['BLUE'],ecolor=P['GRID'],ms=4,elinewidth=2,capsize=0)
ax.axvline(mm.mean(),ls='--',color=P['RED'],lw=1.2,label='média geral')
ax.set_yticks([]); ax.set_xlabel('PTH — média do atleta ± DP intra'); ax.set_ylabel('27 atletas (ordenados)')
ax.legend(frameon=False,fontsize=8); ax.set_title('B · Variabilidade individual do PTH\n(dispersão dos pontos=entre; barras=intra)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C perfis de grupo (z por subescala)
ax=axs[1,0]; xs=np.arange(len(SUBS)); gc=[P['TEAL'],P['GOLD'],P['RED']]
for k in range(3):
    c=[out['segmentacao']['grupos'][k]['centroide'][s] for s in SUBS]
    ax.plot(xs,c,'-o',color=gc[k],lw=2,ms=5,label=f"{names[k]} (n={out['segmentacao']['grupos'][k]['n']})")
ax.axhline(0,color=P['MUT'],lw=.8); ax.set_xticks(xs); ax.set_xticklabels(SUBS,rotation=18,fontsize=8.5)
ax.set_ylabel('perfil-z (média do grupo)'); ax.legend(frameon=False,fontsize=8)
ax.set_title(f'C · Segmentação — perfis de grupo (η² PTH={seg["eta2_PTH_entre_grupos"]})',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D distribuição nula de permutação (FadFis)
ax=axs[1,1]; null,obs=null_fadfis
ax.hist(null,bins=45,color=P['GRID'],edgecolor='white')
ax.axvline(obs,color=P['RED'],lw=2,label=f'observado Δ={obs:.2f}')
ax.axvline(-obs,color=P['RED'],lw=1,ls=':')
pperm=[r['p_perm'] for r in perm if r['var']=='Fadiga física'][0]
ax.set_xlabel('Δ pré→pós sob H₀ (sign-flip)'); ax.set_ylabel('frequência')
ax.legend(frameon=False,fontsize=8); ax.set_title(f'D · Teste de permutação — fadiga física (p={pperm})',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'variabilidade_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_perfil_variabilidade.json + perfil_fig.png + variabilidade_fig.png")
