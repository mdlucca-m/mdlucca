import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy.stats import spearmanr, mannwhitneyu, wilcoxon, kruskal
h=pd.read_csv('hum_prof.csv')
phys=pd.read_csv('phys.csv'); F=pd.read_csv('tcar2_features.csv'); PW=pd.read_csv('pv_wk.csv')
LD=pd.read_csv('hiit_load.csv')
OUT={}
DIMS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('Depressao','Depressão'),('Tensao','Tensão'),
      ('Raiva','Raiva'),('Confusao','Confusão'),('TMD','PTH'),('FadFisica','Fadiga física')]

# ---------- 1) T-CAR descritiva (pico de velocidade) ----------
def desc(s): s=pd.to_numeric(s,errors='coerce').dropna(); return dict(n=int(s.size),m=float(s.mean()),sd=float(s.std(ddof=1)),mn=float(s.min()),mx=float(s.max()))
OUT['tcar']={'PVini':desc(phys['TCAR_PV_ini']),'PVfin':desc(phys['TCAR_PV_final']),
             'dPV':desc(phys['TCAR_PV_final']-phys['TCAR_PV_ini']),'massa':desc(phys['massa']),
             'reps_ini':desc(phys['TCAR_reps_ini']),'reps_fin':desc(phys['TCAR_reps_final'])}

# ---------- 2) T-CAR baseline (PVini) x BRUMS baseline (todas as dimensões, Spearman) ----------
bcol={'Vigor':'b_Vigor','Fadiga':'b_Fadiga','Depressao':'b_Depressao','Tensao':'b_Tensao',
      'Raiva':'b_Raiva','Confusao':'b_Confusao','TMD':'b_TMD','FadFisica':'b_FadFisica'}
cor={}
for k,lab in DIMS:
    d=F[['PVini',bcol[k]]].apply(pd.to_numeric,errors='coerce').dropna()
    r,p=spearmanr(d['PVini'],d[bcol[k]])
    cor[k]={'rho':float(r),'p':float(p),'n':int(len(d))}
OUT['cor_baseline']=cor

# ---------- 3) Tercis de aptidão (T-car) x humor semanal ----------
terc={}
for k,lab in DIMS:
    if k not in PW.columns: continue
    groups=[pd.to_numeric(PW[PW.terc==t][k],errors='coerce').dropna() for t in ['Baixa','Média','Alta']]
    try: st,p=kruskal(*groups)
    except Exception: p=np.nan
    terc[k]={'Baixa':float(groups[0].mean()),'Média':float(groups[1].mean()),'Alta':float(groups[2].mean()),
             'p':float(p),'ns':[int(g.size) for g in groups]}
OUT['tercis']=terc
OUT['terc_pv']={t:float(pd.to_numeric(PW[PW.terc==t]['PVini'],errors='coerce').mean()) for t in ['Baixa','Média','Alta']}

# ---------- 4) Dias HIIT (2,4,7) vs sem HIIT (1,3,5,6): humor por atleta (Wilcoxon pareado) ----------
HII=[2,4,7]; NOH=[1,3,5,6]
hiit_cmp={}
for k,lab in DIMS:
    a=h[h.dia.isin(HII)].groupby('ID')[k].mean(); b=h[h.dia.isin(NOH)].groupby('ID')[k].mean()
    j=a.index.intersection(b.index); aa=a.loc[j].values; bb=b.loc[j].values; diff=aa-bb
    dz=float(np.mean(diff)/np.std(diff,ddof=1)) if np.std(diff)>0 else 0.0
    try: p=float(wilcoxon(aa,bb).pvalue)
    except Exception: p=1.0
    hiit_cmp[k]={'hiit':float(np.mean(aa)),'noh':float(np.mean(bb)),'dz':dz,'p':p,'n':int(len(j)),'sig':bool(p<0.05)}
OUT['hiit_vs_noh']=hiit_cmp

# ---------- 5) Resposta aguda (pré->pós) em dias HIIT vs sem HIIT ----------
g=h.dropna(subset=['dia']).groupby(['dia','momento','ID']).mean(numeric_only=True).reset_index()
acute={}
for k,lab in DIMS:
    def delta(dias):
        pre=h[(h.dia.isin(dias))&(h.momento=='pre')].groupby('ID')[k].mean()
        pos=h[(h.dia.isin(dias))&(h.momento=='pos')].groupby('ID')[k].mean()
        j=pre.index.intersection(pos.index); return (pos.loc[j]-pre.loc[j])
    dh=delta([2,4,7]); dn=delta([3,5,6])  # dia1 só baseline; sem-HIIT com pré/pós = 3,5,6
    if len(dh)>3 and len(dn)>3:
        try: p=float(mannwhitneyu(dh.values,dn.values).pvalue)
        except Exception: p=1.0
        acute[k]={'hiit':float(dh.mean()),'noh':float(dn.mean()),'p':float(p),'sig':bool(p<0.05)}
OUT['acute_hiit']=acute

# ---------- 6) Carga interna do HIIT x resposta aguda do humor (mesmo dia) ----------
# junta carga (mean_pse, mean_fc) por (ID,dia) com delta pré->pós do mesmo dia
load_mood={}
mrg=[]
for _,r in LD.dropna(subset=['dia']).iterrows():
    d=int(r['dia']); pid=r['ID']
    pre=h[(h.ID==pid)&(h.dia==d)&(h.momento=='pre')]
    pos=h[(h.ID==pid)&(h.dia==d)&(h.momento=='pos')]
    if len(pre) and len(pos):
        mrg.append(dict(ID=pid,dia=d,mean_pse=r['mean_pse'],mean_fc=r['mean_fc'],final_pse=r['final_pse'],
            dTMD=float(pos['TMD'].iloc[0]-pre['TMD'].iloc[0]),dFad=float(pos['Fadiga'].iloc[0]-pre['Fadiga'].iloc[0]),
            dVig=float(pos['Vigor'].iloc[0]-pre['Vigor'].iloc[0]),dDep=float(pos['Depressao'].iloc[0]-pre['Depressao'].iloc[0])))
M=pd.DataFrame(mrg)
for load in ['mean_pse','mean_fc','final_pse']:
    for mood in ['dTMD','dFad','dVig','dDep']:
        d=M[[load,mood]].dropna(); r,p=spearmanr(d[load],d[mood])
        load_mood['%s~%s'%(load,mood)]={'rho':float(r),'p':float(p),'n':int(len(d))}
OUT['load_mood']=load_mood
OUT['hiit_load_desc']={'mean_fc':desc(LD['mean_fc']),'peak_fc':desc(LD['peak_fc']),
    'mean_pse':desc(LD['mean_pse']),'final_pse':desc(LD['final_pse'])}
# %FCmax por sessão usando FCmax do T-car
fcmax=phys.set_index('ID')['massa']*0+F.set_index('ID')['FCmax']
LD2=LD.dropna(subset=['ID']).copy(); LD2['fcmax']=LD2['ID'].map(F.set_index('ID')['FCmax'])
LD2['pct']=100*LD2['mean_fc']/LD2['fcmax']
OUT['pct_fcmax']=desc(LD2['pct'])

# ---------- 7) Alometria PV ~ massa (log-log) ----------
d=phys[['massa','TCAR_PV_ini']].apply(pd.to_numeric,errors='coerce').dropna()
lx=np.log(d['massa']); ly=np.log(d['TCAR_PV_ini']); b1,b0=np.polyfit(lx,ly,1)
r,p=spearmanr(d['massa'],d['TCAR_PV_ini'])
OUT['allometry']={'expoente':float(b1),'rho_massa_pv':float(r),'p':float(p),'n':int(len(d))}

# ---------- 8) ROC / limiar PVini para discriminar alta fadiga semanal ----------
from sklearn.metrics import roc_auc_score, roc_curve
pw=PW[['ID','PVini','FadFisica','Fadiga','TMD']].apply(pd.to_numeric,errors='coerce') if 'PVini' in PW else None
pw=PW.copy()
pw['PVini']=pd.to_numeric(pw['PVini'],errors='coerce')
for target in ['FadFisica','Fadiga','TMD']:
    y=pd.to_numeric(pw[target],errors='coerce'); med=y.median(); hi=(y>med).astype(int)
    x=pw['PVini']; d=pd.DataFrame({'x':x,'y':hi}).dropna()
    # PV baixo prediz alta fadiga -> usar -x
    auc=roc_auc_score(d['y'],-d['x'])
    fpr,tpr,thr=roc_curve(d['y'],-d['x']); j=np.argmax(tpr-fpr); cut=-thr[j]
    OUT.setdefault('roc',{})[target]={'auc':float(auc),'cut_pvini':float(cut),'sens':float(tpr[j]),'spec':float(1-fpr[j]),'n':int(len(d))}

json.dump(OUT,open('physio.json','w'),ensure_ascii=False,indent=1)
print('OK physio.json')
print('\nT-CAR PVini: %.1f ± %.1f km/h | PVfin %.1f | ΔPV +%.2f'%(OUT['tcar']['PVini']['m'],OUT['tcar']['PVini']['sd'],OUT['tcar']['PVfin']['m'],OUT['tcar']['dPV']['m']))
print('\nPVini × BRUMS baseline (Spearman):')
for k,l in DIMS: print('  %-13s rho=%+.2f p=%.3f'%(l,cor[k]['rho'],cor[k]['p']))
print('\nHIIT vs sem-HIIT (humor por atleta, dz):')
for k,l in DIMS: c=hiit_cmp[k]; print('  %-13s HIIT %.2f vs %.2f | dz=%+.2f p=%.3f %s'%(l,c['hiit'],c['noh'],c['dz'],c['p'],'*' if c['sig'] else ''))
print('\nCarga HIIT × resposta aguda (Spearman signif.):')
for k,v in OUT['load_mood'].items():
    if v['p']<0.10: print('  %-16s rho=%+.2f p=%.3f'%(k,v['rho'],v['p']))
print('\n%%FCmax no esforco HIIT: %.1f ± %.1f'%(OUT['pct_fcmax']['m'],OUT['pct_fcmax']['sd']))
print('Alometria PV~massa: expoente=%.2f rho=%+.2f p=%.3f'%(OUT['allometry']['expoente'],OUT['allometry']['rho_massa_pv'],OUT['allometry']['p']))
print('\nROC PVini -> alta fadiga:')
for t,v in OUT['roc'].items(): print('  %-11s AUC=%.2f cut=%.1f km/h sens=%.2f spec=%.2f'%(t,v['auc'],v['cut_pvini'],v['sens'],v['spec']))
print('\nTercis (PV) × humor semanal:')
print('  PV:',{t:round(OUT['terc_pv'][t],1) for t in ['Baixa','Média','Alta']})
for k in ['FadFisica','Fadiga','TMD','Depressao','Vigor']:
    if k in terc: print('  %-11s'%k,{t:round(terc[k][t],1) for t in ['Baixa','Média','Alta']},'p=%.3f'%terc[k]['p'])
