"""
Propriedades psicométricas das subescalas do BRUMS: consistência interna
(alfa de Cronbach e correlação média entre itens), efeito de piso (critério
de Terwee: >15% das observações no menor escore) e assimetria. Justifica a
insensibilidade das dimensões negativas à carga.

Entrada (item-level, anonimizado no uso — a coluna de nome é descartada):
  items.csv   : 24 itens do BRUMS por observação
  hum_prof.csv: escores por subescala (0–16)
Saída: psychometric.json
"""
import warnings; warnings.filterwarnings('ignore')
import json, pandas as pd, numpy as np
from scipy import stats

it = pd.read_csv('items.csv').drop(columns=['Atleta'])   # descarta identificacao
h = pd.read_csv('hum_prof.csv')
SUB = {'Tensao': ['Apavorado', 'Ansioso', 'Preocupado', 'Tenso'],
       'Depressao': ['Deprimido', 'Desanimado', 'Triste', 'Infeliz'],
       'Raiva': ['Irritado', 'Zangado', 'ComRaiva', 'MalHumorado'],
       'Vigor': ['Animado', 'ComDisposição', 'ComEnergia', 'Alerta'],
       'Fadiga': ['Esgotado', 'Exausto', 'Sonolento', 'Cansado'],
       'Confusao': ['Confuso', 'Inseguro', 'Desorientado', 'Indeciso']}

def alpha(df):
    k = df.shape[1]; iv = df.var(ddof=1).sum(); tv = df.sum(axis=1).var(ddof=1)
    return (k / (k - 1)) * (1 - iv / tv)

def miic(df):
    c = df.corr().values; n = c.shape[0]; return (c.sum() - n) / (n * (n - 1))

OUT = {}
for s, items in SUB.items():
    df = it[items].dropna(); x = h[s].dropna()
    OUT[s] = dict(alpha=float(alpha(df)), miic=float(miic(df)),
                  floor0=float((x == 0).mean()), floor_le2=float((x <= 2).mean()),
                  mean=float(x.mean()), sd=float(x.std()),
                  cv=float(x.std() / x.mean()) if x.mean() else None,
                  skew=float(stats.skew(x)), floor_effect=bool((x == 0).mean() > 0.15))
json.dump(OUT, open('psychometric.json', 'w'), indent=1, ensure_ascii=False)
print('%-10s %6s %6s %7s %7s %6s' % ('Subescala', 'alpha', 'r_iic', 'floor%', 'skew', 'piso?'))
for s in ['Vigor', 'Fadiga', 'Tensao', 'Raiva', 'Depressao', 'Confusao']:
    o = OUT[s]
    print('%-10s %6.2f %6.2f %6.0f%% %+7.2f %6s' % (
        s, o['alpha'], o['miic'], 100 * o['floor0'], o['skew'], 'SIM' if o['floor_effect'] else 'nao'))
