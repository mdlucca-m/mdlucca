import pandas as pd, numpy as np
from scipy import stats
p='/root/.claude/uploads/9415069c-cc7c-5eeb-b631-02958f369474/dee6d6e0-resultados_handebol.xlsx'
d=pd.read_excel(p,sheet_name='Dados Análise').iloc[:,:13].dropna(subset=['Grupo','Dia'])
d['Momento']=d['Grupo'].map({1:'Pré',2:'Pós',3:'Rec'})
TMD='TMD (Perturbação Total de Humor)'
pre=d[d.Momento=='Pré'][TMD]; pos=d[d.Momento=='Pós'][TMD]
t,pv=stats.ttest_ind(pos,pre,equal_var=False)
# Cohen's d
def cohend(a,b):
    na,nb=len(a),len(b); sp=np.sqrt(((na-1)*a.std()**2+(nb-1)*b.std()**2)/(na+nb-2))
    return (a.mean()-b.mean())/sp
print('TMD Pré=%.1f Pós=%.1f  t=%.2f p=%.4f d=%.2f'%(pre.mean(),pos.mean(),t,pv,cohend(pos,pre)))
for v in ['Vigor','Fadiga','Tensão','Depressão','Raiva','Confusão']:
    a=d[d.Momento=='Pós'][v]; b=d[d.Momento=='Pré'][v]
    t,pv=stats.ttest_ind(a,b,equal_var=False)
    print('%-10s Pré=%.1f Pós=%.1f  d=%+.2f  p=%.3f'%(v,b.mean(),a.mean(),cohend(a,b),pv))
# correlation matrix
print('\nCorrelações (Spearman) com TMD:')
for v in ['Vigor','Fadiga','Tensão','Depressão','Raiva','Confusão','Fadiga_Física','Fadiga_Mental']:
    r,pv=stats.spearmanr(d[v],d[TMD])
    print('  %-14s r=%+.2f p=%.3g'%(v,r,pv))
