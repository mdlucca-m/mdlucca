import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
tc=pd.read_csv('tcar1_features.csv')[['ID','PV','dist','FCmax']]  # T-CAR 1
dm=h.groupby(['ID','dia'])['FadFisica'].mean().reset_index().merge(tc,on='ID',how='left')
def auc(score,label):
    s=np.asarray(score,float); y=np.asarray(label); pos=s[y==1]; neg=s[y==0]
    if len(pos)==0 or len(neg)==0: return np.nan
    return float(stats.mannwhitneyu(pos,neg).statistic/(len(pos)*len(neg)))
def logit(x,y):
    x=np.asarray(x,float); y=np.asarray(y,float); b0,b1=0.,0.
    for _ in range(300):
        z=b0+b1*x; pr=1/(1+np.exp(-z)); W=pr*(1-pr)+1e-9
        g0=np.sum(y-pr); g1=np.sum((y-pr)*x); h00=-np.sum(W); h01=-np.sum(W*x); h11=-np.sum(W*x*x); det=h00*h11-h01*h01
        b0-=(h11*g0-h01*g1)/det; b1-=(-h01*g0+h00*g1)/det
    return b0,b1
def loo(col,dd):
    ids=dd.ID.unique(); preds=[]; ys=[]
    for hold in ids:
        tr=dd[dd.ID!=hold]; te=dd[dd.ID==hold]
        if tr['ev'].nunique()<2: continue
        b0,b1=logit(tr[col],tr['ev']); pr=1/(1+np.exp(-(b0+b1*te[col].values))); preds+=list(pr); ys+=list(te['ev'].values)
    return float(auc(np.array(preds),np.array(ys))) if len(set(ys))>1 else np.nan
def youden(x,y,low=True):
    x=np.asarray(x,float); y=np.asarray(y); best=None
    for t in np.unique(x):
        pred=(x<=t).astype(int) if low else (x>=t).astype(int)
        tp=np.sum((pred==1)&(y==1)); fn=np.sum((pred==0)&(y==1)); tn=np.sum((pred==0)&(y==0)); fp=np.sum((pred==1)&(y==0))
        se=tp/(tp+fn+1e-9); sp=tn/(tn+fp+1e-9); j=se+sp-1
        if best is None or j>best[1]: best=(float(t),float(j))
    return best[0]
dd=dm.dropna(subset=['FadFisica']).copy(); dd['ev']=(dd.FadFisica>=dd.FadFisica.quantile(2/3)).astype(int)
PARAMS=[('PV','PV','low'),('dist','Distância','low'),('FCmax','FCmáx','high')]
ROWS={}; roc_data={}
for col,lab,dirn in PARAMS:
    d2=dd.dropna(subset=[col]).copy()
    score=-d2[col] if dirn=='low' else d2[col]
    A=auc(score,d2['ev']); cv=loo(col,d2.assign())
    b0,b1=logit(d2[col],d2['ev']); sd=d2[col].std(); OR=float(np.exp(b1*sd))
    p=float(stats.mannwhitneyu(d2[d2.ev==1][col],d2[d2.ev==0][col]).pvalue)
    thr=youden(d2[col],d2['ev'],low=(dirn=='low'))
    ROWS[col]=dict(lab=lab,auc=float(A),cv=cv,thr=float(thr),OR=OR,p=p)
    # ROC points
    ths=np.unique(score); tpr=[]; fpr=[]
    for t in np.sort(ths):
        pred=(score>=t).astype(int)
        tp=np.sum((pred==1)&(d2.ev==1)); fn=np.sum((pred==0)&(d2.ev==1)); tn=np.sum((pred==0)&(d2.ev==0)); fp=np.sum((pred==1)&(d2.ev==0))
        tpr.append(tp/(tp+fn+1e-9)); fpr.append(fp/(fp+tn+1e-9))
    roc_data[col]=(list(fpr),list(tpr))
json.dump({k:v for k,v in ROWS.items()},open('tcar1_model.json','w'),indent=1)
print('T-CAR 1 modeling (high fatigue):')
for c,v in ROWS.items(): print('  %-9s AUC=%.2f CV=%.2f thr=%.1f OR=%.2f p=%.3f'%(v['lab'],v['auc'],v['cv'],v['thr'],v['OR'],v['p']))

# ---- Figura 17: ROC curves (apparent) ----
f=go.Figure()
cols={'PV':'#2b8a3e','dist':'#1c7ed6','FCmax':'#e8590c'}
for col,lab,_ in PARAMS:
    fpr,tpr=roc_data[col]; order=np.argsort(fpr); fpr=np.array(fpr)[order]; tpr=np.array(tpr)[order]
    f.add_trace(go.Scatter(x=fpr,y=tpr,mode='lines',line=dict(color=cols[col],width=3),name='%s (AUC %.2f)'%(ROWS[col]['lab'],ROWS[col]['auc'])))
f.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(color='#adb5bd',dash='dash'),showlegend=False))
f.update_layout(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    height=560,width=720,xaxis_title='1 − especificidade',yaxis_title='Sensibilidade',legend=dict(x=0.4,y=0.15,font=dict(size=12)),margin=dict(l=60,r=25,t=40,b=55))
f.write_image(f'{OUT}/x_fig17.png',width=1200,height=760,scale=2)
# ---- Figura 18: apparent vs LOOCV ----
labs=[ROWS[c]['lab'] for c,_,_ in PARAMS]; ap=[ROWS[c]['auc'] for c,_,_ in PARAMS]; cv=[ROWS[c]['cv'] for c,_,_ in PARAMS]
g=go.Figure()
g.add_trace(go.Bar(x=labs,y=ap,name='AUC aparente',marker_color='#4c6ef5',text=['%.2f'%v for v in ap],textposition='outside'))
g.add_trace(go.Bar(x=labs,y=cv,name='AUC validada (LOOCV)',marker_color='#adb5bd',text=['%.2f'%v for v in cv],textposition='outside'))
g.add_hline(y=0.5,line=dict(color='#868e96',dash='dot'))
g.update_layout(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    height=560,width=900,barmode='group',yaxis_title='AUC',yaxis=dict(range=[0,1]),legend=dict(orientation='h',y=1.1,x=0.3),margin=dict(l=60,r=25,t=45,b=45))
g.write_image(f'{OUT}/x_fig18.png',width=1300,height=720,scale=2)
print('figs x_fig17, x_fig18 OK')
