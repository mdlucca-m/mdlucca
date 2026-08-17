import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('limiar2.json')); h=pd.read_csv('hum_prof.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PVini']]
t1,t2=R['t1'],R['t2']
GREEN='#2f9e44'; ORANGE='#e8590c'
Z=[('rgba(224,49,49,0.16)',None,t1),('rgba(250,176,5,0.17)',t1,t2),('rgba(47,158,68,0.16)',t2,None)]

f=make_subplots(rows=1,cols=2,horizontal_spacing=0.12,column_widths=[0.52,0.48],
    subplot_titles=['<b>Três faixas de aptidão pelo PV do T-CAR</b>','<b>Prevalência de dias críticos por faixa</b>'])

# ---- Painel A: pontos atleta-dia no eixo do PV, zonas sombreadas, dois limiares ----
base=h.groupby(['ID','dia']).agg(Fad=('FadFisica','mean'),Vig=('Vigor','mean')).reset_index().merge(F,on='ID').dropna(subset=['PVini'])
hi_fad=(base.Fad>=base.Fad.quantile(2/3)); rng=np.random.default_rng(2024)
xx=base.PVini.values; jit=rng.uniform(-0.32,0.32,len(xx))
xmin,xmax=xx.min()-0.15,xx.max()+0.15
for color,a,b in Z:
    f.add_vrect(x0=(a if a else xmin),x1=(b if b else xmax),fillcolor=color,line_width=0,row=1,col=1)
f.add_trace(go.Scatter(x=xx[~hi_fad],y=jit[~hi_fad],mode='markers',name='Dia normal',
    marker=dict(size=9,color='#adb5bd',opacity=0.7,line=dict(color='white',width=1)),showlegend=True),1,1)
f.add_trace(go.Scatter(x=xx[hi_fad],y=jit[hi_fad],mode='markers',name='Dia de fadiga elevada',
    marker=dict(size=10,color=ORANGE,opacity=0.85,line=dict(color='white',width=1)),showlegend=True),1,1)
for t in (t1,t2):
    f.add_vline(x=t,line=dict(color='#212529',width=3,dash='dash'),row=1,col=1)
    f.add_annotation(x=t,y=1.16,xref='x1',yref='paper',text='<b>%.1f</b>'%t,showarrow=False,font=dict(size=13,color='#212529'))
for lab,xc,col in [('Baixa',(xmin+t1)/2,'#e03131'),('Média',(t1+t2)/2,'#f08c00'),('Alta',(t2+xmax)/2,GREEN)]:
    f.add_annotation(x=xc,y=-0.62,xref='x1',yref='y1',text='<b>%s</b>'%lab,showarrow=False,font=dict(size=12,color=col))
f.update_xaxes(title='Pico de velocidade — T-CAR (km/h)',gridcolor='#eceef1',zeroline=False,row=1,col=1)
f.update_yaxes(showticklabels=False,range=[-0.8,0.8],zeroline=False,showgrid=False,row=1,col=1)

# ---- Painel B: barras de prevalência por faixa (fadiga vs baixo vigor) ----
labs=[b['lab'] for b in R['fadiga']['bands']]
f.add_trace(go.Bar(x=labs,y=[b['prev'] for b in R['fadiga']['bands']],name='Fadiga elevada',
    marker_color=ORANGE,text=[f"{b['prev']:.0f}%" for b in R['fadiga']['bands']],textposition='outside',
    textfont=dict(size=13),showlegend=True),1,2)
f.add_trace(go.Bar(x=labs,y=[b['prev'] for b in R['vigor']['bands']],name='Baixo vigor',
    marker_color='#1971c2',text=[f"{b['prev']:.0f}%" for b in R['vigor']['bands']],textposition='outside',
    textfont=dict(size=13),showlegend=True),1,2)
f.update_xaxes(title='Faixa de aptidão',gridcolor='#eceef1',row=1,col=2)
f.update_yaxes(title='Prevalência de dias críticos (%)',range=[0,62],gridcolor='#eceef1',zeroline=False,row=1,col=2)

f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=58,r=22,t=64,b=64),barmode='group',
    legend=dict(orientation='h',y=1.16,x=0.5,xanchor='center',font=dict(size=12)))
f.write_image(f'{OUT}/limiar2_faixas.png',width=1560,height=620,scale=3)
print('OK limiar2_faixas.png | t1=%.1f t2=%.1f'%(t1,t2))
