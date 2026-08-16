import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); E=json.load(open('extra.json'))
wk=h.groupby('ID')[['Vigor','Fadiga','TMD','FadFisica','Epworth','PSS']].mean()
def base(**k):
    b=dict(template='plotly_white',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=62,r=22,t=54,b=88)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
def band(x,y):
    m=pd.DataFrame({'x':x,'y':y}).dropna(); xx=m.x.values; yy=m.y.values
    lr=stats.linregress(xx,yy); xs=np.linspace(xx.min(),xx.max(),40); ys=lr.intercept+lr.slope*xs
    n=len(xx); dof=n-2; tv=stats.t.ppf(0.975,dof); sx=xx.std(ddof=1)
    se=np.sqrt(np.sum((yy-(lr.intercept+lr.slope*xx))**2)/dof)*np.sqrt(1/n+(xs-xx.mean())**2/((n-1)*sx**2))
    return xs,ys,ys+tv*se,ys-tv*se,lr

# ===== SONO/ESTRESSE: scatter Epworth x Fadiga + grupo sonolência =====
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.12,
    subplot_titles=['<b>Sonolência (Epworth) × Fadiga</b>','<b>Humor: sonolentos vs. não sonolentos</b>'])
xs,ys,up,lo,lr=band(wk.Epworth,wk.Fadiga)
f.add_trace(go.Scatter(x=list(xs)+list(xs[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor='rgba(232,89,12,.15)',mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'),1,1)
f.add_trace(go.Scatter(x=wk.Epworth,y=wk.Fadiga,mode='markers',marker=dict(color='#e8590c',size=10,opacity=0.8,line=dict(color='white',width=1)),showlegend=False),1,1)
f.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color='#e8590c',width=3),showlegend=False),1,1)
f.add_vline(x=10,line=dict(color='#495057',dash='dash',width=1.5),row=1,col=1)
ce=E['epw']['corr']['Fadiga']
f.add_annotation(x=wk.Epworth.max(),y=wk.Fadiga.max(),text='ρ = %s · p = %s'%(('%+.2f'%ce['rho']).replace('.',','),('%.3f'%ce['p']).replace('.',',')),showarrow=False,xanchor='right',font=dict(size=13),row=1,col=1)
# grouped bars sleepy vs not
labs=['Vigor','Fadiga','PTH','Fadiga física']; keys=['Vigor','Fadiga','TMD','FadFisica']
hi=[E['sleepy_cmp'][k]['hi'] for k in keys]; loo=[E['sleepy_cmp'][k]['lo'] for k in keys]
f.add_trace(go.Bar(x=labs,y=hi,name='Sonolentos (Epworth > 10)',marker_color='#9c36b5'),1,2)
f.add_trace(go.Bar(x=labs,y=loo,name='Não sonolentos',marker_color='#adb5bd'),1,2)
f.update_xaxes(title='Epworth (sonolência)',row=1,col=1,**GRID); f.update_yaxes(title='Fadiga (escore semanal)',row=1,col=1,**GRID)
f.update_yaxes(title='Escore semanal',row=1,col=2,**GRID); f.update_xaxes(row=1,col=2,**GRID)
f.update_layout(**base(height=560,width=1350,legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13))))
f.write_image(f'{OUT}/x_sono.png',width=1450,height=620,scale=3)

# ===== HIIT vs não-HIIT grouped bars =====
f=go.Figure()
hh=[E['hiit'][k]['hiit'] for k in keys]; nn=[E['hiit'][k]['nohiit'] for k in keys]
star=['*' if E['hiit'][k]['p']<0.05 else '' for k in keys]
f.add_trace(go.Bar(x=labs,y=hh,name='Dias com HIIT (D2, D4, D7)',marker_color='#e8590c',text=star,textposition='outside',textfont=dict(size=20)))
f.add_trace(go.Bar(x=labs,y=nn,name='Dias sem HIIT (D1, D3, D5, D6)',marker_color='#74c0fc'))
f.update_layout(**base(height=560,width=1080,barmode='group',title=dict(text='<b>Humor e fadiga: dias com vs. sem HIIT</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13))))
f.update_yaxes(title='Escore médio (por atleta)',**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/x_hiit.png',width=1180,height=620,scale=3)
print('OK: x_sono, x_hiit')
