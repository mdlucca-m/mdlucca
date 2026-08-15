import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
h=pd.read_csv('hum_prof.csv')
R=json.load(open('brums_desc.json'))  # base stats
days=np.arange(1,8)
SUB6=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
LAB6=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
def mag(dz):
    a=abs(dz); return 'trivial' if a<0.2 else ('pequeno' if a<0.5 else ('médio' if a<0.8 else 'grande'))

# ---- 1) correlation matrix (trait = athlete weekly means) ----
wk=h.groupby('ID')[SUB6].mean()
corr=wk.corr(method='spearman')
R['corr_trait']=[[float(corr.loc[a,b]) for b in SUB6] for a in SUB6]
# observation-level too
corr_o=h[SUB6].corr(method='spearman')
R['corr_obs']=[[float(corr_o.loc[a,b]) for b in SUB6] for a in SUB6]
R['corr_labels']=LAB6

# ---- 2) per-day correlation of negatives with Fadiga and Vigor ----
dm=h.groupby(['ID','dia'])[SUB6].mean().reset_index()
perday={}
for neg in ['Depressao','Raiva','Confusao','Tensao']:
    perday[neg]={'fad':{},'vig':{}}
    for d in days:
        sub=dm[dm.dia==d]
        rf=stats.spearmanr(sub[neg],sub['Fadiga'],nan_policy='omit').correlation
        rv=stats.spearmanr(sub[neg],sub['Vigor'],nan_policy='omit').correlation
        perday[neg]['fad'][int(d)]=float(rf); perday[neg]['vig'][int(d)]=float(rv)
R['perday_corr']=perday

# ---- 3) negatives intra-day pré→pós per day + D1/D7 focus ----
R['intraday_neg']={}
for k in ['Depressao','Raiva','Confusao','Tensao']:
    dd={}
    for d in days:
        sub=h[(h.dia==d)&(h.momento.isin(['pre','pos']))]
        piv=sub.pivot_table(index='ID',columns='momento',values=k,aggfunc='mean')
        if 'pre' in piv and 'pos' in piv:
            a=piv['pre']; b=piv['pos']; c=a.dropna().index.intersection(b.dropna().index); a,b=a.loc[c],b.loc[c]; di=b-a
            if len(di)>2 and di.std(ddof=1)>0:
                dz=di.mean()/di.std(ddof=1); p=stats.wilcoxon(a,b).pvalue
                dd[int(d)]=dict(pre=float(a.mean()),pos=float(b.mean()),delta=float(di.mean()),dz=float(dz),p=float(p))
            else: dd[int(d)]=dict(pre=float(a.mean()) if len(a) else None,pos=float(b.mean()) if len(b) else None,delta=float(di.mean()) if len(di) else None,dz=None,p=None)
    R['intraday_neg'][k]=dd

# ---- 4) focus on max-vigor day (D1) and max-fatigue day (D7): negatives level + corr ----
def day_focus(d):
    sub=dm[dm.dia==d]
    out={}
    for neg in ['Depressao','Raiva','Confusao','Tensao']:
        out[neg]=dict(mean=float(sub[neg].mean()),
            rho_fad=float(stats.spearmanr(sub[neg],sub['Fadiga'],nan_policy='omit').correlation),
            rho_vig=float(stats.spearmanr(sub[neg],sub['Vigor'],nan_policy='omit').correlation))
    return out
R['focus']={'D1':day_focus(1),'D7':day_focus(7)}
# which day each negative peaks
R['neg_peak']={}
for k,lab in [('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão'),('Tensao','Tensão')]:
    dmean=h.groupby('dia')[k].mean().reindex(days)
    R['neg_peak'][k]=dict(peak_day=int(dmean.idxmax()),peak_val=float(dmean.max()),min_day=int(dmean.idxmin()),min_val=float(dmean.min()))
json.dump(R,open('brums_desc2.json','w'),indent=1,ensure_ascii=False)
print('corr trait matrix (Spearman):')
print('        '+' '.join('%7s'%l[:7] for l in LAB6))
for i,a in enumerate(LAB6): print('%8s '%a[:8]+' '.join('%+7.2f'%R['corr_trait'][i][j] for j in range(6)))
print('\nnegativas — pico e mínimo:')
for k,v in R['neg_peak'].items(): print('  %-10s pico D%d=%.2f | mín D%d=%.2f'%(k,v['peak_day'],v['peak_val'],v['min_day'],v['min_val']))
print('\nFOCO D1 (maior vigor):')
for neg,v in R['focus']['D1'].items(): print('  %-10s média=%.2f ρ×fadiga=%+.2f ρ×vigor=%+.2f'%(neg,v['mean'],v['rho_fad'],v['rho_vig']))
print('FOCO D7 (maior fadiga):')
for neg,v in R['focus']['D7'].items(): print('  %-10s média=%.2f ρ×fadiga=%+.2f ρ×vigor=%+.2f'%(neg,v['mean'],v['rho_fad'],v['rho_vig']))
