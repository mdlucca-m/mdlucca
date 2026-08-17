import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); days=np.arange(1,8); tt=np.linspace(1,7,601)
Vy=h.groupby('dia')['Vigor'].mean().reindex(days).values
Fy=h.groupby('dia')['Fadiga'].mean().reindex(days).values
V=np.poly1d(np.polyfit(days,Vy,3)); F=np.poly1d(np.polyfit(days,Fy,3))
Vc,Fc=V(tt),F(tt)
# cruzamentos exatos (raízes de V-F em [1,7])
D=V-F; cross=sorted([float(r.real) for r in D.roots if abs(r.imag)<1e-6 and 1<=r.real<=7])
cross_json={'cross_days':[round(c,2) for c in cross],'cross_vals':[round(float(V(c)),2) for c in cross],
            'conv_day':2,'gap_d1':float(Vy[0]-Fy[0]),'gap_d7':float(Vy[-1]-Fy[-1])}
json.dump(cross_json,open('cross_pt.json','w'),indent=1,ensure_ascii=False)

GREEN='#2f9e44'; ORANGE='#e8590c'
f=go.Figure()
# área entre as curvas (mostra o 'fechamento da tesoura' e o cruzamento)
f.add_trace(go.Scatter(x=np.r_[tt,tt[::-1]],y=np.r_[Vc,Fc[::-1]],fill='toself',
    fillcolor='rgba(120,120,120,0.10)',line=dict(width=0),hoverinfo='skip',showlegend=False))
# curvas grossas
f.add_trace(go.Scatter(x=tt,y=Vc,mode='lines',line=dict(color=GREEN,width=5.5),name='Vigor'))
f.add_trace(go.Scatter(x=tt,y=Fc,mode='lines',line=dict(color=ORANGE,width=5.5),name='Fadiga'))
# pontos brutos
f.add_trace(go.Scatter(x=days,y=Vy,mode='markers',marker=dict(size=11,color=GREEN,line=dict(color='white',width=1.5)),showlegend=False))
f.add_trace(go.Scatter(x=days,y=Fy,mode='markers',marker=dict(size=11,color=ORANGE,line=dict(color='white',width=1.5)),showlegend=False))
# pontos de cruzamento exatos
for c in cross:
    yv=float(V(c))
    f.add_trace(go.Scatter(x=[c],y=[yv],mode='markers',marker=dict(size=15,color='#212529',symbol='x-thin',line=dict(width=3,color='#212529')),showlegend=False,hoverinfo='skip'))
    f.add_annotation(x=c,y=yv,text='<b>Dia %d</b>'%round(c),showarrow=True,arrowhead=2,arrowwidth=1.6,ax=0,ay=-42,font=dict(size=13,color='#212529'))
# anotações da convergência (Dia 2) e da separação (Dia 7)
f.add_annotation(x=1,y=(Vy[0]+Fy[0])/2,text='gap inicial<br>%.1f pts'%(Vy[0]-Fy[0]),showarrow=False,xanchor='left',font=dict(size=12,color='#495057'))
f.add_annotation(x=7,y=(Vy[-1]+Fy[-1])/2,text='fadiga ><br>vigor',showarrow=False,xanchor='right',font=dict(size=12,color='#495057'))
f.update_layout(template='mdpi',font=dict(color='#1f1f1f',size=17,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=70,r=36,t=64,b=60),width=1150,height=560,
    title=dict(text='<b>Cruzamento energia–fadiga ao longo do microciclo</b>',x=0.5,y=0.97,font=dict(size=19)),
    legend=dict(orientation='h',yanchor='top',y=0.99,xanchor='right',x=0.99,
                bgcolor='rgba(255,255,255,0.95)',bordercolor='#c4c9d0',borderwidth=1.2))
f.update_xaxes(title_text='Dia do microciclo',tickvals=list(days),dtick=1)
f.update_yaxes(title_text='Escore (0–16)',dtick=1)
f.write_image(OUT+'/crossover.png',scale=2)
print('OK crossover.png | cruzamentos (dias):', cross_json['cross_days'])
