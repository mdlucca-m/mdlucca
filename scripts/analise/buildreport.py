import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats
import statsmodels.formula.api as smf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
OUT='/home/user/mdlucca/Artigos/figuras'
import os; os.makedirs(OUT,exist_ok=True)
hum=pd.read_csv(f'{SC}/humor.csv'); hr=pd.read_csv(f'{SC}/hr_series.csv'); ext=pd.read_csv(f'{SC}/ext_load.csv')
rng=np.random.default_rng(2024)
# palette (dark-friendly)
COL={'TMD':'#e64980','Vigor':'#4dabf7','Fadiga':'#ff922b','FadFisica':'#f03e3e','FadMental':'#ffd43b',
     'Tensao':'#845ef7','Depressao':'#5c7cfa','Raiva':'#e8590c','Confusao':'#22b8cf'}
LAB={'TMD':'PTH/TMD','Vigor':'Vigor','Fadiga':'Fadiga (BRUMS)','FadFisica':'Fadiga física','FadMental':'Fadiga mental',
     'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
HIIT=[2,4,7]
TEMPLATE='plotly_dark'
def add_hiit_bands(fig,ymin=None):
    for d in HIIT:
        fig.add_vrect(x0=d-0.15,x1=d+0.15,fillcolor='#ff6b6b',opacity=0.10,line_width=0)

figs={}  # name -> (fig, title)

# ---------- helpers: cubic fit + analytic derivatives + bootstrap CI ----------
def cubic_fit(days,y): return np.polyfit(days,y,3)
def deriv(coef):
    d1=np.polyder(coef,1); d2=np.polyder(coef,2); return d1,d2
def daily_means(df,v): return df.groupby('dia')[v].mean().reindex(range(1,8)).values
def boot_curves(v,grid,nb=800):
    ids=hum.ID.unique(); Y=[];V=[];A=[]
    for _ in range(nb):
        samp=rng.choice(ids,len(ids),replace=True)
        d=pd.concat([hum[hum.ID==i] for i in samp])
        y=d.groupby('dia')[v].mean().reindex(range(1,8)).values
        if np.isnan(y).any(): continue
        c=cubic_fit(np.arange(1,8),y); d1,d2=deriv(c)
        Y.append(np.polyval(c,grid)); V.append(np.polyval(d1,grid)); A.append(np.polyval(d2,grid))
    return np.array(Y),np.array(V),np.array(A)

grid=np.linspace(1,7,120)

# ===== FIG 1: weekly trajectories =====
f=go.Figure()
for v in ['TMD','Vigor','Fadiga','FadFisica']:
    y=daily_means(hum,v)
    f.add_trace(go.Scatter(x=list(range(1,8)),y=y,mode='lines+markers',name=LAB[v],
        line=dict(color=COL[v],width=3),marker=dict(size=9)))
add_hiit_bands(f)
f.update_layout(template=TEMPLATE,title='Fig 1 — Trajetória semanal do humor e da fadiga (faixas = dias de HIIT)',
    xaxis_title='Dia do microciclo',yaxis_title='Escore',hovermode='x unified',height=520)
figs['fig1_trajetoria']=f

# ===== FIG 2: derivatives (velocity & acceleration) with CI =====
f=make_subplots(rows=1,cols=2,subplot_titles=('Velocidade da mudança  dy/dt','Aceleração  d²y/dt²'))
for v in ['TMD','FadFisica','Vigor']:
    y=daily_means(hum,v); c=cubic_fit(np.arange(1,8),y); d1,d2=deriv(c)
    Yb,Vb,Ab=boot_curves(v,grid)
    v1=np.polyval(d1,grid); v2=np.polyval(d2,grid)
    lo1,hi1=np.percentile(Vb,[2.5,97.5],axis=0); lo2,hi2=np.percentile(Ab,[2.5,97.5],axis=0)
    cc=COL[v]
    # velocity
    f.add_trace(go.Scatter(x=np.r_[grid,grid[::-1]],y=np.r_[hi1,lo1[::-1]],fill='toself',
        fillcolor=cc,opacity=0.15,line=dict(width=0),showlegend=False,hoverinfo='skip'),row=1,col=1)
    f.add_trace(go.Scatter(x=grid,y=v1,mode='lines',name=LAB[v],line=dict(color=cc,width=3)),row=1,col=1)
    # acceleration
    f.add_trace(go.Scatter(x=np.r_[grid,grid[::-1]],y=np.r_[hi2,lo2[::-1]],fill='toself',
        fillcolor=cc,opacity=0.15,line=dict(width=0),showlegend=False,hoverinfo='skip'),row=1,col=2)
    f.add_trace(go.Scatter(x=grid,y=v2,mode='lines',name=LAB[v],line=dict(color=cc,width=3),showlegend=False),row=1,col=2)
for c in (1,2):
    f.add_hline(y=0,line=dict(color='gray',dash='dot'),row=1,col=c)
    for d in HIIT: f.add_vline(x=d,line=dict(color='#ff6b6b',dash='dot',width=1),row=1,col=c)
f.update_layout(template=TEMPLATE,title='Fig 2 — Limites e derivadas: velocidade e aceleração da mudança (IC95% bootstrap)',height=520,hovermode='x')
f.update_xaxes(title_text='Dia');
figs['fig2_derivadas']=f

# ===== FIG 3: internal load per session (dissociation) =====
def banister(hm,hr0=60,hmax=195,D=16): r=(hm-hr0)/(hmax-hr0); return D*r*0.64*np.exp(1.92*r)
S=['S1','S2','S3']; days_s=[2,4,7]
fcp=[hr[hr.sessao==s].HRpico.mean() for s in S]
pse=[hr[hr.sessao==s].PSE.mean() for s in S]
hm=[hr[hr.sessao==s].HRmean.mean() for s in S]
tri=[banister(x) for x in hm]; srpe=[p_*26 for p_ in pse]
def z(a): a=np.array(a); return (a-a.mean())/a.std()
f=go.Figure()
for name,arr,cc in [('FC de pico',fcp,'#f03e3e'),('TRIMP (Banister)',tri,'#ff922b'),
                    ('PSE',pse,'#4dabf7'),('session-RPE',srpe,'#51cf66')]:
    f.add_trace(go.Scatter(x=S,y=z(arr),mode='lines+markers',name=name,line=dict(width=3),marker=dict(size=11),
        customdata=arr,hovertemplate='%{x}: %{customdata:.1f}<extra>'+name+'</extra>'))
f.update_layout(template=TEMPLATE,title='Fig 3 — Dissociação da carga interna entre sessões (padronizado z): FC/TRIMP ↓ vs PSE/sRPE ↑',
    xaxis_title='Sessão de HIIT (S1=22/04 · S2=24/04 · S3=27/04)',yaxis_title='z (padronizado)',height=500,hovermode='x unified')
figs['fig3_carga_interna']=f

# ===== FIG 4: sawtooth pre/post (rise + overnight decay) =====
f=make_subplots(rows=1,cols=2,subplot_titles=('Fadiga física — serrote pré/pós','PTH/TMD — serrote pré/pós'))
for col,v in [(1,'FadFisica'),(2,'TMD')]:
    xs=[];ys=[]
    for d in range(1,8):
        g=hum[hum.dia==d]
        pre=g[g.momento=='pre'][v].mean(); pos=g[g.momento=='pos'][v].mean()
        xs+= [d-0.2,d+0.2]; ys+=[pre,pos]
    f.add_trace(go.Scatter(x=xs,y=ys,mode='lines+markers',line=dict(color=COL[v],width=2),
        marker=dict(size=7),name=LAB[v],showlegend=(col==1)),row=1,col=col)
    for d in HIIT: f.add_vline(x=d,line=dict(color='#ff6b6b',dash='dot',width=1),row=1,col=col)
f.update_layout(template=TEMPLATE,title='Fig 4 — Serrote pré→pós: subida na sessão e recuperação noturna incompleta',height=500)
f.update_xaxes(title_text='Dia')
figs['fig4_serrote']=f

# ===== FIG 5: load-response (mood vs internal load) coupling + fit =====
# merge session FC/PSE (by name->via anonymized? use day-level means as dose bins)
# obs-level: mood on HIIT days vs that day's session FC pico (group)
fc_day={2:fcp[0],4:fcp[1],7:fcp[2]}; pse_day={2:pse[0],4:pse[1],7:pse[2]}
hd=hum[hum.dia.isin([2,4,7])].groupby(['ID','dia'])[['TMD','Vigor','FadFisica']].mean().reset_index()
hd['FCpico']=hd['dia'].map(fc_day)
f=go.Figure()
for v,cc in [('TMD','#e64980'),('Vigor','#4dabf7')]:
    f.add_trace(go.Scatter(x=hd['FCpico'],y=hd[v],mode='markers',name=LAB[v],marker=dict(color=cc,size=7,opacity=0.5)))
    b,a=np.polyfit(hd['FCpico'],hd[v],1); xs=np.linspace(hd.FCpico.min(),hd.FCpico.max(),50)
    f.add_trace(go.Scatter(x=xs,y=a+b*xs,mode='lines',line=dict(color=cc,width=3),showlegend=False))
f.update_layout(template=TEMPLATE,title='Fig 5 — Resposta ao custo interno: humor vs FC de pico da sessão (acoplamento tônico do dia)',
    xaxis_title='FC de pico da sessão (bpm)',yaxis_title='Escore de humor',height=500,hovermode='closest')
figs['fig5_carga_resposta']=f

# ===== FIG 6: between-athlete correlation heatmap =====
TR=['FadFisica','Fadiga','TMD','Vigor']
am=hum.groupby('ID')[TR].mean(); C=am.corr().values
f=go.Figure(go.Heatmap(z=C,x=[LAB[t] for t in TR],y=[LAB[t] for t in TR],
    colorscale='RdBu',zmid=0,zmin=-1,zmax=1,text=np.round(C,2),texttemplate='%{text}',
    colorbar=dict(title='r')))
f.update_layout(template=TEMPLATE,title='Fig 6 — Correlação ENTRE-ATLETAS (eixo energia–fadiga como dimensão de traço)',height=520)
figs['fig6_correlacao']=f

# ===== FIG 7: cubic fit with CI (TMD, FadFisica) =====
f=make_subplots(rows=1,cols=2,subplot_titles=('PTH/TMD','Fadiga física'))
for col,v in [(1,'TMD'),(2,'FadFisica')]:
    y=daily_means(hum,v); c=cubic_fit(np.arange(1,8),y)
    Yb,_,_=boot_curves(v,grid); lo,hi=np.percentile(Yb,[2.5,97.5],axis=0)
    cc=COL[v]
    f.add_trace(go.Scatter(x=np.r_[grid,grid[::-1]],y=np.r_[hi,lo[::-1]],fill='toself',fillcolor=cc,opacity=0.15,line=dict(width=0),showlegend=False,hoverinfo='skip'),row=1,col=col)
    f.add_trace(go.Scatter(x=grid,y=np.polyval(c,grid),mode='lines',line=dict(color=cc,width=3),name='ajuste cúbico',showlegend=(col==1)),row=1,col=col)
    f.add_trace(go.Scatter(x=list(range(1,8)),y=y,mode='markers',marker=dict(color='white',size=9,line=dict(color=cc,width=2)),name='média diária',showlegend=(col==1)),row=1,col=col)
    for d in HIIT: f.add_vline(x=d,line=dict(color='#ff6b6b',dash='dot',width=1),row=1,col=col)
f.update_layout(template=TEMPLATE,title='Fig 7 — Ajuste polinomial cúbico com IC95% (subida–alívio–precipitação)',height=500)
f.update_xaxes(title_text='Dia')
figs['fig7_cubico']=f

# ===== FIG 8: ROC (3 tasks, FadFisica/Fadiga) =====
def roc_xy(score,label):
    s=np.asarray(score,float); y=np.asarray(label,int); ok=~np.isnan(s); s,y=s[ok],y[ok]
    thr=np.unique(s); tpr=[];fpr=[]
    P=(y==1).sum(); N=(y==0).sum()
    for t in np.sort(thr)[::-1]:
        pred=s>=t; tpr.append(((pred)&(y==1)).sum()/P); fpr.append(((pred)&(y==0)).sum()/N)
    return [0]+fpr+[1],[0]+tpr+[1]
f=go.Figure()
d17=hum[hum.dia.isin([1,7])].copy(); d17['y']=(d17.dia==7).astype(int)
x,yv=roc_xy(d17['FadFisica'],d17['y']); f.add_trace(go.Scatter(x=x,y=yv,mode='lines',name='Acúmulo D7 vs D1 (fad. física) AUC=0,86',line=dict(color='#f03e3e',width=3)))
h=hum.dropna(subset=['FadFisica']).copy(); thr=h.FadFisica.quantile(2/3); h['y']=(h.FadFisica>=thr).astype(int)
x,yv=roc_xy(h['Fadiga'],h['y']); f.add_trace(go.Scatter(x=x,y=yv,mode='lines',name='Dia fadiga alta (fadiga BRUMS) AUC=0,84',line=dict(color='#ff922b',width=3)))
tr=hum[hum.dia.isin([2,3,4,5,6,7])]; x,yv=roc_xy(tr['TMD'],tr['HIIT']); f.add_trace(go.Scatter(x=x,y=yv,mode='lines',name='Dia de HIIT (TMD) AUC=0,56',line=dict(color='#4dabf7',width=3)))
f.add_trace(go.Scatter(x=[0,1],y=[0,1],mode='lines',line=dict(color='gray',dash='dash'),name='acaso'))
f.update_layout(template=TEMPLATE,title='Fig 8 — Curvas ROC: sinal no acúmulo (AUC=0,86), não na sessão (AUC≈0,5)',
    xaxis_title='1 − especificidade',yaxis_title='Sensibilidade',height=520,hovermode='closest')
figs['fig8_roc']=f

# ===== FIG 9: effect-size forest (D1->D7) =====
es=[('Fadiga física',1.74,1.32,2.62),('Vigor',-0.95,-1.60,-0.56),('Fadiga (BRUMS)',0.72,0.31,1.38),('PTH/TMD',0.41,-0.01,0.87)]
f=go.Figure()
for i,(nm,d,lo,hi) in enumerate(es):
    cc='#f03e3e' if d>0 else '#4dabf7'
    f.add_trace(go.Scatter(x=[lo,hi],y=[i,i],mode='lines',line=dict(color=cc,width=3),showlegend=False))
    f.add_trace(go.Scatter(x=[d],y=[i],mode='markers',marker=dict(color=cc,size=13),showlegend=False,
        hovertemplate=f'{nm}: dz={d:+.2f} [{lo:+.2f},{hi:+.2f}]<extra></extra>'))
f.add_vline(x=0,line=dict(color='gray',dash='dot'))
f.update_layout(template=TEMPLATE,title='Fig 9 — Tamanhos de efeito D1→D7 (dz, IC95% bootstrap)',
    xaxis_title='dz (Cohen pareado)',height=420,yaxis=dict(tickmode='array',tickvals=list(range(len(es))),ticktext=[e[0] for e in es]))
figs['fig9_efeitos']=f

# ------- export 4K PNGs -------
print("Exportando PNGs 4K...")
for name,fig in figs.items():
    try:
        fig.write_image(f'{OUT}/{name}.png',width=3840,height=2160,scale=1)
    except Exception as e: print('  PNG fail',name,e)

# ------- assemble self-contained HTML -------
def figdiv(fig,first=False):
    return pio.to_html(fig,include_plotlyjs=('inline' if first else False),full_html=False,
                       config={'displaylogo':False,'toImageButtonOptions':{'format':'png','width':3840,'height':2160,'scale':1}})

secoes=[
 ('fig1_trajetoria','O humor deteriora-se ao longo da semana, com pico de perturbação no Dia 7; a mudança concentra-se no eixo energia–fadiga (vigor cai, fadiga sobe).'),
 ('fig2_derivadas','As derivadas do ajuste cúbico mostram <b>onde</b> a mudança se concentra: a velocidade (dy/dt) do PTH é máxima no Dia 7 (precipitação final) e a aceleração (d²y/dt²) inverte de sinal nos dias 5–6 — a inflexão que antecede o disparo.'),
 ('fig7_cubico','Ajuste polinomial cúbico (vencedor por AIC e LRT) com IC95%: a trajetória tem três fases — subida inicial, alívio no meio da semana e precipitação no Dia 7.'),
 ('fig4_serrote','Padrão em serrote: cada sessão eleva a fadiga (pré→pós) e a noite recupera parte, mas o resíduo não recuperado acumula-se — o piso de fadiga sobe rumo ao Dia 7.'),
 ('fig3_carga_interna','Dissociação da carga interna: com a carga externa fixa (104% da PV), a FC de pico e o TRIMP <b>caem</b> (supressão cardíaca sob fadiga) enquanto a PSE e o session-RPE <b>sobem</b> — o TRIMP cardíaco subestima a carga.'),
 ('fig5_carga_resposta','Acoplamento tônico: nas sessões de maior FC de pico (frescor) o vigor é maior e a perturbação menor — o custo fisiológico e o psicológico movem-se juntos.'),
 ('fig6_correlacao','Estrutura entre-atletas (modelo misto multivariado): fadiga física, fadiga e PTH covariam forte e positivamente e opõem-se ao vigor (até −0,65) — o eixo energia–fadiga é uma dimensão de traço.'),
 ('fig8_roc','ROC: o humor/fadiga quase não discrimina a sessão de HIIT (AUC≈0,5), mas discrimina fortemente o acúmulo D7 vs D1 (AUC=0,86) — o sinal está na tendência, não no evento.'),
 ('fig9_efeitos','Tamanhos de efeito do acúmulo D1→D7: grandes na fadiga física (dz=+1,74) e no vigor (−0,95).'),
]
body=[]
for name,txt in secoes:
    first=(name==secoes[0][0])
    body.append(f'<section><p class="cap">{txt}</p>{figdiv(figs[name],first)}</section>')
html=f"""<div class="wrap">
<header><h1>Monitoramento do microciclo de choque de HIIT — painel analítico</h1>
<p class="sub">Handebol de elite · semana de 21–28/04/2024 · 27 atletas · 456 observações · reanálise independente (Python)</p>
<p class="sub">Derivadas, curvas de carga–resposta, ajustes cúbicos, ROC e modelo multivariado. Figuras interativas (zoom, hover, exportação PNG 4K pelo ícone da câmera).</p></header>
{''.join(body)}
<footer><p>Atletas anonimizados (A01–A27). Reprodutibilidade: <code>scripts/analise/</code>. Gerado para revisão com o orientador.</p></footer>
</div>
<style>
body{{margin:0;background:#0d1117;color:#e6edf3;font-family:-apple-system,Segoe UI,Roboto,sans-serif}}
.wrap{{max-width:1180px;margin:0 auto;padding:28px 20px 60px}}
header h1{{font-size:1.7rem;margin:0 0 6px;color:#fff}}
.sub{{color:#9aa7b4;margin:2px 0;font-size:.95rem}}
section{{margin:34px 0;padding:18px;background:#131a24;border:1px solid #222c3a;border-radius:14px}}
.cap{{font-size:1.02rem;line-height:1.5;color:#c9d4df;margin:0 0 12px;border-left:3px solid #ff6b6b;padding-left:12px}}
footer{{margin-top:40px;color:#7d8896;font-size:.85rem;border-top:1px solid #222c3a;padding-top:16px}}
code{{background:#1c2530;padding:2px 6px;border-radius:5px}}
</style>"""
open('/home/user/mdlucca/Artigos/Relatorio_Interativo.html','w',encoding='utf-8').write(html)
print("HTML salvo: Artigos/Relatorio_Interativo.html")
print("PNGs 4K em: Artigos/figuras/")
print("figuras:",list(figs.keys()))
