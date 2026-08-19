import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import roc_curve, roc_auc_score
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
M=pd.read_csv('auth_full.csv'); P=json.load(open('physio2.json'))
LD=pd.read_csv('hiit_load.csv')
CV='#2f9e44'; CF='#e8590c'; CP='#7048e8'; CD='#9c36b5'

def lay(f,ttl,h=760,leg=True):
    f.update_layout(template='mdpi',title=dict(text='<b>%s</b>'%ttl,x=0.5,xanchor='center',font=dict(size=16)),
        font=dict(color='#1a1a1a',size=14,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
        margin=dict(l=62,r=24,t=58,b=70))
    if leg: f.update_layout(legend=dict(orientation='h',y=-0.18,x=0.5,xanchor='center',font=dict(size=12),bgcolor='rgba(255,255,255,0.7)',bordercolor='#dee2e6',borderwidth=1))

# ===== 1) T-car PV x humor semanal (vigor e fadiga física) =====
f=make_subplots(rows=1,cols=2,horizontal_spacing=0.12,subplot_titles=['<b>Vigor</b>','<b>Fadiga física</b>'])
for c,(kk,col,lab) in enumerate([('Vigor',CV,'Vigor'),('FadFisica',CF,'Fadiga física')]):
    d=M[['PV',kk]].dropna(); x=d['PV'].values; y=d[kk].values
    b1,b0=np.polyfit(x,y,1); xr=np.array([x.min(),x.max()])
    v=P['pv_week'][kk]
    f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=11,color=col,opacity=0.6,line=dict(color='white',width=1)),showlegend=False),1,c+1)
    f.add_trace(go.Scatter(x=xr,y=b0+b1*xr,mode='lines',line=dict(color=col,width=5),showlegend=False),1,c+1)
    xr_ref='x domain' if c==0 else 'x%d domain'%(c+1); yr_ref='y domain' if c==0 else 'y%d domain'%(c+1)
    f.add_annotation(x=0.5,y=0.97,xref=xr_ref,yref=yr_ref,
        text='ρ = %+.2f · p = %.3f'%(v['rho'],v['p']),showarrow=False,font=dict(size=13,color=col),
        bgcolor='rgba(255,255,255,0.85)',bordercolor=col,borderwidth=1,borderpad=3)
    f.update_xaxes(title='Pico de velocidade no T-car (km/h)',showgrid=False,zeroline=False,row=1,col=c+1)
    f.update_yaxes(title='Escore semanal médio',showgrid=False,zeroline=False,row=1,col=c+1)
lay(f,'Aptidão intermitente (T-car) e humor ao longo da semana',leg=False)
f.write_image(f'{OUT}/pv_mood.png',width=1500,height=680,scale=3); print('OK pv_mood.png')

# ===== 2) Tercis de aptidão x humor semanal (barras) =====
tv=['Baixa','Média','Alta']; COLT=['#adb5bd','#74c0fc','#1971c2']
metrics=[('Vigor','Vigor',CV),('FadFisica','Fadiga física',CF),('TMD','PTH',CP),('Depressao','Depressão',CD)]
f=go.Figure()
xlab=[m[1] for m in metrics]
for i,t in enumerate(tv):
    ys=[P['tercis'][m[0]][t] for m in metrics]
    f.add_trace(go.Bar(x=xlab,y=ys,name='%s aptidão (PV %.1f)'%(t,P['terc_pv'][t]),marker_color=COLT[i],
        marker_line=dict(color='white',width=1)))
for i,m in enumerate(metrics):
    p=P['tercis'][m[0]]['p']
    f.add_annotation(x=xlab[i],y=max(P['tercis'][m[0]][t] for t in tv)+0.4,text='p=%.3f'%p,showarrow=False,font=dict(size=11,color='#495057' if p>=0.05 else '#212529'))
lay(f,'Tercis de aptidão (T-car) e humor semanal')
f.update_yaxes(title='Escore semanal médio',showgrid=False,zeroline=False); f.update_xaxes(showgrid=False,zeroline=False)
f.update_layout(barmode='group')
f.write_image(f'{OUT}/pv_tercis.png',width=1500,height=740,scale=3); print('OK pv_tercis.png')

# ===== 3) HIIT vs sem-HIIT (dumbbell por dimensão) =====
order=['Vigor','PTH','Fadiga','FadFisica','Depressao','Raiva','Tensao','Confusao']
labs={'Vigor':'Vigor','PTH':'PTH','Fadiga':'Fadiga','FadFisica':'Fadiga física','Depressao':'Depressão','Raiva':'Raiva','Tensao':'Tensão','Confusao':'Confusão'}
key={'Vigor':'Vigor','PTH':'TMD','Fadiga':'Fadiga','FadFisica':'FadFisica','Depressao':'Depressao','Raiva':'Raiva','Tensao':'Tensao','Confusao':'Confusao'}
f=go.Figure(); yl=[]
for i,o in enumerate(order):
    v=P['hiit_vs_noh'][key[o]]; y=len(order)-i
    col='#e03131' if v['sig'] else '#adb5bd'
    f.add_trace(go.Scatter(x=[v['noh'],v['hiit']],y=[y,y],mode='lines',line=dict(color=col,width=4),showlegend=False))
    f.add_trace(go.Scatter(x=[v['noh']],y=[y],mode='markers',marker=dict(size=13,color='#1971c2',line=dict(color='white',width=1.4)),showlegend=False))
    f.add_trace(go.Scatter(x=[v['hiit']],y=[y],mode='markers',marker=dict(size=13,color='#e8590c',line=dict(color='white',width=1.4)),showlegend=False))
    f.add_annotation(x=max(v['noh'],v['hiit']),y=y,text='dz=%+.2f%s'%(v['dz'],'*' if v['sig'] else ''),showarrow=False,xshift=48,font=dict(size=11,color=col))
    yl.append((y,labs[o]))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(size=13,color='#1971c2'),name='Sem HIIT (dias 1,3,5,6)'))
f.add_trace(go.Scatter(x=[None],y=[None],mode='markers',marker=dict(size=13,color='#e8590c'),name='Com HIIT (dias 2,4,7)'))
lay(f,'Humor nos dias com vs. sem HIIT (Wilcoxon pareado; * p<0,05)')
f.update_yaxes(tickvals=[y for y,_ in yl],ticktext=[l for _,l in yl],showgrid=False,zeroline=False)
f.update_xaxes(title='Escore médio',showgrid=False,zeroline=False,range=[0,8.5])
f.write_image(f'{OUT}/hiit_contrast.png',width=1500,height=760,scale=3); print('OK hiit_contrast.png')

# ===== 4) ROC — PVini discrimina alta fadiga/baixo vigor semanal =====
f=go.Figure()
COLR={'FadFisica':CF,'Vigor':CV,'Fadiga':'#e8590c','TMD':CP}
LABR={'FadFisica':'Fadiga física','Vigor':'Baixo vigor','Fadiga':'Fadiga','TMD':'PTH'}
f.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(color='#ced4da',width=2,dash='dash'),showlegend=False))
for target,col in [('FadFisica',CF),('Vigor',CV),('TMD',CP)]:
    y=pd.to_numeric(M[target],errors='coerce'); med=y.median()
    hi=(y>med).astype(int) if target!='Vigor' else (y<med).astype(int)
    d=pd.DataFrame({'x':M['PV'],'y':hi}).dropna()
    fpr,tpr,_=roc_curve(d['y'],-d['x']); auc=P['roc'][target]['auc']
    f.add_trace(go.Scatter(x=fpr,y=tpr,mode='lines',line=dict(color=col,width=5,shape='hv'),name='%s (AUC=%.2f)'%(LABR[target],auc)))
cut=P['roc']['FadFisica']['cut']
f.add_annotation(x=0.60,y=0.18,text='limiar PVini ≈ %.1f km/h<br>(fadiga física: sens %.0f%%, esp %.0f%%)'%(cut,100*P['roc']['FadFisica']['sens'],100*P['roc']['FadFisica']['spec']),
    showarrow=False,font=dict(size=11,color='#212529'),bgcolor='rgba(255,255,255,0.88)',bordercolor='#868e96',borderwidth=1,borderpad=4)
lay(f,'Curva ROC: pico de velocidade (T-car) e risco de fadiga/baixo vigor')
f.update_xaxes(title='1 − especificidade',range=[-0.02,1.02],showgrid=False,zeroline=False)
f.update_yaxes(title='Sensibilidade',range=[-0.02,1.02],showgrid=False,zeroline=False)
f.write_image(f'{OUT}/roc_pv.png',width=1100,height=820,scale=3); print('OK roc_pv.png')

# ===== 5) Carga interna do microciclo por sessão HIIT (FC pico por série + PSE) =====
f=make_subplots(specs=[[{'secondary_y':True}]])
days=[2,4,7]
fc=[P['hiit_load_by_day'][str(d)]['fc'] for d in days]; pse=[P['hiit_load_by_day'][str(d)]['pse'] for d in days]
f.add_trace(go.Bar(x=['Dia %d'%d for d in days],y=fc,name='FC de esforço (bpm)',marker_color='#e8590c',marker_line=dict(color='white',width=1),opacity=0.85),secondary_y=False)
f.add_trace(go.Scatter(x=['Dia %d'%d for d in days],y=pse,mode='lines+markers',line=dict(color='#7048e8',width=5),marker=dict(size=13,color='#7048e8',line=dict(color='white',width=1.4)),name='PSE final (0–10)'),secondary_y=True)
lay(f,'Carga interna das sessões de HIIT no microciclo')
f.update_yaxes(title='FC de esforço (bpm)',range=[150,195],showgrid=False,zeroline=False,secondary_y=False)
f.update_yaxes(title='PSE final (0–10)',range=[8,10.5],showgrid=False,zeroline=False,secondary_y=True)
f.update_xaxes(showgrid=False,zeroline=False)
f.write_image(f'{OUT}/hiit_load.png',width=1300,height=720,scale=3); print('OK hiit_load.png')
