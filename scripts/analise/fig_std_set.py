import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); PHJ=json.load(open('posthoc.json'))
# ---------- padrão comum ----------
PAL={'V':'#2f9e44','F':'#e8590c','P':'#7048e8'}
LW=6; MK=9
def phases(f,r,x0,xmid,x1,yhi,pad,show):
    f.add_vrect(x0=x0,x1=xmid,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below',row=r,col=1)
    f.add_vrect(x0=xmid,x1=x1,fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below',row=r,col=1)
    if show:
        f.add_annotation(x=(x0+xmid)/2,y=yhi+pad*0.55,text='início',showarrow=False,font=dict(size=11,color='#1864ab'),row=r,col=1)
        f.add_annotation(x=(xmid+x1)/2,y=yhi+pad*0.55,text='acúmulo',showarrow=False,font=dict(size=11,color='#c0410b'),row=r,col=1)
def smooth(x,y,frac=0.85):
    s=UnivariateSpline(x,y,k=min(4,len(x)-1),s=len(x)*np.var(y)*frac)
    xx=np.linspace(x.min(),x.max(),300); return xx,s(xx),s
def sigmark(x,y,infl_line,f,r,col,yhi,pad):
    xm,ym=x[np.argmax(y)],y.max(); xn,yn=x[np.argmin(y)],y.min()
    f.add_trace(go.Scatter(x=[xm],y=[ym],mode='markers',marker=dict(symbol='triangle-up',size=13,color=col,line=dict(color='white',width=1.5)),showlegend=False),r,1)
    f.add_trace(go.Scatter(x=[xn],y=[yn],mode='markers',marker=dict(symbol='triangle-down',size=13,color=col,line=dict(color='white',width=1.5)),showlegend=False),r,1)
    f.add_annotation(x=xm,y=ym,text='máx',showarrow=True,arrowhead=0,ax=0,ay=-15,font=dict(size=9,color=col),row=r,col=1)
    f.add_annotation(x=xn,y=yn,text='mín',showarrow=True,arrowhead=0,ax=0,ay=15,font=dict(size=9,color=col),row=r,col=1)
    if infl_line is not None:
        f.add_vline(x=infl_line,line=dict(color='#212529',width=2,dash='dot'),row=r,col=1)
        f.add_annotation(x=infl_line,y=yhi+pad*0.15,text='inflexão',showarrow=False,font=dict(size=9.5,color='#212529'),row=r,col=1)
def baselay(f,ttl):
    f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=14,family='Arial'),
        paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=58,r=20,t=58,b=48),
        legend=dict(orientation='h',y=1.10,x=0.5,xanchor='center',font=dict(size=12),
            bgcolor='rgba(255,255,255,0.6)',bordercolor='#dee2e6',borderwidth=1))

VARS=[('V','Vigor','Vigor','#2f9e44'),('F','Fadiga','Fadiga','#e8590c'),('P','TMD','Perturbação total do humor (PTH)','#7048e8')]

# ================= 1) TRAJETÓRIA 7 DIAS (abnt_f1_trajetoria.png) =================
dd=h.dropna(subset=['dia']).groupby('dia').agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean'),
    Vs=('Vigor','sem'),Fs=('Fadiga','sem'),Ps=('TMD','sem')).reset_index()
x=dd.dia.values.astype(float)
f=make_subplots(rows=3,cols=1,vertical_spacing=0.09,subplot_titles=['<b>%s</b>'%lab for _,_,lab,_ in VARS])
for i,(k,col_,lab,col) in enumerate(VARS):
    r=i+1; y=dd[k].values; se=dd[k+'s'].values
    xx,ys,sp=smooth(x,y,0.85); d2=sp.derivative(2)(xx); sign=np.sign(d2); idx=np.where(np.diff(sign)!=0)[0]
    infl=float(xx[idx[0]]) if len(idx) else None
    ylo=min((y-1.96*se).min(),ys.min()); yhi=max((y+1.96*se).max(),ys.max()); pad=(yhi-ylo)*0.18+0.5
    phases(f,r,x.min(),4,x.max(),yhi,pad,r==1)
    f.add_trace(go.Scatter(x=np.r_[x,x[::-1]],y=np.r_[y+1.96*se,(y-1.96*se)[::-1]],fill='toself',mode='lines',
        fillcolor='rgba(120,120,120,0.10)',line=dict(width=0),showlegend=False,hoverinfo='skip'),r,1)
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=MK,color=col,opacity=0.5,line=dict(color='white',width=1)),
        name='Média diária',showlegend=(r==1),legendgroup='m'),r,1)
    f.add_trace(go.Scatter(x=xx,y=ys,mode='lines',line=dict(color=col,width=LW),name='Curva suavizada',showlegend=(r==1),legendgroup='s'),r,1)
    sigmark(xx,ys,infl,f,r,col,yhi,pad)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],gridcolor='#eceef1',zeroline=False,row=r,col=1)
    f.update_xaxes(title='Dia do microciclo' if r==3 else '',dtick=1,range=[0.8,7.2],gridcolor='#eceef1',zeroline=False,row=r,col=1)
baselay(f,'')
f.write_image(f'{OUT}/abnt_f1_trajetoria.png',width=1500,height=1180,scale=3)
print('OK abnt_f1_trajetoria.png (padrão)')

# ================= 2) PRÉ/PÓS POR DIA (abnt_f_prepos.png) =================
g=h.dropna(subset=['dia']).groupby(['dia','momento']).agg(V=('Vigor','mean'),F=('Fadiga','mean'),P=('TMD','mean')).reset_index()
f=make_subplots(rows=3,cols=1,vertical_spacing=0.09,subplot_titles=['<b>%s</b>'%lab for _,_,lab,_ in VARS])
for i,(k,col_,lab,col) in enumerate(VARS):
    r=i+1
    pre=g[g.momento=='pre'].sort_values('dia'); pos=g[g.momento=='pos'].sort_values('dia')
    allv=np.r_[pre[k].values,pos[k].values]; ylo,yhi=allv.min(),allv.max(); pad=(yhi-ylo)*0.2+0.5
    phases(f,r,1.5,4.5,7.5,yhi,pad,r==1)
    f.add_trace(go.Scatter(x=pre.dia,y=pre[k],mode='lines+markers',line=dict(color=col,width=LW-2,dash='dot'),
        marker=dict(size=MK,color='white',line=dict(color=col,width=2)),name='Pré-treino',showlegend=(r==1),legendgroup='pre'),r,1)
    f.add_trace(go.Scatter(x=pos.dia,y=pos[k],mode='lines+markers',line=dict(color=col,width=LW),
        marker=dict(size=MK,color=col,line=dict(color='white',width=1)),name='Pós-treino',showlegend=(r==1),legendgroup='pos'),r,1)
    f.update_yaxes(title='Escore',range=[ylo-pad*0.5,yhi+pad],gridcolor='#eceef1',zeroline=False,row=r,col=1)
    f.update_xaxes(title='Dia do microciclo' if r==3 else '',dtick=1,range=[1.5,7.5],gridcolor='#eceef1',zeroline=False,row=r,col=1)
baselay(f,'')
f.write_image(f'{OUT}/abnt_f_prepos.png',width=1500,height=1180,scale=3)
print('OK abnt_f_prepos.png (padrão)')

# ================= 3) MÉDIAS MARGINAIS vs DIA 1 (ph_emm.png) =================
PHV=[('Vigor','Vigor','#2f9e44'),('Fadiga','Fadiga','#e8590c'),('FadFisica','Fadiga física','#7048e8')]
f=go.Figure()
days=np.arange(1,8)
ally=[]
for k,lab,col in PHV:
    y=np.array([PHJ[k]['emm'][str(d)] for d in days]); ally.append(y)
ally=np.concatenate(ally); ylo,yhi=ally.min(),ally.max(); pad=(yhi-ylo)*0.16+0.4
f.add_vrect(x0=0.8,x1=4,fillcolor='#1971c2',opacity=0.05,line_width=0,layer='below')
f.add_vrect(x0=4,x1=7.2,fillcolor='#e8590c',opacity=0.06,line_width=0,layer='below')
f.add_annotation(x=2.4,y=yhi+pad*0.6,text='início',showarrow=False,font=dict(size=11,color='#1864ab'))
f.add_annotation(x=5.6,y=yhi+pad*0.6,text='acúmulo',showarrow=False,font=dict(size=11,color='#c0410b'))
for k,lab,col in PHV:
    y=np.array([PHJ[k]['emm'][str(d)] for d in days])
    f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers',line=dict(color=col,width=LW),
        marker=dict(size=MK,color=col,line=dict(color='white',width=1)),name=lab))
    # sinalizar dias que diferem do Dia 1
    for d in days[1:]:
        if PHJ[k]['pairs'].get('1_%d'%d,{}).get('ptukey',1)<0.05:
            f.add_annotation(x=d,y=y[d-1],text='*',showarrow=False,yshift=13,font=dict(size=17,color=col))
f.update_yaxes(title='Escore (média marginal estimada)',range=[ylo-pad*0.5,yhi+pad],gridcolor='#eceef1',zeroline=False)
f.update_xaxes(title='Dia do microciclo',dtick=1,range=[0.8,7.2],gridcolor='#eceef1',zeroline=False)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=52,b=50),legend=dict(orientation='h',y=1.10,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.6)',bordercolor='#dee2e6',borderwidth=1))
f.write_image(f'{OUT}/ph_emm.png',width=1500,height=760,scale=3)
print('OK ph_emm.png (padrão) | * = difere do Dia 1 (Tukey p<0,05)')
