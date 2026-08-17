import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
import plotly.graph_objects as go
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); TS=json.load(open('tscore.json'))
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
NM={'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão'}
mu=TS['mu']; sd=TS['sd']
def T(k,x): return 50+10*(x-mu[k])/sd[k]
# cluster order + colors (Terry taxonomy)
CL=['Iceberg','Everest invertido','Iceberg invertido','Submerso','Barbatana tubarão','Superfície']
CLAB={'Iceberg':'Iceberg','Everest invertido':'Everest invertido','Iceberg invertido':'Iceberg invertido','Submerso':'Submerso','Barbatana tubarão':'Barbatana de tubarão','Superfície':'Superfície'}
COL={'Iceberg':'#2f9e44','Everest invertido':'#e03131','Iceberg invertido':'#9c36b5','Submerso':'#1971c2','Barbatana tubarão':'#e8590c','Superfície':'#868e96'}
def base(**k):
    b=dict(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=62,r=22,t=58,b=92)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)

# ===== FIG A: six-cluster T-score profiles (like their Fig 2/3) =====
f=go.Figure()
f.add_hrect(y0=40,y1=60,fillcolor='#f1f3f5',opacity=0.5,line_width=0)
f.add_hline(y=50,line=dict(color='#868e96',dash='dash',width=1.5),annotation_text='Média populacional (T = 50)',annotation_position='top left',annotation_font_size=11)
for c in CL:
    sub=h[h.perfil==c]
    yv=[T(k,sub[k].mean()) for k in SUB]
    f.add_trace(go.Scatter(x=[NM[k] for k in SUB],y=yv,mode='lines+markers',
        name='%s (%.0f%%)'%(CLAB[c],100*len(sub)/len(h)),line=dict(color=COL[c],width=3.2),
        marker=dict(size=9,line=dict(color='white',width=1))))
f.update_layout(**base(height=620,width=1150,title=dict(text='<b>Perfis de humor (clusters) em escores T — amostra do estudo</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=12))))
f.update_yaxes(title='Escore T (M = 50; DP = 10)',range=[30,80],dtick=5,**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/xb6_clusters.png',width=1250,height=680,scale=3)

# ===== FIG B: canonical discriminant functions (like their Fig 4/5) =====
Xr=h[SUB].values
X=np.column_stack([T(k,h[k].values) for k in SUB])  # T-scored
y=h['perfil'].values
lda=LinearDiscriminantAnalysis(n_components=2).fit(X,y)
Z=lda.transform(X)
f=go.Figure()
for c in CL:
    m=y==c
    f.add_trace(go.Scatter(x=Z[m,0],y=Z[m,1],mode='markers',name=CLAB[c],
        marker=dict(color=COL[c],size=7,opacity=0.65,line=dict(color='white',width=0.5))))
# centroids
for c in CL:
    m=y==c; cx,cy=Z[m,0].mean(),Z[m,1].mean()
    f.add_trace(go.Scatter(x=[cx],y=[cy],mode='markers',showlegend=False,
        marker=dict(color=COL[c],size=17,symbol='x',line=dict(color='#111',width=1.5))))
ev=lda.explained_variance_ratio_ if hasattr(lda,'explained_variance_ratio_') else [np.nan,np.nan]
f.update_layout(**base(height=640,width=1050,title=dict(text='<b>Funções discriminantes canônicas dos perfis de humor</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.14,x=0.5,xanchor='center',font=dict(size=12))))
f.update_xaxes(title='Função discriminante 1',**GRID); f.update_yaxes(title='Função discriminante 2',**GRID)
f.write_image(f'{OUT}/xb6_discrim.png',width=1150,height=700,scale=3)
print('OK: xb6_clusters, xb6_discrim | var explicada DF1/DF2:',[round(v,2) for v in ev[:2]])
