import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

def cnum(v,d=2):  # numero em portugues
    return ('%+.*f'%(d,v)).replace('.',',')
RES={}
f=make_subplots(rows=3,cols=1,vertical_spacing=0.10,
    subplot_titles=['<b>%s</b>'%lab for _,lab,_ in VARS])
for i,(k,lab,col) in enumerate(VARS):
    r=i+1; y=D[k].values
    a,b,c,d=np.polyfit(x,y,3)                 # ajuste cubico: y = a x^3 + b x^2 + c x + d
    yhat=np.polyval([a,b,c,d],x)
    ss_res=float(np.sum((y-yhat)**2)); ss_tot=float(np.sum((y-y.mean())**2))
    r2=1-ss_res/ss_tot
    yc=np.polyval([a,b,c,d],xx)
    xi=-b/(3*a)                               # inflexao analitica (y''=0): 6a x + 2b = 0
    yi=float(np.polyval([a,b,c,d],xi))
    RES[k]={'a':float(a),'b':float(b),'c':float(c),'d':float(d),'r2':float(r2),'infl':float(xi),'yinfl':yi}
    ylo,yhi=min(y.min(),yc.min()),max(y.max(),yc.max()); pad=(yhi-ylo)*0.30+0.8
    # fases separadas pela inflexao analitica
    if x.min()<xi<x.max():
        f.add_vrect(x0=x.min(),x1=xi,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below',row=r,col=1)
        f.add_vrect(x0=xi,x1=x.max(),fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below',row=r,col=1)
        f.add_vline(x=xi,line=dict(color='#212529',width=2,dash='dot'),row=r,col=1)
        f.add_trace(go.Scatter(x=[xi],y=[yi],mode='markers',
            marker=dict(size=15,color='#212529',line=dict(color='white',width=2)),showlegend=False),r,1)
        f.add_annotation(x=xi,y=yhi+pad*0.30,text='<b>inflexão · dia %.1f</b>'%xi,showarrow=False,
            font=dict(size=11,color='#212529'),bgcolor='rgba(255,255,255,0.85)',bordercolor='#212529',borderwidth=1,borderpad=3,row=r,col=1)
    # pontos observados
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=9,color=col,opacity=0.40,line=dict(color='white',width=1)),
        name='Média pré/pós (12 pontos)',showlegend=(i==0),legendgroup='raw'),r,1)
    # curva polinomial
    f.add_trace(go.Scatter(x=xx,y=yc,mode='lines',line=dict(color=col,width=7),
        name='Ajuste polinomial (grau 3)',showlegend=(i==0),legendgroup='poly'),r,1)
    # caixa de resultados (equacao + R2)
    eq=('y = %sx³ %sx² %sx %s'%(cnum(a,3),cnum(b,2),cnum(c,2),cnum(d,2)))
    txt='<b>%s</b><br>R² = %s   |   inflexão (y″=0): dia %.1f'%(eq,('%.2f'%r2).replace('.',','),xi)
    f.add_annotation(x=0.015,y=0.03,xref='x domain',yref='y domain',text=txt,showarrow=False,
        xanchor='left',yanchor='bottom',align='left',font=dict(size=11.5,color='#212529'),
        bgcolor='rgba(255,255,255,0.88)',bordercolor=col,borderwidth=1.4,borderpad=5,row=r,col=1)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],showgrid=False,zeroline=False,row=r,col=1)
    f.update_xaxes(title='Dia do microciclo' if i==2 else '',range=[x.min()-0.2,x.max()+0.2],dtick=1,
        showgrid=False,zeroline=False,showticklabels=(i==2),row=r,col=1)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=24,t=64,b=48),
    legend=dict(orientation='h',y=1.09,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/poly_fit.png',width=1560,height=1200,scale=3)
json.dump(RES,open('poly_fit.json','w'),ensure_ascii=False,indent=1)
print('OK poly_fit.png |',{k:{'R2':round(RES[k]['r2'],3),'infl':round(RES[k]['infl'],2)} for k in RES})
