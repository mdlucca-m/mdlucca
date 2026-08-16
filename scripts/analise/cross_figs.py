import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
import plotly.graph_objects as go
OUT='/home/user/mdlucca/Artigos/figuras'
C=json.load(open('cross.json')); days=range(1,8)
def base(**k):
    b=dict(template='plotly_white',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=58,b=90)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
# build 14-timepoint sawtooth: pré at x=d, pós at x=d+0.45
xs=[]; Vy=[]; Fy=[]; lab=[]
for d in days:
    xs.append(d); Vy.append(C['Vpre'][str(d)]); Fy.append(C['Fpre'][str(d)]); lab.append('D%d pré'%d)
    xs.append(d+0.45); Vy.append(C['Vpos'][str(d)]); Fy.append(C['Fpos'][str(d)]); lab.append('D%d pós'%d)
f=go.Figure()
f.add_trace(go.Scatter(x=xs,y=Vy,mode='lines+markers',name='Vigor',line=dict(color='#2f9e44',width=3.2),marker=dict(size=8,line=dict(color='white',width=1)),customdata=lab,hovertemplate='%{customdata}: %{y:.2f}<extra>Vigor</extra>'))
f.add_trace(go.Scatter(x=xs,y=Fy,mode='lines+markers',name='Fadiga',line=dict(color='#e8590c',width=3.2),marker=dict(size=8,line=dict(color='white',width=1)),customdata=lab,hovertemplate='%{customdata}: %{y:.2f}<extra>Fadiga</extra>'))
# mark crossings
for xc in C['cross_pp']:
    f.add_vline(x=xc,line=dict(color='#adb5bd',dash='dot',width=1.2))
f.add_annotation(x=C['cross_pp'][0],y=8.4,text='1º cruzamento<br>(Dia 2)',showarrow=False,font=dict(size=11,color='#495057'))
f.add_annotation(x=7.2,y=C['Fpos']['7'],text='fadiga supera<br>o vigor (D7)',showarrow=True,arrowhead=2,ax=-40,ay=-30,font=dict(size=11,color='#e8590c'))
# shade weekend/last day
f.add_vrect(x0=6.6,x1=7.6,fillcolor='#e8590c',opacity=0.05,line_width=0)
f.update_layout(**base(height=560,width=1300,title=dict(text='<b>Cruzamento vigor × fadiga por dia e momento (pré/pós)</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13))))
f.update_xaxes(title='Dia do microciclo (pré → pós dentro de cada dia)',dtick=1,range=[0.7,7.9],**GRID)
f.update_yaxes(title='Escore (0–16)',**GRID)
f.write_image(f'{OUT}/x_cross.png',width=1400,height=620,scale=3)

# variance decomposition stacked bar
ORD=[('Vigor','Vigor'),('Fadiga','Fadiga'),('TMD','PTH'),('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
labs=[l for _,l in ORD]; ath=[C['dec'][k]['vc']['ath'] for k,_ in ORD]; day=[C['dec'][k]['vc']['day'] for k,_ in ORD]; res=[C['dec'][k]['vc']['res'] for k,_ in ORD]
f=go.Figure()
f.add_trace(go.Bar(x=labs,y=ath,name='Entre atletas',marker_color='#1971c2'))
f.add_trace(go.Bar(x=labs,y=day,name='Dia (microciclo)',marker_color='#2f9e44'))
f.add_trace(go.Bar(x=labs,y=res,name='Resíduo (ruído)',marker_color='#adb5bd'))
f.update_layout(**base(height=540,width=1150,barmode='stack',title=dict(text='<b>Decomposição da variância das variáveis do humor</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13))))
f.update_yaxes(title='% da variância total',range=[0,100],**GRID); f.update_xaxes(**GRID)
f.write_image(f'{OUT}/x_vardecomp.png',width=1250,height=600,scale=3)
print('OK: x_cross, x_vardecomp')
