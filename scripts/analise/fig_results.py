import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('all_results.json')); DL=pd.read_csv('deter_pv.csv')
h=pd.read_csv('hum_prof.csv'); phys=pd.read_csv('phys.csv')[['ID','pos']]; h=h.merge(phys,on='ID',how='left')
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','Tensao':'#1971c2','Depressao':'#9c36b5','Raiva':'#e03131',
     'Confusao':'#f08c00','TMD':'#7048e8','FadFisica':'#0ca678','FadMental':'#c2255c'}
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva',
     'Confusao':'Confusão','TMD':'PTH','FadFisica':'Fadiga física','FadMental':'Fadiga mental'}
POSC={'Goleiro':'#1971c2','Meia':'#2f9e44','Pivô':'#e8590c','Ponta':'#9c36b5'}

# ===== 1) TODAS AS VARIÁVEIS POR DIA (3x3 small multiples) =====
KL=list(LAB.keys())
f=make_subplots(rows=3,cols=3,vertical_spacing=0.10,horizontal_spacing=0.07,subplot_titles=[LAB[k] for k in KL])
for i,k in enumerate(KL):
    r=i//3+1; c=i%3+1; col=COL[k]
    y=[R['por_dia'][k][str(d)] for d in range(1,8)]
    f.add_trace(go.Scatter(x=list(range(1,8)),y=y,mode='lines+markers',line=dict(color=col,width=4),
        marker=dict(size=8,color=col,line=dict(color='white',width=1)),showlegend=False),r,c)
    dd=R['d1d7'][k]
    xrf='x domain' if i==0 else 'x%d domain'%(i+1); yrf='y domain' if i==0 else 'y%d domain'%(i+1)
    f.add_annotation(x=0.97,y=0.95,xref=xrf,yref=yrf,xanchor='right',yanchor='top',
        text='Δ=%+.1f · dz=%+.2f%s'%(dd['delta'],dd['dz'],'*' if dd['sig'] else ''),showarrow=False,
        font=dict(size=9.5,color=col),bgcolor='rgba(255,255,255,0.82)',borderpad=2)
    f.update_xaxes(dtick=1,showgrid=False,zeroline=False,row=r,col=c)
    f.update_yaxes(showgrid=False,zeroline=False,row=r,col=c)
f.update_layout(template='mdpi',title=dict(text='<b>Comportamento de todas as variáveis do BRUMS por dia (média diária, D1–D7)</b>',x=0.5,font=dict(size=16)),
    font=dict(color='#1a1a1a',size=13,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=50,r=20,t=64,b=40),showlegend=False)
f.write_image(f'{OUT}/res_byday.png',width=1560,height=1200,scale=3); print('OK res_byday.png')

# ===== 2) PV × DETERIORAÇÃO (a pergunta central) =====
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.12,subplot_titles=['<b>ΔVigor (D7−D1)</b>','<b>ΔPTH (D7−D1)</b>'])
for c,(k,col) in enumerate([('Vigor','#2f9e44'),('TMD','#7048e8')]):
    d=DL[['PV',k]].dropna(); x=d['PV'].values; y=d[k].values
    b1,b0=np.polyfit(x,y,1); xr=np.array([x.min(),x.max()]); v=R['pv_vs_deterioracao'][k]
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=11,color=col,opacity=0.6,line=dict(color='white',width=1)),showlegend=False),1,c+1)
    f.add_trace(go.Scatter(x=xr,y=b0+b1*xr,mode='lines',line=dict(color=col,width=4,dash='dash'),showlegend=False),1,c+1)
    f.add_hline(y=0,line=dict(color='#adb5bd',width=1),row=1,col=c+1)
    f.add_annotation(x=0.5,y=0.98,xref='x domain' if c==0 else 'x2 domain',yref='y domain' if c==0 else 'y2 domain',
        text='ρ = %+.2f · p = %.3f (n.s.)'%(v['rho'],v['p']),showarrow=False,font=dict(size=12,color=col),bgcolor='rgba(255,255,255,0.85)',bordercolor=col,borderwidth=1,borderpad=3)
    f.update_xaxes(title='Pico de velocidade no T-car (km/h)',showgrid=False,zeroline=False,row=1,col=c+1)
    f.update_yaxes(title='Mudança D1→D7 (escore)',showgrid=False,zeroline=False,row=1,col=c+1)
f.update_layout(template='mdpi',title=dict(text='<b>Aptidão (T-car) NÃO prediz a deterioração do humor na semana</b>',x=0.5,font=dict(size=16)),
    font=dict(color='#1a1a1a',size=13,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=60,b=60),showlegend=False)
f.write_image(f'{OUT}/res_pv_deter.png',width=1500,height=680,scale=3); print('OK res_pv_deter.png')

# ===== 3) DETERIORAÇÃO POR POSIÇÃO (barras agrupadas) =====
pos_order=['Goleiro','Meia','Pivô','Ponta']
f=go.Figure()
for k,col,lab in [('Vigor','#2f9e44','ΔVigor'),('Fadiga','#e8590c','ΔFadiga'),('TMD','#7048e8','ΔPTH')]:
    f.add_trace(go.Bar(x=pos_order,y=[R['por_pos'][p]['delta_d1d7'][k] for p in pos_order],name=lab,marker_color=col,marker_line=dict(color='white',width=1)))
f.update_layout(template='mdpi',barmode='group',title=dict(text='<b>Deterioração do humor (mudança D1→D7) por posição</b>',x=0.5,font=dict(size=16)),
    font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=58,b=64),
    legend=dict(orientation='h',y=-0.16,x=0.5,xanchor='center'))
f.update_yaxes(title='Mudança D1→D7 (escore)',showgrid=False,zeroline=True,zerolinecolor='#adb5bd')
f.update_xaxes(showgrid=False,zeroline=False,ticktext=['%s (n=%d, PV %.1f)'%(p,R['por_pos'][p]['n'],R['por_pos'][p]['PV']) for p in pos_order],tickvals=pos_order)
f.write_image(f'{OUT}/res_bypos.png',width=1400,height=740,scale=3); print('OK res_bypos.png')

# ===== 4) DETERIORAÇÃO INDIVIDUAL (ΔPTH por atleta, ordenado, cor por posição) =====
DL2=DL.merge(phys,on='ID',how='left').sort_values('TMD')
f=go.Figure()
f.add_trace(go.Bar(y=DL2['ID'],x=DL2['TMD'],orientation='h',
    marker_color=[POSC.get(p,'#868e96') for p in DL2['pos']],marker_line=dict(color='white',width=0.5),showlegend=False))
for p,col in POSC.items():
    f.add_trace(go.Bar(y=[None],x=[None],orientation='h',marker_color=col,name=p))
f.add_vline(x=0,line=dict(color='#495057',width=1.5))
f.update_layout(template='mdpi',barmode='overlay',title=dict(text='<b>Deterioração individual: mudança da PTH (D7−D1) por atleta</b>',x=0.5,font=dict(size=16)),
    font=dict(color='#1a1a1a',size=12,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=20,t=58,b=40),
    legend=dict(orientation='h',y=-0.10,x=0.5,xanchor='center'))
f.update_xaxes(title='Mudança da PTH (D7−D1)',showgrid=False,zeroline=False)
f.update_yaxes(showgrid=False,zeroline=False,tickfont=dict(size=9))
f.write_image(f'{OUT}/res_athlete.png',width=1300,height=1000,scale=3); print('OK res_athlete.png')
