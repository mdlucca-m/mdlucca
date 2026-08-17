import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); S4=json.load(open('brums_stats4.json'))
days=np.arange(1,8)
HEX={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#6741d9','Tensao':'#1971c2','Depressao':'#9c36b5','Raiva':'#e03131','Confusao':'#f08c00'}
RGBA={'Vigor':'rgba(47,158,68,.18)','Fadiga':'rgba(232,89,12,.18)','TMD':'rgba(103,65,217,.16)','Tensao':'rgba(25,113,194,.16)','Depressao':'rgba(156,54,181,.16)','Raiva':'rgba(224,49,49,.16)','Confusao':'rgba(240,140,0,.16)'}
NM={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
def base(**k):
    b=dict(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=50,b=48)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
wk=h.groupby('ID')[list(HEX)].mean()
def dstat(k): return h.groupby('dia')[k].mean().reindex(days).values, h.groupby('dia')[k].sem().reindex(days).values

# ===== 1) SCATTER MATRIX (dispersão) 6 subescalas =====
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
f=go.Figure(go.Splom(dimensions=[dict(label=NM[k],values=wk[k]) for k in SUB],
    marker=dict(color='#1c7ed6',size=6,opacity=0.7,line=dict(color='white',width=0.5)),diagonal=dict(visible=False),showupperhalf=False))
f.update_layout(**base(height=900,width=980,margin=dict(l=70,r=20,t=30,b=40)))
f.write_image(f'{OUT}/xb4_splom.png',width=1080,height=1000,scale=3)

# ===== 2) BIG all-variables by day (z-standardized) =====
f=go.Figure()
ORD=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao','TMD']
for k in ORD:
    mu=h[k].mean(); sd=h[k].std(ddof=1); z=(h.groupby('dia')[k].mean().reindex(days)-mu)/sd
    dash='solid' if k in ('Vigor','Fadiga','TMD') else 'dot'
    wid=4 if k in ('Vigor','Fadiga') else (3 if k=='TMD' else 2.4)
    f.add_trace(go.Scatter(x=days,y=z.values,mode='lines+markers',name=NM[k],line=dict(color=HEX[k],width=wid,dash=dash),marker=dict(size=8,line=dict(color='white',width=1))))
f.add_hline(y=0,line=dict(color='#adb5bd',dash='dash'))
f.add_vrect(x0=0.6,x1=1.4,fillcolor='#2f9e44',opacity=0.06,line_width=0,annotation_text='D1 (+vigor)',annotation_position='top left',annotation_font_size=12)
f.add_vrect(x0=6.6,x1=7.4,fillcolor='#e8590c',opacity=0.06,line_width=0,annotation_text='D7 (+fadiga)',annotation_position='top right',annotation_font_size=12)
f.update_layout(**base(height=620,width=1500,legend=dict(orientation='h',y=1.09,x=0.5,xanchor='center',font=dict(size=13))))
f.update_xaxes(title='Dia do microciclo',dtick=1,**GRID); f.update_yaxes(title='Escore padronizado (z)',**GRID)
f.write_image(f'{OUT}/xb4_allz.png',width=1600,height=680,scale=3)

# ===== 3) DUMBBELL D1 vs D7 all variables =====
D=json.load(open('brums_desc2.json'))['d1d7']
f=go.Figure(); ordd=sorted(ORD,key=lambda k:D[k]['d1'])
for k in ordd:
    d1=D[k]['d1']; d7=D[k]['d7']
    f.add_trace(go.Scatter(x=[d1,d7],y=[NM[k],NM[k]],mode='lines',line=dict(color='#ced4da',width=5),showlegend=False))
    f.add_trace(go.Scatter(x=[d1],y=[NM[k]],mode='markers',marker=dict(color='#4dabf7',size=15,line=dict(color='#1971c2',width=1.5)),showlegend=False))
    f.add_trace(go.Scatter(x=[d7],y=[NM[k]],mode='markers',marker=dict(color='#ff922b',size=15,line=dict(color='#e8590c',width=1.5)),showlegend=False))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(color='#4dabf7',size=13),name='Dia 1'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(color='#ff922b',size=13),name='Dia 7'))
f.update_layout(**base(height=520,width=1100,legend=dict(font=dict(size=13),x=0.8,y=0.1)))
f.update_xaxes(title='Escore',**GRID); f.update_yaxes(**GRID)
f.write_image(f'{OUT}/xb4_dumbbell.png',width=1200,height=560,scale=3)

# ===== 4) SIX per-variable figures (shaded band + box per day + effect) =====
for k in SUB:
    m,se=dstat(k)
    f=go.Figure()
    up=m+1.96*se; lo=m-1.96*se
    f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor=RGBA[k],mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'))
    for d in days:
        yv=h[h.dia==d][k].dropna()
        f.add_trace(go.Box(x=[d]*len(yv),y=yv,marker=dict(color=HEX[k],size=3),line=dict(width=1),fillcolor=RGBA[k],opacity=0.5,boxpoints='outliers',showlegend=False,width=0.5))
    f.add_trace(go.Scatter(x=days,y=m,mode='lines+markers',line=dict(color=HEX[k],width=4),marker=dict(size=10,line=dict(color='white',width=1.5)),showlegend=False))
    dz=S4['sens'][k]['dz']; fr=S4['friedman'][k]
    f.add_annotation(x=1,y=max(up)*1.02,xanchor='left',showarrow=False,font=dict(size=13,color='#333'),
        text='Δ D1→D7: dz = %s · Friedman p = %s'%(('%+.2f'%dz).replace('.',','),(('%.3f'%fr['p']).replace('.',','))))
    f.update_layout(**base(height=470,width=900,title=dict(text='<b>%s</b>'%NM[k],x=0.5,font=dict(size=18))))
    f.update_xaxes(title='Dia',dtick=1,**GRID); f.update_yaxes(title='Escore (0–16)',**GRID)
    f.write_image(f'{OUT}/xb4_v_{k}.png',width=1000,height=520,scale=3)

# ===== 5) INDIVIDUAL spaghetti (Vigor, Fadiga) =====
dm=pd.read_csv('brums_daily.csv')
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.09,subplot_titles=['<b>Vigor — trajetória individual</b>','<b>Fadiga — trajetória individual</b>'])
for j,k in enumerate(['Vigor','Fadiga'],1):
    for aid,g in dm.groupby('ID'):
        gg=g.set_index('dia')[k].reindex(days)
        f.add_trace(go.Scatter(x=days,y=gg.values,mode='lines',line=dict(color='#adb5bd',width=1),opacity=0.5,showlegend=False),1,j)
    m=dm.groupby('dia')[k].mean().reindex(days)
    f.add_trace(go.Scatter(x=days,y=m.values,mode='lines+markers',line=dict(color=HEX[k],width=4.5),marker=dict(size=9,line=dict(color='white',width=1.5)),name='Média do grupo',showlegend=(j==1)),1,j)
    f.update_xaxes(title='Dia',dtick=1,row=1,col=j,**GRID); f.update_yaxes(title='Escore (0–16)',row=1,col=j,**GRID)
f.update_layout(**base(height=520,width=1400,legend=dict(font=dict(size=12),y=1.08,x=0.5,orientation='h')))
f.write_image(f'{OUT}/xb4_spaghetti.png',width=1500,height=560,scale=3)
print('all figs OK: splom, allz, dumbbell, 6x per-var, spaghetti')
