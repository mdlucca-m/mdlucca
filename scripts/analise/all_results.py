import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy.stats import spearmanr, friedmanchisquare, wilcoxon, kruskal
h=pd.read_csv('hum_prof.csv')
phys=pd.read_csv('phys.csv')[['ID','pos']]
auth=pd.read_csv('auth_full.csv')[['ID','PV']] if True else None
h=h.merge(phys,on='ID',how='left')
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Tensao','Tensão'),('Depressao','Depressão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','PTH'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental')]
KEYS=[k for k,_ in DIMS]
def desc(s): s=pd.to_numeric(s,errors='coerce').dropna(); return dict(n=int(s.size),m=float(s.mean()),sd=float(s.std(ddof=1)),med=float(s.median()),mn=float(s.min()),mx=float(s.max()),cv=float(100*s.std(ddof=1)/s.mean()) if s.mean()!=0 else None)
R={}

# 1) DESCRITIVA da semana (todas as variáveis)
R['desc_semana']={k:desc(h[k]) for k in KEYS}

# 2) POR DIA (média por dimensão por dia)
byday={}
for k in KEYS:
    byday[k]={int(d):float(h[h.dia==d][k].dropna().mean()) for d in range(1,8)}
R['por_dia']=byday

# 3) ENTRE DIAS: Friedman + W de Kendall; D1 vs D7 (dz, p)
friq={}; d1d7={}
for k in KEYS:
    piv=h.dropna(subset=['dia']).groupby(['ID','dia'])[k].mean().unstack('dia')
    piv=piv.dropna()
    if piv.shape[1]==7 and len(piv)>3:
        st,p=friedmanchisquare(*[piv[c].values for c in piv.columns])
        n,kk=piv.shape; W=st/(n*(kk-1))
        friq[k]={'chi':float(st),'p':float(p),'W':float(W),'n':int(n)}
    # D1 vs D7 por atleta
    a=h[h.dia==1].groupby('ID')[k].mean(); b=h[h.dia==7].groupby('ID')[k].mean()
    j=a.index.intersection(b.index); aa=a.loc[j].values; bb=b.loc[j].values; diff=bb-aa
    dz=float(np.mean(diff)/np.std(diff,ddof=1)) if np.std(diff)>0 else 0.0
    try: p=float(wilcoxon(aa,bb).pvalue)
    except Exception: p=1.0
    d1d7[k]={'d1':float(np.mean(aa)),'d7':float(np.mean(bb)),'delta':float(np.mean(diff)),'dz':dz,'p':p,'n':int(len(j)),'sig':bool(p<0.05)}
R['friedman']=friq; R['d1d7']=d1d7

# 4) PRÉ vs PÓS (todas)
prepos={}
for k in KEYS:
    pre=h[h.momento=='pre'].groupby('ID')[k].mean(); pos=h[h.momento=='pos'].groupby('ID')[k].mean()
    j=pre.index.intersection(pos.index); aa=pre.loc[j].values; bb=pos.loc[j].values; diff=bb-aa
    dz=float(np.mean(diff)/np.std(diff,ddof=1)) if np.std(diff)>0 else 0.0
    try: p=float(wilcoxon(aa,bb).pvalue)
    except Exception: p=1.0
    prepos[k]={'pre':float(np.mean(aa)),'pos':float(np.mean(bb)),'dz':dz,'p':p,'sig':bool(p<0.05)}
R['prepos']=prepos

# 5) PERFIS: prevalência D1 vs D7 e migração por atleta e por posição
def prof_day(dia):
    s=h[h.dia==dia].dropna(subset=['perfil'])
    return s.groupby('ID')['perfil'].agg(lambda x: x.mode().iloc[0] if len(x.mode()) else x.iloc[0])
p1=prof_day(1); p7=prof_day(7); jj=p1.index.intersection(p7.index)
mig=pd.DataFrame({'d1':p1.loc[jj],'d7':p7.loc[jj]})
R['perfil_prev']={'D1':p1.value_counts().to_dict(),'D7':p7.value_counts().to_dict()}
R['perfil_migracao_n']=int((mig.d1!=mig.d7).sum()); R['perfil_estavel_n']=int((mig.d1==mig.d7).sum())
# migração por posição
posmap=phys.set_index('ID')['pos'].to_dict()
mig['pos']=[posmap.get(i) for i in mig.index]
R['perfil_por_pos']={}
for pos in mig['pos'].dropna().unique():
    sub=mig[mig['pos']==pos]
    R['perfil_por_pos'][pos]={'n':int(len(sub)),'mudaram':int((sub.d1!=sub.d7).sum()),
        'D1':sub.d1.value_counts().to_dict(),'D7':sub.d7.value_counts().to_dict()}

# 6) POR POSIÇÃO: média semanal e deterioração (Δ D1->D7) por dimensão
R['por_pos']={}
for pos in h['pos'].dropna().unique():
    sub=h[h['pos']==pos]; ids=sub['ID'].unique()
    wk={k:float(pd.to_numeric(sub[k],errors='coerce').mean()) for k in KEYS}
    dd={}
    for k in KEYS:
        a=h[(h.dia==1)&(h.ID.isin(ids))].groupby('ID')[k].mean(); b=h[(h.dia==7)&(h.ID.isin(ids))].groupby('ID')[k].mean()
        j=a.index.intersection(b.index); dd[k]=float((b.loc[j]-a.loc[j]).mean()) if len(j) else None
    pv=float(auth[auth.ID.isin(ids)]['PV'].mean()) if auth is not None else None
    R['por_pos'][pos]={'n':int(len(ids)),'semanal':wk,'delta_d1d7':dd,'PV':pv}

# 7) POR ATLETA: Δ D1->D7 por dimensão (deterioração individual)
ath={}
for pid in sorted(h['ID'].unique()):
    a=h[(h.dia==1)&(h.ID==pid)]; b=h[(h.dia==7)&(h.ID==pid)]
    if len(a) and len(b):
        ath[pid]={k:float(pd.to_numeric(b[k],errors='coerce').mean()-pd.to_numeric(a[k],errors='coerce').mean()) for k in ['Vigor','Fadiga','TMD','Depressao']}
        ath[pid]['pos']=posmap.get(pid)
R['por_atleta']=ath

# 8) APTIDÃO (T-car PV) × DETERIORAÇÃO do humor (a pergunta central)
# Δ D1->D7 por atleta + PV
dlt={}
for k in ['Vigor','Fadiga','TMD','Depressao','FadFisica']:
    a=h[h.dia==1].groupby('ID')[k].mean(); b=h[h.dia==7].groupby('ID')[k].mean()
    j=a.index.intersection(b.index); dlt[k]=(b.loc[j]-a.loc[j])
DL=pd.DataFrame(dlt).reset_index().merge(auth,on='ID',how='inner')
R['pv_vs_deterioracao']={}
for k in ['Vigor','Fadiga','TMD','Depressao','FadFisica']:
    d=DL[['PV',k]].dropna(); r,p=spearmanr(d['PV'],d[k])
    R['pv_vs_deterioracao'][k]={'rho':float(r),'p':float(p),'n':int(len(d))}
# também: |deterioração global| (soma dos |Δ| do eixo) vs PV
DL['abs_det']=DL[['Vigor','Fadiga','TMD']].abs().sum(axis=1)
d=DL[['PV','abs_det']].dropna(); r,p=spearmanr(d['PV'],d['abs_det'])
R['pv_vs_deterioracao']['global_abs']={'rho':float(r),'p':float(p),'n':int(len(d))}
DL.to_csv('deter_pv.csv',index=False)

json.dump(R,open('all_results.json','w'),ensure_ascii=False,indent=1)
print('OK all_results.json | atletas:',h.ID.nunique(),'| posições:',list(h['pos'].dropna().unique()))
print('\n=== ENTRE DIAS: Friedman (W) e D1->D7 (dz) ===')
for k,l in DIMS:
    fr=friq.get(k); d=d1d7[k]
    frs='W=%.2f p=%.3f'%(fr['W'],fr['p']) if fr else 'n/d'
    print('  %-13s por dia %s | D1->D7 Δ=%+.2f dz=%+.2f p=%.3f %s'%(l,frs,d['delta'],d['dz'],d['p'],'*' if d['sig'] else ''))
print('\n=== APTIDÃO (PV) × DETERIORAÇÃO D1->D7 (a pergunta central) ===')
for k in ['Vigor','Fadiga','TMD','Depressao','FadFisica','global_abs']:
    v=R['pv_vs_deterioracao'][k]; print('  PV × Δ%-11s rho=%+.2f p=%.3f n=%d'%(k,v['rho'],v['p'],v['n']))
print('\n=== POR POSIÇÃO: deterioração Δ D1->D7 (vigor/fadiga/PTH) e PV ===')
for pos,v in R['por_pos'].items():
    print('  %-9s n=%d PV=%s | Δvigor=%+.1f Δfadiga=%+.1f ΔPTH=%+.1f'%(pos,v['n'],('%.1f'%v['PV']) if v['PV'] else 'n/d',v['delta_d1d7']['Vigor'],v['delta_d1d7']['Fadiga'],v['delta_d1d7']['TMD']))
print('\n=== PERFIS: migração ===')
print('  mudaram de perfil D1->D7:',R['perfil_migracao_n'],'| estáveis:',R['perfil_estavel_n'])
print('  prevalência D1:',R['perfil_prev']['D1'])
print('  prevalência D7:',R['perfil_prev']['D7'])
