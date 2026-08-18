"""
Erro de medida e menor mudança relevante para o monitoramento do humor:
  SEM  = erro-padrão de medida = DP * sqrt(1 - ICC)
  SEdiff = sqrt(2) * SEM  (erro-padrão da diferença entre duas medidas)
  MDC90 = 1,65 * SEdiff ; MDC95 = 1,96 * SEdiff  (mudança mínima detectável)
  SWC  = menor mudança relevante = 0,2 * DP entre atletas (limiar de Hopkins)
ICC de consistência das medidas repetidas (icc1) da própria amostra.

Saída: mdc.json
"""
import warnings; warnings.filterwarnings('ignore')
import json, numpy as np, pandas as pd

S = json.load(open('brums_stats3.json'))['icc']
h = pd.read_csv('hum_prof.csv')
DIMS = ['Vigor', 'Fadiga', 'Tensao', 'Depressao', 'Raiva', 'Confusao']
OUT = {}
for v in DIMS:
    icc = float(S[v]['icc1'])
    sd_tot = float(h[v].std())                              # DP total (para SEM)
    sd_bs = float(h.groupby('ID')[v].mean().std())          # DP entre atletas (para SWC)
    sem = sd_tot * np.sqrt(max(0.0, 1 - icc))
    sediff = np.sqrt(2) * sem
    OUT[v] = dict(icc=icc, sd_tot=sd_tot, sd_bs=sd_bs, sem=sem,
                  mdc90=1.65 * sediff, mdc95=1.96 * sediff, swc=0.2 * sd_bs)
json.dump(OUT, open('mdc.json', 'w'), indent=1, ensure_ascii=False)
for v in ['Vigor', 'Fadiga']:
    o = OUT[v]
    print('%s: ICC=%.2f SEM=%.2f | MDC90=%.1f MDC95=%.1f | SWC=%.1f (escala 0–16)' % (
        v, o['icc'], o['sem'], o['mdc90'], o['mdc95'], o['swc']))
print('OK mdc.json')
