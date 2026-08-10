"""Constrói a base analítica limpa a partir de COLETAS/Diario (fonte bruta)."""
import pandas as pd, numpy as np, re, unicodedata
import os
UP=os.environ.get('BRUMS_DATA_DIR','./data/')  # coloque aqui COLETAS.xlsx etc.
def _num(v):
    if pd.isna(v): return np.nan
    m=re.search(r'-?\d+', str(v)); return float(m.group()) if m else np.nan
def norm(s):
    s=str(s).strip().lower(); s=''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')
    return ' '.join(s.split())
GROUPS={'Tensão':['Apavorado','Ansioso','Preocupado','Tenso'],
 'Depressão':['Deprimido','Desanimado','Triste','Infeliz'],
 'Raiva':['Irritado','Zangado','Com Raiva','Mal-humorado'],
 'Vigor':['Animado','Com disposição','Com Energia','Alerta '],
 'Fadiga':['Esgotado','Exausto','Sonolento','Cansado'],
 'Confusão':['Confuso','Inseguro','Desorientado','Indeciso']}
ITEMKEY={'Apavorado':'tensao_1','Ansioso':'tensao_2','Preocupado':'tensao_3','Tenso':'tensao_4',
 'Deprimido':'depressao_1','Desanimado':'depressao_2','Triste':'depressao_3','Infeliz':'depressao_4',
 'Irritado':'raiva_1','Zangado':'raiva_2','Com Raiva':'raiva_3','Mal-humorado':'raiva_4',
 'Animado':'vigor_1','Com disposição':'vigor_2','Com Energia':'vigor_3','Alerta ':'vigor_4',
 'Esgotado':'fadiga_1','Exausto':'fadiga_2','Sonolento':'fadiga_3','Cansado':'fadiga_4',
 'Confuso':'confusao_1','Inseguro':'confusao_2','Desorientado':'confusao_3','Indeciso':'confusao_4'}
def load():
    d=pd.read_excel(UP+'df655e3d-COLETAS.xlsx',sheet_name='Diario',header=0).reset_index(drop=True)
    B='Escala de Humor de Brunel (BRUMS) '
    X=pd.DataFrame()
    X['aid']=d['Nome'].map(norm)
    X['ts']=pd.to_datetime(d['Carimbo de data/hora'])
    X['day']=(X['ts'].dt.normalize()-pd.Timestamp('2024-04-20')).dt.days
    # itens
    items={}
    for s,g in GROUPS.items():
        for n in g:
            items[ITEMKEY[n]]=d[B+'['+n+']'].map(_num)
    IT=pd.DataFrame(items)
    for s,g in GROUPS.items():
        X[s]=IT[[ITEMKEY[n] for n in g]].sum(axis=1,min_count=4)
    X['PTH']=X[['Tensão','Depressão','Raiva','Fadiga','Confusão']].sum(axis=1)-X['Vigor']
    X['FadFis']=d['Qual seu nível de FADIGA FÍSICA no momento?'].map(_num)
    X['FadMen']=d['Qual seu nível de FADIGA MENTAL no momento?'].map(_num)
    estmap={'Péssimo':0,'Ruim':1,'Regular':2,'Bem':3,'Muito bem':4}
    X['EstFis']=d['Como você está se sentido agora fisicamente'].map(estmap)
    X['EstMen']=d['Como você está se sentido agora mentalmente'].map(estmap)
    epw=[c for c in d.columns if 'Probabilidade de cochilar' in c]
    X['Sonol']=pd.concat([d[c].map(_num) for c in epw],axis=1).sum(axis=1,min_count=1)
    pss=[c for c in d.columns if c.startswith('[')]
    rev=['sucesso','lidando bem','confiante','de acordo com a sua vontade','controlar as irritações','sob o seu controle','controlar a maneira']
    P=pd.DataFrame({c:(4-d[c].map(_num) if any(k in c for k in rev) else d[c].map(_num)) for c in pss})
    X['PSS']=P.sum(axis=1,min_count=10)
    IT.index=X.index
    X=pd.concat([X,IT],axis=1)
    # microcycle only
    M=X[X['day'].between(1,7)].copy().sort_values(['aid','day','ts']).reset_index(drop=True)
    M['moment']='Meio'
    first=M.groupby(['aid','day']).head(1).index; last=M.groupby(['aid','day']).tail(1).index
    cnt=M.groupby(['aid','day'])['ts'].transform('size')
    M.loc[first,'moment']='Pré'; M.loc[last,'moment']='Pós'; M.loc[cnt==1,'moment']='Único'
    M['hiit']=M['day'].isin([2,4,7])
    return M, list(ITEMKEY.values())
if __name__=='__main__':
    M,items=load()
    print("obs:",len(M)," atletas:",M['aid'].nunique()," dias:",sorted(M['day'].unique()))
    print("momentos:",M['moment'].value_counts().to_dict())
    M.to_pickle('clean.pkl')
    print("saved clean.pkl")
