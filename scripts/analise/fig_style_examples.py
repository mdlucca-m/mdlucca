import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv')

# ============ 1) BOX PLOT COM COLCHETES DE SIGNIFICÂNCIA (escala ajustada, mais visual) ============
DAYS=[1,4,7]; LAB=['Dia 1','Dia 4','Dia 7']
groups=[h[h.dia==d]['TMD'].dropna().values for d in DAYS]
def pfmt(p): return 'p = %.3f'%p if p>=0.001 else 'p = %.1e'%p
def star(p): return '***' if p<0.001 else '**' if p<0.01 else '*' if p<0.05 else 'ns'
pairs=[(0,1),(1,2),(0,2)]
pres=[(i,j,mannwhitneyu(groups[i],groups[j]).pvalue) for i,j in pairs]
# escala focada na caixa+bigode de Tukey (outliers extremos recortados p/ ficar visual)
def whisk(g):
    q1,q3=np.percentile(g,[25,75]); iqr=q3-q1
    lo=g[g>=q1-1.5*iqr].min(); hi=g[g<=q3+1.5*iqr].max(); return lo,hi
wlo=min(whisk(g)[0] for g in groups); whi=max(whisk(g)[1] for g in groups)
f=go.Figure()
for g,lab in zip(groups,LAB):
    f.add_trace(go.Box(y=g,name=lab,marker=dict(color='#e03131',size=4,opacity=0.5),line=dict(color='#a51111',width=2.6),
        fillcolor='rgba(224,49,49,0.78)',boxpoints='outliers',width=0.55,showlegend=False))
rng=whi-wlo; base=whi+rng*0.06; step=rng*0.13
order=sorted(pres,key=lambda t:(t[1]-t[0]))       # pares curtos embaixo, largos em cima
for lvl,(i,j,p) in enumerate(order):
    yb=base+lvl*step
    for xx in (i,j):
        f.add_shape(type='line',x0=xx,x1=xx,y0=yb-step*0.28,y1=yb,line=dict(color='#333',width=1.6))
    f.add_shape(type='line',x0=i,x1=j,y0=yb,y1=yb,line=dict(color='#333',width=1.6))
    f.add_annotation(x=(i+j)/2,y=yb,yshift=12,text='%s (%s)'%(pfmt(p),star(p)),showarrow=False,font=dict(size=12.5,color='#212529'))
f.update_layout(template='mdpi',title=dict(text='<b>Perturbação total do humor (PTH) ao longo do microciclo</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    margin=dict(l=64,r=24,t=56,b=44))
f.update_yaxes(title='PTH (escore)',range=[wlo-rng*0.08,base+2*step+rng*0.12],gridcolor='#eceef1',zeroline=True,zerolinecolor='#ced4da')
f.update_xaxes(gridcolor='#eceef1',zeroline=False)
f.write_image(f'{OUT}/box_signif.png',width=1240,height=820,scale=3)
print('OK box_signif.png | p:',[(LAB[i],LAB[j],pfmt(p),star(p)) for i,j,p in pres])

# ============ 2) CÍRCULO DE CORRELAÇÃO DA PCA (setas grossas, cores vivas, espessura ∝ contribuição) ============
P=json.load(open('pca.json')); DIMS=P['dims']; vr=P['var_ratio']
L1={k:P['PC1'][k] for k in DIMS}; L2={k:P['PC2'][k] for k in DIMS}
c2v={k:(L1[k]**2+L2[k]**2) for k in DIMS}; tot=sum(c2v.values())
contrib={k:100*c2v[k]/tot for k in DIMS}
PAL={'Tensão':'#1971c2','Depressão':'#9c36b5','Raiva':'#e03131','Vigor':'#2f9e44','Fadiga':'#e8590c','Confusão':'#f08c00'}
cmin=min(contrib.values()); cmax=max(contrib.values())
def wid(k): return 5.0+9.0*(contrib[k]-cmin)/(cmax-cmin+1e-9)   # espessura ∝ contribuição (5–14)
LOFF={'Depressão':(0.03,0.10),'Raiva':(0.0,-0.11)}
f=go.Figure()
th=np.linspace(0,2*np.pi,240)
f.add_trace(go.Scatter(x=np.cos(th),y=np.sin(th),mode='lines',line=dict(color='#adb5bd',width=1.6),showlegend=False,hoverinfo='skip'))
f.add_hline(y=0,line=dict(color='#ced4da',width=1,dash='dash')); f.add_vline(x=0,line=dict(color='#ced4da',width=1,dash='dash'))
for k in DIMS:
    x,y=L1[k],L2[k]; c=PAL[k]; dx,dy=LOFF.get(k,(0,0))
    f.add_annotation(x=x,y=y,ax=0,ay=0,xref='x',yref='y',axref='x',ayref='y',showarrow=True,
        arrowhead=2,arrowsize=1.0,arrowwidth=wid(k),arrowcolor=c)
    f.add_annotation(x=x*1.13+dx,y=y*1.13+dy,text='<b>%s</b>'%k,showarrow=False,font=dict(size=14,color=c))
f.add_annotation(x=-1.12,y=-1.10,text='espessura da seta ∝ contribuição',showarrow=False,
    xanchor='left',font=dict(size=11,color='#666'))
f.update_layout(template='mdpi',title=dict(text='<b>PCA das dimensões do BRUMS: círculo de correlação</b>',font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    xaxis=dict(title='PC1 (%.0f%%)'%(100*vr[0]),range=[-1.20,1.20],gridcolor='#f1f3f5',zeroline=False,scaleanchor='y',scaleratio=1),
    yaxis=dict(title='PC2 (%.0f%%)'%(100*vr[1]),range=[-1.20,1.20],gridcolor='#f1f3f5',zeroline=False),
    margin=dict(l=56,r=20,t=56,b=48),showlegend=False)
f.write_image(f'{OUT}/pca_circulo.png',width=1050,height=1000,scale=3)
print('OK pca_circulo.png | contrib%:',{k:round(contrib[k],1) for k in DIMS})
