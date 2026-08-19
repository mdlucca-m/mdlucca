import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
# ----- 12 pontos pre/pos (dias 2-7), ordenados; x em unidades de dia (pre=d-0.2, pos=d+0.2) -----
g=h.dropna(subset=['dia']).groupby(['dia','momento']).agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
pts=[]
for d in range(2,8):
    for mo,off in [('pre',-0.2),('pos',0.2)]:
        row=g[(g.dia==d)&(g.momento==mo)]
        if len(row): pts.append((d+off,d,mo,float(row.V.iloc[0]),float(row.F.iloc[0]),float(row.P.iloc[0])))
D=pd.DataFrame(pts,columns=['x','dia','mo','V','F','P'])
x=D.x.values
VARS=[('V','Vigor','#2f9e44'),('F','Fadiga','#e8590c'),('P','Perturbação total do humor (PTH)','#7048e8')]
xx=np.linspace(x.min(),x.max(),400)
RES={}
f=make_subplots(rows=3,cols=1,vertical_spacing=0.09,
    subplot_titles=['<b>%s</b>'%lab for _,lab,_ in VARS])
for i,(k,lab,col) in enumerate(VARS):
    r=i+1; y=D[k].values
    # suavizacao: spline quartica com fator de suavizacao (remove ruido); 2a derivada suave
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85)
    ys=s(xx); d2=s.derivative(2)(xx)
    # pontos de inflexao = zeros da 2a derivada (mudanca de sinal)
    sign=np.sign(d2); idx=np.where(np.diff(sign)!=0)[0]
    infl=[float(xx[j]) for j in idx]
    RES[k]={'infl':infl,'ymin_x':float(xx[np.argmin(ys)]),'ymin':float(ys.min()),
            'ymax_x':float(xx[np.argmax(ys)]),'ymax':float(ys.max())}
    ylo,yhi=min(y.min(),ys.min()),max(y.max(),ys.max()); pad=(yhi-ylo)*0.18+0.5
    # fases sombreadas: inicio (dias 2-4) vs acumulo (dias 5-7)
    f.add_vrect(x0=x.min(),x1=4.5,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below',row=r,col=1)
    f.add_vrect(x0=4.5,x1=x.max(),fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below',row=r,col=1)
    if r==1:
        f.add_annotation(x=3.1,y=yhi+pad*0.55,text='início',showarrow=False,font=dict(size=11,color='#1864ab'),row=r,col=1)
        f.add_annotation(x=6.2,y=yhi+pad*0.55,text='acúmulo',showarrow=False,font=dict(size=11,color='#c0410b'),row=r,col=1)
    # sinal bruto (ruidoso) = marcadores finos
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=9,color=col,opacity=0.45,
        line=dict(color='white',width=1)),name='Sinal bruto (12 pontos)',showlegend=(r==1),
        legendgroup='raw'),r,1)
    # curva suavizada (sinal) = linha grossa tematica
    f.add_trace(go.Scatter(x=xx,y=ys,mode='lines',line=dict(color=col,width=6),
        name='Curva suavizada (sinal)',showlegend=(r==1),legendgroup='sm'),r,1)
    # pontos de inflexao (limites da 2a derivada)
    for j,xi in enumerate(infl):
        f.add_vline(x=xi,line=dict(color='#212529',width=2,dash='dot'),row=r,col=1)
        f.add_annotation(x=xi,y=yhi+pad*0.15,text='inflexão<br>dia %.1f'%xi,showarrow=False,
            font=dict(size=9.5,color='#212529'),row=r,col=1)
    # min e max sinalizados
    f.add_trace(go.Scatter(x=[RES[k]['ymax_x']],y=[RES[k]['ymax']],mode='markers',
        marker=dict(symbol='triangle-up',size=13,color=col,line=dict(color='white',width=1.5)),
        showlegend=False),r,1)
    f.add_trace(go.Scatter(x=[RES[k]['ymin_x']],y=[RES[k]['ymin']],mode='markers',
        marker=dict(symbol='triangle-down',size=13,color=col,line=dict(color='white',width=1.5)),
        showlegend=False),r,1)
    f.add_annotation(x=RES[k]['ymax_x'],y=RES[k]['ymax'],text='máx',showarrow=True,arrowhead=0,ax=0,ay=-16,
        font=dict(size=9,color=col),row=r,col=1)
    f.add_annotation(x=RES[k]['ymin_x'],y=RES[k]['ymin'],text='mín',showarrow=True,arrowhead=0,ax=0,ay=16,
        font=dict(size=9,color=col),row=r,col=1)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],showgrid=False,zeroline=False,row=r,col=1)
    f.update_xaxes(title='Dia do microciclo' if r==3 else '',range=[x.min()-0.2,x.max()+0.2],
        dtick=1,showgrid=False,zeroline=False,row=r,col=1)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=58,r=20,t=58,b=48),
    legend=dict(orientation='h',y=1.10,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.6)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/smooth_deriv.png',width=1560,height=1000,scale=3)
json.dump(RES,open('smooth_deriv.json','w'),ensure_ascii=False,indent=1)
print('OK smooth_deriv.png | inflexões:',{k:[round(v,2) for v in RES[k]['infl']] for k in RES})
