# -*- coding: utf-8 -*-
# (A) Decomposicao de variancia em 3 niveis (invariancia vs variacao):
#     - entre atletas  (intra-grupo; diferencas interindividuais)
#     - entre dias no mesmo atleta (intra-sujeito; flutuacao dia a dia)
#     - entre momentos no dia (intra-dia; residual pre/mid/pos)
# (B) Curva no nivel dos momentos: encadeia pos(d-1)->pre(d) (recuperacao noturna)
#     e pre(d)->pos(d) (efeito agudo do dia). Faz as curvas (sawtooth).
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import statsmodels.formula.api as smf
from scipy import stats
rng=np.random.default_rng(7)
S=['Vigor','Fadiga','TMD','FadFisica']
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','FadFisica':'Fadiga física'}
h=pd.read_csv('humor_anon.csv')
h['adia']=h['ID'].astype(str)+'_'+h['dia'].astype(str)

# ---------- (A) componentes de variancia ----------
print("=== DECOMPOSICAO DE VARIANCIA (% do total) ===")
print(f"{'dim':14s} {'atleta':>7s} {'dia':>7s} {'momento':>8s}  (intra-grupo / intra-sujeito / intra-dia)")
vc_rows=[]
for v in S:
    d=h[['ID','adia',v]].dropna().rename(columns={v:'y'})
    md=smf.mixedlm("y ~ 1", d, groups=d["ID"], re_formula="1", vc_formula={"dia":"0+C(adia)"})
    r=md.fit(reml=True)
    va=float(np.asarray(r.cov_re).ravel()[0])   # entre atletas
    vd=float(np.asarray(r.vcomp).ravel()[0]) if len(np.asarray(r.vcomp).ravel()) else 0.0  # entre dias no atleta
    ve=float(r.scale)                          # residual = intra-dia
    tot=va+vd+ve
    pa,pd_,pe=va/tot*100,vd/tot*100,ve/tot*100
    vc_rows.append(dict(dim=v,lab=LAB[v],atleta=round(pa,1),dia=round(pd_,1),momento=round(pe,1),
                        icc_atleta=round(va/tot,3)))
    print(f"{LAB[v]:14s} {pa:6.1f}% {pd_:6.1f}% {pe:7.1f}%")

# ---------- (B) curva pre/pos por dia + agudo e recuperacao ----------
def cell(df,dia,mom,v):
    x=df[(df.dia==dia)&(df.momento==mom)][v]; return x.mean() if len(x) else np.nan
# medias de grupo por dia
grp_pre={v:{d:h[(h.dia==d)&(h.momento=='pre')][v].mean() for d in range(1,8)} for v in S}
grp_pos={v:{d:h[(h.dia==d)&(h.momento=='pos')][v].mean() for d in range(1,8)} for v in S}
# efeitos por atleta: agudo pre->pos (mesmo dia) e recuperacao pos(d-1)->pre(d)
def effects(v):
    ag=[]; rec=[]
    for aid,g in h.groupby('ID'):
        gg=g.set_index(['dia','momento'])[v]
        for d in range(1,8):
            try: pre=gg.loc[(d,'pre')].mean(); pos=gg.loc[(d,'pos')].mean()
            except Exception: pre=pos=np.nan
            if pd.notna(pre) and pd.notna(pos): ag.append(pos-pre)
        for d in range(2,8):
            try: pprev=gg.loc[(d-1,'pos')].mean(); pren=gg.loc[(d,'pre')].mean()
            except Exception: pprev=pren=np.nan
            if pd.notna(pprev) and pd.notna(pren): rec.append(pren-pprev)
    ag=np.array(ag); rec=np.array(rec)
    return ag,rec
eff={}
print("\n=== AGUDO (pre->pos, mesmo dia) e RECUPERACAO (pos[d-1]->pre[d]) ===")
print(f"{'dim':14s} {'agudo M':>8s} {'ag dz':>6s} {'recup M':>8s} {'rec dz':>6s}")
for v in S:
    ag,rec=effects(v)
    agdz=ag.mean()/ag.std(ddof=1); recdz=rec.mean()/rec.std(ddof=1)
    eff[v]=dict(agudo=float(ag.mean()),agudo_dz=float(agdz),recup=float(rec.mean()),recup_dz=float(recdz))
    print(f"{LAB[v]:14s} {ag.mean():+8.2f} {agdz:+6.2f} {rec.mean():+8.2f} {recdz:+6.2f}")

# serie encadeada no nivel do momento (pre,pos alternados) para as curvas
def chain(v):
    xs=[]; ys=[]; lab=[]
    for d in range(1,8):
        pr=grp_pre[v][d]; po=grp_pos[v][d]
        if pd.notna(pr): xs.append(d-0.2); ys.append(float(pr)); lab.append(f'{d}pre')
        if pd.notna(po): xs.append(d+0.2); ys.append(float(po)); lab.append(f'{d}pos')
    return xs,ys,lab
curves={v:dict(zip(['x','y','lab'],chain(v))) for v in S}

out={'vc':vc_rows,'eff':eff,'curves':curves,
     'grp_pre':{v:[None if pd.isna(grp_pre[v][d]) else round(float(grp_pre[v][d]),2) for d in range(1,8)] for v in S},
     'grp_pos':{v:[None if pd.isna(grp_pos[v][d]) else round(float(grp_pos[v][d]),2) for d in range(1,8)] for v in S}}
json.dump(out,open('variancia_momentos.json','w'))

# ---------- figuras ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#7048e8','FadFisica':'#d9480f'}
fig,ax=plt.subplots(1,2,figsize=(13.5,4.8),dpi=200)
# A: componentes de variancia (barras empilhadas)
labs=[r['lab'] for r in vc_rows]; y=np.arange(len(labs))
at=[r['atleta'] for r in vc_rows]; di=[r['dia'] for r in vc_rows]; mo=[r['momento'] for r in vc_rows]
ax[0].barh(y,at,color='#1971c2',label='entre atletas (intra-grupo)')
ax[0].barh(y,di,left=at,color='#e8590c',label='entre dias (intra-sujeito)')
ax[0].barh(y,mo,left=np.array(at)+np.array(di),color='#adb5bd',label='intra-dia (momentos)')
ax[0].set_yticks(y); ax[0].set_yticklabels(labs); ax[0].set_xlabel('% da variância total'); ax[0].set_xlim(0,100)
ax[0].set_title('(A) Onde está a variância: invariância vs variação\ntrait (atleta) × estado (dia) × agudo (momento)',fontweight='bold',fontsize=10.5,loc='left')
ax[0].legend(frameon=False,fontsize=8.5,loc='lower right')
# B: curva encadeada pre/pos (vigor e fadiga)
for v in ['Vigor','Fadiga']:
    c=curves[v]; ax[1].plot(c['x'],c['y'],'-o',color=COL[v],lw=2,ms=5,label=LAB[v])
for d in [2,4,7]: ax[1].axvspan(d-0.35,d+0.35,color='#e8590c',alpha=.08)
ax[1].set_xticks(range(1,8)); ax[1].set_xlabel('dia (○ pré · ● pós encadeados) · faixas = HIIT'); ax[1].set_ylabel('escore')
ax[1].set_title('(B) Curva no nível dos momentos\npré→pós (agudo) e pós→pré (recuperação noturna)',fontweight='bold',fontsize=10.5,loc='left')
ax[1].legend(frameon=False,fontsize=9)
fig.suptitle('Variância (intra-grupo / intra-sujeito / intra-dia) e a curva agudo × recuperação',fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/variancia_momentos.png',bbox_inches='tight',facecolor='white')
print('\n[salvo variancia_momentos.json + figura]')
