import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
T=json.load(open('temporal.json'))
DIMS=T['dims']; KEYS=[k for k,_ in DIMS]; LABS=[l for _,l in DIMS]

# ===== 1) MAPA DE SIGNIFICÂNCIA: variáveis x transições (dz + *) =====
trans=T['trans']; tl=[t['lab'].replace(' → ','→').replace('D','') for t in trans]
tl=[t['lab'].replace('base','b').replace('pré','pr').replace('pós','po') for t in trans]
Z=np.array([[t['vars'][k]['dz'] for t in trans] for k in KEYS])
TX=[['%+.2f%s'%(t['vars'][k]['dz'],'*' if t['vars'][k]['sig'] else '') for t in trans] for k in KEYS]
tlab=[t['lab'] for t in trans]
f=go.Figure(go.Heatmap(z=Z,x=tlab,y=LABS,text=TX,texttemplate='%{text}',textfont=dict(size=10),
    colorscale='RdBu',zmid=0,zmin=-1,zmax=1,reversescale=True,
    colorbar=dict(title='dz',thickness=14,len=0.8)))
# marca colunas agudas vs recuperação
for i,t in enumerate(trans):
    f.add_annotation(x=i,y=len(KEYS)-0.35,xref='x',yref='y',yshift=18,text='A' if t['tipo']=='Agudo' else 'R',
        showarrow=False,font=dict(size=10,color='#e8590c' if t['tipo']=='Agudo' else '#1971c2'))
f.update_layout(template='mdpi',title=dict(text='<b>Mapa temporal: onde e quanto cada variável muda (dz por transição; * p<0,05; A=agudo, R=recuperação)</b>',x=0.5,font=dict(size=15)),
    font=dict(color='#1a1a1a',size=12,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=110,r=20,t=70,b=140))
f.update_xaxes(tickangle=-45,side='bottom',tickfont=dict(size=10)); f.update_yaxes(autorange='reversed')
f.write_image(f'{OUT}/temporal_map.png',width=1700,height=760,scale=3); print('OK temporal_map.png')

# ===== 2) EFEITO AGUDO vs CRÔNICO por variável =====
ac=T['agudo_cronico']
f=go.Figure()
f.add_trace(go.Bar(x=LABS,y=[ac[k]['agudo_medio'] for k in KEYS],name='Agudo (média intradia pré→pós)',marker_color='#e8590c'))
f.add_trace(go.Bar(x=LABS,y=[ac[k]['cronico_delta'] for k in KEYS],name='Crônico (D1→D7)',marker_color='#7048e8'))
for i,k in enumerate(KEYS):
    if ac[k]['cronico_sig']: f.add_annotation(x=LABS[i],y=ac[k]['cronico_delta'],text='*',showarrow=False,yshift=12 if ac[k]['cronico_delta']>0 else -14,font=dict(size=16,color='#7048e8'))
f.update_layout(template='mdpi',barmode='group',title=dict(text='<b>Efeito agudo (intradia) vs efeito crônico (D1→D7) por variável</b>',x=0.5,font=dict(size=15)),
    font=dict(color='#1a1a1a',size=13,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=56,b=90),
    legend=dict(orientation='h',y=-0.28,x=0.5,xanchor='center'))
f.update_yaxes(title='Mudança do escore',showgrid=False,zeroline=True,zerolinecolor='#adb5bd'); f.update_xaxes(showgrid=False,zeroline=False,tickangle=-30)
f.write_image(f'{OUT}/temporal_agudo_cronico.png',width=1500,height=740,scale=3); print('OK temporal_agudo_cronico.png')

# ===== 3) MAIS vs MENOS APTOS: deterioração D1->D7 por variável =====
st=T['estratificacao']
f=go.Figure()
f.add_trace(go.Bar(x=LABS,y=[st[k]['mais_aptos_delta'] for k in KEYS],name='Mais aptos (PV alto)',marker_color='#2f9e44'))
f.add_trace(go.Bar(x=LABS,y=[st[k]['menos_aptos_delta'] for k in KEYS],name='Menos aptos (PV baixo)',marker_color='#e03131'))
f.update_layout(template='mdpi',barmode='group',title=dict(text='<b>Deterioração D1→D7 por variável: mais vs menos aptos (nenhuma diferença significativa)</b>',x=0.5,font=dict(size=14.5)),
    font=dict(color='#1a1a1a',size=13,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=56,b=90),
    legend=dict(orientation='h',y=-0.28,x=0.5,xanchor='center'))
f.update_yaxes(title='Mudança D1→D7 (escore)',showgrid=False,zeroline=True,zerolinecolor='#adb5bd'); f.update_xaxes(showgrid=False,zeroline=False,tickangle=-30)
f.write_image(f'{OUT}/temporal_aptidao.png',width=1500,height=740,scale=3); print('OK temporal_aptidao.png')
