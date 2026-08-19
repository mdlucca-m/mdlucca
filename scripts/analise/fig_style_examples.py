import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')

# ============ 1) BOX PLOT COM COLCHETES DE SIGNIFICÂNCIA (estilo "salinidade") ============
# PTH ao longo do microciclo em três momentos: Dia 1, Dia 4, Dia 7
DAYS=[1,4,7]; LAB=['Dia 1','Dia 4','Dia 7']
groups=[h[h.dia==d]['TMD'].dropna().values for d in DAYS]
def pfmt(p): return '%.3f'%p if p>=0.001 else '%.2e'%p
pairs=[(0,1),(1,2),(0,2)]
pres=[(i,j,mannwhitneyu(groups[i],groups[j]).pvalue) for i,j in pairs]
f=go.Figure()
for i,(g,lab) in enumerate(zip(groups,LAB)):
    f.add_trace(go.Box(y=g,name=lab,marker=dict(color='#b03a2e'),line=dict(color='#7b241c',width=2),
        fillcolor='rgba(192,57,43,0.75)',boxpoints='outliers',marker_size=5,width=0.5,showlegend=False))
ymax=max(np.percentile(g,98) for g in groups); base=ymax+1.0; step=(ymax-min(np.min(g) for g in groups))*0.16+1.4
order=sorted(pres,key=lambda t:(t[1]-t[0]))   # colchetes: pares curtos embaixo, largos em cima
for lvl,(i,j,p) in enumerate(order):
    yb=base+lvl*step
    f.add_shape(type='line',x0=i,x1=i,y0=yb-step*0.22,y1=yb,line=dict(color='#333',width=1.5))
    f.add_shape(type='line',x0=j,x1=j,y0=yb-step*0.22,y1=yb,line=dict(color='#333',width=1.5))
    f.add_shape(type='line',x0=i,x1=j,y0=yb,y1=yb,line=dict(color='#333',width=1.5))
    f.add_annotation(x=(i+j)/2,y=yb,yshift=9,text=pfmt(p),showarrow=False,font=dict(size=12,color='#212529'))
f.update_layout(template='mdpi',title=dict(text='<b>Perturbação total do humor (PTH) ao longo do microciclo</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=64,r=24,t=56,b=44))
f.update_yaxes(title='PTH (escore)',gridcolor='#eceef1',zeroline=False)
f.update_xaxes(gridcolor='#eceef1',zeroline=False)
f.write_image(f'{OUT}/box_signif.png',width=1200,height=820,scale=3)
print('OK box_signif.png | p:',[(LAB[i],LAB[j],pfmt(p)) for i,j,p in pres])

# ============ 2) CÍRCULO DE CORRELAÇÃO DA PCA (mapa de variáveis, estilo atletismo) ============
P=json.load(open('pca.json'))
DIMS=P['dims']; vr=P['var_ratio']
L1={k:P['PC1'][k] for k in DIMS}; L2={k:P['PC2'][k] for k in DIMS}
# contribuição de cada variável ao plano (PC1+PC2), em %
c2v={k:(L1[k]**2+L2[k]**2) for k in DIMS}; tot=sum(c2v.values())
contrib={k:100*c2v[k]/tot for k in DIMS}
cvals=np.array([contrib[k] for k in DIMS])
f=go.Figure()
# círculo unitário
th=np.linspace(0,2*np.pi,200)
f.add_trace(go.Scatter(x=np.cos(th),y=np.sin(th),mode='lines',line=dict(color='#adb5bd',width=1.5),showlegend=False,hoverinfo='skip'))
f.add_hline(y=0,line=dict(color='#ced4da',width=1,dash='dash')); f.add_vline(x=0,line=dict(color='#ced4da',width=1,dash='dash'))
# escala de cor por contribuição (Turbo, como o exemplo)
import plotly.colors as pc
cmin,cmax=cvals.min(),cvals.max()
def col(v):
    t=(v-cmin)/(cmax-cmin+1e-9); return pc.sample_colorscale('Turbo',[0.12+0.8*t])[0]
LOFF={'Depressão':(0.02,0.09),'Raiva':(0.0,-0.10)}   # desempilha rótulos quase colineares
for k in DIMS:
    x,y=L1[k],L2[k]; c=col(contrib[k]); dx,dy=LOFF.get(k,(0,0))
    f.add_annotation(x=x,y=y,ax=0,ay=0,xref='x',yref='y',axref='x',ayref='y',showarrow=True,
        arrowhead=2,arrowsize=1.1,arrowwidth=3.4,arrowcolor=c)
    f.add_annotation(x=x*1.12+dx,y=y*1.12+dy,text='<b>%s</b>'%k,showarrow=False,font=dict(size=13,color=c))
# barra de cor (contribuição)
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(color=[cmin,cmax],colorscale=[[0,col(cmin)],[1,col(cmax)]],
    showscale=True,cmin=cmin,cmax=cmax,colorbar=dict(title='Contrib.<br>(%)',thickness=16,len=0.7)),showlegend=False))
f.update_layout(template='mdpi',title=dict(text='<b>PCA das dimensões do BRUMS — círculo de correlação</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    xaxis=dict(title='PC1 (%.0f%%)'%(100*vr[0]),range=[-1.18,1.18],gridcolor='#f1f3f5',zeroline=False,scaleanchor='y',scaleratio=1),
    yaxis=dict(title='PC2 (%.0f%%)'%(100*vr[1]),range=[-1.18,1.18],gridcolor='#f1f3f5',zeroline=False),
    margin=dict(l=56,r=20,t=56,b=48),showlegend=False)
f.write_image(f'{OUT}/pca_circulo.png',width=1050,height=980,scale=3)
print('OK pca_circulo.png | contrib%:',{k:round(contrib[k],1) for k in DIMS})
