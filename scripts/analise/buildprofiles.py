import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
import plotly.graph_objects as go, plotly.io as pio
from plotly.subplots import make_subplots
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
import os; os.makedirs(OUT,exist_ok=True)
hum=pd.read_csv(f'{SC}/hum_prof.csv')
TPL='plotly_dark'
PROF=['Iceberg','Barbatana tubarão','Superfície','Submerso','Iceberg invertido','Everest invertido']
PCOL={'Iceberg':'#4dabf7','Barbatana tubarão':'#f03e3e','Superfície':'#adb5bd','Submerso':'#7048e8',
      'Iceberg invertido':'#ff922b','Everest invertido':'#e64980'}
figs={}
T=dict(template=TPL,font=dict(size=14))

# F1: stacked area of 6 profiles across days
tab=pd.crosstab(hum['dia'],hum['perfil'],normalize='index').mul(100).reindex(columns=PROF).fillna(0)
f=go.Figure()
for pr in PROF:
    f.add_trace(go.Scatter(x=tab.index,y=tab[pr],mode='lines',stackgroup='one',name=pr,
        line=dict(width=0.5,color=PCOL[pr]),fillcolor=PCOL[pr],hovertemplate='D%{x}: %{y:.0f}%<extra>'+pr+'</extra>'))
f.update_layout(**T,title='Fig 1 — Distribuição dos 6 perfis de humor ao longo da semana (%)',
    xaxis_title='Dia',yaxis_title='% dos atletas',height=560,xaxis=dict(dtick=1),legend=dict(orientation='h',y=-0.15))
figs['perfil_1_area']=f

# F2: iceberg index raw (noise) + LOWESS smooth, toggle
d=hum.dropna(subset=['ice_idx']).copy()
lo=lowess(d['ice_idx'],d['dia'],frac=0.5,return_sorted=True)
day_m=d.groupby('dia')['ice_idx'].mean()
f=go.Figure()
f.add_trace(go.Scatter(x=d['dia']+np.random.default_rng(1).normal(0,0.06,len(d)),y=d['ice_idx'],mode='markers',
    name='observações (ruído)',marker=dict(color='#4dabf7',size=5,opacity=.35)))
f.add_trace(go.Scatter(x=day_m.index,y=day_m.values,mode='lines+markers',name='média diária',line=dict(color='#fff',width=2,dash='dot'),marker=dict(size=8)))
f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name='LOWESS (suavizado)',line=dict(color='#f03e3e',width=4)))
f.add_hline(y=0,line=dict(color='gray',dash='dot'))
f.update_layout(**T,title='Fig 2 — Índice iceberg (z): observações (ruído) vs curva suavizada (LOWESS)',
    xaxis_title='Dia',yaxis_title='Índice iceberg (vigor − negativas, z)',height=520,xaxis=dict(dtick=1),
    updatemenus=[dict(type='buttons',x=0,y=1.15,buttons=[
      dict(label='Mostrar ruído',method='restyle',args=[{'visible':[True,True,True]}]),
      dict(label='Só suavizado',method='restyle',args=[{'visible':[False,True,True]}])])])
figs['perfil_2_smooth']=f

# F3: pré vs pós (group)
g=hum.groupby('momento')
pre=hum[hum.momento=='pre']; pos=hum[hum.momento=='pos']
cats=['Índice iceberg (z)','% Iceberg','% Superfície','% Barbatana']
val_pre=[pre.ice_idx.mean(),100*(pre.perfil=='Iceberg').mean(),100*(pre.perfil=='Superfície').mean(),100*(pre.perfil=='Barbatana tubarão').mean()]
val_pos=[pos.ice_idx.mean(),100*(pos.perfil=='Iceberg').mean(),100*(pos.perfil=='Superfície').mean(),100*(pos.perfil=='Barbatana tubarão').mean()]
f=go.Figure()
f.add_trace(go.Bar(x=cats,y=[round(v,2) for v in val_pre],name='pré',marker_color='#4dabf7'))
f.add_trace(go.Bar(x=cats,y=[round(v,2) for v in val_pos],name='pós',marker_color='#f03e3e'))
f.update_layout(**T,title='Fig 3 — Pré vs pós (geral do grupo): humor piora dentro do dia',barmode='group',height=460)
figs['perfil_3_prepos']=f

# F4: variation per day (violin of ice_idx)
f=go.Figure()
for dd in range(1,8):
    f.add_trace(go.Violin(y=hum[hum.dia==dd]['ice_idx'],name='D'+str(dd),box_visible=True,meanline_visible=True,
        line_color='#f03e3e' if dd in (2,4,7) else '#4dabf7',points='all',pointpos=0,marker=dict(size=3,opacity=.4)))
f.update_layout(**T,title='Fig 4 — Variação do índice iceberg por dia (vermelho=HIIT) · maior dispersão no D6',
    yaxis_title='Índice iceberg (z)',height=520,showlegend=False)
figs['perfil_4_variacao']=f

# F5: fatigue triad with LOWESS
f=go.Figure()
for v,c in [('FadFisica','#f03e3e'),('Fadiga','#ff922b'),('FadMental','#ffd43b')]:
    dv=hum.dropna(subset=[v])
    l=lowess(dv[v],dv['dia'],frac=0.6,return_sorted=True)
    m=hum.groupby('dia')[v].mean()
    lab={'FadFisica':'Fadiga física (0–10)','Fadiga':'Fadiga BRUMS','FadMental':'Fadiga mental (0–10)'}[v]
    f.add_trace(go.Scatter(x=m.index,y=m.values,mode='markers',marker=dict(color=c,size=7,opacity=.6),showlegend=False))
    f.add_trace(go.Scatter(x=l[:,0],y=l[:,1],mode='lines',name=lab,line=dict(color=c,width=4)))
f.update_layout(**T,title='Fig 5 — Fadiga física × BRUMS × mental (LOWESS): física e BRUMS sobem juntas; mental dissocia',
    xaxis_title='Dia',yaxis_title='Escore',height=500,xaxis=dict(dtick=1),legend=dict(orientation='h',y=-0.18))
figs['perfil_5_fadiga']=f

# F6: radar D1 vs D7 (z subscales)
SUB=['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']; LABS=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
Z=hum[SUB].apply(lambda c:(c-c.mean())/c.std()); Zc=pd.concat([hum[['dia']],Z],axis=1)
f=go.Figure()
for dd,c in [(1,'#4dabf7'),(7,'#f03e3e')]:
    r=Zc[Zc.dia==dd][SUB].mean().values
    f.add_trace(go.Scatterpolar(r=list(r)+[r[0]],theta=LABS+[LABS[0]],fill='toself',name='Dia '+str(dd),line=dict(color=c,width=3),opacity=.6))
f.update_layout(**T,title='Fig 6 — Forma do perfil de humor (z): Dia 1 (iceberg) vs Dia 7 (achatado)',height=520,
    polar=dict(bgcolor='rgba(0,0,0,0)'))
figs['perfil_6_radar']=f

# export 4K PNG
for n,fig in figs.items():
    try: fig.write_image(f'{OUT}/{n}.png',width=3840,height=2160,scale=1)
    except Exception as e: print('png fail',n,e)

# interactive HTML
def div(fig,first): return pio.to_html(fig,include_plotlyjs=('inline' if first else False),full_html=False,config={'displaylogo':False,'toImageButtonOptions':{'format':'png','width':3840,'height':2160,'scale':1}})
secs=[('perfil_1_area','O perfil <b>iceberg</b> cai de 40% (D1) para 17% (D7), enquanto a <b>barbatana de tubarão</b> (fadiga em pico) sobe de 2% para 28% — a assinatura do acúmulo.'),
 ('perfil_2_smooth','Índice iceberg: os pontos (ruído) mostram a variabilidade; a curva LOWESS revela a tendência de queda. Use o botão para alternar ruído/suavizado.'),
 ('perfil_3_prepos','Dentro do dia (pré→pós), o índice iceberg cai (+0,20→−0,28; Wilcoxon p=0,0005) e o iceberg cede lugar à superfície — o humor piora após o treino.'),
 ('perfil_4_variacao','A dispersão entre atletas e a variação intra-dia são máximas no <b>Dia 6</b>; a variância não difere significativamente entre dias (Fligner p=0,26).'),
 ('perfil_5_fadiga','Fadiga física e fadiga do BRUMS sobem juntas (ρ=0,68) e em paralelo; a <b>fadiga mental permanece estável</b> (dissociação) — o custo inscreve-se no corpo, não no mental.'),
 ('perfil_6_radar','A forma do perfil: no D1 o vigor projeta-se sobre as negativas (iceberg); no D7 o vigor recua e a fadiga sobe — o perfil achata-se.')]
body=''.join(f'<section><p class="cap">{t}</p>{div(figs[n],i==0)}</section>' for i,(n,t) in enumerate(secs))
html='<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Perfis de humor — microciclo</title></head><body><div class="wrap"><header><h1>Perfis de humor ao longo do microciclo de choque</h1><p class="sub">Análise transversal dos 6 perfis (Parsons-Smith) · 21–28/04/2024 · 27 atletas · curvas suavizadas (LOWESS) · figuras 4K pelo ícone da câmera</p></header>'+body+'<footer>Atletas anonimizados. Reprodutibilidade: scripts/analise/profiles.py</footer></div><style>body{margin:0;background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,Roboto,sans-serif}.wrap{max-width:1180px;margin:0 auto;padding:26px 18px 60px}header h1{font-size:1.6rem;margin:0 0 4px;color:#fff}.sub{color:#9aa7b4;font-size:.9rem}section{margin:30px 0;padding:16px;background:#131a24;border:1px solid #222c3a;border-radius:14px}.cap{font-size:1rem;line-height:1.5;color:#c9d4df;border-left:3px solid #f03e3e;padding-left:12px;margin:0 0 10px}footer{margin-top:34px;color:#7d8896;font-size:.82rem;border-top:1px solid #222c3a;padding-top:14px}</style></body></html>'
open('/home/user/mdlucca/Artigos/Perfis_Humor.html','w',encoding='utf-8').write(html)
print('OK figs:',list(figs.keys()))
print('HTML salvo:',round(len(html)/1024,1),'KB')
