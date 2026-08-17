import os; os.environ['BROWSER_PATH']='/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mdpi_style
OUT='/home/user/mdlucca/Artigos/figuras'
R=json.load(open('moduladores.json'))
h=pd.read_csv('hum_prof.csv'); phys=pd.read_csv('phys.csv'); F=pd.read_csv('tcar2_features.csv')[['ID','PVini','TRIMP']]
MODS=R['mods']; MODLAB=R['modlab']
HEXv={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#6741d9'}

f=make_subplots(rows=1,cols=2,horizontal_spacing=0.11,column_widths=[0.56,0.44],
    subplot_titles=['<b>Modulação da taxa semanal — coeficiente de determinação (R²)</b>',
                    '<b>Taxa de queda do vigor × potência (CMJ)</b>'])

# --- Painel A: R² de cada moderador sobre a inclinação de Vigor e Fadiga ---
short={'PVini':'Aptidão<br>(PV)','pGordura':'% gordura','massa':'Massa','CMJ_mai':'Potência<br>(CMJ)',
       'Baker_mai':'Sprints rep.<br>(Baker)','Epworth':'Sono<br>(Epworth)','PSS':'Estresse<br>(PSS)','TRIMP':'Carga<br>(TRIMP)'}
xlab=[short[m] for m in MODS]
for v in ['Vigor','Fadiga']:
    r2s=[R['chronic']['matrix'][v][m]['r2'] if R['chronic']['matrix'][v][m] else 0 for m in MODS]
    sig=[('*' if (R['chronic']['matrix'][v][m] and R['chronic']['matrix'][v][m]['p']<0.05) else '') for m in MODS]
    f.add_trace(go.Bar(x=xlab,y=r2s,name='Vigor (taxa)' if v=='Vigor' else 'Fadiga (taxa)',
        marker_color=HEXv[v],opacity=0.9,text=sig,textposition='outside',textfont=dict(size=16,color='#111')),1,1)
f.update_yaxes(title='R² (variância explicada)',range=[0,0.26],gridcolor='#eceef1',zeroline=False,row=1,col=1)
f.update_xaxes(tickfont=dict(size=11),row=1,col=1)

# --- Painel B: regressão sl_Vigor ~ CMJ (dispersão + reta + IC + R²) ---
dm=h.groupby(['ID','dia']).mean(numeric_only=True).reset_index()
def wslope(g,v):
    gg=g.dropna(subset=[v]); return stats.linregress(gg.dia,gg[v]).slope if gg.dia.nunique()>=4 else np.nan
sl=dm.groupby('ID').apply(lambda g: wslope(g,'Vigor')).rename('slV')
D=pd.concat([sl,phys.set_index('ID')['CMJ_mai']],axis=1).dropna()
x=D.CMJ_mai.values; y=D.slV.values
lr=stats.linregress(x,y); xx=np.linspace(x.min(),x.max(),100); yy=lr.intercept+lr.slope*xx
# IC95% da reta
n=len(x); se=np.sqrt(np.sum((y-(lr.intercept+lr.slope*x))**2)/(n-2))
sxx=np.sum((x-x.mean())**2); ci=1.96*se*np.sqrt(1/n+(xx-x.mean())**2/sxx)
f.add_trace(go.Scatter(x=np.r_[xx,xx[::-1]],y=np.r_[yy+ci,(yy-ci)[::-1]],fill='toself',
    fillcolor='rgba(47,158,68,0.14)',line=dict(width=0),showlegend=False,hoverinfo='skip'),1,2)
f.add_trace(go.Scatter(x=xx,y=yy,mode='lines',line=dict(color='#2f9e44',width=5),showlegend=False),1,2)
f.add_trace(go.Scatter(x=x,y=y,mode='markers',marker=dict(size=11,color='#2f9e44',opacity=0.8,
    line=dict(color='white',width=1.3)),showlegend=False),1,2)
f.add_annotation(x=0.04,y=0.06,xref='x2 domain',yref='y2 domain',showarrow=False,xanchor='left',
    text='R² = %s · r = %s · p = %s'%(('%.2f'%lr.rvalue**2).replace('.',','),('%+.2f'%lr.rvalue).replace('.',','),('%.3f'%lr.pvalue).replace('.',',')),
    font=dict(size=14,color='#1a1a1a'),bgcolor='rgba(255,255,255,0.8)')
f.update_xaxes(title='Potência de MMII — salto CMJ (cm)',gridcolor='#eceef1',zeroline=False,row=1,col=2)
f.update_yaxes(title='Taxa de variação do vigor (pontos/dia)',gridcolor='#eceef1',zeroline=False,row=1,col=2)

f.update_layout(template='mdpi',font=dict(color='#1a1a1a',size=15,family='Arial'),
    paper_bgcolor='white',plot_bgcolor='white',margin=dict(l=60,r=22,t=58,b=60),barmode='group',
    legend=dict(orientation='h',y=1.13,x=0.27,xanchor='center',font=dict(size=12)))
f.write_image(f'{OUT}/moduladores.png',width=1560,height=600,scale=3)
print('OK moduladores.png')
