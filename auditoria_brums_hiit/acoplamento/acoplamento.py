# -*- coding: utf-8 -*-
"""Acoplamento carga interna × humor — PSE, FC, TRIMP, Fadiga mental, TMD (PTH).

Relaciona os cinco marcadores no nível do atleta (dias de HIIT), respondendo:
a carga interna (PSE, FC de pico, TRIMP) se acopla ao humor (fadiga mental, TMD)?

Duas leituras:
  • TÔNICO  — médias do atleta nos dias de HIIT (nível do dia)
  • AGUDO   — Δ pós−pré médio do atleta (resposta da sessão)

Matriz de correlações (Pearson) + p, com destaque para as células carga × humor.
Autocontido: lê ../trimp/fc_fases.csv e ../modelagem/base_modelagem.csv (anonimizadas).
Uso: python acoplamento.py → resultados_acoplamento.json + heatmap_acoplamento.png
Dependências: numpy scipy pandas matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(RED='#C0392B',TEAL='#0E8C86',NAVY='#122438',MUT='#5B6B82')

fc=pd.read_csv(os.path.join(HERE,'..','trimp','fc_fases.csv'))
bm=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))

# --- carga interna por atleta (só atletas com código A, casados ao BRUMS) ---
fc=fc[fc['atleta'].str.startswith('A')].copy()
fc['valida']=fc['fc_pos'].notna()
rest=fc.groupby('atleta')['fc_pre'].min(); mx=fc.groupby('atleta')['fc_pos'].max()
fc['rest']=fc['atleta'].map(rest); fc['max']=fc['atleta'].map(mx)
fc['hrr']=np.where(fc['valida'],((fc['fc_pos']-fc['rest'])/(fc['max']-fc['rest'])).clip(0,1),np.nan)
fc['w']=fc['hrr']*0.64*np.exp(1.92*fc['hrr'])
sess=fc.groupby(['atleta','sessao']).agg(trimp=('w','sum'),pse=('pse','sum'),fc_pico=('fc_pos','max'),nval=('valida','sum')).reset_index()
sess=sess[sess['nval']>=3]
carga=sess.groupby('atleta').agg(PSE=('pse','mean'),FC=('fc_pico','mean'),TRIMP=('trimp','mean')).reset_index()

# --- humor por atleta nos dias de HIIT: tônico (média) e agudo (Δ pós−pré) ---
h=bm[bm.hiit==1]
ton=h.groupby('atleta').agg(FadMen=('FadMen','mean'),TMD=('PTH','mean')).reset_index()
hp=h[h.momento.isin(['pre','pos'])]
ag=[]
for a,g in hp.groupby('atleta'):
    dm=[]; dt=[]
    for d,gd in g.groupby('dia'):
        pre=gd[gd.momento=='pre']; pos=gd[gd.momento=='pos']
        if len(pre) and len(pos):
            dm.append(pos['FadMen'].mean()-pre['FadMen'].mean()); dt.append(pos['PTH'].mean()-pre['PTH'].mean())
    if dm: ag.append({'atleta':a,'dFadMen':np.mean(dm),'dTMD':np.mean(dt)})
ag=pd.DataFrame(ag)

ton_df=carga.merge(ton,on='atleta').dropna()
ag_df=carga.merge(ag,on='atleta').dropna()

def cormat(df,cols):
    M=np.zeros((len(cols),len(cols))); Pv=np.ones((len(cols),len(cols)))
    for i,a in enumerate(cols):
        for j,b in enumerate(cols):
            r,p=stats.pearsonr(df[a],df[b]); M[i,j]=r; Pv[i,j]=p
    return M,Pv

def do(df,cols,titulo,fname,key):
    M,Pv=cormat(df,cols); n=len(df)
    rec={'n':int(n),'variaveis':cols,'r':np.round(M,2).tolist(),
         'pares_carga_humor':[]}
    load=['PSE','FC','TRIMP']; mood=[c for c in cols if c not in load]
    for a in load:
        for b in mood:
            i,j=cols.index(a),cols.index(b)
            rec['pares_carga_humor'].append({'x':a,'y':b,'r':round(float(M[i,j]),2),'p':round(float(Pv[i,j]),3),'sig':bool(Pv[i,j]<0.05)})
    out[key]=rec
    fig,ax=plt.subplots(figsize=(5.6,4.8),dpi=170)
    im=ax.imshow(M,cmap='RdBu_r',vmin=-1,vmax=1)
    ax.set_xticks(range(len(cols))); ax.set_yticks(range(len(cols)))
    ax.set_xticklabels(cols,rotation=40,ha='right',fontsize=9); ax.set_yticklabels(cols,fontsize=9)
    for i in range(len(cols)):
        for j in range(len(cols)):
            star='*' if Pv[i,j]<0.05 and i!=j else ''
            ax.text(j,i,f'{M[i,j]:.2f}{star}',ha='center',va='center',fontsize=8,
                    color='white' if abs(M[i,j])>0.55 else '#222')
    cb=fig.colorbar(im,fraction=0.046,pad=0.04); cb.set_label('r de Pearson')
    ax.set_title(titulo,fontsize=10.5,loc='left',color=P['NAVY'])
    fig.tight_layout(); fig.savefig(os.path.join(HERE,fname),facecolor='white'); plt.close()
    return rec

out={}
recT=do(ton_df,['PSE','FC','TRIMP','FadMen','TMD'],'Acoplamento tônico (médias do atleta nos dias de HIIT)','heatmap_tonico.png','tonico')
recA=do(ag_df,['PSE','FC','TRIMP','dFadMen','dTMD'],'Acoplamento agudo (Δ pós−pré médio do atleta)','heatmap_agudo.png','agudo')
# painel combinado
import matplotlib.image as mpimg
fig,axs=plt.subplots(1,2,figsize=(11.5,4.9),dpi=160)
for ax,f in zip(axs,['heatmap_tonico.png','heatmap_agudo.png']):
    ax.imshow(mpimg.imread(os.path.join(HERE,f))); ax.axis('off')
fig.tight_layout(); fig.savefig(os.path.join(HERE,'heatmap_acoplamento.png'),facecolor='white'); plt.close()

json.dump(out,open(os.path.join(HERE,'resultados_acoplamento.json'),'w'),ensure_ascii=False,indent=1,default=str)
print("=== TÔNICO (n=%d) — carga × humor ==="%recT['n'])
for p in recT['pares_carga_humor']: print(f"   {p['x']:5s}×{p['y']:7s} r={p['r']:+.2f} p={p['p']:.3f} {'*' if p['sig'] else ''}")
print("=== AGUDO (n=%d) — carga × Δhumor ==="%recA['n'])
for p in recA['pares_carga_humor']: print(f"   {p['x']:5s}×{p['y']:8s} r={p['r']:+.2f} p={p['p']:.3f} {'*' if p['sig'] else ''}")
print("\nSalvo resultados_acoplamento.json + heatmap_acoplamento.png")
