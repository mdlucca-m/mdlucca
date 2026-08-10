# -*- coding: utf-8 -*-
"""Modelagem estatística completa — BRUMS × HIIT.

Ajusta, de forma reproduzível, todos os modelos inferenciais do estudo, sempre
com o ATLETA como unidade (efeitos aleatórios) — corrigindo a pseudorreplicação
que é o ponto metodológico central do trabalho:

  A. Resposta aguda pré→pós      — modelo misto (intercepto aleat.) + FDR
  B. Efeito do dia / acúmulo     — misto com INCLINAÇÃO aleatória (crescimento) + ICC
  C. Efeito do HIIT (nível dia)  — misto no nível atleta×dia (dias 2–7)
  D. Interação Condição×Momento  — misto hiit*momento (o "efeito específico" do HIIT)
  E. Confirmação multivariada    — Hotelling T² (6 subescalas e eixo vigor+fadiga)

Autocontido: lê `base_modelagem.csv` (anonimizada) desta pasta.
Uso:  python modelagem.py            # grava resultados_modelagem.json
Dependências: numpy scipy pandas statsmodels
"""
import os, json, warnings, numpy as np, pandas as pd
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests
from scipy import stats
warnings.filterwarnings('ignore')

HERE = os.path.dirname(os.path.abspath(__file__))
d = pd.read_csv(os.path.join(HERE, 'base_modelagem.csv'))
SUBS = ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
OUT  = ['PTH','FadFis','Fadiga','Vigor','FadMen','Tensão','Depressão','Raiva','Confusão']
res  = {'n_obs': int(len(d)), 'n_atletas': int(d['atleta'].nunique())}

def icc_from(md):
    """ICC do atleta = var(intercepto) / (var(intercepto)+var(resíduo))."""
    try:
        vg = float(md.cov_re.iloc[0,0]); ve = float(md.scale)
        return round(vg/(vg+ve), 3)
    except Exception:
        return None

# ---------- A. Resposta aguda pré→pós (misto) ----------
print("A. Resposta aguda pré→pós (modelo misto, atleta aleatório)")
ap = d[d['momento'].isin(['pre','pos'])].copy()
ap['pos'] = (ap['momento']=='pos').astype(int)
rowsA, pvals = [], []
for y in OUT:
    dat = ap[['atleta','pos',y]].dropna()
    try:
        m = smf.mixedlm(f"Q('{y}') ~ pos", dat, groups=dat['atleta']).fit(reml=False, method='lbfgs')
        b = float(m.fe_params['pos']); p = float(m.pvalues['pos'])
        # dz intra-sujeito (agregado por atleta) como tamanho de efeito
        w = dat.pivot_table(index='atleta', columns='pos', values=y, aggfunc='mean').dropna()
        dz = float((w[1]-w[0]).mean()/(w[1]-w[0]).std(ddof=1)) if len(w)>2 else np.nan
        rowsA.append({'y':y,'b_pos':round(b,3),'p':p,'dz':round(dz,2),'icc':icc_from(m)}); pvals.append(p)
    except Exception as e:
        rowsA.append({'y':y,'erro':str(e)[:80]}); pvals.append(1.0)
_,pf,_,_ = multipletests([r.get('p',1) for r in rowsA], method='fdr_bh')
for r,pp in zip(rowsA,pf):
    if 'p' in r: r['p']=round(r['p'],4); r['p_FDR']=round(float(pp),4); r['signif_FDR']=bool(pp<0.05)
res['A_resposta_aguda'] = rowsA
for r in rowsA:
    if 'b_pos' in r: print(f"   {r['y']:10s} b(pós)={r['b_pos']:+.2f} dz={r['dz']:+.2f} p_FDR={r['p_FDR']:.3f} {'*' if r['signif_FDR'] else ''}")

# ---------- B. Efeito do dia / acúmulo (crescimento com inclinação aleatória) ----------
print("\nB. Acúmulo no microciclo (misto com inclinação aleatória por atleta)")
rowsB = []
for y in ['PTH','FadFis','Fadiga','Vigor']:
    dat = d[['atleta','dia',y]].dropna()
    try:
        m = smf.mixedlm(f"Q('{y}') ~ dia", dat, groups=dat['atleta'], re_formula="~dia").fit(reml=False, method='lbfgs')
        slope = float(m.fe_params['dia']); p = float(m.pvalues['dia'])
        try: var_slope = float(m.cov_re.loc['dia','dia'])
        except Exception: var_slope = None
        rowsB.append({'y':y,'inclinacao_por_dia':round(slope,3),'p':round(p,4),
                      'var_inclinacao_atleta':round(var_slope,3) if var_slope is not None else None,'icc':icc_from(m)})
        print(f"   {y:8s} +{slope:+.3f}/dia  p={p:.3f}  var(inclinação)={var_slope}")
    except Exception as e:
        rowsB.append({'y':y,'erro':str(e)[:80]})
res['B_acumulo_microciclo'] = rowsB

# ---------- C. Efeito do HIIT (nível atleta×dia, dias 2–7) ----------
print("\nC. HIIT vs. técnico-tático (nível do dia, dias 2–7)")
dd = d[d['dia'].between(2,7)].copy()
rowsC = []
for y in ['PTH','FadFis','Fadiga','Vigor','FadMen']:
    ad = dd.groupby(['atleta','dia']).agg(y=(y,'mean'), hiit=('hiit','max')).dropna().reset_index()
    try:
        m = smf.mixedlm("y ~ hiit", ad, groups=ad['atleta']).fit(reml=False, method='lbfgs')
        rowsC.append({'y':y,'efeito_HIIT':round(float(m.fe_params['hiit']),3),'p':round(float(m.pvalues['hiit']),4),'icc':icc_from(m)})
        print(f"   {y:8s} Δ(HIIT−sem)={float(m.fe_params['hiit']):+.2f}  p={float(m.pvalues['hiit']):.3f}")
    except Exception as e:
        rowsC.append({'y':y,'erro':str(e)[:80]})
res['C_efeito_HIIT_nivel_dia'] = rowsC

# ---------- D. Interação Condição × Momento (efeito específico do HIIT) ----------
print("\nD. Interação Condição×Momento (o HIIT muda a resposta aguda?)")
di = d[(d['momento'].isin(['pre','pos'])) & (d['dia'].between(2,7))].copy()
di['pos']=(di['momento']=='pos').astype(int)
rowsD=[]
for y in ['PTH','FadFis','Fadiga','Vigor']:
    dat=di[['atleta','pos','hiit',y]].dropna()
    try:
        m=smf.mixedlm(f"Q('{y}') ~ pos*hiit", dat, groups=dat['atleta']).fit(reml=False, method='lbfgs')
        key=[k for k in m.fe_params.index if ':' in k][0]
        rowsD.append({'y':y,'interacao':round(float(m.fe_params[key]),3),'p':round(float(m.pvalues[key]),4)})
        print(f"   {y:8s} pós×HIIT={float(m.fe_params[key]):+.2f}  p={float(m.pvalues[key]):.3f}")
    except Exception as e:
        rowsD.append({'y':y,'erro':str(e)[:80]})
res['D_interacao_condicao_momento']=rowsD

# ---------- E. Confirmação multivariada (Hotelling T²) ----------
print("\nE. Hotelling T² sobre a mudança pré→pós (agregada por atleta)")
def hotelling(cols):
    # restrito aos dias de HIIT/microciclo (2–7), como no manuscrito
    w = d[(d['momento'].isin(['pre','pos'])) & (d['dia'].between(2,7))].copy(); w['pos']=(w['momento']=='pos').astype(int)
    piv = w.pivot_table(index='atleta', columns='pos', values=cols, aggfunc='mean')
    D = pd.DataFrame({c: piv[(c,1)]-piv[(c,0)] for c in cols}).dropna()
    n,p = len(D), len(cols); m = D.mean().values; S = np.cov(D.values.T)
    T2 = n * m @ np.linalg.inv(S) @ m
    F = (n-p)/(p*(n-1)) * T2; pv = 1-stats.f.cdf(F, p, n-p)
    return {'F':round(float(F),2),'df':f'({p},{n-p})','p':round(float(pv),3),'D_mahalanobis':round(float(np.sqrt(m@np.linalg.inv(S)@m)),2)}
res['E_hotelling'] = {'6_subescalas':hotelling(SUBS), 'eixo_vigor_fadiga':hotelling(['Vigor','Fadiga'])}
print("   6 subescalas:", res['E_hotelling']['6_subescalas'])
print("   eixo vigor+fadiga:", res['E_hotelling']['eixo_vigor_fadiga'])

json.dump(res, open(os.path.join(HERE,'resultados_modelagem.json'),'w'), ensure_ascii=False, indent=1, default=str)
print("\nSalvo em resultados_modelagem.json")
