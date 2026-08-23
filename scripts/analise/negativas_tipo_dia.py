# -*- coding: utf-8 -*-
# Comportamento das dimensoes NEGATIVAS do humor por TIPO DE DIA de treino.
# Tipos (tabela real do microciclo): HIIT (D2,D4,D7) | Amistoso/jogo (D3,D5) | Outro/tecnico-forca (D1 baseline, D6).
# Pergunta: as negativas sao sensiveis ao TIPO de estimulo (nao so a carga)? Trazem informacao alem do eixo energia-fadiga?
import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
from scipy import stats
import statsmodels.formula.api as smf
h=pd.read_csv('humor_anon.csv')
TIPO={1:'Outro',2:'HIIT',3:'Amistoso',4:'HIIT',5:'Amistoso',6:'Outro',7:'HIIT'}
NEG=[('Tensao','Tensão'),('Depressao','Depressão'),('Raiva','Raiva'),('Confusao','Confusão')]
POS=[('Vigor','Vigor'),('Fadiga','Fadiga')]
ALL=NEG+POS
h['tipo']=h['dia'].map(TIPO)
ad=h.groupby(['ID','dia'])[[k for k,_ in ALL]].mean().reset_index(); ad['tipo']=ad['dia'].map(TIPO)

res={'means':{},'am_vs_hiit':{},'midweek':{},'friedman':{},'acute':{},'mixed':{}}
# medias por tipo
for k,lab in ALL:
    res['means'][k]={t:float(ad[ad.tipo==t][k].mean()) for t in ['Outro','HIIT','Amistoso']}

def paired(sub,groupcol,a,b,k):
    piv=sub.groupby(['ID',groupcol])[k].mean().unstack().dropna()
    d=piv[a]-piv[b]; dz=d.mean()/d.std(ddof=1)
    p=stats.wilcoxon(piv[a],piv[b]).pvalue
    return float(piv[a].mean()),float(piv[b].mean()),float(dz),float(p),int(len(piv))

# Amistoso vs HIIT (todos os dias)
for k,lab in ALL:
    a,b,dz,p,n=paired(ad[ad.tipo.isin(['HIIT','Amistoso'])],'tipo','Amistoso','HIIT',k)
    res['am_vs_hiit'][k]=dict(lab=lab,amist=a,hiit=b,dz=dz,p=p,n=n)
# Amistoso (D3,D5) vs HIIT meio de semana (D2,D4) — controla posicao na semana
mid=ad[ad.dia.isin([2,3,4,5])].copy(); mid['g']=mid['dia'].map({2:'HIIT',4:'HIIT',3:'Amistoso',5:'Amistoso'})
for k,lab in ALL:
    a,b,dz,p,n=paired(mid,'g','Amistoso','HIIT',k)
    res['midweek'][k]=dict(lab=lab,amist=a,hiit=b,dz=dz,p=p,n=n)
# Friedman entre 3 tipos
for k,lab in ALL:
    piv=ad.groupby(['ID','tipo'])[k].mean().unstack().dropna()
    fr=stats.friedmanchisquare(piv['Outro'],piv['HIIT'],piv['Amistoso'])
    res['friedman'][k]=dict(lab=lab,chi=float(fr.statistic),p=float(fr.pvalue),W=float(fr.statistic/(len(piv)*2)),n=int(len(piv)))
# Efeito agudo pre->pos por tipo
pp=h[h.momento.isin(['pre','pos'])]
for k,lab in ALL:
    res['acute'][k]={'lab':lab}
    for t in ['HIIT','Amistoso']:
        dd=[d for d in range(1,8) if TIPO[d]==t]
        w=pp[pp.dia.isin(dd)].pivot_table(index=['ID','dia'],columns='momento',values=k).dropna()
        res['acute'][k][t]=float((w['pos']-w['pre']).mean())
# Modelo misto: escore ~ C(tipo) + posicao_semana, random intercept por atleta (retem todos os dados)
adm=ad.copy(); adm['semana']=(adm['dia']-1)/6.0
for k,lab in ALL:
    try:
        m=smf.mixedlm(f"{k} ~ C(tipo, Treatment('HIIT')) + semana",adm,groups=adm['ID']).fit(reml=False)
        coefs={}
        for name in m.params.index:
            if 'Amistoso' in name or 'Outro' in name:
                coefs[name.split('[T.')[-1].rstrip(']')]={'b':float(m.params[name]),'p':float(m.pvalues[name])}
        res['mixed'][k]=dict(lab=lab,coefs=coefs)
    except Exception as e:
        res['mixed'][k]=dict(lab=lab,err=str(e))

json.dump(res,open('negativas_tipo_dia.json','w'),ensure_ascii=False,indent=1)
# ---- print resumo ----
print("MEDIA POR TIPO (Outro / HIIT / Amistoso):")
for k,lab in ALL:
    m=res['means'][k]; print(f"  {lab:10s} {m['Outro']:.2f} / {m['HIIT']:.2f} / {m['Amistoso']:.2f}")
print("\nAMISTOSO vs HIIT meio-de-semana (controlado):")
for k,lab in NEG:
    r=res['midweek'][k]; print(f"  {lab:10s} dz={r['dz']:+.2f} p={r['p']:.3f}")
print("\nMISTO (ref=HIIT), coef Amistoso:")
for k,lab in NEG:
    c=res['mixed'][k].get('coefs',{}).get('Amistoso',{}); print(f"  {lab:10s} b={c.get('b',float('nan')):+.2f} p={c.get('p',float('nan')):.3f}")
print("[salvo negativas_tipo_dia.json]")
