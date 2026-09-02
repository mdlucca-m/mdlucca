# -*- coding: utf-8 -*-
"""Constrói a base única do estudo, a partir dos JSON canônicos do pipeline V2.
Camadas 1 e 2. A camada 3 (acervo das planilhas) fica em colher_planilhas.py."""
import json, sqlite3, os, datetime, itertools, numpy as np
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JS=os.environ.get("HH_JSON") or os.path.join(RAIZ,"dados")   # os JSON canônicos vivem no repositório
DB=os.path.join(RAIZ,"base","humor_handebol.sqlite")
def j(n): return json.load(open(os.path.join(JS,n),encoding='utf-8'))
B=j("V2_base.json"); Q=j("V2_perfis.json"); A1=j("V2_a1.json"); A2=j("V2_a2.json")
A3=j("V2_a3.json"); AU=j("V2_audit.json")

SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']; V7=SUB+['TMD']
VX=V7+['Fad.Física','Fad.Mental','Epworth','PSS']
COL={'Tensão':'tensao','Depressão':'depressao','Raiva':'raiva','Vigor':'vigor','Fadiga':'fadiga',
     'Confusão':'confusao','TMD':'pth','Fad.Física':'fadiga_fisica','Fad.Mental':'fadiga_mental',
     'Epworth':'epworth','PSS':'pss'}
FAIXA={0:'Favorável',1:'Neutra',2:'Neutra',3:'De risco',4:'De risco',5:'De risco'}
NOMES=Q['NOMES']; NORMA=B['NORMA']; CARGA=B['CARGA']

os.makedirs(os.path.dirname(DB), exist_ok=True)
if os.path.exists(DB): os.remove(DB)
for suf in ('-wal','-shm'):
    if os.path.exists(DB+suf): os.remove(DB+suf)
cx=sqlite3.connect(DB); cx.executescript(open(os.path.join(RAIZ,"base","esquema.sql")).read())

# ---------------- variavel ----------------
MET={'Tensão':('Tensão','BRUMS',0,16,'alto pior'),'Depressão':('Depressão','BRUMS',0,16,'alto pior'),
     'Raiva':('Raiva','BRUMS',0,16,'alto pior'),'Vigor':('Vigor','BRUMS',0,16,'alto melhor'),
     'Fadiga':('Fadiga','BRUMS',0,16,'alto pior'),'Confusão':('Confusão','BRUMS',0,16,'alto pior'),
     'TMD':('Perturbação total do humor','composto',-16,80,'alto pior'),
     'Fad.Física':('Fadiga física','fadiga',0,10,'alto pior'),
     'Fad.Mental':('Fadiga mental','fadiga',0,10,'alto pior'),
     'Epworth':('Sonolência diurna (Epworth)','sono',0,24,'alto pior'),
     'PSS':('Estresse percebido (PSS)','estresse',0,56,'alto pior')}
cx.executemany("INSERT INTO variavel VALUES (?,?,?,?,?,?,?,?)",
  [(v,MET[v][0],MET[v][1],MET[v][2],MET[v][3],MET[v][4],
    NORMA.get(v,[None,None])[0], NORMA.get(v,[None,None])[1]) for v in VX])

# ---------------- dia ----------------
reg=B['registros']
JAN={}
for d in range(1,8):
    hs=sorted(r['ts'][11:16] for r in reg if r['dia']==d)
    JAN[d]=f"{hs[0]} às {hs[-1]}"
for d in range(1,8):
    c=CARGA[str(d)]
    cx.execute("INSERT INTO dia VALUES (?,?,?,?,?,?,?,?,?,?)",
      (d, (datetime.date(2024,4,20)+datetime.timedelta(days=d)).isoformat(), c['tipo'], c['cont'],
       c['h'], c['ses'], c['acum'],
       sum(1 for r in reg if r['dia']==d), len({r['a'] for r in reg if r['dia']==d}), JAN[d]))

# ---------------- registro ----------------
def periodo(h):
    h=int(h[:2])
    return 'madrugada' if h<6 else ('manhã' if h<12 else ('tarde' if h<18 else 'noite'))
porad={}
for r in reg: porad.setdefault((r['a'],r['dia']),[]).append(r)
for k in porad: porad[k].sort(key=lambda x:x['ts'])
i=0
for (a,d),g in sorted(porad.items(), key=lambda x:(x[0][1],x[0][0])):
    for o,r in enumerate(g,1):
        if d==1: mom='único'
        elif len(g)==1: mom='único'
        elif o==1: mom='pré'
        elif o==len(g): mom='pós'
        else: mom='intermediário'
        i+=1
        cx.execute("INSERT INTO registro VALUES (?,?,?,?,?,?,?,?,"+",".join(["?"]*11)+")",
          (i,a,d,r['ts'],r['ts'][11:16],periodo(r['ts'][11:16]),mom,o,
           *[r.get(v) for v in VX]))

# ---------------- atleta_dia ----------------
lab=Q['lab_AD']; diaAD=Q['dia_AD']; aAD=Q['a_AD']; T=Q['T_AD']
mapa={(aAD[i],diaAD[i]):(lab[i],T[i]) for i in range(len(lab))}
for p in B['pares']:
    k=(p['a'],p['dia']); l,t=mapa[k]
    cx.execute("INSERT INTO atleta_dia VALUES (?,?,?,"+",".join(["?"]*11)+","+",".join(["?"]*6)+",?,?)",
      (p['a'],p['dia'],p['nobs'],*[p.get(v) for v in VX],*t,NOMES[l],FAIXA[l]))

# ---------------- atleta ----------------
for a in sorted({p['a'] for p in B['pares']}):
    ds={p['dia'] for p in B['pares'] if p['a']==a}
    npp=sum(1 for p in B['prepos'] if p['a']==a)
    nreg=sum(1 for r in reg if r['a']==a)
    ass='completa' if len(ds)==7 else ('parcial' if len(ds)>=5 else 'esparsa')
    cx.execute("INSERT INTO atleta VALUES (?,?,?,?,?,?,?)",
      (a,nreg,len(ds),npp,int(1 in ds),int(7 in ds),ass))

# ---------------- pre_pos ----------------
for p in B['prepos']:
    for v in VX:
        a_,b_=p.get('pre_'+v), p.get('pos_'+v)
        if a_ is None and b_ is None: continue
        cx.execute("INSERT INTO pre_pos VALUES (?,?,?,?,?,?,?,?)",
          (p['a'],p['dia'],p.get('h_pre'),p.get('h_pos'),v,a_,b_,
           (b_-a_) if (a_ is not None and b_ is not None) else None))

# ---------------- series ----------------
for v,s in A1['SER'].items():
    for d in range(1,8):
        cx.execute("INSERT INTO serie_diaria VALUES (?,?,?,?,?,?,?,?,?)",
          (v,d,s['med'][d-1],s['ep'][d-1],s['sm'][d-1],
           s['d1'][d-2] if d>=2 else None, s['d2'][d-3] if d>=3 else None,
           s['piso'], int((d-1) in s['choque'])))
for nm,s in A3['SERP'].items():
    for d in range(1,8):
        cx.execute("INSERT INTO serie_perfil VALUES (?,?,?,?,?,?,?,?)",
          (nm,d,s['y'][d-1],s['se'][d-1],s['sm'][d-1],
           s['d1'][d-2] if d>=2 else None, s['piso'], int((d-1) in s['choque'])))

# ---------------- unidades e auditoria ----------------
cx.executemany("INSERT INTO unidade_analise VALUES (?,?,?,?,?,?)",
  [(u['sigla'],u['nome'],u['n'],u['regra'],u['usada_em'],u['vies']) for u in AU['UNIDADES']])
cx.executemany("INSERT INTO auditoria VALUES (?,?,?,?,?,?)",
  [(a['id'],a['titulo'],a['achado'],a['correcao'],a['impacto'],a['gravidade']) for a in AU['ACHADOS']])

# ---------------- resultados ----------------
R=[]
def add(**k):
    k.setdefault('significativo', int((k.get('p_ajustado') if k.get('p_ajustado') is not None else k.get('p') or 1)<.05))
    R.append(k)
for v,d in A1['DESC'].items():
    for rot,val,lab_ in [('média',d['m'],'DP'),('mediana',d['md'],'AIQ'),('média aparada 20%',d['tm'],'MAD')]:
        add(dominio='descritiva',via='robusta',unidade='U-AD',variavel=v,recorte='geral',
            teste=rot,estatistica=val,rotulo_estatistica=rot,p=None,
            efeito=d['sd'] if rot=='média' else (d['aiq'] if rot=='mediana' else d['mad']),
            rotulo_efeito=lab_,ic_inf=d['ic'][0] if rot=='média' else (d['md_ic'][0] if rot=='mediana' else None),
            ic_sup=d['ic'][1] if rot=='média' else (d['md_ic'][1] if rot=='mediana' else None),
            n=d['n'],artigo='ambos',significativo=0)
    add(dominio='descritiva',via='paramétrica',unidade='U-AD',variavel=v,recorte='normalidade',
        teste='Shapiro-Wilk',estatistica=d['W'],rotulo_estatistica='W',p=d['pW'],n=d['n'],artigo='ambos')
    add(dominio='descritiva',via='descritiva',unidade='U-AD',variavel=v,recorte='efeito de piso',
        teste='percentual no valor mínimo',estatistica=d['piso'],rotulo_estatistica='%',p=None,
        n=d['n'],artigo='ambos',significativo=int(d['piso']>15))
for v,d in A1['ICC'].items():
    add(dominio='confiabilidade',via='paramétrica',unidade='U-AD',variavel=v,recorte='entre dias',
        teste='CCI (1,1)',estatistica=d['icc'],rotulo_estatistica='CCI',p=None,
        efeito=d['mvd'],rotulo_efeito='MVD',n=d['n'],artigo='ambos',significativo=0)
for v,d in A1['SER'].items():
    add(dominio='série',via='robusta',unidade='U-AD',variavel=v,recorte='D1→D7',
        teste='piso de ruído',estatistica=d['dtot'],rotulo_estatistica='Δ',p=None,
        efeito=d['razao'],rotulo_efeito='|Δ|/piso',n=166,artigo='ambos',significativo=int(d['sinal']))
for v,d in A2['NP'].items():
    add(dominio='tendência',via='não paramétrica',unidade='U-AD',variavel=v,recorte='D1..D7',
        teste='Friedman',estatistica=d['chi'],rotulo_estatistica='χ²',gl='6',p=d['p'],
        efeito=d['W'],rotulo_efeito='W de Kendall',n=d['n'],artigo='ambos')
    add(dominio='tendência',via='não paramétrica',unidade='U-AD',variavel=v,recorte='ordenada D1→D7',
        teste='L de Page',estatistica=d['z'],rotulo_estatistica='z',p=d['pz'],n=d['n'],artigo='ambos')
    for e in d['PH']:
        add(dominio='contraste',via='não paramétrica',unidade='U-AD',variavel=v,recorte=e['par'],
            teste='Wilcoxon',estatistica=e['d'],rotulo_estatistica='Δ',p=e['p'],
            p_ajustado=e['ph'],metodo_ajuste='Holm',efeito=e['r'],rotulo_efeito='r',n=e['n'],artigo='ambos')
for v,d in A2['PA'].items():
    add(dominio='tendência',via='paramétrica',unidade='U-AD',variavel=v,recorte='D1..D7',
        teste='ANOVA de medidas repetidas (Greenhouse-Geisser)',estatistica=d['F'],rotulo_estatistica='F',
        gl=f"{d['gl'][0]}, {d['gl'][1]}",p=d['pGG'],efeito=d['eta2p'],rotulo_efeito='η²p',n=d['n'],artigo='A2')
    add(dominio='contraste',via='paramétrica',unidade='U-AD',variavel=v,recorte='D1→D7',
        teste='t pareado',estatistica=d['t'],rotulo_estatistica='t',gl=str(d['ndz']-1),p=d['pt'],
        efeito=d['dz'],rotulo_efeito='dz',ic_inf=d['ic'][0],ic_sup=d['ic'][1],n=d['ndz'],artigo='A2')
for v,d in A3['LMM'].items():
    if 'b_dia' not in d: continue
    add(dominio='tendência',via='modelo misto',unidade='U-AD',variavel=v,recorte='efeito linear do dia',
        teste='modelo linear misto (intercepto aleatório por atleta)',estatistica=d['b_dia'],
        rotulo_estatistica='b por dia',p=d['p'],efeito=d['icc'],rotulo_efeito='CCI do atleta',
        ic_inf=d['ic'][0],ic_sup=d['ic'][1],n=166,artigo='A2')
for v,d in A3['NIV'].items():
    add(dominio='contraste',via='não paramétrica',unidade='U-AD',variavel=v,recorte='entre estímulos',
        teste='Friedman',estatistica=d['chi'],rotulo_estatistica='χ²',gl='2',p=d['p'],
        efeito=d['W'],rotulo_efeito='W',n=d['n'],artigo='ambos')
    add(dominio='contraste',via='paramétrica',unidade='U-AD',variavel=v,recorte='entre estímulos',
        teste='ANOVA de medidas repetidas',estatistica=d['F'],rotulo_estatistica='F',gl=f"2, {2*(d['n']-1)}",
        p=d['pF'],efeito=d['eta2p'],rotulo_efeito='η²p',n=d['n'],artigo='A2')
for v,dd in A3['AG'].items():
    for t,d in dd.items():
        add(dominio='contraste',via='não paramétrica',unidade='U-AD',variavel=v,recorte=f'pré×pós — {t}',
            teste='Wilcoxon',estatistica=d['d'],rotulo_estatistica='Δ',p=d['p'],
            efeito=d['r'],rotulo_efeito='r',n=d['n'],artigo='ambos')
        add(dominio='contraste',via='paramétrica',unidade='U-AD',variavel=v,recorte=f'pré×pós — {t}',
            teste='t pareado',estatistica=d['t'],rotulo_estatistica='t',p=d['pt'],
            efeito=d['dz'],rotulo_efeito='dz',n=d['n'],artigo='A2')
for k,d in A3['MAT'].items():
    a_,b_=k.split('×')
    add(dominio='associação',via='não paramétrica',unidade='U-AD',variavel=k,recorte='geral',
        teste='Spearman',estatistica=d['rho'],rotulo_estatistica='ρ',p=d['p'],p_ajustado=d['ph'],
        metodo_ajuste='Holm',n=166,artigo='ambos')
    add(dominio='associação',via='paramétrica',unidade='U-AD',variavel=k,recorte='geral',
        teste='Pearson',estatistica=d['r'],rotulo_estatistica='r',p=d['pr'],p_ajustado=d['phr'],
        metodo_ajuste='Holm',n=166,artigo='A2')
AS=j("V2_assoc.json")
for x in AS['ACOPL']['dias']:
    add(dominio='associação',via='não paramétrica',unidade='U-AD',variavel='Fadiga×TMD',
        recorte=f"D{x['dia']}",teste='Spearman',estatistica=x['rho'],rotulo_estatistica='ρ',
        p=x['p'],n=x['n'],artigo='A1')
add(dominio='tendência',via='não paramétrica',unidade='U-AD',variavel='Fadiga×TMD',
    recorte='acoplamento D1→D7',teste='Spearman sobre os sete coeficientes',
    estatistica=AS['ACOPL']['tendencia_rho'],rotulo_estatistica='ρ',
    p=AS['ACOPL']['tendencia_p'],n=7,artigo='A1')
for k,d in AS['PLANOS'].items():
    add(dominio='associação',via='não paramétrica',unidade='atleta',variavel=k,recorte='entre atletas',
        teste='Spearman sobre as médias individuais',estatistica=d['entre_rho'],
        rotulo_estatistica='ρ',p=d['entre_p'],n=d['entre_n'],artigo='A1')
    add(dominio='associação',via='não paramétrica',unidade='U-AD',variavel=k,recorte='dentro do atleta',
        teste='Spearman sobre os desvios da média do atleta',estatistica=d['dentro_rho'],
        rotulo_estatistica='ρ',p=d['dentro_p'],n=d['dentro_n'],artigo='A1')
for nm,d in A3['CQ'].items():
    add(dominio='categórica',via='não paramétrica',unidade='U-AD',variavel=nm,recorte='estabilidade D1..D7',
        teste='Q de Cochran',estatistica=d['Q'],rotulo_estatistica='Q',gl='6',p=d['p'],n=d['n'],artigo='ambos')
for t,d in A3['MCN'].items():
    add(dominio='categórica',via='não paramétrica',unidade='U-AD',variavel='Faixa de risco',
        recorte=f'migração pré→pós — {t}',teste='McNemar',estatistica=d['chi'],rotulo_estatistica='χ²',
        gl='1',p=d['p'],p_ajustado=d.get('ph'),metodo_ajuste='Holm' if 'ph' in d else None,
        efeito=d['entra']-d['sai'],rotulo_efeito='entram − saem',n=d['n'],artigo='ambos')
add(dominio='categórica',via='não paramétrica',unidade='U-AD',variavel='Perfil',recorte='perfil × estímulo',
    teste='qui-quadrado de contingência',estatistica=A3['chi'],rotulo_estatistica='χ²',gl=str(A3['gl']),
    p=A3['p_chi'],n=166,artigo='ambos')
add(dominio='categórica',via='não paramétrica',unidade='U-AD',variavel='Faixa',recorte='faixa × estímulo',
    teste='qui-quadrado de contingência',estatistica=A3['chi_f'],rotulo_estatistica='χ²',gl=str(A3['gl_f']),
    p=A3['p_f'],n=166,artigo='ambos')
cols=['dominio','via','unidade','variavel','recorte','teste','estatistica','rotulo_estatistica','gl',
      'p','p_ajustado','metodo_ajuste','efeito','rotulo_efeito','ic_inf','ic_sup','n','significativo','artigo']
cx.executemany(f"INSERT INTO resultado ({','.join(cols)}) VALUES ({','.join(['?']*len(cols))})",
               [tuple(r.get(c) for c in cols) for r in R])

# ---------------- prevalências ----------------
P=[]
for u,d in Q['REC'].items():
    for k,nm in enumerate(NOMES):
        P.append((u,'geral','todos',nm,d['prev'][k],d['n'],None))
for nm,s in A3['SERP'].items():
    for d in range(1,8):
        P.append(('U-AD','dia',f'D{d}',nm,s['y'][d-1],int(A3['nd'][d-1]),s['se'][d-1]))
for nm,dd in A3['PREV_EST'].items():
    for t,v in dd.items(): P.append(('U-AD','estimulo',t,nm,v,A3['NPOR'][t],None))
for nm,dd in A3['FAIXA_EST'].items():
    for t,v in dd.items(): P.append(('U-AD','estimulo',t,'Faixa '+nm,v,A3['NPOR'][t],None))
cx.executemany("INSERT INTO prevalencia (unidade,recorte_tipo,recorte,perfil,prevalencia,n,erro_padrao) "
               "VALUES (?,?,?,?,?,?,?)", P)
cx.commit()
n=lambda t: cx.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
print("base construída:", DB)
for t in ['atleta','dia','variavel','registro','atleta_dia','pre_pos','serie_diaria','serie_perfil',
          'unidade_analise','resultado','prevalencia','auditoria']:
    print(f"   {t:18} {n(t):6}")
cx.close()
