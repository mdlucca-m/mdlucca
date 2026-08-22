# -*- coding: utf-8 -*-
# (A) Limites e DERIVADAS separando dias com HIIT (2,4,7) e sem HIIT (1,3,5,6):
#     velocidade (1a derivada discreta) e aceleracao do humor ao ENTRAR em dia de HIIT
#     vs em dia de recuperacao; pareado por atleta.
# (B) LIMIARES do pico de velocidade do T-CAR (faixas de aptidao) e relacao com o humor.
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
rng=np.random.default_rng(7)
S=['Vigor','Fadiga','TMD','FadFisica']
LAB={'Vigor':'Vigor','Fadiga':'Fadiga','TMD':'PTH','FadFisica':'Fadiga física'}
HIITD=[2,4,7]

# ================= (A) derivadas por HIIT =================
h=pd.read_csv('humor_anon.csv')
day=h.groupby(['ID','dia'])[['Vigor','Fadiga','TMD','FadFisica']].mean().reset_index()
# velocidade por atleta: v_d = mean_d - mean_{d-1}, d=2..7 ; rotulo = HIIT do dia d
def vel_series(g,v):
    s=g.set_index('dia')[v].reindex(range(1,8))
    return {d: s[d]-s[d-1] for d in range(2,8) if pd.notna(s[d]) and pd.notna(s[d-1])}
velA={v:{'hiit':[],'rest':[]} for v in S}
for aid,g in day.groupby('ID'):
    for v in S:
        vv=vel_series(g,v)
        hh=[vv[d] for d in vv if d in HIITD]; rr=[vv[d] for d in vv if d not in HIITD]
        if hh: velA[v]['hiit'].append(np.mean(hh))
        if rr: velA[v]['rest'].append(np.mean(rr))
rowsA=[]
for v in S:
    hh=np.array(velA[v]['hiit']); rr=np.array(velA[v]['rest'])
    n=min(len(hh),len(rr)); hh,rr=hh[:n],rr[:n]
    dif=hh-rr; dz=dif.mean()/dif.std(ddof=1)
    try: w,p=stats.wilcoxon(hh,rr)
    except Exception: p=np.nan
    rowsA.append(dict(dim=v,lab=LAB[v],v_hiit=float(hh.mean()),v_rest=float(rr.mean()),dz=float(dz),p=float(p)))
# velocidade e aceleracao no nivel do grupo (para a curva)
grp=day.groupby('dia')[S].mean().reindex(range(1,8))
velG={v:{d: float(grp[v][d]-grp[v][d-1]) for d in range(2,8)} for v in S}
accG={v:{d: float(velG[v][d]-velG[v][d-1]) for d in range(3,8)} for v in S}

print("=== (A) DERIVADA (velocidade) ENTRANDO EM DIA DE HIIT vs RECUPERACAO ===")
print(f"{'dim':14s} {'v_HIIT':>7s} {'v_rest':>7s} {'dz':>6s} {'p':>7s}")
for r in rowsA:
    print(f"{r['lab']:14s} {r['v_hiit']:+7.2f} {r['v_rest']:+7.2f} {r['dz']:+6.2f} {r['p']:7.3f}")

# ================= (B) limiares do pico de velocidade =================
pm=json.load(open('pv_mood_matched.json'))
PV=np.array(pm['Vigor']['PV'])
MOOD={k:np.array(pm[k]['mood']) for k in ['Vigor','Fadiga','FadFisica','TMD']}
med=float(np.median(PV))
t1,t2=np.quantile(PV,[1/3,2/3])
def cmp_thr(mask_hi,mask_lo,y):
    a=y[mask_hi]; b=y[mask_lo]
    dz=(a.mean()-b.mean())/np.sqrt(((a.std(ddof=1)**2)+(b.std(ddof=1)**2))/2)
    try: u,p=stats.mannwhitneyu(a,b)
    except Exception: p=np.nan
    return float(a.mean()),float(b.mean()),float(dz),float(p)
print(f"\n=== (B) LIMIAR DO PICO DE VELOCIDADE (mediana={med:.1f} km/h; tercis={t1:.1f}/{t2:.1f}) ===")
hi=PV>=med; lo=PV<med
rowsB=[]
for k in ['Vigor','Fadiga','FadFisica','TMD']:
    ah,al,dz,p=cmp_thr(hi,lo,MOOD[k])
    rowsB.append(dict(dim=k,lab=LAB[k],hi=ah,lo=al,dz=dz,p=p))
    print(f"  {LAB[k]:14s} PV<{med:.1f}: {al:.2f} | PV>={med:.1f}: {ah:.2f} | dz={dz:+.2f} p={p:.3f}")
# tercis para a curva (perfil por faixa)
band=np.where(PV<t1,0,np.where(PV<t2,1,2))
bands={k:[float(MOOD[k][band==b].mean()) for b in range(3)] for k in ['Vigor','Fadiga','FadFisica','TMD']}
bandn=[int((band==b).sum()) for b in range(3)]
print(f"  tercis n={bandn}  (baixo/medio/alto PV)")

out={'derivHIIT':{'rows':rowsA,'velG':velG,'accG':accG,'hiit_days':HIITD,'grp':{v:[float(grp[v][d]) for d in range(1,8)] for v in S}},
     'limiarPV':{'rows':rowsB,'median':med,'tertiles':[float(t1),float(t2)],'bands':bands,'band_n':bandn,'PV':[float(x) for x in PV],'mood':{k:[float(x) for x in MOOD[k]] for k in MOOD}}}
json.dump(out,open('hiit_deriv_limiar.json','w'))

# ================= figura =================
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,'axes.spines.right':False})
COL={'Vigor':'#2f9e44','Fadiga':'#e8590c','TMD':'#7048e8','FadFisica':'#d9480f'}
fig,ax=plt.subplots(1,3,figsize=(15,4.6),dpi=200)
# 1: velocidade ao longo da semana com HIIT sombreado
for v in ['Vigor','Fadiga']:
    xs=list(range(2,8)); ys=[velG[v][d] for d in xs]
    ax[0].plot(xs,ys,'-o',color=COL[v],lw=2.4,label=v)
for d in HIITD: ax[0].axvspan(d-0.5,d+0.5,color='#e8590c',alpha=.10)
ax[0].axhline(0,color='#adb5bd',lw=.8); ax[0].set_xlabel('dia (transição d−1 → d)'); ax[0].set_ylabel('velocidade (Δ/dia)')
ax[0].set_title('(A) Velocidade do humor · dias de HIIT sombreados\nfadiga acelera ao entrar no HIIT; recupera fora',fontweight='bold',fontsize=10.5,loc='left'); ax[0].legend(frameon=False,fontsize=9)
# 2: velocidade HIIT-entry vs rest-entry (barras pareadas)
x=np.arange(len(rowsA)); w=0.38
ax[1].bar(x-w/2,[r['v_rest'] for r in rowsA],w,label='entra em recuperação',color='#adb5bd')
ax[1].bar(x+w/2,[r['v_hiit'] for r in rowsA],w,label='entra em dia de HIIT',color='#e8590c')
ax[1].axhline(0,color='#adb5bd',lw=.8); ax[1].set_xticks(x); ax[1].set_xticklabels([r['lab'] for r in rowsA],fontsize=9)
ax[1].set_ylabel('velocidade média (Δ/dia)')
for i,r in enumerate(rowsA):
    if r['p']<0.05: ax[1].text(i+w/2,r['v_hiit']+(0.05 if r['v_hiit']>=0 else -0.12),'†',ha='center',fontsize=13,color='#e8590c')
ax[1].set_title('(A) Derivada: entrar no HIIT vs recuperar\n† p<0,05 (pareado por atleta)',fontweight='bold',fontsize=10.5,loc='left'); ax[1].legend(frameon=False,fontsize=8.5)
# 3: limiar PV — perfil por tercil
xs=[0,1,2]
for v in ['Vigor','Fadiga','FadFisica']:
    ax[2].plot(xs,bands[v],'-o',color=COL[v],lw=2.4,label=LAB[v])
ax[2].set_xticks(xs); ax[2].set_xticklabels([f'baixo\n(n={bandn[0]})',f'médio\n(n={bandn[1]})',f'alto\n(n={bandn[2]})'])
ax[2].set_xlabel('faixa de pico de velocidade (T-CAR)'); ax[2].set_ylabel('escore médio semanal')
ax[2].set_title('(B) Limiar do PV × humor\nmais apto → menos fadiga, mais vigor',fontweight='bold',fontsize=10.5,loc='left'); ax[2].legend(frameon=False,fontsize=9)
fig.suptitle('Derivadas por dia de HIIT e limiares do pico de velocidade na relação com o humor',fontweight='bold',fontsize=12.5,y=1.03)
fig.tight_layout(); fig.savefig('/home/user/mdlucca/Artigos/figuras/hiit_deriv_limiar.png',bbox_inches='tight',facecolor='white')
print('\n[salvo hiit_deriv_limiar.json + figura]')
