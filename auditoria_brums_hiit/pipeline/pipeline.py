#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline automatizado (estilo N8N) — Estudo BRUMS × HIIT no handebol.
Cada 'nó' é uma etapa encadeada: ingestão → análises → gráficos → relatório.
Uso:
    BRUMS_DATA_DIR=/caminho/xlsx  python3 pipeline.py            # roda tudo
    python3 pipeline.py --only ingest,descriptives              # roda nós específicos
    python3 pipeline.py --list                                  # lista os nós
Saídas: pipe/tables/*.csv, pipe/charts/*.png, pipe/manifest.json, pipe/summary.md
"""
import os, sys, json, warnings, argparse, unicodedata, re
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd
from scipy import stats, integrate
BASE=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(BASE,'pipe'); TAB=os.path.join(OUT,'tables'); CH=os.path.join(OUT,'charts')
for d in (OUT,TAB,CH): os.makedirs(d,exist_ok=True)
DATA=os.environ.get('BRUMS_DATA_DIR', '/root/.claude/uploads/be05edff-5e11-5b0e-96b8-3aa1f3635d62/')
def _find(sub):
    import glob
    g=glob.glob(os.path.join(DATA,'*'+sub))
    return g[0] if g else os.path.join(DATA,sub)
COLETAS=_find('COLETAS.xlsx'); FCPSE=_find('HIIT_FC_PSE.xlsx')
PALE=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
GROUPS={'Tensão':['Apavorado','Ansioso','Preocupado','Tenso'],'Depressão':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','Com Raiva','Mal-humorado'],'Vigor':['Animado','Com disposição','Com Energia','Alerta '],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],'Confusão':['Confuso','Inseguro','Desorientado','Indeciso']}
SUBS=list(GROUPS)

def _num(s):
    def f(v):
        if pd.isna(v): return np.nan
        m=re.search(r'-?\d+',str(v)); return float(m.group()) if m else np.nan
    return s.map(f)
def _norm(s):
    s=str(s).strip().lower(); s=''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn'); return ' '.join(s.split())

# ---------------- NODES ----------------
def node_ingest(ctx):
    d=pd.read_excel(COLETAS,sheet_name='Diario',header=0).reset_index(drop=True)
    B='Escala de Humor de Brunel (BRUMS) '
    X=pd.DataFrame(); X['aid']=d['Nome'].map(_norm); X['ts']=pd.to_datetime(d['Carimbo de data/hora'])
    X['day']=(X['ts'].dt.normalize()-pd.Timestamp('2024-04-20')).dt.days
    ITEMS={}
    for s,g in GROUPS.items():
        cols=[_num(d[B+'['+n+']']) for n in g]
        for n,col in zip(g,cols): ITEMS[s+'::'+n]=col
        X[s]=pd.concat(cols,axis=1).sum(axis=1,min_count=4)
    for k,v in ITEMS.items(): X[k]=v
    X['PTH']=X[['Tensão','Depressão','Raiva','Fadiga','Confusão']].sum(axis=1)-X['Vigor']
    X['FadFis']=_num(d['Qual seu nível de FADIGA FÍSICA no momento?']); X['FadMen']=_num(d['Qual seu nível de FADIGA MENTAL no momento?'])
    em={'Péssimo':0,'Ruim':1,'Regular':2,'Bem':3,'Muito bem':4}
    X['EstFis']=d['Como você está se sentido agora fisicamente'].map(em); X['EstMen']=d['Como você está se sentido agora mentalmente'].map(em)
    M=X[X['day'].between(1,7)].copy().sort_values(['aid','day','ts']).reset_index(drop=True)
    M['moment']='Meio'; f=M.groupby(['aid','day']).head(1).index; l=M.groupby(['aid','day']).tail(1).index
    c=M.groupby(['aid','day'])['ts'].transform('size'); M.loc[f,'moment']='Pré'; M.loc[l,'moment']='Pós'; M.loc[c==1,'moment']='Único'
    M['hiit']=M['day'].isin([2,4,7])
    ctx['M']=M; M.to_csv(os.path.join(TAB,'00_base_limpa.csv'),index=False)
    return dict(rows=len(M),athletes=int(M['aid'].nunique()),pairs=int((M.moment=='Pré').sum()))

def node_descriptives(ctx):
    M=ctx['M']; rows=[]
    for k in ['PTH','Vigor','Fadiga','Tensão','Depressão','Raiva','Confusão','FadFis','FadMen']:
        x=M[k].dropna(); q1,q3=np.percentile(x,[25,75])
        rows.append(dict(var=k,media=round(x.mean(),2),dp=round(x.std(ddof=1),2),mediana=round(x.median(),1),
            IQR=round(q3-q1,1),assimetria=round(stats.skew(x),2),curtose=round(stats.kurtosis(x),2),piso_pct=round(100*(x==0).mean(),1)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'01_descritivas.csv'),index=False); return dict(vars=len(rows))

def node_reliability(ctx):
    M=ctx['M']; rows=[]
    for s,g in GROUPS.items():
        cols=[s+'::'+n for n in g]; Xg=M[cols].dropna(); k=len(cols)
        a=k/(k-1)*(1-Xg.var(ddof=1).sum()/Xg.sum(axis=1).var(ddof=1))
        cc=Xg.corr().values; rii=cc[np.triu_indices(k,1)].mean()
        rows.append(dict(subescala=s,alpha=round(a,3),r_inter_item=round(rii,3)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'02_confiabilidade.csv'),index=False); return dict(subs=len(rows))

def node_correlations(ctx):
    M=ctx['M']; ext=['FadFis','FadMen','EstFis','EstMen']; out=[]
    for s in SUBS:
        row={'subescala':s}
        for e in ext:
            m=M[[s,e]].dropna(); row[e]=round(m[s].corr(m[e]),2)
        out.append(row)
    pd.DataFrame(out).to_csv(os.path.join(TAB,'03_correlacoes.csv'),index=False); return dict(ok=True)

def node_day_effect(ctx):
    M=ctx['M']; vars_=['FadFis','Fadiga','PTH','Vigor']; rows=[]
    for v in vars_:
        ts=M.groupby(['aid','day'])[v].mean().groupby('day').mean(); obs=M.groupby('day')[v].mean()
        rows.append(dict(var=v,**{f'D{d}_2passos':round(ts.get(d,np.nan),2) for d in range(1,8)}))
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'04_medias_diarias.csv'),index=False)
    M['iceberg']=(M['Vigor']>M[['Tensão','Depressão','Raiva','Fadiga','Confusão']].max(axis=1)).astype(int)
    ice=(M.groupby('day')['iceberg'].mean()*100).round(1); ice.to_csv(os.path.join(TAB,'04b_iceberg.csv'))
    ctx['iceberg']=ice; return dict(iceberg_D1=float(ice.get(1)),iceberg_D7=float(ice.get(7)))

def node_acute(ctx):
    M=ctx['M']; pre=M[M.moment=='Pré']; pos=M[M.moment=='Pós']; pr=pre.merge(pos,on=['aid','day'],suffixes=('_pre','_pos'))
    from statsmodels.stats.multitest import multipletests
    vlist=['FadFis','Fadiga','PTH','Vigor','FadMen','Depressão','Tensão','Raiva','Confusão']; rows=[]; pv=[]
    for v in vlist:
        dl=(pr[v+'_pos']-pr[v+'_pre']).dropna(); dz=dl.mean()/dl.std(ddof=1); t,p=stats.ttest_1samp(dl,0)
        rows.append(dict(var=v,delta=round(dl.mean(),2),dz=round(dz,2),p=p)); pv.append(p)
    _,pf,_,_=multipletests(pv,method='fdr_bh')
    for r,p in zip(rows,pf): r['p_FDR']=round(p,3); r['p']=round(r['p'],4)
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'05_resposta_aguda.csv'),index=False)
    ctx['acute']=pd.DataFrame(rows); return dict(fadfis_dz=rows[0]['dz'])

def node_hiit(ctx):
    M=ctx['M']; tr=M[M.day.between(2,7)]; vars_=SUBS+['PTH','FadFis','FadMen']
    h=tr[tr.hiit].groupby('aid')[vars_].mean().mean(); nh=tr[~tr.hiit].groupby('aid')[vars_].mean().mean()
    pd.DataFrame(dict(var=vars_,HIIT=h[vars_].round(2).values,semHIIT=nh[vars_].round(2).values,dif=(h[vars_]-nh[vars_]).round(2).values)).to_csv(os.path.join(TAB,'06_hiit_vs_sem.csv'),index=False)
    return dict(dPTH=round(float(h['PTH']-nh['PTH']),2))

def node_multivariate(ctx):
    M=ctx['M']; pre=M[M.moment=='Pré']; pos=M[M.moment=='Pós']; pr=pre.merge(pos,on=['aid','day'],suffixes=('_pre','_pos')); prt=pr[pr.day.between(2,7)]
    def hot(cols):
        dd=pd.DataFrame({c:(prt[c+'_pos']-prt[c+'_pre']) for c in cols}); dd['aid']=prt['aid'].values
        a=dd.groupby('aid')[cols].mean().dropna(); n=len(a); p=len(cols); m=a.mean().values; S=np.cov(a.values.T)
        T2=n*m@np.linalg.inv(S)@m; F=(n-p)/(p*(n-1))*T2; pv=1-stats.f.cdf(F,p,n-p); D=np.sqrt(m@np.linalg.inv(S)@m)
        return round(F,2),round(pv,3),round(D,2),f'({p},{n-p})'
    r6=hot(SUBS); r2=hot(['Vigor','Fadiga'])
    pd.DataFrame([dict(conjunto='6 subescalas',F=r6[0],df=r6[3],p=r6[1],D=r6[2]),
                  dict(conjunto='Vigor+Fadiga',F=r2[0],df=r2[3],p=r2[1],D=r2[2])]).to_csv(os.path.join(TAB,'07_multivariada.csv'),index=False)
    return dict(hotelling6_F=r6[0],hotelling6_p=r6[1])

def node_variance(ctx):
    M=ctx['M']; import statsmodels.formula.api as smf; rows=[]
    for s in SUBS:
        dat=M[['aid','day',s]].dropna().rename(columns={s:'y'}); dat['adk']=dat.aid.astype(str)+'_'+dat.day.astype(str)
        md=smf.mixedlm("y~1",dat,groups=dat['aid'],re_formula="1",vc_formula={"day":"0+C(adk)"}).fit(reml=True)
        va,vd,ve=md.cov_re.iloc[0,0],md.vcomp[0],md.scale; tot=va+vd+ve
        rows.append(dict(subescala=s,traco_pct=round(100*va/tot,1),dia_pct=round(100*vd/tot,1),estado_pct=round(100*ve/tot,1)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'08_variancia.csv'),index=False); return dict(ok=True)

def node_complementary(ctx):
    M=ctx['M']; rng=np.random.RandomState(7)
    d1=M[M.day==1].groupby('aid')[['FadFis','Fadiga','Vigor','PTH']].mean(); d7=M[M.day==7].groupby('aid')[['FadFis','Fadiga','Vigor','PTH']].mean()
    b=d1.join(d7,lsuffix='_1',rsuffix='_7').dropna(); rows=[]
    for v in ['FadFis','Fadiga','Vigor','PTH']:
        dl=(b[v+'_7']-b[v+'_1']).values; dz=dl.mean()/dl.std(ddof=1)
        bs=[np.mean(dl[rng.randint(0,len(dl),len(dl))]) for _ in range(2000)]; lo,hi=np.percentile(bs,[2.5,97.5])
        rows.append(dict(var=v,delta=round(dl.mean(),2),dz=round(dz,2),ic_lo=round(lo,2),ic_hi=round(hi,2)))
    pd.DataFrame(rows).to_csv(os.path.join(TAB,'09_mudanca_semanal.csv'),index=False)
    # cluster
    from sklearn.preprocessing import StandardScaler; from sklearn.cluster import KMeans
    prof=M.groupby('aid')[SUBS].mean(); Z=StandardScaler().fit_transform(prof); km=KMeans(3,n_init=20,random_state=1).fit(Z)
    import collections; sz=collections.Counter(km.labels_)
    pd.DataFrame([dict(cluster=int(k),n=int(sz[k])) for k in sz]).to_csv(os.path.join(TAB,'10_tipologia.csv'),index=False)
    # network
    Xc=M[SUBS].dropna(); C=np.corrcoef(Xc.values.T); P=np.linalg.inv(C); pc=-P/np.sqrt(np.outer(np.diag(P),np.diag(P))); np.fill_diagonal(pc,0)
    strg=np.abs(pc).sum(1); pd.DataFrame(dict(subescala=SUBS,forca=strg.round(2))).sort_values('forca',ascending=False).to_csv(os.path.join(TAB,'11_rede.csv'),index=False)
    ctx['weekly']=pd.DataFrame(rows); return dict(cluster_sizes={str(int(k)):int(v) for k,v in sz.items()},weekly_fadfis_dz=rows[0]["dz"])

def node_charts(ctx):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    M=ctx['M']; P=PALE; dd=list(range(1,8)); made=[]
    def sty(ax):
        for s in['top','right']: ax.spines[s].set_visible(False)
        ax.tick_params(colors=P['MUT']); ax.grid(axis='y',color=P['GRID'],lw=1); ax.set_axisbelow(True)
    # trajectory
    fig,ax=plt.subplots(figsize=(6.6,4),dpi=170)
    for hd in[2,4,7]: ax.axvspan(hd-.35,hd+.35,color='#FBEAE8',lw=0)
    for v,c in [('FadFis',P['RED']),('Fadiga',P['GOLD']),('Vigor',P['TEAL']),('PTH',P['VIO'])]:
        y=[M.groupby(['aid','day'])[v].mean().groupby('day').mean().get(d,np.nan) for d in dd]; ax.plot(dd,y,'-o',color=c,lw=2.6,label=v)
    sty(ax); ax.set_xticks(dd); ax.legend(frameon=False,ncol=2,fontsize=9); fig.tight_layout(); fig.savefig(f'{CH}/trajetoria.png',facecolor='white'); plt.close(); made.append('trajetoria')
    # floor
    fig,ax=plt.subplots(figsize=(6,3.8),dpi=170)
    fl=[(s,100*(M[s]==0).mean()) for s in ['Confusão','Depressão','Raiva','Tensão','Vigor','Fadiga']]+[('FadFis',100*(M['FadFis']==0).mean())]
    fl=sorted(fl,key=lambda t:t[1]); ax.barh([f[0] for f in fl],[f[1] for f in fl],color=[P['RED'] if f[1]>=40 else P['TEAL'] for f in fl])
    ax.set_xlabel('% no piso'); [ax.spines[s].set_visible(False) for s in['top','right']]; fig.tight_layout(); fig.savefig(f'{CH}/efeito_piso.png',facecolor='white'); plt.close(); made.append('efeito_piso')
    # acute dz
    a=ctx.get('acute'); 
    if a is not None:
        fig,ax=plt.subplots(figsize=(6.4,4),dpi=170); y=np.arange(len(a))[::-1]
        ax.barh(y,a['dz'],color=[P['RED'] if v>=0 else P['TEAL'] for v in a['dz']]); ax.set_yticks(y); ax.set_yticklabels(a['var']); ax.axvline(0,color=P['MUT']); ax.set_xlabel('dz')
        [ax.spines[s].set_visible(False) for s in['top','right','left']]; fig.tight_layout(); fig.savefig(f'{CH}/resposta_aguda.png',facecolor='white'); plt.close(); made.append('resposta_aguda')
    # iceberg
    ice=ctx.get('iceberg'); 
    if ice is not None:
        fig,ax=plt.subplots(figsize=(6,3.6),dpi=170); yv=[ice.get(d,np.nan) for d in dd]
        for hd in[2,4,7]: ax.axvspan(hd-.35,hd+.35,color='#FBEAE8',lw=0)
        ax.fill_between(dd,yv,color=P['TEAL'],alpha=.18); ax.plot(dd,yv,'-o',color=P['TEAL'],lw=2.6); sty(ax); ax.set_xticks(dd); ax.set_ylabel('% iceberg')
        fig.tight_layout(); fig.savefig(f'{CH}/iceberg.png',facecolor='white'); plt.close(); made.append('iceberg')
    # weekly change
    w=ctx.get('weekly')
    if w is not None:
        fig,ax=plt.subplots(figsize=(6,3.4),dpi=170); y=np.arange(len(w))[::-1]
        for yi,(_,r) in zip(y,w.iterrows()):
            c=P['RED'] if r['dz']>=0 else P['TEAL']; ax.plot([r['ic_lo'],r['ic_hi']],[yi,yi],color=c,lw=2.2,alpha=.5); ax.plot(r['dz'],yi,'o',color=c,ms=9)
        ax.set_yticks(y); ax.set_yticklabels(w['var']); ax.axvline(0,color=P['MUT']); ax.set_xlabel('dz D1→D7 (IC95%)')
        [ax.spines[s].set_visible(False) for s in['top','right','left']]; fig.tight_layout(); fig.savefig(f'{CH}/mudanca_semanal.png',facecolor='white'); plt.close(); made.append('mudanca_semanal')
    return dict(charts=made)

def node_report(ctx):
    man=ctx['_manifest']; 
    lines=['# Pipeline BRUMS × HIIT — sumário de execução\n']
    for n in man: lines.append(f"- **{n['node']}** — {n['status']} — {json.dumps(n['result'],ensure_ascii=False)}")
    lines.append('\n## Tabelas geradas'); 
    for f in sorted(os.listdir(TAB)): lines.append(f"- tables/{f}")
    lines.append('\n## Gráficos gerados')
    for f in sorted(os.listdir(CH)): lines.append(f"- charts/{f}")
    open(os.path.join(OUT,'summary.md'),'w').write('\n'.join(lines))
    return dict(tables=len(os.listdir(TAB)),charts=len(os.listdir(CH)))

# reliability needs items -> add items to base in ingest
def _patch_items():
    pass

NODES=[('ingest',node_ingest),('descriptives',node_descriptives),('reliability',node_reliability),
('correlations',node_correlations),('day_effect',node_day_effect),('acute',node_acute),('hiit',node_hiit),
('multivariate',node_multivariate),('variance',node_variance),('complementary',node_complementary),
('charts',node_charts),('report',node_report)]

def _cols(s): return None
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--only'); ap.add_argument('--list',action='store_true'); a=ap.parse_args()
    if a.list:
        for n,_ in NODES: print(n); return
    sel=set(a.only.split(',')) if a.only else None
    ctx={}; manifest=[]; ctx['_manifest']=manifest
    for name,fn in NODES:
        if sel and name not in sel and name not in('ingest','report'): continue
        try:
            res=fn(ctx); manifest.append(dict(node=name,status='OK',result=res)); print(f"[OK] {name}: {res}")
        except Exception as e:
            manifest.append(dict(node=name,status='ERRO',result=str(e))); print(f"[ERRO] {name}: {e}")
    json.dump(manifest,open(os.path.join(OUT,'manifest.json'),'w'),ensure_ascii=False,indent=2,default=str)
if __name__=='__main__': main()
