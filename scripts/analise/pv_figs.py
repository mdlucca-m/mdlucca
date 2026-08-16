import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
WK=pd.read_csv('pv_wk.csv'); PS=json.load(open('pv_stats.json'))
HEX={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#6741d9','FadFisica':'#0c8599'}
RGBA={'Vigor':'rgba(47,158,68,.15)','Fadiga':'rgba(232,89,12,.15)','TMD':'rgba(103,65,217,.14)','FadFisica':'rgba(12,133,153,.15)'}
NM={'Vigor':'Vigor (BRUMS)','Fadiga':'Fadiga (BRUMS)','TMD':'PTH','FadFisica':'Fadiga física'}
def base(**k):
    b=dict(template='plotly_white',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=52,b=50)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
thr=14.9  # T-CAR1 Youden threshold
def regband(ax,x,y,col):
    m=pd.DataFrame({'x':x,'y':y}).dropna(); xx=m.x.values; yy=m.y.values
    lr=stats.linregress(xx,yy); rho,pr=stats.spearmanr(xx,yy)
    xs=np.linspace(xx.min(),xx.max(),50); ys=lr.intercept+lr.slope*xs
    n=len(xx); dof=n-2; tval=stats.t.ppf(0.975,dof); sx=xx.std(ddof=1)
    se=np.sqrt(np.sum((yy-(lr.intercept+lr.slope*xx))**2)/dof)*np.sqrt(1/n+(xs-xx.mean())**2/((n-1)*sx**2))
    up=ys+tval*se; lo=ys-tval*se
    return xs,ys,up,lo,lr,rho,pr

# ===== 2x2 scatter+regression: T-CAR1 vs Vigor/Fadiga/TMD/FadFisica =====
cols=['Vigor','Fadiga','TMD','FadFisica']
f=make_subplots(rows=2,cols=2,vertical_spacing=0.14,horizontal_spacing=0.11,
    subplot_titles=['<b>%s</b>'%NM[c] for c in cols])
for i,c in enumerate(cols):
    r,cc=divmod(i,2); r+=1; cc+=1
    xs,ys,up,lo,lr,rho,pr=regband(None,WK.PVini,WK[c],c)
    f.add_trace(go.Scatter(x=list(xs)+list(xs[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor=RGBA[c],mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'),r,cc)
    f.add_trace(go.Scatter(x=WK.PVini,y=WK[c],mode='markers',marker=dict(color=HEX[c],size=9,opacity=0.75,line=dict(color='white',width=1)),showlegend=False),r,cc)
    f.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color=HEX[c],width=3),showlegend=False),r,cc)
    f.add_vline(x=thr,line=dict(color='#adb5bd',dash='dash',width=1.5),row=r,col=cc)
    txt='ρ = %s · R² = %s · p = %s'%(('%+.2f'%rho).replace('.',','),('%.2f'%lr.rvalue**2).replace('.',','),(('%.3f'%pr).replace('.',',') if pr>=0.001 else '< 0,001'))
    f.add_annotation(x=WK.PVini.max(),y=WK[c].max(),xref='x%d'%(i+1),yref='y%d'%(i+1),text=txt,showarrow=False,xanchor='right',font=dict(size=12,color='#333'))
    f.update_xaxes(title='T-CAR1 – pico de velocidade (km/h)' if r==2 else '',row=r,col=cc,**GRID)
    f.update_yaxes(title='Escore',row=r,col=cc,**GRID)
f.update_layout(**base(height=760,width=1200))
f.write_image(f'{OUT}/pv7_scatter.png',width=1300,height=820,scale=3)

# ===== terciles bar: weekly fatigue (BRUMS + physical) by fitness tercile =====
terc=PS['terc']; order=['Baixa','Média','Alta']
f=go.Figure()
f.add_trace(go.Bar(x=order,y=[terc[k]['Fadiga'] for k in order],name='Fadiga (BRUMS)',marker=dict(color='#e8590c',line=dict(color='white',width=1))))
f.add_trace(go.Bar(x=order,y=[terc[k]['FadFisica'] for k in order],name='Fadiga física',marker=dict(color='#0c8599',line=dict(color='white',width=1))))
f.update_layout(**base(height=520,width=920,barmode='group',title=dict(text='<b>Fadiga semanal por tercil de aptidão (T-CAR1)</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=1.1,x=0.5,xanchor='center',font=dict(size=13))))
f.update_yaxes(title='Escore médio semanal',**GRID); f.update_xaxes(title='Tercil de pico de velocidade',**GRID)
f.write_image(f'{OUT}/pv8_tercis.png',width=1000,height=560,scale=3)

# ===== single highlighted scatter: T-CAR1 vs physical fatigue w/ threshold =====
c='FadFisica'
xs,ys,up,lo,lr,rho,pr=regband(None,WK.PVini,WK[c],c)
f=go.Figure()
f.add_vrect(x0=WK.PVini.min()-0.2,x1=thr,fillcolor='#e8590c',opacity=0.05,line_width=0,annotation_text='Menor aptidão (≤ %.1f km/h)'%thr,annotation_position='top left',annotation_font_size=12)
f.add_trace(go.Scatter(x=list(xs)+list(xs[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor=RGBA[c],mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'))
f.add_trace(go.Scatter(x=WK.PVini,y=WK[c],mode='markers',marker=dict(color=HEX[c],size=12,opacity=0.8,line=dict(color='white',width=1.2)),showlegend=False))
f.add_trace(go.Scatter(x=xs,y=ys,mode='lines',line=dict(color=HEX[c],width=3.5),showlegend=False))
f.add_vline(x=thr,line=dict(color='#495057',dash='dash',width=2))
f.add_annotation(x=WK.PVini.max(),y=WK[c].max(),text='ρ = %s · R² = %s · p = %s'%(('%+.2f'%rho).replace('.',','),('%.2f'%lr.rvalue**2).replace('.',','),('%.3f'%pr).replace('.',',')),showarrow=False,xanchor='right',font=dict(size=14,color='#333'))
f.update_layout(**base(height=560,width=1000,title=dict(text='<b>Aptidão intermitente (T-CAR1) e fadiga física semanal</b>',x=0.5,font=dict(size=17))))
f.update_xaxes(title='T-CAR1 – pico de velocidade (km/h)',**GRID); f.update_yaxes(title='Fadiga física (escore semanal)',**GRID)
f.write_image(f'{OUT}/pv9_limiar.png',width=1100,height=620,scale=3)
print('PV figs OK: pv7_scatter, pv8_tercis, pv9_limiar')
