# -*- coding: utf-8 -*-
"""Limites e derivadas da trajetória de humor (BRUMS × HIIT).

Tratamento de cálculo da dinâmica do humor ao longo do microciclo:
  A. A trajetória diária como função contínua f(t): ajuste saturante
     f(t) = L − (L − f1)·e^{−k(t−1)} à média diária da fadiga física.
  B. DERIVADA por LIMITE: a razão incremental [f(t0+h) − f(t0)]/h → f'(t0)
     quando h → 0 (definição), mostrada numericamente convergindo.
  C. DERIVADAS analíticas: f'(t) (velocidade de acúmulo) e f''(t)
     (aceleração), comparadas às diferenças finitas centrais empíricas.
  D. LIMITES assintóticos: lim_{t→∞} f(t) = L (estado estacionário) e a
     derivada do modelo teórico fitness–fadiga, com o ponto crítico
     (State'(t*) = 0 → pico de fadiga) e o retorno à linha de base.

Autocontido: lê ../modelagem/base_modelagem.csv. Uso: python limites_derivadas.py
Dependências: numpy scipy pandas matplotlib
"""
import os, json, warnings, numpy as np, pandas as pd
from scipy.optimize import curve_fit
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
warnings.filterwarnings('ignore')
HERE=os.path.dirname(os.path.abspath(__file__))
P=dict(BLUE='#245C8B',TEAL='#0E8C86',GOLD='#C7871B',RED='#C0392B',NAVY='#122438',MUT='#5B6B82',VIO='#7A5AA8',GRID='#E3E9F0')
df=pd.read_csv(os.path.join(HERE,'..','modelagem','base_modelagem.csv'))
t=np.arange(1,8,dtype=float)
y=df.groupby('dia')['FadFis'].mean().reindex(range(1,8)).values  # fadiga física média por dia
out={'variavel':'Fadiga física (média diária)','t':list(t),'y':[round(float(v),3) for v in y]}

# ---------- A. ajuste saturante f(t)=L-(L-f1)e^{-k(t-1)} ----------
def fsat(tt,L,f1,k): return L-(L-f1)*np.exp(-k*(tt-1))
p0=[y.max()+1,y[0],0.5]
popt,_=curve_fit(fsat,t,y,p0=p0,maxfev=20000); L,f1,k=popt
def f(tt): return fsat(tt,L,f1,k)
def fp(tt): return k*(L-f1)*np.exp(-k*(tt-1))       # f'(t) analítica
def fpp(tt): return -k*k*(L-f1)*np.exp(-k*(tt-1))   # f''(t) analítica
out['ajuste']={'forma':'f(t)=L-(L-f1)·e^{-k(t-1)}','L':round(float(L),3),'f1':round(float(f1),3),'k':round(float(k),3),
               'R2':round(float(1-np.sum((y-f(t))**2)/np.sum((y-y.mean())**2)),3)}
print(f"A. Ajuste: L={L:.2f} f1={f1:.2f} k={k:.2f} R²={out['ajuste']['R2']:.3f}")

# ---------- B. derivada por limite (razão incremental) em t0 ----------
t0=2.0; hs=[1,0.5,0.25,0.1,0.05,0.01,0.001]
quo=[(f(t0+h)-f(t0))/h for h in hs]
out['B_definicao_limite']={'t0':t0,'f_linha_analitica':round(float(fp(t0)),4),
    'razoes_incrementais':[{'h':h,'quociente':round(float(q),4)} for h,q in zip(hs,quo)]}
print(f"B. Razão incremental em t0={t0:.0f}: h=1→{quo[0]:.3f} ... h=0,001→{quo[-1]:.3f} · f'(t0) analítica={fp(t0):.3f}")

# ---------- C. derivadas analíticas vs diferenças finitas ----------
dc=np.gradient(y,t)  # diferença central empírica
out['C_derivadas']=[{'dia':int(tt),'f':round(float(f(tt)),2),
    'f_linha':round(float(fp(tt)),3),'f_2linha':round(float(fpp(tt)),3),
    'dif_central_empirica':round(float(dc[i]),3)} for i,tt in enumerate(t)]
print("C. f'(t) decrescente (aceleração<0):", [round(float(fp(tt)),2) for tt in t])

# ---------- D. limites assintóticos + modelo teórico ----------
# limite t->inf do ajuste: L (estado estacionário)
lim_inf=float(L)
# modelo teórico fitness-fadiga (pós-sessão, parâmetros ILUSTRATIVOS)
k1,k2,tau1,tau2=3.0,6.0,3.0,1.0  # fitness lenta, fadiga rápida (ilustrativo)
def St(tt): return k1*np.exp(-tt/tau1)-k2*np.exp(-tt/tau2)      # desvio da linha de base
def Sp(tt): return -(k1/tau1)*np.exp(-tt/tau1)+(k2/tau2)*np.exp(-tt/tau2)  # State'(t)
# ponto crítico State'(t*)=0  =>  t* = ln[(k2/tau2)/(k1/tau1)] / (1/tau2 - 1/tau1)
tstar=np.log((k2/tau2)/(k1/tau1))/(1/tau2-1/tau1)
out['D_limites']={
  'lim_t_inf_ajuste':round(lim_inf,3),
  'interpretacao_lim':'a fadiga física satura em ~L (estado estacionário do acúmulo)',
  'modelo_teorico':{'State(t)=k1·e^{-t/τ1}-k2·e^{-t/τ2}':True,
     'derivada':"State'(t)=-(k1/τ1)e^{-t/τ1}+(k2/τ2)e^{-t/τ2}",
     'params_ilustrativos':{'k1':k1,'k2':k2,'tau1':tau1,'tau2':tau2},
     'ponto_critico_t*':round(float(tstar),3),
     'nota_ponto_critico':'State\'(t*)=0 → nadir do estado (pico de fadiga aguda); antes recupera, depois relaxa',
     'lim_t_inf':'State(t)→0 (retorno à linha de base p0)'}}
print(f"D. lim_(t→∞) ajuste = {lim_inf:.2f} (estado estacionário) · ponto crítico teórico t*={tstar:.2f} · lim modelo→0 (baseline)")

json.dump(out,open(os.path.join(HERE,'resultados_limites_derivadas.json'),'w'),ensure_ascii=False,indent=1,default=str)

# ================= figura =================
plt.rcParams.update({'font.family':'DejaVu Sans'})
fig,axs=plt.subplots(2,2,figsize=(13,9.4),dpi=150)
tg=np.linspace(1,7,300)
# A trajetória + curva + reta tangente em t0
ax=axs[0,0]
ax.plot(t,y,'o',color=P['BLUE'],ms=8,label='média diária (dados)')
ax.plot(tg,f(tg),'-',color=P['TEAL'],lw=2,label='ajuste f(t) saturante')
# reta tangente em t0=2: y = f(t0)+f'(t0)(t-t0)
tt=np.linspace(t0-1,t0+1.6,50); ax.plot(tt,f(t0)+fp(t0)*(tt-t0),'--',color=P['RED'],lw=1.8,label=f"tangente em t={t0:.0f} (f'={fp(t0):.2f})")
ax.plot([t0],[f(t0)],'s',color=P['RED'],ms=8)
ax.axhline(L,ls=':',color=P['MUT'],lw=1.2); ax.text(6.4,L+0.05,f'L={L:.1f}',fontsize=8,color=P['MUT'])
ax.set_xlabel('dia do microciclo (t)'); ax.set_ylabel('fadiga física'); ax.legend(fontsize=8,frameon=False,loc='lower right')
ax.set_title('A · Trajetória f(t) e a reta tangente\n(inclinação = derivada)',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# B razão incremental -> derivada
ax=axs[1,0] if False else axs[0,1]
ax.plot(range(len(hs)),quo,'-o',color=P['VIO'],lw=2,ms=6)
ax.axhline(fp(t0),ls='--',color=P['RED'],lw=1.6,label=f"f'(t₀) analítica = {fp(t0):.3f}")
ax.set_xticks(range(len(hs))); ax.set_xticklabels([f'{h:g}' for h in hs],fontsize=8)
ax.set_xlabel('h (incremento) →  0'); ax.set_ylabel('[f(t₀+h)−f(t₀)]/h')
ax.legend(fontsize=9,frameon=False); ax.set_title(f'B · Definição por limite em t₀={t0:.0f}\na razão incremental → derivada quando h→0',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# C derivada (velocidade) analítica vs diferenças finitas
ax=axs[1,0]
ax.plot(tg,fp(tg),'-',color=P['TEAL'],lw=2,label="f'(t) analítica (velocidade)")
ax.plot(t,dc,'o',color=P['BLUE'],ms=7,label='diferença central (empírica)')
ax.axhline(0,color=P['MUT'],lw=.8)
ax.set_xlabel('dia (t)'); ax.set_ylabel("f'(t) — acúmulo por dia"); ax.legend(fontsize=8.5,frameon=False)
ax.set_title("C · Derivada = velocidade de acúmulo\nf'>0 e decrescente → aceleração f''<0",fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
# D modelo teórico fitness-fadiga: State e State' com ponto crítico e limite
ax=axs[1,1]; td=np.linspace(0,8,300)
ax.plot(td,St(td),'-',color=P['NAVY'],lw=2,label='State(t) (desvio da base)')
ax.plot(td,Sp(td),'-',color=P['GOLD'],lw=1.8,label="State'(t)")
ax.axhline(0,color=P['MUT'],lw=.8)
ax.axvline(tstar,ls='--',color=P['RED'],lw=1.4); ax.plot([tstar],[St(tstar)],'o',color=P['RED'],ms=8)
ax.text(tstar+0.1,St(tstar),f"  t*={tstar:.2f}\n  State'=0",fontsize=8,color=P['RED'],va='center')
ax.text(6.0,0.15,'lim  State(t) = 0\n(base)',fontsize=8,color=P['MUT'])
ax.set_xlabel('tempo após a sessão (t)'); ax.set_ylabel('estado / derivada'); ax.legend(fontsize=8.5,frameon=False,loc='lower right')
ax.set_title('D · Modelo teórico fitness–fadiga\nderivada zera no pico de fadiga; limite → base',fontsize=10.5,loc='left',color=P['NAVY'],fontweight='bold')
for sp in['top','right']: ax.spines[sp].set_visible(False)
fig.tight_layout(); fig.savefig(os.path.join(HERE,'limites_derivadas_fig.png'),facecolor='white'); plt.close()
print("\nSalvo resultados_limites_derivadas.json + limites_derivadas_fig.png")
