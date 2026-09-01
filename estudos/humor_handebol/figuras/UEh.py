# -*- coding: utf-8 -*-
import json, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Patch, Rectangle
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import os
RAIZ=os.environ.get("HH_RAIZ") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DADOS=os.path.join(RAIZ,"dados"); SAIDA=os.path.join(RAIZ,"saida")
os.makedirs(SAIDA, exist_ok=True)
B=json.load(open(f"{DADOS}/U_base.json"))
Q=json.load(open(f"{DADOS}/U_perfis.json"))
St=json.load(open(f"{DADOS}/U_stats.json")); S2=json.load(open(f"{DADOS}/U_stats2.json"))
PP=json.load(open(f"{DADOS}/U_prepos.json")); CT=json.load(open(f"{DADOS}/U_cont.json"))
B1=json.load(open(f"{DADOS}/U_brums1.json")); B2=json.load(open(f"{DADOS}/U_brums2.json"))
E=json.load(open(f"{DADOS}/U_estimulo.json"))
NORMA=B['NORMA']; CARGA=B['CARGA']
SUB=['Tensão','Depressão','Raiva','Vigor','Fadiga','Confusão']
PERF=['Iceberg','Superfície','Submerso','Barbatana de tubarão','Iceberg invertido','Everest invertido']
# paleta validada (light mode)
CAT=['#2166AC','#1A9070','#E0952B','#C1440E','#8A4FBF','#A31E52']
CV={'Tensão':'#2166AC','Depressão':'#1A9070','Raiva':'#E0952B','Vigor':'#C1440E',
    'Fadiga':'#8A4FBF','Confusão':'#A31E52','TMD':'#2A2F33'}
CPF={PERF[i]:CAT[i] for i in range(6)}
CEST={'Basal':'#6B7378','HIIT':'#C1440E','Amistoso':'#2166AC','Técnico':'#1A9070','Técnico/força':'#1A9070'}
INK='#2A2F33'; MUT='#6B7378'; GRID='#DDE0E2'; SURF='#FFFFFF'
plt.rcParams.update({'font.size':10,'font.family':'DejaVu Sans','axes.spines.top':False,
  'axes.spines.right':False,'figure.dpi':300,'savefig.dpi':300,'axes.linewidth':1.1,
  'axes.edgecolor':'#8A9299','text.color':INK,'axes.labelcolor':INK,
  'xtick.color':MUT,'ytick.color':MUT,'figure.facecolor':SURF,'axes.facecolor':SURF})
def vg(v,n=1):
    return f"{v:.{n}f}".replace('.',',').replace('-','−')
def pv(p):
    return ('p < 0,001' if p<0.001 else 'p = '+f"{p:.3f}".replace('.',','))
def Tv(k,x):
    m,s=NORMA[k]; return (x-m)/s*10+50
x7=np.arange(1,8)
TIPO={d:CARGA[str(d)]['tipo'] for d in range(1,8)}
def marcar(a,alpha=1.0,y=None):
    for d in range(1,8):
        t=TIPO[d]
        c={'Basal':'#F0F1F2','HIIT':'#FBEAE3','Amistoso':'#E7EFF7','Técnico/força':'#E4F1EC'}[t]
        a.axvspan(d-.5,d+.5,color=c,zorder=0,lw=0,alpha=alpha)
def rodape(fig,txt):
    fig.text(0.008,0.008,txt,fontsize=8.2,color=MUT,style='italic',ha='left',va='bottom')
def gy(a):
    a.grid(axis='y',color=GRID,lw=.8,zorder=0); a.set_axisbelow(True)
