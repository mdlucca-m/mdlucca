import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import json
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('indiv.json'))['pts13']
x=list(range(len(R['lab'])))
f=go.Figure()
for v,col,nm in [('Vigor','#2f9e44','Vigor'),('Fadiga','#e8590c','Fadiga'),('TMD','#7048e8','PTH')]:
    f.add_trace(go.Scatter(x=x,y=R[v],mode='lines+markers',line=dict(color=col,width=4.3),
        marker=dict(size=9,color=col,line=dict(color='white',width=1)),name=nm))
# faixas dos dias (sombreado alternado leve)
for d in range(2,8):
    i0=1+(d-2)*2-0.5;
    if (d%2)==0:
        f.add_vrect(x0=i0,x1=i0+2,fillcolor='#000000',opacity=0.03,line_width=0,layer='below')
f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=13,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=24,t=54,b=96),width=1120,height=460,
    legend=dict(orientation='h',yanchor='bottom',y=1.04,xanchor='center',x=0.5),
    xaxis=dict(tickmode='array',tickvals=x,ticktext=R['lab'],tickangle=-45,gridcolor='#e6e8eb',zeroline=False),
    yaxis=dict(title='Escore (0–16)',gridcolor='#e6e8eb',zeroline=False))
f.write_image(OUT+'/pts13_curve.png',scale=2)
print('OK pts13_curve.png')
