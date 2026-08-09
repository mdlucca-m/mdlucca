"""
Reprodução independente das análises do estudo BRUMS/HIIT (handebol).
Uso:
    BRUMS_DATA_DIR=/caminho/para/xlsx  python3 reproduce.py
Espera encontrar em BRUMS_DATA_DIR: COLETAS.xlsx e HIIT_FC_PSE.xlsx (nomes com prefixo aceitos via glob).
Recalcula e compara com os valores reportados no artigo.
"""
import os, glob, warnings, numpy as np, pandas as pd
from scipy import stats, integrate
warnings.filterwarnings('ignore')
from clean_data import load, GROUPS, ITEMKEY

def main():
    M, items = load()
    subs6 = ['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
    it_by = {s:[ITEMKEY[n] for n in g] for s,g in GROUPS.items()}
    print(f"Base: {len(M)} obs | {M['aid'].nunique()} atletas | "
          f"{(M.moment=='Pré').sum()} pares pré/pós")

    # Descritivas (Tab.2)
    print("\n[Tab.2] Descritivas")
    for k in ['PTH','Vigor','Fadiga','Tensão','Depressão','Raiva','Confusão','FadFis','FadMen']:
        x = M[k].dropna()
        print(f"  {k:8} M={x.mean():.2f} DP={x.std(ddof=1):.2f} "
              f"assim={stats.skew(x):.2f} piso%={100*(x==0).mean():.1f}")

    # Confiabilidade (Tab.3)
    print("\n[Tab.3] alpha de Cronbach")
    def cron(X):
        X=X.dropna(); k=X.shape[1]
        return k/(k-1)*(1-X.var(ddof=1).sum()/X.sum(axis=1).var(ddof=1))
    for s in subs6:
        print(f"  {s:10} α={cron(M[it_by[s]]):.3f}")

    # Efeito do dia — ICC atleta e médias diárias (Tab.19)
    print("\n[Tab.19] Média diária PTH (2 passos)")
    ts = M.groupby(['aid','day'])['PTH'].mean().groupby('day').mean()
    print("  ", [round(ts.get(d),2) for d in range(1,8)])

    # Iceberg (Tab.20)
    M['iceberg']=(M['Vigor']>M[['Tensão','Depressão','Raiva','Fadiga','Confusão']].max(axis=1)).astype(int)
    print("\n[Tab.20] Iceberg %:", [round(100*v,1) for v in M.groupby('day')['iceberg'].mean()])

    # HIIT vs sem (Tab.25)
    tr=M[M.day.between(2,7)]
    h=tr[tr.hiit].groupby('aid')[subs6+['PTH','FadFis']].mean().mean()
    nh=tr[~tr.hiit].groupby('aid')[subs6+['PTH','FadFis']].mean().mean()
    print("\n[Tab.25] HIIT-sem diff PTH={:+.2f} Fadiga={:+.2f} FadFis={:+.2f} Vigor={:+.2f}".format(
        h['PTH']-nh['PTH'], h['Fadiga']-nh['Fadiga'], h['FadFis']-nh['FadFis'], h['Vigor']-nh['Vigor']))

    # Resposta aguda (Tab.22) — dz por observação
    pre=M[M.moment=='Pré']; pos=M[M.moment=='Pós']; pr=pre.merge(pos,on=['aid','day'],suffixes=('_pre','_pos'))
    print("\n[Tab.22] Resposta aguda (dz por observação):")
    for k in ['FadFis','Fadiga','PTH','Vigor']:
        dl=(pr[k+'_pos']-pr[k+'_pre']).dropna()
        print(f"  {k:8} Δ={dl.mean():+.2f} dz={dl.mean()/dl.std(ddof=1):+.2f}")

    # Hotelling T² (Tab.23)
    prt=pr[pr.day.between(2,7)]
    dd=pd.DataFrame({s:(prt[s+'_pos']-prt[s+'_pre']) for s in subs6}); dd['aid']=prt['aid'].values
    ath=dd.groupby('aid')[subs6].mean().dropna(); n=len(ath); p=6
    m=ath.mean().values; S=np.cov(ath.values.T)
    T2=n*m@np.linalg.inv(S)@m; F=(n-p)/(p*(n-1))*T2; pv=1-stats.f.cdf(F,p,n-p)
    print(f"\n[Tab.23] Hotelling T² 6 sub.: F(6,21)={F:.2f} p={pv:.3f} D={np.sqrt(m@np.linalg.inv(S)@m):.2f}")

    # Decomposição de variância (Tab.37)
    import statsmodels.formula.api as smf
    print("\n[Tab.37] Variância traço/dia/estado (% atleta):")
    for s in subs6:
        dat=M[['aid','day',s]].dropna().rename(columns={s:'y'}); dat['adk']=dat.aid.astype(str)+'_'+dat.day.astype(str)
        md=smf.mixedlm("y~1",dat,groups=dat['aid'],re_formula="1",vc_formula={"day":"0+C(adk)"}).fit(reml=True)
        va,vd,ve=md.cov_re.iloc[0,0],md.vcomp[0],md.scale; tot=va+vd+ve
        print(f"  {s:10} atleta={100*va/tot:.1f}% dia={100*vd/tot:.1f}% estado={100*ve/tot:.1f}%")

if __name__=='__main__':
    main()
