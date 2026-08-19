import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); ADV=json.load(open('adv.json'))
seq=[(1,'baseline',1.0)]
for d in range(2,8): seq+=[(d,'pre',d-0.2),(d,'pos',d+0.2)]
x=np.array([xx for _,_,xx in seq])
def cm(k): return np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m,_ in seq])
yP=cm('TMD'); yV=cm('Vigor'); yF=cm('Fadiga')
CA='#e8590c'; CR='#1971c2'  # agudo / recuperacao
trans=ADV['trans']
f=go.Figure()
# faixas de dia de treino (sombra leve entre pre e pos)
for d in range(2,8):
    f.add_vrect(x0=d-0.2,x1=d+0.2,fillcolor='#e8590c',opacity=0.05,line_width=0,layer='below')
# contexto: vigor e fadiga finas
f.add_trace(go.Scatter(x=x,y=yV,mode='lines+markers',line=dict(color='#2f9e44',width=2.4),
    marker=dict(size=6,color='#2f9e44'),name='Vigor',opacity=0.75))
f.add_trace(go.Scatter(x=x,y=yF,mode='lines+markers',line=dict(color='#f08c00',width=2.4),
    marker=dict(size=6,color='#f08c00'),name='Fadiga',opacity=0.75))
# PTH sawtooth com segmentos coloridos por tipo
for i in range(len(x)-1):
    tp=trans[i]['tipo']; col=CA if tp.startswith('Agudo') else CR
    f.add_trace(go.Scatter(x=[x[i],x[i+1]],y=[yP[i],yP[i+1]],mode='lines',line=dict(color=col,width=6),showlegend=False))
    # marca de significancia da PTH
    tv=trans[i]['vars']['TMD']
    if tv['sig']:
        xm=(x[i]+x[i+1])/2; ym=(yP[i]+yP[i+1])/2
        f.add_annotation(x=xm,y=ym,text='<b>dz %+.2f*</b>'%tv['dz'],showarrow=False,
            yshift=16 if tv['dm']>0 else -16,font=dict(size=10.5,color=col),
            bgcolor='rgba(255,255,255,0.85)',borderpad=1)
f.add_trace(go.Scatter(x=x,y=yP,mode='markers',marker=dict(size=10,color='#7048e8',line=dict(color='white',width=1.4)),name='PTH'))
# legenda de tipo (linhas fantasma)
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color=CA,width=6),name='Agudo (pré→pós)'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='lines',line=dict(color=CR,width=6),name='Recuperação (pós→pré)'))
# rotulos de dia no eixo
f.update_layout(template='mdpi',title=dict(text='<b>Efeito agudo (pré→pós) e recuperação (pós→pré) ao longo das 13 coletas</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=60,r=20,t=58,b=76),legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=12),
        bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))
f.update_yaxes(title='Escore',showgrid=False,zeroline=False)
f.update_xaxes(title='Dia do microciclo (base D1; pré/pós D2–D7)',dtick=1,range=[0.8,7.4],showgrid=False,zeroline=False)
f.add_annotation(x=0.99,y=0.98,xref='paper',yref='paper',xanchor='right',yanchor='top',
    text='* transição significativa da PTH (Wilcoxon pareado, p<0,05)',showarrow=False,font=dict(size=10,color='#868e96'))
f.write_image(f'{OUT}/sequential.png',width=1560,height=880,scale=3)
print('OK sequential.png')
