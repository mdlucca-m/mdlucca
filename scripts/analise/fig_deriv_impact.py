import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')
# ---- 12 pontos pre/pos (dias 2-7); x em unidades de dia (pre=d-0.2, pos=d+0.2) ----
g=h.dropna(subset=['dia']).groupby(['dia','momento']).agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
pts=[]
for d in range(2,8):
    for mo,off in [('pre',-0.2),('pos',0.2)]:
        row=g[(g.dia==d)&(g.momento==mo)]
        if len(row): pts.append((d+off,float(row.V.iloc[0]),float(row.F.iloc[0]),float(row.P.iloc[0])))
D=pd.DataFrame(pts,columns=['x','V','F','P']); x=D.x.values
xx=np.linspace(x.min(),x.max(),400)
VARS=[('V','Vigor','#2f9e44'),('F','Fadiga','#e8590c'),('P','Perturbação total do humor (PTH)','#7048e8')]

def hexa(hx,a):
    hx=hx.lstrip('#'); return 'rgba(%d,%d,%d,%.2f)'%(int(hx[0:2],16),int(hx[2:4],16),int(hx[4:6],16),a)
def capsule(f,r,xv,yv,text,color,yshift,xshift=0):
    f.add_annotation(x=xv,y=yv,text=text,showarrow=False,yshift=yshift,xshift=xshift,
        font=dict(size=12,color='white',family='Arial'),align='center',
        bgcolor=color,bordercolor='white',borderwidth=1.4,borderpad=4,row=r,col=1)

f=make_subplots(rows=6,cols=1,
    row_heights=[0.215,0.12,0.215,0.12,0.215,0.12],vertical_spacing=0.035,
    subplot_titles=['<b>%s</b>'%lab if lab else '' for lab in
        ['Vigor','','Fadiga','','Perturbação total do humor (PTH)','']])

for i,(k,lab,col) in enumerate(VARS):
    rs=2*i+1; rd=2*i+2                      # linha do sinal / linha da derivada
    y=D[k].values
    s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85)
    ys=s(xx); d1=s.derivative(1)(xx); d2=s.derivative(2)(xx)
    sign=np.sign(d2); zc=np.where(np.diff(sign)!=0)[0]
    infl=float(xx[zc[0]]) if len(zc) else None
    xmax,ymax=xx[np.argmax(ys)],ys.max(); xmin,ymin=xx[np.argmin(ys)],ys.min()
    # taxa de variacao mais intensa (extremo da 1a derivada)
    j=int(np.argmax(np.abs(d1))); rate=d1[j]; xrate=xx[j]
    ylo,yhi=min(y.min(),ys.min()),max(y.max(),ys.max()); pad=(yhi-ylo)*0.34+0.8

    # ---------- PAINEL DO SINAL ----------
    # fases separadas pela inflexao
    if infl is not None:
        f.add_vrect(x0=x.min(),x1=infl,fillcolor=hexa(col,0.05),line_width=0,layer='below',row=rs,col=1)
        f.add_vrect(x0=infl,x1=x.max(),fillcolor=hexa(col,0.12),line_width=0,layer='below',row=rs,col=1)
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=8,color=col,opacity=0.35,
        line=dict(color='white',width=1)),name='Sinal bruto (12 pontos)',showlegend=(i==0),legendgroup='raw'),rs,1)
    f.add_trace(go.Scatter(x=xx,y=ys,mode='lines',line=dict(color=col,width=7),
        name='Curva suavizada',showlegend=(i==0),legendgroup='sm'),rs,1)
    # extremos realcados em capsulas de valor
    f.add_trace(go.Scatter(x=[xmax],y=[ymax],mode='markers',marker=dict(symbol='triangle-up',size=15,color=col,line=dict(color='white',width=1.6)),showlegend=False),rs,1)
    f.add_trace(go.Scatter(x=[xmin],y=[ymin],mode='markers',marker=dict(symbol='triangle-down',size=15,color=col,line=dict(color='white',width=1.6)),showlegend=False),rs,1)
    capsule(f,rs,xmax,ymax,'máx %.1f · dia %.1f'%(ymax,xmax),col,30)
    capsule(f,rs,xmin,ymin,'mín %.1f · dia %.1f'%(ymin,xmin),col,-30)
    if infl is not None:
        f.add_vline(x=infl,line=dict(color='#212529',width=2,dash='dot'),row=rs,col=1)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.6,yhi+pad],showgrid=False,zeroline=False,row=rs,col=1)
    f.update_xaxes(range=[x.min()-0.2,x.max()+0.2],dtick=1,showgrid=False,zeroline=False,showticklabels=False,row=rs,col=1)

    # ---------- PAINEL DA 2a DERIVADA ----------
    f.add_trace(go.Scatter(x=xx,y=d2,mode='lines',line=dict(color=col,width=3.5),
        fill='tozeroy',fillcolor=hexa(col,0.20),
        name="2ª derivada (concavidade)",showlegend=(i==0),legendgroup='d2'),rd,1)
    f.add_hline(y=0,line=dict(color='#495057',width=1.4),row=rd,col=1)
    d2a=np.abs(d2).max()
    if infl is not None:
        f.add_vline(x=infl,line=dict(color='#212529',width=2,dash='dot'),row=rd,col=1)
        f.add_trace(go.Scatter(x=[infl],y=[0],mode='markers',
            marker=dict(size=15,color='#212529',line=dict(color='white',width=2),symbol='circle'),showlegend=False),rd,1)
        f.add_annotation(x=infl,y=d2a*0.62,text='<b>inflexão · dia %.1f</b><br>(d² = 0)'%infl,showarrow=False,
            font=dict(size=11,color='#212529'),bgcolor='rgba(255,255,255,0.85)',bordercolor='#212529',borderwidth=1,borderpad=3,row=rd,col=1)
    f.update_yaxes(title='d²',range=[-d2a*1.25,d2a*1.35],showgrid=False,zeroline=False,row=rd,col=1)
    f.update_xaxes(title='Dia do microciclo' if i==2 else '',range=[x.min()-0.2,x.max()+0.2],dtick=1,
        showgrid=False,zeroline=False,showticklabels=(i==2),row=rd,col=1)

f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=24,t=60,b=46),
    legend=dict(orientation='h',y=1.075,x=0.5,xanchor='center',font=dict(size=11.5),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/deriv_impact.png',width=1560,height=1500,scale=3)
print('OK deriv_impact.png | inflexoes:',
    {k:(round(float(UnivariateSpline(x,D[k].values,k=4,s=len(x)*np.var(D[k].values)*0.85)
        .derivative(2)(xx)[np.where(np.diff(np.sign(UnivariateSpline(x,D[k].values,k=4,s=len(x)*np.var(D[k].values)*0.85).derivative(2)(xx)))!=0)[0][0]]),2) if True else None) for k,_,_ in VARS})
