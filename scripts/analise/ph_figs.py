import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, json
import plotly.graph_objects as go
import mdpi_style  # estilo MDPI (registra template e torna padrão)
OUT='/home/user/mdlucca/Artigos/figuras'
PH=json.load(open('posthoc.json')); days=list(range(1,8))
def base(**k):
    b=dict(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=25,t=60,b=96)); b.update(k); return b
GRID=dict(gridcolor='#eceef1',zeroline=False)
def emm(v): return [PH[v]['emm'][str(d)] for d in days]
def star(v):  # sig vs D1 (Tukey)
    out=[]
    for d in days:
        if d==1: out.append(''); continue
        p=PH[v]['pairs']['1_%d'%d]['ptukey']; out.append('*' if p<0.05 else '')
    return out
f=go.Figure()
for v,col,nm in [('Vigor','#2f9e44','Vigor'),('Fadiga','#e8590c','Fadiga (BRUMS)'),('FadFisica','#0c8599','Fadiga física')]:
    y=emm(v); s=star(v)
    f.add_trace(go.Scatter(x=days,y=y,mode='lines+markers+text',name=nm,line=dict(color=col,width=3.5),
        marker=dict(size=10,line=dict(color='white',width=1.5)),text=s,textposition='top center',textfont=dict(size=16,color=col)))
# highlight key days
f.add_vrect(x0=1,x1=2,fillcolor='#2f9e44',opacity=0.06,line_width=0,annotation_text='queda de vigor mais forte (D1→D2)',annotation_position='top left',annotation_font_size=11)
f.add_vrect(x0=6,x1=7,fillcolor='#e8590c',opacity=0.07,line_width=0,annotation_text='fadiga sobe mais forte (D6→D7)',annotation_position='bottom right',annotation_font_size=11)
f.update_layout(**base(height=580,width=1250,title=dict(text='<b>Trajetória diária (médias marginais do modelo misto) com pós-teste vs. Dia 1</b>',x=0.5,font=dict(size=17)),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center',font=dict(size=13))))
f.update_xaxes(title='Dia do microciclo',dtick=1,**GRID); f.update_yaxes(title='Escore (média marginal estimada)',**GRID)
f.add_annotation(x=7,y=PH['Vigor']['emm']['7'],text='vigor mín.',showarrow=True,arrowhead=2,ay=30,ax=0,font=dict(size=11,color='#2f9e44'))
f.add_annotation(x=7,y=PH['FadFisica']['emm']['7'],text='fadiga máx.',showarrow=True,arrowhead=2,ay=-38,ax=25,font=dict(size=11,color='#0c8599'))
f.write_image(f'{OUT}/ph_emm.png',width=1350,height=640,scale=3)
print('OK ph_emm; * = p<0,05 vs D1 (Tukey)')
