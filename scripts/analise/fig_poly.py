import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
COLS={'V':'Vigor','F':'Fadiga','P':'TMD'}
VARS=[('V','Vigor','#2f9e44'),('F','Fadiga','#e8590c'),('P','Perturbação total do humor (PTH)','#7048e8')]

# ---- 7 pontos: medias diarias (dia 1..7, agrupando todos os momentos do dia) ----
dm=h.dropna(subset=['dia']).groupby('dia').agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
x7=dm.dia.values.astype(float)
# ---- 14 pontos: linha de base do dia 1 (pre/pos) + medias pre/pos dos dias 2-7 ----
g=h.dropna(subset=['dia']).groupby(['dia','momento']).agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
p14=[]
b1=g[(g.dia==1)&(g.momento=='baseline')]
if len(b1):
    for off in (-0.2,0.2): p14.append((1+off,float(b1.V.iloc[0]),float(b1.F.iloc[0]),float(b1.P.iloc[0])))
for d in range(2,8):
    for mo,off in [('pre',-0.2),('pos',0.2)]:
        rr=g[(g.dia==d)&(g.momento==mo)]
        if len(rr): p14.append((d+off,float(rr.V.iloc[0]),float(rr.F.iloc[0]),float(rr.P.iloc[0])))
P14=pd.DataFrame(p14,columns=['x','V','F','P']).sort_values('x'); x14=P14.x.values

def cnum(v,d=2): return ('%+.*f'%(d,v)).replace('.',',')
def fit3(x,y):
    a,b,c,d=np.polyfit(x,y,3)
    yhat=np.polyval([a,b,c,d],x)
    r2=1-np.sum((y-yhat)**2)/np.sum((y-y.mean())**2)
    xi=-b/(3*a); yi=float(np.polyval([a,b,c,d],xi))
    return dict(a=float(a),b=float(b),c=float(c),d=float(d),r2=float(r2),infl=float(xi),yinfl=yi)

RES={}
xx=np.linspace(0.8,7.2,400)
f=make_subplots(rows=3,cols=1,vertical_spacing=0.10,subplot_titles=['<b>%s</b>'%lab for _,lab,_ in VARS])
for i,(k,lab,col) in enumerate(VARS):
    r=i+1
    y7=dm[k].values; y14=P14[k].values
    F7=fit3(x7,y7); F14=fit3(x14,y14); RES[k]={'d7':F7,'d14':F14}
    yc7=np.polyval([F7['a'],F7['b'],F7['c'],F7['d']],xx)
    yc14=np.polyval([F14['a'],F14['b'],F14['c'],F14['d']],xx)
    allv=np.r_[y7,y14,yc7,yc14]; ylo,yhi=allv.min(),allv.max(); pad=(yhi-ylo)*0.30+0.8
    xi=F7['infl']
    if 0.8<xi<7.2:
        f.add_vrect(x0=0.8,x1=xi,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below',row=r,col=1)
        f.add_vrect(x0=xi,x1=7.2,fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below',row=r,col=1)
        f.add_vline(x=xi,line=dict(color='#212529',width=2,dash='dot'),row=r,col=1)
        f.add_trace(go.Scatter(x=[xi],y=[F7['yinfl']],mode='markers',
            marker=dict(size=15,color='#212529',line=dict(color='white',width=2)),showlegend=False),r,1)
        f.add_annotation(x=xi,y=yhi+pad*0.30,text='<b>inflexão (diária) · dia %.1f</b>'%xi,showarrow=False,
            font=dict(size=11,color='#212529'),bgcolor='rgba(255,255,255,0.85)',bordercolor='#212529',borderwidth=1,borderpad=3,row=r,col=1)
    # pontos pre/pos (14) e sua curva tracejada
    f.add_trace(go.Scatter(x=x14,y=y14,mode='markers',marker=dict(size=7,color=col,opacity=0.30,line=dict(color='white',width=0.6)),
        name='Pré/pós (14 pontos)',showlegend=(i==0),legendgroup='p14'),r,1)
    f.add_trace(go.Scatter(x=xx,y=yc14,mode='lines',line=dict(color=col,width=3.4,dash='dash'),
        name='Polinômio · pré/pós',showlegend=(i==0),legendgroup='c14'),r,1)
    # medias diarias (7) e sua curva cheia
    f.add_trace(go.Scatter(x=x7,y=y7,mode='markers',marker=dict(size=12,color=col,symbol='square',line=dict(color='white',width=1.4)),
        name='Média diária (7 pontos)',showlegend=(i==0),legendgroup='p7'),r,1)
    f.add_trace(go.Scatter(x=xx,y=yc7,mode='lines',line=dict(color=col,width=7),
        name='Polinômio · diária',showlegend=(i==0),legendgroup='c7'),r,1)
    # caixa de resultados
    eq='y = %sx³ %sx² %sx %s'%(cnum(F7['a'],3),cnum(F7['b'],2),cnum(F7['c'],2),cnum(F7['d'],2))
    txt=('<b>Diária (7 pts): %s</b><br>R² = %s   |   inflexão (y″=0): dia %.1f<br>'
         'Pré/pós (14 pts): R² = %s   |   inflexão: dia %.1f')%(
         eq,('%.2f'%F7['r2']).replace('.',','),F7['infl'],('%.2f'%F14['r2']).replace('.',','),F14['infl'])
    f.add_annotation(x=0.015,y=0.03,xref='x domain',yref='y domain',text=txt,showarrow=False,
        xanchor='left',yanchor='bottom',align='left',font=dict(size=11,color='#212529'),
        bgcolor='rgba(255,255,255,0.88)',bordercolor=col,borderwidth=1.4,borderpad=5,row=r,col=1)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],showgrid=False,zeroline=False,row=r,col=1)
    f.update_xaxes(title='Dia do microciclo' if i==2 else '',range=[0.6,7.4],dtick=1,
        showgrid=False,zeroline=False,showticklabels=(i==2),row=r,col=1)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=24,t=66,b=48),
    legend=dict(orientation='h',y=1.10,x=0.5,xanchor='center',font=dict(size=11),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/poly_fit.png',width=1560,height=1240,scale=3)
json.dump(RES,open('poly_fit.json','w'),ensure_ascii=False,indent=1)
print('OK poly_fit.png')
for k in RES: print(' ',k,'| 7pts R2=%.3f infl=%.2f | 14pts R2=%.3f infl=%.2f'%(
    RES[k]['d7']['r2'],RES[k]['d7']['infl'],RES[k]['d14']['r2'],RES[k]['d14']['infl']))
