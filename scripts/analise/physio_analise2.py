import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, unicodedata
from scipy.stats import spearmanr, wilcoxon, mannwhitneyu, kruskal
from sklearn.metrics import roc_auc_score, roc_curve
def norm(s): return unicodedata.normalize('NFKD',str(s).strip().lower()).encode('ascii','ignore').decode()
h=pd.read_csv('hum_prof.csv')
k=pd.read_csv('key.csv'); k.columns=['ID','nome']; name2id={norm(r['nome']):r['ID'] for _,r in k.iterrows()}
D=pd.ExcelFile('Handebol_2024.xlsx').parse('Dados'); D['ID']=D['Atleta'].map(lambda s: name2id.get(norm(s))); D=D.dropna(subset=['ID'])
LD=pd.read_csv('hiit_load.csv')
OUT={}
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Depressao','Depressão'),('Tensao','Tensão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','PTH'),('FadFisica','Fadiga física')]
def desc(s): s=pd.to_numeric(s,errors='coerce').dropna(); return dict(n=int(s.size),m=float(s.mean()),sd=float(s.std(ddof=1)),mn=float(s.min()),mx=float(s.max()))

# 1) T-CAR descritiva (autoritativa, mestre)
OUT['tcar']={'PVpre':desc(D['TCARpv_pre']),'PVpos':desc(D['TCARpv_pos']),'dPV':desc(D['TCARpv_pos']-D['TCARpv_pre']),'massa':desc(D['Massa'])}

# merge autoritativo: PV + humor semanal + baseline (D1) + sono/estresse
wk=h.dropna(subset=['dia']).groupby('ID').agg(**{k:(k,'mean') for k,_ in DIMS}).reset_index()
base=h[h.dia==1].groupby('ID').agg(**{'b_'+k:(k,'mean') for k,_ in DIMS}).reset_index()
ss=h.groupby('ID').agg(Epworth=('Epworth','mean'),PSS=('PSS','mean')).reset_index()
M=D[['ID','TCARpv_pre','TCARpv_pos','Massa']].rename(columns={'TCARpv_pre':'PV','TCARpv_pos':'PVpos','Massa':'massa'})
M=M.merge(wk,on='ID').merge(base,on='ID',how='left').merge(ss,on='ID',how='left')
M['dPV']=M['PVpos']-M['PV']; M.to_csv('auth_full.csv',index=False)

# 2) PV x humor semanal + PV x baseline (todas as dimensões, incl depressão)
OUT['pv_week']={}; OUT['pv_base']={}
for kk,lab in DIMS:
    d=M[['PV',kk]].dropna(); r,p=spearmanr(d['PV'],d[kk]); OUT['pv_week'][kk]={'rho':float(r),'p':float(p),'n':int(len(d))}
    if 'b_'+kk in M:
        d=M[['PV','b_'+kk]].dropna(); r,p=spearmanr(d['PV'],d['b_'+kk]); OUT['pv_base'][kk]={'rho':float(r),'p':float(p),'n':int(len(d))}

# 3) tercis de aptidão x humor semanal
M['terc']=pd.qcut(M['PV'],3,labels=['Baixa','Média','Alta'])
OUT['terc_pv']={t:float(M[M.terc==t]['PV'].mean()) for t in ['Baixa','Média','Alta']}
OUT['tercis']={}
for kk,lab in DIMS:
    g=[M[M.terc==t][kk].dropna() for t in ['Baixa','Média','Alta']]
    try: st,p=kruskal(*g)
    except: p=np.nan
    OUT['tercis'][kk]={t:float(M[M.terc==t][kk].mean()) for t in ['Baixa','Média','Alta']}; OUT['tercis'][kk]['p']=float(p)

# 4) HIIT (2,4,7) vs sem HIIT (1,3,5,6): humor por atleta (27 do BRUMS)
HII=[2,4,7]; NOH=[1,3,5,6]; OUT['hiit_vs_noh']={}
for kk,lab in DIMS:
    a=h[h.dia.isin(HII)].groupby('ID')[kk].mean(); b=h[h.dia.isin(NOH)].groupby('ID')[kk].mean()
    j=a.index.intersection(b.index); aa=a.loc[j].values; bb=b.loc[j].values; diff=aa-bb
    dz=float(np.mean(diff)/np.std(diff,ddof=1)) if np.std(diff)>0 else 0.0
    try: p=float(wilcoxon(aa,bb).pvalue)
    except: p=1.0
    OUT['hiit_vs_noh'][kk]={'hiit':float(np.mean(aa)),'noh':float(np.mean(bb)),'dz':dz,'p':p,'n':int(len(j)),'sig':bool(p<0.05)}

# 5) carga interna do microciclo (FC/PSE das sessões HIIT do xlsx) — %FCmax com FCmax do T-car (~198)
FCMAX=198.5
LD2=LD.dropna(subset=['dia']).copy(); LD2['pctFC']=100*LD2['mean_fc']/FCMAX
OUT['hiit_load']={'mean_fc':desc(LD['mean_fc']),'peak_fc':desc(LD['peak_fc']),'mean_pse':desc(LD['mean_pse']),
    'final_pse':desc(LD['final_pse']),'pctFCmax':desc(LD2['pctFC'])}
OUT['hiit_load_by_day']={int(d):{'fc':float(LD[LD.dia==d]['mean_fc'].mean()),'pse':float(LD[LD.dia==d]['final_pse'].mean())} for d in [2,4,7]}

# 6) ROC/limiar PVini -> alta fadiga/PTH semanal (mediana), autoritativo
OUT['roc']={}
for target in ['FadFisica','Fadiga','TMD','Vigor']:
    y=pd.to_numeric(M[target],errors='coerce'); med=y.median()
    hi=(y>med).astype(int) if target!='Vigor' else (y<med).astype(int)  # baixo vigor = risco
    d=pd.DataFrame({'x':M['PV'],'y':hi}).dropna()
    auc=roc_auc_score(d['y'],-d['x']); fpr,tpr,thr=roc_curve(d['y'],-d['x']); jj=np.argmax(tpr-fpr); cut=-thr[jj]
    OUT['roc'][target]={'auc':float(auc),'cut':float(cut),'sens':float(tpr[jj]),'spec':float(1-fpr[jj]),'n':int(len(d))}

# 7) alometria PV ~ massa (log-log)
d=M[['massa','PV']].dropna(); b1,b0=np.polyfit(np.log(d['massa']),np.log(d['PV']),1); r,p=spearmanr(d['massa'],d['PV'])
OUT['allometry']={'expoente':float(b1),'rho':float(r),'p':float(p),'n':int(len(d))}
# aptidão escalonada por massa (PV/massa^0.19) x fadiga física
M['PV_allo']=M['PV']/ (M['massa']**abs(b1))
d=M[['PV_allo','FadFisica']].dropna(); r0,p0=spearmanr(M['PV'],M['FadFisica']); r1,p1=spearmanr(d['PV_allo'],d['FadFisica'])
OUT['allo_effect']={'bruto_rho':float(r0),'bruto_p':float(p0),'allo_rho':float(r1),'allo_p':float(p1)}

# 8) sono (Epworth) e estresse (PSS) x humor semanal
OUT['sleep_stress']={}
for pred in ['Epworth','PSS']:
    OUT['sleep_stress' if False else 'sleep_stress']=OUT.get('sleep_stress',{})
    for kk in ['Vigor','Fadiga','TMD','Depressao','FadFisica']:
        d=M[[pred,kk]].dropna(); r,p=spearmanr(d[pred],d[kk]); OUT['sleep_stress'].setdefault(pred,{})[kk]={'rho':float(r),'p':float(p),'n':int(len(d))}
OUT['epworth']=desc(M['Epworth']); OUT['pss']=desc(M['PSS'])

json.dump(OUT,open('physio2.json','w'),ensure_ascii=False,indent=1)
print('OK physio2.json | n T-car:',OUT['tcar']['PVpre']['n'])
print('\nT-CAR PV: %.1f±%.1f -> %.1f (ΔPV +%.2f)'%(OUT['tcar']['PVpre']['m'],OUT['tcar']['PVpre']['sd'],OUT['tcar']['PVpos']['m'],OUT['tcar']['dPV']['m']))
print('\nPV × humor semanal (Spearman):')
for kk,l in DIMS: v=OUT['pv_week'][kk]; print('  %-13s rho=%+.2f p=%.3f'%(l,v['rho'],v['p']))
print('\nPV × humor BASELINE (D1) — incl. depressão:')
for kk,l in DIMS: v=OUT['pv_base'].get(kk); print('  %-13s rho=%+.2f p=%.3f'%(l,v['rho'],v['p']))
print('\nHIIT vs sem-HIIT (dz):')
for kk,l in DIMS: v=OUT['hiit_vs_noh'][kk]; print('  %-13s dz=%+.2f p=%.3f %s'%(l,v['dz'],v['p'],'*' if v['sig'] else ''))
print('\nCarga microciclo: FC %.0f | %%FCmax %.0f | PSE final %.1f'%(OUT['hiit_load']['mean_fc']['m'],OUT['hiit_load']['pctFCmax']['m'],OUT['hiit_load']['final_pse']['m']))
print('ROC PVini:',{t:'AUC=%.2f cut=%.1f'%(v['auc'],v['cut']) for t,v in OUT['roc'].items()})
print('Alometria expoente=%.2f | bruto rho=%.2f->allo rho=%.2f'%(OUT['allometry']['expoente'],OUT['allo_effect']['bruto_rho'],OUT['allo_effect']['allo_rho']))
print('Epworth %.1f | PSS %.1f'%(OUT['epworth']['m'],OUT['pss']['m']))
print('Epworth×Fadiga rho=%.2f p=%.3f | PSS×TMD rho=%.2f p=%.3f'%(OUT['sleep_stress']['Epworth']['Fadiga']['rho'],OUT['sleep_stress']['Epworth']['Fadiga']['p'],OUT['sleep_stress']['PSS']['TMD']['rho'],OUT['sleep_stress']['PSS']['TMD']['p']))
