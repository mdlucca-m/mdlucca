import pandas as pd, numpy as np, json
p='/root/.claude/uploads/9415069c-cc7c-5eeb-b631-02958f369474/dee6d6e0-resultados_handebol.xlsx'
d=pd.read_excel(p,sheet_name='Dados Análise').iloc[:,:13].dropna(subset=['Grupo','Dia'])
d['Momento']=d['Grupo'].map({1:'Pré',2:'Pós',3:'Rec'})
cols={'Tensão':'Tensão','Depressão':'Depressão','Raiva':'Raiva','Vigor':'Vigor','Fadiga':'Fadiga',
      'Confusão':'Confusão','TMD (Perturbação Total de Humor)':'TMD','Fadiga_Física':'Fadiga física',
      'Fadiga_Mental':'Fadiga mental'}
brums=[]
for _,r in d.iterrows():
    o={'mom':r['Momento'],'dia':int(r['Dia']),'perfil':str(r['Classificação dos perfis'])}
    for k,v in cols.items(): o[v]=float(r[k])
    brums.append(o)
# HIIT long
h=pd.read_csv('analise/hiit_long.csv')
h=h.dropna(subset=['fc_pre','fc_pos'],how='all')
hiit=[]
for _,r in h.iterrows():
    hiit.append({'sessao':int(r['sessao']),'bloco':r['bloco'],
                 'fc_pre':None if pd.isna(r['fc_pre']) else float(r['fc_pre']),
                 'fc_pos':None if pd.isna(r['fc_pos']) else float(r['fc_pos']),
                 'pse':None if pd.isna(r['pse']) else float(r['pse'])})
data={'brums':brums,'brumsVars':list(cols.values()),'hiit':hiit}
json.dump(data,open('analise/data.json','w'),ensure_ascii=False)
print('brums',len(brums),'hiit',len(hiit),'vars',data['brumsVars'])
