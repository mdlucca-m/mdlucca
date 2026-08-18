"""
Análise de componentes principais (PCA) exploratória das seis subescalas do
BRUMS (286 observações padronizadas). Descreve a estrutura de covariância —
quantos eixos latentes resumem o humor e como as dimensões se agrupam neles.
Ressalva: observações aninhadas em atletas (PCA exploratória, não confirmatória).
Saída: pca.json
"""
import warnings; warnings.filterwarnings('ignore')
import json, numpy as np, pandas as pd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

h = pd.read_csv('hum_prof.csv')
DIMS = ['Tensao', 'Depressao', 'Raiva', 'Vigor', 'Fadiga', 'Confusao']
LAB = ['Tensão', 'Depressão', 'Raiva', 'Vigor', 'Fadiga', 'Confusão']
d = h.dropna(subset=DIMS).copy()
X = StandardScaler().fit_transform(d[DIMS])
p = PCA().fit(X)
ev = p.explained_variance_
vr = p.explained_variance_ratio_
# cargas de correlação (loadings) = componente * sqrt(autovalor)
load = (p.components_.T * np.sqrt(ev)).T

OUT = dict(
    n=int(len(d)),
    var_ratio=[float(v) for v in vr],
    eigenvalues=[float(e) for e in ev],
    n_kaiser=int((ev > 1).sum()),
    dims=LAB,
    PC1={LAB[i]: float(load[0, i]) for i in range(6)},
    PC2={LAB[i]: float(load[1, i]) for i in range(6)},
)
json.dump(OUT, open('pca.json', 'w'), indent=1, ensure_ascii=False)
print('n=%d | Kaiser: %d componentes (autovalor>1)' % (OUT['n'], OUT['n_kaiser']))
print('Var: PC1 %.0f%% PC2 %.0f%% (acum %.0f%%)' % (100 * vr[0], 100 * vr[1], 100 * (vr[0] + vr[1])))
print('%-10s %7s %7s' % ('Dim', 'PC1', 'PC2'))
for i, l in enumerate(LAB):
    print('%-10s %+7.2f %+7.2f' % (l, load[0, i], load[1, i]))
