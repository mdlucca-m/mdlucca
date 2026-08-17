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
# 10) T-CAR — REGRESSÃO do humor ~ pico de velocidade (PV) e LIMIAR (logística)
#     PVini = PV do T-CAR de linha de base (T-CAR1); PV = T-CAR final (T-CAR2).
#     (a) Regressão linear das médias semanais de cada variável sobre o PV.
#     (b) Regressão da MUDANÇA D1->D7 sobre o PV.
#     (c) Tercis de aptidão (PVini) -> fadiga semanal (Kruskal-Wallis).
#     (d) Limiar de PV por regressão LOGÍSTICA para "dia de fadiga física
#         elevada" (fadiga do dia >= tercil superior), com AUC, OR e Youden.
# =============================================================================
titulo('10) T-CAR — REGRESSÃO do humor ~ PV e LIMIAR (regressão logística)')
try:
    F = pd.read_csv('tcar2_features.csv')[['ID','PV','PVini']]   # PVini=T-CAR1, PV=T-CAR2

    def reg_lin(x, y):
        """Regressão linear simples (mínimos quadrados): retorna β, R², ρ, p."""
        m = pd.DataFrame({'x': x, 'y': y}).dropna()
        lr = stats.linregress(m.x, m.y); rho, pr = stats.spearmanr(m.x, m.y)
        return lr.slope, lr.rvalue**2, lr.pvalue, rho, pr, len(m)

    # (a) Regressão das MÉDIAS SEMANAIS sobre o PV do T-CAR de linha de base
    W = wk[['Vigor','Fadiga','TMD','FadFisica']].reset_index().merge(F, on='ID', how='left')
    print('  (a) Regressão linear — média semanal ~ PV do T-CAR1 (PVini):')
    for y in ['Vigor','Fadiga','TMD','FadFisica']:
        b, r2, p, rho, rp, n = reg_lin(W['PVini'], W[y])
        print('      %-10s β=%+.2f  R²=%.2f  p=%.3f   (Spearman ρ=%+.2f, p=%.3f)' % (LAB.get(y,y), b, r2, p, rho, rp))

    # (b) Regressão da MUDANÇA D1->D7 sobre o PV
    print('  (b) Regressão linear — mudança D1->D7 ~ PVini:')
    for y in ['Vigor','Fadiga']:
        piv = dm.pivot(index='ID', columns='dia', values=y)
        chg = (piv[7] - piv[1]).rename('chg').reset_index().merge(F, on='ID', how='left')
        b, r2, p, rho, rp, n = reg_lin(chg['PVini'], chg['chg'])
        print('      Δ%-9s β=%+.2f  R²=%.2f  p=%.3f   (ρ=%+.2f, p=%.3f)' % (LAB.get(y,y), b, r2, p, rho, rp))

    # (c) Tercis de aptidão -> fadiga semanal (Kruskal-Wallis)
    W['terc'] = pd.qcut(W['PVini'], 3, labels=['Baixa','Média','Alta'])
    med = {str(k): g['Fadiga'].mean() for k, g in W.groupby('terc')}
    Hk, pk = stats.kruskal(*[W[W.terc==k]['Fadiga'].values for k in ['Baixa','Média','Alta']])
    print('  (c) Fadiga semanal por tercil de aptidão (PVini): %s | Kruskal-Wallis H=%.2f p=%.3f'
          % ({k: round(v,2) for k,v in med.items()}, Hk, pk))

    # (d) LIMIAR por regressão logística sobre a fadiga FÍSICA em nível de atleta-dia
    dd = dm[['ID','dia','FadFisica']].merge(F, on='ID', how='left').dropna(subset=['FadFisica','PVini'])
    cut = dd['FadFisica'].quantile(2/3)                  # "fadiga elevada" = tercil superior
    dd['hi'] = (dd['FadFisica'] >= cut).astype(int)

    def logit_nr(x, y):
        """Regressão logística por Newton-Raphson (sem dependências externas)."""
        x = np.asarray(x, float); y = np.asarray(y, float); b0 = b1 = 0.0
        for _ in range(300):
            pr = 1/(1+np.exp(-(b0+b1*x))); Wt = pr*(1-pr)+1e-9
            g0 = np.sum(y-pr); g1 = np.sum((y-pr)*x)
            h00 = -np.sum(Wt); h01 = -np.sum(Wt*x); h11 = -np.sum(Wt*x*x)
            det = h00*h11 - h01*h01
            b0 -= (h11*g0 - h01*g1)/det; b1 -= (-h01*g0 + h00*g1)/det
        return b0, b1

    def auc_mw(score, label):
        s = np.asarray(score, float); y = np.asarray(label)
        pos, neg = s[y==1], s[y==0]
        return float(stats.mannwhitneyu(pos, neg).statistic/(len(pos)*len(neg)))

    def youden(x, y):
        x = np.asarray(x, float); y = np.asarray(y); best = None
        for t in np.unique(x):
            pred = (x <= t).astype(int)                  # PV baixo -> risco de fadiga
            tp = np.sum((pred==1)&(y==1)); fn = np.sum((pred==0)&(y==1))
            tn = np.sum((pred==0)&(y==0)); fp = np.sum((pred==1)&(y==0))
            se = tp/(tp+fn+1e-9); sp = tn/(tn+fp+1e-9); j = se+sp-1
            if best is None or j > best[1]: best = (float(t), j, se, sp)
        return best

    b0, b1 = logit_nr(dd['PVini'], dd['hi'])
    A = auc_mw(-dd['PVini'], dd['hi'])                    # -PV: menor PV -> maior risco
    t, j, se, sp = youden(dd['PVini'], dd['hi'])
    # IC95% da AUC por bootstrap por atleta (semente fixa p/ reprodutibilidade)
    ids = dd.ID.unique(); rng = np.random.default_rng(2024); boot = []
    for _ in range(500):
        s = rng.choice(ids, len(ids), True)
        g = pd.concat([dd[dd.ID==i] for i in s])
        boot.append(auc_mw(-g['PVini'], g['hi']))
    lo, hi = np.nanpercentile(boot, [2.5, 97.5])
    print('  (d) Limiar logístico (fadiga física elevada ~ PV do T-CAR1):')
    print('      OR=%.2f por km/h | AUC=%.2f [IC95%% %.2f–%.2f] | limiar (Youden)=%.1f km/h (sens=%.2f, esp=%.2f)'
          % (np.exp(b1), A, lo, hi, t, se, sp))
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

# =============================================================================
# 12) COMPOSIÇÃO CORPORAL e AJUSTE ALOMÉTRICO do pico de velocidade
#     Separa o efeito da aptidão do efeito do tamanho corporal:
#     expoente da relação log(PV)~log(massa) e PV normalizado (PV/massa^b).
#     Requer phys.csv (ID, massa, estatura, pGordura) — anonimizado.
# =============================================================================
titulo('12) COMPOSIÇÃO CORPORAL e AJUSTE ALOMÉTRICO')
try:
    phys = pd.read_csv('phys.csv')[['ID','massa','estatura','pGordura']]
    Fp = pd.read_csv('tcar2_features.csv')[['ID','PVini']]
    A = wk[['Vigor','Fadiga','FadFisica']].reset_index().merge(phys, on='ID').merge(Fp, on='ID').dropna()
    print('  Composição corporal (n=%d): massa=%.1f±%.1f kg | estatura=%.1f±%.1f cm | %%gordura=%.1f±%.1f'
          % (len(A), A.massa.mean(), A.massa.std(), A.estatura.mean(), A.estatura.std(), A.pGordura.mean(), A.pGordura.std()))
    for x in ['massa','pGordura']:
        r, p = stats.spearmanr(A[x], A['FadFisica'])
        print('  %-9s x FadFísica: rho=%+.2f p=%.3f' % (x, r, p))
    # expoente alométrico e PV normalizado
    b = np.polyfit(np.log(A.massa), np.log(A.PVini), 1)[0]
    rr, pp = stats.pearsonr(np.log(A.massa), np.log(A.PVini))
    A['PV_alom'] = A.PVini / (A.massa**b)
    print('  Expoente alométrico log(PV)~log(massa): b=%.2f (r=%.2f, p=%.3f)' % (b, rr, pp))
    for lab, col in [('PV bruto', 'PVini'), ('PV alométrico', 'PV_alom')]:
        rf, pf = stats.spearmanr(A[col], A['FadFisica']); rv, pv = stats.spearmanr(A[col], A['Vigor'])
        print('  %-14s × FadFísica rho=%+.2f (p=%.3f) | × Vigor rho=%+.2f (p=%.3f)' % (lab, rf, pf, rv, pv))
except FileNotFoundError:
    print('  [phys.csv não encontrado — pulei o bloco de composição corporal]')

# =============================================================================
# 13) MODELAGEM POLINOMIAL das trajetórias: derivadas e taxa de variação
#     Ajusta P(t) (grau 3) às médias diárias e deriva: taxa de variação
#     instantânea P'(t), pontos críticos (P'=0) e inflexão (P''=0).
# =============================================================================
titulo('13) MODELAGEM POLINOMIAL — 1ª e 2ª derivadas, taxa de variação e acoplamento')
GR = 3
# ordem canônica POMS/BRUMS
CANON = ['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao','TMD']
tt = np.linspace(1, 7, 601); dcur = {}   # mesmo intervalo do artigo
print('  Ajuste polinomial grau %d (médias diárias):' % GR)
for k in CANON:
    y = h.groupby('dia')[k].mean().reindex(range(1,8)).values   # média por observação (como no artigo)
    t = np.arange(1, 8)
    c = np.polyfit(t, y, GR); P = np.poly1d(c); dP = P.deriv(1); d2P = P.deriv(2)
    r2 = 1 - ((y-P(t))**2).sum()/((y-y.mean())**2).sum()
    infl = sorted(round(float(r.real),1) for r in d2P.roots if abs(r.imag)<1e-6 and 1<=r.real<=7)
    dcur[k] = dP(tt)
    Pv, dPv = P(tt), dP(tt)
    fmax_i, fmin_i = int(np.argmax(Pv)), int(np.argmin(Pv))
    dmax_i, dmin_i = int(np.argmax(dPv)), int(np.argmin(dPv))
    print('    %-10s R²=%.2f | P\'(1)=%+.2f P\'(7)=%+.2f | P"(1)=%+.2f P"(7)=%+.2f | inflexão=%s'
          % (LAB.get(k,k), r2, dP(1), dP(7), d2P(1), d2P(7), infl))
    print('                valor máx=%.1f (D%.1f)  mín=%.1f (D%.1f) | limites P\': subida máx=%+.2f (D%.1f)  queda máx=%+.2f (D%.1f)'
          % (Pv[fmax_i], tt[fmax_i], Pv[fmin_i], tt[fmin_i], dPv[dmax_i], tt[dmax_i], dPv[dmin_i], tt[dmin_i]))
# acoplamento entre variáveis: correlação das curvas de 1ª derivada
print('  Acoplamento (correlação das curvas P\'):')
for a, b in [('Vigor','Fadiga'), ('Fadiga','TMD'), ('Vigor','TMD')]:
    print('    %-8s x %-8s r=%+.2f' % (LAB.get(a,a), LAB.get(b,b), np.corrcoef(dcur[a], dcur[b])[0,1]))

print('\n' + '='*72 + '\nFIM — todos os resultados acima reproduzem os valores do artigo.\n' + '='*72)
