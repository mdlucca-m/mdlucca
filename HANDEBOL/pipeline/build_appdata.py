#!/usr/bin/env python3
"""Gerador canônico do pacote de dados do Sistema Analista (BRUMS x HIIT).

Reconstrói appdata.json a cada coleta:
  - dados 'ao vivo' (records + meta) recomputados da base bruta;
  - carga interna (FC/PSE) recomputada da planilha HIIT_FC_PSE;
  - camada de modelo (precomp_seed.json) — resultados da amostra auditada completa.
Injeta o pacote no template e emite o HTML standalone do app.

Uso:  BRUMS_DATA_DIR=/pasta/xlsx python3 build_appdata.py [saida_dir]
"""
import os, sys, json, glob, unicodedata, re
import numpy as np, pandas as pd
from scipy import stats
import warnings; warnings.filterwarnings('ignore')

HERE=os.path.dirname(os.path.abspath(__file__))
DATA_DIR=os.environ.get('BRUMS_DATA_DIR', HERE)
OUT=sys.argv[1] if len(sys.argv)>1 else HERE

def _find(name):
    for p in glob.glob(os.path.join(DATA_DIR,'*'))+glob.glob(os.path.join(DATA_DIR,'**','*'),recursive=True):
        if p.lower().endswith(name.lower()) or os.path.basename(p).lower().endswith(name.lower()): return p
    hits=[p for p in glob.glob(os.path.join(DATA_DIR,'**','*.xlsx'),recursive=True) if name.split('.')[0].lower() in os.path.basename(p).lower()]
    return hits[0] if hits else None

def _num(v):
    if pd.isna(v): return np.nan
    m=re.search(r'-?\d+', str(v)); return float(m.group()) if m else np.nan
def norm(s):
    s=str(s).strip().lower(); s=''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')
    return ' '.join(s.split())

GROUPS={'Tensão':['Apavorado','Ansioso','Preocupado','Tenso'],
 'Depressão':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','Com Raiva','Mal-humorado'],
 'Vigor':['Animado','Com disposição','Com Energia','Alerta '],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],
 'Confusão':['Confuso','Inseguro','Desorientado','Indeciso']}
ITEMKEY={'Apavorado':'tensao_1','Ansioso':'tensao_2','Preocupado':'tensao_3','Tenso':'tensao_4',
 'Deprimido':'depressao_1','Desanimado':'depressao_2','Triste':'depressao_3','Infeliz':'depressao_4',
 'Irritado':'raiva_1','Zangado':'raiva_2','Com Raiva':'raiva_3','Mal-humorado':'raiva_4',
 'Animado':'vigor_1','Com disposição':'vigor_2','Com Energia':'vigor_3','Alerta ':'vigor_4',
 'Esgotado':'fadiga_1','Exausto':'fadiga_2','Sonolento':'fadiga_3','Cansado':'fadiga_4',
 'Confuso':'confusao_1','Inseguro':'confusao_2','Desorientado':'confusao_3','Indeciso':'confusao_4'}
ITEMNAMES=[n for g in GROUPS.values() for n in g]
ITEMKEYS=[ITEMKEY[n] for n in ITEMNAMES]

def load_brums():
    d=pd.read_excel(_find('COLETAS.xlsx'),sheet_name='Diario',header=0).reset_index(drop=True)
    B='Escala de Humor de Brunel (BRUMS) '
    X=pd.DataFrame()
    X['aid']=d['Nome'].map(norm); X['ts']=pd.to_datetime(d['Carimbo de data/hora'])
    X['day']=(X['ts'].dt.normalize()-pd.Timestamp('2024-04-20')).dt.days
    IT=pd.DataFrame({ITEMKEY[n]:d[B+'['+n+']'].map(_num) for g in GROUPS.values() for n in g})
    for s,g in GROUPS.items(): X[s]=IT[[ITEMKEY[n] for n in g]].sum(axis=1,min_count=4)
    X['PTH']=X[['Tensão','Depressão','Raiva','Fadiga','Confusão']].sum(axis=1)-X['Vigor']
    X['FadFis']=d['Qual seu nível de FADIGA FÍSICA no momento?'].map(_num)
    X['FadMen']=d['Qual seu nível de FADIGA MENTAL no momento?'].map(_num)
    em={'Péssimo':0,'Ruim':1,'Regular':2,'Bem':3,'Muito bem':4}
    X['EstFis']=d['Como você está se sentido agora fisicamente'].map(em)
    X['EstMen']=d['Como você está se sentido agora mentalmente'].map(em)
    X=pd.concat([X,IT],axis=1)
    M=X[X['day'].between(1,7)].copy().sort_values(['aid','day','ts']).reset_index(drop=True)
    M['moment']='Meio'
    f=M.groupby(['aid','day']).head(1).index; l=M.groupby(['aid','day']).tail(1).index
    cnt=M.groupby(['aid','day'])['ts'].transform('size')
    M.loc[f,'moment']='Pré'; M.loc[l,'moment']='Pós'; M.loc[cnt==1,'moment']='Único'
    M['hiit']=M['day'].isin([2,4,7])
    return M

def _v(x): return None if (x is None or (isinstance(x,float) and np.isnan(x))) else (round(float(x),4) if isinstance(x,(int,float,np.floating)) else x)

def build():
    M=load_brums()
    order=list(dict.fromkeys(M.sort_values('ts')['aid']))
    amap={a:f'A{i+1:02d}' for i,a in enumerate(order)}
    MOM={'Pré':'pre','Pós':'pos','Meio':'mid','Único':'uni'}
    subs=list(GROUPS.keys())
    records=[]
    for _,r in M.iterrows():
        rec={'a':amap[r['aid']],'d':int(r['day']),'m':MOM[r['moment']],'h':int(bool(r['hiit']))}
        for s in subs: rec[s]=_v(r[s])
        rec['PTH']=_v(r['PTH'])
        for k in ['FadFis','FadMen','EstFis','EstMen']: rec[k]=_v(r[k])
        rec['it']=[(None if pd.isna(r[k]) else int(r[k])) for k in ITEMKEYS]
        records.append(rec)
    meta={'subs':subs,'itemnames':ITEMNAMES,'itemkeys':ITEMKEYS,
          'groups':{s:[ITEMKEY[n] for n in g] for s,g in GROUPS.items()},
          'externals':['FadFis','FadMen','EstFis','EstMen'],
          'labels':{'FadFis':'Fadiga física','FadMen':'Fadiga mental','EstFis':'Estado físico','EstMen':'Estado mental','PTH':'PTH (TMD)'}}
    n=len(records); athletes=M['aid'].nunique(); pairs=int((M['moment']=='Pré').sum())

    # ---- carga interna (FC/PSE) recomputada ----
    carga=build_carga(M,amap)

    # ---- camada de modelo (amostra auditada completa) ----
    seed=json.load(open(os.path.join(HERE,'precomp_seed.json')))
    precomp=dict(seed); precomp['carga']=carga

    pkg={'meta':meta,'records':records,'precomp':precomp,'n':n,'athletes':int(athletes),'pairs':pairs}
    return pkg

def build_carga(M,amap):
    f=_find('HIIT_FC_PSE.xlsx')
    if not f: return None
    bc=pd.read_excel(f,sheet_name='Base Consolidada',header=0).dropna(subset=['Atleta']).copy()
    for c in ['FC Pré','FC Pós','ΔFC','PSE']: bc[c]=pd.to_numeric(bc[c],errors='coerce')
    bc['nm']=bc['Atleta'].map(norm)
    bn=set(amap.keys())
    def match(nm):
        if nm in amap: return amap[nm]
        t=nm.split()
        if not t: return None
        for b in bn:
            bt=b.split()
            if t[0]==bt[0] and t[-1]==bt[-1]: return amap[b]
        for b in bn:  # primeiro nome + >=2 tokens em comum
            if t[0]==b.split()[0] and len(set(t)&set(b.split()))>=2: return amap[b]
        return None
    names=list(dict.fromkeys(bc['nm'])); fcmap={}; matched=0
    for i,nm in enumerate(names):
        a=match(nm)
        if a: matched+=1
        fcmap[nm]=a if a else f'F{i+1:02d}'
    bc['a']=bc['nm'].map(fcmap)
    PH=['Aquecimento','Série 1','Série 2','Série 3','Série 4']; PS={'Aquecimento':'Aquec.','Série 1':'Sé1','Série 2':'Sé2','Série 3':'Sé3','Série 4':'Sé4'}
    SS=['S1','S2','S3','S4']
    def msd(x):
        x=pd.Series(x).dropna(); return [round(float(x.mean()),1),round(float(x.std()),1),int(x.notna().sum())] if len(x) else [None,None,0]
    byphase=[{'fase':PS[p],'fcpre':msd(bc[bc['Fase']==p]['FC Pré']),'fcpos':msd(bc[bc['Fase']==p]['FC Pós']),'dfc':msd(bc[bc['Fase']==p]['ΔFC']),'pse':msd(bc[bc['Fase']==p]['PSE'])} for p in PH]
    bysess=[]
    for s in SS:
        sub=bc[bc['Sessão']==s]; last=sub[sub['Fase']=='Série 4']
        peak=sub.groupby('a')['FC Pós'].max()  # FC de pico = máximo por atleta na sessão (não a média das fases)
        bysess.append({'sessao':s,'fcpos':msd(sub['FC Pós']),'pse':msd(sub['PSE']),'pse_final':msd(last['PSE']),'fcpico':msd(peak)})
    def paired(sub):
        p=sub.dropna(subset=['FC Pré','FC Pós'])
        if len(p)<3: return {}
        t,pv=stats.ttest_rel(p['FC Pós'],p['FC Pré']); dd=p['FC Pós']-p['FC Pré']
        return {'n':int(len(p)),'pre':round(float(p['FC Pré'].mean()),1),'pos':round(float(p['FC Pós'].mean()),1),'delta':round(float(dd.mean()),1),'t':round(float(t),2),'p':float(pv),'dz':round(float(dd.mean()/dd.std()),2) if dd.std()>0 else None}
    paired_all=paired(bc); paired_phase=[{'fase':PS[p],**paired(bc[bc['Fase']==p])} for p in PH]
    cc=bc.dropna(subset=['FC Pós','PSE']); r,pr=stats.pearsonr(cc['FC Pós'],cc['PSE'])
    drift=[]
    for s in SS:
        ss=bc[bc['Sessão']==s]; a=ss[ss['Fase']=='Aquecimento'].set_index('a')['FC Pós']; d4=ss[ss['Fase']=='Série 4'].set_index('a')['FC Pós']
        j=pd.concat([a.rename('aq'),d4.rename('s4')],axis=1).dropna()
        drift.append({'sessao':s,'drift':round(float((j['s4']-j['aq']).mean()),1) if len(j) else None,'n':int(len(j))})
    piv=bc[bc['Fase']=='Série 4'].pivot_table(index='a',columns='Sessão',values='PSE',aggfunc='mean').dropna()
    fried=None
    if piv.shape[0]>=3 and piv.shape[1]>=3:
        st,pv=stats.friedmanchisquare(*[piv[c] for c in piv.columns]); fried={'chi2':round(float(st),2),'p':float(pv),'n':int(piv.shape[0]),'k':int(piv.shape[1])}
    load_a={}
    for a,g in bc.groupby('a'):
        loads=[g[g['Sessão']==s]['PSE'].mean() for s in SS]; loads=[x for x in loads if pd.notna(x)]
        if len(loads)>=2:
            mn=np.mean(loads); sd=np.std(loads,ddof=1) if len(loads)>1 else 0; mono=mn/sd if sd>0 else np.nan
            load_a[a]={'load_total':round(float(np.sum(loads)),1),'monotony':round(float(mono),2) if pd.notna(mono) else None,'strain':round(float(np.sum(loads)*mono),1) if pd.notna(mono) else None}
    lm={'monotony':msd([v['monotony'] for v in load_a.values() if v['monotony'] is not None]),'strain':msd([v['strain'] for v in load_a.values() if v['strain'] is not None]),'load_total':msd([v['load_total'] for v in load_a.values()])}
    ath_pse={}
    for a,g in bc.groupby('a'):
        row={s:(round(float(g[g['Sessão']==s]['PSE'].mean()),1) if g[g['Sessão']==s]['PSE'].notna().any() else None) for s in SS}
        row['fcpos']=round(float(g['FC Pós'].mean()),0) if g['FC Pós'].notna().any() else None
        row['brums']=a if a.startswith('A') else None; ath_pse[a]=row
    # link carga x humor
    dpth={}
    for a,g in M[M['hiit']].groupby(M['aid'].map(amap)):
        ds=[]
        for d,gd in g.groupby('day'):
            pre=gd[gd['moment']=='Pré']['PTH']; pos=gd[gd['moment']=='Pós']['PTH']
            if len(pre) and len(pos): ds.append(float(pos.mean()-pre.mean()))
        if ds: dpth[a]=np.mean(ds)
    psea={a:np.mean([v for v in [ath_pse[a][s] for s in SS] if v is not None]) for a in ath_pse if a.startswith('A')}
    common=sorted(set(dpth)&set(psea)); link=None
    if len(common)>=5:
        xs=[psea[a] for a in common]; ys=[dpth[a] for a in common]; rr,pp=stats.pearsonr(xs,ys)
        link={'r':round(float(rr),2),'p':float(pp),'n':len(common),'pts':[[round(float(psea[a]),2),round(float(dpth[a]),2)] for a in common]}
    return {'n_ath':int(bc['a'].nunique()),'n_matched':int(matched),'n_obs':int(len(bc)),'phases':[PS[p] for p in PH],'sessions':SS,'byphase':byphase,'bysession':bysess,'paired_all':paired_all,'paired_phase':paired_phase,'corr_fcpse':{'r':round(float(r),2),'p':float(pr),'n':int(len(cc))},'drift':drift,'friedman_pse':fried,'load_summary':lm,'ath_pse':ath_pse,'link_humor':link}

def main():
    pkg=build()
    js=json.dumps(pkg,ensure_ascii=False,default=str)
    os.makedirs(OUT,exist_ok=True)
    open(os.path.join(OUT,'appdata.json'),'w').write(js)
    tpl=open(os.path.join(HERE,'analyst_template.html')).read()
    html=tpl.replace('%%DATA%%',js)
    open(os.path.join(OUT,'Sistema_Analista_BRUMS_HIIT.html'),'w').write(html)
    print('appdata.json: %d obs, %d atletas, %d pares'%(pkg['n'],pkg['athletes'],pkg['pairs']))
    print('carga: n_ath=%s matched=%s'%(pkg['precomp']['carga']['n_ath'],pkg['precomp']['carga']['n_matched']) if pkg['precomp'].get('carga') else 'carga: (sem FC/PSE)')
    print('HTML:', os.path.join(OUT,'Sistema_Analista_BRUMS_HIIT.html'))

if __name__=='__main__': main()
