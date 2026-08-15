import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); it=pd.read_csv('items.csv')
VIG=['Animado','ComDisposição','ComEnergia','Alerta']
FAD=['Esgotado','Exausto','Sonolento','Cansado']
NEG=['Apavorado','Ansioso','Preocupado','Tenso','Deprimido','Desanimado','Triste','Infeliz',
     'Irritado','Zangado','ComRaiva','MalHumorado','Esgotado','Exausto','Sonolento','Cansado',
     'Confuso','Inseguro','Desorientado','Indeciso']
def alpha(df,cols):
    X=df[cols].dropna(); k=len(cols); vi=X.var(ddof=1).sum(); vt=X.sum(axis=1).var(ddof=1)
    return float(k/(k-1)*(1-vi/vt))
# TMD composite: negatives + reversed vigor (4 - vigor item), 24 items
tmd_it=it.copy()
for c in VIG: tmd_it[c+'_r']=4-tmd_it[c]
TMD_cols=NEG+[c+'_r' for c in VIG]
A={'Vigor':alpha(it,VIG),'Fadiga':alpha(it,FAD),'TMD':alpha(tmd_it,TMD_cols)}
print('Cronbach α:',{k:round(v,3) for k,v in A.items()})

# per-athlete D1 & D7 (daily mean)
dm=h.groupby(['ID','dia'])[['Vigor','Fadiga','TMD']].mean().reset_index()
def piv(v): return dm.pivot(index='ID',columns='dia',values=v)
RES={}; rows=[]; SD1={}
for v in ['Vigor','Fadiga','TMD']:
    p=piv(v); d1=p[1]; d7=p[7]; sd1=d1.std(ddof=1); SD1[v]=float(sd1)
    sediff=sd1*np.sqrt(2*(1-A[v]))
    rci=(d7-d1)/sediff
    RES[v]=dict(alpha=A[v],sd1=float(sd1),sediff=float(sediff),
        rci={str(i):(float(x) if pd.notna(x) else None) for i,x in rci.items()})
# per-athlete table
ids=sorted(dm.ID.unique())
def cls(v,r):
    if r is None or np.isnan(r): return '—'
    if v=='Vigor': return '↓ piora' if r<=-1.96 else ('↑ melhora' if r>=1.96 else '→ estável')
    return '↑ piora' if r>=1.96 else ('↓ melhora' if r<=-1.96 else '→ estável')
for aid in ids:
    row={'ID':aid}
    for v in ['Vigor','Fadiga','TMD']:
        r=RES[v]['rci'].get(aid); row[v+'_rci']=r; row[v+'_cls']=cls(v,r)
    rows.append(row)
T=pd.DataFrame(rows); T.to_csv('rci_athletes.csv',index=False)
# summary counts
SUMM={}
for v in ['Vigor','Fadiga','TMD']:
    vals=[RES[v]['rci'][a] for a in ids if RES[v]['rci'].get(a) is not None]
    det=sum(1 for r in vals if (v=='Vigor' and r<=-1.96) or (v!='Vigor' and r>=1.96))
    imp=sum(1 for r in vals if (v=='Vigor' and r>=1.96) or (v!='Vigor' and r<=-1.96))
    sta=len(vals)-det-imp
    SUMM[v]=dict(n=len(vals),piora=det,estavel=sta,melhora=imp,
        pct_piora=round(100*det/len(vals),0),pct_estavel=round(100*sta/len(vals),0),pct_melhora=round(100*imp/len(vals),0))
json.dump(dict(alpha=A,sd1=SD1,sediff={v:RES[v]['sediff'] for v in RES},summary=SUMM,
    rci={v:RES[v]['rci'] for v in RES}),open('rci.json','w'),indent=1)
print('SEdiff:',{v:round(RES[v]['sediff'],2) for v in RES})
print('Resumo:')
for v,s in SUMM.items(): print('  %-6s n=%d | piora %d (%.0f%%) estável %d (%.0f%%) melhora %d (%.0f%%)'%(v,s['n'],s['piora'],s['pct_piora'],s['estavel'],s['pct_estavel'],s['melhora'],s['pct_melhora']))

# ---- figure: RCI per athlete (3 panels, sorted lollipop) ----
f=make_subplots(rows=1,cols=3,horizontal_spacing=0.09,subplot_titles=['Vigor','Fadiga','PTH/TMD'])
for j,v in enumerate(['Vigor','Fadiga','TMD'],1):
    data=[(a,RES[v]['rci'][a]) for a in ids if RES[v]['rci'].get(a) is not None]
    data=sorted(data,key=lambda x:x[1])
    ys=[a for a,_ in data]; xs=[r for _,r in data]
    cols=[]
    for r in xs:
        det=(v=='Vigor' and r<=-1.96) or (v!='Vigor' and r>=1.96)
        imp=(v=='Vigor' and r>=1.96) or (v!='Vigor' and r<=-1.96)
        cols.append('#c92a2a' if det else ('#2b8a3e' if imp else '#adb5bd'))
    for a,r,c in zip(ys,xs,cols):
        f.add_trace(go.Scatter(x=[0,r],y=[a,a],mode='lines',line=dict(color=c,width=2),showlegend=False),1,j)
    f.add_trace(go.Scatter(x=xs,y=ys,mode='markers',marker=dict(size=8,color=cols),showlegend=False),1,j)
    for xb in [-1.96,1.96]: f.add_vline(x=xb,line=dict(color='#495057',dash='dash'),row=1,col=j)
    f.add_vline(x=0,line=dict(color='#111',width=1),row=1,col=j)
    f.update_xaxes(title='RCI',row=1,col=j,range=[-6,6])
f.update_layout(template='plotly_white',font=dict(color='#111',size=12,family='Arial'),paper_bgcolor='white',plot_bgcolor='white',
    height=720,width=1400,margin=dict(l=55,r=20,t=45,b=45))
f.write_image(f'{OUT}/x_rci.png',width=1500,height=780,scale=2)
print('fig x_rci OK')
