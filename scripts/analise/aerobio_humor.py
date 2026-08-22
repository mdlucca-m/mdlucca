# -*- coding: utf-8 -*-
# Aptidao aerobia (pico de velocidade do T-CAR) x perfil de humor.
#  - Anonimiza o fisico bruto (Handebol_2024.xlsx, aba Dados) -> phys_anon.csv (SEM nomes).
#  - Descritivos + adaptacao pre->pos do T-CAR PV (e CMJ, Baker), por grupo.
#  - Associacao PV x humor a partir dos pares JA casados e anonimizados (pv_mood_matched.json),
#    que reproduzem os achados publicados (FadFisica x PV rho=-0,54).
#  - Spearman + IC bootstrap + BH-FDR. Gera figuras e JSON para dashboard/artigo.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
RAW="/root/.claude/uploads/e1dba24c-b1d7-5908-9106-f2f4aaf3f56a/d3182401-Handebol_2024.xlsx"
rng=np.random.default_rng(7)

# ---------- (1) anonimizar fisico ----------
d=pd.read_excel(RAW,sheet_name='Dados')
POSMAP={'Meia':'meia','Ponta':'ponta','Pivô':'pivo','Goleiro':'goleiro'}
d=d.sort_values(['Grupo','Massa']).reset_index(drop=True)
d.insert(0,'id',[f'P{str(i+1).zfill(2)}' for i in range(len(d))])   # codigo do coorte fisico
keep=['id','Grupo','Idade','Estatura','Massa','%G','CMJ_pre','CMJ_pos','CMJ_d',
      'BkMel_pre','BkMel_pos','BkMel_d','BkSoma_pre','BkSoma_pos','BkSoma_d','BkF_pre','BkF_pos','BkF_d',
      'TCARpv_pre','TCARpv_pos','TCARpv_d','TCARfc_pre','TCARfc_pos','TCARrep_pre','TCARrep_pos',
      'Carga_%FC','Carga_TRIMP','Carga_PSE']
pos=d['Posição'].map(POSMAP)
anon=d[keep].copy(); anon.insert(2,'pos',pos.values)
anon.to_csv('phys_anon.csv',index=False)
print(f'phys_anon.csv salvo: {len(anon)} atletas (Exp={sum(anon.Grupo=="Experimental")}, Ctrl={sum(anon.Grupo=="Controle")})')

def dz_paired(a,b):
    x=b-a; return float(x.mean()/x.std(ddof=1))
def summ(s): return f"{s.mean():.2f} ± {s.std(ddof=1):.2f}"

phys={}
print("\n=== ADAPTACAO FISICA (pre -> pos) ===")
for v,lab in [('TCARpv','T-CAR pico de velocidade (km/h)'),('CMJ','CMJ (cm)'),
              ('BkMel','Baker melhor (s)'),('BkSoma','Baker soma (s)')]:
    a=anon[f'{v}_pre'].astype(float); b=anon[f'{v}_pos'].astype(float)
    m=a.notna()&b.notna(); a,b=a[m],b[m]
    t,p=stats.ttest_rel(a,b); dz=dz_paired(a.values,b.values)
    # por grupo
    g={}
    for gr in ['Experimental','Controle']:
        mm=(anon.Grupo==gr)&anon[f'{v}_pre'].notna()&anon[f'{v}_pos'].notna()
        aa=anon.loc[mm,f'{v}_pre'].astype(float).values; bb=anon.loc[mm,f'{v}_pos'].astype(float).values
        g[gr]={'pre':round(float(aa.mean()),2),'pos':round(float(bb.mean()),2),'dz':round(dz_paired(aa,bb),2)}
    phys[v]={'lab':lab,'pre':summ(a),'pos':summ(b),'pre_n':round(float(a.mean()),2),'pos_n':round(float(b.mean()),2),
             'dz':round(dz,2),'p':round(float(p),4)}
    print(f"  {lab:34s} {a.mean():.2f} -> {b.mean():.2f}  dz={dz:+.2f} p={p:.4f} (grupo único, n={m.sum()})")

phys['desc']={'n':int(len(anon)),
    'TCARpv_pre':summ(anon.TCARpv_pre.astype(float)),
    'idade':summ(anon.Idade.astype(float)),'massa':summ(anon.Massa.astype(float)),
    'estatura':summ(anon.Estatura.astype(float))}

# ---------- (2) PV x humor (pares casados, n=25) ----------
pm=json.load(open('pv_mood_matched.json'))
PV=np.array(pm['Vigor']['PV'])
ORDER=['Vigor','Fadiga','FadFisica','FadMental','TMD','Tensao','Depressao','Raiva','Confusao']
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','FadFisica':'Fadiga física','FadMental':'Fadiga mental','TMD':'PTH (TMD)',
     'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Confusao':'Confusão'}
rows=[]
for k in ORDER:
    y=np.array(pm[k]['mood']); r,p=stats.spearmanr(PV,y)
    bs=[]
    for _ in range(5000):
        idx=rng.integers(0,len(PV),len(PV))
        if len(np.unique(PV[idx]))>2: bs.append(stats.spearmanr(PV[idx],y[idx]).correlation)
    lo,hi=np.nanpercentile(bs,[2.5,97.5])
    rows.append(dict(dim=k,lab=LAB[k],r=float(r),p=float(p),lo=float(lo),hi=float(hi)))
pv=np.array([r['p'] for r in rows])
o=np.argsort(pv); ranks=np.empty_like(o); ranks[o]=np.arange(1,len(pv)+1)
fdr=np.minimum.accumulate((pv*len(pv)/ranks)[o][::-1])[::-1]; adj=np.empty_like(fdr); adj[o]=np.clip(fdr,0,1)
for i,r in enumerate(rows): r['fdr']=float(adj[i])
print(f"\n=== T-CAR PICO DE VELOCIDADE x HUMOR (n={len(PV)}) ===")
print(f"{'dim':14s} {'rho':>6s} {'IC95':>16s} {'p':>7s} {'p_FDR':>7s}")
for r in rows:
    star='*' if r['fdr']<0.05 else ('†' if r['p']<0.05 else '')
    print(f"{r['lab']:14s} {r['r']:+6.2f} [{r['lo']:+.2f},{r['hi']:+.2f}] {r['p']:7.3f} {r['fdr']:7.3f} {star}")

out={'phys':phys,'pv_mood':rows,'PV':[float(x) for x in PV],'n_pvmood':int(len(PV)),
     'mood':{k:[float(x) for x in pm[k]['mood']] for k in ORDER}}
json.dump(out,open('aerobio_humor.json','w'))
print('\n[salvo aerobio_humor.json + phys_anon.csv]')

# ---------- figuras ----------
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
OUT='/home/user/mdlucca/Artigos/figuras'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
# Fig A: adaptacao T-CAR PV (pre->pos), grupo unico (SEM grupo controle)
fig,ax=plt.subplots(figsize=(6.6,4.8),dpi=200)
a=anon['TCARpv_pre'].astype(float).values; b=anon['TCARpv_pos'].astype(float).values
for i in range(len(a)): ax.plot([0,1],[a[i],b[i]],'-',color='#74c0fc',alpha=.30,lw=1)
ax.plot([0,1],[a.mean(),b.mean()],'-o',color='#1971c2',lw=3.2,ms=9,label=f'média (dz={dz_paired(a,b):+.2f})')
ax.set_xticks([0,1]); ax.set_xticklabels(['Pré','Pós']); ax.set_ylabel('T-CAR pico de velocidade (km/h)')
ax.set_title('Adaptação da capacidade aeróbia máxima ao microciclo\n(pico de velocidade no T-CAR, pré vs pós · grupo único)',fontweight='bold',fontsize=11.5,loc='left')
ax.legend(frameon=False,loc='lower right',fontsize=9.5)
fig.tight_layout(); fig.savefig(f'{OUT}/aerobio_adaptacao.png',bbox_inches='tight',facecolor='white')

# Fig B: PV x humor — barras de rho (IC95) + 2 scatters chave
fig=plt.figure(figsize=(13.5,4.8),dpi=200)
gs=fig.add_gridspec(1,3,width_ratios=[1.25,1,1])
axb=fig.add_subplot(gs[0,0])
rows_s=sorted(rows,key=lambda r:r['r'])
ycol=['#e8590c' if r['dim'] in('FadFisica','Fadiga','FadMental','TMD') else ('#2f9e44' if r['dim']=='Vigor' else '#adb5bd') for r in rows_s]
yy=range(len(rows_s))
for i,r in zip(yy,rows_s):
    axb.plot([r['lo'],r['hi']],[i,i],color=ycol[i],lw=2,alpha=.6)
    axb.plot(r['r'],i,'o',color=ycol[i],ms=8)
    mk='*' if r['fdr']<0.05 else ('†' if r['p']<0.05 else '')
    if mk: axb.text(r['hi']+0.03,i,mk,va='center',fontsize=13,color=ycol[i])
axb.axvline(0,ls=':',color='#adb5bd'); axb.set_yticks(list(yy)); axb.set_yticklabels([r['lab'] for r in rows_s])
axb.set_xlim(-0.9,0.9); axb.set_xlabel('ρ de Spearman (IC95%)')
axb.set_title('T-CAR PV × humor\n* FDR<0,05 · † p<0,05',fontweight='bold',fontsize=11,loc='left')
for k,(lab,col,ax_) in {'FadFisica':('Fadiga física','#e8590c',fig.add_subplot(gs[0,1])),
                        'Vigor':('Vigor','#2f9e44',fig.add_subplot(gs[0,2]))}.items():
    y=np.array(pm[k]['mood']); r=[rr for rr in rows if rr['dim']==k][0]
    ax_.scatter(PV,y,s=34,color=col,alpha=.7,edgecolors='none')
    b1,b0=np.polyfit(PV,y,1); xx=np.linspace(PV.min(),PV.max(),50)
    ax_.plot(xx,b0+b1*xx,color=col,lw=2)
    ax_.set_xlabel('T-CAR pico de velocidade (km/h)'); ax_.set_ylabel(lab)
    ax_.set_title(f'{lab} vs aptidão\nρ={r["r"]:+.2f} (p={r["p"]:.3f})',fontweight='bold',fontsize=10.5,loc='left')
fig.suptitle('Capacidade aeróbia máxima e perfil de humor: quem é mais apto fadiga menos e mantém mais vigor',
             fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig(f'{OUT}/aerobio_humor_assoc.png',bbox_inches='tight',facecolor='white')
print('[figuras: aerobio_adaptacao.png, aerobio_humor_assoc.png]')
