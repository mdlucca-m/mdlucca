import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
hum=pd.read_csv(f'{SC}/humor.csv'); phys=pd.read_csv(f'{SC}/phys.csv')
rng=np.random.default_rng(7)
VARS=['FadFisica','TMD','Vigor','Fadiga']
LAB={'FadFisica':'Fadiga física','TMD':'PTH/TMD','Vigor':'Vigor','Fadiga':'Fadiga (BRUMS)'}
NEG=['Tensao','Depressao','Raiva','Fadiga','Confusao']

# athlete attributes
posmap={'Meia':'Armador','Ponta':'Ala','Pivô':'Pivô','Goleiro':'Goleiro'}
phys['posg']=phys['pos'].map(posmap)
pv=phys.set_index('ID')['TCAR_PV_ini']
q1,q2=pv.quantile([1/3,2/3])
def tercil(x):
    if pd.isna(x): return None
    return 'Aptidão baixa' if x<=q1 else ('Aptidão alta' if x>q2 else 'Aptidão média')
apt=pv.map(tercil); posg=phys.set_index('ID')['posg']
hum=hum.merge(phys[['ID','posg']],on='ID',how='left'); hum['apt']=hum['ID'].map(apt)

# standardization for iceberg index (full sample)
zmu={v:hum[v].mean() for v in ['Vigor']+NEG}; zsd={v:hum[v].std() for v in ['Vigor']+NEG}
def zc(df,v): return (df[v]-zmu[v])/zsd[v]

def seg_ids(dim,seg):
    if seg=='Todos': return set(hum.ID.unique())
    if dim=='Aptidão': return set(apt[apt==seg].index)
    if dim=='Posição': return set(posg[posg==seg].index)
    return set(hum.ID.unique())

def dz_ci(sub,v):
    d1=sub[sub.dia==1].groupby('ID')[v].mean(); d7=sub[sub.dia==7].groupby('ID')[v].mean()
    j=pd.concat([d1,d7],axis=1,keys=['a','b']).dropna()
    if len(j)<4: return [None,None,None]
    d=j.b-j.a; dz=d.mean()/d.std(ddof=1)
    bs=[]
    for _ in range(1000):
        s=j.iloc[rng.choice(len(j),len(j),True)]; dd=s.b-s.a
        if dd.std(ddof=1)>0: bs.append(dd.mean()/dd.std(ddof=1))
    return [round(dz,2),round(np.percentile(bs,2.5),2),round(np.percentile(bs,97.5),2)]

def icc_trait(sub,v):
    g=sub.dropna(subset=[v]).groupby('ID')[v]; k=g.ngroups
    if k<3: return None
    N=sub[v].notna().sum(); ni=g.count(); n0=(N-(ni**2).sum()/N)/(k-1); gm=sub[v].mean()
    msb=(ni*(g.mean()-gm)**2).sum()/(k-1)
    msw=sub.dropna(subset=[v]).groupby('ID')[v].apply(lambda s:((s-s.mean())**2).sum()).sum()/(N-k)
    return round(max((msb-msw)/(msb+(n0-1)*msw),0),2)

def iceberg_pct(sub):
    out=[]
    for d in range(1,8):
        g=sub[sub.dia==d]
        if len(g)==0: out.append(None); continue
        neg=g[NEG].mean(axis=1); out.append(round(100*(g['Vigor']>neg).mean(),0))
    return out

def build_segment(dim,seg):
    ids=seg_ids(dim,seg); sub=hum[hum.ID.isin(ids)]
    traj={}
    for v in VARS:
        m=sub.groupby('dia')[v].mean().reindex(range(1,8))
        se=sub.groupby('dia')[v].sem().reindex(range(1,8))
        traj[v]={'mean':[None if pd.isna(x) else round(x,2) for x in m],
                 'se':[0 if pd.isna(x) else round(x,2) for x in se]}
    # iceberg index heatmap: athletes x day
    aids=sorted(ids)
    z=[]
    for aid in aids:
        row=[]
        for d in range(1,8):
            g=sub[(sub.ID==aid)&(sub.dia==d)]
            if len(g)==0: row.append(None)
            else:
                ic=(zc(g,'Vigor')-pd.concat([zc(g,n) for n in NEG],axis=1).mean(axis=1)).mean()
                row.append(round(float(ic),2))
        z.append(row)
    # between-athlete corr
    am=sub.groupby('ID')[VARS].mean(); C=am.corr().round(2).values.tolist()
    ib=iceberg_pct(sub)
    return {
        'n_ath':len(ids),'n_obs':int(len(sub)),
        'kpi':{
            'FadFisica_dz':dz_ci(sub,'FadFisica'),'Vigor_dz':dz_ci(sub,'Vigor'),
            'iceberg_d1':ib[0],'iceberg_d7':ib[6],
            'tmd_d7':round(sub[sub.dia==7]['TMD'].mean(),1) if len(sub[sub.dia==7]) else None,
            'icc_tmd':icc_trait(sub,'TMD'),
        },
        'traj':traj,'iceberg_by_day':ib,
        'heatmap':{'athletes':[f'A{i+1:02d}' for i in range(len(aids))],'z':z},
        'corr':{'labels':[LAB[v] for v in VARS],'z':C},
    }

DIMS={'Geral':['Todos'],'Aptidão':['Aptidão baixa','Aptidão média','Aptidão alta'],'Posição':['Armador','Ala','Pivô','Goleiro']}
segments={}
for dim,segs in DIMS.items():
    for seg in segs: segments[seg]=build_segment(dim,seg)

# segment comparison: dz D1->D7 by segment within each dimension
seg_compare={}
for dim in ['Aptidão','Posição']:
    d={'segments':DIMS[dim]}
    for v in VARS:
        d[v]=[segments[s]['kpi'][f'{v}_dz'][0] if f'{v}_dz' in segments[s]['kpi'] else
              dz_ci(hum[hum.ID.isin(seg_ids(dim,s))],v)[0] for s in DIMS[dim]]
    seg_compare[dim]=d
# add all VARS dz to each segment kpi for compare
for s in segments:
    pass

DATA={'dims':DIMS,'segments':segments,'seg_compare':seg_compare,'vars':VARS,'lab':LAB}
json.dump(DATA,open(f'{SC}/dash_data.json','w'),ensure_ascii=False)
print('segmentos:',list(segments.keys()))
print('exemplo Todos KPI:',segments['Todos']['kpi'])
print('exemplo Aptidão alta n_ath:',segments['Aptidão alta']['n_ath'],'dz FadFisica:',segments['Aptidão alta']['kpi']['FadFisica_dz'])
print('saved dash_data.json', round(len(json.dumps(DATA))/1024,1),'KB')
