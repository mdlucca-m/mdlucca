import warnings; warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, json
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from scipy.interpolate import UnivariateSpline
OUT='/home/user/mdlucca/Artigos/figuras'
h=pd.read_csv('hum_prof.csv'); LD=pd.read_csv('hiit_load.csv'); PHY=json.load(open('physio2.json'))
# ---- 13 coletas (base D1; pré/pós D2-D7), x em dias ----
seq=[(1,'baseline',1.0)]
for d in range(2,8): seq+=[(d,'pre',d-0.2),(d,'pos',d+0.2)]
x=np.array([xx for _,_,xx in seq])
def cm(k): return np.array([float(h[(h.dia==d)&(h.momento==m)][k].dropna().mean()) for d,m,_ in seq])
V=cm('Vigor'); F=cm('Fadiga'); P=cm('TMD')
xx=np.linspace(x.min(),x.max(),400)
def spl(y): return UnivariateSpline(x,y,k=4,s=len(x)*np.var(y)*0.85)
sV,sF,sP=spl(V),spl(F),spl(P)
VV,FF,PP=sV(xx),sF(xx),sP(xx)
velP=sP.derivative(1)(xx)      # "velocidade" da PTH (pontos/dia)
accP=sP.derivative(2)(xx)      # "aceleração" da PTH (pontos/dia²)
# carga HIIT por dia (FC de esforço e %FCmáx)
FCMAX=198.5; days=[2,4,7]
fc=[float(LD[LD.dia==d]['mean_fc'].mean()) for d in days]
pctfc=[100*v/FCMAX for v in fc]
pse=[float(LD[LD.dia==d]['final_pse'].mean()) for d in days]
# taxa de fadiga: %perda de vigor por dia vs melhor dia (dia com maior vigor)
vig_day=h.dropna(subset=['dia']).groupby('dia')['Vigor'].mean()
best=vig_day.max(); floss=[100*(best-vig_day[d])/best for d in range(1,8)]

TEAL='#0f8b8d'; CORAL='#e8737a'; GOLD='#e8b84a'; RED='#e03b3b'; PURP='#b39ddb'; DARK='#2b3a4a'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':12,'axes.edgecolor':'#333',
    'axes.linewidth':1.1,'axes.grid':True,'grid.color':'#dddddd','grid.linewidth':0.8})
fig=plt.figure(figsize=(15,17)); gs=GridSpec(6,2,figure=fig,height_ratios=[1.4,1.1,1.6,1.2,1.2,1.3],hspace=0.55,wspace=0.22)

# A) sinais + limites
axA=fig.add_subplot(gs[0,:])
axA.plot(xx,VV,color=TEAL,lw=3,label='Vigor'); axA.plot(xx,FF,color=GOLD,lw=3,label='Fadiga'); axA.plot(xx,PP,color=CORAL,lw=3,label='PTH')
axA.axhline(PP.min(),ls=':',color=CORAL,lw=1.6); axA.axhline(PP.max(),ls=':',color=CORAL,lw=1.6)
for d in days: axA.axvline(d,color='#999',ls='--',lw=1)
axA.set_title('A) DINÂMICA DO HUMOR — trajetórias e LIMITES (linhas pontilhadas = mín/máx da PTH; tracejado = dias de HIIT)',fontweight='bold',fontsize=12.5)
axA.set_xlabel('Dia do microciclo'); axA.set_ylabel('Escore'); axA.legend(loc='lower right',ncol=3,framealpha=0.9)

# B) velocidade
axB=fig.add_subplot(gs[1,0])
axB.plot(xx,velP,color=TEAL,lw=2.5); axB.axhline(0,color='#333',lw=1)
axB.set_title('B) Velocidade da mudança — PTH (pontos/dia)',fontweight='bold',fontsize=12)
axB.set_xlabel('Dia'); axB.set_ylabel('dPTH/dt')
# C) aceleracao
axC=fig.add_subplot(gs[1,1])
axC.plot(xx,accP,color=CORAL,lw=2.5); axC.axhline(0,color='#333',lw=1)
axC.set_title('C) Aceleração da mudança — PTH (pontos/dia²)',fontweight='bold',fontsize=12)
axC.set_xlabel('Dia'); axC.set_ylabel('d²PTH/dt²')

# D) carga interna do HIIT (magnitude FC + intensidade %FCmáx)
axD=fig.add_subplot(gs[2,:])
axD.bar(days,fc,width=0.5,color=DARK,alpha=0.85,label='FC de esforço (bpm)')
for xd,v in zip(days,fc): axD.text(xd,v+2,'%.0f'%v,ha='center',fontsize=10,color=DARK)
axD.set_ylim(140,200); axD.set_ylabel('FC de esforço (bpm)',color=DARK)
axD2=axD.twinx(); axD2.plot(days,pse,color=PURP,lw=3,marker='o',ms=10,label='PSE final (0–10)')
axD2.set_ylim(7,10.5); axD2.set_ylabel('PSE final (0–10)',color='#7048e8'); axD2.grid(False)
axD.set_title('D) CARGA INTERNA DO HIIT — magnitude (FC) e intensidade percebida (PSE), dias 2/4/7',fontweight='bold',fontsize=12.5)
axD.set_xlabel('Dia do microciclo'); axD.set_xticks(days)
l1,la1=axD.get_legend_handles_labels(); l2,la2=axD2.get_legend_handles_labels(); axD.legend(l1+l2,la1+la2,loc='upper left',framealpha=0.9)

# E) taxa de desenvolvimento da perturbação (RFD analog = dPTH/dt) sessão completa
axE=fig.add_subplot(gs[3,:])
axE.plot(xx,velP,color=RED,lw=2.2); axE.axhline(0,color='#333',lw=1)
for d in days: axE.axvline(d,color=CORAL,ls='--',lw=1.4)
axE.set_title('E) TAXA DE DESENVOLVIMENTO DA PERTURBAÇÃO (dPTH/dt) — microciclo completo (tracejado = HIIT)',fontweight='bold',fontsize=12.5)
axE.set_xlabel('Dia do microciclo'); axE.set_ylabel('dPTH/dt (pontos/dia)')

# F) taxa de fadiga (%perda de vigor por dia)
axF=fig.add_subplot(gs[4,0])
cols=[TEAL,GOLD,CORAL,RED,PURP,'#8bc34a','#00897b']
axF.bar(range(1,8),floss,color=cols,alpha=0.85)
axF.set_title('F) Taxa de fadiga (%perda de vigor por dia vs melhor dia)',fontweight='bold',fontsize=12)
axF.set_xlabel('Dia'); axF.set_ylabel('%perda de vigor'); axF.set_xticks(range(1,8))

# caixa de limites
axG=fig.add_subplot(gs[4,1]); axG.axis('off')
vpk=np.max(np.abs(velP)); apk=np.max(np.abs(accP))
txt=('LIMITES DA SESSÃO (microciclo)\n\n'
 'Vigor:   %.1f  –  %.1f\n'
 'Fadiga:  %.1f  –  %.1f\n'
 'PTH:     %.1f  –  %.1f\n\n'
 'Vel. pico da PTH:   %.1f pts/dia\n'
 'Acel. pico da PTH:  %.1f pts/dia²\n'
 'FC pico:            %.0f bpm (%.0f%% FCmáx)\n'
 'PSE final (máx):    %.1f / 10'%(
   VV.min(),VV.max(),FF.min(),FF.max(),PP.min(),PP.max(),vpk,apk,max(fc),max(pctfc),max(pse)))
axG.text(0.0,0.95,txt,va='top',ha='left',family='DejaVu Sans Mono',fontsize=12.5)

fig.suptitle('PAINEL PSICOFISIOLÓGICO — dinâmica do humor, derivadas, carga do HIIT e taxa de fadiga',
    fontweight='bold',fontsize=15,y=0.995)
fig.savefig(f'{OUT}/dashboard_humor.png',dpi=150,bbox_inches='tight',facecolor='white')
print('OK dashboard_humor.png')
