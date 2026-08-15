import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); R=json.load(open('brums_desc.json'))
days=np.arange(1,8)
def T(**k):
    b=dict(template='plotly_white',font=dict(color='#111',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=50,b=50)); b.update(k); return b

# ---- Fig framework (organograma) ----
f=go.Figure()
boxes=[('27 atletas de handebol\n(elite, masculino)',0.85,'#1c7ed6'),
       ('7 dias consecutivos\n21–27/04/2024 (pré-temporada)',0.70,'#1c7ed6'),
       ('2 coletas/dia: PRÉ e PÓS-treino',0.55,'#2b8a3e'),
       ('456 observações · BRUMS-24 (24 itens)',0.40,'#2b8a3e'),
       ('6 subescalas + Perturbação Total do Humor (PTH)',0.25,'#6741d9'),
       ('Classificação nos 6 perfis de humor de Terry',0.10,'#6741d9')]
for txt,y,col in boxes:
    f.add_shape(type='rect',x0=0.12,x1=0.88,y0=y-0.055,y1=y+0.055,line=dict(color=col,width=2),fillcolor=col,opacity=0.12)
    f.add_annotation(x=0.5,y=y,text=txt.replace('\n','<br>'),showarrow=False,font=dict(size=15,color='#111'))
for i in range(len(boxes)-1):
    y0=boxes[i][1]-0.055; y1=boxes[i+1][1]+0.055
    f.add_annotation(x=0.5,y=y1,ax=0.5,ay=y0,xref='x',yref='y',axref='x',ayref='y',showarrow=True,arrowhead=2,arrowsize=1.2,arrowwidth=2,arrowcolor='#495057')
f.update_xaxes(visible=False,range=[0,1]); f.update_yaxes(visible=False,range=[0,1])
f.update_layout(**T(height=760,width=780,margin=dict(l=10,r=10,t=20,b=10)))
f.write_image(f'{OUT}/xb_framework.png',width=900,height=880,scale=2)

# ---- Fig trajectories (2 panels: energy-fatigue axis + negatives) ----
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.10,subplot_titles=['A) Eixo energia–fadiga','B) Subescalas negativas'])
axis=[('Vigor','#2b8a3e'),('Fadiga','#e8590c'),('TMD','#6741d9')]
neg=[('Tensao','#1c7ed6'),('Depressao','#7048e8'),('Raiva','#e03131'),('Confusao','#f08c00')]
def dseries(k):
    return h.groupby('dia')[k].mean().reindex(days).values, h.groupby('dia')[k].sem().reindex(days).values
for k,c in axis:
    y,se=dseries(k); f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers',name=k.replace('TMD','PTH'),line=dict(color=c,width=3),marker=dict(size=7),error_y=dict(type='data',array=1.96*se,color=c,thickness=1)),1,1)
for k,c in neg:
    y,se=dseries(k); f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers',name=k.replace('Tensao','Tensão').replace('Depressao','Depressão').replace('Confusao','Confusão'),line=dict(color=c,width=2.5),marker=dict(size=6)),1,2)
f.update_xaxes(title='Dia',dtick=1); f.update_yaxes(title='Escore',row=1,col=1); f.update_yaxes(title='Escore (0–16)',row=1,col=2)
f.update_layout(**T(height=520,width=1400,legend=dict(font=dict(size=11))))
f.write_image(f'{OUT}/xb_traj.png',width=1500,height=560,scale=2)

# ---- Fig intra-day pré/pós per day (Vigor, Fadiga, TMD) ----
f=make_subplots(rows=1,cols=3,horizontal_spacing=0.07,subplot_titles=['Vigor','Fadiga','PTH/TMD'])
for j,k in enumerate(['Vigor','Fadiga','TMD'],1):
    pre=[R['byday'][k][str(d)]['pre'] for d in days]; pos=[R['byday'][k][str(d)]['pos'] for d in days]
    f.add_trace(go.Bar(x=days,y=pre,name='pré',marker_color='#74c0fc',showlegend=(j==1)),1,j)
    f.add_trace(go.Bar(x=days,y=pos,name='pós',marker_color='#f76707',showlegend=(j==1)),1,j)
    f.update_xaxes(title='Dia',dtick=1,row=1,col=j)
f.update_yaxes(title='Escore',row=1,col=1)
f.update_layout(**T(height=500,width=1400,barmode='group',legend=dict(orientation='h',y=1.12,x=0.45)))
f.write_image(f'{OUT}/xb_intraday.png',width=1500,height=540,scale=2)

# ---- Fig profiles stacked ----
PROF=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
COLS=['#2b8a3e','#1c7ed6','#7048e8','#868e96','#e03131','#f59f00']
recs=[('D1 (linha de base)','D1'),('Semana','overall'),('D7 (último dia)','D7'),('Pré','pre'),('Pós','pos')]
f=go.Figure()
for p,c in zip(PROF,COLS):
    f.add_trace(go.Bar(x=[lab for lab,_ in recs],y=[R['profiles'][key][p] for _,key in recs],name=p.replace('Barbatana tubarão','Barbatana de tubarão'),marker_color=c))
f.update_layout(**T(height=560,width=1100,barmode='stack',yaxis_title='% de observações',legend=dict(font=dict(size=11))))
f.write_image(f'{OUT}/xb_profiles.png',width=1300,height=620,scale=2)
print('figs OK: xb_framework, xb_traj, xb_intraday, xb_profiles')
