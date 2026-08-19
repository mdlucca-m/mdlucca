import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.interpolate import UnivariateSpline
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); ADV=json.load(open('adv.json'))
seq=[(1,'baseline',1.0)]
for d in range(2,8): seq+=[(d,'pre',d-0.2),(d,'pos',d+0.2)]
x=np.array([xx for _,_,xx in seq]); xd=np.linspace(x.min(),x.max(),400)
def cm(k): return np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m,_ in seq])
VARS=[('Vigor','Vigor','#2f9e44'),('Fadiga','Fadiga','#e8590c'),('TMD','PTH','#7048e8'),
      ('Tensao','Tensão','#1971c2'),('Depressao','Depressão','#9c36b5'),
      ('Raiva','Raiva','#e03131'),('Confusao','Confusão','#f08c00')]
f=make_subplots(rows=4,cols=2,vertical_spacing=0.085,horizontal_spacing=0.09,
    subplot_titles=[lab for _,lab,_ in VARS]+[''])
for i,(k,lab,col) in enumerate(VARS):
    r=i//2+1; c=i%2+1
    y=cm(k); s=UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85); ys=s(xd)
    d2=s.derivative(2)(xd); sign=np.sign(d2); idx=np.where(np.diff(sign)!=0)[0]
    sn=ADV['snr'][k]
    ylo=min(y.min(),ys.min()); yhi=max(y.max(),ys.max()); pad=(yhi-ylo)*0.30+0.4
    # sinal bruto (ruido) = marcadores; sinal suavizado = linha grossa
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=6,color=col,opacity=0.40,line=dict(color='white',width=0.6)),
        showlegend=False),r,c)
    f.add_trace(go.Scatter(x=xd,y=ys,mode='lines',line=dict(color=col,width=5),showlegend=False),r,c)
    # inflexoes
    for j in idx:
        f.add_vline(x=xd[j],line=dict(color='#212529',width=1.4,dash='dot'),row=r,col=c)
    # min/max
    f.add_trace(go.Scatter(x=[sn['ymax_x']],y=[sn['ymax']],mode='markers',marker=dict(symbol='triangle-up',size=10,color=col,line=dict(color='white',width=1)),showlegend=False),r,c)
    f.add_trace(go.Scatter(x=[sn['ymin_x']],y=[sn['ymin']],mode='markers',marker=dict(symbol='triangle-down',size=10,color=col,line=dict(color='white',width=1)),showlegend=False),r,c)
    # anotacao sinal/ruido e piso
    f.add_annotation(x=0.03,y=0.05,xref='x domain',yref='y domain',xanchor='left',yanchor='bottom',
        text='S/R = %.1f · piso %.0f%%'%(sn['snr_amp'],sn['floor0']),showarrow=False,
        font=dict(size=9.5,color='#495057'),bgcolor='rgba(255,255,255,0.82)',borderpad=2,row=r,col=c)
    f.update_yaxes(title='Escore' if c==1 else '',range=[ylo-pad*0.5,yhi+pad],showgrid=False,zeroline=False,row=r,col=c)
    f.update_xaxes(title='Dia' if r==4 else '',dtick=1,range=[x.min()-0.1,x.max()+0.1],showgrid=False,zeroline=False,
        showticklabels=(r==4 or i>=5),row=r,col=c)
# celula 8 vazia -> nota
f.add_annotation(x=0.5,y=0.5,xref='x8 domain' if False else 'paper',yref='paper',text='',showarrow=False)
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=13,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=58,r=22,t=44,b=44),showlegend=False)
# esconder eixos da 8a celula (r4c2)
f.update_xaxes(visible=False,row=4,col=2); f.update_yaxes(visible=False,row=4,col=2)
f.add_annotation(x=0.75,y=0.11,xref='paper',yref='paper',xanchor='center',align='left',
    text='<b>Marcadores</b>: sinal bruto (ruído)<br><b>Linha</b>: sinal suavizado<br>'
         '<b>▲/▼</b>: máximo/mínimo · <b>┊</b>: inflexão (2ª derivada nula)<br>'
         '<b>S/R</b>: razão sinal/ruído (amplitude) · <b>piso</b>: % de escores nulos',
    showarrow=False,font=dict(size=11,color='#343a40'),bgcolor='rgba(248,249,250,0.9)',bordercolor='#dee2e6',borderwidth=1,borderpad=6)
f.write_image(f'{OUT}/all_deriv.png',width=1500,height=1500,scale=3)
print('OK all_deriv.png')
