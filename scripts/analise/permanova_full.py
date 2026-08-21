# -*- coding: utf-8 -*-
# =============================================================================
# PERMANOVA multivariada do perfil de humor (6 subescalas do BRUMS)  + R2 + PERMDISP
# -----------------------------------------------------------------------------
#  - distancia euclidiana sobre escores padronizados (z)
#  - permutacao RESTRITA AO ATLETA (respeita o desenho de medidas repetidas;
#    sem isso o p seria invalido por pseudorreplicacao)
#  - reporta pseudo-F, R2 (tamanho de efeito) e p (9999 permutacoes)
#  - PERMDISP (Anderson 2006): homogeneidade das dispersoes multivariadas,
#    para separar deslocamento de centroide (locacao) de heterogeneidade de
#    variancia (dispersao)
#
# ENTRADA: humor_anon.csv (banco anonimizado A01..A27; SEM nomes)
#   colunas: ID, dia, momento (pre/mid/pos), HIIT (0/1) e as 6 subescalas em S.
# USO:      python permanova_full.py
#
# REPRODUCIBILIDADE: reproduz os valores publicados
#   momento pre/mid/pos -> pseudo-F = 1,75 ;  HIIT -> pseudo-F = 2,71.
# =============================================================================
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd

S = ['Tensao','Depressao','Raiva','Vigor','Fadiga','Confusao']
NPERM = 9999
rng = np.random.default_rng(7)

hum = pd.read_csv('humor_anon.csv')
train = hum[hum.dia.isin([2,3,4,5,6,7])].dropna(subset=S).copy()

def zmat(df):
    return ((df[S] - df[S].mean()) / df[S].std(ddof=1)).values

def ss_decomp(X, g):
    tot = ((X - X.mean(0))**2).sum(); wg = 0.0
    for lev in np.unique(g):
        Xi = X[g == lev]; wg += ((Xi - Xi.mean(0))**2).sum()
    return tot, tot - wg, wg

def pseudoF_R2(X, g):
    a = len(np.unique(g)); N = len(X)
    tot, between, within = ss_decomp(X, g)
    return (between/(a-1))/(within/(N-a)), between/tot

def restricted_perm(g, ids):
    gp = g.copy()
    for aid in np.unique(ids):
        idx = np.where(ids == aid)[0]; gp[idx] = rng.permutation(g[idx])
    return gp

def permanova(df, col):
    X = zmat(df); g = df[col].values.astype(object); ids = df['ID'].values
    F0, R2 = pseudoF_R2(X, g); cnt = 1
    for _ in range(NPERM):
        if pseudoF_R2(X, restricted_perm(g, ids))[0] >= F0: cnt += 1
    return F0, R2, cnt/(NPERM+1), len(X), len(np.unique(g))

def permdisp(df, col):
    X = zmat(df); g = df[col].values.astype(object); ids = df['ID'].values
    def dispF(gg):
        d = np.empty(len(X))
        for lev in np.unique(gg):
            m = X[gg == lev].mean(0); d[gg == lev] = np.sqrt(((X[gg == lev]-m)**2).sum(1))
        a = len(np.unique(gg)); N = len(X); gm = d.mean()
        bet = sum((gg==lev).sum()*(d[gg==lev].mean()-gm)**2 for lev in np.unique(gg))
        wit = sum(((d[gg==lev]-d[gg==lev].mean())**2).sum() for lev in np.unique(gg))
        return (bet/(a-1))/(wit/(N-a)), {str(lev): round(float(d[gg==lev].mean()),3) for lev in np.unique(gg)}
    F0, means = dispF(g); cnt = 1
    for _ in range(NPERM):
        if dispF(restricted_perm(g, ids))[0] >= F0: cnt += 1
    return F0, means, cnt/(NPERM+1)

CONTRASTES = [
    ('Pre vs pos (momento pre/pos)', train[train.momento.isin(['pre','pos'])], 'momento'),
    ('Momento pre/mid/pos',           train,                                   'momento'),
    ('HIIT vs nao-HIIT',              train,                                   'HIIT'),
]
print(f"N(dias 2-7) = {len(train)} | atletas = {train.ID.nunique()} | subescalas = {len(S)}\n")
for lab, df, col in CONTRASTES:
    F, R2, p, N, a = permanova(df, col)
    dF, dmeans, dp = permdisp(df, col)
    print(f"[{lab}]  N={N}, grupos={a}")
    print(f"  PERMANOVA : pseudo-F = {F:.3f} | R2 = {R2:.3f} ({R2*100:.1f}% da variancia) | p = {p:.4f}")
    print(f"  PERMDISP  : F = {dF:.3f} | p = {dp:.4f} | dispersoes medias = " +
          ", ".join(f"{k}={v}" for k,v in dmeans.items()))
    print(f"  Leitura   : " + ("dispersoes homogeneas -> efeito de LOCACAO (centroide)"
                                if dp > 0.05 else
                                "dispersoes DIFEREM -> parte do efeito e de dispersao (reportar)") + "\n")
