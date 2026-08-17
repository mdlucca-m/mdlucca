import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
rsa=pd.read_csv('rsa_anon.csv'); phys=pd.read_csv('phys.csv')[['ID','massa']]
h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PVini']]
wk=h.groupby('ID').agg(FadFisica=('FadFisica','mean')).reset_index()
M=wk.merge(rsa,on='ID').merge(phys,on='ID').merge(F,on='ID').dropna()

def panel(f,col,xv,xlab,color,title,c):
    d=M[[xv,'FadFisica']].dropna(); x=d[xv].values; y=d.FadFisica.values
    lr=stats.linregress(x,y); xx=np.linspace(x.min(),x.max(),100); yy=lr.intercept+lr.slope*xx
    n=len(x); se=np.sqrt(np.sum((y-(lr.intercept+lr.slope*x))**2)/(n-2)); sxx=np.sum((x-x.mean())**2)
    ci=1.96*se*np.sqrt(1/n+(xx-x.mean())**2/sxx)
    rgba=color.replace('rgb','rgba').replace(')',',0.14)') if color.startswith('rgb') else 'rgba(120,120,120,0.14)'
    f.add_trace(go.Scatter(x=np.r_[xx,xx[::-1]],y=np.r_[yy+ci,(yy-ci)[::-1]],fill='toself',fillcolor=rgba,line=dict(width=0),showlegend=False,hoverinfo='skip'),1,c)
    f.add_trace(go.Scatter(x=xx,y=yy,mode='lines',line=dict(color=color,width=5),showlegend=False),1,c)
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=11,color=color,opacity=0.8,line=dict(color='white',width=1.3)),showlegend=False),1,c)
    rho,pv=stats.spearmanr(x,y)
    ax='x domain' if c==1 else 'x%d domain'%c; ay='y domain' if c==1 else 'y%d domain'%c
    f.add_annotation(x=0.04,y=0.055,xref=ax,yref=ay,showarrow=False,xanchor='left',
        text='ρ = %s · R² = %s · p = %s'%(('%+.2f'%rho).replace('.',','),('%.2f'%rho**2).replace('.',','),('%.3f'%pv).replace('.',',')),
        font=dict(size=13,color='#1a1a1a'),bgcolor='rgba(255,255,255,0.82)')
    f.update_xaxes(title=xlab,gridcolor='#eceef1',zeroline=False,row=1,col=c)
    f.update_yaxes(title='Fadiga física semanal (0–10)',gridcolor='#eceef1',zeroline=False,row=1,col=c)

f=make_subplots(rows=1,cols=2,horizontal_spacing=0.11,
    subplot_titles=['<b>Capacidade anaeróbia (RSA — melhor tempo)</b>','<b>Aptidão aeróbia (PV do T-CAR)</b>'])
panel(f,1,'BkMel','Melhor tempo em sprints repetidos (s) — menor = melhor','#e8590c','',1)
panel(f,1,'PVini','Pico de velocidade — T-CAR (km/h) — maior = melhor','#2f9e44','',2)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=56,b=58))
f.write_image(f'{OUT}/rsa_especificidade.png',width=1560,height=600,scale=3)
print('OK rsa_especificidade.png')
