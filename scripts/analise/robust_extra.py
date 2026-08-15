import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import statsmodels.formula.api as smf
from scipy import stats
import plotly.graph_objects as go
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
F=pd.read_csv('tcar2_features.csv')[['ID','PVini']].rename(columns={'PVini':'PV'})
SUB=[('FadFisica','Fadiga física'),('Fadiga','Fadiga (BRUMS)'),('TMD','PTH/TMD'),('Vigor','Vigor'),
     ('FadMental','Fadiga mental'),('Depressao','Depressão'),('Tensao','Tensão'),('Raiva','Raiva'),('Confusao','Confusão')]
piv=h.pivot_table(index=['ID','dia'],columns='momento',values=[s for s,_ in SUB],aggfunc='mean')
rng=np.random.default_rng(2024)
AC={}
for v,lab in SUB:
    a=piv[(v,'pre')]; b=piv[(v,'pos')]; dd=(b-a).dropna()
    dz=dd.mean()/dd.std(); p=stats.wilcoxon(dd).pvalue if dd.std()>0 else 1.0
    ids=dd.index.get_level_values(0).unique(); boot=[]
    dfb=dd.reset_index()
    for _ in range(1000):
        s=rng.choice(ids,len(ids),True); g=pd.concat([dfb[dfb.ID==i] for i in s])[0]
        if g.std()>0: boot.append(g.mean()/g.std())
    lo,hi=np.percentile(boot,[2.5,97.5])
    AC[v]=dict(lab=lab,delta=float(dd.mean()),dz=float(dz),lo=float(lo),hi=float(hi),p=float(p),n=int(len(dd)))
# mixed models (report)
df=h.merge(F,on='ID',how='left').dropna(subset=['PV']).copy(); df['dia_c']=df.dia-4; df['PV_c']=df.PV-df.PV.mean()
MM={}
for y in ['Vigor','FadFisica']:
    m=smf.mixedlm('%s ~ dia_c * PV_c'%y,df,groups=df['ID'],re_formula='~dia_c').fit(reml=False)
    MM[y]={t:dict(b=float(m.fe_params[t]),p=float(m.pvalues[t])) for t in ['dia_c','PV_c','dia_c:PV_c']}
json.dump(dict(acute=AC,mm=MM,n_obs=int(len(df)),n_ath=int(df.ID.nunique())),open('robust_extra.json','w'))

# forest plot dz
order=sorted(SUB,key=lambda x:-abs(AC[x[0]]['dz']))
labs=[AC[v]['lab'] for v,_ in order]; dz=[AC[v]['dz'] for v,_ in order]
lo=[AC[v]['dz']-AC[v]['lo'] for v,_ in order]; hi=[AC[v]['hi']-AC[v]['dz'] for v,_ in order]
cols=['#c92a2a' if AC[v]['p']<0.05 and AC[v]['dz']>0 else ('#2b8a3e' if AC[v]['p']<0.05 else '#adb5bd') for v,_ in order]
f=go.Figure()
f.add_trace(go.Scatter(x=dz,y=labs,mode='markers',marker=dict(size=13,color=cols),
    error_x=dict(type='data',symmetric=False,array=hi,arrayminus=lo,color='#495057',thickness=2),showlegend=False))
f.add_vline(x=0,line=dict(color='#111',width=1))
for thr,txt in [(0.2,'pequeno'),(0.5,'médio'),(0.8,'grande')]:
    f.add_vline(x=thr,line=dict(color='#ced4da',dash='dot')); f.add_vline(x=-thr,line=dict(color='#ced4da',dash='dot'))
f.update_layout(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    height=560,width=1000,xaxis_title='Tamanho de efeito pré→pós (dz) com IC95%',yaxis=dict(autorange='reversed'),margin=dict(l=140,r=30,t=30,b=55))
f.write_image(f'{OUT}/x_agudo.png',width=1400,height=760,scale=2)
print('fig x_agudo OK')
print('ACUTE (dz, ordenado):')
for v,_ in order: a=AC[v]; print('  %-14s dz=%+.2f [%.2f,%.2f] p=%.1e'%(a['lab'],a['dz'],a['lo'],a['hi'],a['p']))
print('MM Vigor dia p=%.4f PV p=%.4f | FadFis dia p=%.1e PV p=%.4f'%(MM['Vigor']['dia_c']['p'],MM['Vigor']['PV_c']['p'],MM['FadFisica']['dia_c']['p'],MM['FadFisica']['PV_c']['p']))
