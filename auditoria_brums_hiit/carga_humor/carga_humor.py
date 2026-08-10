# -*- coding: utf-8 -*-
"""Carga interna (PSE, FC, TRIMP) × PERFIL DE HUMOR completo, e quais variáveis
são mais SENSÍVEIS e CONFIÁVEIS para predizer estado de fadiga (alta vs. baixa).

Consolida e estende o módulo de acoplamento, respondendo diretamente:
  (A) Como PSE, TRIMP e FC se relacionam com CADA escala do BRUMS e com os
      índices derivados (PTH/TMD, fadiga física, fadiga mental)? Leituras
      TÔNICA (médias do atleta nos dias de HIIT) e AGUDA (Δ pós−pré do atleta),
      no nível do atleta (unidade = atleta), com correção FDR (Benjamini–Hochberg).
  (B) Quais variáveis melhor predizem um ESTADO de fadiga ALTA vs. BAIXA?
      Alvo = tercil superior vs. inferior da subescala Fadiga (contraste limpo).
      Para cada preditor concorrente: AUC (IC95% por bootstrap agrupado por
      atleta), e no ponto de corte de Youden a SENSIBILIDADE e a ESPECIFICIDADE.
      CONFIABILIDADE de cada preditor: ICC(2,1) entre medidas repetidas
      (estabilidade) — o cruzamento sensibilidade × confiabilidade identifica
      os marcadores simultaneamente sensíveis E confiáveis.

Autocontido, anonimizado (A01–A27). Reproduzível:
    python carga_humor.py  →  resultados_carga_humor.json + carga_humor_fig.png
Dependências: numpy scipy pandas matplotlib statsmodels pingouin
"""
import os, json, warnings
import numpy as np, pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests
import pingouin as pg
warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from matplotlib.patches import Patch

HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.dirname(HERE)
TEAL='#0e9c90'; CORAL='#c0392b'; INK='#16273d'; MUT='#5b6b82'; LINE='#d6deea'; GOLD='#b0790f'; BLUE='#245c8b'; VIOLET='#7a4fb0'; GREEN='#2e7d5b'
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':INK,'axes.edgecolor':LINE,'axes.labelcolor':INK,
 'xtick.color':INK,'ytick.color':INK,'figure.facecolor':'white','axes.facecolor':'white'})
RNG=np.random.default_rng(20260802)

# ===================== dados =====================
fc=pd.read_csv(os.path.join(ROOT,'trimp','fc_fases.csv'))
bm=pd.read_csv(os.path.join(ROOT,'modelagem','base_modelagem.csv'))

# carga interna por atleta (TRIMP relativo por HRR + PSE-sessão + FC de pico)
fc=fc[fc['atleta'].str.startswith('A')].copy()
fc['valida']=fc['fc_pos'].notna()
rest=fc.groupby('atleta')['fc_pre'].min(); mx=fc.groupby('atleta')['fc_pos'].max()
fc['rest']=fc['atleta'].map(rest); fc['max']=fc['atleta'].map(mx)
fc['hrr']=np.where(fc['valida'],((fc['fc_pos']-fc['rest'])/(fc['max']-fc['rest'])).clip(0,1),np.nan)
fc['w']=fc['hrr']*0.64*np.exp(1.92*fc['hrr'])
sess=fc.groupby(['atleta','sessao']).agg(trimp=('w','sum'),pse=('pse','sum'),fc_pico=('fc_pos','max'),nval=('valida','sum')).reset_index()
sess=sess[sess['nval']>=3]
carga=sess.groupby('atleta').agg(PSE=('pse','mean'),FC=('fc_pico','mean'),TRIMP=('trimp','mean')).reset_index()

MOODS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','PTH','FadFis','FadMen']
LOADS=['PSE','FC','TRIMP']

# TÔNICO: média do atleta nos dias de HIIT
h=bm[bm.hiit==1]
ton=h.groupby('atleta')[MOODS].mean().reset_index()
# AGUDO: Δ pós−pré médio do atleta
hp=h[h.momento.isin(['pre','pos'])]
ag=[]
for a,g in hp.groupby('atleta'):
    dd={m:[] for m in MOODS}
    for d,gd in g.groupby('dia'):
        pre=gd[gd.momento=='pre']; pos=gd[gd.momento=='pos']
        if len(pre) and len(pos):
            for m in MOODS: dd[m].append(pos[m].mean()-pre[m].mean())
    if dd['Fadiga']: ag.append({'atleta':a,**{m:np.mean(dd[m]) for m in MOODS}})
ag=pd.DataFrame(ag)

tonD=carga.merge(ton,on='atleta').dropna()
agD=carga.merge(ag,on='atleta').dropna()

def coupling(df,tag):
    rows=[]
    for L in LOADS:
        for M in MOODS:
            r,p=stats.pearsonr(df[L],df[M])
            rows.append({'carga':L,'humor':M,'r':round(float(r),2),'p_bruto':float(p)})
    ps=[x['p_bruto'] for x in rows]
    rej,q,_,_=multipletests(ps,method='fdr_bh')
    for i,x in enumerate(rows):
        x['q_fdr']=round(float(q[i]),3); x['sig_fdr']=bool(rej[i]); x['p_bruto']=round(x['p_bruto'],3)
    return {'n':int(len(df)),'pares':rows}

cpl={'tonico':coupling(tonD,'ton'),'agudo':coupling(agD,'ag')}

# ===================== (B) preditores de estado de fadiga =====================
# alvo = tercil superior (fadiga ALTA) vs inferior (fadiga BAIXA) da subescala Fadiga
obs=bm[bm.momento.isin(['pre','mid','pos','uni'])].copy()
q1,q2=obs['Fadiga'].quantile([1/3,2/3])
obs['alvo']=np.where(obs['Fadiga']>=q2,1,np.where(obs['Fadiga']<=q1,0,np.nan))
lab=obs.dropna(subset=['alvo']).copy(); lab['alvo']=lab['alvo'].astype(int)
# preditores concorrentes (exclui a própria Fadiga p/ evitar circularidade)
# PTH/TMD excluído dos preditores: contém aritmeticamente a subescala Fadiga (circular).
PREDS=[('FadFis','Fadiga física'),('FadMen','Fadiga mental'),('Vigor','Vigor'),
       ('Confusão','Confusão'),('Depressão','Depressão'),
       ('Tensão','Tensão'),('Raiva','Raiva')]

def auc_of(y,x):
    # AUC de Mann–Whitney (concordância); orienta p/ ≥0,5
    x=np.asarray(x,float); y=np.asarray(y,int)
    pos=x[y==1]; neg=x[y==0]
    if len(pos)==0 or len(neg)==0: return 0.5
    U=stats.mannwhitneyu(pos,neg,alternative='two-sided').statistic
    a=U/(len(pos)*len(neg)); return max(a,1-a)

def youden(y,x):
    x=np.asarray(x,float); y=np.asarray(y,int)
    # direção: se AUC bruta<0.5, inverte o sinal
    U=stats.mannwhitneyu(x[y==1],x[y==0],alternative='two-sided').statistic
    sgn=1 if U/(len(x[y==1])*len(x[y==0]))>=0.5 else -1
    xs=sgn*x
    thr=np.unique(xs); best=(-1,None,None,None)
    for t in thr:
        pred=(xs>=t).astype(int)
        tp=np.sum((pred==1)&(y==1)); fn=np.sum((pred==0)&(y==1))
        tn=np.sum((pred==0)&(y==0)); fp=np.sum((pred==1)&(y==0))
        sens=tp/(tp+fn) if tp+fn else 0; spec=tn/(tn+fp) if tn+fp else 0
        if sens+spec-1>best[0]: best=(sens+spec-1,sens,spec,t)
    return best[1],best[2]

def boot_auc_ci(df,var,B=2000):
    # pré-agrupa por atleta em arrays numpy (cluster bootstrap rápido)
    groups=[(g['alvo'].to_numpy(),g[var].to_numpy(float)) for _,g in df.groupby('atleta')]
    idx=np.arange(len(groups)); vals=[]
    for _ in range(B):
        pick=RNG.choice(idx,len(idx),replace=True)
        y=np.concatenate([groups[i][0] for i in pick]); x=np.concatenate([groups[i][1] for i in pick])
        if len(np.unique(y))<2: continue
        vals.append(auc_of(y,x))
    return (float(np.percentile(vals,2.5)),float(np.percentile(vals,97.5))) if vals else (np.nan,np.nan)

def icc21(var):
    # estabilidade entre medidas repetidas: alvos=atleta, avaliadores=índice de repetição
    d=bm[['atleta','dia','momento',var]].dropna().copy()
    d['rep']=d['dia'].astype(str)+d['momento'].astype(str)
    piv=d.pivot_table(index='atleta',columns='rep',values=var,aggfunc='mean')
    piv=piv.dropna(axis=1,thresh=int(0.6*len(piv)))  # colunas com ≥60% dos atletas
    long=piv.reset_index().melt(id_vars='atleta',var_name='rep',value_name='v')
    try:
        res=pg.intraclass_corr(data=long,targets='atleta',raters='rep',ratings='v',nan_policy='omit')
        # ICC(2,1): duas vias, aleatório, medida única, concordância absoluta
        sel=res[res['Type'].isin(['ICC2','ICC(A,1)'])]
        return float(sel['ICC'].values[0])
    except Exception:
        return np.nan

# alpha de Cronbach por subescala (confiabilidade interna) — mapeia p/ os preditores
ALPHA={'FadFis':None,'FadMen':None,'PTH':None,
       'Vigor':0.80,'Confusão':0.60,'Depressão':0.83,'Tensão':0.55,'Raiva':0.85,'Fadiga':0.85}

preditores=[]
for var,lb in PREDS:
    a=auc_of(lab['alvo'],lab[var]); ci=boot_auc_ci(lab,var)
    sens,spec=youden(lab['alvo'],lab[var]); icc=icc21(var)
    preditores.append({'var':var,'label':lb,'AUC':round(a,3),'IC95':[round(ci[0],3),round(ci[1],3)],
        'sensibilidade':round(sens,3),'especificidade':round(spec,3),
        'ICC21':round(icc,3) if icc==icc else None,'alpha':ALPHA.get(var)})
preditores=sorted(preditores,key=lambda z:-z['AUC'])

partB={'alvo':'Fadiga ALTA (tercil superior) vs BAIXA (tercil inferior) da subescala Fadiga',
       'n_alta':int((lab['alvo']==1).sum()),'n_baixa':int((lab['alvo']==0).sum()),
       'corte_tercis':[round(float(q1),2),round(float(q2),2)],
       'validacao_AUC':'IC95% por bootstrap agrupado por atleta (2000)','preditores':preditores}

OUT={'acoplamento':cpl,'preditores_fadiga':partB}
json.dump(OUT,open(os.path.join(HERE,'resultados_carga_humor.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=1)

# ===================== FIGURA =====================
fig=plt.figure(figsize=(13.6,6.0),dpi=150)
gs=fig.add_gridspec(1,3,width_ratios=[1.1,1.1,1.35],wspace=0.55)
fig.suptitle('Carga interna × perfil de humor e preditores de estado de fadiga',x=0.055,ha='left',fontsize=15,fontweight='bold',y=0.98)

# painéis A/B: heatmaps de acoplamento (tônico e agudo) carga×humor
def heat(ax,rec,titulo):
    R=np.array([[next(p['r'] for p in rec['pares'] if p['carga']==L and p['humor']==M) for M in MOODS] for L in LOADS])
    S=[[next((p['sig_fdr'],p['p_bruto']<0.05) for p in rec['pares'] if p['carga']==L and p['humor']==M) for M in MOODS] for L in LOADS]
    im=ax.imshow(R,cmap='RdBu_r',vmin=-1,vmax=1,aspect='auto')
    ax.set_xticks(range(len(MOODS))); ax.set_xticklabels(MOODS,rotation=55,ha='right',fontsize=7.5)
    ax.set_yticks(range(len(LOADS))); ax.set_yticklabels(LOADS,fontsize=9)
    for i in range(len(LOADS)):
        for j in range(len(MOODS)):
            fdr,raw=S[i][j]; mk='†' if fdr else ('*' if raw else '')
            ax.text(j,i,f'{R[i,j]:+.2f}{mk}',ha='center',va='center',fontsize=6.8,
                    color='white' if abs(R[i,j])>0.5 else '#222')
    ax.set_title(titulo,fontsize=10.5,loc='left'); return im
axA=fig.add_subplot(gs[0,0]); heat(axA,cpl['tonico'],f"A · Tônico (nível do atleta, n={cpl['tonico']['n']})")
axB=fig.add_subplot(gs[0,1]); im=heat(axB,cpl['agudo'],f"B · Agudo (Δ pós−pré, n={cpl['agudo']['n']})")
cax=fig.add_axes([0.605,0.16,0.009,0.62]); cb=fig.colorbar(im,cax=cax); cb.set_label('r de Pearson',fontsize=8,labelpad=2); cb.ax.tick_params(labelsize=7); cax.yaxis.set_label_position('left')

# painel C: sensibilidade (AUC) × confiabilidade (ICC), preditores de fadiga
axC=fig.add_subplot(gs[0,2])
xs=[p['ICC21'] or 0 for p in preditores]; ys=[p['AUC'] for p in preditores]
sz=[220 for _ in preditores]
axC.axhspan(0.7,1.0,color=GREEN,alpha=0.06); axC.axvspan(0.7,1.0,color=GREEN,alpha=0.06)
axC.axhline(0.7,color=MUT,ls=':',lw=1); axC.axvline(0.7,color=MUT,ls=':',lw=1)
axC.axhline(0.5,color=LINE,lw=1)
sc=axC.scatter(xs,ys,s=sz,c=[BLUE if (p['AUC']>=0.6 and (p['ICC21'] or 0)>=0.5) else MUT for p in preditores],
               edgecolor='white',linewidth=1.4,zorder=3)
for p,x,y in zip(preditores,xs,ys):
    axC.annotate(p['label'].split(' (')[0],(x,y),textcoords='offset points',xytext=(7,4),fontsize=7,color=INK)
axC.set_xlim(0,1); axC.set_ylim(0.45,0.96); axC.set_xlabel('confiabilidade — ICC(2,1) entre medidas')
axC.set_ylabel('sensibilidade — AUC (fadiga alta vs. baixa)')
axC.set_title('C · Sensível E confiável (quadrante ↗)',fontsize=10.5,loc='left')
for s in ['top','right']: axC.spines[s].set_visible(False)

fig.text(0.055,0.02,'† significativo após FDR (Benjamini–Hochberg); * p<0,05 bruto. Unidade = atleta; correlações no nível do atleta. '
         'AUC por Mann–Whitney com IC95% por bootstrap agrupado por atleta; sensibilidade/especificidade no ponto de Youden.',
         fontsize=7.5,color=MUT)
fig.subplots_adjust(left=0.055,right=0.985,top=0.87,bottom=0.14)
fig.savefig(os.path.join(HERE,'carga_humor_fig.png'),dpi=150,facecolor='white',bbox_inches='tight'); plt.close(fig)

# ===================== console =====================
print('=== ACOPLAMENTO TÔNICO (n=%d) — |r| ordenado, carga×humor ==='%cpl['tonico']['n'])
for p in sorted(cpl['tonico']['pares'],key=lambda z:-abs(z['r']))[:6]:
    print(f"   {p['carga']:5s}×{p['humor']:9s} r={p['r']:+.2f} p={p['p_bruto']:.3f} q={p['q_fdr']:.3f} {'†' if p['sig_fdr'] else ''}")
print('=== PREDITORES DE FADIGA ALTA vs BAIXA (n alta=%d / baixa=%d) ==='%(partB['n_alta'],partB['n_baixa']))
for p in preditores:
    print(f"   {p['label']:24s} AUC={p['AUC']:.2f} [{p['IC95'][0]:.2f};{p['IC95'][1]:.2f}]  sens={p['sensibilidade']:.2f} spec={p['especificidade']:.2f}  ICC={p['ICC21']}")
print('\nSalvo resultados_carga_humor.json + carga_humor_fig.png')
