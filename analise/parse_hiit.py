import pandas as pd, numpy as np, json
raw = pd.read_excel('/root/.claude/uploads/9415069c-cc7c-5eeb-b631-02958f369474/d472c957-HIIT_FC_PSE.xlsx', header=None)
# Row0 dates at cols 1,19,37,55 ; sessions span 18 cols each
dates = ['2024-04-22','2024-04-24','2024-04-27','2024-04-29']
blocks = [('Aquecimento',0),('Série 1',3),('Série 2',6),('Série 3',9),('Série 4',12)]  # each Pré,Pós,PSE
recov_off = 15  # 1', 3', PSE
rows=[]
for si,base in enumerate([1,19,37,55]):
    date=dates[si]
    for r in range(3, raw.shape[0]):
        atleta = raw.iat[r,0]
        if pd.isna(atleta): continue
        for bname,off in blocks:
            pre=raw.iat[r,base+off]; pos=raw.iat[r,base+off+1]; pse=raw.iat[r,base+off+2]
            rows.append(dict(sessao=si+1,data=date,atleta=str(atleta).strip(),bloco=bname,
                             fc_pre=pre,fc_pos=pos,pse=pse))
        # recovery
        rec1=raw.iat[r,base+recov_off]; rec3=raw.iat[r,base+recov_off+1]; rpse=raw.iat[r,base+recov_off+2]
        rows.append(dict(sessao=si+1,data=date,atleta=str(atleta).strip(),bloco='Recuperação',
                         fc_pre=rec1,fc_pos=rec3,pse=rpse))
df=pd.DataFrame(rows)
for c in ['fc_pre','fc_pos','pse']:
    df[c]=pd.to_numeric(df[c],errors='coerce')
df.to_csv('/home/user/mdlucca/analise/hiit_long.csv',index=False)
print('atletas:', df['atleta'].nunique(), '| linhas:', len(df))
series=df[df.bloco.str.startswith('Série')].copy()
series['delta']=series.fc_pos-series.fc_pre
print('\n== FC (bpm) e PSE por Série (média das 4 sessões) ==')
g=series.groupby('bloco').agg(fc_pre=('fc_pre','mean'),fc_pos=('fc_pos','mean'),delta=('delta','mean'),pse=('pse','mean')).round(1)
print(g.to_string())
print('\n== Por sessão (Séries): FC Pós média, PSE média ==')
print(series.groupby('sessao').agg(fc_pos=('fc_pos','mean'),pse=('pse','mean')).round(1).to_string())
# PSE da sessão (carga interna) = média PSE por atleta/sessão
print('\n== FC máx atingida (Pós Série4) e range ==')
s4=df[df.bloco=='Série 4']
print('FC Pós Série4: média %.0f  min %.0f  max %.0f'%(s4.fc_pos.mean(),s4.fc_pos.min(),s4.fc_pos.max()))
aq=df[df.bloco=='Aquecimento']
print('FC Pré Aquecimento (basal): média %.0f'%aq.fc_pre.mean())
