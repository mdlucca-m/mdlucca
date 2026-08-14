import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, os
import plotly.graph_objects as go, plotly.io as pio
import statsmodels.formula.api as smf
from statsmodels.stats.anova import anova_lm
from statsmodels.nonparametric.smoothers_lowess import lowess
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'; os.makedirs(OUT,exist_ok=True)
os.environ.setdefault('BROWSER_PATH','/opt/pw-browsers/chromium-1194/chrome-linux/chrome')
hum=pd.read_csv(f'{SC}/humor.csv')
D=json.load(open(f'{SC}/amp_data.json'))
TPL='plotly_dark'; T=dict(template=TPL,font=dict(size=14))
figs={}
LABS={'FadFisica':'Fadiga física','Fadiga':'Fadiga BRUMS','Vigor':'Vigor','TMD':'PTH/TMD','FadMental':'Fadiga mental',
      'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
order=['FadFisica','Fadiga','Vigor','TMD','FadMental','Raiva','Confusao','Depressao','Tensao']

# FIG A — variance partition (stacked 100%): signal-day / trait / noise
sn=D['sn']
xs=[LABS[v] for v in order]
day=[sn[v]['pday'] for v in order]; tr=[sn[v]['ptrait'] for v in order]; no=[sn[v]['pnoise'] for v in order]
f=go.Figure()
f.add_trace(go.Bar(x=xs,y=day,name='Sinal do microciclo (dia)',marker_color='#f03e3e',
   hovertemplate='%{y:.1f}% sinal-dia<extra></extra>'))
f.add_trace(go.Bar(x=xs,y=tr,name='Traço (entre atletas, estável)',marker_color='#4dabf7',
   hovertemplate='%{y:.1f}% traço<extra></extra>'))
f.add_trace(go.Bar(x=xs,y=no,name='Ruído (erro + flutuação aleatória)',marker_color='#495057',
   hovertemplate='%{y:.1f}% ruído<extra></extra>'))
f.update_layout(**T,barmode='stack',height=560,title='Fig A — De onde vem a variância? Sinal do microciclo vs traço vs ruído (%)',
   yaxis_title='% da variância total',legend=dict(orientation='h',y=-0.22),xaxis_tickangle=-20)
figs['amp_a_variancia']=f

# FIG B — signal amplitude vs noise thresholds (individual MDC vs group MDC vs SWC)
sig=[sn[v]['sig'] for v in order]; mdc=[sn[v]['mdc'] for v in order]
mdcg=[sn[v]['mdc_g'] for v in order]; swc=[sn[v]['swc'] for v in order]
f=go.Figure()
f.add_trace(go.Bar(x=xs,y=sig,name='Amplitude do sinal semanal',marker_color='#f03e3e',
   hovertemplate='ampl.=%{y:.2f}<extra></extra>'))
f.add_trace(go.Scatter(x=xs,y=mdc,name='MDC95 individual (ruído p/ 1 atleta)',mode='markers',
   marker=dict(symbol='line-ew',size=26,line=dict(width=4,color='#ffd43b'))))
f.add_trace(go.Scatter(x=xs,y=mdcg,name='MDC95 grupo (ruído da média, ÷√n)',mode='markers',
   marker=dict(symbol='line-ew',size=26,line=dict(width=4,color='#51cf66'))))
f.add_trace(go.Scatter(x=xs,y=swc,name='SWC (mínima mudança relevante)',mode='markers',
   marker=dict(symbol='line-ew',size=26,line=dict(width=3,color='#adb5bd'))))
f.update_layout(**T,height=560,title='Fig B — A oscilação semanal supera o ruído? Sinal vs MDC individual vs MDC do grupo',
   yaxis_title='Unidades da escala',legend=dict(orientation='h',y=-0.22),xaxis_tickangle=-20)
figs['amp_b_limiares']=f

# FIG C — amplitude: total vs signal vs intra-athlete
amp=D['amp']
tot=[amp[v]['tot'] for v in order]; sg=[amp[v]['sig'] for v in order]; intra=[amp[v]['intra'] for v in order]
f=go.Figure()
f.add_trace(go.Bar(x=xs,y=tot,name='Amplitude total (max−min amostra)',marker_color='#495057'))
f.add_trace(go.Bar(x=xs,y=intra,name='Amplitude intra-atleta (média)',marker_color='#4dabf7'))
f.add_trace(go.Bar(x=xs,y=sg,name='Amplitude do sinal (trajetória do grupo)',marker_color='#f03e3e'))
f.update_layout(**T,barmode='group',height=520,title='Fig C — Amplitude (range): total vs intra-atleta vs sinal do microciclo',
   yaxis_title='Unidades da escala',legend=dict(orientation='h',y=-0.22),xaxis_tickangle=-20)
figs['amp_c_amplitude']=f

# FIG D — noise vs signal visual for FadFisica: raw jitter + LOWESS + individual noise band + group mean band
v='FadFisica'; d=hum.dropna(subset=[v]).copy()
m=smf.ols(f'{v} ~ C(ID)+C(dia)',data=d).fit()
etm=np.sqrt(anova_lm(m,typ=1).loc['Residual','mean_sq'])
daym=d.groupby('dia')[v].mean(); days=daym.index.values
n_day=d.groupby('dia').size().values; sem_g=etm/np.sqrt(n_day)
lo=lowess(d[v],d['dia'],frac=0.6,return_sorted=True)
rng=np.random.default_rng(3)
f=go.Figure()
# individual noise band (±MDC/2 around group mean) — the "you can't tell for one athlete" zone
f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),
   y=list(daym.values+1.96*etm)+list((daym.values-1.96*etm)[::-1]),fill='toself',
   fillcolor='rgba(255,212,59,0.10)',line=dict(width=0),name='banda de ruído individual (±MDC)',hoverinfo='skip'))
f.add_trace(go.Scatter(x=d['dia']+rng.normal(0,0.07,len(d)),y=d[v],mode='markers',name='observações (sinal+ruído)',
   marker=dict(color='#74c0fc',size=5,opacity=.35)))
# group mean ± its SEM band (tight)
f.add_trace(go.Scatter(x=list(days)+list(days[::-1]),
   y=list(daym.values+1.96*sem_g)+list((daym.values-1.96*sem_g)[::-1]),fill='toself',
   fillcolor='rgba(81,207,102,0.28)',line=dict(width=0),name='IC95% da média do grupo',hoverinfo='skip'))
f.add_trace(go.Scatter(x=days,y=daym.values,mode='lines+markers',name='média diária do grupo (sinal)',
   line=dict(color='#fff',width=2,dash='dot'),marker=dict(size=8)))
f.add_trace(go.Scatter(x=lo[:,0],y=lo[:,1],mode='lines',name='LOWESS (sinal suavizado)',line=dict(color='#f03e3e',width=4)))
f.update_layout(**T,height=560,xaxis=dict(dtick=1,title='Dia'),yaxis_title='Fadiga física (0–10)',
   title='Fig D — Fadiga física: sinal (média/LOWESS) emerge do ruído no grupo, mas cabe na banda individual',
   legend=dict(orientation='h',y=-0.18))
figs['amp_d_sinal_ruido']=f

for n,fig in figs.items():
    try: fig.write_image(f'{OUT}/{n}.png',width=3840,height=2160,scale=1)
    except Exception as e: print('png fail',n,e)

def div(fig,first): return pio.to_html(fig,include_plotlyjs=('inline' if first else False),full_html=False,config={'displaylogo':False,'toImageButtonOptions':{'format':'png','width':3840,'height':2160,'scale':1}})
caps=[('amp_a_variancia','Para quase todas as variáveis, o <b>sinal do microciclo</b> (efeito do dia) é a menor fatia da variância (1–12%); a maior parte é <b>traço</b> (diferenças estáveis entre atletas, 32–73%) e <b>ruído</b> (erro de medida + flutuação aleatória, 26–64%). A fadiga física tem a maior fatia de sinal (12%).'),
 ('amp_b_limiares','A amplitude da oscilação semanal fica <b>abaixo do MDC95 individual</b> (não dá para confiar na mudança de UM atleta com UMA coleta) mas <b>muito acima do MDC95 do grupo</b> (a média de ~27 atletas encolhe o ruído por √n) — por isso o efeito é real no grupo e exige médias de ≥3 coletas no indivíduo.'),
 ('amp_c_amplitude','A amplitude <b>total</b> mistura tudo; a amplitude <b>intra-atleta</b> (o quanto um atleta oscila na semana) é grande porque soma sinal+ruído; a amplitude do <b>sinal</b> (a trajetória média do grupo) é bem menor — a maior parte do balanço individual é ruído, não microciclo.'),
 ('amp_d_sinal_ruido','A nuvem azul é a medida bruta (sinal+ruído). A curva branca/LOWESS é o sinal. A faixa verde estreita (IC95% da média) mostra que o sinal do grupo é nítido; a faixa amarela larga (banda de ruído individual, ±MDC) mostra que, para um único atleta, a subida semanal ainda cabe dentro do ruído.')]
body=''.join(f'<section><p class="cap">{c}</p>{div(figs[n],i==0)}</section>' for i,(n,c) in enumerate(caps))
html='<!DOCTYPE html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Amplitude, ruído e sinal — microciclo</title></head><body><div class="wrap"><header><h1>Amplitude, ruído e sinal no microciclo de choque</h1><p class="sub">Quanto da oscilação é sinal do microciclo, quanto é traço estável e quanto é ruído · 21–28/04/2024 · 27 atletas · figuras 4K pelo ícone da câmera</p></header>'+body+'<footer>Atletas anonimizados. Reprodutibilidade: scripts/analise/amplitude.py</footer></div><style>body{margin:0;background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,Roboto,sans-serif}.wrap{max-width:1180px;margin:0 auto;padding:26px 18px 60px}header h1{font-size:1.6rem;margin:0 0 4px;color:#fff}.sub{color:#9aa7b4;font-size:.9rem}section{margin:30px 0;padding:16px;background:#131a24;border:1px solid #222c3a;border-radius:14px}.cap{font-size:1rem;line-height:1.5;color:#c9d4df;border-left:3px solid #f03e3e;padding-left:12px;margin:0 0 10px}footer{margin-top:34px;color:#7d8896;font-size:.82rem;border-top:1px solid #222c3a;padding-top:14px}</style></body></html>'
open('/home/user/mdlucca/Artigos/Amplitude_Ruido_Sinal.html','w',encoding='utf-8').write(html)
print('OK figs:',list(figs.keys())); print('HTML',round(len(html)/1024,1),'KB')
