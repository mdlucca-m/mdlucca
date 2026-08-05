import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json, openpyxl
from scipy import stats
SC='/tmp/claude-0/-home-user-mdlucca/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/scratchpad'
UP='/root/.claude/uploads/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a'
hum=pd.read_csv(f'{SC}/humor.csv'); phys=pd.read_csv(f'{SC}/phys.csv')
hr=pd.read_csv(f'{SC}/hr_series.csv'); ext=pd.read_csv(f'{SC}/ext_load.csv')
well=pd.read_csv(f'{SC}/wellness_all.csv')
rng=np.random.default_rng(11)

# ---------- socio ----------
wb=openpyxl.load_workbook(f'{UP}/789b3ee8-Avalia__es_Handebol_S_o_Jos__2024.xlsx', data_only=True)
soc=[]
for r in list(wb['Atletas'].iter_rows(values_only=True))[4:]:
    if r[0] and str(r[0]).startswith('A'):
        soc.append(dict(ID=r[0],idade=r[3],pos=r[4],estatura=r[6],massa=r[7],pG=r[8]))
soc=pd.DataFrame(soc)
exp={}
for r in list(wb['Caracterização (limpa)'].iter_rows(values_only=True))[4:]:
    if r[2] and str(r[2]).startswith('A'): exp[r[2]]=r[5]
soc['exp']=soc['ID'].map(exp)
posmap={'Meia':'Armador','Ponta':'Ala','Pivô':'Pivô','Goleiro':'Goleiro','Armador':'Armador'}
soc['posg']=soc['pos'].map(lambda x:posmap.get(x,x))
soc=soc.merge(phys[['ID','TCAR_PV_ini','CMJ_ini']],on='ID',how='left')
for c in ['idade','estatura','massa','pG','exp','TCAR_PV_ini','CMJ_ini']: soc[c]=pd.to_numeric(soc[c],errors='coerce')

def num(s): return [None if pd.isna(x) else round(float(x),2) for x in s]
SOCIO={
 'athletes':[{'id':r.ID,'idade':r.idade,'pos':r.posg,'exp':r.exp,'estatura':r.estatura,
              'massa':r.massa,'pG':r.pG,'PV':r.TCAR_PV_ini,'CMJ':r.CMJ_ini} for _,r in soc.iterrows()],
 'agg':{'idade':[round(soc.idade.mean(),1),round(soc.idade.std(),1),int(soc.idade.min()),int(soc.idade.max())],
        'exp':[round(soc.exp.mean(),1),round(soc.exp.std(),1)],
        'estatura':[round(soc.estatura.mean(),1),round(soc.estatura.std(),1)],
        'massa':[round(soc.massa.mean(),1),round(soc.massa.std(),1)],
        'pG':[round(soc.pG.mean(),1),round(soc.pG.std(),1)],
        'PV':[round(soc.TCAR_PV_ini.mean(),2),round(soc.TCAR_PV_ini.std(),2)]},
 'pos_counts':soc.posg.value_counts().to_dict(),
}

# ---------- variables ----------
NEG=['Tensao','Depressao','Raiva','Fadiga','Confusao']
ALLV=['FadFisica','Fadiga','Vigor','TMD','Tensao','Depressao','Raiva','Confusao','FadMental']
LAB={'FadFisica':'Fadiga física (0–10)','Fadiga':'Fadiga (BRUMS)','Vigor':'Vigor','TMD':'PTH/TMD',
     'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão','FadMental':'Fadiga mental'}

# session load by day (HIIT days)
S=['S1','S2','S3']; day_s={2:'S1',4:'S2',7:'S3'}
fc_day={2:hr[hr.sessao=='S1'].HRpico.mean(),4:hr[hr.sessao=='S2'].HRpico.mean(),7:hr[hr.sessao=='S3'].HRpico.mean()}
pse_day={2:hr[hr.sessao=='S1'].PSE.mean(),4:hr[hr.sessao=='S2'].PSE.mean(),7:hr[hr.sessao=='S3'].PSE.mean()}
pv_ath=phys.set_index('ID')['TCAR_PV_ini']; dist_ath=ext.set_index('ID')['dist_sessao']

def dz_paired(a,b):
    d=b-a; return round(d.mean()/d.std(ddof=1),2) if d.std(ddof=1)>0 else None
def acute_dz(v):
    tr=hum[hum.dia.isin([2,3,4,5,6,7])]; per=[]
    for aid,g in tr.groupby('ID'):
        ds=[]
        for dia,gd in g.groupby('dia'):
            gd=gd.sort_values('seq'); pre=gd[gd.momento=='pre'][v]; pos=gd[gd.momento=='pos'][v]
            if len(pre) and len(pos) and pd.notna(pre.iloc[0]) and pd.notna(pos.iloc[0]): ds.append(pos.iloc[0]-pre.iloc[0])
        if ds: per.append(np.mean(ds))
    per=np.array(per); return round(per.mean()/per.std(ddof=1),2) if per.std()>0 else None
def icc1(v):
    d=hum.dropna(subset=[v]); g=d.groupby('ID')[v]; k=g.ngroups; N=len(d)
    ni=g.count(); n0=(N-(ni**2).sum()/N)/(k-1); gm=d[v].mean()
    msb=(ni*(g.mean()-gm)**2).sum()/(k-1)
    msw=d.groupby('ID')[v].apply(lambda s:((s-s.mean())**2).sum()).sum()/(N-k)
    return round(max((msb-msw)/(msb+(n0-1)*msw),0),2)

VARDATA={}
for v in ALLV:
    s=hum[v].dropna()
    # histogram
    cnts,edges=np.histogram(s,bins=12)
    # group trajectory
    gm=hum.groupby('dia')[v].mean().reindex(range(1,8)); ge=hum.groupby('dia')[v].sem().reindex(range(1,8))
    # per-athlete daily
    piv=hum.pivot_table(index='ID',columns='dia',values=v,aggfunc='mean').reindex(columns=range(1,8))
    ath_ids=list(piv.index); ath_z=[[None if pd.isna(x) else round(float(x),2) for x in piv.loc[a]] for a in ath_ids]
    d1=hum[hum.dia==1].groupby('ID')[v].mean(); d7=hum[hum.dia==7].groupby('ID')[v].mean()
    j=pd.concat([d1,d7],axis=1,keys=['a','b']).dropna()
    # corr with others (spearman on obs)
    corr_o={}
    for o in ALLV:
        if o==v: continue
        dd=hum[[v,o]].dropna(); corr_o[o]=round(stats.spearmanr(dd[v],dd[o]).correlation,2)
    # vs internal load (athlete-day HIIT)
    hd=hum[hum.dia.isin([2,4,7])].groupby(['ID','dia'])[v].mean().reset_index()
    hd['FC']=hd['dia'].map(fc_day); hd['PSE']=hd['dia'].map(pse_day)
    rFC=round(stats.spearmanr(hd[v],hd['FC']).correlation,2)
    # vs fitness/external (athlete weekly)
    wk=hum.groupby('ID')[v].mean()
    mo=pd.concat([wk,pv_ath,dist_ath],axis=1,keys=[v,'PV','dist']).dropna()
    rPV=round(stats.spearmanr(mo[v],mo['PV']).correlation,2) if len(mo)>5 else None
    rDist=round(stats.spearmanr(mo[v],mo['dist']).correlation,2) if len(mo)>5 else None
    VARDATA[v]={
      'lab':LAB[v],
      'desc':{'mean':round(s.mean(),2),'sd':round(s.std(),2),'median':round(s.median(),2),
              'iqr':round(s.quantile(.75)-s.quantile(.25),2),'skew':round(s.skew(),2),
              'kurt':round(s.kurt(),2),'floor':round(100*(s==s.min()).mean(),1),
              'shapiro':round(stats.shapiro(s.sample(min(len(s),500),random_state=1)).pvalue,4),'n':int(len(s))},
      'hist':{'counts':cnts.tolist(),'edges':[round(x,2) for x in edges]},
      'traj':{'mean':num(gm),'se':[0 if pd.isna(x) else round(x,2) for x in ge]},
      'ath':{'ids':[f'A{i+1:02d}' for i in range(len(ath_ids))],'z':ath_z},
      'kpi':{'dz_week':dz_paired(j.a,j.b) if len(j)>3 else None,'dz_acute':acute_dz(v),
             'floor':round(100*(s==s.min()).mean(),1),'icc':icc1(v)},
      'corr_others':corr_o,
      'load':{'FC':{'x':num(hd['FC']),'y':num(hd[v]),'r':rFC},
              'PV':{'x':num(mo['PV']),'y':num(mo[v]),'r':rPV},
              'dist':{'x':num(mo['dist']),'y':num(mo[v]),'r':rDist}},
    }

# correlation matrix (all)
KEY=['FadFisica','Fadiga','Vigor','TMD','Tensao','Depressao','Raiva','Confusao']
CM=hum[KEY].corr(method='spearman').round(2)
CORRM={'labels':[LAB[k] for k in KEY],'z':CM.values.tolist()}

# internal load sessions
def banister(hm,hr0=60,hmax=195,D=16): r=(hm-hr0)/(hmax-hr0); return round(D*r*0.64*np.exp(1.92*r),1)
INTLOAD={'sessions':S,'FCpico':num([hr[hr.sessao==x].HRpico.mean() for x in S]),
         'FCmedia':num([hr[hr.sessao==x].HRmean.mean() for x in S]),
         'PSE':num([hr[hr.sessao==x].PSE.mean() for x in S]),
         'TRIMP':[banister(hr[hr.sessao==x].HRmean.mean()) for x in S],
         'sRPE':num([hr[hr.sessao==x].PSE.mean()*26 for x in S])}
# external load
e=ext[ext.vel_kmh>0]
EXTLOAD={'vel_mean':round(e.vel_kmh.mean(),2),'vel_sd':round(e.vel_kmh.std(),2),'vel_vals':num(e.vel_kmh),
         'dist_mean':round(e.dist_sessao.mean(),0),'dist_sd':round(e.dist_sessao.std(),0),'dist_vals':num(e.dist_sessao),
         'dist_total':round(e.dist_total3.mean(),0),'dist_total_sd':round(e.dist_total3.std(),0),
         'pv_dist':{'x':num(e.merge(phys[['ID','TCAR_PV_ini']],on='ID').TCAR_PV_ini),
                    'y':num(e.merge(phys[['ID','TCAR_PV_ini']],on='ID').dist_sessao)}}

# ---------- wellness (within-window means) ----------
wl=well.copy(); wl['date']=pd.to_datetime(wl['datadia'],errors='coerce')
wl=wl[(wl['date']>=pd.Timestamp(2024,4,21))&(wl['date']<=pd.Timestamp(2024,4,27))]
def ms(col): s=pd.to_numeric(wl[col],errors='coerce').dropna(); return {'mean':round(s.mean(),2),'sd':round(s.std(),2),'n':int(len(s))}
WELL={'TQR':dict(ms('TQR'),lab='Recuperação (TQR 6–20)',icon='🛌',range='6–20'),
      'Epworth':dict(ms('Epworth'),lab='Sonolência (Epworth 0–18)',icon='😴',range='0–18'),
      'PSS':dict(ms('PSS'),lab='Estresse percebido (PSS)',icon='⚡',range='0–56')}
# BRUMS week means (from desc) as overview + internal load summary
BRUMS_MEANS={v:{'mean':VARDATA[v]['desc']['mean'],'sd':VARDATA[v]['desc']['sd'],'lab':LAB[v]} for v in ALLV}
INT_SUMMARY={'FCpico':round(np.mean(INTLOAD['FCpico']),0),'PSE':round(np.mean(INTLOAD['PSE']),1),
             'TRIMP':round(np.mean(INTLOAD['TRIMP']),0),'sRPE':round(np.mean(INTLOAD['sRPE']),0)}
HIGHLIGHTS=[
 {'icon':'📈','v':'+1,74','l':'Acúmulo de fadiga física D1→D7 (dz)','d':'efeito muito grande · IC95% [1,32; 2,62]','c':'red'},
 {'icon':'📉','v':'−0,95','l':'Queda do vigor D1→D7 (dz)','d':'efeito grande','c':'blue'},
 {'icon':'🧊','v':'93% → 67%','l':'Perfil iceberg (D1 → D7)','d':'achatamento do perfil de humor','c':'org'},
 {'icon':'🎯','v':'AUC 0,86','l':'Discriminância do acúmulo (D7 vs D1)','d':'vs sessão de HIIT AUC≈0,50 → sinal na tendência','c':'grn'},
 {'icon':'❤️','v':'184 → 181','l':'FC de pico entre sessões de HIIT (bpm)','d':'cai enquanto a PSE sobe = fadiga acumulada','c':'red'},
 {'icon':'🔗','v':'ρ −0,54','l':'Aptidão (T-CAR) × fadiga da semana','d':'o mais apto fadiga menos (p=0,005)','c':'vio'},
]

# ---------- segmentation mapping (aligned to per-athlete pivot order) ----------
ath_order=list(hum.pivot_table(index='ID',columns='dia',values='FadFisica',aggfunc='mean').index)
pvq=phys.set_index('ID')['TCAR_PV_ini']; q1,q2=pvq.quantile([1/3,2/3])
def tercil(a):
    x=pvq.get(a,np.nan)
    if pd.isna(x): return None
    return 'Aptidão baixa' if x<=q1 else ('Aptidão alta' if x>q2 else 'Aptidão média')
posd=soc.set_index('ID')['posg'].to_dict()
SEG={'order_ids':[f'A{i+1:02d}' for i in range(len(ath_order))],
     'apt':[tercil(a) for a in ath_order],
     'pos':[posd.get(a) for a in ath_order],
     'dims':{'Aptidão':['Aptidão baixa','Aptidão média','Aptidão alta'],
             'Posição':['Armador','Ala','Pivô','Goleiro']}}

APP={'socio':SOCIO,'vars':VARDATA,'order':ALLV,'lab':LAB,'corr':CORRM,'intload':INTLOAD,'extload':EXTLOAD,'seg':SEG,
     'well':WELL,'brums_means':BRUMS_MEANS,'int_summary':INT_SUMMARY,'highlights':HIGHLIGHTS}
def conv(o):
    if isinstance(o,dict): return {k:conv(v) for k,v in o.items()}
    if isinstance(o,list): return [conv(x) for x in o]
    if isinstance(o,(np.floating,)): return float(o)
    if isinstance(o,(np.integer,)): return int(o)
    if isinstance(o,float) and (np.isnan(o)): return None
    return o
json.dump(conv(APP),open(f'{SC}/app_data.json','w'),ensure_ascii=False)
print('OK. vars:',len(VARDATA),'| socio athletes:',len(SOCIO['athletes']),'| size KB:',round(len(json.dumps(conv(APP)))/1024,1))
print('exemplo Fadiga kpi:',VARDATA['Fadiga']['kpi'],'| rFC=',VARDATA['Fadiga']['load']['FC']['r'],'rPV=',VARDATA['Fadiga']['load']['PV']['r'])
print('pos counts:',SOCIO['pos_counts'])
