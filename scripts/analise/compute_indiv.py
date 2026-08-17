import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
h=pd.read_csv(SC+'/hum_prof.csv')
dm=h.groupby(['ID','dia'])[['Vigor','Fadiga','TMD']].mean().reset_index()

# ===== 1) MODELAGEM POR ATLETA: inclinação linear individual ao longo da semana =====
R={'perath':{},'slopes':{}}
for v,exp in [('Vigor','neg'),('Fadiga','pos'),('TMD','pos')]:
    sl=[]; ncub=0
    for aid,g in dm.groupby('ID'):
        g=g.sort_values('dia')
        if g['dia'].nunique()>=2: sl.append(float(stats.linregress(g['dia'],g[v]).slope))
        if g['dia'].nunique()>=4: ncub+=1
    sl=np.array(sl)
    resp=100*(sl<0).mean() if exp=='neg' else 100*(sl>0).mean()
    R['perath'][v]=dict(n=int(len(sl)),mean=float(sl.mean()),sd=float(sl.std(ddof=1)),
        mn=float(sl.min()),mx=float(sl.max()),resp_pct=float(resp),n_cub=int(ncub))
    R['slopes'][v]=[float(x) for x in sl]
n7=int((dm.groupby('ID')['dia'].nunique()>=7).sum()); n4=int((dm.groupby('ID')['dia'].nunique()>=4).sum())
R['cover']=dict(n7=n7,n4=n4,ntot=int(dm['ID'].nunique()))

# ===== 2) CURVA DE 13 PONTOS: baseline + pré/pós de cada dia de treino =====
# ordem cronológica: D1 baseline; D2 pré, D2 pós; ...; D7 pré, D7 pós
order=[(1,'baseline')]+[ (d,m) for d in range(2,8) for m in ('pre','pos') ]
lab13=[]; V=[]; F=[]; T=[]; nobs=[]
for d,m in order:
    sub=h[(h.dia==d)&(h.momento==m)]
    if len(sub)==0: continue
    lab13.append('D%d %s'%(d, {'baseline':'base','pre':'pré','pos':'pós'}[m]))
    V.append(float(sub['Vigor'].mean())); F.append(float(sub['Fadiga'].mean())); T.append(float(sub['TMD'].mean())); nobs.append(int(len(sub)))
R['pts13']=dict(lab=lab13,Vigor=V,Fadiga=F,TMD=T,nobs=nobs,npts=len(lab13))
json.dump(R,open(SC+'/indiv.json','w'),indent=1,ensure_ascii=False)

print('=== POR ATLETA (inclinação individual/dia) ===')
for v in ['Vigor','Fadiga','TMD']:
    a=R['perath'][v]; print('  %-6s média=%+.2f/d (DP %.2f) | %.0f%% na direção esperada | cúbica p/ %d atletas'%(
        v,a['mean'],a['sd'],a['resp_pct'],a['n_cub']))
print('  Cobertura: %d/%d com 7 dias; %d/%d com >=4 dias'%(R['cover']['n7'],R['cover']['ntot'],R['cover']['n4'],R['cover']['ntot']))
print('\n=== CURVA DE 13 PONTOS (grupo) ===')
print('  pontos:', R['pts13']['npts'], '| Vigor:', [round(x,1) for x in V])
print('  labels:', lab13)
