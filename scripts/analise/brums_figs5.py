import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
T=json.load(open('tscore.json'))['profile']
# classic BRUMS mood-profile: x = 6 subscales, y = T-score, reference line at 50
ORD=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
NM={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão'}
def base(**k):
    b=dict(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=64,r=22,t=64,b=90)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
# ===== mood-profile D1 vs D7 (iceberg -> shark) =====
f=go.Figure()
f.add_hrect(y0=40,y1=60,fillcolor='#f1f3f5',opacity=0.5,line_width=0)
f.add_hline(y=50,line=dict(color='#868e96',dash='dash',width=1.5),annotation_text='Média populacional (T=50)',annotation_position='top left',annotation_font_size=11)
for name,col,mk in [('D1','#2f9e44','circle'),('D7','#e8590c','diamond')]:
    yv=[T[name][k] for k in ORD]
    f.add_trace(go.Scatter(x=[NM[k] for k in ORD],y=yv,mode='lines+markers',name='Dia %s'%name[1],
        line=dict(color=col,width=4),marker=dict(size=13,symbol=mk,line=dict(color='white',width=1.5))))
f.update_layout(**base(height=560,width=1050,title=dict(text='<b>Perfil de humor (escores T) — Dia 1 vs Dia 7</b>',x=0.5,font=dict(size=18)),
    legend=dict(orientation='h',y=-0.14,x=0.5,xanchor='center',font=dict(size=14))))
f.update_yaxes(title='Escore T (M = 50; DP = 10)',range=[38,62],dtick=5,**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/xb5_profile_d1d7.png',width=1150,height=620,scale=3)
# ===== mood-profile pre vs pos =====
f=go.Figure()
f.add_hrect(y0=40,y1=60,fillcolor='#f1f3f5',opacity=0.5,line_width=0)
f.add_hline(y=50,line=dict(color='#868e96',dash='dash',width=1.5))
for name,col,mk in [('Pre','#1971c2','circle'),('Pos','#e8590c','diamond')]:
    yv=[T[name][k] for k in ORD]
    f.add_trace(go.Scatter(x=[NM[k] for k in ORD],y=yv,mode='lines+markers',name=('Pré' if name=='Pre' else 'Pós'),
        line=dict(color=col,width=4),marker=dict(size=13,symbol=mk,line=dict(color='white',width=1.5))))
f.update_layout(**base(height=560,width=1050,title=dict(text='<b>Perfil de humor (escores T) — pré vs pós-treino</b>',x=0.5,font=dict(size=18)),
    legend=dict(orientation='h',y=-0.14,x=0.5,xanchor='center',font=dict(size=14))))
f.update_yaxes(title='Escore T (M = 50; DP = 10)',range=[38,62],dtick=5,**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/xb5_profile_prepos.png',width=1150,height=620,scale=3)
print('mood-profile figs OK: xb5_profile_d1d7, xb5_profile_prepos')

# ===== cluster prevalence D1 vs D7 grouped bar =====
import json as _j
MS=_j.load(open('model_stats.json'))
PROF=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
ABBR=['Iceberg','Everest inv.','Iceberg inv.','Submerso','Barbatana','Superfície']
d1=MS['prev']['D1']; d7=MS['prev']['D7']; n1=MS['prev']['n_d1']; n7=MS['prev']['n_d7']
p1=[100*d1[p]/n1 for p in PROF]; p7=[100*d7[p]/n7 for p in PROF]
f=go.Figure()
f.add_trace(go.Bar(x=ABBR,y=p1,name='Dia 1',marker=dict(color='#2f9e44',line=dict(color='white',width=1))))
f.add_trace(go.Bar(x=ABBR,y=p7,name='Dia 7',marker=dict(color='#e8590c',line=dict(color='white',width=1))))
f.update_layout(**base(height=540,width=1050,barmode='group',title=dict(text='<b>Prevalência dos perfis de humor — Dia 1 vs Dia 7</b>',x=0.5,font=dict(size=18)),
    legend=dict(orientation='h',y=1.08,x=0.5,xanchor='center',font=dict(size=14))))
f.update_yaxes(title='Prevalência (%)',**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/xb5_prev.png',width=1150,height=600,scale=3)
print('prevalence bar OK: xb5_prev')
