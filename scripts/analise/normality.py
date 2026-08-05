import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv'); phys=pd.read_csv(f'{SC}/phys.csv'); ext=pd.read_csv(f'{SC}/ext_load.csv')
well=pd.read_csv(f'{SC}/wellness_all.csv'); well['date']=pd.to_datetime(well['datadia'],errors='coerce')
wl=well[(well['date']>=pd.Timestamp(2024,4,21))&(well['date']<=pd.Timestamp(2024,4,27))]
out=[];
def p(*a): out.append(' '.join(str(x) for x in a)); print(*a)

def normtest(s):
    s=pd.to_numeric(s,errors='coerce').dropna().values
    if len(s)<8: return None
    W,pw=stats.shapiro(s[:5000])
    try: k2,pk=stats.normaltest(s)
    except: pk=np.nan
    sk=stats.skew(s); ku=stats.kurtosis(s)
    normal = (pw>0.05) and (abs(sk)<1)
    return dict(n=len(s),W=round(W,3),shapiro_p=pw,dagostino_p=pk,skew=round(sk,2),kurt=round(ku,2),normal=bool(normal))

LAB={'FadFisica':'Fadiga física','Fadiga':'Fadiga (BRUMS)','Vigor':'Vigor','TMD':'PTH/TMD','Tensao':'Tensão',
     'Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão','FadMental':'Fadiga mental',
     'TQR':'Recuperação (TQR)','Epworth':'Sonolência (Epworth)','PSS':'Estresse (PSS)',
     'vel_kmh':'Velocidade (104%PV)','dist_sessao':'Distância/sessão','TCAR_PV_ini':'T-CAR PV','CMJ_ini':'CMJ','massa':'Massa','estatura':'Estatura'}

p("="*90)
p("NORMALIDADE — DISTRIBUIÇÃO BRUTA (nível de observação/atleta)")
p("="*90)
p(f"{'Variável':22s} {'n':>4s} {'W':>6s} {'Shapiro p':>10s} {'Assim.':>7s} {'Curt.':>7s}  {'Normal?':>8s}  Família")
rows=[]
# mood (pooled obs)
for v in ['Vigor','Fadiga','FadFisica','FadMental','TMD','Tensao','Depressao','Raiva','Confusao']:
    r=normtest(hum[v]); r['var']=v; r['level']='obs'; rows.append(r)
# wellness (pooled obs)
for v in ['TQR','Epworth','PSS']:
    r=normtest(wl[v]); r['var']=v; r['level']='obs'; rows.append(r)
# load / socio (athlete level)
for df,v in [(ext,'vel_kmh'),(ext,'dist_sessao'),(phys,'TCAR_PV_ini'),(phys,'CMJ_ini'),(phys,'massa'),(phys,'estatura')]:
    s=df[v];
    if v in ('vel_kmh','dist_sessao'): s=df[df['vel_kmh']>0][v] if 'vel_kmh' in df else s
    r=normtest(s); r['var']=v; r['level']='atleta'; rows.append(r)
for r in rows:
    fam='paramétrica' if r['normal'] else 'NÃO PARAMÉTRICA'
    p(f"{LAB[r['var']]:22s} {r['n']:>4d} {r['W']:>6.3f} {r['shapiro_p']:>10.2e} {r['skew']:>7.2f} {r['kurt']:>7.2f}  {'sim' if r['normal'] else 'NÃO':>8s}  {fam}")

p("\n"+"="*90)
p("NORMALIDADE — ESCORES DE MUDANÇA POR ATLETA (D7−D1) — base dos testes pareados")
p("="*90)
p(f"{'Variável':22s} {'n':>4s} {'W':>6s} {'Shapiro p':>10s} {'Assim.':>7s}  {'Normal?':>8s}  Teste pareado recomendado")
rows2=[]
for v in ['Vigor','Fadiga','FadFisica','FadMental','TMD','Tensao','Depressao','Raiva','Confusao']:
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    j=pd.concat([d1,d7],axis=1,keys=['a','b']).dropna(); delta=(j.b-j.a)
    r=normtest(delta);
    if r: r['var']=v; rows2.append(r)

for r in rows2:
    test='t pareado (ok)' if r['normal'] else 'Wilcoxon (não paramétrico)'
    p(f"{LAB[r['var']]:22s} {r['n']:>4d} {r['W']:>6.3f} {r['shapiro_p']:>10.2e} {r['skew']:>7.2f}  {'sim' if r['normal'] else 'NÃO':>8s}  {test}")

# summary
nn_obs=sum(1 for r in rows if not r['normal']); nn_ch=sum(1 for r in rows2 if not r['normal'])
p("\n"+"="*90)
p("DECISÃO ANALÍTICA")
p("="*90)
p(f"Distribuição: {nn_obs}/{len(rows)} variáveis NÃO normais.")
p(f"Mudança por atleta: {nn_ch}/{len(rows2)} variáveis NÃO normais.")
p("→ Rota adotada: NÃO PARAMÉTRICA para as variáveis de humor/bem-estar")
p("   (mediana/IQR; Spearman; Wilcoxon/Mann-Whitney; Kruskal-Wallis; PERMANOVA; bootstrap).")
p("   Variáveis contínuas normais (aptidão/antropometria) podem usar via paramétrica.")

# save JSON for app
def conv(o):
    if isinstance(o,dict): return {k:conv(v) for k,v in o.items()}
    if isinstance(o,list): return [conv(x) for x in o]
    if isinstance(o,(np.floating,)): return float(o)
    if isinstance(o,(np.integer,)): return int(o)
    if isinstance(o,(np.bool_,)): return bool(o)
    return o
# qq data for a few key vars
qq={}
for v in ['Vigor','FadFisica','TMD','Depressao','vel_kmh']:
    s=(hum[v] if v in hum else ext[ext.vel_kmh>0][v]).dropna().values
    s=np.sort(s); n=len(s); theo=stats.norm.ppf((np.arange(1,n+1)-0.5)/n)
    # standardize sample
    ss=(s-s.mean())/s.std()
    qq[v]={'theo':[round(float(x),3) for x in theo],'samp':[round(float(x),3) for x in ss],'lab':LAB[v]}
NORM={'dist':[{'var':r['var'],'lab':LAB[r['var']],'level':r['level'],'n':r['n'],'W':r['W'],
              'p':r['shapiro_p'],'skew':r['skew'],'kurt':r['kurt'],'normal':r['normal']} for r in rows],
      'change':[{'var':r['var'],'lab':LAB[r['var']],'n':r['n'],'W':r['W'],'p':r['shapiro_p'],'skew':r['skew'],'normal':r['normal']} for r in rows2],
      'qq':qq,'summary':{'nn_obs':nn_obs,'tot_obs':len(rows),'nn_ch':nn_ch,'tot_ch':len(rows2)}}
json.dump(conv(NORM),open(f'{SC}/norm_data.json','w'),ensure_ascii=False)
open(f'{SC}/res_norm.txt','w').write('\n'.join(out)); print('\n[saved norm_data.json, res_norm.txt]')
