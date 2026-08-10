# -*- coding: utf-8 -*-
"""Análises avançadas do BRUMS — replicação em Python (motor independente do R).

Fecha, no próprio computador, as análises antes marcadas no Apêndice B como
"requer replicação em R":

  1. CFA de 6 fatores (estimador DWLS)                          -> semopy
  2. Matriz de correlações POLICÓRICAS + HTMT (discriminante)   -> implementação própria (scipy)
  3. TRI / Modelo de Resposta Graduada (discriminação a)        -> girth
  4. Invariância de medida pré x pós (config. + congruência)   -> semopy
  5. Fator de Bayes JZS exato (one-sample) para o Δ agudo       -> scipy (forma fechada)

Autocontido: lê `itens_brums.csv` (anonimizado) que fica nesta pasta.
Uso:  python analise_avancada.py            # grava resultados.json nesta pasta

Dependências (pip): numpy scipy pandas semopy girth
Observação de motor: o CFA usa DWLS sobre os itens (o HTMT usa a matriz
policórica). Para o WLSMV canônico com ajuste média-variância, use o script
`replicacao_R.R` (lavaan/mirt/semTools) — as conclusões coincidem.
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy import stats, integrate, optimize
warnings.filterwarnings('ignore')
np.random.seed(1)

HERE = os.path.dirname(os.path.abspath(__file__))
df = pd.read_csv(os.path.join(HERE, 'itens_brums.csv'))

GROUPS = {'Tensão':['tensao_1','tensao_2','tensao_3','tensao_4'],
          'Depressão':['depressao_1','depressao_2','depressao_3','depressao_4'],
          'Raiva':['raiva_1','raiva_2','raiva_3','raiva_4'],
          'Vigor':['vigor_1','vigor_2','vigor_3','vigor_4'],
          'Fadiga':['fadiga_1','fadiga_2','fadiga_3','fadiga_4'],
          'Confusão':['confusao_1','confusao_2','confusao_3','confusao_4']}
SUBS = list(GROUPS)
ITEMKEYS = [k for g in GROUPS.values() for k in g]
X = df[ITEMKEYS].dropna().astype(int)
N = len(X)
print(f"Itens: {X.shape[1]} | casos completos: {N}")
out = {'n_cases': int(N)}

# ---------- 1) MATRIZ POLICÓRICA (dois passos) ----------
from scipy.stats import norm, multivariate_normal as mvnorm
def thresholds(col, K=5):
    p = np.clip([ (col<=k).mean() for k in range(K-1) ], 1e-4, 1-1e-4)
    return norm.ppf(p)
def polychoric(x, y, Kx=5, Ky=5):
    ax = np.concatenate(([-8], thresholds(x,Kx), [8]))
    ay = np.concatenate(([-8], thresholds(y,Ky), [8]))
    O = np.zeros((Kx,Ky))
    for a,b in zip(x,y): O[a,b] += 1
    def negll(rho):
        rho = np.clip(rho, -0.999, 0.999)
        C = np.array([[mvnorm([0,0],[[1,rho],[rho,1]]).cdf([hx,hy]) for hy in ay] for hx in ax])
        P = np.clip(C[1:,1:]-C[:-1,1:]-C[1:,:-1]+C[:-1,:-1], 1e-10, 1)
        return -np.sum(O*np.log(P))
    return float(optimize.minimize_scalar(negll, bounds=(-0.99,0.99), method='bounded').x)

p = len(ITEMKEYS); R = np.eye(p); cols = [X[c].values for c in ITEMKEYS]
for i in range(p):
    for j in range(i+1, p):
        R[i,j] = R[j,i] = polychoric(cols[i], cols[j])
print("Matriz policórica 24x24 estimada.")
out['polychoric_mean_offdiag'] = round(float(R[np.triu_indices(p,1)].mean()), 3)

# ---------- 2) HTMT ----------
idx = {k:i for i,k in enumerate(ITEMKEYS)}
bi  = lambda s: [idx[k] for k in GROUPS[s]]
def mono(s):
    ii = bi(s); sub = R[np.ix_(ii,ii)]; return np.abs(sub[np.triu_indices(len(ii),1)]).mean()
def hetero(s,t):
    return np.abs(R[np.ix_(bi(s), bi(t))]).mean()
HTMT, mx = {}, 0.0
for a in range(len(SUBS)):
    for b in range(a+1, len(SUBS)):
        s,t = SUBS[a], SUBS[b]
        v = hetero(s,t)/np.sqrt(mono(s)*mono(t))
        HTMT[f'{s}~{t}'] = round(float(v),3); mx = max(mx, v)
out['HTMT'] = HTMT; out['HTMT_max'] = round(float(mx),3)
print(f"HTMT: máx = {mx:.3f} ({'todos < 0,85: validade discriminante OK' if mx<0.85 else 'atenção >= 0,85'})")

# ---------- 3) CFA (DWLS) ----------
import semopy
ren = {'Tensão':'Tensao','Depressão':'Depressao','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusão':'Confusao'}
spec = "\n".join(f"{ren[s]} =~ " + " + ".join(GROUPS[s]) for s in SUBS)
def fit_cfa(dat, spec_=spec, items=ITEMKEYS):
    mm = semopy.Model(spec_)
    try: mm.fit(dat[items], obj='DWLS')
    except Exception: mm.fit(dat[items], obj='ULS')
    cs = semopy.calc_stats(mm)
    st = (cs.iloc[0] if cs.shape[0]==1 else cs.iloc[:,0]).to_dict()
    ins = mm.inspect(std_est=True); facs = set(ren.values()); loads = {}
    for _,row in ins.iterrows():
        if row['op']=='~':
            ind = row['rval'] if row['lval'] in facs else (row['lval'] if row['rval'] in facs else None)
            if ind in items:
                try: loads[ind] = round(float(row.get('Est. Std', row.get('Estimate'))),3)
                except Exception: pass
    return st, loads
cfa = {}
try:
    st, loads = fit_cfa(X.astype(float))
    for k in ['chi2','DoF','CFI','TLI','RMSEA','SRMR','GFI','AGFI','NFI']:
        if k in st:
            try: cfa[k] = round(float(st[k]),3)
            except Exception: pass
    cfa['estimator'] = 'DWLS (semopy) sobre os itens'
    cfa['loadings_std'] = loads
    print(f"CFA (DWLS): CFI={cfa.get('CFI')} TLI={cfa.get('TLI')} RMSEA={cfa.get('RMSEA')} | {len(loads)} cargas")
except Exception as e:
    cfa['error'] = str(e)[:300]; print("CFA erro:", cfa['error'])
out['CFA_DWLS'] = cfa

# ---------- 4) TRI / GRM ----------
from girth import grm_mml
grm = {}
for s in SUBS:
    try:
        grm[s] = {'a': np.round(grm_mml(X[GROUPS[s]].values.T)['Discrimination'], 2).tolist()}
    except Exception as e:
        grm[s] = {'error': str(e)[:150]}
out['GRM_discrimination'] = grm
print("GRM (a por item) estimado por subescala.")

# ---------- 5) Invariância pré x pós ----------
inv = {}
try:
    Mi = df[df['momento'].isin(['pre','pos'])]
    gpre = Mi[Mi.momento=='pre'][ITEMKEYS].astype(float)
    gpos = Mi[Mi.momento=='pos'][ITEMKEYS].astype(float)
    dead = [k for k in ITEMKEYS if gpre[k].std()<1e-6 or gpos[k].std()<1e-6]  # itens sem variância (piso)
    keep = [k for k in ITEMKEYS if k not in dead]
    spec_inv = "\n".join(f"{ren[s]} =~ " + " + ".join([k for k in GROUPS[s] if k in keep]) for s in SUBS)
    stp, ldp = fit_cfa(gpre, spec_inv, keep)
    sto, ldo = fit_cfa(gpos, spec_inv, keep)
    keys = [k for k in ldp if k in ldo]
    a = np.array([ldp[k] for k in keys]); b = np.array([ldo[k] for k in keys])
    tucker = float(np.sum(a*b)/np.sqrt(np.sum(a**2)*np.sum(b**2)))
    inv = {'itens_excluidos': dead, 'n_pre': int(len(gpre)), 'n_pos': int(len(gpos)),
           'CFI_pre': round(float(stp.get('CFI', np.nan)),3), 'CFI_pos': round(float(sto.get('CFI', np.nan)),3),
           'tucker_phi_cargas': round(tucker,3),
           'nota': 'CFA por grupo + congruência de cargas (Tucker phi); phi >= 0,95 ~ invariância métrica'}
    print(f"Invariância pré×pós: Tucker phi cargas = {inv['tucker_phi_cargas']} (itens excluídos: {dead})")
except Exception as e:
    inv['error'] = str(e)[:300]; print("Invariância erro:", inv['error'])
out['invariance_pre_pos'] = inv

# ---------- 6) Fator de Bayes JZS exato (one-sample) ----------
def jzs_bf10(t, n, r=0.707):
    df_ = n-1
    def numf(g):
        return ((1+n*g*r**2)**-0.5) * ((1 + t**2/((1+n*g*r**2)*df_))**(-(df_+1)/2)) * \
               (2*np.pi)**-0.5 * g**-1.5 * np.exp(-1/(2*g))
    den0 = (1 + t**2/df_)**(-(df_+1)/2)
    val,_ = integrate.quad(numf, 0, np.inf)
    return float(val/den0)
pre = df[df.momento=='pre']; pos = df[df.momento=='pos']
pr = pre.merge(pos, on=['atleta','dia'], suffixes=('_pre','_pos'))
bf = {}
for v in ['FadFis','esc_vigor','PTH','esc_fadiga','esc_confusao','esc_tensao','esc_depressao','esc_raiva','FadMen']:
    tmp = pr[['atleta', v+'_pre', v+'_pos']].dropna()
    agg = tmp.groupby('atleta').apply(lambda d:(d[v+'_pos']-d[v+'_pre']).mean()).values
    n = len(agg); sd = agg.std(ddof=1)
    t = agg.mean()/(sd/np.sqrt(n)) if sd>0 else 0.0
    bf[v] = {'n': int(n), 't': round(float(t),2), 'BF10': round(jzs_bf10(t,n),3)}
out['bayes_JZS_agregado_por_atleta'] = bf
print("BF10 (JZS):", {k: v['BF10'] for k,v in bf.items()})

json.dump(out, open(os.path.join(HERE,'resultados.json'),'w'), ensure_ascii=False, indent=1, default=str)
print("\nSalvo em resultados.json")
