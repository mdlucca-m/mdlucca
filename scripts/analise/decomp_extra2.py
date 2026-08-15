import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
import plotly.graph_objects as go
from plotly.subplots import make_subplots
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])].copy()
CORE=[('Vigor','Vigor'),('Fadiga','Fadiga BRUMS'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD')]
CV={'Vigor':'#2b8a3e','Fadiga':'#c92a2a','FadFisica':'#d9480f','FadMental':'#6741d9','TMD':'#0b7285'}
days=np.arange(1,8); D={}
def daily(v): return h2.dropna(subset=[v]).groupby(['ID','dia'])[v].mean().reset_index()

# 1) 3-facet + 2) slopes + 3) ACF + 4) RCI
facet={}; slope={}; acf={}; rci={}; islopes={}
for v,lab in CORE:
    d=h2.dropna(subset=[v]).copy()
    m=smf.mixedlm(f'{v} ~ 1', d, groups=d['ID'], re_formula='1', vc_formula={'dia':'0+C(dia)'}).fit(reml=True)
    va=float(m.cov_re.iloc[0,0]); vd=float(m.vcomp[0]) if len(m.vcomp) else 0.0; ve=float(m.scale); tot=va+vd+ve
    facet[v]=dict(lab=lab,ptrait=100*va/tot,pstate=100*vd/tot,pnoise=100*ve/tot,icc1=va/tot,phi=va/(va+vd/7+ve/14))
    try:
        ms=smf.mixedlm(f'{v} ~ dia', d, groups=d['ID'], re_formula='~dia').fit(reml=True)
        slope[v]=dict(mean=float(ms.fe_params['dia']),sd=float(np.sqrt(ms.cov_re.loc['dia','dia'])))
    except Exception: slope[v]=dict(mean=None,sd=None)
    mod=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit(); d['res']=mod.resid; etm=np.sqrt(anova_lm(mod,typ=1).loc['Residual','mean_sq'])
    acs=[]
    for aid,g in d.groupby('ID'):
        g=g.sort_values(['dia','momento']); r=g['res'].values
        if len(r)>3: acs.append(np.corrcoef(r[:-1],r[1:])[0,1])
    acf[v]=float(np.nanmean(acs))
    w=daily(v).pivot(index='ID',columns='dia',values=v); ch=(w[7]-w[1]).dropna()
    r_=ch/(np.sqrt(2)*etm); rci[v]=dict(etm=float(etm),mdc=float(1.96*np.sqrt(2)*etm),pct=float(100*(r_.abs()>1.96).mean()))
    # per-athlete slopes for the box figure
    sl=[]
    for aid,g in daily(v).groupby('ID'):
        if g['dia'].nunique()>=3: sl.append(float(stats.linregress(g['dia'],g[v]).slope))
    islopes[v]=sl
# 5) PCA
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']; Z=h2[SUB].dropna(); Zs=(Z-Z.mean())/Z.std()
ev=np.sort(np.linalg.eigvalsh(np.corrcoef(Zs.T.values)))[::-1]; pv=(100*ev/ev.sum()).tolist()
D=dict(facet=facet,slope=slope,acf=acf,rci=rci,pca=pv)
json.dump(D,open(f'{SC}/decomp_extra.json','w'),indent=1)

def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=16,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=55,b=60)); b.update(k); return b
def save(f,n): f.write_image(f'{OUT}/{n}.png',width=1600,height=900,scale=2)
xs=[l for _,l in CORE]
# G: 3-facet stacked
f=go.Figure()
f.add_trace(go.Bar(x=xs,y=[facet[v]['pstate'] for v,_ in CORE],name='Estado (dia) — sinal do microciclo',marker_color='#c92a2a'))
f.add_trace(go.Bar(x=xs,y=[facet[v]['ptrait'] for v,_ in CORE],name='Traço (entre atletas)',marker_color='#1c7ed6'))
f.add_trace(go.Bar(x=xs,y=[facet[v]['pnoise'] for v,_ in CORE],name='Ruído (intra-dia / erro)',marker_color='#adb5bd'))
f.update_layout(**T(height=560,barmode='stack',legend=dict(orientation='h',y=-0.2)),yaxis_title='% da variância'); save(f,'x_facet')
# G: PCA variance explained
f=go.Figure()
f.add_trace(go.Bar(x=[f'PC{i+1}' for i in range(6)],y=pv,marker_color='#0b7285',name='variância'))
f.add_trace(go.Scatter(x=[f'PC{i+1}' for i in range(6)],y=np.cumsum(pv),mode='lines+markers',name='acumulada',line=dict(color='#c92a2a',width=3),yaxis='y'))
f.update_layout(**T(height=520,legend=dict(orientation='h',y=-0.18)),yaxis_title='% da variância'); save(f,'x_pca')
# F: individual slopes box (heterogeneidade do declínio)
f=go.Figure()
for v,lab in CORE:
    f.add_trace(go.Box(y=islopes[v],name=lab,marker_color=CV[v],line=dict(color=CV[v]),boxpoints='all',pointpos=0,jitter=0.4,marker=dict(size=5,opacity=.5)))
f.add_hline(y=0,line=dict(color='#111',width=1,dash='dot'))
f.update_layout(**T(height=560,showlegend=False),yaxis_title='Inclinação individual (unid./dia)'); save(f,'x_slopes')

print('DECOMP EXTRA salvo. Resumo:')
for v,lab in CORE:
    print('  %-15s traço=%.0f%% estado=%.0f%% ruído=%.0f%% Phi=%.2f | slopeSD=%.2f ACF1=%+.2f RCI%%=%.0f'%(lab,facet[v]['ptrait'],facet[v]['pstate'],facet[v]['pnoise'],facet[v]['phi'],(slope[v]['sd'] or 0),acf[v],rci[v]['pct']))
print('  PCA:',['%.0f%%'%x for x in pv[:4]])
