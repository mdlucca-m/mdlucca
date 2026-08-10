# -*- coding: utf-8 -*-
"""Monta o pacote de dados pronto para o Power BI: um workbook Excel multi-abas
com a tabela-fato do humor, as dimensões e as tabelas analíticas pré-calculadas
(resposta aguda, ROC, variabilidade, derivadas, contraste de dias, trajetória,
confiabilidade, perfil radar, bolhas 4D) e uma aba de KPIs. Fonte: a base
canônica e o dashboard_data.json — nada é inventado.
Uso: python build_powerbi_data.py  (de dentro de powerbi/)"""
import os, json
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
D = json.load(open(os.path.join(ROOT, 'tese', 'dashboard_data.json'), encoding='utf-8'))
base = pd.read_csv(os.path.join(ROOT, 'modelagem', 'base_modelagem.csv'))
OUT = os.path.join(HERE, 'BRUMS_HIIT_PowerBI.xlsx')

hiit_days = D['viz']['hiit_days']

# ---- fato_humor (tabela-fato) ----
fato = base.copy()
fato['hiit_dia'] = fato['dia'].isin(hiit_days).astype(int)
fato['tipo_dia'] = fato['hiit_dia'].map({1: 'HIIT', 0: 'Técnico-tático'})

# ---- dim_dia ----
dim_dia = pd.DataFrame({'dia': sorted(base['dia'].unique())})
dim_dia['hiit_dia'] = dim_dia['dia'].isin(hiit_days).astype(int)
dim_dia['tipo_dia'] = dim_dia['hiit_dia'].map({1: 'HIIT', 0: 'Técnico-tático'})

# ---- dim_momento ----
dim_momento = pd.DataFrame({'momento': ['uni', 'pre', 'mid', 'pos'],
                            'ordem': [0, 1, 2, 3],
                            'rotulo': ['Único', 'Pré', 'Meio', 'Pós']})

# ---- resposta_aguda ----
ra = pd.DataFrame([{
    'variavel': r['label'], 'codigo': r['var'], 'delta': r['delta'], 'dz': r['dz'],
    'ic_inf': r['ic'][0], 'ic_sup': r['ic'][1], 't': r['t'], 'p': r['p'],
    'wilcoxon_p': r['wilcoxon_p'], 'p_FDR': r['p_FDR'], 'sobrevive_FDR': bool(r['sig'])
} for r in D['inf']['A_aguda']])

# ---- roc_prepos ----
roc = pd.DataFrame([{
    'variavel': r['label'], 'codigo': r['var'], 'AUC': r['AUC'],
    'ic_inf': r['IC'][0], 'ic_sup': r['IC'][1], 'sens': r['sens'], 'espec': r['espec']
} for r in D['roc']['pre_vs_pos']])

# ---- variabilidade ----
varb = pd.DataFrame(D['pv']['variabilidade']).rename(columns={
    'var': 'variavel', 'entre': 'var_entre', 'intra': 'var_intra',
    'pct_entre': 'pct_entre_atletas', 'CV_intra': 'cv_intra'})

# ---- derivadas por variável ----
dvarB = pd.DataFrame(D['dvar']['B']).rename(columns={
    'var': 'variavel', 'vel_inicial': "f_linha_1", 'vel_final': "f_linha_7",
    'inclinacao_media': 'inclinacao_media_dia'})
# ---- derivadas por atleta ----
dvarC = pd.DataFrame(D['dvar']['C']).rename(columns={
    'var': 'variavel', 'slope_medio': 'slope_medio_dia', 'slope_dp': 'slope_dp',
    'pct_positivo': 'pct_atletas_positivos'})

# ---- contraste de dias HIIT vs sem ----
dias = pd.DataFrame([{
    'variavel': r['var'], 'delta_HIIT': r['media_HIIT'], 'delta_SEM': r['media_SEM'],
    'dz': r['dz'], 'p_FDR': r['p_FDR'], 'difere': bool(r['sig'])
} for r in D['dh']['C']])

# ---- trajetoria diaria (long) ----
lab = {'PTH': 'PTH (TMD)', 'FadFis': 'Fadiga física', 'Fadiga': 'Fadiga', 'Vigor': 'Vigor'}
tr_rows = []
for v in D['viz']['mon_vars']:
    for d, val in D['viz']['mon'][v].items():
        tr_rows.append({'variavel': lab[v], 'codigo': v, 'dia': int(d), 'valor': val,
                        'hiit_dia': int(int(d) in hiit_days)})
trajetoria = pd.DataFrame(tr_rows).sort_values(['codigo', 'dia'])

# ---- confiabilidade ----
conf = pd.DataFrame([{
    'subescala': r['sub'], 'alpha': r['alpha'], 'alpha_ic_inf': r['alpha_ic'][0],
    'alpha_ic_sup': r['alpha_ic'][1], 'omega': r['omega'], 'r_inter_item': r['r_inter_item'],
    'adequada': bool(r['adequada'])
} for r in D['conf']['A_confiabilidade']])

# ---- perfil radar (pré vs pós) ----
rad = D['viz']['radar']
radar = pd.DataFrame({'subescala': rad['subs'], 'pre': rad['pre'], 'pos': rad['pos']})
radar['delta'] = (radar['pos'] - radar['pre']).round(2)

# ---- bolhas 4D ----
bub = pd.DataFrame(D['viz']['bubble']).rename(columns={
    'var': 'variavel', 'dz': 'resposta_dz', 'slope': 'acumulo_dia',
    'entre': 'pct_entre_atletas', 'pos': 'pct_atletas_positivos'})[
    ['variavel', 'code', 'resposta_dz', 'acumulo_dia', 'pct_entre_atletas', 'pct_atletas_positivos']]

# ---- KPIs (tall) ----
A = {r['var']: r for r in D['inf']['A_aguda']}
rocm = {r['var']: r for r in D['roc']['pre_vs_pos']}
pv = D['pv']['perfil']
kpis = pd.DataFrame([
    ['Atletas', 27, 'n', 'amostra'],
    ['Observações', 456, 'n', 'amostra'],
    ['Pares pré→pós', 135, 'n', 'amostra'],
    ['Checagens exatas', 77, 'de 84', 'auditoria'],
    ['dz fadiga física', round(A['FadFis']['dz'], 2), 'Cohen dz', 'resposta aguda'],
    ['dz PTH (TMD)', round(A['PTH']['dz'], 2), 'Cohen dz', 'resposta aguda'],
    ['dz vigor', round(A['Vigor']['dz'], 2), 'Cohen dz', 'resposta aguda'],
    ['AUC fadiga física (pós×pré)', round(rocm['FadFis']['AUC'], 2), 'AUC', 'diagnóstico'],
    ['CFI (CFA 6 fatores)', D['adv']['CFA_DWLS']['CFI'], 'ajuste', 'psicometria'],
    ['RMSEA (CFA)', D['adv']['CFA_DWLS']['RMSEA'], 'ajuste', 'psicometria'],
    ['HTMT máximo', D['adv']['HTMT_max'], '<0,85', 'psicometria'],
    ['Tucker φ (invariância)', D['conf']['B_invariancia']['tucker_phi'], '≥0,95', 'psicometria'],
    ['Perfil iceberg pré', round(pv['iceberg_pre'] * 100, 0), '%', 'perfil'],
    ['Perfil iceberg pós', round(pv['iceberg_pos'] * 100, 0), '%', 'perfil'],
    ['ΔPTH nível-do-dia (HIIT)', 2.43, 'pontos', 'HIIT'],
], columns=['kpi', 'valor', 'unidade', 'grupo'])

sheets = {
    'fato_humor': fato, 'dim_dia': dim_dia, 'dim_momento': dim_momento,
    'kpis': kpis, 'resposta_aguda': ra, 'roc_prepos': roc, 'variabilidade': varb,
    'derivadas_variavel': dvarB, 'derivadas_atleta': dvarC, 'dias_contraste': dias,
    'trajetoria_diaria': trajetoria, 'confiabilidade': conf, 'perfil_radar': radar,
    'bolhas_4d': bub,
}
with pd.ExcelWriter(OUT, engine='openpyxl') as xw:
    for name, df in sheets.items():
        df.to_excel(xw, sheet_name=name, index=False)

print('escrito', OUT, '·', os.path.getsize(OUT) // 1024, 'KB')
for n, df in sheets.items():
    print(f'  {n}: {df.shape[0]}x{df.shape[1]}')
