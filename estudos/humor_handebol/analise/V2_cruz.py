# -*- coding: utf-8 -*-
"""Anatomia dos cruzamentos entre séries diárias, por limiar e por derivadas.

Um cruzamento entre duas séries é um zero da série da diferença. Dizer que ele
ocorre em certa abscissa não basta: interessa saber com que velocidade a
diferença atravessa o zero, se essa travessia acelera ou freia, e em que
intervalo de dias a diferença permanece indistinguível de zero. Esta rotina
calcula essas quantidades e as grava para o texto e para as figuras.

Definições, todas sobre a série suavizada pelo filtro binomial 1-2-1:
  dif(d)      diferença entre as duas séries no dia d
  limiar      raiz da soma dos quadrados dos dois pisos de ruído
  cruzamento  abscissa em que dif muda de sinal, por interpolação linear
  velocidade  primeira derivada de dif no segmento que contém o cruzamento,
              expressa em limiares por dia
  aceleração  segunda derivada de dif, em limiares por dia ao quadrado
  zona de indecisão   intervalo contíguo de dias em torno do cruzamento no
              qual |dif| < limiar, isto é, no qual a diferença entre as duas
              séries não se distingue do ruído somado das duas
  resíduo do filtro   diferença entre a série observada e a suavizada, que é
              a componente de alta frequência removida
"""
import os, json
import numpy as np
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S=os.path.join(RAIZ,"dados")
A1=json.load(open(os.path.join(S,"V2_a1.json")))

def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z

VAR=['Vigor','Fadiga','TMD']
PARES=[('Vigor','Fadiga'),('Vigor','TMD'),('Fadiga','TMD')]
OB={v:np.array(A1['SER'][v]['med'],float) for v in VAR}
SM={v:suav(OB[v]) for v in VAR}
PI={v:float(A1['SER'][v]['piso']) for v in VAR}
EP={v:np.array(A1['SER'][v]['ep'],float) for v in VAR}

# -------- o que o filtro remove, em unidades do piso de cada série --------
FILTRO={}
for v in VAR:
    r=OB[v]-SM[v]
    FILTRO[v]=dict(observado=OB[v].tolist(), suavizado=SM[v].tolist(),
                   residuo=r.tolist(), piso=PI[v], ep=EP[v].tolist(),
                   residuo_em_pisos=(r/PI[v]).tolist(),
                   max_residuo_em_pisos=float(np.abs(r).max()/PI[v]),
                   media_abs_residuo=float(np.abs(r[1:-1]).mean()))
# resposta em frequência do núcleo [1/4,1/2,1/4]: H(w)=cos^2(w/2)
w=np.linspace(0,np.pi,181)
RESP=dict(w=w.tolist(), H=(np.cos(w/2)**2).tolist(),
          H_media_movel=((1+2*np.cos(w))/3).tolist())

def zeros(y, xs=None):
    """abscissas em que a série muda de sinal, por interpolação linear"""
    out=[]
    for i in range(len(y)-1):
        if y[i]==0 or y[i]*y[i+1]<0:
            out.append(1+i+abs(y[i])/(abs(y[i])+abs(y[i+1])))
    return out

def cruza_nivel(y, nivel):
    """abscissas em que |y| cruza o nível dado"""
    return zeros(np.abs(np.asarray(y,float))-nivel)

CRUZ={}
for a,b in PARES:
    d=SM[a]-SM[b]; lim=float(np.hypot(PI[a],PI[b]))
    d1=np.diff(d); d2=np.diff(d1)
    cs=zeros(d)
    itens=[]
    for c in cs:
        k=int(np.floor(c))-1                      # segmento que contém o cruzamento
        vel=float(d1[k])                          # pontos por dia
        # aceleração no ponto: média das duas segundas derivadas adjacentes
        viz=[d2[j] for j in (k-1,k) if 0<=j<len(d2)]
        ace=float(np.mean(viz)) if viz else float('nan')
        # zona de indecisão: intervalo contíguo em torno de c com |dif| < limiar
        marcas=sorted(cruza_nivel(d, lim))
        antes=[m for m in marcas if m<c]; depois=[m for m in marcas if m>c]
        ini = max(antes) if antes else 1.0
        fim = min(depois) if depois else 7.0
        itens.append(dict(abscissa=float(c), velocidade=vel,
                          velocidade_em_limiares=float(vel/lim),
                          aceleracao=ace, aceleracao_em_limiares=float(ace/lim),
                          zona_ini=float(ini), zona_fim=float(fim),
                          zona_largura=float(fim-ini),
                          nitido=bool(abs(vel)/lim >= 1.0)))
    CRUZ[f"{a}×{b}"]=dict(a=a, b=b, dif=d.tolist(), limiar=lim,
                          d1=d1.tolist(), d2=d2.tolist(),
                          d1_em_limiares=(d1/lim).tolist(),
                          d2_em_limiares=(d2/lim).tolist(),
                          d1_ini=float(d[0]), d7_fim=float(d[-1]),
                          estabelecida=bool(abs(d[0])>lim and abs(d[-1])>lim),
                          cruzamentos=itens)

json.dump(dict(FILTRO=FILTRO, RESPOSTA=RESP, CRUZ=CRUZ, PARES=[list(p) for p in PARES]),
          open(os.path.join(S,"V2_cruz.json"),"w",encoding="utf-8"), ensure_ascii=False)

b_=lambda x,d=2: f"{x:.{d}f}".replace('.',',').replace('-','−')
print("O QUE O FILTRO BINOMIAL REMOVE, EM UNIDADES DO PISO DE CADA SÉRIE")
print(f"  {'série':<8}{'piso':>7}{'|resíduo| médio':>17}{'maior |resíduo|':>17}{'em pisos':>10}")
for v in VAR:
    f=FILTRO[v]
    print(f"  {v:<8}{f['piso']:7.2f}{f['media_abs_residuo']:17.3f}"
          f"{max(abs(x) for x in f['residuo']):17.3f}{f['max_residuo_em_pisos']:10.2f}")
print("\nANATOMIA DE CADA CRUZAMENTO")
for k,c in CRUZ.items():
    print(f"\n  {k}   limiar {b_(c['limiar'])}   D1 {b_(c['d1_ini'])}   D7 {b_(c['d7_fim'])}   "
          f"{'inversão estabelecida' if c['estabelecida'] else 'divergência'}")
    for it in c['cruzamentos']:
        print(f"    cruza em D{b_(it['abscissa'])}  ·  velocidade {b_(it['velocidade'])} pt/dia "
              f"({b_(it['velocidade_em_limiares'])} limiar/dia)  ·  aceleração "
              f"{b_(it['aceleracao'])} pt/dia² ({b_(it['aceleracao_em_limiares'])} limiar/dia²)")
        print(f"    zona de indecisão: D{b_(it['zona_ini'])} a D{b_(it['zona_fim'])}  "
              f"(largura {b_(it['zona_largura'])} dia)  ·  travessia "
              f"{'nítida' if it['nitido'] else 'lenta em relação ao ruído'}")
print(f"\nsalvo: {os.path.join(S,'V2_cruz.json')}")
