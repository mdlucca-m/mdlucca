import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
from scipy import stats
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
SC='.'
hum=pd.read_csv('hum_prof.csv'); h2=hum[hum.momento.isin(['pre','pos'])]
days=np.arange(1,8)
def daily(df,v,idc='ID'): return df.dropna(subset=[v]).groupby([idc,'dia'])[v].mean().reset_index()

# ================= A) OUTROS QUESTIONÁRIOS =================
W={}
# Epworth & PSS (anonimizado em hum_prof)
for v,lab,rng in [('Epworth','Sonolência (Epworth)','0–24'),('PSS','Estresse (PSS)','')]:
    d=daily(h2,v).pivot(index='ID',columns='dia',values=v)
    dm=d.mean(); a=d[1].dropna(); b=d[7].dropna(); c=a.index.intersection(b.index); a,b=a.loc[c],b.loc[c]; diff=b-a
    dz=diff.mean()/diff.std(); p=stats.wilcoxon(a,b).pvalue if diff.std()>0 else np.nan
    rho_fad=stats.spearmanr(h2[v],h2['FadFisica'],nan_policy='omit').correlation
    lr=stats.linregress(days,dm.reindex(days).values)
    W[v]=dict(lab=lab,d1=float(a.mean()),d7=float(b.mean()),dz=float(dz),p=float(p),slope=float(lr.slope),r2=float(lr.rvalue**2),
        p_slope=float(lr.pvalue),rho_fad=float(rho_fad),daymean=[float(x) for x in dm.reindex(days).values])
# TQR (wellness_all, nível de grupo — sem nomes na saída)
wl=pd.read_csv('wellness_all.csv'); wl['datadia']=pd.to_datetime(wl['datadia'],errors='coerce')
win=wl[(wl.datadia>='2024-04-21')&(wl.datadia<='2024-04-28')].copy(); win['dia']=win.datadia.dt.day-20
tq=win.dropna(subset=['TQR'])
dm=tq.groupby('dia')['TQR'].mean().reindex(days)
lr=stats.linregress(tq['dia'],tq['TQR'])
rho_fad=stats.spearmanr(tq['TQR'],tq['FadFisica'],nan_policy='omit').correlation
rho_vig=stats.spearmanr(tq['TQR'],tq['Vigor'],nan_policy='omit').correlation
d1=tq[tq.dia==1]['TQR']; d7=tq[tq.dia==7]['TQR']
W['TQR']=dict(lab='Recuperação (TQR)',d1=float(d1.mean()),d7=float(d7.mean()),slope=float(lr.slope),r2=float(lr.rvalue**2),
    p_slope=float(lr.pvalue),rho_fad=float(rho_fad),rho_vig=float(rho_vig),daymean=[float(x) for x in dm.values],
    mw_p=float(stats.mannwhitneyu(d1,d7).pvalue))
json.dump(W,open('wellness.json','w'),indent=1)
print('QUESTIONÁRIOS (janela):')
for k in ['TQR','Epworth','PSS']:
    w=W[k]; print('  %-22s D1=%.1f D7=%.1f | b/dia=%+.3f (p=%.3f) | ρ×fadiga=%+.2f'%(w['lab'],w['d1'],w['d7'],w['slope'],w['p_slope'],w['rho_fad']))

# ================= B) BAYESIANO / EQUIVALÊNCIA =================
def bf10_paired(x,y):  # Wagenmakers (2007) BIC approximation
    d=(y-x).dropna(); n=len(d); t=d.mean()/(d.std()/np.sqrt(n))
    bf01=np.sqrt(n)*(1+t**2/(n-1))**(-n/2); return 1/bf01, float(t), n
def tost(x,y,sesoi_sd):  # equivalence within ±sesoi (in SD units) via TOST
    d=(y-x).dropna(); n=len(d); m=d.mean(); se=d.std()/np.sqrt(n); bound=sesoi_sd*d.std()
    t1=(m-(-bound))/se; t2=(m-bound)/se
    p1=stats.t.sf(t1,n-1); p2=stats.t.cdf(t2,n-1); return float(max(p1,p2))  # equivalence p = max of the two one-sided
VARS=[('Vigor','Vigor'),('Fadiga','Fadiga (BRUMS)'),('FadFisica','Fadiga física'),('FadMental','Fadiga mental'),('TMD','PTH/TMD'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
BZ={}
print('\nBAYESIANO / EQUIVALÊNCIA (D1→D7, agregado por atleta; ROPE ±0,2 DP):')
print('%-15s %10s %8s %10s'%('Variável','BF10','p_TOST','veredito'))
for v,lab in VARS:
    d=daily(h2,v).pivot(index='ID',columns='dia',values=v); a=d[1]; b=d[7]; c=a.dropna().index.intersection(b.dropna().index)
    bf,t,n=bf10_paired(a.loc[c],b.loc[c]); pt=tost(a.loc[c],b.loc[c],0.2)
    verd='efeito' if bf>3 else ('equivalência/nulo' if (bf<1/3 or pt<0.05) else 'indeterminado')
    BZ[v]=dict(lab=lab,bf10=float(bf),tost_p=float(pt),verd=verd)
    print('%-15s %10.2f %8.3f  %s'%(lab,bf,pt,verd))
json.dump(BZ,open('bayes.json','w'),indent=1)

# ============ FIGURES ============
import plotly.graph_objects as go
from plotly.subplots import make_subplots
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=65,r=25,t=55,b=60)); b.update(k); return b
OUT='/home/user/mdlucca/Artigos/figuras'
# questionnaires trajectory
f=make_subplots(rows=1,cols=3,subplot_titles=['Recuperação (TQR)','Sonolência (Epworth)','Estresse (PSS)'],horizontal_spacing=0.09)
for j,(k,col) in enumerate([('TQR','#2b8a3e'),('Epworth','#e8590c'),('PSS','#6741d9')],1):
    f.add_trace(go.Scatter(x=days,y=W[k]['daymean'],mode='lines+markers',line=dict(color=col,width=3),marker=dict(size=8),showlegend=False),1,j)
    lr=stats.linregress(days,W[k]['daymean']); f.add_trace(go.Scatter(x=np.array([1,7]),y=lr.intercept+lr.slope*np.array([1,7]),mode='lines',line=dict(color='#111',width=1.5,dash='dash'),showlegend=False),1,j)
f.update_layout(**T(height=460)); f.update_xaxes(dtick=1,title='Dia'); f.write_image(f'{OUT}/x_wellness.png',width=1600,height=560,scale=2)
# bayes factor bar (log scale)
f=go.Figure(); labs=[BZ[v]['lab'] for v,_ in VARS]; bfs=[BZ[v]['bf10'] for v,_ in VARS]
cols=['#2b8a3e' if b>3 else ('#c92a2a' if b<1/3 else '#adb5bd') for b in bfs]
f.add_trace(go.Bar(x=labs,y=bfs,marker_color=cols,showlegend=False))
f.add_hline(y=3,line=dict(color='#2b8a3e',dash='dot')); f.add_hline(y=1/3,line=dict(color='#c92a2a',dash='dot'))
f.update_layout(**T(height=520,yaxis_type='log'),yaxis_title='Fator de Bayes BF₁₀ (escala log)',xaxis_tickangle=-25)
f.write_image(f'{OUT}/x_bayes.png',width=1600,height=760,scale=2)
print('\nfigs OK: x_wellness, x_bayes')
