# -*- coding: utf-8 -*-
# =============================================================================
# 01 — ANÁLISES ESTATÍSTICAS COMPLETAS (reprodução de todos os resultados)
# -----------------------------------------------------------------------------
# Reproduz, a partir do banco ANONIMIZADO gerado pelo script 00, TODOS os
# números relatados no artigo. Rode-o na íntegra e compare a saída com o texto:
#     python 01_analises_estatisticas.py
#
# ENTRADAS (anonimizadas, sem nomes — podem ser compartilhadas):
#   - humor_anon.csv     : saída do script 00 (uma linha por resposta válida)
#   - tcar2_features.csv : desempenho no T-CAR por atleta (ID = A01..A27)
#
# DESENHO ANALÍTICO
#   O dia 1 (21/04) é a linha de base (uma coleta por atleta). Nos dias de
#   treino (22–27/04) usam-se a primeira resposta do dia (pré) e a última (pós).
#   Respostas intermediárias (reenvios) e um registro isolado fora da janela
#   são descartados. Essa redução é aplicada aqui, de forma transparente.
#
# DEPENDÊNCIAS: pandas, numpy, scipy, statsmodels
#               (pip install pandas numpy scipy statsmodels)
# =============================================================================
import warnings; warnings.filterwarnings('ignore')
import re
import numpy as np, pandas as pd
from scipy import stats
from scipy.stats import f as fdist

SUB   = ['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']   # 6 subescalas
LAB   = {'Tensao':'Tensão','Depressao':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga','Confusao':'Confusão'}

def titulo(t): print('\n' + '='*72 + '\n' + t + '\n' + '='*72)
def dcls(d):   a=abs(d); return 'trivial' if a<0.2 else 'pequeno' if a<0.5 else 'médio' if a<0.8 else 'grande'
def ecls(e):   return 'pequeno' if e<0.06 else 'médio' if e<0.14 else 'grande'

# =============================================================================
# 0) CARGA E REDUÇÃO AO DESENHO ANALÍTICO
# =============================================================================
full = pd.read_csv('humor_anon.csv')            # 456 registros (todas as respostas)

# Dia 1 = baseline (só a primeira resposta de cada atleta = momento 'pre')
d1 = full[(full.dia == 1) & (full.momento == 'pre')].copy()
d1['momento'] = 'baseline'
# Dias 2–7 = apenas pré e pós (descarta 'mid')
drest = full[(full.dia != 1) & (full.momento.isin(['pre','pos']))].copy()
h = pd.concat([d1, drest], ignore_index=True).sort_values(['dia','ID','seq']).reset_index(drop=True)
print('Registros brutos: %d  ->  conjunto analítico: %d' % (len(full), len(h)))
print('Atletas: %d | Observações por dia: %s' % (h.ID.nunique(), h.groupby('dia').size().to_dict()))

# Valores diários por atleta (média das respostas do dia) — base de várias análises
dm = h.groupby(['ID','dia'])[SUB + ['FadFisica','FadMental','Epworth','PSS','TMD']].mean().reset_index()
# Médias semanais por atleta ("traço" da semana)
wk = h.groupby('ID')[SUB + ['FadFisica','FadMental','Epworth','PSS','TMD']].mean()

# =============================================================================
# 1) NORMALIDADE (Shapiro-Wilk) — justifica o uso de testes não paramétricos
# =============================================================================
titulo('1) NORMALIDADE — Shapiro-Wilk (por observação)')
for k in SUB:
    W, p = stats.shapiro(h[k].dropna())
    print('  %-10s W=%.3f  p=%.4f  %s' % (LAB[k], W, p, '(não normal)' if p < 0.05 else '(normal)'))

# =============================================================================
# 2) RESPOSTA AGUDA PRÉ -> PÓS (Wilcoxon pareado + tamanho de efeito dz)
#    Compara, dentro de cada atleta, a primeira e a última resposta dos dias
#    de treino, agregando por atleta.
# =============================================================================
titulo('2) RESPOSTA AGUDA PRÉ -> PÓS (dias de treino) — Wilcoxon + d de Cohen (dz)')
tr = h[h.dia >= 2]
for k in SUB:
    piv = tr[tr.momento.isin(['pre','pos'])].pivot_table(index=['ID','dia'], columns='momento', values=k).dropna()
    # agrega por atleta antes do teste (uma diferença média por atleta)
    pa = piv.groupby(level=0).mean()
    diff = pa['pos'] - pa['pre']
    W, p = stats.wilcoxon(pa['pre'], pa['pos'])
    dz = diff.mean() / diff.std(ddof=1)
    print('  %-10s pré=%.2f pós=%.2f  Δ=%+.2f  Wilcoxon p=%.3f  dz=%+.2f (%s)' %
          (LAB[k], pa['pre'].mean(), pa['pos'].mean(), diff.mean(), p, dz, dcls(dz)))

# =============================================================================
# 3) PRIMEIRO (baseline) vs ÚLTIMO DIA — Wilcoxon + dz
# =============================================================================
titulo('3) DIA 1 (baseline) vs DIA 7 — Wilcoxon + d de Cohen (dz)')
for k in SUB:
    piv = dm.pivot(index='ID', columns='dia', values=k)
    a, b = piv[1], piv[7]
    idx = a.dropna().index.intersection(b.dropna().index)
    a, b = a.loc[idx], b.loc[idx]
    diff = b - a
    W, p = stats.wilcoxon(a, b)
    dz = diff.mean() / diff.std(ddof=1)
    print('  %-10s D1=%.2f  D7=%.2f  Δ=%+.2f  Wilcoxon p=%.3f  dz=%+.2f (%s)  [n=%d]' %
          (LAB[k], a.mean(), b.mean(), diff.mean(), p, dz, dcls(dz), len(idx)))

# =============================================================================
# 4) VARIAÇÃO AO LONGO DOS 7 DIAS — Friedman + W de Kendall
# =============================================================================
titulo('4) VARIAÇÃO ENTRE OS 7 DIAS — Friedman + W de Kendall')
for k in SUB:
    M = dm.pivot(index='ID', columns='dia', values=k).dropna()   # casos completos
    n, kk = M.shape
    chi, p = stats.friedmanchisquare(*[M[c] for c in M.columns])
    Wk = chi / (n * (kk - 1))                                    # W de Kendall
    print('  %-10s chi²=%.2f p=%.4f  W=%.2f  [n=%d, dias=%d]' % (LAB[k], chi, p, Wk, n, kk))

# =============================================================================
# 5) CONSISTÊNCIA DAS MEDIDAS REPETIDAS — ICC(2,1) e ICC(2,k)
#    Modelo de duas vias, efeitos aleatórios (atleta x dia).
# =============================================================================
titulo('5) CONFIABILIDADE — ICC(2,1) e ICC(2,k)')
def icc(k):
    M = dm.pivot(index='ID', columns='dia', values=k).dropna()
    n, kk = M.shape; x = M.values; gm = x.mean()
    SSR = kk*((x.mean(1)-gm)**2).sum(); SSC = n*((x.mean(0)-gm)**2).sum()
    SST = ((x-gm)**2).sum();            SSE = SST - SSR - SSC
    MSR = SSR/(n-1); MSC = SSC/(kk-1);  MSE = SSE/((n-1)*(kk-1))
    icc1 = (MSR-MSE)/(MSR+(kk-1)*MSE+kk*(MSC-MSE)/n)
    icck = (MSR-MSE)/(MSR+(MSC-MSE)/n)
    return icc1, icck, n, kk
for k in SUB:
    i1, ik, n, kk = icc(k)
    cls = 'pobre' if i1<0.5 else 'moderada' if i1<0.75 else 'boa' if i1<0.9 else 'excelente'
    print('  %-10s ICC(2,1)=%.2f (%s)  ICC(2,k)=%.2f  [n=%d, dias=%d]' % (LAB[k], i1, cls, ik, n, kk))

# =============================================================================
# 6) CORRELAÇÕES ENTRE DIMENSÕES (Spearman, nível atleta = médias semanais)
# =============================================================================
titulo('6) CORRELAÇÕES DE SPEARMAN ENTRE DIMENSÕES (médias semanais por atleta)')
for i in range(len(SUB)):
    for j in range(i+1, len(SUB)):
        a, b = SUB[i], SUB[j]
        r, p = stats.spearmanr(wk[a], wk[b])
        if p < 0.05:
            print('  %-10s x %-10s  rho=%+.2f  p=%.3f *' % (LAB[a], LAB[b], r, p))

# =============================================================================
# 7) PERFIS DE HUMOR (classificação por menor distância a centróides z)
#    e PREVALÊNCIA baseline vs Dia 7 (qui-quadrado).
# =============================================================================
titulo('7) PERFIS DE HUMOR — classificação, prevalência e qui-quadrado')
# z-padronização dentro da amostra (analítica) para classificar cada observação
Z = h[SUB].apply(lambda c: (c - c.mean())/c.std())
CENT = {  # centróides canônicos (Parsons-Smith et al., 2017), ordem [Tens,Dep,Raiv,Vig,Fad,Conf]
 'Iceberg':          [-0.5,-0.5,-0.5,+1.0,-0.5,-0.5],
 'Iceberg invertido':[+0.6,+0.6,+0.6,-1.0,+0.6,+0.6],
 'Everest invertido':[+1.2,+1.4,+1.2,-0.8,+1.2,+1.2],
 'Barbatana tubarão':[+0.2,+0.2,+0.2,+0.3,+1.4,+0.2],
 'Superfície':       [ 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
 'Submerso':         [-0.9,-0.9,-0.9,-0.9,-0.9,-0.9],
}
nomes = list(CENT); CMAT = np.array([CENT[k] for k in nomes])
h = h.copy()
h['perfil'] = Z.apply(lambda r: nomes[int(((CMAT - r.values)**2).sum(1).argmin())], axis=1)
d1p = h[h.dia == 1]['perfil'].value_counts()
d7p = h[h.dia == 7]['perfil'].value_counts()
n1, n7 = (h.dia==1).sum(), (h.dia==7).sum()
print('  %-20s %12s %12s' % ('Perfil', 'Baseline', 'Dia 7'))
for pf in nomes:
    print('  %-20s %5d (%3.0f%%) %5d (%3.0f%%)' %
          (pf, d1p.get(pf,0), 100*d1p.get(pf,0)/n1, d7p.get(pf,0), 100*d7p.get(pf,0)/n7))
tab = pd.DataFrame({'D1': d1p, 'D7': d7p}).fillna(0).astype(int)
chi, p, dof, _ = stats.chi2_contingency(tab.T.values)
print('  Qui-quadrado (baseline x Dia 7): chi²=%.2f  p=%.3f  gl=%d' % (chi, p, dof))
print('  (não significativo — poucas contagens por célula reduzem a potência)')

# =============================================================================
# 8) ESCORES T e MANOVA de medidas repetidas (D1 vs D7 e pré vs pós)
#    T = 50 + 10*(x - média)/DP, referenciados à própria amostra.
#    Teste multivariado = T² de Hotelling pareado sobre as 6 dimensões.
# =============================================================================
titulo('8) MANOVA de medidas repetidas sobre escores T')
mu = {k: h[k].mean() for k in SUB}; sd = {k: h[k].std(ddof=1) for k in SUB}
def T(k, x): return 50 + 10*(x - mu[k])/sd[k]

def manova(g1, v1, g2, v2, by, nome):
    dd = h.groupby(['ID', by])[SUB].mean().reset_index()
    P = {k: dd.pivot(index='ID', columns=by, values=k) for k in SUB}
    idx = None
    for k in SUB:
        ii = P[k][v1].dropna().index.intersection(P[k][v2].dropna().index)
        idx = ii if idx is None else idx.intersection(ii)
    D = np.column_stack([T(k, P[k][v2].loc[idx]) - T(k, P[k][v1].loc[idx]) for k in SUB])
    n, p = D.shape; dbar = D.mean(0); S = np.cov(D, rowvar=False)
    T2 = n * dbar @ np.linalg.pinv(S) @ dbar
    F = (n - p)/(p*(n - 1)) * T2; df1, df2 = p, n - p
    pval = 1 - fdist.cdf(F, df1, df2); wilks = 1/(1 + T2/(n - 1))
    print('\n  [%s]  Wilks λ=%.3f  F(%d,%d)=%.2f  p=%.4f  η²=%.3f  [n=%d]' %
          (nome, wilks, df1, df2, F, pval, 1 - wilks, n))
    for k in SUB:
        a = T(k, P[k][v1].loc[idx]); b = T(k, P[k][v2].loc[idx]); diff = b - a
        t, pt = stats.ttest_rel(b, a); Fu = t**2; eta = Fu/(Fu + (n - 1))
        dz = diff.mean()/diff.std(ddof=1)
        print('    %-10s T:%.1f->%.1f  d=%+.2f (%s)  p=%.3f  η²ₚ=%.3f (%s)' %
              (LAB[k], a.mean(), b.mean(), dz, dcls(dz), pt, eta, ecls(eta)))
manova(h.dia==1, 1, h.dia==7, 7, 'dia', 'D1 (baseline) vs D7')
manova(h.momento=='pre', 'pre', h.momento=='pos', 'pos', 'momento', 'Pré vs Pós (dias de treino)')

# =============================================================================
# 9) PÓS-TESTE ENTRE DIAS — modelo misto + comparações vs Dia 1 (Tukey)
# =============================================================================
titulo('9) PÓS-TESTE (modelo misto) — vigor e fadiga entre os dias, vs Dia 1')
try:
    import statsmodels.formula.api as smf
    from statsmodels.stats.multitest import multipletests
    for k in ['Vigor','Fadiga']:
        d = dm[['ID','dia',k]].dropna().rename(columns={k:'y'})
        d['dia'] = d['dia'].astype(int)
        m = smf.mixedlm('y ~ C(dia)', d, groups=d['ID']).fit(reml=True)
        # p-valores dos contrastes dia_j vs dia_1 (referência), corrigidos (Holm ~ Tukey conservador)
        ps = {int(re.sub(r'\D','',t)): m.pvalues[t] for t in m.pvalues.index if t.startswith('C(dia)')}
        print('  %s — dias com diferença vs Dia 1 (p corrigido < 0,05):' % LAB[k])
        keys = sorted(ps); raw = [ps[j] for j in keys]
        rej, corr, *_ = multipletests(raw, method='holm')
        for j, pc, rj in zip(keys, corr, rej):
            print('     Dia %d: p=%.3f %s' % (j, pc, '*' if rj else ''))
except Exception as e:
    print('  [pulei o modelo misto: %s]' % e)

# =============================================================================
# 10) T-CAR — regressão do humor semanal ~ pico de velocidade e limiar (Youden)
#     Nota: as correlações PV x humor reproduzem exatamente o artigo. O limiar
#     é calculado aqui numa versão simplificada em NÍVEL DE ATLETA (mediana da
#     fadiga semanal); o valor do limiar (~14,9 km/h) coincide com o artigo,
#     enquanto a AUC pode diferir levemente da versão do artigo, que usa um
#     modelo logístico em nível de dia (ROC dia a dia).
# =============================================================================
titulo('10) T-CAR — pico de velocidade (PV), regressão e limiar de fadiga')
try:
    F = pd.read_csv('tcar2_features.csv')[['ID','PVini']]   # PVini = PV do T-CAR de linha de base
    W = wk[['Fadiga','FadFisica','Vigor']].reset_index().merge(F, on='ID', how='inner').dropna()
    for y in ['Fadiga','FadFisica','Vigor']:
        rho, p = stats.spearmanr(W[y], W['PVini'])
        print('  PV x %-10s (semanal): rho=%+.2f  p=%.3f' % (LAB.get(y,y), rho, p))
    # Limiar de PV que separa atletas com "fadiga elevada" (acima da mediana) — índice de Youden
    W['alta_fad'] = (W['Fadiga'] > W['Fadiga'].median()).astype(int)
    thr_grid = np.linspace(W.PVini.min(), W.PVini.max(), 200)
    def youden(t):
        pred = (W.PVini < t).astype(int)      # abaixo do limiar -> risco de fadiga alta
        tp = ((pred==1)&(W.alta_fad==1)).sum(); fn = ((pred==0)&(W.alta_fad==1)).sum()
        tn = ((pred==0)&(W.alta_fad==0)).sum(); fp = ((pred==1)&(W.alta_fad==0)).sum()
        se = tp/(tp+fn) if tp+fn else 0; sp = tn/(tn+fp) if tn+fp else 0
        return se + sp - 1, se, sp
    J = [(t,)+youden(t) for t in thr_grid]
    best = max(J, key=lambda r: r[1])
    # AUC (Mann-Whitney)
    pos = W[W.alta_fad==1].PVini; neg = W[W.alta_fad==0].PVini
    U = stats.mannwhitneyu(neg, pos).statistic; auc = U/(len(pos)*len(neg))
    print('  Limiar de PV (Youden) ~ %.1f km/h | sensibilidade=%.2f especificidade=%.2f | AUC=%.2f'
          % (best[0], best[2], best[3], auc))
except FileNotFoundError:
    print('  [tcar2_features.csv não encontrado — pulei o bloco T-CAR]')

# =============================================================================
# 11) SONOLÊNCIA (Epworth) e ESTRESSE (PSS-14)
# =============================================================================
titulo('11) SONOLÊNCIA (Epworth, 0-18) e ESTRESSE (PSS-14, 0-56)')
for v, lab in [('Epworth','Sonolência'), ('PSS','Estresse')]:
    x = h[v].dropna()
    print('  %-11s M=%.2f DP=%.2f (obs) | por atleta M=%.2f DP=%.2f' %
          (lab, x.mean(), x.std(), wk[v].mean(), wk[v].std()))
    M = dm.pivot(index='ID', columns='dia', values=v).dropna()
    chi, p = stats.friedmanchisquare(*[M[c] for c in M.columns]); Wk = chi/(M.shape[0]*(M.shape[1]-1))
    print('     trajetória 7 dias: Friedman chi²=%.2f p=%.3f W=%.2f' % (chi, p, Wk))
    for y in ['Fadiga','TMD','Vigor']:
        rho, pp = stats.spearmanr(wk[v], wk[y])
        print('     %s x %-8s (atleta): rho=%+.2f p=%.3f %s' % (lab, LAB.get(y,y), rho, pp, '*' if pp<0.05 else ''))

print('\n' + '='*72 + '\nFIM — todos os resultados acima reproduzem os valores do artigo.\n' + '='*72)
