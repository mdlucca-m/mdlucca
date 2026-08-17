import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); R=json.load(open('brums_desc2.json'))
days=np.arange(1,8)
PAL={'Vigor':('#2f9e44','rgba(47,158,68,0.16)'),'Fadiga':('#e8590c','rgba(232,89,12,0.16)'),
     'TMD':('#6741d9','rgba(103,65,217,0.15)'),'Tensao':('#1971c2','rgba(25,113,194,0.15)'),
     'Depressao':('#9c36b5','rgba(156,54,181,0.15)'),'Raiva':('#e03131','rgba(224,49,49,0.15)'),
     'Confusao':('#f08c00','rgba(240,140,0,0.15)')}
NM={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
def base(**k):
    b=dict(template='plotly_white',font=dict(color='#1a1a1a',size=16,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
        margin=dict(l=64,r=24,t=54,b=54)); b.update(k); return b
def band(f,x,y,se,key,row,col,legend=True):
    col_,fill=PAL[key]; up=np.array(y)+1.96*np.array(se); lo=np.array(y)-1.96*np.array(se)
    f.add_trace(go.Scatter(x=list(x)+list(x[::-1]),y=list(up)+list(lo[::-1]),fill='toself',fillcolor=fill,mode='lines',line=dict(width=0),showlegend=False,hoverinfo='skip'),row,col)
    f.add_trace(go.Scatter(x=x,y=y,mode='lines+markers',line=dict(color=col_,width=3.6),marker=dict(size=9,color=col_,line=dict(color='white',width=1.5)),name=NM[key],showlegend=legend),row,col)
def dstat(k):
    m=h.groupby('dia')[k].mean().reindex(days).values; se=h.groupby('dia')[k].sem().reindex(days).values; return m,se
GRID=dict(gridcolor='#eceef1',zeroline=False)

# ============ FIG 1: ORGANOGRAMA (didático, com sombras) ============
f=go.Figure()
def sbox(x0,x1,y0,y1,fill,line,title,sub=''):
    # sombra
    f.add_shape(type='rect',x0=x0+0.008,x1=x1+0.008,y0=y0-0.012,y1=y1-0.012,fillcolor='rgba(0,0,0,0.13)',line=dict(width=0),layer='below')
    f.add_shape(type='rect',x0=x0,x1=x1,y0=y0,y1=y1,fillcolor=fill,line=dict(color=line,width=2.2))
    yc=(y0+y1)/2
    f.add_annotation(x=(x0+x1)/2,y=yc+(0.018 if sub else 0),text='<b>%s</b>'%title,showarrow=False,font=dict(size=16,color='#1a1a1a'))
    if sub: f.add_annotation(x=(x0+x1)/2,y=yc-0.028,text=sub,showarrow=False,font=dict(size=12.5,color='#495057'))
def arrow(x0,y0,x1,y1):
    f.add_annotation(x=x1,y=y1,ax=x0,ay=y0,xref='x',yref='y',axref='x',ayref='y',showarrow=True,arrowhead=2,arrowsize=1.3,arrowwidth=2.2,arrowcolor='#868e96')
sbox(0.28,0.72,0.90,1.00,'#e7f5ff','#1971c2','27 atletas de handebol de elite','Masculino · Armadores, Pontas, Pivôs, Goleiros')
arrow(0.5,0.90,0.5,0.83)
sbox(0.20,0.80,0.72,0.82,'#e7f5ff','#1971c2','Microciclo pré-competitivo · 7 dias (21–27/04/2024)','Três sessões de HIIT (22, 24 e 27/04)')
arrow(0.5,0.72,0.5,0.65)
sbox(0.14,0.86,0.54,0.64,'#e6fcf5','#0ca678','2 coletas por dia de treino','PRÉ (antes do treino) e PÓS (após o treino)')
# split arrows to pre/pos illustrative
arrow(0.5,0.54,0.5,0.47)
sbox(0.24,0.76,0.36,0.46,'#e6fcf5','#0ca678','456 observações válidas do BRUMS-24','24 adjetivos · escala 0–4')
arrow(0.5,0.36,0.5,0.29)
sbox(0.16,0.84,0.18,0.28,'#f3f0ff','#7048e8','6 subescalas (0–16) + Perturbação Total do Humor (PTH)','Tensão · Depressão · Raiva · Vigor · Fadiga · Confusão')
arrow(0.5,0.18,0.5,0.11)
sbox(0.22,0.78,0.00,0.10,'#f3f0ff','#7048e8','Classificação nos 6 perfis de humor de Terry','Iceberg · Everest inv. · Iceberg inv. · Submerso · Barbatana · Superfície')
f.update_xaxes(visible=False,range=[0,1]); f.update_yaxes(visible=False,range=[-0.02,1.02])
f.update_layout(**base(height=940,width=980,margin=dict(l=8,r=8,t=14,b=8)))
f.write_image(f'{OUT}/xb2_framework.png',width=1100,height=1060,scale=3)

# ============ FIG 2: TRAJETÓRIAS com bandas (energia-fadiga + negativas) ============
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.10,subplot_titles=['<b>A) Eixo energia–fadiga</b>','<b>B) Subescalas negativas</b>'])
for k in ['Vigor','Fadiga','TMD']:
    m,se=dstat(k); band(f,days,m,se,k,1,1)
for k in ['Tensao','Depressao','Raiva','Confusao']:
    m,se=dstat(k); band(f,days,m,se,k,1,2)
f.update_xaxes(title='Dia',dtick=1,**GRID); f.update_yaxes(title='Escore',row=1,col=1,**GRID); f.update_yaxes(title='Escore (0–16)',row=1,col=2,**GRID)
f.update_layout(**base(height=560,width=1440,legend=dict(font=dict(size=13),orientation='v')))
f.write_image(f'{OUT}/xb2_traj.png',width=1500,height=600,scale=3)

# ============ FIG 3: NEGATIVAS detalhadas (Depressão, Raiva, Confusão) com D1/D7 ============
f=make_subplots(rows=1,cols=3,horizontal_spacing=0.075,subplot_titles=['<b>Depressão</b>','<b>Raiva</b>','<b>Confusão</b>'])
for j,k in enumerate(['Depressao','Raiva','Confusao'],1):
    m,se=dstat(k); band(f,days,m,se,k,1,j,legend=False)
    # highlight D1 e D7
    for dd,txt,cc in [(1,'D1 (+vigor)','#2f9e44'),(7,'D7 (+fadiga)','#e8590c')]:
        f.add_vrect(x0=dd-0.25,x1=dd+0.25,fillcolor=cc,opacity=0.10,line_width=0,row=1,col=j)
    f.update_xaxes(title='Dia',dtick=1,row=1,col=j,**GRID)
f.update_yaxes(title='Escore (0–16)',row=1,col=1,**GRID)
f.update_layout(**base(height=470,width=1440))
f.write_image(f'{OUT}/xb2_negatives.png',width=1500,height=500,scale=3)

# ============ FIG 4: HEATMAP correlação (traço) ============
LAB=R['corr_labels']; M=np.array(R['corr_trait'])
f=go.Figure(go.Heatmap(z=M,x=LAB,y=LAB,colorscale='RdBu',zmid=0,zmin=-1,zmax=1,
    text=[['%+.2f'%v for v in row] for row in M],texttemplate='%{text}',textfont=dict(size=15),
    colorbar=dict(title='ρ',thickness=16)))
f.update_layout(**base(height=620,width=720,margin=dict(l=90,r=30,t=40,b=60)))
f.update_yaxes(autorange='reversed')
f.write_image(f'{OUT}/xb2_heatmap.png',width=820,height=720,scale=3)

# ============ FIG 5: CORRELAÇÃO FOCO — negativas × fadiga em D1 vs D7 + por dia ============
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.12,subplot_titles=['<b>A) ρ (negativa × fadiga): dia de +vigor (D1) vs +fadiga (D7)</b>','<b>B) Acoplamento negativa–fadiga por dia</b>'])
negs=['Depressao','Raiva','Confusao']; labs=[NM[k] for k in negs]
d1=[R['focus']['D1'][k]['rho_fad'] for k in negs]; d7=[R['focus']['D7'][k]['rho_fad'] for k in negs]
f.add_trace(go.Bar(x=labs,y=d1,name='D1 (maior vigor)',marker=dict(color='#69db7c',line=dict(color='#2f9e44',width=1.5)),text=['%+.2f'%v for v in d1],textposition='outside'),1,1)
f.add_trace(go.Bar(x=labs,y=d7,name='D7 (maior fadiga)',marker=dict(color='#ff8787',line=dict(color='#e03131',width=1.5)),text=['%+.2f'%v for v in d7],textposition='outside'),1,1)
f.update_yaxes(title='ρ com fadiga',range=[-0.4,0.95],row=1,col=1,**GRID)
for k in negs:
    y=[R['perday_corr'][k]['fad'][str(d)] for d in days]
    f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers',name=NM[k],line=dict(color=PAL[k][0],width=3),marker=dict(size=8)),1,2)
f.add_hline(y=0,line=dict(color='#adb5bd'),row=1,col=2)
f.update_xaxes(title='Dia',dtick=1,row=1,col=2,**GRID); f.update_yaxes(title='ρ (negativa × fadiga)',row=1,col=2,**GRID)
f.update_layout(**base(height=520,width=1440,barmode='group',legend=dict(font=dict(size=12))))
f.write_image(f'{OUT}/xb2_corrfocus.png',width=1500,height=560,scale=3)

# ============ FIG 6: INTRA-DIA pré/pós (energia-fadiga + negativas) ============
f=make_subplots(rows=1,cols=4,horizontal_spacing=0.055,subplot_titles=['<b>Vigor</b>','<b>Fadiga</b>','<b>PTH</b>','<b>Negativas (Δ pós−pré)</b>'])
for j,k in enumerate(['Vigor','Fadiga','TMD'],1):
    pre=[R['byday'][k][str(d)]['pre'] for d in days]; pos=[R['byday'][k][str(d)]['pos'] for d in days]
    f.add_trace(go.Bar(x=days,y=pre,name='pré',marker=dict(color='#a5d8ff',line=dict(color='#1971c2',width=1)),showlegend=(j==1)),1,j)
    f.add_trace(go.Bar(x=days,y=pos,name='pós',marker=dict(color='#ffc078',line=dict(color='#e8590c',width=1)),showlegend=(j==1)),1,j)
    f.update_xaxes(title='Dia',dtick=1,row=1,col=j,**GRID)
for k in ['Depressao','Raiva','Confusao']:
    dd=R['intraday_neg'][k]; y=[(dd[str(d)]['delta'] if dd.get(str(d)) and dd[str(d)]['delta'] is not None else None) for d in days]
    f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers',name=NM[k],line=dict(color=PAL[k][0],width=2.6),marker=dict(size=7)),1,4)
f.add_hline(y=0,line=dict(color='#adb5bd'),row=1,col=4)
f.update_xaxes(title='Dia',dtick=1,row=1,col=4,**GRID); f.update_yaxes(title='Escore',row=1,col=1,**GRID)
f.update_layout(**base(height=470,width=1500,barmode='group',legend=dict(orientation='h',y=1.14,x=0.35)))
f.write_image(f'{OUT}/xb2_intraday.png',width=1560,height=500,scale=3)

# ============ FIG 7: PERFIS empilhados (restyle) ============
PROF=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
COLS=['#2f9e44','#4dabf7','#845ef7','#adb5bd','#e03131','#ffa94d']
recs=[('D1 (linha de base)','D1'),('Semana','overall'),('D7 (último dia)','D7'),('Pré','pre'),('Pós','pos')]
f=go.Figure()
for p,c in zip(PROF,COLS):
    ys=[R['profiles'][key][p] for _,key in recs]
    f.add_trace(go.Bar(x=[l for l,_ in recs],y=ys,name=p.replace('Barbatana tubarão','Barbatana de tubarão'),marker=dict(color=c,line=dict(color='white',width=1.2)),
        text=['%d%%'%v if v>=6 else '' for v in ys],textposition='inside',insidetextfont=dict(color='white',size=13)))
f.update_layout(**base(height=600,width=1160,barmode='stack',yaxis_title='% de observações',legend=dict(font=dict(size=12))))
f.update_yaxes(**GRID)
f.write_image(f'{OUT}/xb2_profiles.png',width=1300,height=660,scale=3)
print('all figs OK')
