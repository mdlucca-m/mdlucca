import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
h=pd.read_csv('hum_prof.csv')
days=np.arange(1,8)
def dmean(v,mask=None):
    d=h if mask is None else h[mask]
    return d.groupby('dia')[v].mean().reindex(days).values
# --- daily group means (all obs) ---
V=dmean('Vigor'); Fa=dmean('Fadiga')
diff=V-Fa   # energy-fatigue gap
# zero crossings (linear interp) of Vigor - Fadiga across days
cross=[]
for i in range(len(days)-1):
    a,b=diff[i],diff[i+1]
    if a==0: cross.append(float(days[i]))
    if a*b<0:
        frac=a/(a-b); cross.append(float(days[i]+frac))
# --- pre/pos resolution: 14 timepoints ---
pre_i=h.momento=='pre'; pos_i=h.momento=='pos'
Vpre=dmean('Vigor',pre_i); Vpos=dmean('Vigor',pos_i)
Fpre=dmean('Fadiga',pre_i); Fpos=dmean('Fadiga',pos_i)
# build ordered timeline day.moment: pre=day, pos=day+0.5
tl=[]; xs=[]
for i,d in enumerate(days):
    tl.append((d,'pré',Vpre[i],Fpre[i])); xs.append(d)
    tl.append((d,'pós',Vpos[i],Fpos[i])); xs.append(d+0.5)
Vser=np.array([t[2] for t in tl]); Fser=np.array([t[3] for t in tl]); dser=Vser-Fser
cross_pp=[]
for i in range(len(xs)-1):
    a,b=dser[i],dser[i+1]
    if a*b<0:
        frac=a/(a-b); xc=xs[i]+frac*(xs[i+1]-xs[i]); cross_pp.append(float(xc))
# --- intraday acute change pre->pos, averaged and per day ---
acute={}
for v in ['Vigor','Fadiga','TMD']:
    pr=dmean(v,pre_i); po=dmean(v,pos_i); acute[v]=dict(pre=float(np.nanmean(pr)),pos=float(np.nanmean(po)),
        delta=float(np.nanmean(po-pr)),per_day={int(d):float(po[i]-pr[i]) for i,d in enumerate(days)})
# --- limits (amplitude), derivatives, decomposition per variable ---
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
dec={}
for v,lab in VARS:
    dd=h.dropna(subset=[v]); dm=dd.groupby('dia')[v].mean().reindex(days).values
    # derivatives via cubic fit
    c=np.polyfit(days,dm,3); vel=np.polyval(np.polyder(c,1),days); acc=np.polyval(np.polyder(c,2),days)
    pkvel=int(days[np.argmax(np.abs(vel))]); pkvel_val=float(vel[np.argmax(np.abs(vel))])
    # limits/amplitude
    amp_tot=float(dd[v].max()-dd[v].min()); amp_sig=float(np.nanmax(dm)-np.nanmin(dm))
    amp_intra=float(dd.groupby('ID')[v].apply(lambda s:s.max()-s.min()).mean())
    # variance decomposition athlete/day/residual
    try:
        m=smf.ols('%s ~ C(ID)+C(dia)'%v,data=dd).fit(); a=anova_lm(m,typ=1); ss=a['sum_sq']
        tot=ss['C(ID)']+ss['C(dia)']+ss['Residual']
        vc=dict(ath=float(100*ss['C(ID)']/tot),day=float(100*ss['C(dia)']/tot),res=float(100*ss['Residual']/tot))
    except Exception: vc=dict(ath=np.nan,day=np.nan,res=np.nan)
    dec[v]=dict(lab=lab,amp_tot=amp_tot,amp_sig=amp_sig,amp_intra=amp_intra,
        vel={int(d):float(x) for d,x in zip(days,vel)},acc={int(d):float(x) for d,x in zip(days,acc)},
        pkvel_day=pkvel,pkvel_val=pkvel_val,vc=vc,dm={int(d):float(x) for d,x in zip(days,dm)})
R=dict(cross_day=cross,cross_pp=cross_pp,diff={int(d):float(x) for d,x in zip(days,diff)},
    Vday={int(d):float(x) for d,x in zip(days,V)},Fday={int(d):float(x) for d,x in zip(days,Fa)},
    acute=acute,dec=dec,
    Vpre={int(d):float(Vpre[i]) for i,d in enumerate(days)},Vpos={int(d):float(Vpos[i]) for i,d in enumerate(days)},
    Fpre={int(d):float(Fpre[i]) for i,d in enumerate(days)},Fpos={int(d):float(Fpos[i]) for i,d in enumerate(days)})
json.dump(R,open('cross.json','w'),indent=1,ensure_ascii=False)
print('Vigor por dia :',{int(d):round(x,2) for d,x in zip(days,V)})
print('Fadiga por dia:',{int(d):round(x,2) for d,x in zip(days,Fa)})
print('Cruzamento Vigor=Fadiga (dias):',[round(x,2) for x in cross])
print('Cruzamento com resolução pré/pós (dia.frac):',[round(x,2) for x in cross_pp])
print('\nMudança aguda pré->pós (média): Vigor %.2f  Fadiga %.2f  PTH %.2f'%(acute['Vigor']['delta'],acute['Fadiga']['delta'],acute['TMD']['delta']))
print('Dia de maior taxa (derivada): Vigor D%d (%.2f/dia)  Fadiga D%d (%.2f/dia)'%(dec['Vigor']['pkvel_day'],dec['Vigor']['pkvel_val'],dec['Fadiga']['pkvel_day'],dec['Fadiga']['pkvel_val']))
print('\nDecomposição da variância (atleta/dia/resíduo):')
for v,lab in VARS: vc=dec[v]['vc']; print('  %-10s atleta=%.0f%% dia=%.0f%% resíduo=%.0f%% | amplitude sinal=%.2f'%(lab,vc['ath'],vc['day'],vc['res'],dec[v]['amp_sig']))
