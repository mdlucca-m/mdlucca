# -*- coding: utf-8 -*-
"""Decomposição da variação do humor no microciclo, em quatro camadas.

O estudo afirma que a semana se move por choques nas pontas, com platô no
meio, e que parte do que se observa é ruído amostral. As duas afirmações são
quantificáveis, e esta rotina as quantifica por decomposições explícitas, cada
uma com o seu estimador declarado.

A) COMPONENTES DE VARIÂNCIA, no par atleta-dia
   y(a,d) = μ + α(a) + δ(d) + ε(a,d), com α e δ aleatórios e cruzados.
   Separa o que é diferença estável entre atletas, o que é movimento do elenco
   inteiro de um dia para o outro, e o que sobra. Interessa porque a pergunta
   do pesquisador é sobre δ e a do preparador é sobre ε.

B) SÉRIE DE MÉDIAS DIÁRIAS: variação verdadeira contra erro de amostragem
   A variância observada entre as sete médias diárias contém duas parcelas:
       Var(observada) = Var(verdadeira) + média dos EP²
   porque cada média diária carrega o seu próprio erro-padrão. Subtraindo a
   segunda parcela obtém-se a variação que sobreviveria se cada dia tivesse
   sido medido sem erro, e a razão entre uma e outra é a fidedignidade da
   série diária. É a mesma ideia do piso de ruído, levada da comparação entre
   dois pontos para a série inteira.

C) DESLOCAMENTO TOTAL: quanto veio de choque e quanto veio de deriva
   O deslocamento entre o primeiro e o sétimo dia é a soma das seis
   transições. Separam-se as que superam o piso de ruído, ditas de choque,
   das que não o superam, ditas de deriva, e mede-se quanto do total cada
   grupo carrega. Quantifica a afirmação de que a semana se move por eventos.

D) FILTRO: variância retida e variância removida
   A série observada decompõe-se em suavizada mais resíduo. As duas parcelas
   não são ortogonais, e por isso a covariância entre elas é reportada em vez
   de omitida.
"""
import os, json, warnings
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
warnings.filterwarnings("ignore")
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S=os.path.join(RAIZ,"dados")
B=json.load(open(os.path.join(S,"V2_base.json")))
A1=json.load(open(os.path.join(S,"V2_a1.json")))
V7=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão','TMD']
LB={'TMD':'PTH'}

def suav(y):
    y=np.asarray(y,float); z=y.copy()
    for i in range(1,len(y)-1): z[i]=.25*y[i-1]+.5*y[i]+.25*y[i+1]
    return z

PAR=pd.DataFrame(B['pares'])

# ---------- A) componentes de variância, com efeitos cruzados ----------
COMP={}
for v in V7:
    d=PAR[['a','dia',v]].dropna().rename(columns={v:'y'}).copy()
    d['um']=1
    m=smf.mixedlm("y ~ 1", d, groups=d['um'],
                  vc_formula={"atleta":"0+C(a)","dia":"0+C(dia)"}).fit(reml=True)
    va=float(m.vcomp[list(m.model.exog_vc.names).index('atleta')])
    vd=float(m.vcomp[list(m.model.exog_vc.names).index('dia')])
    ve=float(m.scale)
    tot=va+vd+ve
    COMP[v]=dict(atleta=va, dia=vd, residual=ve, total=tot,
                 p_atleta=100*va/tot, p_dia=100*vd/tot, p_residual=100*ve/tot,
                 n=int(len(d)))

# ---------- B) série diária: variação verdadeira contra erro ----------
SERIE={}
for v in V7:
    med=np.array(A1['SER'][v]['med'],float); ep=np.array(A1['SER'][v]['ep'],float)
    vobs=float(np.var(med, ddof=1)); verro=float(np.mean(ep**2))
    vver=max(0.0, vobs-verro)
    SERIE[v]=dict(var_observada=vobs, var_erro=verro, var_verdadeira=vver,
                  fidedignidade=(vver/vobs if vobs>0 else float('nan')),
                  dp_verdadeiro=float(np.sqrt(vver)), dp_erro=float(np.sqrt(verro)),
                  negativa=bool(vobs-verro < 0))

# ---------- C) deslocamento: choque contra deriva ----------
DESL={}
for v in V7:
    sm=suav(A1['SER'][v]['med']); piso=float(A1['SER'][v]['piso'])
    tr=np.diff(sm)                                   # seis transições
    ch=np.array([t if abs(t)>piso else 0.0 for t in tr])
    dr=tr-ch
    total=float(tr.sum())
    DESL[v]=dict(total=total, choque=float(ch.sum()), deriva=float(dr.sum()),
                 n_choques=int((ch!=0).sum()),
                 p_choque=(100*ch.sum()/total if total!=0 else float('nan')),
                 transicoes=tr.tolist(), piso=piso,
                 soma_abs=float(np.abs(tr).sum()),
                 p_choque_abs=(100*np.abs(ch).sum()/np.abs(tr).sum()
                               if np.abs(tr).sum()>0 else float('nan')))

# ---------- D) filtro: retido contra removido ----------
FIL={}
for v in V7:
    ob=np.array(A1['SER'][v]['med'],float); sm=suav(ob); r=ob-sm
    vs=float(np.var(sm,ddof=1)); vr=float(np.var(r,ddof=1))
    cov=float(np.cov(sm,r,ddof=1)[0,1]); vo=float(np.var(ob,ddof=1))
    FIL[v]=dict(var_observada=vo, var_suavizada=vs, var_residuo=vr, covariancia=cov,
                soma_conferida=vs+vr+2*cov, p_retida=100*vs/vo, p_removida=100*vr/vo)

json.dump(dict(COMPONENTES=COMP, SERIE=SERIE, DESLOCAMENTO=DESL, FILTRO=FIL, V7=V7),
          open(os.path.join(S,"V2_decomp.json"),"w",encoding="utf-8"), ensure_ascii=False)

L=lambda k: LB.get(k,k)
b=lambda x,d=2: f"{x:.{d}f}".replace('.',',').replace('-','−')
print("A) COMPONENTES DE VARIÂNCIA NO PAR ATLETA-DIA  (efeitos cruzados, REML)")
print(f"  {'variável':<11}{'entre atletas':>15}{'entre dias':>13}{'residual':>11}   soma")
for v in V7:
    c=COMP[v]
    print(f"  {L(v):<11}{c['p_atleta']:14.1f}%{c['p_dia']:12.1f}%{c['p_residual']:10.1f}%   {b(c['total'])}")
print("\nB) SÉRIE DE MÉDIAS DIÁRIAS: QUANTO DA VARIAÇÃO É VERDADEIRO")
print(f"  {'variável':<11}{'Var obs':>10}{'Var erro':>10}{'Var verd.':>11}{'fidedig.':>10}  {'DP verd.':>9}")
for v in V7:
    s=SERIE[v]
    print(f"  {L(v):<11}{b(s['var_observada'],3):>10}{b(s['var_erro'],3):>10}"
          f"{b(s['var_verdadeira'],3):>11}{b(s['fidedignidade'],3):>10}  {b(s['dp_verdadeiro']):>9}"
          + ("   ← estimativa nula" if s['negativa'] else ""))
print("\nC) DESLOCAMENTO TOTAL: QUANTO VEIO DE CHOQUE")
print("   O percentual sobre o total com sinal pode ultrapassar 100 quando choque e deriva")
print("   apontam em sentidos opostos; por isso a coluna de referência é a do movimento absoluto.")
print(f"  {'variável':<11}{'Δ total':>9}{'de choque':>11}{'de deriva':>11}{'nº':>4}"
      f"{'% do |movimento|':>18}")
for v in V7:
    d=DESL[v]
    print(f"  {L(v):<11}{b(d['total']):>9}{b(d['choque']):>11}{b(d['deriva']):>11}"
          f"{d['n_choques']:>4}{b(d['p_choque_abs'],1):>17}%")
print("\nD) O FILTRO: VARIÂNCIA RETIDA E REMOVIDA")
print("   Identidade: Var(observada) = Var(suavizada) + Var(resíduo) + 2·cov. As duas parcelas")
print("   não são ortogonais, e onde a covariância é negativa a parcela retida excede o total.")
print(f"  {'variável':<11}{'Var obs':>10}{'retida':>10}{'removida':>11}{'2·cov':>10}{'soma':>9}")
for v in V7:
    f=FIL[v]
    print(f"  {L(v):<11}{b(f['var_observada'],3):>10}{b(f['var_suavizada'],3):>10}"
          f"{b(f['var_residuo'],3):>11}{b(2*f['covariancia'],3):>10}{b(f['soma_conferida'],3):>9}")
print(f"\nsalvo: {os.path.join(S,'V2_decomp.json')}")
